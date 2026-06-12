import asyncio
import json
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def get_credentials():
    # Attempt to read from ~/.config/wright/mcp-secrets.json first
    secrets_path = Path.home() / ".config" / "wright" / "mcp-secrets.json"
    if secrets_path.exists():
        try:
            with open(secrets_path, "r") as f:
                data = json.load(f)
                server_secrets = data.get("jarvis-onshape-mcp", {})
                access_key = server_secrets.get("ONSHAPE_ACCESS_KEY")
                secret_key = server_secrets.get("ONSHAPE_SECRET_KEY")
                if access_key and secret_key:
                    return access_key, secret_key
        except Exception as e:
            print(f"Warning: Failed to read secrets file: {e}", file=sys.stderr)

    # Fallback to env vars
    access_key = os.environ.get("ONSHAPE_ACCESS_KEY")
    secret_key = os.environ.get("ONSHAPE_SECRET_KEY")
    return access_key, secret_key

async def main():
    access_key, secret_key = get_credentials()
    if not access_key or not secret_key:
        print("Error: ONSHAPE_ACCESS_KEY and ONSHAPE_SECRET_KEY must be set in ~/.config/wright/mcp-secrets.json or as environment variables.", file=sys.stderr)
        sys.exit(1)

    # Define the stdio command for jarvis-onshape-mcp
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "--with", "git+https://github.com/ReshefElisha/jarvis-onshape-mcp.git", "onshape-mcp"],
        env={
            "ONSHAPE_ACCESS_KEY": access_key,
            "ONSHAPE_SECRET_KEY": secret_key,
            "PATH": os.environ.get("PATH", ""),
        }
    )

    print("Connecting to jarvis-onshape-mcp server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            print("Initializing session...")
            await session.initialize()
            
            # Create a new document
            print("1. Creating Onshape document 'MCP Cube Demo'...")
            create_doc_res = await session.call_tool("create_document", {"name": "MCP Cube Demo", "isPublic": True})
            
            if not create_doc_res.content:
                raise ValueError("Failed to create document: Empty response")
            
            doc_info = json.loads(create_doc_res.content[0].text)
            print("Created Document Info:", json.dumps(doc_info, indent=2))
            
            document_id = doc_info["document_id"]
            workspace_id = doc_info["workspace_id"]
            element_id = doc_info["part_studio_id"]
            
            # Create a sketch rectangle on the Top plane
            print("\n2. Creating sketch rectangle on Top plane...")
            sketch_res = await session.call_tool("create_sketch_rectangle", {
                "documentId": document_id,
                "workspaceId": workspace_id,
                "elementId": element_id,
                "plane": "Top",
                "corner1": [-10, -10],
                "corner2": [10, 10],
                "name": "Base Sketch"
            })
            
            sketch_info = json.loads(sketch_res.content[0].text)
            print("Sketch Info:", json.dumps(sketch_info, indent=2))
            
            sketch_feature_id = sketch_info.get("feature_id") or sketch_info.get("featureId") or sketch_info.get("sketchFeatureId")
            if not sketch_feature_id:
                raise ValueError(f"Could not retrieve sketchFeatureId from: {sketch_info}")
                
            print(f"Sketch Feature ID: {sketch_feature_id}")
            
            # Extrude the sketch to form a 20mm cube
            print("\n3. Extruding sketch...")
            extrude_res = await session.call_tool("create_extrude", {
                "documentId": document_id,
                "workspaceId": workspace_id,
                "elementId": element_id,
                "sketchFeatureId": sketch_feature_id,
                "depth": 20,
                "name": "Cube Extrude"
            })
            
            extrude_info = json.loads(extrude_res.content[0].text)
            print("Extrude Info:", json.dumps(extrude_info, indent=2))
            
            # Export the Part Studio to STL
            print("\n4. Exporting Part Studio to STL...")
            export_res = await session.call_tool("export_part_studio", {
                "documentId": document_id,
                "workspaceId": workspace_id,
                "elementId": element_id,
                "format": "STL"
            })
            
            raw_text = export_res.content[0].text
            print(f"Raw Export Response text: {raw_text}")
            try:
                export_info = json.loads(raw_text)
                print("Export Info:", json.dumps(export_info, indent=2))
                file_path = export_info.get("localFilePath") or export_info.get("path") or export_info.get("filePath")
            except Exception:
                # Extract path from raw text lines like "Path: /tmp/..."
                file_path = None
                for line in raw_text.splitlines():
                    if line.strip().lower().startswith("path:"):
                        file_path = line.split(":", 1)[1].strip()
                        break
                if not file_path:
                    file_path = raw_text.strip()
            
            print(f"\nSuccess! STL file exported to: {file_path}")

if __name__ == "__main__":
    asyncio.run(main())
