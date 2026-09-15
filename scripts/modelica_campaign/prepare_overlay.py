"""Build a reviewed, separately identified Modelica kit overlay from pinned MIT source.

This does not edit the checkout, original kit assets, or a running installation.
The selected Docker build derives its new parameter facts using the real compiler.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

COMMIT = "62e26009a566d15b625493b0c3510bdd14b01c3b"
KIT = "wright-water-heater-v1"


def replace_one(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"Pinned source anchor count changed: {old[:100]!r}")
    return text.replace(old, new)


def prepare(source: Path, destination: Path) -> dict:
    commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if commit != COMMIT:
        raise ValueError("Unexpected upstream commit")
    destination.mkdir(parents=True, exist_ok=True)
    written = {}

    def read(relative):
        return (source / relative).read_text(encoding="utf-8")

    def write(relative, content):
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        written[relative] = hashlib.sha256(path.read_bytes()).hexdigest()

    # The original thermal storage, losses, thermostat and heat source topology
    # remain verbatim. Only this NEW model distinguishes electrical input and heat.
    model = read("models/CoffeeMachine.mo").replace("CoffeeMachine", "WrightWaterHeater")
    model = replace_one(model, "parameter SI.HeatCapacity boilerHeatCapacity = 500;", "parameter SI.HeatCapacity boilerHeatCapacity = 180;")
    model = replace_one(model, "parameter SI.Power heaterPowerRated = 1500;", "parameter SI.Power electricalPowerRated = 1500;\n  parameter SI.Efficiency heaterEfficiency = 0.92;")
    model = replace_one(model, "k = heaterPowerRated", "k = electricalPowerRated * heaterEfficiency")
    model = replace_one(model, "Modelica.Blocks.Continuous.Integrator heaterEnergy(y_start = 0);", "Modelica.Blocks.Continuous.Integrator heaterEnergy(y_start = 0);\n  Modelica.Blocks.Continuous.Integrator electricalEnergy(y_start = 0);")
    model = replace_one(model, 'output Real heaterOn(unit = "1");', 'output Real heaterOn(unit = "1");\n  output SI.Power electricalPowerW;\n  output SI.Energy electricalEnergyJ;')
    model = replace_one(model, "heaterOn = heaterCommand.y;", "heaterOn = heaterCommand.y;\n  electricalPowerW = electricalPowerRated * heaterCommand.y;\n  electricalEnergy.u = electricalPowerW;\n  electricalEnergyJ = electricalEnergy.y;")
    write("models/WrightWaterHeater.mo", "// Selected Wright campaign derivative of Casys CoffeeMachine, MIT; see LICENSE.\n" + model)

    kit = read("src/kits/coffee-machine.ts")
    kit = kit.replace("CoffeeMachine", "WrightWaterHeater").replace("coffee-machine-v1", KIT).replace("coffee-machine-result-normalizer", "wright-water-heater-result-normalizer")
    kit = kit.replace('import { extractWrightWaterHeaterMetrics } from "../domain/metrics.ts";', 'import { extractCoffeeMachineMetrics } from "../domain/metrics.ts";')
    start = kit.index('const SCENARIO_SOURCE =')
    end = kit.index('// These remain qualification decisions:')
    kit = kit[:start] + kit[end:]
    kit = kit.replace('import { readKitAsset, registerEmbeddedKitAsset }', 'import { readKitAsset }')
    kit = kit.replace('import { generatedKitAssetText } from "./generated-kit-assets.ts";\n', '')
    kit = replace_one(kit, 'id: "heater_power",\n    modelicaName: "heaterPowerRated",', 'id: "electrical_power",\n    modelicaName: "electricalPowerRated",')
    kit = replace_one(kit, 'description: "Rated electrical-to-thermal heater power.",', 'description: "Rated electrical input; delivered heat is electrical_power times heater_efficiency.",')
    kit = replace_one(kit, 'minimum: 500,\n    maximum: 3000,', 'minimum: 350,\n    maximum: 1800,')
    kit = replace_one(kit, 'defaultValue: 500,\n    minimum: 100,\n    maximum: 5000,', 'defaultValue: 180,\n    minimum: 90,\n    maximum: 480,')
    kit = replace_one(kit, 'minimum: 0.1,\n    maximum: 3,', 'minimum: 0.35,\n    maximum: 1.5,')
    kit = replace_one(kit, 'defaultValue: 5,\n    minimum: 0.1,\n    maximum: 50,', 'defaultValue: 5,\n    minimum: 0.6,\n    maximum: 5,')
    # Keep the upstream default 5 W/K within the new finite envelope, including
    # all explicitly supplied uncertainty cases 0.6..2.88 W/K.
    kit = replace_one(kit, 'const parameters: readonly ParameterDefinition[] = [', '''const parameters: readonly ParameterDefinition[] = [
  {
    id: "heater_efficiency", modelicaName: "heaterEfficiency",
    modelicaType: "Modelica.Units.SI.Efficiency", description: "Electrical input converted into heater heat; inverter losses are outside this model.",
    unit: "1", defaultValue: 0.92, minimum: 0.92, maximum: 0.94,
    conversion: { from: "1", to: "1", factor: 1, offset: 0 },
  },''')
    kit = replace_one(kit, 'const [model, parameterSchema, scenarioBytes] = await Promise.all([', 'const [model, parameterSchema] = await Promise.all([')
    kit = replace_one(kit, '    readKitAsset(SCENARIO_SOURCE),\n', '')
    kit = replace_one(kit, '  const scenarioSource = scenarioBytes.source;\n', '')
    kit = replace_one(kit, '  const scenario = parseScenario(scenarioSource);', '''  const scenarios = await Promise.all(SCENARIO_IDS.map(async (id) => {
    const url = new URL(`../../scenarios/${id}.json`, import.meta.url);
    const bytes = await readKitAsset(url);
    return { ...parseScenario(bytes.source), sourceUrl: url };
  }));''')
    kit = replace_one(kit, 'scenarios: [scenario],', 'scenarios,')
    kit = replace_one(kit, 'normalize: extractWrightWaterHeaterMetrics,', 'normalize: extractElectricalMetrics,')
    kit = replace_one(kit, '    producedMetrics: [', '''    producedMetrics: [
      { id: "electrical_energy", unit: "J", description: "Actual integrated electrical input energy.", required: true },
      { id: "electrical_power_peak", unit: "W", description: "Peak electrical input power.", required: true },''')
    kit = kit.replace('description: "Integrated heater energy.",', 'description: "Integrated delivered thermal energy (not electrical energy).",')
    kit = kit.replace('description: "Maximum heater power.",', 'description: "Maximum delivered thermal power (not electrical power).",')
    kit = replace_one(kit, '    sourceUrl: SCENARIO_SOURCE,', '    numericalControls: parseNumericalControls(parsed.numerical_controls),')
    kit = 'import { parseNumericalControls } from "../domain/wright-numerical-controls.ts";\n' + kit
    kit += '''
const SCENARIO_IDS = ["wright-300-baseline", "wright-300-refined", "wright-600-baseline", "wright-600-refined", "wright-700-baseline", "wright-700-refined"];

function extractElectricalMetrics(csv: string, scenario: SimulationScenario) {
  const result = extractCoffeeMachineMetrics(csv, scenario);
  const rows = csv.trim().split(/\\r?\\n/).map(line => line.split(",").map(cell => cell.trim().replace(/^"|"$/g, "")));
  const headers = rows[0];
  const energy = headers.indexOf("electricalEnergyJ"), power = headers.indexOf("electricalPowerW");
  if (energy < 0 || power < 0) throw new Error("Native CSV lacks required electrical energy/power outputs.");
  const values = rows.slice(1).map(row => ({ energy: Number(row[energy]), power: Number(row[power]) }));
  if (!values.length || values.some(v => !Number.isFinite(v.energy) || !Number.isFinite(v.power))) throw new Error("Native electrical output is not finite.");
  result.metrics.electrical_energy = { value: values.at(-1)!.energy, unit: "J" };
  result.metrics.electrical_power_peak = { value: Math.max(...values.map(v => v.power)), unit: "W" };
  return result;
}
'''
    write("src/kits/wright-water-heater.ts", kit)
    for horizon in (300, 600, 700):
        for label, step, tolerance in (("baseline", 1, 1e-6), ("refined", 0.25, 1e-8)):
            scenario_id = f"wright-{horizon}-{label}"
            write(f"scenarios/{scenario_id}.json", json.dumps({
                "id": scenario_id, "description": f"Selected water heater campaign {horizon} s; {label} solver controls; 1 s output grid.",
                "start_time_s": 0, "stop_time_s": horizon, "number_of_intervals": horizon,
                "solver": "dassl", "target_temperature": {"value": 90, "unit": "degC"},
                "numerical_controls": {"max_step_size_s": step, "tolerance": tolerance},
            }, indent=2) + "\n")
    generator = read("scripts/derive-modelica-parameter-schema.ts").replace("CoffeeMachine", "WrightWaterHeater")
    generator = replace_one(generator, '  "Modelica.Units.SI.Mass": "kg",', '  "Modelica.Units.SI.Efficiency": "1",\n  "Modelica.Units.SI.Mass": "kg",')
    write("scripts/derive-wright-parameter-schema.ts", generator)

    registry = read("src/kits/registry.ts")
    registry = 'import { loadWrightWaterHeaterKit } from "./wright-water-heater.ts";\n' + registry
    registry = replace_one(registry, 'const [coffeeMachine, linearThermalRamp]', 'const [coffeeMachine, linearThermalRamp, wrightWaterHeater]')
    registry = replace_one(registry, '    loadLinearThermalRampKit(),', '    loadLinearThermalRampKit(),\n    loadWrightWaterHeaterKit(),')
    registry = replace_one(registry, 'new KitRegistry([coffeeMachine, linearThermalRamp])', 'new KitRegistry([coffeeMachine, linearThermalRamp, wrightWaterHeater])')
    write("src/kits/registry.ts", registry)
    policy = read("src/domain/runtime-compatibility.ts")
    policy = replace_one(policy, '  "coffee-machine-v1@0.1.0":', '  "wright-water-heater-v1@0.1.0": QUALIFIED_KIT_RUNTIME,\n  "coffee-machine-v1@0.1.0":')
    write("src/domain/runtime-compatibility.ts", policy)
    controls = (Path(__file__).parent / "wright-numerical-controls.ts").read_text(encoding="utf-8")
    write("src/domain/wright-numerical-controls.ts", controls)
    types = read("src/domain/types.ts")
    types = 'import type { NumericalControls } from "./wright-numerical-controls.ts";\n' + types
    types = replace_one(types, '  numberOfIntervals: number;', '  numberOfIntervals: number;\n  numericalControls?: NumericalControls;')
    write("src/domain/types.ts", types)
    manifest = read("src/domain/simulation-manifest.ts")
    manifest = 'import { parseNumericalControls, type NumericalControls } from "./wright-numerical-controls.ts";\n' + manifest
    manifest = replace_one(manifest, '      number_of_intervals: number;', '      number_of_intervals: number;\n      numerical_controls?: NumericalControls;')
    manifest = replace_one(manifest, '    [],\n    "manifest.scenario.public",', '    ["numerical_controls"],\n    "manifest.scenario.public",')
    manifest = replace_one(manifest, '    number_of_intervals: intervals,', '    number_of_intervals: intervals,\n    ...(scenario.numerical_controls === undefined ? {} : { numerical_controls: parseNumericalControls(scenario.numerical_controls) }),')
    write("src/domain/simulation-manifest.ts", manifest)
    service = read("src/domain/service.ts")
    service = 'import { numericalArguments, numericalFlags } from "./wright-numerical-controls.ts";\n' + service
    service = replace_one(service, '    number_of_intervals: scenario.numberOfIntervals,', '    number_of_intervals: scenario.numberOfIntervals,\n    ...(scenario.numericalControls === undefined ? {} : { numerical_controls: scenario.numericalControls }),')
    service = replace_one(service, '    \'outputFormat="csv", fileNamePrefix="result", \' +', '    numericalArguments(scenario.numericalControls) + \'outputFormat="csv", fileNamePrefix="result", \' +')
    service = replace_one(service, '`simflags="-override=${overrides}");`,', '`simflags="-override=${overrides}${numericalFlags(scenario.numericalControls)}");`,')
    write("src/domain/service.ts", service)
    resume = read("src/application/resumable-simulation-service.ts")
    resume = 'import { numericalArguments, numericalFlags } from "../domain/wright-numerical-controls.ts";\n' + resume
    resume = replace_one(resume, '      number_of_intervals: scenario.numberOfIntervals,', '      number_of_intervals: scenario.numberOfIntervals,\n      ...(scenario.numericalControls === undefined ? {} : { numerical_controls: scenario.numericalControls }),')
    resume = replace_one(resume, 'lowering: { id: "modelica-omc-lowering", version: "1.0.0" },', 'lowering: scenario.numericalControls === undefined ? { id: "modelica-omc-lowering", version: "1.0.0" } : { id: "wright-modelica-numerical-lowering", version: "1.0.0" },')
    resume = replace_one(resume, '    numberOfIntervals: scenario.number_of_intervals,', '    numberOfIntervals: scenario.number_of_intervals,\n    ...(scenario.numerical_controls === undefined ? {} : { numericalControls: scenario.numerical_controls }),')
    resume = replace_one(resume, 'manifest.lowering.id !== "modelica-omc-lowering" ||', 'manifest.lowering.id !== (manifest.scenario.public.numerical_controls === undefined ? "modelica-omc-lowering" : "wright-modelica-numerical-lowering") ||')
    resume = replace_one(resume, '    `method="${scenario.solver}", outputFormat="csv", fileNamePrefix="result", ` +', '    numericalArguments(scenario.numerical_controls) + `method="${scenario.solver}", outputFormat="csv", fileNamePrefix="result", ` +')
    resume = replace_one(resume, '`simflags="-override=${overrides}");`,', '`simflags="-override=${overrides}${numericalFlags(scenario.numerical_controls)}");`,')
    write("src/application/resumable-simulation-service.ts", resume)
    schema = '''{ type: "object", additionalProperties: false,
      properties: { max_step_size_s: { enum: [1, 0.25] }, tolerance: { enum: [1e-6, 1e-8] } },
      required: ["max_step_size_s", "tolerance"],
      oneOf: [{ properties: { max_step_size_s: { const: 1 }, tolerance: { const: 1e-6 } } },
              { properties: { max_step_size_s: { const: 0.25 }, tolerance: { const: 1e-8 } } }] }'''
    for relative, anchor in [("src/tools/resumable-results.ts", '  number_of_intervals: { type: "integer", minimum: 1 },'),
                             ("src/tools/results.ts", '    number_of_intervals: { type: "integer" },')]:
        output_schema = replace_one(read(relative), anchor, anchor + '\n    numerical_controls: ' + schema + ',')
        write(relative, output_schema)
    server = replace_one(read("server.ts"), 'name: "mcp-modelica",', 'name: "wright-modelica-campaign",')
    server = 'import { registerRecordedExport } from "./src/recorded-export.ts";\n' + server
    server = 'import { registerStudySummary } from "./src/study-summary.ts";\n' + server
    server = replace_one(server, '  const viewerRegistration = registerResultsViewer(', '  registerRecordedExport(server, resumableService);\n  const viewerRegistration = registerResultsViewer(')
    server = replace_one(server, '  registerRecordedExport(server, resumableService);', '  registerRecordedExport(server, resumableService);\n  registerStudySummary(server, resumableService);')
    write("server.ts", server)
    write("src/recorded-export.ts", (Path(__file__).parent / "recorded-export.ts").read_text(encoding="utf-8"))
    write("src/study-summary.ts", (Path(__file__).parent / "study-summary.ts").read_text(encoding="utf-8"))
    release = read("src/release-identity.ts")
    release = replace_one(release, 'PACKAGE_VERSION = "0.6.5"', 'PACKAGE_VERSION = "0.6.5+wright.1"')
    release = replace_one(release, 'Release identity: @casys/mcp-modelica ${PACKAGE_VERSION}.', 'Selected derivative identity: wright-modelica-campaign ${PACKAGE_VERSION}; based on @casys/mcp-modelica 0.6.5 commit 62e26009a566d15b625493b0c3510bdd14b01c3b, MIT.')
    write("src/release-identity.ts", release)
    write("LICENSE", read("LICENSE"))
    result = {"kit_id": KIT, "kit_version": "0.1.0", "upstream_commit": commit, "overlay_sha256": written}
    (destination / "overlay-manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.destination), indent=2))
