# R0 findings: make the useful work easy to reach and return to

12 October 2026. Bounded desk-research pass complete: six integration examples,
one firsthand failure report, five findings and three experiments. Sources were
opened, not just searched. No accounts connected or customers contacted. This
is source research, not hands-on testing of the six integrations or measured
customer acceptance of Wright. Customer benefit remains a hypothesis unless
the evidence below says otherwise. All examples were retrieved on this date;
installed build numbers are unknown unless explicitly stated.

## Comparison and concrete journeys

| Integration / source | Documented journey and useful outcome | Friction / evidence limit | Wright decision |
| --- | --- | --- | --- |
| Canva — [OpenAI extensions](https://developers.openai.com/plugins/build/extensions) | Open the sidebar design experience, create a design, inspect its preview beside the conversation. The artifact is the focus. | OpenAI describes ChatGPT sidebar behavior; no Windows build or independent customer outcome was verified. Setup, detailed recovery and customer benefit were not established by this page. | **Adopt** artifact beside chat; **defer** extra global navigation until the actual host supports it. |
| Figma — [Figma MCP guide](https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Figma-MCP-server), [OpenAI extensions](https://developers.openai.com/plugins/build/extensions) | Connect a supported client, select/reference a design node or file, retrieve structured design context and generate/refine corresponding work. Desktop composer mentions help select files; Figma separately documents MCP and reusable skills. | Seats/features and remote versus desktop differ. Figma describes emerging write features as beta. Broad Codex support is not proof of our exact native UI surface. Speed/accuracy statements are vendor claims. | **Adopt** exact workspace/workflow context; **test** selection-to-chat; keep source identities instead of retyping paths. |
| Adobe — [OpenAI extensions](https://developers.openai.com/plugins/build/extensions) | Open a supported file into the appropriate Acrobat/Photoshop editing experience and work on the document through the host. | Documented file-handler pattern; account, exact OS/build, save/close behavior and customer outcomes were not tested. | **Test** a `.wflow` handler, retaining Wright source validation and safe save; **defer** broad file associations. |
| Linear — [MCP docs](https://linear.app/docs/mcp), [26 February 2026 handoff release](https://linear.app/changelog/2026-02-26-deeplink-to-ai-coding-tools) | Find an issue, launch a coding tool with its context already prepared, inspect proposed changes; MCP also reads/updates durable issues. It reduces copying context between applications. | This is tool/context handoff, not proof of an embedded editor. Current MCP docs still mention an older experimental client flag; do not copy that setup into runtime 0.159.2. Claimed convenience is vendor-reported, not measured customer improvement. | **Adopt** exact-subject handoffs and durable objects; **avoid** treating a new worker/cloud coding session as this conversation. |
| Notion — [MCP overview](https://developers.notion.com/guides/mcp/overview) | Authorize access, search workspace content, read it, then create/update pages or databases that remain available in Notion. | Authority comes from authorized access. The overview supplies no native panel lifecycle or measured customer outcomes; compatible client examples do not attest our build. | **Adopt** durable saved work and contextual open/read/edit; **avoid** another UI-only source of truth. |
| Sentry — [MCP documentation](https://mcp.sentry.dev/) | Authorize a project-scoped connection, search errors, investigate performance/triage using the selected project context. Scoping hides unnecessary discovery tools. | Diagnostic rather than manufacturing work; no native Codex panel or independently measured user benefit was established. OAuth and experimental variants are explicit dependencies. | **Adopt** bounded workspace context and fewer irrelevant choices; **defer** generic discovery/admin dashboards in the daily workflow. |

Source screenshots/demonstrations are linked from the OpenAI extension examples
and the Linear release page (including its prompt-template screenshot). These
are publisher demonstrations, not captures from our installation. No external
images have been copied into Wright's implementation gallery.

### Firsthand negative evidence

[Codex issue 33288](https://github.com/openai/codex/issues/33288), reported
15 July 2026, describes first-task timeouts on Windows desktop build
26.707.72221. The reporter later identified unhealthy optional MCP entries and
reported successful first-task tests after disabling only those entries on
26.707.9981.0 / CLI 0.144.2. The issue was closed 5 August. This supports a
specific friction finding, not prevalence or a claim that today's build has the
same defect. No proposed repair from that report was applied to this user's host.

Our [existing reasoning-progress record](../../reasoning-progress.md) provides
another concrete local friction case: clicking Run appeared stuck until the
same desktop conversation answered the pending bounded task. These are prototype
observations, not representative customer research.

## Five findings and resulting decisions

1. **Make the artifact the visual reward.** Open the saved workflow, result or
   evidence directly beside chat. Lead with what the user is accomplishing;
   keep connection/protocol details behind disclosure. Canva/Adobe document this
   presentation pattern; its engineering usability is our testable hypothesis.
2. **Carry context explicitly.** A selection must identify the workspace,
   workflow/revision and relevant block/result without another prompt asking
   the user to copy identifiers. Figma/Linear show useful mechanisms. Prefer
   existing exact navigation references; adding composer integration can wait.
3. **Useful saved work outlasts the panel.** Reopening should attach to the same
   process/run and preserve a draft. Notion/Linear emphasize durable objects;
   Wright already owns these records. Do not add another persistence system.
4. **Trust and recovery are part of pleasantness.** Show connected, unavailable,
   pending chat, declared review and failed as distinct states. The Windows
   report and Wright's local episode provide direct friction evidence. A pulse
   animation or a green connection badge cannot prove model work is progressing.
5. **Scope and progressive disclosure beat more permanent chrome.** Sentry's
   project scope and OpenAI's [UI guidance](https://developers.openai.com/plugins/concepts/ui-guidelines)
   support focused controls. Keep one Add step popover, contextual inspector and
   run drawer rather than another left navigation strip.

The pass found no independent quantitative evidence that these integrations
improve engineering customers' task time or satisfaction. No adoption estimate
or claim of “proven customer value” is justified. Their mechanisms support
small experiments; confidence should come from observed Wright task completion.

## Updated journey and three experiments

**Journey:** native chat or Workflows → select/create the Wright workspace →
open the accepted workflow → inspect/edit → visible save or conflict → readiness
→ start once → useful progress/result or an honest wait → declared response or
review → evidence → close/reopen the same work. A selected workspace appears
in the work surface; native chat remains the only composer. Secondary tools
are contextual. Each unavailable capability offers a bounded next step.

| Experiment | Hypothesis / task | Observable success | Cost / dependency |
| --- | --- | --- | --- |
| 1. Native workspace panel | A compact native overview makes entry and connection limits understandable. Open it and identify the current workspace and available work. | Actual Windows rendering; scoped data correct; no URL copying; light/dark and resize usable; no credential or cross-workspace leak. | Small read-only MCP resource/tool; exact host UI support required. |
| 2. Chat + shared canvas | Compact controls and a bottom inspector let a user edit without fighting sidebars. Change one input, save and reopen. | Correct source/layout retained; user finds Add step/inspector/save; no duplicate chat/tab chrome; no lost draft on close. | Existing editor composition and scoped theme; native tabs qualified separately. |
| 3. Explain and finish a wait | Clear status plus an explicit, supported continuation path makes Run understandable. Identify the wait, continue and find the output. | User distinguishes model handoff from review; same run completes with its original output identity; interruption never repeats an uncertain action. | Existing reasoning/status/process clients; same-conversation message capability is a separate spike. |

Adopt the approved neutral canvas once across hosts. Implement the small panel
probe first, then the shared compact controls. Defer broad composer search,
new global sidebars, generated custom dashboards and automatic background turns.
Do not hide a missing native capability behind a simulated tab strip.

## Formative walkthrough script

After a usable slice exists, use the user and, if available, two to four other
engineers/reviewers. Give tasks without instructions for where to click:
open/create work; change a requirement and save; locate a result; explain the
current wait and next action; record a declared response; close and return.
Repeat comparable tasks on the current prototype. Record completion, elapsed
time to useful work, help requests, wrong turns and repeated context entry.
Ask for 1–5 ease/confidence/pleasantness ratings and one thing to change.
Observe whether they distinguish draft/save/start/review/continue. Small-sample
feedback is formative, not a market-wide result. If no participants are
available, label the walkthrough expert evaluation and leave customer acceptance
pending. No outreach or scheduling is implied by this script.

## Implementation checkpoint

Isolated branch `codex/host-adaptive-ui-prototype`, inherited baseline commit
`2d1e6c02`, source prototype `c0769319` plus 22 frozen files. The original
prototype remains unchanged. Locked local dependencies installed: Python 3.13.12,
MCP 1.28.1, Node 22.22.0, npm 11.10.1. npm reports its existing jsdom engine
minimum is slightly newer than the installed Node; exercise actual tests before
assuming incompatibility, and make no global runtime change.
