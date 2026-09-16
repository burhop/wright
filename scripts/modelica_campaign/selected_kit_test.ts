import { createDefaultKitRegistry } from "/app/src/kits/registry.ts";
import { numericalArguments, numericalFlags, parseNumericalControls } from "/app/src/domain/wright-numerical-controls.ts";
import { runtimeCompatibilityPolicy } from "/app/src/domain/runtime-compatibility.ts";
import { validateExportInput } from "/app/src/recorded-export.ts";
import { observeCsv } from "/app/src/study-summary.ts";

function assert(value: unknown, message: string): asserts value {
  if (!value) throw new Error(message);
}

Deno.test("selected numerical authority rejects unknown pairs and caller flags", () => {
  for (const value of [undefined, null, [], {}, { max_step_size_s: 1, tolerance: 1e-8 },
    { max_step_size_s: 0.25, tolerance: 1e-6 }, { max_step_size_s: 0, tolerance: 1e-6 },
    { max_step_size_s: 1, tolerance: 1e-6, simflags: "-override=x=1" }]) {
    let rejected = false;
    try { parseNumericalControls(value); } catch { rejected = true; }
    assert(rejected, "Unqualified numerical control was accepted");
  }
  assert(numericalArguments() === "" && numericalFlags() === "", "Original lowering must remain unchanged");
  assert(numericalFlags({ max_step_size_s: 0.25, tolerance: 1e-8 }) === " -maxStepSize=0.25", "Refinement must constrain internal solver steps");
});

Deno.test("new kit identity retains original kit bounds and compiler agreement", async () => {
  const kits = (await createDefaultKitRegistry()).list();
  const original = kits.find(kit => kit.id === "coffee-machine-v1")!;
  const selected = kits.find(kit => kit.id === "wright-water-heater-v1")!;
  assert(original.parameters.find(p => p.id === "heater_power")!.minimum === 500, "Original approved power range changed");
  assert(original.parameters.find(p => p.id === "boiler_heat_capacity")!.minimum === 100, "Original approved vessel range changed");
  assert(original.scenarios.length === 1 && original.scenarios[0].stopTimeS === 900, "Original scenario changed");
  assert(!original.scenarios[0].numericalControls, "Original numerical lowering changed");
  assert(selected.parameterSchemaSource && selected.scenarios.length === 6, "Compiler facts or fixed scenarios missing");
  assert(selected.parameters.find(p => p.id === "electrical_power")!.minimum === 350, "Dataset range missing");
  assert(selected.parameters.find(p => p.id === "boiler_heat_capacity")!.minimum === 90, "Dataset vessel range missing");
  assert(!selected.parameters.find(p => p.id === "heater_power"), "Thermal power must not be mislabeled as electrical input");
  for (const horizon of [300, 600, 700]) {
    const pair = selected.scenarios.filter(s => s.stopTimeS === horizon);
    assert(pair.length === 2 && pair.every(s => s.numberOfIntervals === horizon), "Output grid must remain one second across solver refinements");
  }
});

Deno.test("unknown kit identities never inherit compatibility qualification", () => {
  let rejected = false;
  try { runtimeCompatibilityPolicy({ id: "wright-water-heater-v1", version: "0.2.0" }); } catch { rejected = true; }
  assert(rejected, "Unreviewed kit version inherited native runtime authority");
});

Deno.test("export input rejects cross-attempt, cross-dataset and arbitrary path authority", () => {
  const input = { dataset_id: "water-heater-sizing-01", attempt_id: "attempt-001", request_id: "water-heater-sizing-01-attempt-001-p350-baseline", expected_manifest_sha256: "a".repeat(64) };
  validateExportInput(input);
  for (const value of [{ ...input, attempt_id: "attempt-002" }, { ...input, dataset_id: "water-heater-sizing-02" },
    { ...input, output_path: "/arbitrary" }, { ...input, request_id: "../../outside" }, { ...input, attempt_id: "attempt-../outside" }]) {
    let rejected = false;
    try { validateExportInput(value); } catch { rejected = true; }
    assert(rejected, "Unscoped export authority was accepted");
  }
});

Deno.test("independent sample integration and target interpolation preserve energy units", () => {
  const source = '"time","waterTemperatureC","electricalPowerW","electricalEnergyJ","heaterPowerW","heaterEnergyJ"\n0,20,10,0,9,0\n1,21,10,10,9,9\n';
  const parameters = { water_mass: { value: 0 }, boiler_heat_capacity: { value: 9 }, heat_loss_conductance: { value: 0 }, ambient_temperature: { value: 20 } };
  const result = observeCsv(source, parameters, 20.5);
  assert(result.timeToTarget === .5 && result.electricalIntegral === 10 && result.thermalIntegral === 9 && result.balanceErrorJ === 0, "Independent time/energy observations are inconsistent");
  assert(observeCsv(source, parameters, 90).timeToTarget === null, "Unreached target must remain absent");
  let rejected = false;
  try { observeCsv(source.replace("1,21", "-1,21"), parameters, 20.5); } catch { rejected = true; }
  assert(rejected, "Backward solver time was accepted");
});
