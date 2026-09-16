# Structured correction demonstration

`20260916T202647Z/` is the retained evidence from an isolated canonical workflow
run against the configured Hermes model endpoint on 2026-09-16. The ordinary AI
producer created a controlled 98 mm value, received the validator's measured
feedback, created a distinct 100 mm revision, passed the pinned profile, and
released the consumer.

The run was produced with:

```powershell
.venv\Scripts\python.exe scripts/run_process_validation_structured_loop.py `
  --output-dir artifacts/process-validation/structured-loop/20260916T202647Z
```

The run directory keeps the source, both output revisions, both immutable
assessments, feedback delivery, run events, final result, model usage and release
note. `manifest.json` inventories every retained file by size and SHA-256. The
isolated SQLite database and nested workspace Git metadata were removed after
capture because they are runtime state rather than review evidence.

Verify the retained evidence without calling a model:

```powershell
.venv\Scripts\python.exe -m pytest `
  tests/external/process_validation/test_structured_loop_evidence.py -q
```
