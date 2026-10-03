# Recovery after backend-owner recreation

Primary-assertion review found that one earlier approval test used a request ID
containing “restart” while retaining the same backend owner. That name/request
was insufficient restart evidence. The controlled tests now recreate actual
file/action/policy or input owners against their existing SQLite/run records.
No authority is re-enrolled and no human review or external action is invented.

67 existing continuation, supervision and approval cases pass with stronger
assertions. Four primary functions (five parameterized scenario instances) cover
unknown input continuation, completed cached action, failed post-approval segment
and unknown enrolled digital handoff. They preserve original run/checkpoint/subject
identity, retain unknown consumed state and forbid model/action replay. Unknown
records remain byte-identical. The handoff failure injection is absent after
recreation; safe refusal comes from durable state rather than the old closure.

These are actual backend-owner/storage behaviors with simulated model responses
and a fixed nonphysical enrolled handoff. They support EDGE-04 and the relevant
NEG-05/07/08 assertions. They do not prove every part of those broad obligations,
OS power-loss durability, live provider restart, physical operation or human
acceptance. Source/UI generation and the full 182-obligation semantic audit remain
separate. No business runtime code changes in this checkpoint.

Read primary-assertions.json, command.json, case-index.json and checked-scope.json.
Counts overlap previous runs and must not be summed. 550 retained engineering/UI
files and protected campaign/context hashes remain unchanged. No protected review,
physical/supplier effect, push/merge/release or provider/model call occurred.
T056/T057 and the goal remain open.
