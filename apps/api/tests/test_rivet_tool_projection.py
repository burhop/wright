from api.routers.workspace import _project_rivet_output_schema


def test_rivet_output_projection_exposes_bounded_nested_result_paths() -> None:
    schema = {
        "type": "object",
        "properties": {
            "result": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "providerId": {"type": "string"},
                        "isDefault": {"type": "boolean"},
                    },
                },
            }
        },
    }

    assert _project_rivet_output_schema(schema) == {
        "type": "object",
        "paths": [
            {"path": "result[].providerId", "type": "string"},
            {"path": "result[].isDefault", "type": "boolean"},
        ],
    }


def test_rivet_output_projection_limits_child_schema_size() -> None:
    schema = {
        "type": "object",
        "properties": {
            f"field{index}": {"type": "string"} for index in range(100)
        },
    }

    projected = _project_rivet_output_schema(schema, maximum_paths=5)

    assert projected is not None
    assert len(projected["paths"]) == 5
