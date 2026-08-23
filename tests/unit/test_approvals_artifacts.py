from pathlib import Path

import pytest

from app.approvals import ApprovalManager, ApprovalStatus
from app.artifacts import ArtifactStore


def test_approval_lifecycle() -> None:
    manager = ApprovalManager()
    created = manager.create("deploy", "production side effect")

    assert created.status is ApprovalStatus.PENDING

    resolved = manager.resolve(created.id, approved=True)
    assert resolved.status is ApprovalStatus.APPROVED
    assert resolved.resolved_at is not None

    with pytest.raises(ValueError, match="already resolved"):
        manager.resolve(created.id, approved=False)


def test_artifact_store_persists_content_and_metadata(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    artifact = store.put_bytes("report.txt", b"hello", media_type="text/plain")

    assert artifact.name == "report.txt"
    assert artifact.size_bytes == 5
    assert store.read_bytes(artifact.id) == b"hello"
    assert store.get(artifact.id) == artifact
