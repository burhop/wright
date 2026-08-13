import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EngineeringModelMaintenance } from "../src/components/models/EngineeringModelMaintenance";
import { engineeringModelService } from "../src/services/engineering-model-service";

vi.mock("../src/services/engineering-model-service", async (loadOriginal) => {
  const original =
    await loadOriginal<
      typeof import("../src/services/engineering-model-service")
    >();
  return {
    ...original,
    engineeringModelService: {
      getInstallationMaintenance: vi.fn(),
      compareInstallationUpdate: vi.fn(),
      createMaintenancePlan: vi.fn(),
      confirmPlan: vi.fn(),
      setModelReferenceState: vi.fn(),
    },
  };
});

const status = {
  installation_id: "installation-one",
  state: "ready",
  active: true,
  reclaimable_bytes: 0,
  blockers: [
    {
      kind: "workflow",
      owner_id: "workflow-one",
      reference_id: "reference-one",
    },
  ],
  references: [
    {
      kind: "workflow",
      owner_id: "workflow-one",
      reference_id: "reference-one",
      state: "active",
    },
  ],
};

const maintenancePlan = (operationKind: "rollback" | "export") => ({
  schema_version: "1.0" as const,
  plan_id: `plan-${operationKind}`,
  plan_digest: "b".repeat(64),
  operation_kind: operationKind,
  model_id: "wright-affine-test",
  variant_id: "json-cpu-f64",
  state: "confirmable",
  effects: [
    {
      kind: operationKind === "export" ? "export" : "write",
      description: `Apply exact ${operationKind} effects.`,
      maximum_bytes: 128,
      reversible: true,
    },
  ],
  blockers: [],
  requirements: {
    network: "none",
    credential: "none",
    license_action: "none",
    runtime_change: "separate_plan_only",
  },
  rollback: "Keep the active revision until commit.",
  cleanup: "Report cleanup truthfully.",
  expires_at: "2099-08-13T12:10:00Z",
});

describe("EngineeringModelMaintenance", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(
      engineeringModelService.getInstallationMaintenance,
    ).mockResolvedValue(status);
    vi.mocked(
      engineeringModelService.compareInstallationUpdate,
    ).mockResolvedValue({
      changed_facets: ["artifacts", "schemas"],
      requires_retest: true,
      diff_digest: "a".repeat(64),
    });
    vi.mocked(engineeringModelService.createMaintenancePlan).mockImplementation(
      async (_installationId, operationKind) =>
        maintenancePlan(operationKind as "rollback" | "export"),
    );
    vi.mocked(engineeringModelService.confirmPlan).mockImplementation(
      async (planId) => ({
        operation_id: `operation-${planId}`,
        state: "succeeded",
        phase: "complete",
        progress: {
          completed_items: 1,
          total_items: 1,
          completed_bytes: 128,
          maximum_bytes: 128,
        },
        cleanup_state: "clean",
        result:
          planId === "plan-export"
            ? { artifact_id: "export-one", sha256: "b".repeat(64), size: 128 }
            : { state: "testing_required" },
      }),
    );
    vi.mocked(engineeringModelService.setModelReferenceState).mockResolvedValue(
      { reference_id: "reference-one", state: "archived" },
    );
  });

  it("compares semantic changes and keeps rollback explicit", async () => {
    render(
      <EngineeringModelMaintenance
        installationId="installation-one"
        modelId="wright-affine-test"
        variantId="json-cpu-f64"
      />,
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: /compare available revision/i,
      }),
    );
    expect(await screen.findByText(/artifacts, schemas/i)).toBeInTheDocument();
    expect(screen.getByText(/standard retest required/i)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText(/rollback installation identity/i), {
      target: { value: "installation-zero" },
    });
    fireEvent.click(screen.getByRole("button", { name: /prepare rollback/i }));
    await waitFor(() =>
      expect(
        engineeringModelService.createMaintenancePlan,
      ).toHaveBeenCalledWith(
        "installation-one",
        "rollback",
        "installation-zero",
      ),
    );
  });

  it("explains blocked purge, archives references, and exports by opaque identity", async () => {
    render(
      <EngineeringModelMaintenance
        installationId="installation-one"
        modelId="wright-affine-test"
        variantId="json-cpu-f64"
      />,
    );
    expect(await screen.findByText(/workflow-one/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /purge verified bytes/i }),
    ).toBeDisabled();
    fireEvent.click(
      screen.getByRole("button", { name: /archive workflow-one/i }),
    );
    await waitFor(() =>
      expect(
        engineeringModelService.setModelReferenceState,
      ).toHaveBeenCalledWith("reference-one", "archived"),
    );
    fireEvent.click(
      screen.getByRole("button", { name: /create offline export/i }),
    );
    fireEvent.click(
      await screen.findByRole("button", { name: /confirm export/i }),
    );
    expect(await screen.findByText(/export-one/i)).toBeInTheDocument();
  });
});
