# Wright with Hermes Desktop

Hermes Desktop uses the same production Git adapter as Hermes CLI. Wright does
not modify Hermes, copy files into Desktop by hand, or require a source checkout.

Install and enable the adapter through Hermes:

```text
hermes plugins install https://github.com/burhop/hermes-plugin-wright --enable
```

Restart Desktop if it does not rescan newly installed plugins, then run:

```text
/wright start
/wright status
/wright doctor
```

Git is required by Hermes for adapter installation and update. Wright's runtime
and retained data live under `WRIGHT_HOME` (default `~/.wright`), not under
Hermes state or a repository. The first start creates the contained runtime and
returns the UI URL.

Wright's LLM status is separate from the Hermes gateway. Configure the chosen
local or hosted OpenAI-compatible endpoint through approved Hermes or Wright
configuration; credentials never belong in logs, artifacts, or release
evidence.

Hermes exposes no pre-remove hook. To remove runtime code as well as the
adapter, use:

```text
/wright uninstall
hermes plugins remove wright
```

Default uninstall preserves `WRIGHT_HOME/data`. Use `/wright purge` and then
`/wright purge <confirmation-code>` only when you intend to delete the exact
disclosed Wright-owned data path.
