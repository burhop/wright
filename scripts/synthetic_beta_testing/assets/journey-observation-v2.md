# Continuous customer observations — version 2

Use journey_step to mark the start and outcome of each high-level activity from
the declared plan. Use its step IDs; order may vary and revisits are allowed.
Finish the previous step before starting another. Outcome marks do not stop the
continuous elapsed clock. Mark completed only after seeing the intended outcome;
this is a customer report, not independent verification or engineering approval.

Every desktop action needs a short `intent`, such as “Read the MCP setup options”
or “Open the saved workflow.” Describe what you are doing, not private reasoning.
For wait actions, set wait_for to wright or external and name the expected visible
change in the intent. Do not add artificial waits to imitate human thinking.

The observer automatically records navigation, typing, screen capture and waits.
Between tool calls it records reviewing/deciding, including AI/controller delay.
Use activity_note when your activity changes without a UI action: reading help,
considering another approach, recovering, or preparing final feedback. A brief
statement such as “Considering a manual workflow after chat stalled” is enough;
never supply private reasoning, credentials or invented durations. Record what you
actually do, including abandoning an approach or returning to an earlier screen.
Before writing the final report, mark activity feedback. This diary adds no product
permissions and grants no tool, engineering-review or terms authority.

Keep brief evidence-linked feedback. Experience categories remain slow,
unclear_instructions, broken_behavior, unclear_progress, hard_to_find, setup_access,
hard_to_recover, unhelpful_result and unexpected_effort. They describe symptoms,
not proven root causes. Preserve the unchanged six-field final report.
