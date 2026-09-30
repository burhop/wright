# Spec-Kit Workflow

Wright enforces a **Spec-Driven Development** methodology using the **Spec Kit** agentic protocol. This ensures that features are fully specified, planned, and reviewed before any code files are modified.

Applicable features must also follow the agreed
[workflow platform vision](../design/workflow-platform-vision.md). The spec,
plan, and task templates start from the user journey and capture ownership,
reused mechanisms, revision/evidence behaviour, and checks for unintended domain
coupling. Process UI features follow the [process UI design](../design/process-apps.md):
an interaction contract, shared Wright kit/client, workspace-tab hosting, saved
UI bindings, and a common-view fallback on the existing runtime. Prefer existing
MCP providers; provider-specific workarounds do not define the platform roadmap.
Keep that guidance outside
the managed Spec Kit block in `AGENTS.md` so a context refresh preserves it.
Record a feature's actual supported scope; a reference workflow does not define
the platform's required process or prove every integration. The current print
prototype's [refactoring plan](../architecture/workflow-platform-refactoring-plan.md)
is a follow-on proposal, not an amendment to historical feature evidence.

---

## 1. What is Spec Kit?

Spec Kit is a set of standardized agentic slash commands and templates that track feature design files inside the `.specify/` and `specs/` directories of the repository.

Every feature under development has a dedicated folder under `specs/<feature-name>/`:
*   `spec.md`: High-level user scenarios and acceptance criteria.
*   `plan.md`: Technical implementation choices, dependency checks, and architecture.
*   `research.md`: Decisions, tradeoffs, and alternative selections.
*   `data-model.md`: Data schemas, tables, and folder maps.
*   `tasks.md`: Structured, step-by-step TODO lists for coding.
*   `checklists/requirements.md`: Feature specification quality lists.

---

## 2. Standard Development Life Cycle

Developers and coding agents walk through five sequential workflow phases:

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ 1. Specify   │ ───> │  2. Clarify  │ ───> │   3. Plan    │
│  (/specify)  │      │  (/clarify)  │      │   (/plan)    │
└──────────────┘      └──────────────┘      └──────────────┘
                                                   │
                                                   ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  6. Commit   │ <─── │ 5. Implement │ <─── │   4. Tasks   │
│  (/commit)   │      │ (/implement) │      │   (/tasks)   │
└──────────────┘      └──────────────┘      └──────────────┘
```

### Phase 1: `/speckit-specify`
Initializes a new feature spec template. The developer outlines what needs to be built in plain markdown.

### Phase 2: `/speckit-clarify`
Runs an automated consistency check to identify vague specifications or missing requirements, resolving them through interactive questions.

### Phase 3: `/speckit-plan`
Creates the technical implementation plan, checking against project constitution design rules and validating dependencies.

### Phase 4: `/speckit-tasks`
Generates a dependency-ordered, checklist-based implementation plan in `tasks.md`.

### Phase 5: `/speckit-implement`
Triggers coding execution. The agent iterates through each task in `tasks.md`, updating the checkboxes to `[x]` as they complete.

### Phase 6: `/speckit-git-commit`
Automates lint and format checks, commits changes, and merges with developer staging branches.
