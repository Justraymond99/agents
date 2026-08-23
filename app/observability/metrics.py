from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class MetricsRecorder:
    counters: dict[str, int] = field(default_factory=dict)
    timings_ms: dict[str, list[float]] = field(default_factory=dict)

    def increment(self, name: str, value: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + value

    def observe(self, name: str, value_ms: float) -> None:
        self.timings_ms.setdefault(name, []).append(value_ms)

    def snapshot(self) -> dict[str, object]:
        return {
            "counters": dict(self.counters),
            "timings_ms": {key: list(values) for key, values in self.timings_ms.items()},
        }
