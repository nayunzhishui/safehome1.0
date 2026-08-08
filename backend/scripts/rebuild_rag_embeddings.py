"""Rebuild optional embeddings for approved SafeHome knowledge chunks only."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from database import get_connection, json_dumps, now_iso
from services.ai_qa_retrieval_service import sync_approved_knowledge
from services.embedding_service import embed_texts, embedding_model, public_status
from services.schema_migration_service import apply_pending_schema_migrations


def eligible_chunks(conn, limit=None):
    sql = """
    SELECT c.id, c.content_text, c.content_hash
    FROM ai_knowledge_chunks c
    JOIN ai_knowledge_documents d ON d.id = c.document_id
    JOIN content_governance_versions v ON v.id = d.version_id AND v.status = 'published'
    JOIN content_governance_releases r ON r.id = d.release_id AND r.status = 'active'
    WHERE d.status = 'active' AND d.review_status = 'approved'
    ORDER BY d.id, c.ordinal
    """
    params = ()
    if limit is not None:
        sql += " LIMIT ?"
        params = (limit,)
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def rebuild(batch_size=32, limit=None, dry_run=False, allow_hash=False):
    provider = public_status()
    if provider["provider"] == "hash" and not allow_hash:
        raise RuntimeError("hash模式已有vector_json；写embedding列需显式 --allow-hash")
    sync_approved_knowledge()
    with get_connection() as conn:
        apply_pending_schema_migrations(conn)
        conn.commit()
        chunks = eligible_chunks(conn, limit)
    if dry_run:
        return {"dry_run": True, "eligible_chunks": len(chunks), "provider": provider["provider"], "model": embedding_model()}

    updated = 0
    dimensions = None
    for offset in range(0, len(chunks), batch_size):
        batch = chunks[offset:offset + batch_size]
        vectors = embed_texts([item["content_text"] for item in batch])
        with get_connection() as conn:
            for item, vector in zip(batch, vectors):
                current = len(vector)
                if dimensions is None:
                    dimensions = current
                if dimensions != current:
                    raise RuntimeError("embedding维度不一致")
                conn.execute(
                    """UPDATE ai_knowledge_chunks
                    SET embedding_json = ?, embedding_model = ?, embedding_dimensions = ?,
                        embedding_updated_at = ?, retrieval_metadata_json = ?
                    WHERE id = ?""",
                    (json_dumps(vector), embedding_model(), current, now_iso(),
                     json_dumps({"source": "governed_active_knowledge", "content_hash": item["content_hash"]}), item["id"]),
                )
                updated += 1
            conn.commit()
    return {"dry_run": False, "updated_chunks": updated, "model": embedding_model(), "dimensions": dimensions}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-hash", action="store_true")
    args = parser.parse_args()
    result = rebuild(max(1, min(args.batch_size, 128)), args.limit, args.dry_run, args.allow_hash)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
