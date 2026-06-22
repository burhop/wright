# Interface Contracts: Wright Hermes Plugin

This document specifies the interfaces exposed by the `hermes-plugin-wright` package to the Hermes Agent loader and the slash command subsystem.

## 1. Hermes Plugin Manager Contract (Python Entry Point)

The Hermes Agent loads plugins dynamically via PEP 517/518 entry point discovery.

* **Entry Point Group**: `hermes_agent.plugins`
* **Entry Point Name**: `wright`
* **Target Function**: `hermes_plugin_wright:register`

### Signature
```python
def register(ctx: RegistrationContext) -> None:
    ...
```

### RegistrationContext Protocol
The `ctx` object passed by Hermes is expected to conform to the following minimal interface (to be utilized in subsequent features):

```python
class RegistrationContext:
    def register_command(self, name: str, handler: callable, description: str = "") -> None:
        """Registers a slash command handler."""
        ...
```

---

## 2. Slash Command Namespace Contract

The plugin declares its command namespace inside the `plugin.yaml` manifest.

* **Command Namespace**: `/wright`
* **Syntax**: `/wright [subcommand] [arguments]`
* **Initial State**: Registered but inactive (no subcommands are wired up in the skeleton phase, only the namespace capability is declared).
