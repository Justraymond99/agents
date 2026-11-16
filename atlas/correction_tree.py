"""Deterministic decision-tree fixture helper, NOT a model-behavior evaluation.

A human/test author supplies which mechanisms are *reliably* available.
The helper tests the ordering contract; it cannot establish that an agent
correctly diagnosed a real-world failure.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class CorrectionCase:
    name: str
    redesign: bool = False
    lint: bool = False
    verify: bool = False
    rule: bool = False
    human_approval_required: bool = False


def select_layer(case: CorrectionCase) -> str:
    """Return the first reliable layer, or human review as fallback."""
    for available, layer in (
        (case.redesign, "redesign"),
        (case.lint, "lint"),
        (case.verify, "verify"),
        (case.rule, "rule"),
    ):
        if available:
            return layer
    return "human-review"
