# CP3O Research — Block Interfaces and Hierarchical Composition

**Status**: Research captured; no implementation selected

**Date**: 2026-08-26
**Related evidence**: [CP3N left-input/right-output concept](cp3n-left-input-right-output-artifact-ports.md)

## Ambiguity being reduced

The artifact-placement concepts established that engineers should be able to
trace inputs into a block and outputs out of it. They did not yet establish:

1. what a port should look like or which part is connected, inspected, or
   opened;
2. how required, optional, collection, missing, running, produced, failed, and
   stale states should be represented;
3. whether data/artifact flow and execution/control flow should use the same
   notation; or
4. whether a group of blocks can collapse into one reusable block without
   introducing a second visual or execution model.

These questions matter independently of React Flow and independently of the
four-block fixture. The result must remain understandable for workflows with
fan-in, branches, feedback loops, many engineering disciplines, and multiple
levels of detail.

## Research hypothesis

A hybrid typed-port design will be more understandable than either tiny
anonymous sockets or full artifact cards. The same public interface can make a
primitive operation, a locally collapsed graph, a reusable subworkflow, and an
externally executed MCP action behave consistently at the parent level.

The smallest useful future experiment is a block-only comparison rather than a
complete executable workflow.

## Deliberate exclusions

- No production component, schema, renderer, or interaction is selected here.
- No graph-library behavior is treated as canonical Wright behavior.
- No CAD-, FEA-, CAM-, CFD-, PLM-, supplier-, or application-specific port is
  introduced.
- No recursive components, workflow persistence migration, or runtime
  scheduling semantics are designed here.
- No source code was changed as part of this research checkpoint.

## Industry evidence

| System                                                                                                                                           | Port/interface evidence                                                                                                                                | Composition evidence                                                                                                                                                                                  | Lesson for Wright                                                                                                                                |
| ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| [Dynamo](https://primer.dynamobim.org/en/03_Anatomy-of-a-Dynamo-Definition/3-1_dynamo_nodes.html)                                                | Data enters on the left and leaves on the right; ports expose expected types and hover descriptions; warning and error states are visible on the node. | [Custom nodes](https://primer.dynamobim.org/en/10_Custom-Nodes/10-2_Creating.html) turn a selected graph into a named node with public inputs and outputs and open the internal graph on demand.      | Left/right flow and nearby readable labels are strong defaults; detailed metadata can remain progressive.                                        |
| [Grasshopper](https://developer.rhino3d.com/en/guides/grasshopper/simple-parameters/)                                                            | Parameters can be input, output, or free-standing; type and access semantics distinguish individual items, lists, and trees.                           | Reusable clustered/user components expose parameter interfaces.                                                                                                                                       | Cardinality is part of the contract and should not be hidden inside an untyped wire.                                                             |
| [Unreal Blueprints](https://dev.epicgames.com/documentation/en-us/unreal-engine/nodes-in-unreal-engine)                                          | Execution pins and typed data pins are visually and semantically separate; compatible types guide connection behavior.                                 | [Collapsed graphs, functions, and macros](https://dev.epicgames.com/documentation/unreal-engine/collapsing-graphs-in-unreal-engine?lang=en-US) distinguish local organization from reusable behavior. | Do not make decisions/retries/control tokens look identical to files and data; local collapse and reusable components are different operations.  |
| [Simulink](https://www.mathworks.com/help/simulink/slref/subsystem.html)                                                                         | Subsystem inputs and outputs correspond to explicit internal Inport and Outport blocks and support engineering data types.                             | [Model references](https://www.mathworks.com/help/simulink/model-reference.html) provide reusable, independently testable components with defined external interfaces.                                | A composite must preserve a deliberate boundary contract; visual grouping alone must not silently change execution semantics.                    |
| [LabVIEW](https://www.ni.com/en/support/downloads/instrument-drivers/tools-resources/instrument-driver-guidelines/icon-and-connector-panes.html) | Connector panes favor left inputs, right outputs, aligned related terminals, and visible required/recommended/optional semantics.                      | A subVI uses the same connector contract as a primitive operation; changing a connector pattern can force callers to rewire.                                                                          | Stable port identity, order, and compatibility are product requirements for reusable components.                                                 |
| [Blender Geometry Nodes](https://docs.blender.org/manual/en/latest/interface/controls/nodes/groups.html)                                         | Group sockets define the external node interface and can be named, typed, ordered, and organized into panels.                                          | Node groups hide internal nodes while behaving like ordinary nodes; recursive node groups are prohibited.                                                                                             | Composite interfaces need deliberate curation and overflow organization; recursion should not be an early requirement.                           |
| [Node-RED](https://nodered.org/docs/user-guide/editor/workspace/subflows)                                                                        | Ports can be labeled and a node can expose runtime status.                                                                                             | A selected flow can become a reusable subflow that opens in another tab.                                                                                                                              | Opening a composite in a separate tab is understandable, but Node-RED's one-input constraint is not suitable for Wright's fan-in workflows.      |
| [OMG UML/SysML](https://www.omg.org/spec/SysML/2.0/Language/PDF)                                                                                 | Ports are typed connection points with direction and compatibility; UML lollipop/socket notation represents provided and required interfaces.          | Composite structures publish interfaces independently of their internal parts.                                                                                                                        | Lollipops are appropriate for capability/service compatibility, not for concrete photographs, documents, STEP files, or other runtime artifacts. |
| [LangGraph](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)                                                                       | Parent and child graphs communicate through explicit state schemas or adapter functions when schemas differ.                                           | A subgraph can execute as a node within a parent graph.                                                                                                                                               | Public component state should be smaller and more stable than internal execution state, with explicit adapters for mismatched schemas.           |

## Four concepts that must remain distinct

### Port definition

A static interface contract owned by the workflow definition. It includes a
stable identity, name, direction, data/artifact type, schema, cardinality,
requiredness, and compatibility rules. It exists before any run.

### Binding or connection

A static graph relationship from one output port to a compatible input port.
It answers where a value will come from, not whether the value currently
exists.

### Runtime artifact or value

The actual photograph set, prompt, document, model, table, message, or file
produced or consumed by one run. It has provenance, version, lifetime, and
available actions. It may be absent, pending, stale, failed, or produced while
the port and connection remain valid.

### Component definition and instance

A definition publishes an external interface. An instance binds that
definition into a parent workflow and may be pinned to a version. Its internal
graph and run evidence remain inspectable without leaking every internal value
onto the parent canvas.

Conflating these concepts caused earlier prototypes to use one small glyph for
connection, artifact existence, output inspection, and error state. The
production design should model them separately and render them together only
where that improves comprehension.

## Port treatments considered

| Treatment                    | Strengths                                                                                                | Weaknesses                                                                        | Provisional disposition                                 |
| ---------------------------- | -------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------- |
| Small circle/dot             | Compact, familiar, supports dense graphs                                                                 | Weak type and artifact cues, small target, difficult state inspection             | Retain as a comparison candidate, not the default       |
| Square engineering terminal  | Familiar in Simulink/LabVIEW-style systems, aligns well, works for composites                            | Can look like an electrical schematic when numerous                               | Retain as a strong base candidate                       |
| UML lollipop/socket          | Precise required/provided capability semantics                                                           | Commonly means an interface rather than a data instance; unfamiliar to many users | Reserve for a future advanced capability-binding view   |
| Fully labeled parameter rows | Excellent names, schemas, errors, and accessibility                                                      | Makes every canvas block large                                                    | Use in expanded/inspector views, not the default canvas |
| Artifact cards or rails      | Strong inspection and action affordances                                                                 | Duplicates the flow and competes visually with the graph                          | Do not use as an always-visible second workflow         |
| Hybrid typed port            | Combines a compact connection target, readable label/type cue, and separate artifact state/access target | Requires careful hit targets and progressive disclosure                           | Preferred hypothesis for the next experiment            |

## Preferred hypothesis: hybrid typed ports

The default block should place input sockets on the left and output sockets on
the right. A compact icon and short port name sit immediately inside the block.
The socket is the drag/connect target. The adjacent icon or artifact indicator
is the inspect/open target. Hover or keyboard focus reveals the full type,
schema, source, requiredness, cardinality, and current value state.

This preserves a block-to-block process reading while making the data crossing
each boundary explicit. The visible socket may be visually small, but its
interactive target must be large enough for reliable mouse, touchpad, and
keyboard use at normal zoom.

Suggested semantic states for testing, not final styling:

- optional and unconnected: neutral hollow socket;
- required and missing: red outlined socket plus readable error text;
- connected input available: filled or checked socket;
- pending/streaming: activity ring without claiming an artifact exists;
- produced: artifact indicator plus available action count;
- stale: amber/version cue because upstream inputs changed;
- failed: red failure cue attached to the failing production boundary;
- collection: stacked-item icon and count rather than multiple duplicate ports.

Color should communicate broad families and status only with a redundant icon,
shape, or label. Precise types belong in icons, names, and schemas rather than
dozens of port colors. Data/artifact connections should be visually distinct
from execution, approval, decision, and feedback control connections.

## Composition model

Wright should distinguish three composition operations:

1. **Local collapsed group** — visual organization inside one workflow. It is
   not shared, versioned, or silently promoted to a library component.
2. **Reusable workflow component** — a named, versioned definition with a
   deliberately published and compatibility-checked interface.
3. **External capability component** — an ordinary workflow block whose
   implementation is an exact MCP tool, local application, or governed external
   service. Its public ports remain domain-neutral even when its display title
   is engineer-friendly.

When collapsing a selection, each connection crossing the selection boundary
becomes a candidate public port. One external artifact feeding several internal
blocks should normally become one group input that fans out internally. One
internal output used by several external consumers should remain one public
output. The user reviews port name, type, order, cardinality, requiredness, and
default before the boundary is accepted.

The external anatomy and interaction must be the same whether a block contains
one operation or fifty. Double-clicking a primitive block opens its
configuration/results; double-clicking an artifact indicator opens the value;
double-clicking a composite block opens its internal graph in a tab with
breadcrumbs. These actions must remain distinct.

Reusable interfaces require stable port identities and version rules. Adding
an optional port may be compatible; removing, renaming, reordering by identity,
or narrowing a type may be breaking. Instances should be pinned to a definition
version and updated through a visible compatibility/migration review rather
than silently rewired.

## Failure and diagnosis across a composite boundary

A failed composite must not expose every internal detail on the parent canvas.
It should identify:

- which public output was not produced or is stale;
- which internal step is the current failure frontier;
- a short engineer-readable cause and recovery action; and
- an action to open the failing internal step and its evidence.

The parent view remains compact while evidence remains traceable. Internal
cycles and feedback may be permitted when the runtime semantics support them,
but direct or indirect recursive component containment should be excluded from
the first production design.

## Evidence, inference, and provisional decisions

**Evidence from mature systems**:

- left-input/right-output flow is a widespread engineering and computational
  design convention;
- typed sockets, cardinality, requiredness, and stable interfaces reduce
  ambiguity;
- data flow and control flow are often distinct;
- subgraphs/components can behave like ordinary nodes through published
  boundary interfaces; and
- local visual collapse and reusable component creation are materially
  different operations.

**Inference for Wright**:

- a hybrid socket plus readable label/artifact indicator should better balance
  density and inspectability than a pure dot or always-visible artifact rail;
- opening composite contents in another tab should preserve context better
  than expanding a large graph inline; and
- lollipop/socket notation is more likely to help capability binding than
  ordinary artifact flow.

These inferences require usability evidence before becoming production rules.

## Next experiment

Build a non-executing block laboratory containing the same semantic ports in
three treatments: simple dot, square engineering terminal, and hybrid typed
port. Exercise:

1. one required file input;
2. a collection of images;
3. optional context;
4. one produced document or model;
5. missing, incompatible, pending, produced, failed, and stale states;
6. keyboard focus and connection at normal and reduced zoom; and
7. one collapsed group shown beside its expanded graph.

Human tasks should measure whether an engineer can identify the missing input,
trace producer to consumer, distinguish control from data, open the current
artifact, enter a composite, and identify an internal failure without reading
raw schema or run JSON.

## Recommendation

- **Keep** the CP3N left-input/right-output direction and one canonical artifact
  identity across producer and consumer.
- **Revise** the current tiny artifact glyph into a tested port anatomy that
  separates connection, contract, and runtime artifact access.
- **Add** explicit local-collapse and reusable-component concepts with the same
  external block interface.
- **Defer** final shape, color, overflow, version-migration, recursion, and
  inline-versus-tab details until the block laboratory produces human evidence.
