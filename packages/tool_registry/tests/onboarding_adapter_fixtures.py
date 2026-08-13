from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FakeOnboardingAdapter:
    kind: str
    version: str = "test-1"
    fail_at: str | None = None
    calls: list[str] = field(default_factory=list)

    def _step(self, name: str) -> dict:
        self.calls.append(name)
        if self.fail_at == name:
            raise RuntimeError(f"injected {name} failure")
        return {"step": name, "status": "succeeded"}

    def prepare(self) -> dict:
        return self._step("prepare")

    def apply(self) -> dict:
        return self._step("apply")

    def validate(self) -> dict:
        return self._step("validate")

    def rollback(self) -> dict:
        return self._step("rollback")

    def remove(self) -> dict:
        return self._step("remove")
