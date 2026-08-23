from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    action: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    payload: dict[str, object] = Field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: datetime | None = None


class ApprovalManager:
    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}

    def create(self, action: str, reason: str, payload: dict[str, object] | None = None) -> ApprovalRequest:
        request = ApprovalRequest(action=action, reason=reason, payload=payload or {})
        self._requests[request.id] = request
        return request.model_copy(deep=True)

    def get(self, approval_id: str) -> ApprovalRequest | None:
        request = self._requests.get(approval_id)
        return request.model_copy(deep=True) if request else None

    def resolve(self, approval_id: str, approved: bool) -> ApprovalRequest:
        request = self._requests.get(approval_id)
        if request is None:
            raise KeyError(f"approval '{approval_id}' not found")
        if request.status is not ApprovalStatus.PENDING:
            raise ValueError("approval is already resolved")
        request.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        request.resolved_at = datetime.now(timezone.utc)
        return request.model_copy(deep=True)
