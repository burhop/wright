# Interface Contracts: FreeCAD MCP Tools

This document defines the JSON-RPC tool schemas exposed by the FreeCAD MCP server.

## 1. tool: `freecad_status`
- **Type**: `read` (no parameters)
- **Response Schema**:
  ```json
  {
    "success": true,
    "freecad_ok": true,
    "version": "FreeCAD 1.1.1, build ...",
    "bridge_mode": "tcp" | "subprocess",
    "work_dir": "/tmp/freecad_mcp_work"
  }
  ```

## 2. tool: `step_to_stl`
- **Type**: `write`
- **Request Parameters**:
  ```json
  {
    "file_name": "bracket.step",
    "output_name": "bracket.stl"
  }
  ```
- **Response Schema**:
  ```json
  {
    "success": true,
    "output": "bracket.stl",
    "data": {
      "objects": 1,
      "size_kb": 124.5
    }
  }
  ```

## 3. tool: `create_shape`
- **Type**: `write`
- **Request Parameters**:
  ```json
  {
    "shape_type": "box" | "cylinder" | "sphere" | "cone",
    "params": {
      "width": 10.0,
      "height": 20.0,
      "depth": 5.0
    },
    "output_name": "box.stl"
  }
  ```
- **Response Schema**:
  ```json
  {
    "success": true,
    "output": "box.stl",
    "data": {
      "type": "box",
      "volume": 1000.0,
      "bbox": {
        "xmin": 0, "xmax": 10,
        "ymin": 0, "ymax": 20,
        "zmin": 0, "zmax": 5
      }
    }
  }
  ```

## 4. tool: `model_info`
- **Type**: `read`
- **Request Parameters**:
  ```json
  {
    "file_name": "bracket.step"
  }
  ```
- **Response Schema**:
  ```json
  {
    "success": true,
    "data": {
      "objects": [
        {
          "name": "BasePart",
          "solids": 1,
          "volume": 25000.0,
          "bbox": {
            "xmin": -50.0, "xmax": 50.0,
            "ymin": -50.0, "ymax": 50.0,
            "zmin": 0.0, "zmax": 10.0
          }
        }
      ],
      "total": 1
    }
  }
  ```
