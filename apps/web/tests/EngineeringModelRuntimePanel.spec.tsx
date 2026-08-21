import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EngineeringModelRuntimePanel } from "../src/components/models/EngineeringModelRuntimePanel";
import { engineeringModelService } from "../src/services/engineering-model-service";
import type { EngineeringModelRuntimeTest } from "../src/services/engineering-model-service";

vi.mock("../src/services/engineering-model-service", async (loadOriginal) => {
  const original =
    await loadOriginal<
      typeof import("../src/services/engineering-model-service")
    >();
  return {
    ...original,
    engineeringModelService: {
      runStandardTest: vi.fn(),
      getStandardTestEvidence: vi.fn(),
      createWorkspaceBinding: vi.fn(),
      setWorkspaceBindingState: vi.fn(),
    },
  };
});

const tested: EngineeringModelRuntimeTest = {
  installation_id: "installation-one",
  installation_state: "ready",
  adapter_id: "wright-deterministic",
  adapter_version: "1.0.0",
  evidence: [
    {
      evidence_id: "evidence-one",
      state: "passed",
      material_digest: "a".repeat(64),
      observation_digest: "b".repeat(64),
      material: { vector_id: "predict-two", result: "passed" },
      observation: { timing_ms: 1 },
    },
  ],
};
const binding = {
  binding_id: "binding-one",
  binding_digest: "c".repeat(64),
  workspace_id: "workspace-one",
  installation_id: "installation-one",
  task_id: "predict",
  tool_name: "wright_model__wright_affine_test__predict",
  policy_snapshot_digest: "d".repeat(64),
  state: "enabled" as const,
};

describe("EngineeringModelRuntimePanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(
      engineeringModelService.getStandardTestEvidence,
    ).mockResolvedValue({
      ...tested,
      installation_state: "installed",
      evidence: [],
    });
    vi.mocked(engineeringModelService.runStandardTest).mockResolvedValue(
      tested,
    );
    vi.mocked(engineeringModelService.createWorkspaceBinding).mockResolvedValue(
      binding,
    );
    vi.mocked(
      engineeringModelService.setWorkspaceBindingState,
    ).mockResolvedValue({ ...binding, state: "disabled" });
  });

  it("requires mandatory evidence before workspace enablement", async () => {
    render(
      <EngineeringModelRuntimePanel
        installationId="installation-one"
        taskId="predict"
        workspaceId="workspace-one"
      />,
    );
    expect(
      await screen.findByText(/standard test required/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /enable for workspace/i }),
    ).toBeNull();

    fireEvent.click(
      screen.getByRole("button", { name: /run mandatory standard test/i }),
    );
    expect(await screen.findByText(/evidence-one/i)).toBeInTheDocument();
    expect(screen.getByText(/wright-deterministic 1.0.0/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /enable for workspace/i }),
    ).toBeEnabled();
  });

  it("enables and disables the exact typed workspace binding", async () => {
    vi.mocked(
      engineeringModelService.getStandardTestEvidence,
    ).mockResolvedValue(tested);
    render(
      <EngineeringModelRuntimePanel
        installationId="installation-one"
        taskId="predict"
        workspaceId="workspace-one"
      />,
    );
    fireEvent.click(
      await screen.findByRole("button", { name: /enable for workspace/i }),
    );
    expect(
      await screen.findByText(/wright_model__wright_affine_test__predict/i),
    ).toBeInTheDocument();
    expect(engineeringModelService.createWorkspaceBinding).toHaveBeenCalledWith(
      "workspace-one",
      "installation-one",
      "predict",
    );
    fireEvent.click(
      screen.getByRole("button", { name: /disable workspace capability/i }),
    );
    await waitFor(() =>
      expect(
        engineeringModelService.setWorkspaceBindingState,
      ).toHaveBeenCalledWith("workspace-one", "binding-one", "disabled"),
    );
  });

  it("shows resource rejection and stale-binding recovery without claiming readiness", async () => {
    vi.mocked(engineeringModelService.runStandardTest).mockRejectedValueOnce(
      Object.assign(
        new Error("Host memory is below the declared requirement."),
        {
          recovery: "Close other applications or choose a smaller variant.",
        },
      ),
    );
    render(
      <EngineeringModelRuntimePanel
        installationId="installation-one"
        taskId="predict"
        workspaceId="workspace-one"
      />,
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: /run mandatory standard test/i,
      }),
    );
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Host memory is below");
    expect(alert).toHaveTextContent("choose a smaller variant");
    expect(screen.queryByText(/ready for workspace/i)).toBeNull();
  });

  it("keeps a stale binding disabled until the user reviews a fresh one", async () => {
    vi.mocked(
      engineeringModelService.getStandardTestEvidence,
    ).mockResolvedValue(tested);
    vi.mocked(
      engineeringModelService.createWorkspaceBinding,
    ).mockRejectedValueOnce(
      Object.assign(new Error("The reviewed binding is stale."), {
        recovery: "Reload the workspace and review a fresh binding.",
      }),
    );
    render(
      <EngineeringModelRuntimePanel
        installationId="installation-one"
        taskId="predict"
        workspaceId="workspace-one"
      />,
    );
    fireEvent.click(
      await screen.findByRole("button", { name: /enable for workspace/i }),
    );
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("binding is stale");
    expect(alert).toHaveTextContent("review a fresh binding");
    expect(
      screen.queryByRole("button", { name: /disable workspace capability/i }),
    ).toBeNull();
  });
});
