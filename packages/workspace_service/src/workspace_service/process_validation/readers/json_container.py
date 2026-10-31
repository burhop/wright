"""Select one explicitly declared JSON string inside an exact JSON artifact.

No envelope inference, model rewriting, provider protocol or recursive decoding.
The original artifact remains the hashed subject; both selectors are evidence.
"""

from core.process_validation import ReaderIdentity, canonical_digest

from .base import ValidationIssue
from .structured import StructuredReader, _check_structure, _invalid, _pointer


class JsonContainerReader(StructuredReader):
    identity = ReaderIdentity(
        id="structured-json-container",
        version="1",
        config_digest=canonical_digest(
            {"parser": "json-string-container", "version": 1}
        ),
        method="structured_value",
        formats=("json",),
    )

    def _json_value(self, text, check, context):
        pointer = check.parameters.get("json_container_pointer")
        if not isinstance(pointer, str) or not pointer.startswith("/"):
            raise ValidationIssue(
                "profile.json_container",
                "Declare a JSON pointer to one JSON-encoded string in the artifact.",
                category="source_conflict",
            )
        outer = super()._json_value(text, check, context)
        _check_structure(outer, context)
        inner = _pointer(outer, pointer)
        if not isinstance(inner, str):
            raise _invalid(
                "The declared JSON container must contain a JSON-encoded string.",
                "output.json_container_type",
            )
        return super()._json_value(inner, check, context)

    def measure(self, snapshot, check, context):
        measurement = super().measure(snapshot, check, context)
        pointer = check.parameters["json_container_pointer"]
        return measurement.model_copy(
            update={
                "evidence_refs": (
                    f"subject:{snapshot.subject.id}@{snapshot.subject.sha256}"
                    f"#{pointer}::json#{check.selector}",
                    *measurement.evidence_refs[1:],
                )
            }
        )
