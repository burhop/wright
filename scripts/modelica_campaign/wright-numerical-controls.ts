import { ValidationError } from "./errors.ts";

/** Server-owned selected kit controls; no free-form flags or solver input. */
export interface NumericalControls {
  max_step_size_s: number;
  tolerance: number;
}

export function parseNumericalControls(value: unknown): NumericalControls {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new ValidationError("Selected numerical controls must be a bounded object.");
  }
  const fields = value as Record<string, unknown>;
  if (Object.keys(fields).sort().join(",") !== "max_step_size_s,tolerance") {
    throw new ValidationError("Selected numerical controls have unexpected keys.");
  }
  const step = fields.max_step_size_s, tolerance = fields.tolerance;
  if (!((step === 1 && tolerance === 1e-6) || (step === 0.25 && tolerance === 1e-8))) {
    throw new ValidationError("Only the separately qualified baseline/refined control pairs are allowed.");
  }
  return { max_step_size_s: step, tolerance };
}

export function numericalArguments(controls?: NumericalControls): string {
  if (controls === undefined) return "";
  return `tolerance=${parseNumericalControls(controls).tolerance}, `;
}

export function numericalFlags(controls?: NumericalControls): string {
  if (controls === undefined) return "";
  return ` -maxStepSize=${parseNumericalControls(controls).max_step_size_s}`;
}
