"""Measure retained original images plus saved review instructions; no run or model call."""

import base64
import hashlib
import json
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(p) for p in (root / "packages").glob("*/src")]
    from workspace_service.workflow_source_execution import compile_prompt_workflow
    from agent_adapters.workflow_instructions import workflow_response_instructions
    from core.process_validation import canonical_json

    source = (
        root
        / "examples/stevecad-demonstrations/prompt-to-reviewed-cad/prompt-to-reviewed-cad-native.workflow.wflow"
    )
    workflow = compile_prompt_workflow(source.read_text())
    step = next(s for s in workflow.steps if s.id == "design_review")
    instructions = workflow_response_instructions(
        step.output_format,
        instruction_set=step.instruction_set,
        instruction_override=step.instruction_override,
    )
    records = []
    for case in ("block-native-006", "six-hole-native-001"):
        directory = (
            root
            / "artifacts/stevecad-demonstrations/prompt-to-reviewed-cad"
            / case
            / "outputs"
        )
        documents = [
            directory / name
            for name in (
                "design_document.md",
                "test_plan.md",
                "create_design.json",
                "validate_design.json",
            )
        ]
        prompt = (
            step.prompt
            + "\n\n"
            + "\n\n".join(p.name + "\n" + p.read_text() for p in documents)
        )
        content = [{"type": "text", "text": prompt}]
        for name in (
            "cad-isometric.png",
            "cad-top.png",
            "cad-front.png",
            "render_isometric.png",
            "render_top.png",
            "render_front.png",
        ):
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,"
                        + base64.b64encode((directory / name).read_bytes()).decode()
                    },
                }
            )
        payload = {
            "messages": [
                {"role": "system", "content": instructions.text},
                {"role": "user", "content": content},
            ],
            "tools": [],
            "tool_choice": "none",
        }
        encoded = canonical_json(payload).encode()
        records.append(
            {
                "case": case,
                "serialized_bytes": len(encoded),
                "payload_sha256": hashlib.sha256(encoded).hexdigest(),
                "text_bytes": len(prompt.encode()) + len(instructions.text.encode()),
                "image_count": 6,
            }
        )
    print(
        json.dumps(
            {
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "scope": "Saved compiled review instructions plus four retained documents and six original images. Diagnostic assembly, not a runtime-resolved complete request: export identity, render geometry result and runtime framing are not included.",
                "measurements": records,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
