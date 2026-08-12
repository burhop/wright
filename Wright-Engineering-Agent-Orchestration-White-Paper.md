# Wright: An Open Agent Control Plane for Engineering Software

*Using existing tools, open integration standards, local-to-cloud AI, and durable workflows to make engineering applications agent-operable.*

## Executive summary

Engineering teams do not need another isolated AI assistant. They need an agent layer that can work across the applications they already use: CAD, CAM, CAE, EDA, coding environments, data systems, PLM, and project-management tools.

Wright is designed to provide that layer.

Its most important architectural role is to sit between two very different worlds:

- **Non-deterministic generative AI**, which is good at interpreting objectives, assembling context, proposing plans, selecting tools, and recovering from ordinary failures.
- **Deterministic engineering software**, which is responsible for exact geometry, calculations, simulation, compilation, validation, configuration control, and released product data.

Wright does not attempt to replace the applications engineers trust. It orchestrates them. It turns an engineer's intent into a governed sequence of operations, records what happened, reports progress and blockers, and keeps the engineer in control of consequential decisions.

This paper organizes Wright's value around nine propositions:

1. One AI agent layer for engineering software.
2. Use the tools you already own.
3. Connect through MCP, WebMCP, CLI, and APIs.
4. Give engineers language-flexible vibe-coding tools.
5. Preserve agent-framework and model choice.
6. Deploy from air-gapped local systems to connected cloud infrastructure.
7. Adopt, bundle, and customize an open-source framework.
8. Improve continuously as AI capabilities advance.
9. Turn agent activity into durable engineering workflows.

## 1. One AI agent layer for engineering software

A meaningful engineering task rarely remains inside one application. A design change may begin with a requirement, modify a CAD assembly, invoke a calculation or simulation, update a drawing and bill of materials, generate or revise code, and finish in a change-management or project system.

Every application contributes specialized value. The difficulty lies between them: incompatible APIs, local desktop constraints, inconsistent authentication, manual transfers, fragmented context, and no single place to manage the overall objective.

Wright is intended to become that common place. An engineer should be able to describe an outcome while Wright determines which approved applications and tools are needed, maintains state across the work, and returns evidence rather than merely a conversational answer.

This is the control-plane opportunity described in [Who Will Control AI-Native Engineering?](https://burhop.substack.com/p/who-will-control-ai-native-engineering): the strategically important layer is the system that receives engineering intent, chooses context and tools, manages the sequence, and explains the result. CAD kernels, solvers, manufacturing applications, and lifecycle systems remain indispensable execution engines.

## 2. Use the tools you already own

Engineering organizations have already invested in software, automation, validation, training, data, and supplier relationships. A useful AI strategy should compound those investments rather than demand wholesale platform replacement.

Wright is designed to orchestrate a broad engineering toolchain:

- **Mechanical design and manufacturing:** CAD, CAM, drawings, geometry kernels, toolpath generation, metrology, and file conversion.
- **Analysis and science:** CAE, FEA, CFD, multiphysics, optimization, numerical notebooks, material databases, and laboratory systems.
- **Electronics and systems:** EDA, PCB, electrical design, requirements, MBSE, test systems, firmware, and embedded toolchains.
- **Software and data:** editors, compilers, build systems, test frameworks, databases, version control, data pipelines, and visualization.
- **Lifecycle and coordination:** PLM/PDM, documentation, issue tracking, project management, quality, procurement, ERP, MES, and collaboration.

This breadth matters to both customers and software vendors.

For customers, Wright offers a path to cross-application workflows without pretending every tool shares the same data model. For engineering-software vendors, Wright can provide a reusable agent surface above the vendor's application while preserving its native semantics, permissions, validation, and differentiated domain capability.

Autodesk's [Design and Engineering APIs](https://aps.autodesk.com/developer/overview/design-and-engineering) and [Automation APIs](https://aps.autodesk.com/design-automation-apis) illustrate why this approach is practical: valuable engineering capability already exists across desktop, cloud, data, and automation surfaces. The opportunity is to orchestrate those capabilities coherently.

## 3. Connect through MCP, WebMCP, CLI, and APIs

No single integration mechanism reaches every engineering application. Wright therefore treats MCP, WebMCP, command-line tools, and application APIs as complementary surfaces.

| Surface | Best fit | Value | Important limitation |
|---|---|---|---|
| **MCP** | Agent-native tools and context | Tool discovery, typed schemas, reusable clients and servers, structured results, capability descriptions, and host-mediated approvals | MCP connects capabilities; it does not replace workflow governance or application validation |
| **WebMCP** | Browser-resident applications | Lets web applications expose structured JavaScript tools instead of relying only on brittle visual automation | It is currently an emerging W3C Community Group draft and should be treated accordingly |
| **CLI** | Local tools, builds, scripts, and headless jobs | Composable execution, exit codes, standard streams, reproducibility, and broad language support | Requires sandboxing, path control, secrets hygiene, and complete output capture |
| **API or SDK** | Deep vendor-native capability | Access to domain objects, transactions, events, permissions, and application-specific validation | Versioning, authentication, licensing, and vendor coupling remain real |

MCP contributes more than a generic way to call an API. The [Model Context Protocol](https://modelcontextprotocol.io/docs/getting-started/intro) gives agent hosts a common way to discover tools and context, understand structured inputs, and consume structured results. Its [tools specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) also recommends visible tool use, confirmation for sensitive operations, and human control.

WebMCP extends the same general idea into browser applications. The current [WebMCP draft](https://webmachinelearning.github.io/webmcp/) defines a way for web applications to expose tools with natural-language descriptions and structured schemas.

CLIs and native APIs remain essential. A CLI is often the cleanest path to a compiler, solver, build, script, or local utility. APIs and SDKs expose the full semantics and validation rules of commercial engineering systems. [OpenAPI](https://spec.openapis.org/oas/latest.html) helps describe HTTP APIs in a language-independent form, but many important desktop applications will continue to require vendor SDKs, local bridges, or purpose-built adapters.

The right integration should be selected per application and per action—not by protocol ideology.

## 4. Language-flexible vibe coding for engineers

Engineers already automate in the languages their applications and disciplines support: Python, JavaScript and TypeScript, shell, PowerShell, MATLAB, Julia, R, C and C++, C#, Java, notebook environments, CAD scripting dialects, and vendor-specific macro languages.

Wright should not force that ecosystem through one preferred language. It should help engineers create, run, test, inspect, and revise the smallest useful automation in the environment where it belongs.

“Vibe coding” is valuable when it lowers the cost of translating engineering intent into executable automation. It becomes dangerous when it is used to bypass verification. Wright's approach should make code a first-class workflow artifact:

1. Generate a small script or patch against explicit inputs and targets.
2. Run the checks appropriate to the application: formatting, types, tests, CAD regeneration, solver convergence, unit checks, or data validation.
3. Present the diff, commands, outputs, and uncertainty to the engineer.
4. Require approval before destructive, expensive, credentialed, or release-controlled operations.
5. Retain the code, environment facts, outputs, and disposition as evidence.

The benefit is not that generated code is inherently correct. It is that an agent can rapidly create testable glue between systems: a geometry script, solver preprocessor, conversion utility, verification harness, reporting step, or application wrapper.

This reflects the engineering pattern described in [AI for Engineers — What Is Working and What Does Not](https://burhop.substack.com/p/ai-for-engineers-what-is-working): use the language model as a planner and interface, then push exact work into deterministic subsystems that can be executed, inspected, and reproduced.

## 5. Preserve agent-framework and model choice

The agent client may become the new front door to engineering. That makes portability strategically important.

Wright is intended to work across leading agent architectures rather than binding engineering applications permanently to one model vendor or chat product. Its framework-neutral direction includes Hermes, OpenAI and ChatGPT surfaces, Anthropic and Claude surfaces, OpenClaw, and custom agents.

The supporting ecosystem is developing quickly:

- [Hermes](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) documents local and remote MCP integration with tool discovery.
- [Anthropic](https://docs.anthropic.com/en/docs/agents-and-tools/mcp) supports MCP across Claude products.
- [OpenAI](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt) documents custom MCP apps, write actions, and administrative controls in ChatGPT.
- [OpenClaw's published vision](https://github.com/openclaw/openclaw/blob/main/VISION.md) includes MCP server and runtime support.

These products do not expose identical features, security models, or release timelines. Wright should therefore treat them as adapter targets, not claim perfect interchangeability.

### Current-status note

Wright is a public-alpha project. Its repository currently documents a production Hermes adapter and a direct MCP profile for Codex. Broader ChatGPT, Claude, OpenClaw, and other client integrations are part of the framework-neutral product direction and should be claimed as generally available only after release-specific validation. See the [Wright README](https://github.com/burhop/wright) and [roadmap](https://github.com/burhop/wright/blob/main/ROADMAP.md).

## 6. Deploy from air-gapped local systems to the cloud

Engineering workloads carry source code, unreleased geometry, formulas, manufacturing processes, supplier data, export-controlled information, and credentials to systems of record. Deployment choice is therefore a primary product requirement.

Wright is intended to support a continuum:

- **Air-gapped local:** Models, agents, engineering tools, and records remain inside a disconnected environment.
- **Private local or edge:** Models and tools run near engineers and desktop applications with controlled network access.
- **Hybrid:** Sensitive tools and data remain local while an approved hosted model provides selected intelligence.
- **Connected cloud:** Models, services, and collaboration run on managed infrastructure with internet access.

Systems based on NVIDIA's [GB10 Grace Blackwell platform](https://www.nvidia.com/en-us/products/workstations/dgx-spark/) demonstrate that substantial inference and agent workloads can run on compact local hardware. “Air-gapped” must still be understood as a complete deployment pattern—including networks, updates, model acquisition, telemetry, credentials, and connected applications—not as a property guaranteed by the processor alone.

Important security controls include:

- Least-privilege identities and separate read, write, execute, and release authorities.
- Model and endpoint allow-lists, explicit network-egress policy, and the ability to use only vendors the organization trusts.
- Workspace and secret isolation, command and path confinement, resource limits, and safe failure behavior.
- Approval gates for destructive, irreversible, regulated, costly, or release-controlled actions.
- Durable logs, connector inventory, monitoring, incident response, and validation of model or tool updates.

The [NIST AI Risk Management Framework](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/) supports this emphasis on documentation, human oversight, ongoing monitoring, and accountability.

## 7. Open, customizable, and bundleable

Wright is free and open source under the MIT License. This matters because the orchestration layer sits at a sensitive boundary: it can see proprietary context and may invoke powerful engineering tools.

Customers and vendors need the ability to inspect the code, constrain it, extend it, and operate it in environments the original developer does not control.

For engineering-software vendors, Wright can be a bundleable framework. A vendor can ship a curated agent environment with product-specific tools, knowledge, permissions, safety metadata, and validation. The application remains the differentiated execution layer while gaining access to multiple agent ecosystems.

For engineering customers, Wright can become an internal control plane connecting commercial applications to company scripts, procedures, data, approval rules, and trusted local or hosted models.

The European Commission's [open-source strategy](https://commission.europa.eu/about/departments-and-executive-agencies/digital-services/open-source-software-strategy_en) identifies related benefits: reuse, interoperability, innovation, digital autonomy, and control.

## 8. Improve continuously as AI advances

AI models, client features, MCP capabilities, and security practices are changing too quickly for a once-a-year integration release.

Wright's modular architecture and public catalog are intended to shorten the path from a useful new integration to an available engineering tool. New MCP servers, adapters, and workflow components can be added without waiting for a monolithic engineering application release.

Speed must still be governed. A production connector should include:

- Clear ownership and provenance.
- Version pinning and compatibility metadata.
- Declared permissions and external dependencies.
- Automated tests and clean-environment validation.
- A controlled update path and rollback procedure.
- Documentation of destructive or release-affecting actions.

The value proposition is not automatic updates at any cost. It is continuous improvement with the option for conservative organizations to approve, stage, reproduce, and audit what they run.

The [Stanford AI Index](https://hai.stanford.edu/ai-index/2025-ai-index-report) documents the rapid evolution and broadening adoption of AI capabilities that make this update model necessary.

## 9. Durable engineering workflows

A significant engineering objective is not a single prompt-response exchange. It is a workflow that moves through partial results, questions, failures, waiting states, human decisions, and downstream effects.

Wright is designed to retain that state and provide continuous feedback:

- What is running?
- What completed?
- What changed?
- What evidence was produced?
- What remains unclear?
- What is blocked?
- What action would unblock it?
- Where is human approval required?

A useful durable record should include:

- The objective, scope, inputs, assumptions, authoritative revisions, and responsible engineer.
- The plan, selected tools, versions, commands, parameters, and permissions used.
- Outputs, diffs, validation results, warnings, failures, and derived artifacts.
- Clarification requests, approvals, rejections, overrides, and the evidence shown at each decision.
- Current status, blockers, dependencies, retry history, next action, and completion criteria.

This record keeps the engineer oriented, supports recovery and team handoff, provides data for improving workflows, and creates a foundation for audit and incident analysis. NASA's [Systems Engineering Handbook](https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf) similarly treats configuration status, revision history, traceability, and technical-data management as central engineering controls.

Most importantly, a useful engineering agent must know when to stop. If a dimension is ambiguous, a credential is missing, a tool reports an invalid model, a cost limit is reached, or a release boundary is encountered, Wright should surface the blocker and ask the smallest useful question rather than hide the failure or invent a result.

## Example workflow

Consider this request:

> Reduce the mass of this bracket without changing its mounting interfaces. Compare two manufacturable options. Update the model, analysis summary, drawing note, and change task. Stop for approval before writing release-controlled data.

A credible agent workflow would:

1. Identify the correct assembly, part revision, requirements, and protected interfaces.
2. Inspect the native CAD model and choose supported parametric operations.
3. Generate alternatives using the CAD system or a reviewed script.
4. Regenerate the model and run geometric checks.
5. Execute the approved simulation workflow and validate units and solver criteria.
6. Compare mass, performance, manufacturability, cost assumptions, and uncertainty.
7. Prepare downstream drawing, report, and project-system updates.
8. Present the evidence and pause for engineer approval.
9. Apply only the approved changes and retain the complete workflow record.

The language model contributes interpretation, planning, and recovery. The engineering applications contribute geometry, physics, manufacturing logic, and authoritative data. Wright coordinates the two.

## Product status and direction

Wright's [public repository](https://github.com/burhop/wright) describes a public-alpha system with agent orchestration surfaces, an MCP registry, selected deterministic CAD/CAE/CAM and calculation adapters, a Docker appliance, a production Hermes adapter, a direct MCP profile for Codex, and bring-your-own local or hosted OpenAI-compatible endpoints.

The [roadmap](https://github.com/burhop/wright/blob/main/ROADMAP.md) includes broader framework support, WebMCP, OpenClaw integration, project-management coverage, and a larger engineering-tool catalog. These are product directions until implemented and verified.

That distinction is important. The long-term value proposition is broad, but credibility requires precise separation between what an alpha release does today and what the architecture is designed to support.

## Conclusion

The opportunity in engineering AI is not simply to generate more content. It is to create a trustworthy path from intent to verified action across the applications that already design, simulate, manufacture, document, and manage products.

Wright's nine value propositions form one coherent architecture:

- A broad agent layer over existing engineering tools.
- MCP, WebMCP, CLI, and API integration.
- Language-flexible engineering automation.
- Agent, model, and deployment choice.
- An open framework that vendors can bundle and customers can customize.
- Rapid but controlled evolution.
- Durable workflows that expose progress, uncertainty, evidence, and blockers.

If Wright maintains the boundary between probabilistic planning and deterministic execution—and makes every consequential transition visible to an accountable engineer—it can become useful infrastructure for engineering-software vendors and engineering organizations alike.

The applications keep their precision and domain authority. The agent gains reach. The engineer keeps control.

## Selected supporting essays

- [Who Will Control AI-Native Engineering?](https://burhop.substack.com/p/who-will-control-ai-native-engineering)
- [AI for Engineers — What Is Working and What Does Not](https://burhop.substack.com/p/ai-for-engineers-what-is-working)
- [Do You Work in Product Development or Manufacturing? Here's the MCP Overview You Actually Need](https://burhop.substack.com/p/do-you-work-in-product-development)
- [Interfaces as the Primary Bottleneck for AI in Product Design](https://burhop.substack.com/p/interfaces-as-the-primary-bottleneck)
- [The Problems of Tokenization in Design and Manufacturing](https://burhop.substack.com/p/the-problems-of-tokenization-in-design)
- [The New CAD](https://burhop.substack.com/p/the-new-cad)
