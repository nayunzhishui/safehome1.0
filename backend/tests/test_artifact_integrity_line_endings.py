import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.artifact_integrity_service import artifact_sha256, artifact_size_bytes


def test_text_artifact_hash_and_size_are_independent_of_line_endings(tmp_path: Path):
    lf = tmp_path / "artifact.json"
    crlf = tmp_path / "artifact-crlf.json"
    lf.write_bytes(b'{\n  "ok": true\n}\n')
    crlf.write_bytes(b'{\r\n  "ok": true\r\n}\r\n')

    assert artifact_sha256(lf) == artifact_sha256(crlf)
    assert artifact_size_bytes(lf) == artifact_size_bytes(crlf)


def test_binary_artifact_hash_preserves_raw_bytes(tmp_path: Path):
    lf = tmp_path / "artifact.bin"
    crlf = tmp_path / "artifact-crlf.bin"
    lf.write_bytes(b"a\nb")
    crlf.write_bytes(b"a\r\nb")

    assert artifact_sha256(lf) != artifact_sha256(crlf)
    assert artifact_size_bytes(lf) != artifact_size_bytes(crlf)


def test_release_package_uses_the_same_text_bytes_as_manifest_binding(tmp_path, monkeypatch):
    import base64
    import json
    from services import operations_governance_service as service

    content = tmp_path / "content"
    content.mkdir()
    artifact = content / "sample.json"
    artifact.write_bytes(b'{\r\n  "ok": true\r\n}\r\n')
    manifest = content / "manifest.json"
    manifest.write_text(json.dumps({"artifacts": [{"path": "content/sample.json", "sha256": artifact_sha256(artifact), "size_bytes": artifact_size_bytes(artifact)}]}), encoding="utf-8")
    monkeypatch.setattr(service, "ROOT", tmp_path)
    monkeypatch.setattr(service, "RELEASE_MANIFEST_PATH", manifest)
    from flask import Flask
    app = Flask(__name__)
    app.config["CONTENT_DIR"] = content
    with app.app_context():
        bundle = service._snapshot_manifest()
    assert base64.b64decode(bundle["artifacts"][0]["bundle_b64"]) == b'{\n  "ok": true\n}\n'
