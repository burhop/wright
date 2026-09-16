"""Selected offline ROS tracking MCP; fixed operations, confined workspace files."""
from pathlib import Path
import os
from mcp.server.fastmcp import FastMCP
import robot_tracking_operations as operations

ROOT = Path(os.environ["WRIGHT_ROBOT_WORKSPACE"]).resolve()
mcp = FastMCP("wright-offline-robot-tracking")


def confined(relative):
    if Path(relative).is_absolute():
        raise ValueError("Workspace-relative paths required")
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Path escapes enrolled workspace")
    return path


def authorize_source(operation_source_document, input_path, output_path):
    snapshot = confined(operation_source_document)
    if operations.sha(snapshot) != operations.sha(operations.__file__):
        raise ValueError("Staged operation source differs from the executing selected operation")
    attempt = snapshot.parent.parent
    if snapshot.parent.name != "inputs" or not input_path.is_relative_to(attempt) or not output_path.is_relative_to(attempt / "artifacts"):
        raise ValueError("Inputs/source and outputs must share the same explicit campaign attempt")


@mcp.tool()
def normalize_csv_to_ros2(input_directory: str, output_directory: str, operation_source_document: str) -> dict:
    """Serialize uploaded CSVs to real ROS2 CDR bag; preserve header/frame offsets and original files. Output must be new."""
    inputs, output = confined(input_directory), confined(output_directory)
    authorize_source(operation_source_document, inputs, output)
    return operations.convert_csv_to_bag(inputs, output)


@mcp.tool()
def calculate_tracking_metrics(bag_directory: str, alignment_document: str, output_directory: str, operation_source_document: str) -> dict:
    """Read actual bag messages, apply explicit survey/time alignment, save timeline/overlay/metrics/source; enforce 1% independent metrics and event within one sample. No robot access."""
    bag, alignment, output = confined(bag_directory), confined(alignment_document), confined(output_directory)
    authorize_source(operation_source_document, bag, output)
    authorize_source(operation_source_document, alignment, output)
    return operations.analyze_tracking_bag(bag, alignment, output)


if __name__ == "__main__":
    mcp.run(transport="stdio")
