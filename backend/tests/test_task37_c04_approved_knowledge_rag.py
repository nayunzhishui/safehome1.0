import hashlib
import importlib
import json
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
CONTENT_ROOT = PROJECT_ROOT / "content"


def _fresh_app(tmp_path, monkeypatch):
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))
    for name in list(sys.modules):
        if name in {"app", "config", "database", "models"} or name.startswith(
            ("routes.", "services.")
        ):
            sys.modules.pop(name, None)
    content_dir = tmp_path / "content"
    shutil.copytree(CONTENT_ROOT, content_dir)
    monkeypatch.setenv(
        "DATABASE_PATH", str(tmp_path / "safehome-test.sqlite3")
    )
    monkeypatch.setenv("CONTENT_DIR", str(content_dir))
    monkeypatch.setenv("AI_QA_ENABLED", "0")
    monkeypatch.setenv("AI_QA_SANDBOX_ENABLED", "1")
    monkeypatch.setenv("AI_QA_PROVIDER", "fake")
    return importlib.import_module("app").app


def _actors(app):
    specs = [
        ("researcher-c04", "researcher"),
        ("supervisor-c04", "supervisor"),
        ("admin-c04", "admin"),
    ]
    with app.app_context():
        database = importlib.import_module("database")
        auth_utils = importlib.import_module("routes.auth_utils")
        with database.get_connection() as conn:
            now = database.now_iso()
            for actor_id, role in specs:
                conn.execute(
                    """
                    INSERT INTO users
                    (id, nickname, role, source, status, created_at, updated_at)
                    VALUES (?, ?, ?, 'test', 'active', ?, ?)
                    """,
                    (actor_id, actor_id, role, now, now),
                )
            conn.commit()
        return {
            actor_id: {
                "Authorization": (
                    "Bearer "
                    + auth_utils.generate_auth_token(
                        {"id": actor_id, "role": role}
                    )
                )
            }
            for actor_id, role in specs
        }


def _seed_governed_version(
    app,
    *,
    version_id="cgv-c04-approved",
    release_id="release-c04-approved",
    item_id="three_second_pause",
    status="published",
    release_status="active",
    reviewed=True,
    expires_at="2099-12-31T23:59:59+00:00",
    source="safehome://content/training_cards.json",
    copyright_status="owned",
):
    payload = {
        "id": item_id,
        "title": "三秒暂停",
        "purpose": "情绪升高时先暂停，留意身体信号，再选择一个低负担回应。",
        "steps": ["停一下", "慢呼气", "再选择"],
        "boundary_notice": "这是一项低负担练习，不替代专业帮助。",
    }
    metadata = {
        "source": source,
        "source_version": "2026-07-28",
        "copyright_status": copyright_status,
        "age_scope": "adult",
        "audience": ["researcher", "participant"],
        "change_summary": "T37-C04 test fixture",
        "valid_from": "2026-01-01T00:00:00+00:00",
        "expires_at": expires_at,
    }
    payload_text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    payload_hash = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            now = database.now_iso()
            conn.execute(
                """
                INSERT INTO content_governance_versions
                (id, content_type, item_id, version, payload_json, payload_hash,
                 metadata_json, status, created_by, created_at, updated_at,
                 published_at)
                VALUES (?, 'training_card', ?, 'v1', ?, ?, ?, ?, 'fixture',
                        ?, ?, ?)
                """,
                (
                    version_id,
                    item_id,
                    payload_text,
                    payload_hash,
                    json.dumps(metadata, ensure_ascii=False),
                    status,
                    now,
                    now,
                    now if status == "published" else None,
                ),
            )
            conn.execute(
                """
                INSERT INTO content_governance_releases
                (id, version_id, content_type, item_id, payload_hash,
                 package_json, release_reason, status, released_by, created_at)
                VALUES (?, ?, 'training_card', ?, ?, ?, 'fixture', ?,
                        'fixture', ?)
                """,
                (
                    release_id,
                    version_id,
                    item_id,
                    payload_hash,
                    json.dumps(
                        {"package_hash": f"pkg-{release_id}"},
                        ensure_ascii=False,
                    ),
                    release_status,
                    now,
                ),
            )
            if reviewed:
                for index, discipline in enumerate(
                    ("research", "psychology", "ethics", "content")
                ):
                    conn.execute(
                        """
                        INSERT INTO content_governance_reviews
                        (id, version_id, discipline, decision, reviewer_id,
                         reviewer_role, evidence_path, note, created_at)
                        VALUES (?, ?, ?, 'approved', ?, 'admin', ?, 'fixture',
                                ?)
                        """,
                        (
                            f"review-{version_id}-{discipline}",
                            version_id,
                            discipline,
                            f"reviewer-{index}",
                            f"evidence://{version_id}/{discipline}",
                            now,
                        ),
                    )
            conn.commit()


def test_rebuild_only_indexes_authorized_reviewed_active_content(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    _seed_governed_version(app)
    _seed_governed_version(
        app,
        version_id="cgv-c04-unreviewed",
        release_id="release-c04-unreviewed",
        item_id="unreviewed_web",
        reviewed=False,
        source="https://example.org/public-post",
        copyright_status="public_domain",
    )
    client = app.test_client()

    response = client.post(
        "/api/ai-qa/knowledge/rebuild", headers=headers["admin-c04"]
    )

    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["active_documents"] == 1
    assert data["indexed_documents"] == 1
    assert data["rejected_documents"] >= 1
    listing = client.get(
        "/api/ai-qa/knowledge", headers=headers["researcher-c04"]
    ).get_json()["data"]
    assert [item["item_id"] for item in listing["documents"]] == [
        "three_second_pause"
    ]
    assert listing["documents"][0]["rights_status"] == "owned"
    assert listing["documents"][0]["review_status"] == "approved"
    assert listing["documents"][0]["chunk_count"] >= 3


def test_bm25_vector_and_hybrid_return_traceable_citation(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    _seed_governed_version(app)
    client = app.test_client()
    client.post("/api/ai-qa/knowledge/rebuild", headers=headers["admin-c04"])

    for method in ("bm25", "vector", "hybrid"):
        response = client.get(
            "/api/ai-qa/knowledge/retrieve",
            query_string={
                "query": "情绪升高时怎样暂停和呼气",
                "method": method,
                "audience": "researcher",
            },
            headers=headers["researcher-c04"],
        )
        assert response.status_code == 200
        result = response.get_json()["data"]
        assert result["retrieval_method"] == method
        assert result["citations"]
        citation = result["citations"][0]
        assert citation["content_id"] == "three_second_pause"
        assert citation["chunk_id"]
        assert citation["location"]
        assert citation["source_ref"].startswith("safehome://")
        assert citation["rights_status"] == "owned"
        assert citation["review_status"] == "approved"
        assert set(citation["scores"]) == {
            "bm25",
            "vector",
            "rerank",
            "final",
        }


def test_no_evidence_and_withdrawal_propagate_immediately(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    _seed_governed_version(app)
    client = app.test_client()
    client.post("/api/ai-qa/knowledge/rebuild", headers=headers["admin-c04"])

    unknown = client.get(
        "/api/ai-qa/knowledge/retrieve",
        query_string={
            "query": "量子航天发动机维修",
            "method": "hybrid",
            "audience": "researcher",
        },
        headers=headers["researcher-c04"],
    ).get_json()["data"]
    assert unknown["citations"] == []
    assert unknown["evidence_status"] == "insufficient"

    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            conn.execute(
                """
                UPDATE content_governance_releases
                SET status = 'retired'
                WHERE id = 'release-c04-approved'
                """
            )
            conn.commit()

    withdrawn = client.get(
        "/api/ai-qa/knowledge/retrieve",
        query_string={
            "query": "情绪升高时怎样暂停",
            "method": "hybrid",
            "audience": "researcher",
        },
        headers=headers["researcher-c04"],
    ).get_json()["data"]
    assert withdrawn["citations"] == []
    listing = client.get(
        "/api/ai-qa/knowledge", headers=headers["researcher-c04"]
    ).get_json()["data"]
    assert listing["documents"][0]["status"] == "withdrawn"


def test_expired_content_and_public_candidate_never_enter_index(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    _seed_governed_version(
        app,
        expires_at="2026-01-01T00:00:00+00:00",
    )
    client = app.test_client()

    content_attempt = client.post(
        "/api/ai-qa/knowledge/candidates",
        json={
            "source_url": "https://example.org/article",
            "title": "公开文章",
            "source_hash": "a" * 64,
            "source_text": "不得直接进入知识库的网页正文",
        },
        headers={
            **headers["admin-c04"],
            "Idempotency-Key": "candidate-content",
        },
    )
    assert content_attempt.status_code == 400
    assert (
        content_attempt.get_json()["error"]["code"]
        == "knowledge_candidate_content_forbidden"
    )

    candidate = client.post(
        "/api/ai-qa/knowledge/candidates",
        json={
            "source_url": "https://example.org/article",
            "title": "公开文章",
            "source_hash": "b" * 64,
            "rights_status": "unverified",
        },
        headers={
            **headers["admin-c04"],
            "Idempotency-Key": "candidate-metadata",
        },
    )
    assert candidate.status_code == 200
    assert candidate.get_json()["data"]["status"] == "quarantined"
    assert candidate.get_json()["data"]["indexed"] is False

    rebuilt = client.post(
        "/api/ai-qa/knowledge/rebuild", headers=headers["admin-c04"]
    ).get_json()["data"]
    assert rebuilt["active_documents"] == 0
    listing = client.get(
        "/api/ai-qa/knowledge", headers=headers["researcher-c04"]
    ).get_json()["data"]
    assert listing["candidates"][0]["status"] == "quarantined"
    assert listing["candidates"][0]["indexed"] is False


def test_retrieval_evaluation_records_recall_citation_and_no_evidence(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    headers = _actors(app)
    _seed_governed_version(app)
    client = app.test_client()
    client.post("/api/ai-qa/knowledge/rebuild", headers=headers["admin-c04"])

    response = client.post(
        "/api/ai-qa/knowledge/evaluation/run",
        json={
            "suite_version": "c04-test-v1",
            "cases": [
                {
                    "id": "recall",
                    "query": "情绪升高时先暂停",
                    "expected_content_ids": ["three_second_pause"],
                },
                {
                    "id": "no-evidence",
                    "query": "量子航天发动机维修",
                    "expected_content_ids": [],
                },
            ],
        },
        headers=headers["researcher-c04"],
    )

    assert response.status_code == 200
    result = response.get_json()["data"]
    assert result["metrics"]["recall_at_k"] == 1.0
    assert result["metrics"]["citation_accuracy"] == 1.0
    assert result["metrics"]["no_evidence_accuracy"] == 1.0
    assert result["status"] == "engineering_threshold_passed"
    assert result["human_release_approval"] is False


def test_schema_053_has_versioned_knowledge_without_candidate_raw_text(
    tmp_path, monkeypatch
):
    app = _fresh_app(tmp_path, monkeypatch)
    with app.app_context():
        database = importlib.import_module("database")
        with database.get_connection() as conn:
            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
            candidate_columns = {
                row["name"]
                for row in conn.execute(
                    "PRAGMA table_info(ai_knowledge_candidates)"
                ).fetchall()
            }

    assert database.CURRENT_SCHEMA_VERSION == "2026_07_28_053"
    assert database.CURRENT_SCHEMA_NAME == "approved_knowledge_rag"
    assert {
        "ai_knowledge_documents",
        "ai_knowledge_chunks",
        "ai_knowledge_candidates",
        "ai_knowledge_evaluation_runs",
    }.issubset(tables)
    assert not {
        "source_text",
        "raw_text",
        "content_text",
        "page_html",
    } & candidate_columns
