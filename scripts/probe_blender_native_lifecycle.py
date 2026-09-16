"""Native lifecycle proof only; never runs mesh tools or awards campaign credit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import uuid4

from core.native_application import utc_now
from data_vault.migrations import upgrade_database
from data_vault.native_application_repository import NativeApplicationRepository
from tool_registry.native_application_blender import BlenderLifecycleError, BlenderNativeApplicationAdapter
from tool_registry.native_application_lifecycle import NativeApplicationLifecycle


def write(path, value):
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cycles", type=int, choices=(1, 2, 3), default=3)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    upgrade_database(args.database)
    repository = NativeApplicationRepository(str(args.database))
    adapter = BlenderNativeApplicationAdapter(allowed_roots=(output,))
    lifecycle = NativeApplicationLifecycle(repository, adapter)
    trace = "blender-lifecycle-proof-" + uuid4().hex
    result = {"kind": "native-lifecycle-diagnostic", "campaign_credit": False, "started_at": utc_now(),
              "safe_mode": True, "cycles": [], "preserved_dirty_witness": [], "errors": []}
    sessions = []

    def create(label):
        record = adapter.launch(args.executable, output / label)
        session = lifecycle.register_session(record, trace_id=trace)
        sessions.append(session)
        lease = lifecycle.acquire(session["session_id"], owner_id=trace, case_id="lifecycle-proof",
                                  attempt=label, trace_id=trace)
        operation = "create-empty-scene-" + label
        lifecycle.begin_operation(session["session_id"], lease["lease_id"], operation, trace_id=trace)
        try:
            created = adapter.create_document(session, "blank-scene-" + label)
            evidence = output / label / "creation.json"
            write(evidence, created)
            lifecycle.register_document(session["session_id"], lease["lease_id"], {
                "native_id": created["native_id"], "path": None, "dirty": True, "ownership": "owned",
                "preexisted": False, "creation_evidence": str(evidence), "case_id": "lifecycle-proof", "attempt": label,
                "recovery_path": str(output / label / "recovery.blend"),
            }, trace_id=trace)
            lifecycle.finish_operation(session["session_id"], operation, outcome="succeeded",
                                       evidence_reference=str(evidence), trace_id=trace)
        except Exception:
            lifecycle.finish_operation(session["session_id"], operation, outcome="unknown",
                                       evidence_reference=str(output / label / "control"), trace_id=trace)
            raise
        return session

    try:
        witness = create("borrowed-witness")
        # It is created by this probe for eventual owner cleanup, but presented
        # as borrowed to exercise preservation while other owned sessions cycle.
        borrowed = {**witness, "ownership": "borrowed"}
        before_requests = len(list((output / "borrowed-witness/control/requests").glob("*.json")))
        try:
            adapter.quit_application(borrowed)
            raise AssertionError("Borrowed witness accepted a quit operation")
        except BlenderLifecycleError as error:
            result["borrowed_quit_refused"] = str(error)
        assert before_requests == len(list((output / "borrowed-witness/control/requests").glob("*.json")))
        for index in range(1, args.cycles + 1):
            session = create(f"cycle-{index}")
            receipt = lifecycle.cleanup(session["session_id"], f"cleanup-{index}", reason="diagnostic_success", trace_id=trace)
            observation = adapter.inspect(session)
            assert receipt["status"] == "completed", receipt
            assert observation["alive"] is False and observation["endpoint_alive"] is False
            repeated = lifecycle.cleanup(session["session_id"], f"cleanup-{index}", reason="diagnostic_success", trace_id=trace)
            assert receipt == repeated
            result["cycles"].append({"session_id": session["session_id"], "identity": session["identity"],
                                     "version": session["version"], "cleanup": receipt, "post_cleanup": observation,
                                     "double_cleanup_identical": True})
            preserved = adapter.inspect(witness)
            assert preserved["alive"] and preserved["documents"][0]["dirty"]
            assert preserved["documents"][0]["native_id"] == "blank-scene-borrowed-witness"
            result["preserved_dirty_witness"].append(preserved)
            write(output / "acceptance.json", result)
    except Exception as error:
        result["errors"].append(f"{type(error).__name__}: {error}")
        raise
    finally:
        # Exact recorded owned sessions only; unresolved operations remain
        # quarantined by the lifecycle manager rather than forced closed.
        cleanup = []
        for session in sessions:
            cleanup.append(lifecycle.cleanup(session["session_id"], "final-diagnostic-cleanup", reason="diagnostic_finished", trace_id=trace))
        result["final_cleanup"] = cleanup
        result["finished_at"] = utc_now()
        write(output / "acceptance.json", result)
        print(json.dumps({"output": str(output), "cycles": len(result["cycles"]),
                          "cleanup_statuses": [row["status"] for row in cleanup], "errors": result["errors"]}))


if __name__ == "__main__":
    main()
