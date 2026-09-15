# Heater selection from recorded Modelica runs

Lowest demonstrated electrical setting: **800 W** across every supplied loss case.

Target90°C; time limit360s. All 1 declared candidate/loss baselines are present. Independent first-crossing interpolation, trapezoidal electrical/thermal energy integration and capacity-plus-ambient-loss balance use the actual sealed CSV samples. Refined simulations independently constrain DASSL maxStepSize to0.25s and tolerance1e-8; baseline1s/1e-6, with unchanged1s output grid. Engineering screening thresholds used here:1% energy consistency, time difference at most max(1s,1%), and1% final electrical-energy difference. These explicit numerical screening assumptions are not manufacturing approval or the campaign's future content-validation tests.

Thermal power equals electrical input times heater efficiency. Inverter efficiency is outside this thermal model; apply the supplied battery/inverter budget separately. The selected model retains upstream lumped storage, ambient losses and thermostat topology.

| Power W | Loss W/K | Time to90°C s | Refined difference s | Time met | Energy consistent | Stable |
|---|---|---|---|---|---|---|
| 800 | 0.85 | 263.5897141453984 | 0.00004039225524365975 | true | true | true |
