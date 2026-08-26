export const mountingPlateSmokeId = "HEADLESS-4-BLOCK-001";
export const mountingPlateExpectedFeatureIds = [
  "SMOKE_BASE",
  "SMOKE_HOLE_1",
  "SMOKE_HOLE_2",
  "SMOKE_HOLE_3",
  "SMOKE_HOLE_4",
];

const expectedCenters = [
  [-40, -20],
  [40, -20],
  [40, 20],
  [-40, 20],
];

function objectValue(value, message) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(message);
  }
  return value;
}

function exactNumber(value, expected, label) {
  if (typeof value !== "number" || value !== expected) {
    throw new Error(`${label} must be ${expected}; received ${String(value)}.`);
  }
  return value;
}

export function mountingPlateGenerationInstructions() {
  return `Interpret the supplied request as a small, tool-independent mounting-plate specification. Return ONLY this JSON shape with no Markdown fences or commentary:
{"kind":"mounting-plate","units":"mm","width":100,"height":60,"thickness":8,"holes":[{"diameter":8,"centerX":-40,"centerZ":-20},{"diameter":8,"centerX":40,"centerZ":-20},{"diameter":8,"centerX":40,"centerZ":20},{"diameter":8,"centerX":-40,"centerZ":20}]}

Do not emit BREP features, tool arguments, application-internal IDs, or extra fields. Before responding, verify that there are exactly four holes and the JSON matches the request.`;
}

export function parseMountingPlateSpec(text) {
  let parsed;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw Object.assign(
      new Error(
        "The AI output was not valid JSON for the typed mounting-plate specification.",
      ),
      { stepOutput: text },
    );
  }
  const spec = objectValue(
    parsed,
    "The AI output is not a specification object.",
  );
  if (spec.kind !== "mounting-plate" || spec.units !== "mm") {
    throw new Error("The AI output has the wrong specification kind or units.");
  }
  exactNumber(spec.width, 100, "width");
  exactNumber(spec.height, 60, "height");
  exactNumber(spec.thickness, 8, "thickness");
  if (!Array.isArray(spec.holes) || spec.holes.length !== 4) {
    throw new Error(
      "The mounting-plate specification must contain four holes.",
    );
  }
  spec.holes.forEach((candidate, index) => {
    const hole = objectValue(candidate, `Hole ${index + 1} is invalid.`);
    exactNumber(hole.diameter, 8, `hole ${index + 1} diameter`);
    exactNumber(
      hole.centerX,
      expectedCenters[index][0],
      `hole ${index + 1} centerX`,
    );
    exactNumber(
      hole.centerZ,
      expectedCenters[index][1],
      `hole ${index + 1} centerZ`,
    );
  });
  return spec;
}

export function compileMountingPlateSpecToBrepArguments(specValue) {
  const spec = parseMountingPlateSpec(JSON.stringify(specValue));
  const base = {
    type: "Primitive Cube",
    inputParams: {
      id: mountingPlateExpectedFeatureIds[0],
      sizeX: spec.width,
      sizeY: spec.thickness,
      sizeZ: spec.height,
      transform: {
        position: [-spec.width / 2, 0, -spec.height / 2],
        rotationEuler: [0, 0, 0],
        scale: [1, 1, 1],
      },
      boolean: { targets: [], operation: "NONE" },
    },
    persistentData: {},
    timestamp: null,
  };
  const holes = spec.holes.map((hole, index) => ({
    type: "Primitive Cylinder",
    inputParams: {
      id: mountingPlateExpectedFeatureIds[index + 1],
      radius: hole.diameter / 2,
      height: spec.thickness + 2,
      resolution: 48,
      transform: {
        position: [hole.centerX, -1, hole.centerZ],
        rotationEuler: [0, 0, 0],
        scale: [1, 1, 1],
      },
      boolean: {
        targets: [mountingPlateExpectedFeatureIds[0]],
        operation: "SUBTRACT",
      },
    },
    persistentData: {},
    timestamp: null,
  }));
  return {
    history: {
      features: [base, ...holes],
      idCounter: 5,
      expressions: "",
      pmiViews: [],
      metadata: {
        workflowSmokeId: mountingPlateSmokeId,
        title: "Four-hole mounting plate",
        units: "mm",
      },
      assemblyConstraints: [],
      assemblyConstraintIdCounter: 0,
    },
  };
}

export function mountingPlateInspectionAccepted(observation) {
  return (
    observation.stateFeatureCount === mountingPlateExpectedFeatureIds.length &&
    observation.historyFeatureCount ===
      mountingPlateExpectedFeatureIds.length &&
    observation.workflowSmokeId === mountingPlateSmokeId &&
    JSON.stringify(observation.ids) ===
      JSON.stringify(mountingPlateExpectedFeatureIds)
  );
}
