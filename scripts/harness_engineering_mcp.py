"""Confined fixed engineering MCP for the explicit WireViz harness substitute."""
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP
import harness_engineering_operations as operation

ROOT = Path(os.environ["WRIGHT_HARNESS_WORKSPACE"]).resolve()
mcp = FastMCP("wright-harness-wireviz")


def path(relative):
    if Path(relative).is_absolute():
        raise ValueError("Workspace relative path required")
    result=(ROOT/relative).resolve()
    if not result.is_relative_to(ROOT):
        raise ValueError("Workspace path escape")
    return result


def check(source_document, output_directory, *inputs):
    source=path(source_document)
    if operation.sha(source) != operation.sha(operation.__file__):
        raise ValueError("Staged operation source differs from selected executable")
    attempt=source.parent.parent
    output=path(output_directory)
    if source.parent.name != "inputs" or not output.is_relative_to(attempt/"artifacts") or any(not path(item).is_relative_to(attempt) for item in inputs):
        raise ValueError("Inputs and outputs must share the exact campaign attempt")
    return output


@mcp.tool()
def retrieve_harness_component_records(source_specification: str, output_directory: str, operation_source_document: str) -> dict:
    """Retrieve reviewed primary manufacturer connector/wire/terminal/tool documents, retain actual bytes/hashes and unresolved ratings. HTTPS read only; no accounts or purchases."""
    output=check(operation_source_document,output_directory,source_specification)
    return operation.retrieve_records(path(source_specification),output)


@mcp.tool()
def generate_harness_package(input_directory: str, design_document: str, research_directory: str, output_directory: str, operation_source_document: str) -> dict:
    """Generate actual native WireViz/Graphviz source, diagram/BOM plus exact cut/pin/assembly files from uploaded schedule and retrieved source facts. No fixture or Splice output."""
    output=check(operation_source_document,output_directory,input_directory,design_document,research_directory)
    return operation.synthesize(path(input_directory),path(design_document),path(research_directory),output)


@mcp.tool()
def verify_harness_package(input_directory: str, research_directory: str, generated_directory: str, output_directory: str, operation_source_document: str) -> dict:
    """Independently inspect actual emitted WireViz netlist; check opens/shorts/reserves/shared currents, nominal ratings and loaded copper drop. Missing contact/derating evidence produces explicit release HOLD, never false electrical approval."""
    output=check(operation_source_document,output_directory,input_directory,research_directory,generated_directory)
    return operation.independent_verify(path(input_directory),path(research_directory),path(generated_directory),output)


if __name__ == "__main__":
    mcp.run(transport="stdio")
