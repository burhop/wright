"""Transport envelopes; shared process contracts stay owned by core."""

from pydantic import Field

from core.process_interactions import InputBinding, Locator
from core.process_validation import Contract, Digest, Identifier


class ProcessSourceRequest(Contract):
    session_id: Identifier
    path: Locator
    expected_storage_digest: Digest


class SetProcessInputsRequest(ProcessSourceRequest):
    bindings: tuple[InputBinding, ...] = Field(default=(), max_length=256)


class ProcessReadinessRequest(ProcessSourceRequest):
    input_snapshot_id: Identifier
