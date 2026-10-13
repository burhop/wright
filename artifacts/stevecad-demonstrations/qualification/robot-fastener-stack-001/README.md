# Robot home-pose fastener measurements

Independent passive exact-STEP home-pose alignment, axial-stack and planar bearing-area observations. Simplified purchased references have no threads, driver geometry or physical engagement proof. No CAD edit or MCP invocation.

All 29 stacks pass shaft/nut alignment and modeled nut-span checks. Both ends have measured planar bearings; 66 positive-area planar contact pairs have zero overlap. The report retains the face-intersection areas and near-pair observations. The original workflow verdicts and native contact declarations are unchanged.

| Shaft | Nut | Coaxial error mm | Shaft length mm | Nut span along shaft mm | Bearing at both ends |
|---|---|---:|---:|---|---|
| base_bolt_1 | base_nut_1 | 0 | 16 | 2..4.4 | PASS |
| base_bolt_2 | base_nut_2 | 0 | 16 | 2..4.4 | PASS |
| base_bolt_3 | base_nut_3 | 0 | 16 | 2..4.4 | PASS |
| base_bolt_4 | base_nut_4 | 0 | 16 | 2..4.4 | PASS |
| cradle_bolt_a | cradle_nut_a | 2.52687e-11 | 25 | 5.5..7.9 | PASS |
| cradle_bolt_b | cradle_nut_b | 5.66205e-11 | 25 | 5.5..7.9 | PASS |
| elbow_cradle_bolt | elbow_cradle_nut | 0 | 20 | 17.5..19.3 | PASS |
| elbow_mount_bolt | elbow_mount_nut | 1.89759e-12 | 40 | 2.6..5 | PASS |
| guide_bolt_fl | guide_nut_fl | 1.23292e-11 | 30 | 4.6..7 | PASS |
| guide_bolt_fr | guide_nut_fr | 1.23292e-11 | 30 | 4.6..7 | PASS |
| guide_bolt_nl | guide_nut_nl | 6.96159e-11 | 30 | 4.6..7 | PASS |
| guide_bolt_nr | guide_nut_nr | 6.96159e-11 | 30 | 4.6..7 | PASS |
| retainer_elbow_bolt_1 | retainer_elbow_nut_1 | 0 | 16 | 13..14.8 | PASS |
| retainer_elbow_bolt_2 | retainer_elbow_nut_2 | 0 | 16 | 13..14.8 | PASS |
| retainer_gripper_bolt_1 | retainer_gripper_nut_1 | 0 | 16 | 13..14.8 | PASS |
| retainer_gripper_bolt_2 | retainer_gripper_nut_2 | 0 | 16 | 13..14.8 | PASS |
| retainer_shoulder_bolt_1 | retainer_shoulder_nut_1 | 0 | 16 | 13..14.8 | PASS |
| retainer_shoulder_bolt_2 | retainer_shoulder_nut_2 | 0 | 16 | 13..14.8 | PASS |
| retainer_wrist_bolt_1 | retainer_wrist_nut_1 | 0 | 16 | 13..14.8 | PASS |
| retainer_wrist_bolt_2 | retainer_wrist_nut_2 | 0 | 16 | 13..14.8 | PASS |
| retainer_yaw_bolt_1 | retainer_yaw_nut_1 | 0 | 16 | 13..14.8 | PASS |
| retainer_yaw_bolt_2 | retainer_yaw_nut_2 | 0 | 16 | 13..14.8 | PASS |
| shoulder_cradle_bolt | shoulder_cradle_nut | 0 | 20 | 17.5..19.3 | PASS |
| wrist_cradle_bolt | wrist_cradle_nut | 0 | 20 | 17.5..19.3 | PASS |
| wrist_mount_bolt | wrist_mount_nut | 9.5115e-12 | 40 | 2.6..5 | PASS |
| yaw_shaft | yaw_nut | 0 | 25 | 16.4..20.4 | PASS |
| shoulder_shaft | shoulder_nut | 0 | 70 | 62..66 | PASS |
| elbow_shaft | elbow_nut | 0 | 70 | 62..66 | PASS |
| wrist_shaft | wrist_nut | 0 | 70 | 62..66 | PASS |

See `fastener-audit.json`, the exact executed `audit.py`, and `execution-environment.json`. Physical threads, torque, tool access and engagement remain unverified.
