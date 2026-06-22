# Data Model: Hermes Wright Plugin Skeleton

This feature does not introduce database tables or persistent relational entities. However, it defines schemas for configuration files, manifest models, and the plugin entry point signature.

## Configurations & Schemas

### 1. Plugin Manifest (`plugin.yaml`)
The Hermes plugin manifest configuration structure.

| Field | Type | Required | Description / Constraints |
|---|---|---|---|
| `name` | string | Yes | Must be `"wright"`. |
| `version` | string | Yes | Initial version `"1.0.0"`. |
| `description` | string | Yes | Brief description of the Wright plugin. |
| `author` | string | Yes | Author information. |
| `license` | string | Yes | Project license (e.g., `MIT`). |
| `homepage` | string | Yes | Repository URL. |
| `capabilities` | list[string]| Yes | Must include `"commands"` to support the slash command namespace. |
| `min_hermes_version`| string | Yes | Minimum compatible Hermes version (e.g., `"1.0.0"`). |

### 2. Entry Point Interface (`register`)
The function signature called by the Hermes Plugin Manager.

```python
def register(ctx: object) -> None:
    """
    Main registration hook called on load.
    
    Args:
        ctx: The Hermes plugin registration context object, 
             providing methods to register commands, providers, etc.
    """
```

### 3. Package Distribution Metadata (`pyproject.toml`)
Metadata defining the PyPI installable structure.

* **Package Name**: `hermes-plugin-wright`
* **Python Target**: `>=3.11`
* **Build System**: `hatchling`
* **Dependencies**:
  * `httpx>=0.27`
  * `pyyaml>=6.0`
  * `pydantic>=2.0`
* **Entry Point Mapping**:
  * Group: `"hermes_agent.plugins"`
  * Name: `wright`
  * Value: `hermes_plugin_wright:register`
