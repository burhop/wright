import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  CapabilityApiError,
  mcpService,
  type CatalogMutationResult,
  type CatalogStateResponse,
  type CatalogUpdatePreview,
} from "../../services/mcp-service";
import { CatalogUpdatePanel } from "./CatalogUpdatePanel";

vi.mock("../../services/mcp-service", async (loadOriginal) => {
  const original =
    await loadOriginal<typeof import("../../services/mcp-service")>();
  return {
    ...original,
    mcpService: {
      getCatalogState: vi.fn(),
      previewCatalogUpdate: vi.fn(),
      activateCatalogUpdate: vi.fn(),
      rollbackCatalog: vi.fn(),
    },
  };
});

const state: CatalogStateResponse = {
  bundled_snapshot_id: "bundled-69",
  active_snapshot_id: "bundled-69",
  previous_snapshot_id: null,
  active_sequence: 1,
  active_channel: "bundled",
  active_generation: 1,
  updated_at: "2026-08-12T00:00:00Z",
  updated_by: "wright-bootstrap",
  configured_channels: ["stable"],
  diagnostic: null,
  history: [
    {
      activation_id: "bootstrap-1",
      from_snapshot_id: null,
      to_snapshot_id: "bundled-69",
      kind: "bootstrap",
      actor: "wright-bootstrap",
      trace_id: "trace-bootstrap",
      occurred_at: 1,
      result: "succeeded",
      reason_code: null,
    },
  ],
};

const preview: CatalogUpdatePreview = {
  preview_id: "preview-1",
  active_snapshot_id: "bundled-69",
  candidate_snapshot_id: "stable-70",
  candidate: {
    channel: "stable",
    sequence: 2,
    schema_version: 1,
    payload_sha256: "a".repeat(64),
    signer_key_id: "key-1",
    expires_at: "2026-08-19T00:00:00Z",
  },
  diff: {
    added: [{ id: "onshape-labs-featurescript-mcp" }],
    removed: [],
    changed: [],
    summary: {
      added: 1,
      removed: 0,
      changed: 0,
      total_before: 69,
      total_after: 70,
    },
  },
  risk_summary: {
    new_executable_entries: 0,
    new_remote_entries: 1,
    high_or_safety_critical: 0,
    note: "Catalog activation changes metadata only; it cannot install or enable.",
  },
  actor: "local-admin",
  created_at: "2026-08-12T00:00:00Z",
  expires_at: "2026-08-12T00:10:00Z",
  state: "open",
  preview_digest: "b".repeat(64),
};

const mutation: CatalogMutationResult = {
  state,
  reconciled: 70,
  preserved_user_state: true,
  preserved_counts: {},
};

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

describe("CatalogUpdatePanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(mcpService.getCatalogState).mockResolvedValue(state);
    vi.mocked(mcpService.previewCatalogUpdate).mockResolvedValue(preview);
    vi.mocked(mcpService.activateCatalogUpdate).mockResolvedValue(mutation);
    vi.mocked(mcpService.rollbackCatalog).mockResolvedValue(mutation);
  });

  it("shows bundled recovery when no signed channel is configured", async () => {
    vi.mocked(mcpService.getCatalogState).mockResolvedValue({
      ...state,
      configured_channels: [],
    });
    render(<CatalogUpdatePanel />);

    expect(await screen.findByText(/No signed update channel/)).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Check for updates" }),
    ).toBeDisabled();
    expect(screen.getByText(/Active source:/)).toHaveTextContent("bundled");
  });

  it("shows checking and a verified exact diff before activation", async () => {
    const user = userEvent.setup();
    const pending = deferred<CatalogUpdatePreview>();
    vi.mocked(mcpService.previewCatalogUpdate).mockReturnValue(pending.promise);
    render(<CatalogUpdatePanel />);
    const check = await screen.findByRole("button", {
      name: "Check for updates",
    });

    await user.click(check);
    expect(screen.getByRole("button", { name: "Checking…" })).toBeDisabled();
    pending.resolve(preview);

    expect(await screen.findByText("Verified signed update")).toBeVisible();
    expect(screen.getByTestId("catalog-update-preview")).toHaveTextContent(
      "1 added · 0 changed · 0 removed",
    );
    expect(screen.getByTestId("catalog-update-preview")).toHaveTextContent(
      "cannot install or enable",
    );
  });

  it("renders a redacted verification failure with recovery and trace", async () => {
    const user = userEvent.setup();
    vi.mocked(mcpService.previewCatalogUpdate).mockRejectedValue(
      new CapabilityApiError(
        "The signature is invalid.",
        "catalog_signature_invalid",
        "trace-42",
        "Keep the current catalog.",
      ),
    );
    render(<CatalogUpdatePanel />);
    await user.click(
      await screen.findByRole("button", { name: "Check for updates" }),
    );

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("catalog_signature_invalid");
    expect(alert).toHaveTextContent("Keep the current catalog");
    expect(alert).toHaveTextContent("trace-42");
  });

  it("shows activation progress, reloads state, and keeps history", async () => {
    const user = userEvent.setup();
    const pending = deferred<CatalogMutationResult>();
    const changed = vi.fn();
    vi.mocked(mcpService.activateCatalogUpdate).mockReturnValue(
      pending.promise,
    );
    vi.mocked(mcpService.getCatalogState)
      .mockResolvedValueOnce(state)
      .mockResolvedValueOnce({
        ...state,
        active_snapshot_id: "stable-70",
        previous_snapshot_id: "bundled-69",
        active_sequence: 2,
        active_channel: "stable",
      });
    render(<CatalogUpdatePanel onCatalogChanged={changed} />);
    await user.click(
      await screen.findByRole("button", { name: "Check for updates" }),
    );
    await user.click(
      await screen.findByRole("button", { name: "Activate update" }),
    );
    expect(screen.getByRole("button", { name: "Activating…" })).toBeDisabled();

    pending.resolve(mutation);
    await waitFor(() => expect(changed).toHaveBeenCalledOnce());
    expect(screen.getByTestId("catalog-active-source")).toHaveTextContent(
      "stable",
    );
    await user.click(screen.getByText("Catalog history"));
    expect(
      screen.getByRole("list", { name: "Catalog history" }),
    ).toHaveTextContent("bootstrap · succeeded");
  });

  it("supports rollback progress and reports rollback failure", async () => {
    const user = userEvent.setup();
    vi.mocked(mcpService.getCatalogState).mockResolvedValue({
      ...state,
      active_snapshot_id: "stable-70",
      previous_snapshot_id: "bundled-69",
      active_channel: "stable",
      active_sequence: 2,
    });
    vi.mocked(mcpService.rollbackCatalog).mockRejectedValue(
      new CapabilityApiError(
        "The catalog changed before rollback.",
        "catalog_state_conflict",
      ),
    );
    render(<CatalogUpdatePanel />);
    await user.click(await screen.findByRole("button", { name: "Roll back" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "catalog_state_conflict",
    );
  });
});
