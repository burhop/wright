# MakerEngineer.com: website agent handoff

**Prepared:** 25 October 2026. **Audience:** the agent maintaining MakerEngineer.com
in its separate website project. **Purpose:** prepare focused website content and
navigation changes that help a new visitor understand Wright and reach a useful
first step. This brief is self-contained; Wright's internal feature plans are not
required to understand it.

The product owner has confirmed that MakerEngineer.com is the public front door
and can be substantially updated, including tutorials and examples. The proposed
copy and delivery slice below are recommendations. Use the website project's
existing preview, review and deployment process; this document itself does not
publish changes or establish release availability.

## 1. The outcome we want

A visitor arrives with a job, such as:

> My drawer handle broke. I have a 3D printer. Can Wright help me make a replacement?

The website should help that visitor follow this journey:

**Recognize their job → inspect an actual example result → understand what they
need → choose a suitable setup path → enter Wright with a clear next action.**

We call the first-contact experience the **golden hour**. Begin by improving the
first few minutes. Success is an understandable, actionable next step; we have no
basis to promise a complete engineering job or installation within a fixed time.

MakerEngineer.com owns this introduction. GitHub remains available for source,
technical references, issues and contribution. Visitors should be able to
understand an example and its requirements before having to interpret a repository.

## 2. What Wright is and how to explain it

Wright coordinates engineering work across existing tools, AI, inputs, checks and
human decisions. A saved process connects the work: outputs from one stage become
inputs to the next, with inspectable results and a durable record of progress.

Show the engineering applications and what each contributes. Explain their
connections in terms of the job, rather than leading with agents, protocols,
deployment categories or model providers. Keep technical details available when
they help with setup or a decision.

Users can build and inspect a process in a graphical editor and carry out that
same process in a working view. The public website introduces and explains this
experience. Wright's existing backend owns execution, validation, run state,
reviews and recovery; this website assignment does not add a workflow executor.

Set expectations for people seeking an immediate visual model or reconstruction
from a photograph. Explain the inputs and tool capabilities a particular job
needs. A photograph alone does not establish an arbitrary part's dimensions,
material, fit or strength.

Manufacturing is one useful example. Preserve the broader purpose: analysis,
investigation, design and engineering documentation also belong in Wright.

## 3. What prompted this work

We have user reports of expensive work starting before intent was aligned and
slow changes. Some visitors interpreted Wright as a general CAD generator or an
out-of-the-box reverse-engineering service. These reports identify possible
problems; they are not a measured distribution of customer needs.

On 25 October we observed one synthetic tester starting at MakerEngineer.com.
Its route was:

**Homepage → Use Cases → CAD & Product Design → Getting Started.**

It found related CAD capability descriptions. Getting Started then displayed a
prominent **Coming Soon** notice describing active private development and future
deployment modules. The attempt stopped before a usable setup procedure or
replacement-part job. No external destination, installation or engineering run
was attempted.

The visited Use Cases/CAD panels described disciplines and capabilities, but the
tester did not find a worked replacement-part example there. This finding applies
to the visited route, not every part of the website.

A separate GitHub-entry observation found the native-Hermes route, then stopped
because its guide assumed an available Hermes environment without linking to
Hermes installation or launch instructions. Website setup guidance should cover
that handoff explicitly.

**Study limitations:** these were synthetic observations. Fresh-history agents
still inherited repository instructions, so fully naive context isolation was
not achieved. They used rendered-page text as well as screenshots and encountered
automation locator errors. Elapsed times are not human patience or completion
benchmarks. The evidence supports concrete content observations, not customer
satisfaction, conversion or adoption claims.

## 4. Recommended first delivery

Prepare a reviewable preview of **one connected route**, reusing the existing
website stack and useful existing content:

| Priority | Change                                                                             | Visitor benefit                                                                         |
| -------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| First    | Correct the Getting Started availability message and supply one honest next action | Visitors can tell whether they can run, explore or only preview the selected experience |
| First    | Clarify the homepage explanation and primary call to action                        | Visitors understand the engineering job Wright helps coordinate                         |
| First    | Add one replacement-handle example page                                            | Visitors can inspect a concrete result and the work behind it                           |
| First    | Add or connect a prerequisite-aware setup tutorial                                 | Visitors know what to obtain and where to continue                                      |
| Later    | Expand tutorials, examples and feedback based on observed gaps                     | Further content follows evidence rather than a broad rewrite                            |

The first delivery should include the homepage/entry changes, one example page
and its setup handoff. Do not make completion depend on a new brand, a complete
site rebuild, all engineering disciplines, all installation routes, a new
analytics platform or new Wright functionality. Actual route names are the
website project's choice; use stable, shareable URLs for examples and tutorials.

## 5. Suggested homepage structure and draft copy

These are editorial starting points, not approved final wording.

**Headline:** Put your engineering tools to work together.

**Supporting copy:** Wright coordinates your tools, AI, inputs and reviews in a
reusable engineering process. Follow the work, inspect the results and see what
still needs checking.

**Primary action:** Explore a replacement-part example.

**Secondary action:** Check setup requirements.

Place an actual example image and a short explanation close to these actions.
For the first example, explain that a dimensioned handle moves through design,
geometry preparation, comparison of print preparations and digital review.
Let people inspect recorded results before installing engineering tools.

Below that introduction, show:

- What the visitor starts with, which tools contribute, and what they receive.
- A short worked example with an obvious next step and current availability.
- A plain distinction between viewing recorded evidence and running a new job.
- Setup help, tutorials, support and technical references.

Keep broader discipline pages as supporting navigation. Review phrases such as
universal automation, generation of arbitrary CAD, zero data leakage and setup
in minutes against specific supported behavior before retaining them. Audit the
named CAD integrations, communication channels and model providers; their
appearance in current marketing does not establish qualification.

## 6. The replacement-handle example page

Recommended title: **Prepare a replacement drawer handle for 3D printing.**

Recommended introduction: **Explore a dimensioned example, see how engineering
tools prepare its geometry and compare print orientations, then inspect the
digital checks. Adapt the inputs to your own part once the requirements and
tools are ready.**

The page should answer:

1. **What job is this?** A supplied, dimensioned replacement-handle assignment;
   users' own handles require their own measurements and requirements.
2. **What can I see now?** The supplied sketch, an actual recorded geometry
   preview, a short walkthrough, the resulting package and its stated checks.
3. **What do the tools do?** FreeCAD constructs geometry; Blender repairs and
   previews it; Orca prepares and slices alternatives; OASiS supplies supporting
   passive inspection; Wright coordinates the handoffs, reviews and validation.
   This example does not include an FEA strength solve.
4. **What do I need to run it?** A supported Wright/agent-host environment, model
   access, the selected independent engineering integrations and exact example
   inputs/profiles. State relevant host limits before the run action.
5. **What does the evidence establish?** A particular digital package passed its
   checks and exact review. Physical fit, strength and actual printing remain
   unverified.
6. **What happens next?** Choose between viewing the recorded walkthrough and
   preparing an installation for a new run. Each button names that actual action.

Use real assets with provenance and clear development/recorded labels. A diagram
should show meaningful artifact handoffs, rather than merely a count of blocks.
Retain the connection between a changed design, its checks and its deliverables.

## 7. Make setup a complete handoff

Native Wright through Hermes is the selected first-contact route in the local
development work. Verify its publicly obtainable version and supported host
before describing this particular example as available to run. Docker and Codex
have separate installation/qualification questions; they need not be equal
choices on the first screen.

The setup tutorial should cover this sequence with working links and expected
results:

1. **Check compatibility:** identify the supported operating system, Wright
   version, example version and last verification date.
2. **Obtain the agent host:** explain Hermes briefly and link to its verified
   official installation/sign-in instructions. Provide “I already have Hermes”
   and “I need to set it up” paths, with a clear return point.
3. **Install and open Wright:** use the current supported adapter instructions;
   show what success looks like and where its local workspace URL appears.
4. **Explore the example:** name the actual controls in the documented version.
   Explain what can be viewed without engineering-tool or model execution.
5. **Prepare only this job's tools and inputs:** explain required integrations,
   model access, measurements and profiles. A catalog entry or successful sign-in
   alone is not proof of readiness.
6. **Review before starting:** show the actual readiness result, what work will
   run, any known limits and where time/cost remain unknown.
7. **Return or get help:** show how to reopen the same run, locate a failure and
   deliberately share reviewed support information.

Do not paste development proof scripts, local workspace paths, existing account
details or test approval mechanisms into a public setup recipe. Keep secrets and
engineering approvals in Wright's supported setup and review flows.

## 8. Availability and claims that need care

The local Feature 084 journey is complete in its authorized development scope.
It is **not evidence that its example, UI and dependencies are present in the
currently published release**. The website agent needs a verified release/host
matrix from the Wright owner before offering a “Run this example” action.

| Actual availability                                                 | Appropriate page behavior                                                                                           |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Public release and example verified on a named host                 | Show a run/setup action with exact supported instructions and versions                                              |
| Recorded development evidence available, public run path unverified | Offer the recorded example and walkthrough; label development status and explain the missing run-path qualification |
| Capability proposed or not qualified                                | Label it as planned; offer useful related material without implying it can run                                      |

Replace the blanket Coming Soon handoff with the accurate state for each action.
If installation is still unavailable for this example, provide a usable recorded
experience and a specific explanation; do not invent a download or silently send
visitors into unsupported instructions. Signup can remain optional for updates.

Important limits of the retained handle demonstration:

- The final recorded package passed **43 digital checks** on its exact subjects.
  That is not general certification or proof of physical fit/strength.
- The demonstrated orientation correction required a **full fresh run**. General
  cheap local recomputation and one-click correction are not established here.
- The **137-second video is edited**, with captions and development labels. Its
  length is not the duration of engineering execution.
- Fresh-run time and model cost are unknown without a measured basis. Timeouts
  and call limits are not a complete spending cap.
- No physical print or live printer handoff was authorized in this work. The
  retained transfer is simulated.
- Raspberry Pi enclosures are a desired later demonstration. Superiority over a
  competent direct Astra session has not been established and must not be claimed.
- An internal QA stage became faster; that does not support a customer-facing
  claim that Wright completes engineering jobs 46% faster.

## 9. Materials available from the Wright project

The portable packet supplied with this brief includes these observation assets:

- Website-start storyboard (retained local evidence: `artifacts/first-contact/golden-hour-002/storyboard.pdf`).
- Actual arrival (retained local evidence: `artifacts/first-contact/golden-hour-002/tester/01-arrival.png`).
- Visited CAD page (retained local evidence: `artifacts/first-contact/golden-hour-002/tester/03-cad-product-design.png`).
- Getting Started stopping point (retained local evidence: `artifacts/first-contact/golden-hour-002/tester/05-stopping-point.png`).

Those screenshots document the site observed on 25 October. They are not new
designs. The packet preserves their bytes; it is for implementation context.

The following are repository-relative source locations to request from the Wright
owner if the separate website project cannot access them. They are candidate
content inputs, not guaranteed public URLs or automatically approved release media:

| Material                                  | Wright repository location                                                   | Required treatment                                                              |
| ----------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Development handle guide                  | `docs/getting-started/first-handle-workflow.md`                              | Adapt to the verified public version; preserve prerequisites and limits         |
| Native installation guide                 | `docs/getting-started/hermes-plugin.md`                                      | Verify release instructions and add the prerequisite Hermes handoff             |
| Captioned walkthrough and transcript      | `artifacts/first-contact/084/native-handle-walkthrough-021/`                 | Development recording; edited, captioned, not elapsed execution                 |
| Recorded sketch/actual-preview provenance | `artifacts/first-contact/084/recorded-handle-outcome-022/`                   | Obtain the actual asset locations from its provenance; preserve recorded status |
| Completed corrected digital package       | `artifacts/first-contact/084/native-handle-correction-020/final-validation/` | Exact package evidence; physical validation remains unassessed                  |
| Current local delivery state              | `specs/084-first-contact-experience/progress.md`                             | Current checkpoint takes precedence over older draft planning language          |

If a required release fact or asset cannot be verified, list it as an explicit
content dependency and continue the preview work that does not rely on it. Avoid
adding a public link to an unpublished local file or inventing a screenshot.

## 10. Review and lightweight evaluation

The website agent's first review package should contain:

- A local/staged preview of the connected entry, example and setup handoff.
- Proposed copy, the source of each material capability/availability claim, and
  a short list of unresolved product-owner dependencies.
- Desktop and narrow/mobile screenshots, plus checks that primary actions,
  keyboard navigation, focus, links and example/tutorial deep links work.
- Working media with captions/transcript and meaningful image descriptions;
  introductory motion must not obscure navigation or the primary action.
- The existing website project's applicable checks and a concise change summary.

Re-run a single bounded first-contact observation against the preview after the
content is ready. Use the same broken-handle scenario and the website entry,
without supplying the successful route. Observe whether the visitor can find an
example, describe the needed inputs/tools and reach a real next step or a clear
availability explanation. Report inherited-context and automation limitations.
Human acceptance remains a separate question.

Keep measurement proportionate. If already-approved website analytics exist,
review the path from entry to example to setup handoff, rather than collecting
raw engineering prompts, credentials or full sessions. Optional feedback can ask
what the visitor wanted to do and where they got stuck. New telemetry and a
customer pilot are separate decisions; neither is needed for this first delivery.

The next milestone is a coherent, truthful starting experience for one useful
job, with evidence for its claims and a clear handoff into Wright.

Local evidence references identify preserved operator records; they are not included in the public documentation build.
