# Heater selection from recorded Modelica runs

No setting has demonstrated every declared time, energy and numerical-stability criterion in the supplied completed runs.

Target90°C; time limit180s. All 1 declared candidate/loss baselines are present. Independent first-crossing interpolation, trapezoidal electrical/thermal energy integration and capacity-plus-ambient-loss balance use the actual sealed CSV samples. Refined simulations independently constrain DASSL maxStepSize to0.25s and tolerance1e-8; baseline1s/1e-6, with unchanged1s output grid. Engineering screening thresholds used here:1% energy consistency, time difference at most max(1s,1%), and1% final electrical-energy difference. These explicit numerical screening assumptions are not manufacturing approval or the campaign's future content-validation tests.

Thermal power equals electrical input times heater efficiency. Inverter efficiency is outside this thermal model; apply the supplied battery/inverter budget separately. The selected model retains upstream lumped storage, ambient losses and thermostat topology.

| Power W | Loss W/K | Time to90°C s | Refined difference s | Time met | Energy consistent | Stable |
|---|---|---|---|---|---|---|
| 350 | 0.6 | not reached | not demonstrated | false | true | false |
