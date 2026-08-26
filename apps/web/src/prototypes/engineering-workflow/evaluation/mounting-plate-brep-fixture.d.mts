export interface MountingPlateHoleSpec {
  diameter: number;
  centerX: number;
  centerZ: number;
}

export interface MountingPlateSpec {
  kind: "mounting-plate";
  units: "mm";
  width: number;
  height: number;
  thickness: number;
  holes: MountingPlateHoleSpec[];
}

export const mountingPlateSmokeId: string;
export const mountingPlateExpectedFeatureIds: readonly string[];
export function mountingPlateGenerationInstructions(): string;
export function parseMountingPlateSpec(text: string): MountingPlateSpec;
export function compileMountingPlateSpecToBrepArguments(
  spec: MountingPlateSpec,
): { history: Record<string, unknown> };
export function mountingPlateInspectionAccepted(observation: {
  stateFeatureCount: unknown;
  historyFeatureCount: unknown;
  workflowSmokeId: unknown;
  ids: unknown;
}): boolean;
