import type { ModelicaKit, ParameterDefinition, SimulationScenario } from "../domain/types.ts";
import { extractCoffeeMachineMetrics } from "../domain/metrics.ts";
import {
  assertModelicaParameterAgreement,
  type IntentionallyUnqualifiedParameter,
  parseModelicaParameterSchema,
} from "./modelica-parameter-schema.ts";
import { readKitAsset, registerEmbeddedKitAsset } from "./kit-asset.ts";
import { generatedKitAssetText } from "./generated-kit-assets.ts";

const MODEL_SOURCE = new URL("../../models/CoffeeMachine.mo", import.meta.url);
const PARAMETER_SCHEMA_SOURCE = new URL(
  "../../models/CoffeeMachine.parameters.json",
  import.meta.url,
);
const SCENARIO_SOURCE = new URL("../../scenarios/heat-up-nominal.json", import.meta.url);
registerEmbeddedKitAsset(MODEL_SOURCE, generatedKitAssetText["models/CoffeeMachine.mo"]);
registerEmbeddedKitAsset(
  PARAMETER_SCHEMA_SOURCE,
  generatedKitAssetText["models/CoffeeMachine.parameters.json"],
);
registerEmbeddedKitAsset(SCENARIO_SOURCE, generatedKitAssetText["scenarios/heat-up-nominal.json"]);

// These remain qualification decisions: public ids, narrative, valid ranges
// and the explicitly declared exposure conversion do not follow from Modelica.
const parameters: readonly ParameterDefinition[] = [
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
    id: "heater_power",
    modelicaName: "heaterPowerRated",
    modelicaType: "Modelica.Units.SI.Power",
    description: "Rated electrical-to-thermal heater power.",
    unit: "W",
    defaultValue: 1500,
    minimum: 500,
    maximum: 3000,
    conversion: { from: "W", to: "W", factor: 1, offset: 0 },
  },
  {
    id: "water_mass",
    modelicaName: "waterMass",
    modelicaType: "Modelica.Units.SI.Mass",
    description: "Water mass represented by the lumped thermal capacity.",
    unit: "kg",
    defaultValue: 0.5,
    minimum: 0.1,
    maximum: 3,
    conversion: { from: "kg", to: "kg", factor: 1, offset: 0 },
  },
  {
    id: "boiler_heat_capacity",
    modelicaName: "boilerHeatCapacity",
    modelicaType: "Modelica.Units.SI.HeatCapacity",
    description: "Thermal capacity of the boiler hardware.",
    unit: "J/K",
    defaultValue: 500,
    minimum: 100,
    maximum: 5000,
    conversion: { from: "J/K", to: "J/K", factor: 1, offset: 0 },
  },
  {
    id: "heat_loss_conductance",
    modelicaName: "heatLossConductance",
    modelicaType: "Modelica.Units.SI.ThermalConductance",
    description: "Lumped thermal conductance from boiler to ambient.",
    unit: "W/K",
    defaultValue: 5,
    minimum: 0.1,
    maximum: 50,
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

export async function loadCoffeeMachineKit(): Promise<ModelicaKit> {
  const [model, parameterSchema, scenarioBytes] = await Promise.all([
    readKitAsset(MODEL_SOURCE),
    readKitAsset(PARAMETER_SCHEMA_SOURCE),
    readKitAsset(SCENARIO_SOURCE),
  ]);
  const modelSource = model.source;
  const parameterSchemaSource = parameterSchema.source;
  const scenarioSource = scenarioBytes.source;
  await assertModelicaParameterAgreement({
    modelName: "CoffeeMachine",
    modelSource,
    schema: parseModelicaParameterSchema(parameterSchemaSource),
    parameters,
    intentionallyUnqualified,
  });
  const scenario = parseScenario(scenarioSource);
  return {
    id: "coffee-machine-v1",
    version: "0.1.0",
    description: "Lumped boiler/water electro-thermal model with losses and thermostat hysteresis.",
    modelName: "CoffeeMachine",
    modelSource,
    modelSourceUrl: MODEL_SOURCE,
    parameterSchemaSource,
    parameterSchemaSourceUrl: PARAMETER_SCHEMA_SOURCE,
    parameters,
    scenarios: [scenario],
    producedMetrics: [
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
        description: "Integrated heater energy.",
        required: true,
      },
      {
        id: "heater_power_peak",
        unit: "W",
        description: "Maximum heater power.",
        required: true,
      },
    ],
    resultNormalizer: {
      id: "coffee-machine-result-normalizer",
      version: "1.0.0",
      normalize: extractCoffeeMachineMetrics,
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
    throw new Error("CoffeeMachine scenario has an invalid schema.");
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
    sourceUrl: SCENARIO_SOURCE,
  };
}
