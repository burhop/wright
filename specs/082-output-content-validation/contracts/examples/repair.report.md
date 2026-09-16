# Process validation report

**Verdict:** HOLD
**Assessment:** `assessment-c15a88754bb042aeb37a84d3dfaad2bf`
**Assessment digest:** `7452e73f926b513a1feee4602eff33da82e0c91fce7760f2c40ba083d17d0bb5`
**Profile:** `structured-demo@2`
**Current as of:** `2026-09-16T21:00:00Z` — yes

## Summary

| Content verified | Requirements compliant | Complete | Release eligible |
|---|---|---|---|
| true | false | true | false |

## Requirements traceability

| Requirement | Check | Expected | Observed | Status | Evidence | Action |
|---|---|---|---|---|---|---|
| DEMO-001 — length\_mm is 100.0 +/- 0.2 mm inclusive | length | \{&quot;inclusive&quot;:true,&quot;operator&quot;:&quot;within&quot;,&quot;target&quot;:100.0,&quot;tolerance&quot;:0.2\} | \[\{&quot;frame&quot;:null,&quot;unit&quot;:&quot;mm&quot;,&quot;value&quot;:98\}\] | fail | \[&quot;subject:output-978a7a8171ca87007e969fe78ff2a81a92a35d86ccdeed9d9ca195f4a407a854@14e0945dff0d53884f02b154fd2bcf425ae913419e741d3af766a7e7a268d03b\#/length\_mm&quot;\] | revise\_output |
| DEMO-002 — part\_id is demo-plate | part-identity | \{&quot;expected&quot;:&quot;demo-plate&quot;,&quot;inclusive&quot;:true,&quot;operator&quot;:&quot;equals&quot;\} | \[\{&quot;frame&quot;:null,&quot;unit&quot;:null,&quot;value&quot;:&quot;demo-plate&quot;\}\] | pass | \[&quot;subject:output-978a7a8171ca87007e969fe78ff2a81a92a35d86ccdeed9d9ca195f4a407a854@14e0945dff0d53884f02b154fd2bcf425ae913419e741d3af766a7e7a268d03b\#/part\_id&quot;\] |  |
| DEMO-003 — Output is a JSON object with required fields | part-identity | \{&quot;expected&quot;:&quot;demo-plate&quot;,&quot;inclusive&quot;:true,&quot;operator&quot;:&quot;equals&quot;\} | \[\{&quot;frame&quot;:null,&quot;unit&quot;:null,&quot;value&quot;:&quot;demo-plate&quot;\}\] | pass | \[&quot;subject:output-978a7a8171ca87007e969fe78ff2a81a92a35d86ccdeed9d9ca195f4a407a854@14e0945dff0d53884f02b154fd2bcf425ae913419e741d3af766a7e7a268d03b\#/part\_id&quot;\] |  |
| DEMO-003 — Output is a JSON object with required fields | object | \{&quot;expected&quot;:&quot;object&quot;,&quot;inclusive&quot;:true,&quot;operator&quot;:&quot;type&quot;\} | \[\{&quot;frame&quot;:null,&quot;unit&quot;:null,&quot;value&quot;:\{&quot;length\_mm&quot;:98,&quot;part\_id&quot;:&quot;demo-plate&quot;\}\}\] | pass | \[&quot;subject:output-978a7a8171ca87007e969fe78ff2a81a92a35d86ccdeed9d9ca195f4a407a854@14e0945dff0d53884f02b154fd2bcf425ae913419e741d3af766a7e7a268d03b\#&quot;\] |  |
| DEMO-003 — Output is a JSON object with required fields | length-present | \{&quot;inclusive&quot;:true,&quot;operator&quot;:&quot;exists&quot;\} | \[\{&quot;frame&quot;:null,&quot;unit&quot;:null,&quot;value&quot;:98\}\] | pass | \[&quot;subject:output-978a7a8171ca87007e969fe78ff2a81a92a35d86ccdeed9d9ca195f4a407a854@14e0945dff0d53884f02b154fd2bcf425ae913419e741d3af766a7e7a268d03b\#/length\_mm&quot;\] |  |

## Scope and limitations

- Geometry, manufacture and physical fit are not assessed.
