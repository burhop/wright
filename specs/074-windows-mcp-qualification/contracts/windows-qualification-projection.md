# Contract: Windows Qualification Catalog Projection

`CapabilityDetail.windows_qualification` is optional. Absence means no current
structured Windows evidence is bundled; it does not imply failure.

When present it contains:

- `observed_at`, `evidence_path`, `evidence_digest`
- `current` and bounded `stale_reasons`
- `source`, `package_or_registration`, `startup`, `protocol`,
  `host_or_backend`, `wright_setup`, `gateway`, and `cleanup`
- each group has one required result value, a short engineer-facing label, and a
  stable reason code
- optional exact `claim`

The UI MUST:

1. title the section “Tested on this Windows setup” when current and “Windows
   test needs to be rerun” when stale;
2. describe remote setup as registration/connection rather than installation;
3. say “MCP server installed; host app needed” when package/protocol passed but
   the commercial host is absent;
4. keep gateway and backend results visible separately;
5. expose the validation date and evidence reference;
6. never replace these results with a single `Compatible`/`Incompatible` badge;
7. use existing design tokens, semantic status colors, keyboard structure, and
   stable `data-testid` attributes.

The catalog loader validates the evidence digest/path format and claim rule.
Raw evidence, commands, environment material, private paths, and output are not
part of this projection.
