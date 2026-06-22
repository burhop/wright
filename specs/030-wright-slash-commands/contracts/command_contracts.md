# Contracts: Command Routing Interfaces

This document defines the interface and routing contracts for the `/wright` slash commands.

---

## 1. Hermes Command Callback Signature

The command module must register the command under the name `wright` with the Hermes plugin context. The callback follows this asynchronous function contract:

```python
async def handle_wright_command(ctx: Any, args: List[str]) -> str:
    """
    Main entry point callback for /wright slash commands.
    
    Args:
        ctx: The Hermes execution context (provides session and registration tools).
        args: List of command-line token parameters entered by the user.
        
    Returns:
        A Markdown-formatted string containing the command output response or help menu.
    """
```

---

## 2. Command Dispatch Schema

The command parser maps tokens to specific handler methods:

| Subcommand Pattern | Callback Method | Argument Constraints |
|:---|:---|:---|
| `start` | `handle_start()` | No arguments |
| `stop` | `handle_stop()` | No arguments |
| `open` | `handle_open()` | No arguments |
| `doctor` | `handle_doctor()` | No arguments |
| `status` | `handle_status()` | No arguments |
| `catalog` | `handle_catalog_list()` | Optional: `[domain]` tag filter |
| `catalog search <query>` | `handle_catalog_search()` | Requires: `<query>` string |
| `info <id>` | `handle_info()` | Requires: `<id>` tool identifier |
| `install <id>` | `handle_install()` | Requires: `<id>` tool identifier |
| *(unknown / empty)* | `handle_help()` | Default fallback |

---

## 3. Output Formats and Layout Contracts

All returns MUST be standard GitHub Flavored Markdown (GFM) strings.

### A. Catalog List Layout
Command: `/wright catalog`
```markdown
| ID | Tool Name | Locality | Weight |
|:---|:---|:---|:---|
| `calculix` | CalculiX FEA | local | heavy |
| `freecad` | FreeCAD | local | medium |
```

### B. Info Details Layout
Command: `/wright info <id>`
```markdown
### 🛠️ CalculiX FEA (`calculix`)
* **Vendor**: CalculiX Project
* **Domains**: cad, fea
* **Locality**: local (Weight: heavy)
* **Transport**: stdio

#### Description
Finite Element Analysis tool for structural mechanics...

#### Execution Command
```bash
ccx -i job
```

#### Dependencies
- **System**: gfortran, make
```

### C. Status Dashboard Layout
Command: `/wright status`
```markdown
### 🌐 Wright Status
* **API Connection**: ● Connected (http://127.0.0.1:8000)
* **Active Workspace**: My CAD Project (`/path/to/workspace`)

#### 🛠️ Configured MCP Tools
* ● **freecad** (active)
* ○ **onshape** (needs action - missing ONSHAPE_API_KEY)
* 🔴 **calculix** (inactive)
```
