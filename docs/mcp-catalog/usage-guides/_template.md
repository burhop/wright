# <Provider name> MCP usage guide

Last updated: <date>. Guide status: <installed / protocol verified / engineering
use verified, with exact scope>.

## Identity and sources

- Independent provider and official documentation: <links>.
- Catalog entry and setup recipe: <links>.
- Observed server/package/native-host versions and source revision: <values>.
- Environment and qualification evidence: <platform, date, links>.
- Local registration identifiers, if needed for evidence, are environment-specific;
  rediscover and bind actual tool schemas on another installation.

## Installation and readiness

Record required host software, credentials mechanism without credential values,
platform support, paths/mounts, units and other predictable inputs. Record what
installation, initialization and tool discovery actually established. State any
missing capability and its diagnostic. Link the existing setup recipe.

## Verified workflows and successful calls

For each actual use, record the engineering job, tool names and observed schemas,
the minimum successful sequence, exact nonsecret input examples, outputs, units,
coordinate conventions, resource/revision identities and evidence links. Explain
how to check real tool results, including nested native errors, and how the next
tool consumes the outputs. Do not mark a listed tool verified without using it.

## Pitfalls and recovery

Record observed mistakes, their causes, exact diagnostics and verified fixes.
Distinguish invalid caller inputs, missing prerequisites and provider defects.
Describe how to observe an existing operation after an uncertain timeout, what
constitutes terminal evidence, and when a fresh attempt is actually permitted.

## Validation, authority and limitations

Describe exact-output checks, tolerances, dependency invalidation and downstream
evidence. Separate transport success, artifact existence, digital compliance,
human review and physical acceptance. Record required external-action authority.
Label unsupported and untested capabilities explicitly.

## Bugs and follow-ups

Use the provider's supported channel for confirmed bugs. Link the redacted minimal
reproduction and exact expected/observed behavior, versions, inputs and outputs.
Record submission/report identity and status to prevent duplicates. An unsubmitted
packet remains unsubmitted. Feature requests and suspected bugs remain separate.

## Maintenance

After a server update or a new lesson, record the date, affected versions and new
evidence. Retain historical findings with their scope. Add links to this guide
from the shared index and relevant catalog/setup/follow-up records.
