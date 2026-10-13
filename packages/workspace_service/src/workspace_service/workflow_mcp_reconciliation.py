"""Bounded observation of an exact pending operation declared in accepted source.

No provider names or status vocabulary live here. A contract does not grant tool
access: the existing gateway, action-intent and task budgets still apply.
"""

import json
from dataclasses import dataclass


def _invalid(message):
    from .workflow_source_execution import _invalid as error

    return error(
        message, "Review the saved reconciliation contract and operation receipt."
    )


def _path(value):
    return (
        isinstance(value, list)
        and 1 <= len(value) <= 8
        and all(isinstance(key, str) and key and len(key) <= 80 for key in value)
    )


def at(value, path):
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def equal(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def validate_reconciliation_contracts(value, *, agent_task, allowed_tools):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            raise _invalid("MCP reconciliation contracts must be JSON.") from None
    if not isinstance(value, dict) or len(value) > 8 or (value and not agent_task):
        raise _invalid("Use at most eight reconciliation contracts on an MCP task.")
    keys = {
        "pending_status_path",
        "pending_status_values",
        "terminal_status_values",
        "receipt_path",
        "argument_bindings",
        "fixed_arguments",
        "max_polls",
    }
    for tool, spec in value.items():
        if tool not in allowed_tools or not isinstance(spec, dict) or set(spec) != keys:
            raise _invalid("Bind each reconciliation contract to a selected tool.")
        values = spec["pending_status_values"]
        terminal = spec["terminal_status_values"]
        bindings = spec["argument_bindings"]
        fixed = spec["fixed_arguments"]
        if (
            not _path(spec["pending_status_path"])
            or not _path(spec["receipt_path"])
            or not isinstance(values, list)
            or not 1 <= len(values) <= 8
            or any(not isinstance(v, str) or not v or len(v) > 80 for v in values)
            or len(set(values)) != len(values)
            or not isinstance(terminal, list)
            or not 1 <= len(terminal) <= 8
            or any(not isinstance(v, str) or not v or len(v) > 80 for v in terminal)
            or len(set(terminal)) != len(terminal)
            or set(values) & set(terminal)
            or not isinstance(bindings, dict)
            or not 1 <= len(bindings) <= 8
            or any(
                not isinstance(k, str) or not k or not _path(p)
                for k, p in bindings.items()
            )
            or not isinstance(fixed, dict)
            or len(fixed) > 16
            or any(
                not isinstance(k, str)
                or not k
                or not isinstance(v, (str, int, float, bool, type(None)))
                for k, v in fixed.items()
            )
            or type(spec["max_polls"]) is not int
            or not 1 <= spec["max_polls"] <= 8
        ):
            raise _invalid(
                "Declare bounded status paths, receipt identity and exact argument constraints."
            )
    return value


@dataclass
class PendingOperation:
    receipt: str | int
    pending: bool
    polls: int = 0


class ReconciliationTracker:
    def __init__(self, contracts):
        self.contracts = contracts
        self.operations = {}

    def permit_repeat(self, signature, tool_name):
        operation = self.operations.get(signature)
        if not operation or not operation.pending:
            return False
        if operation.polls >= self.contracts[tool_name]["max_polls"]:
            raise _invalid(
                "The declared pending-operation observation budget is exhausted."
            )
        operation.polls += 1
        return True

    def observe(self, signature, tool_name, arguments, result):
        spec = self.contracts.get(tool_name)
        if spec is None:
            return None
        old = self.operations.get(signature)
        status = at(result, spec["pending_status_path"])
        pending = status in spec["pending_status_values"]
        if not pending and old is None:
            return None
        if not pending and status not in spec["terminal_status_values"]:
            raise _invalid(
                "The existing operation returned no declared pending or terminal state."
            )
        receipt = at(result, spec["receipt_path"])
        matches = all(
            key in arguments
            and equal(arguments[key], at(result, path))
            and arguments[key] is not None
            for key, path in spec["argument_bindings"].items()
        ) and all(
            key in arguments and equal(arguments[key], expected)
            for key, expected in spec["fixed_arguments"].items()
        )
        if (
            not matches
            or type(receipt) not in (str, int)
            or receipt == ""
            or (old is not None and not equal(old.receipt, receipt))
        ):
            raise _invalid(
                "The pending-operation receipt or exact request identity could not be reconciled."
            )
        self.operations[signature] = PendingOperation(
            receipt, pending, old.polls if old else 0
        )
        return {
            "receipt": receipt,
            "pending": pending,
            "observed_status": status,
            "polls": old.polls if old else 0,
            "maximum_polls": spec["max_polls"],
        }
