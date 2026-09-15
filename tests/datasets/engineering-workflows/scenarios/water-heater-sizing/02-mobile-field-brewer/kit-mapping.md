# Requested quantity mapping worksheet
The uploaded names are human descriptions. Populate actual API names only after reading the approved kit's schema.
| Requested quantity | Unit | Source |
|---|---|---|
| Water mass | kg | parameters.csv |
| Start/target/ambient temperature | °C | parameters.csv |
| Effective vessel heat capacity | J/K | parameters.csv |
| Linear ambient loss coefficient | W/K | parameters.csv |
| Electrical-to-thermal efficiency | dimensionless 0..1 | parameters.csv |
| Candidate electrical power | W | power-candidates.csv |
| Maximum heat-up time | s | parameters.csv |
| Simulation stop time/output interval | s | parameters.csv |
A missing capability is an explicit blocker, not consent to replace the kit or alter the physical brief. Temperature conversion to Kelvin must be recorded if the kit uses absolute-temperature SI values. Do not sum a Celsius offset into a temperature difference.
