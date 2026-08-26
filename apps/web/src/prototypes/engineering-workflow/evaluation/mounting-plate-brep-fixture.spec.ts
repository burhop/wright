import { describe, expect, it } from "vitest";

import {
  compileMountingPlateSpecToBrepArguments,
  mountingPlateExpectedFeatureIds,
  parseMountingPlateSpec,
} from "./mounting-plate-brep-fixture.mjs";

const specification = {
  kind: "mounting-plate",
  units: "mm",
  width: 100,
  height: 60,
  thickness: 8,
  holes: [
    { diameter: 8, centerX: -40, centerZ: -20 },
    { diameter: 8, centerX: 40, centerZ: -20 },
    { diameter: 8, centerX: 40, centerZ: 20 },
    { diameter: 8, centerX: -40, centerZ: 20 },
  ],
} as const;

describe("mounting plate BREP diagnostic fixture", () => {
  it("keeps the AI result tool-independent and compiles exact BREP arguments deterministically", () => {
    const parsed = parseMountingPlateSpec(JSON.stringify(specification));
    const argumentsValue = compileMountingPlateSpecToBrepArguments(parsed);
    const features = argumentsValue.history.features as Array<{
      inputParams: { id: string; boolean: { targets: string[] } };
    }>;

    expect(features.map(({ inputParams }) => inputParams.id)).toEqual(
      mountingPlateExpectedFeatureIds,
    );
    expect(
      features.slice(1).map(({ inputParams }) => inputParams.boolean.targets),
    ).toEqual([["SMOKE_BASE"], ["SMOKE_BASE"], ["SMOKE_BASE"], ["SMOKE_BASE"]]);
  });

  it("rejects application-internal BREP history as the AI task output", () => {
    expect(() =>
      parseMountingPlateSpec(
        JSON.stringify({ history: { features: [], idCounter: 0 } }),
      ),
    ).toThrow("wrong specification kind or units");
  });
});
