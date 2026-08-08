"""Cross-platform hashing for repository-managed text artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path


TEXT_ARTIFACT_SUFFIXES = frozenset({".csv", ".json", ".jsonl", ".md", ".txt", ".yaml", ".yml"})


def artifact_bytes(path: Path) -> bytes:
    """Return stable bytes for hashing while preserving binary artifacts exactly."""

    raw = path.read_bytes()
    if path.suffix.lower() in TEXT_ARTIFACT_SUFFIXES:
        return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return raw


def artifact_sha256(path: Path) -> str:
    return hashlib.sha256(artifact_bytes(path)).hexdigest()


def artifact_size_bytes(path: Path) -> int:
    return len(artifact_bytes(path))
