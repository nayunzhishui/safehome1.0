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
