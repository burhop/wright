"""Administrative bounds; generated source cannot change its build envelope."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProcessInterfaceLimits:
    inline_bytes: int = 65_536
    maximum_upload_bytes: int = 33_554_432
    maximum_input_request_bytes: int = 67_108_864
    maximum_source_bytes: int = 1_048_576
    maximum_asset_bytes: int = 10_485_760
    maximum_bundle_bytes: int = 31_457_280
    maximum_source_files: int = 32
    maximum_page_items: int = 256
    maximum_diagnostics: int = 64
    compiler_timeout_seconds: int = 120
    maximum_repairs: int = 2

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if type(value) is not int or value < (
                0 if name == "maximum_repairs" else 1
            ):
                raise ValueError(
                    "Process interface limits must be finite positive integers"
                )
        if self.maximum_repairs > 2:
            raise ValueError("Authoring may attempt at most two corrections")
        if (
            self.maximum_source_files > 32
            or self.maximum_page_items > 256
            or self.maximum_diagnostics > 64
        ):
            raise ValueError("Administrative limits must fit the versioned contract")
