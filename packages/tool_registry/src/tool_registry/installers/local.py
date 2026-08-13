from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from ..capability_models import InstallPlan


class LocalAdapterError(RuntimeError):
    pass


def _unconfigured(_effect: dict[str, Any]) -> dict[str, Any]:
    raise LocalAdapterError("Local onboarding effect handler is not configured")


class LocalPackageAdapter:
    kind = "local_package"
    version = "1"

    def __init__(
        self,
        *,
        reviewed_recipes: Mapping[str, Mapping[str, Any]],
        effect_handler: Callable[[dict[str, Any]], dict[str, Any]] = _unconfigured,
    ) -> None:
        self.reviewed_recipes = dict(reviewed_recipes)
        self.effect_handler = effect_handler

    def prepare(self, plan: InstallPlan) -> dict[str, Any]:
        recipe = self.reviewed_recipes.get(plan.capability_id)
        if recipe is None:
            raise LocalAdapterError("No reviewed literal package recipe exists")
        if recipe.get("command") != plan.source.get("command"):
            raise LocalAdapterError("The reviewed package recipe changed")
        return {"step": "prepare", "status": "succeeded", "effects": []}

    def apply(self, plan: InstallPlan) -> dict[str, Any]:
        results = [
            self.effect_handler(effect.model_dump(mode="json"))
            for effect in plan.effects
        ]
        return {"step": "apply", "status": "succeeded", "effects": results}

    def validate(self, _plan: InstallPlan) -> dict[str, Any]:
        return {
            "step": "validate",
            "status": "succeeded",
            "limitation": "protocol validation pending",
        }

    def rollback(self, plan: InstallPlan) -> dict[str, Any]:
        results = [
            self.effect_handler(step.model_dump(mode="json"))
            for step in plan.rollback_steps
        ]
        return {"step": "rollback", "status": "succeeded", "effects": results}

    def remove(self, plan: InstallPlan) -> dict[str, Any]:
        return self.rollback(plan)


class LocalCommandAdapter(LocalPackageAdapter):
    kind = "local_command"

    def prepare(self, plan: InstallPlan) -> dict[str, Any]:
        command = plan.source.get("command")
        arguments = plan.source.get("arguments", [])
        recipe = self.reviewed_recipes.get(plan.capability_id)
        if (
            recipe is None
            or recipe.get("command") != command
            or recipe.get("arguments", []) != arguments
        ):
            raise LocalAdapterError(
                "The literal local command is not an approved reviewed recipe"
            )
        return {"step": "prepare", "status": "succeeded", "effects": []}
