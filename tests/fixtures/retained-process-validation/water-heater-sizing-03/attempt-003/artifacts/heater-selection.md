# Heater selection from recorded Modelica runs

Lowest demonstrated electrical setting: **1500 W** across every supplied loss case.

Target90°C; time limit400s. All 9 declared candidate/loss baselines are present. Independent first-crossing interpolation, trapezoidal electrical/thermal energy integration and capacity-plus-ambient-loss balance use the actual sealed CSV samples. Refined simulations independently constrain DASSL maxStepSize to0.25s and tolerance1e-8; baseline1s/1e-6, with unchanged1s output grid. Engineering screening thresholds used here:1% energy consistency, time difference at most max(1s,1%), and1% final electrical-energy difference. These explicit numerical screening assumptions are not manufacturing approval or the campaign's future content-validation tests.

Thermal power equals electrical input times heater efficiency. Inverter efficiency is outside this thermal model; apply the supplied battery/inverter budget separately. The selected model retains upstream lumped storage, ambient losses and thermostat topology.

| Power W | Loss W/K | Time to90°C s | Refined difference s | Time met | Energy consistent | Stable |
|---|---|---|---|---|---|---|
| 1200 | 1.92 | 446.0158176899982 | not demonstrated | false | true | false |
| 1200 | 2.4 | 453.5667085910589 | not demonstrated | false | true | false |
| 1200 | 2.88 | 461.47347145743595 | not demonstrated | false | true | false |
| 1500 | 1.92 | 352.17089274772275 | 1.0627047686284641e-7 | true | true | true |
| 1500 | 2.4 | 356.8126793682013 | 1.6599500440861448e-7 | true | true | true |
| 1500 | 2.88 | 361.62317608894085 | 2.3903129431346315e-7 | true | true | true |
| 1800 | 1.92 | 290.97150510989445 | not demonstrated | true | true | false |
| 1800 | 2.4 | 294.11164769873557 | not demonstrated | true | true | false |
| 1800 | 2.88 | 297.3446680201564 | not demonstrated | true | true | false |
