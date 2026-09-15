import { parseNumericalControls } from "../domain/wright-numerical-controls.ts";
import type { ModelicaKit, ParameterDefinition, SimulationScenario } from "../domain/types.ts";
import { extractCoffeeMachineMetrics } from "../domain/metrics.ts";
import {
  assertModelicaParameterAgreement,
  type IntentionallyUnqualifiedParameter,
  parseModelicaParameterSchema,
} from "./modelica-parameter-schema.ts";
import { readKitAsset } from "./kit-asset.ts";

const MODEL_SOURCE = new URL("../../models/WrightWaterHeater.mo", import.meta.url);
const PARAMETER_SCHEMA_SOURCE = new URL(
  "../../models/WrightWaterHeater.parameters.json",
  import.meta.url,
);
// These remain qualification decisions: public ids, narrative, valid ranges
// and the explicitly declared exposure conversion do not follow from Modelica.
const parameters: readonly ParameterDefinition[] = [
  {
    id: "heater_efficiency", modelicaName: "heaterEfficiency",
    modelicaType: "Modelica.Units.SI.Efficiency", description: "Electrical input converted into heater heat; inverter losses are outside this model.",
    unit: "1", defaultValue: 0.92, minimum: 0.92, maximum: 0.94,
    conversion: { from: "1", to: "1", factor: 1, offset: 0 },
  },
  {
    id: "initial_water_temperature",
    modelicaName: "initialWaterTemperature",
    modelicaType: "Modelica.Units.SI.Temperature",
    description: "Water and boiler temperature at t=0.",
    unit: "degC",
    defaultValue: 20,
    minimum: 0,
    maximum: 45,
    conversion: { from: "degC", to: "K", factor: 1, offset: 273.15 },
  },
  {
    id: "ambient_temperature",
    modelicaName: "ambientTemperature",
    modelicaType: "Modelica.Units.SI.Temperature",
    description: "Fixed ambient temperature used by the loss model.",
    unit: "degC",
    defaultValue: 20,
    minimum: -10,
    maximum: 50,
    conversion: { from: "degC", to: "K", factor: 1, offset: 273.15 },
  },
  {
    id: "electrical_power",
    modelicaName: "electricalPowerRated",
    modelicaType: "Modelica.Units.SI.Power",
    description: "Rated electrical input; delivered heat is electrical_power times heater_efficiency.",
    unit: "W",
    defaultValue: 1500,
    minimum: 350,
    maximum: 1800,
    conversion: { from: "W", to: "W", factor: 1, offset: 0 },
  },
  {
    id: "water_mass",
    modelicaName: "waterMass",
    modelicaType: "Modelica.Units.SI.Mass",
    description: "Water mass represented by the lumped thermal capacity.",
    unit: "kg",
    defaultValue: 0.5,
    minimum: 0.35,
    maximum: 1.5,
    conversion: { from: "kg", to: "kg", factor: 1, offset: 0 },
  },
  {
    id: "boiler_heat_capacity",
    modelicaName: "boilerHeatCapacity",
    modelicaType: "Modelica.Units.SI.HeatCapacity",
    description: "Thermal capacity of the boiler hardware.",
    unit: "J/K",
    defaultValue: 180,
    minimum: 90,
    maximum: 480,
    conversion: { from: "J/K", to: "J/K", factor: 1, offset: 0 },
  },
  {
    id: "heat_loss_conductance",
    modelicaName: "heatLossConductance",
    modelicaType: "Modelica.Units.SI.ThermalConductance",
    description: "Lumped thermal conductance from boiler to ambient.",
    unit: "W/K",
    defaultValue: 5,
    minimum: 0.6,
    maximum: 5,
    conversion: { from: "W/K", to: "W/K", factor: 1, offset: 0 },
  },
  {
    id: "setpoint_temperature",
    modelicaName: "setpointTemperature",
    modelicaType: "Modelica.Units.SI.Temperature",
    description: "Thermostat centre setpoint.",
    unit: "degC",
    defaultValue: 93,
    minimum: 70,
    maximum: 110,
    conversion: { from: "degC", to: "K", factor: 1, offset: 273.15 },
  },
  {
    id: "hysteresis",
    modelicaName: "hysteresis",
    modelicaType: "Modelica.Units.SI.TemperatureDifference",
    description: "Total thermostat hysteresis band.",
    unit: "K",
    defaultValue: 2,
    minimum: 0.1,
    maximum: 20,
    conversion: { from: "K", to: "K", factor: 1, offset: 0 },
  },
];

// `waterSpecificHeatCapacity` is a model capability, but no bounded agent
// override has been qualified for it. Naming that decision keeps the public
// contract unchanged without treating an unexposed Modelica parameter as an
// accidental omission.
const intentionallyUnqualified: readonly IntentionallyUnqualifiedParameter[] = [
  {
    modelicaName: "waterSpecificHeatCapacity",
    modelicaType: "Modelica.Units.SI.SpecificHeatCapacity",
    unit: "J/(kg.K)",
    defaultValue: 4180,
    reason:
      "The kit has no reviewed domain for a water material-property override; retain the model default.",
  },
];

export async function loadWrightWaterHeaterKit(): Promise<ModelicaKit> {
  const [model, parameterSchema] = await Promise.all([
    readKitAsset(MODEL_SOURCE),
    readKitAsset(PARAMETER_SCHEMA_SOURCE),
  ]);
  const modelSource = model.source;
  const parameterSchemaSource = parameterSchema.source;
  await assertModelicaParameterAgreement({
    modelName: "WrightWaterHeater",
    modelSource,
    schema: parseModelicaParameterSchema(parameterSchemaSource),
    parameters,
    intentionallyUnqualified,
  });
  const scenarios = await Promise.all(SCENARIO_IDS.map(async (id) => {
    const url = new URL(`../../scenarios/${id}.json`, import.meta.url);
    const bytes = await readKitAsset(url);
    return { ...parseScenario(bytes.source), sourceUrl: url };
  }));
  return {
    id: "wright-water-heater-v1",
    version: "0.1.0",
    description: "Lumped boiler/water electro-thermal model with losses and thermostat hysteresis.",
    modelName: "WrightWaterHeater",
    modelSource,
    modelSourceUrl: MODEL_SOURCE,
    parameterSchemaSource,
    parameterSchemaSourceUrl: PARAMETER_SCHEMA_SOURCE,
    parameters,
    scenarios,
    producedMetrics: [
      { id: "electrical_energy", unit: "J", description: "Actual integrated electrical input energy.", required: true },
      { id: "electrical_power_peak", unit: "W", description: "Peak electrical input power.", required: true },
      {
        id: "water_temperature_max",
        unit: "degC",
        description: "Maximum water temperature.",
        required: true,
      },
      {
        id: "time_to_target_temperature",
        unit: "s",
        description: "First sampled time at the scenario target; absent if not reached.",
        required: false,
      },
      {
        id: "heater_energy",
        unit: "J",
        description: "Integrated delivered thermal energy (not electrical energy).",
        required: true,
      },
      {
        id: "heater_power_peak",
        unit: "W",
        description: "Maximum delivered thermal power (not electrical power).",
        required: true,
      },
    ],
    resultNormalizer: {
      id: "wright-water-heater-result-normalizer",
      version: "1.0.0",
      normalize: extractElectricalMetrics,
    },
  };
}

function parseScenario(source: string): SimulationScenario {
  const parsed = JSON.parse(source) as Record<string, unknown>;
  const target = parsed.target_temperature as Record<string, unknown> | undefined;
  if (
    typeof parsed.id !== "string" ||
    typeof parsed.description !== "string" ||
    typeof parsed.start_time_s !== "number" ||
    typeof parsed.stop_time_s !== "number" ||
    typeof parsed.number_of_intervals !== "number" ||
    typeof parsed.solver !== "string" ||
    !target ||
    typeof target.value !== "number" ||
    typeof target.unit !== "string"
  ) {
    throw new Error("WrightWaterHeater scenario has an invalid schema.");
  }
  return {
    id: parsed.id,
    description: parsed.description,
    startTimeS: parsed.start_time_s,
    stopTimeS: parsed.stop_time_s,
    numberOfIntervals: parsed.number_of_intervals,
    solver: parsed.solver,
    targetTemperature: { value: target.value, unit: target.unit },
    source,
    numericalControls: parseNumericalControls(parsed.numerical_controls),
  };
}

const SCENARIO_IDS = ["wright-300-baseline", "wright-300-refined", "wright-600-baseline", "wright-600-refined", "wright-700-baseline", "wright-700-refined"];

function extractElectricalMetrics(csv: string, scenario: SimulationScenario) {
  const result = extractCoffeeMachineMetrics(csv, scenario);
  const rows = csv.trim().split(/\r?\n/).map(line => line.split(",").map(cell => cell.trim().replace(/^"|"$/g, "")));
  const headers = rows[0];
  const energy = headers.indexOf("electricalEnergyJ"), power = headers.indexOf("electricalPowerW");
  if (energy < 0 || power < 0) throw new Error("Native CSV lacks required electrical energy/power outputs.");
  const values = rows.slice(1).map(row => ({ energy: Number(row[energy]), power: Number(row[power]) }));
  if (!values.length || values.some(v => !Number.isFinite(v.energy) || !Number.isFinite(v.power))) throw new Error("Native electrical output is not finite.");
  result.metrics.electrical_energy = { value: values.at(-1)!.energy, unit: "J" };
  result.metrics.electrical_power_peak = { value: Math.max(...values.map(v => v.power)), unit: "W" };
  return result;
}
