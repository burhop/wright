import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EngineeringModelInstallFlow } from "../src/components/models/EngineeringModelInstallFlow";
import {
  engineeringModelService,
  type EngineeringModelPlan,
} from "../src/services/engineering-model-service";

vi.mock("../src/services/engineering-model-service", async (loadOriginal) => {
  const original =
    await loadOriginal<
      typeof import("../src/services/engineering-model-service")
    >();
  return {
    ...original,
    engineeringModelService: {
      createPlan: vi.fn(),
      confirmPlan: vi.fn(),
      getOperation: vi.fn(),
      cancelOperation: vi.fn(),
    },
  };
});

const plan: EngineeringModelPlan = {
  schema_version: "1.0",
  plan_id: "plan-1",
  plan_digest: "a".repeat(64),
  operation_kind: "install",
  model_id: "wright-affine-test",
  variant_id: "json-cpu-f64",
  state: "confirmable",
  effects: [
    {
      kind: "write",
      description: "Write four verified artifacts to Wright model data.",
      exact_bytes: 96,
      maximum_bytes: 96,
      reversible: true,
      safe_location: "Wright engineering-model content store",
    },
  ],
  blockers: [],
  requirements: {
    network: "none",
    credential: "none",
    license_action: "none",
    runtime_change: "separate_plan_only",
  },
  rollback: "Remove the inactive installation view.",
  cleanup: "Delete operation staging; verified shared cache may be retained.",
  expires_at: "2026-08-13T12:10:00Z",
};

const operation = {
  operation_id: "operation-1",
  state: "running",
  phase: "acquiring",
  progress: {
    completed_items: 1,
    total_items: 4,
    completed_bytes: 24,
    maximum_bytes: 96,
    message: "Verified one of four artifacts.",
  },
  cleanup_state: "not_needed",
};

describe("EngineeringModelInstallFlow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(engineeringModelService.createPlan).mockResolvedValue(plan);
    vi.mocked(engineeringModelService.confirmPlan).mockResolvedValue(operation);
    vi.mocked(engineeringModelService.getOperation).mockResolvedValue(
      operation,
    );
    vi.mocked(engineeringModelService.cancelOperation).mockResolvedValue({
      ...operation,
      state: "cancelling",
      cleanup_state: "pending",
    });
  });

  it("previews exact effects and requires explicit digest-bound confirmation", async () => {
    render(
      <EngineeringModelInstallFlow
        modelId="wright-affine-test"
        variantId="json-cpu-f64"
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: /review install effects/i }),
    );

    expect(
      await screen.findByText(/write four verified artifacts/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/96 B maximum/i)).toBeInTheDocument();
    expect(screen.getByText(/network: none/i)).toBeInTheDocument();
    expect(
      screen.getByText(/remove the inactive installation view/i),
    ).toBeInTheDocument();
    expect(engineeringModelService.confirmPlan).not.toHaveBeenCalled();

    fireEvent.click(
      screen.getByRole("button", { name: /confirm and install/i }),
    );
    await waitFor(() =>
      expect(engineeringModelService.confirmPlan).toHaveBeenCalledWith(
        "plan-1",
        "a".repeat(64),
      ),
    );
  });

  it("shows progress and offers idempotent cancellation", async () => {
    render(
      <EngineeringModelInstallFlow
        modelId="wright-affine-test"
        variantId="json-cpu-f64"
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: /review install effects/i }),
    );
    fireEvent.click(
      await screen.findByRole("button", { name: /confirm and install/i }),
    );

    expect(
      await screen.findByText(/verified one of four artifacts/i),
    ).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: /cancel installation/i }),
    );
    expect(await screen.findByText(/cancelling/i)).toBeInTheDocument();
    expect(engineeringModelService.cancelOperation).toHaveBeenCalledWith(
      "operation-1",
    );
  });

  it("renders blockers without a confirmation action", async () => {
    vi.mocked(engineeringModelService.createPlan).mockResolvedValueOnce({
      ...plan,
      state: "blocked",
      blockers: [
        {
          category: "runtime_missing",
          message: "The reviewed runtime adapter is not installed.",
          recovery: "Review the adapter through its separate plan.",
        },
      ],
    });
    render(<EngineeringModelInstallFlow modelId="candidate" variantId="cpu" />);
    fireEvent.click(
      screen.getByRole("button", { name: /review install effects/i }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "runtime adapter is not installed",
    );
    expect(
      screen.queryByRole("button", { name: /confirm and install/i }),
    ).toBeNull();
  });

  it("reports stable failure recovery and cleanup state", async () => {
    vi.mocked(engineeringModelService.confirmPlan).mockRejectedValueOnce(
      Object.assign(new Error("Artifact digest did not match."), {
        recovery: "Discard operation staging and retry from a fresh plan.",
      }),
    );
    render(
      <EngineeringModelInstallFlow
        modelId="wright-affine-test"
        variantId="json-cpu-f64"
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: /review install effects/i }),
    );
    fireEvent.click(
      await screen.findByRole("button", { name: /confirm and install/i }),
    );
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Artifact digest did not match");
    expect(alert).toHaveTextContent("Discard operation staging");
  });
});
