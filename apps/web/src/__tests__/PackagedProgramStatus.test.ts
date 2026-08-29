import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  canonicalProgramStatusDigest,
  decodeProgramStatusBundle,
  verifyProgramStatusIdentity,
} from "../services/program-status";

describe("packaged program status fallback", () => {
  it("is accepted by the same decoder and identity verifier as the browser", async () => {
    const raw = JSON.parse(
      readFileSync(
        resolve(
          process.cwd(),
          "../../src/wright_engineering/static/program-status/current.json",
        ),
        "utf8",
      ),
    );

    expect(raw.bundle_id).toBe(
      await canonicalProgramStatusDigest({
        source: raw.source,
        dashboard: raw.dashboard,
        supplement: raw.supplement,
      }),
    );
    await expect(verifyProgramStatusIdentity(raw)).resolves.toBeUndefined();
    expect(decodeProgramStatusBundle(raw).bundle_id).toBe(raw.bundle_id);
  });
});
