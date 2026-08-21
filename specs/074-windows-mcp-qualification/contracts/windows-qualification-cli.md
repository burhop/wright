# Contract: Windows Qualification CLI

The operator interface is separate from the default Docker validation command.
It is opt-in and refuses non-Windows hosts and non-allowlisted identities.

## Preview

```text
python -m tool_registry.windows_qualification_cli preview SERVER_ID
  --evidence-dir PATH
```

Preview loads the signed catalog entry and declarative recipe, performs no
network/process/install/onboarding action, and emits the recipe digest, source,
required boundaries, risks, planned stages, and current safety-decision state.

## Qualify one server

```text
python -m tool_registry.windows_qualification_cli qualify SERVER_ID
  --evidence-dir PATH
  --work-root PATH
  --safety-decision PATH
```

The command MUST:

1. enforce the exact allowlist before resolving the recipe;
2. require native Windows and a validated safety decision bound to the recipe;
3. verify work/evidence roots are explicit and work root is not a repository,
   user-home, drive-root, system, program-files, or other broad directory;
4. execute typed operations without a command shell;
5. checkpoint after each stage and always attempt cleanup;
6. write redacted JSON and Markdown and print only safe identities/paths.

Exit status is zero only for infrastructure completion, not only when all stages
pass. A factual partial/blocked/obsolete server still completes its checkpoint.
Schema/allowlist/safety/cleanup infrastructure failures use a nonzero exit.

## Qualify ordered allowlist

```text
python -m tool_registry.windows_qualification_cli qualify-all
  --evidence-dir PATH
  --work-root PATH
  --decisions-dir PATH
```

The command processes the fixed order, cleans after every entry, continues on
external boundaries, and writes matrix/progress/install/cleanup/non-allowlist
ledgers after every checkpoint. It never accepts an additional server ID.

## Sensitive output

Commands, environment values, credentials, private paths, raw tool arguments,
and subprocess streams are not printed or persisted. Evidence stores digests,
counts, bounded public identities, classifications, and recovery guidance.

