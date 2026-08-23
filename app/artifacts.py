from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field


class Artifact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(min_length=1)
    path: str = Field(min_length=1)
    media_type: str = "application/octet-stream"
    sha256: str = Field(min_length=64, max_length=64)
    size_bytes: int = Field(ge=0)


class ArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self._artifacts: dict[str, Artifact] = {}

    def _resolve(self, relative_path: str) -> Path:
        target = (self.root / relative_path).resolve()
        if self.root not in target.parents and target != self.root:
            raise ValueError("artifact path escapes configured root")
        return target

    def put_bytes(
        self,
        name: str,
        data: bytes,
        *,
        media_type: str = "application/octet-stream",
    ) -> Artifact:
        artifact_id = str(uuid4())
        suffix = Path(name).suffix
        relative = f"{artifact_id}{suffix}"
        path = self._resolve(relative)
        path.write_bytes(data)
        artifact = Artifact(
            id=artifact_id,
            name=name,
            path=relative,
            media_type=media_type,
            sha256=hashlib.sha256(data).hexdigest(),
            size_bytes=len(data),
        )
        self._artifacts[artifact.id] = artifact
        return artifact.model_copy(deep=True)

    def get(self, artifact_id: str) -> Artifact | None:
        artifact = self._artifacts.get(artifact_id)
        return artifact.model_copy(deep=True) if artifact else None

    def read_bytes(self, artifact_id: str) -> bytes:
        artifact = self._artifacts.get(artifact_id)
        if artifact is None:
            raise KeyError(f"artifact '{artifact_id}' not found")
        return self._resolve(artifact.path).read_bytes()
