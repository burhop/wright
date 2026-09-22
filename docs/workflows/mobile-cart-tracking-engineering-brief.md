# Investigating path drift in a mobile cart

Engineering purpose and decision brief

Wright robot tracking pilot · Robot 010 · 21 September 2026

**Product-purpose correction:** This brief explains the current analysis task;
it does not establish that the example is a strong demonstration of Wright.
The user's subsequent clarification makes extended chains of existing
engineering tools, exposed through MCP servers and connected by actual outputs,
fundamental to the product. The current Robot example mainly expands one
analysis activity into several steps. See the controlling
[engineering demonstration principles](../design/engineering-demonstration-principles.md).
Improved wording or an acceptance threshold alone does not resolve that gap.

## The engineering job

**An engineer is commissioning a small mobile cart that appears to wander while driving straight. The job is to establish what the recorded motion actually shows, separate that from measurement disagreement, and choose the next useful test before changing the machine.**

The floor seam is a suspected disturbance in this investigation. It is not the reason to build the workflow, and crossing a seam is not itself a failure. The more general engineering problem is: **the machine is not apparently following its intended motion, and the available measurements disagree about what happened.**

This workflow turns the recorded test into a reviewable engineering evidence package. Its immediate deliverable is a justified next-test recommendation, supported by measurements and plots. It does not promise a confirmed root cause, a repaired cart, or approval to put the cart into service.

## A situation in which an engineer would use it

Imagine commissioning an automated cart for an indoor material-handling route. During a straight-line trial, the technician notices a sideways wobble near a floor joint. The cart's wheel-based position estimate shows one amount of wandering; an overhead tracker shows another.

The engineer now has practical questions. Is the recorded departure from the route substantial enough to investigate? Did the cart move as far sideways as its own estimate says? Does the disturbance occur at a particular location? Should the next investigation focus on the wheel and caster assembly, the position estimate, or the measurement setup?

Acting on the visual impression alone could lead to an unnecessary mechanical modification or controller adjustment. Looking only at the robot's own estimate could also misstate the movement. The engineer needs the intended motion, independently measured position, wheel-based estimate, and operator observations on the same time and coordinate basis.

The workflow is most relevant to a commissioning, test, mechatronics, or mechanical engineer investigating mobile equipment. It is not intended to be a robot-specific task that every mechanical engineer performs. The recognizable engineering activity is **compare intended and observed behavior, quantify the discrepancy, and design the next experiment**.

## The particular cart and test represented here

The supplied example describes an unloaded 32 kg differential-drive cart: its two driven wheels provide motion and steering, and the operator's note refers to a front caster. The test lane is 8 m long and 1.5 m wide. The intended motion is straight ahead at 0.22 m/s. A 30-second record contains samples every 0.5 seconds, and the operator marks a taped floor-seam crossing at 15 seconds. [1]

**These are fictional commissioning circumstances and synthetic logs, not measurements from a real customer installation.** The calculations operate on actual input files, but their results describe that constructed example. Robot 010 means the tenth software attempt for this example; it does not mean ten independent physical trials were performed.

The lane dimensions provide context, not an acceptance criterion. No allowable path deviation, calibrated tracker uncertainty, or complete clearance requirement is supplied. A measured deviation therefore cannot be called acceptable or unacceptable for service from this brief alone.

## What the different measurements mean

Three different descriptions of the route must remain distinct:

| Information | What it means | What it does not establish |
| --- | --- | --- |
| Intended route | Where the cart was supposed to go | Where it actually went |
| External position measurement | Where the overhead tracker reports the cart was | Perfect ground truth; the tracker's repeatability is unknown here |
| Wheel based position estimate | Where the cart estimates it went from wheel motion | An independent measurement of movement relative to the floor |

The command is also separate: a requested speed of 0.22 m/s is not a measurement that the cart actually moved at that speed. A difference between commanded speed and the wheel estimate cannot, on its own, demonstrate wheel slip.

The operator's event note supplies a time to examine. It is not a force measurement and is not proof that the seam caused the observed behavior.

## What the workflow does

1. **Assemble and check the test record.** Read the original motion logs, operating context, and event note. Check that the required recordings are present and usable. In this implementation, the uploaded tables are packaged into a standard robot recording before analysis; that is a data-handling step, not another physical test.
2. **Put the recordings on a common basis.** Apply the supplied clock and coordinate relationships so that two positions being compared refer to the same time and reference axes. This example already uses matching coordinates and clocks, so the specified corrections are zero. They are supplied assumptions, not a calibration discovered by the workflow.
3. **Compare intended and recorded motion.** Plot the planned route, overhead measurement, and wheel estimate together. Show sideways deviation against time and identify the interval around the operator's event. Preserve missing measurements as gaps rather than inventing a continuous observed path.
4. **Calculate and explain the discrepancy.** Report error measures, retained samples, relevant time ranges, and disagreements. Preserve the aligned sample table so another engineer can inspect the calculation. Distinguish the numerical observations from possible causes.
5. **Prepare an engineering recommendation and review it.** Explain what remains unknown and propose one inexpensive follow-up experiment. The engineer reviews the evidence and interpretation. Downstream checking and collection of the final package do not replace that judgment.

In short: **recorded trial → comparable measurements → quantified observations → next-test decision**.

### What the four input blocks are

They are supporting material, not four separate questions for the AI:

- **Human context:** the engineering request, operating situation, and uploaded log contents.
- **Alignment contract:** the stated relationship between clocks and position coordinates.
- **Authored operation source:** the calculation procedure used by the analysis software. This is implementation support, not a normal measurement an engineer would collect.
- **Route sketch:** an illustration of the lane and marked event, not a measured trajectory or dimensional inspection drawing.

The engineer's reason to use the workflow should be understandable without opening the calculation source.

## What this example actually tells us

Robot 010 produced the following observations. The peak values, timing, and lateral RMS were also checked directly against the original numerical inputs while preparing this brief. [2]

| Observation | Engineering interpretation |
| --- | --- |
| External measurement reaches 45 mm left of the intended route at 15 s | The external record contains a sideways excursion; its magnitude still carries unknown measurement uncertainty |
| Wheel estimate reaches 95 mm left at the same time | The wheel estimate reports a larger excursion, disagreeing by 50 mm at the peak |
| Whole record lateral RMS error is about 14.1 mm across 61 samples | This summarizes the deviation across the record; it is not the 45 mm peak, a confidence interval, or an allowable limit |
| Nonzero external sideways deviation is already present at 12.5 s; the seam event is marked at 15 s | The annotation coincides with the peak, not the start; it does not establish the seam as the initiating cause |
| The external measurement returns to the intended line by 18 s | The supplied record shows a temporary excursion rather than a persistent final offset |

The appropriate conclusion is:

> The records show a temporary sideways excursion and a disagreement between the external measurement and the wheel-based estimate. The seam crossing occurs during that excursion, but these data do not identify its physical cause. A controlled repeat comparison is needed before choosing a corrective change.

This is useful negative evidence as well as positive evidence: it prevents an unsupported statement such as “the wheels slipped when they hit the seam.” A result can improve an engineering decision by showing that a suspected explanation has not yet been demonstrated.

The plots deliberately enlarge the sideways scale to make millimetre-level differences visible over several metres of travel. They are not physical-scale drawings; apparent angles in the path view should not be interpreted geometrically. [3]

## What the engineer should do with the result

The proposed next experiment is a **repeat and control comparison**: repeat the unloaded, same-speed trial over the marked seam and over a comparable nearby seam-free route. Keep the cart configuration and measurement setup consistent, document the two routes, and record the crossing location and time. This is a proposed test for an engineer to plan and authorize, not a command issued by Wright.

Compare whether the externally measured excursion recurs at the seam location, whether it also appears on the control route, and whether the wheel estimate continues to disagree with the external measurement. A synchronized additional observation of the caster crossing could help resolve event timing. A faster contact or vibration measurement would be a separate addition; the present 0.5-second motion samples cannot resolve the detailed dynamics of a brief impact.

The follow-up outcomes would guide further investigation:

- If an externally measured disturbance recurs specifically at the seam location, a location-dependent mechanical interaction becomes better supported, but its particular mechanism still needs examination.
- If the wheel estimate changes without a comparable external displacement, investigate the position-estimation and measurement chain before treating the estimate as actual cart motion.
- If both routes show similar behavior, the evidence for a seam-specific explanation weakens.
- If the result is not repeatable or measurement uncertainty is too large, improve the measurement basis before interpreting a small difference.

These are conditional investigation directions, not diagnoses already established by this pilot. No controller changes or live robot actions are part of the current workflow.

## Why use Wright rather than just look at a graph

An engineer could perform this analysis manually using plotting and numerical tools. Wright's intended contribution is to retain the complete chain from the supplied test record to the engineering recommendation: which data were compared, what alignment was used, which samples were excluded, how the numbers were calculated, and which plots support the conclusions.

The useful package is the **diagnosis, annotated path and error plot, and proposed next experiment**. The aligned timeline and calculation record support inspection and reuse; intermediate conversion records are supporting evidence, not the main engineering result.

This becomes more valuable when the same analysis must be repeated for another trial or configuration, or reviewed by someone other than the person who made the first plot. It is intended to reduce repeated preparation and inconsistent comparisons. This pilot has not measured a time saving or demonstrated a financial return.

## Why this is a Wright pilot

There are two separate purposes:

**For the engineer:** investigate apparent path wandering and decide what evidence to obtain next.

**For Wright development:** demonstrate that a connected workflow can consume engineering inputs, run calculations, expose understandable results, preserve the evidence behind them, and stop for the appropriate human judgment. Robot 010 also exercises a repaired handoff of generated files to downstream checking. That software repair is not the customer's engineering reason for running the workflow.

As observed on 21 September 2026, Robot 010 has produced its analysis and diagnosis and is awaiting engineering review. This brief does not approve those outputs or claim that the full workflow has passed validation. The review asks whether the findings and next-test recommendation are justified, not whether the interface looks satisfactory.

## What would make this a complete engineering investigation

**The example is meaningful as a preliminary commissioning investigation. It is not yet a complete root-cause study or a formal performance acceptance test.** That distinction should be explicit in the product.

A real project would additionally need a defined operating problem and consequence, an allowable tracking-error requirement tied to the application, a credible measurement-uncertainty assessment, and repeated trials under relevant loads and conditions. Confirming a mechanical cause would require measurements that discriminate that cause from alternatives. Approving service would require the project's separate operating and safety assessment.

None of those requirements should be invented merely to make the example look complete. We can retain the existing workflow and data while presenting its honest purpose more clearly:

> Investigate why a mobile cart appears to wander from its intended route, and determine the next test needed to distinguish actual motion from measurement disagreement.

That describes the value of the analysis task, but not the extended multi-tool engineering process Wright needs to demonstrate. This brief must not be used as qualification of the example's product-demonstration value.

## Source material and current evidence

1. [Original engineering situation](../../tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis/01-aisle-floor-seam/context.md), [operator request](../../tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis/01-aisle-floor-seam/prompt.txt), and [scenario definition](../../tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis/01-aisle-floor-seam/scenario.json). The context file also contains an older software-testing note about file-presence checks; that note is not an engineering performance requirement or a description of current validation capability.
2. Original [external measurements](../../tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis/01-aisle-floor-seam/external-pose.csv), [wheel estimates](../../tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis/01-aisle-floor-seam/odometry.csv), and [event annotation](../../tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis/01-aisle-floor-seam/events.csv). Current local outputs: [Robot 010 diagnosis](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/robot-tracking-diagnosis-01/attempt-010/artifacts/diagnosis.md), [measurements](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/robot-tracking-diagnosis-01/attempt-010/artifacts/analysis/tracking-metrics.json), and [path and error plot](C:/Users/markb/wright-feature-081/engineering-workflow-demos/campaign/robot-tracking-diagnosis-01/attempt-010/artifacts/analysis/trajectory-overlay.png). Local output links require this computer's demonstration workspace.
3. [Plot interpretation and limitations](../design/robot-tracking-plots.md), [engineering purpose of the existing examples](../../tests/datasets/engineering-workflows/ENGINEERING-GUIDE.md#robot-motion), and [open Robot 010 in Wright](http://127.0.0.1:5173/workspace/c33593b1-73a8-4056-a7f4-a07a9903dd2d?workflow=canonical&workflowPath=workflows%2Fvalidator-082-robot-tracking-diagnosis-01-attempt-010.workflow.wflow).
