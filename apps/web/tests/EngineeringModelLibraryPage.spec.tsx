import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EngineeringModelLibraryPage } from "../src/components/pages/EngineeringModelLibraryPage";
import { engineeringModelService } from "../src/services/engineering-model-service";

vi.mock("../src/services/engineering-model-service", async (loadOriginal) => {
  const original =
    await loadOriginal<
      typeof import("../src/services/engineering-model-service")
    >();
  return {
    ...original,
    engineeringModelService: {
      listCatalog: vi.fn(),
      getCatalogModel: vi.fn(),
      listInstallations: vi.fn(),
    },
  };
});

const snapshot = {
  snapshot_id: "wright-models-bundled-1",
  catalog_digest: "a".repeat(64),
  freshness: "bundled",
  offline: true,
};

const generated = {
  model_id: "wright-affine-test",
  display_name: "Wright Affine Test Model",
  description: "Generated deterministic lifecycle fixture.",
  tasks: ["predict"],
  source: {
    kind: "wright",
    uri: "wright://generated/affine-test",
    immutable_revision: "fixture-revision-1",
  },
  license: {
    expression: "MIT",
    attribution: "Wright contributors",
    redistribution: "allowed",
  },
  readiness: "approved",
  compatibility: { state: "compatible", reasons: [] },
  evidence: {
    source: "bundled",
    license: "bundled",
    artifact: "bundled",
    runtime: "bundled",
    compatibility: "cached",
    security: "bundled",
    test: "bundled",
  },
  limitations: [
    {
      limitation_id: "test-only",
      description: "Not a production engineering model.",
      severity: "critical",
    },
  ],
  variants: [
    {
      variant_id: "json-cpu-f64",
      format: "wright-affine-json",
      accelerator: "cpu",
      resources: {
        download_bytes: 96,
        installed_bytes: 96,
        ram_bytes: 1_048_576,
      },
      runtime: { adapter_id: "wright-deterministic" },
    },
  ],
  blockers: [],
  generator: {
    kind: "deterministic_recipe",
    recipe:
      "Generate canonical JSON coefficients with scale=2.0 and offset=1.0.",
    inputs: { scale: 2, offset: 1 },
    constraints: ["JSON data only; no executable code or model weights."],
    manifest_digest: "b".repeat(64),
    artifact_set_digest: "c".repeat(64),
  },
  manifest_digest: "b".repeat(64),
  entry_digest: "d".repeat(64),
  snapshot,
};

const pointnet = {
  ...generated,
  model_id: "keras-io-pointnet",
  display_name: "Keras PointNet ModelNet10 Candidate",
  description: "Pinned public point-cloud classification candidate.",
  tasks: ["point_cloud_classification"],
  source: {
    kind: "hugging_face",
    uri: "https://huggingface.co/keras-io/PointNet",
    immutable_revision: "308acfe5d36d9bb34215d1766f13fac612abe18c",
  },
  readiness: "needs_review",
  compatibility: {
    state: "uncertain",
    reasons: ["No approved runtime adapter is installed."],
  },
  evidence: { ...generated.evidence, runtime: "absent", test: "absent" },
  blockers: [
    {
      category: "runtime_missing",
      message: "No approved runtime adapter is installed.",
      recovery: "Review the adapter through a separate runtime plan.",
    },
  ],
  generator: null,
};

const chatterSource = {
  ...generated,
  model_id: "wright-chatter",
  display_name: "Wright Chatter Screening Source",
  description: "Private source record for explicit local qualification.",
  tasks: ["screen_chatter_candidates"],
  source: {
    kind: "offline",
    uri: "wright://internal/chatter/source",
    immutable_revision: "4eeb36dbfede3c194c43b3d2039abd5860a675f6",
  },
  license: {
    expression: "LicenseRef-Wright-Internal-Chatter",
    attribution: "Wright-owned internal source boundary.",
    redistribution: "prohibited",
  },
  readiness: "needs_review",
  compatibility: {
    state: "uncertain",
    reasons: ["Exact local serving artifacts are absent."],
  },
  evidence: {
    ...generated.evidence,
    artifact: "absent",
    test: "absent",
  },
  variants: [],
  blockers: [
    {
      category: "local_qualification_required",
      message: "No exact locally qualified serving revision is attached.",
      recovery: "Run the explicit trusted local qualification.",
    },
  ],
  generator: null,
  qualification: {
    dataset: "Dataset 2 process-only features",
    dataset_digest: "1".repeat(64),
    feature_count: 37,
    membership: {
      splitter: "GroupShuffleSplit",
      random_state: 42,
      train_groups: 96,
      validation_groups: 24,
      overlap_groups: 0,
    },
    recipe: { family: "RandomForestClassifier", n_estimators: 500 },
    serving_boundary:
      "Explicit trusted local retraining and numeric export only.",
    parity_requirements: {
      class_agreement_minimum: 0.995,
      mean_score_delta_maximum: 0.01,
      maximum_score_delta: 0.05,
    },
  },
};

describe("EngineeringModelLibraryPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(engineeringModelService.listInstallations).mockResolvedValue([]);
    vi.mocked(engineeringModelService.listCatalog).mockResolvedValue({
      snapshot,
      models: [generated, pointnet],
      next_cursor: null,
      total: 2,
    });
    vi.mocked(engineeringModelService.getCatalogModel).mockImplementation(
      async (modelId) =>
        modelId === generated.model_id
          ? generated
          : modelId === chatterSource.model_id
            ? chatterSource
            : pointnet,
    );
  });

  it("separates engineering models from conversational Model Setup", async () => {
    render(<EngineeringModelLibraryPage />);

    expect(
      await screen.findByRole("heading", { name: "Engineering Models" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/specialized engineering models/i),
    ).toBeInTheDocument();
    expect(screen.getByTestId("model-snapshot-state")).toHaveTextContent(
      "Offline snapshot",
    );
    expect(
      screen.getByTestId("model-card-wright-affine-test"),
    ).toHaveTextContent("Approved");
    expect(
      screen.getByTestId("model-card-keras-io-pointnet"),
    ).toHaveTextContent("Needs review");
  });

  it("shows exact generated recipe while external entries show provenance", async () => {
    render(<EngineeringModelLibraryPage />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: /inspect wright affine test model/i,
      }),
    );

    expect(await screen.findByRole("dialog")).toHaveTextContent(
      "Generate canonical JSON coefficients",
    );
    expect(screen.getByRole("dialog")).toHaveTextContent("Artifact-set digest");
    expect(screen.getByRole("dialog")).toHaveTextContent("MIT");
    expect(screen.getByRole("dialog")).toHaveTextContent("Download");
    expect(screen.getByRole("dialog")).toHaveTextContent("96 B");
    expect(screen.getByRole("dialog")).toHaveTextContent(
      "Not a production engineering model",
    );
    expect(screen.getByRole("dialog")).toHaveTextContent("bundled");
    fireEvent.click(screen.getByTestId("model-detail-close"));
    fireEvent.click(
      screen.getByRole("button", {
        name: /inspect keras pointnet modelnet10 candidate/i,
      }),
    );
    expect(await screen.findByRole("dialog")).toHaveTextContent(
      "https://huggingface.co/keras-io/PointNet",
    );
    expect(screen.getByRole("dialog")).not.toHaveTextContent(
      "Generate canonical JSON coefficients",
    );
  });

  it("explains blockers and recovery without offering an install", async () => {
    render(<EngineeringModelLibraryPage />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: /inspect keras pointnet modelnet10 candidate/i,
      }),
    );

    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveTextContent(
      "No approved runtime adapter is installed",
    );
    expect(dialog).toHaveTextContent(
      "Review the adapter through a separate runtime plan",
    );
    expect(screen.queryByRole("button", { name: /^install$/i })).toBeNull();
  });

  it("applies search and task filters through the typed service", async () => {
    render(<EngineeringModelLibraryPage />);
    await screen.findByText("Wright Affine Test Model");

    fireEvent.change(screen.getByLabelText("Search engineering models"), {
      target: { value: "point cloud" },
    });
    fireEvent.change(screen.getByLabelText("Engineering task"), {
      target: { value: "point_cloud_classification" },
    });

    await waitFor(() =>
      expect(engineeringModelService.listCatalog).toHaveBeenLastCalledWith(
        expect.objectContaining({
          search: "point cloud",
          task: "point_cloud_classification",
        }),
      ),
    );
  });

  it("renders a bounded recovery state when the offline catalog cannot load", async () => {
    vi.mocked(engineeringModelService.listCatalog).mockRejectedValueOnce(
      new Error("catalog unavailable"),
    );
    render(<EngineeringModelLibraryPage />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The engineering model catalog could not be loaded",
    );
    expect(screen.getByTestId("model-catalog-retry")).toBeInTheDocument();
  });

  it("keeps cards keyboard operable and uses a narrow-width-safe grid", async () => {
    render(<EngineeringModelLibraryPage />);
    const inspect = await screen.findByRole("button", {
      name: /inspect wright affine test model/i,
    });
    inspect.focus();
    expect(inspect).toHaveFocus();
    fireEvent.click(inspect);
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    expect(screen.getByTestId("model-library-grid")).toHaveStyle({
      gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 20rem), 1fr))",
    });
  });

  it("shows the private Chatter source as inert until exact local qualification", async () => {
    vi.mocked(engineeringModelService.listCatalog).mockResolvedValueOnce({
      snapshot,
      models: [chatterSource],
      next_cursor: null,
      total: 1,
    });
    render(<EngineeringModelLibraryPage />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: /inspect wright chatter screening source/i,
      }),
    );
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveTextContent("Local qualification required");
    expect(dialog).toHaveTextContent("37 ordered features");
    expect(dialog).toHaveTextContent("GroupShuffleSplit");
    expect(dialog).toHaveTextContent("private, non-redistributable package");
    expect(dialog).toHaveTextContent(
      "Run the explicit trusted local qualification",
    );
    expect(screen.queryByRole("button", { name: /^install$/i })).toBeNull();
  });
});
