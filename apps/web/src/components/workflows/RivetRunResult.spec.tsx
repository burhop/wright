import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { RivetRunResultItem } from "../../services/workspace-service";
import { RivetRunResult } from "./RivetRunResult";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("RivetRunResult", () => {
  it("presents retained empty text as available and distinct from no value", async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    const availableEmpty: RivetRunResultItem = {
      result_id: "final_output:output",
      name: "output",
      origin: "final_output",
      kind: "text",
      data_type: "text",
      evidence_state: "available",
      value: "",
      preview: "",
      complete: true,
      truncation_reason: null,
      original_bytes: 2,
      retained_bytes: 2,
      digest:
        "12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126",
      redaction_count: 0,
      artifact: null,
    };
    const noValue: RivetRunResultItem = {
      ...availableEmpty,
      result_id: "final_output:missing",
      name: "missing",
      evidence_state: "no-value",
      value: null,
      digest: "",
    };
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);
    const createObjectURL = vi
      .spyOn(URL, "createObjectURL")
      .mockReturnValue("blob:empty-output");
    const revokeObjectURL = vi
      .spyOn(URL, "revokeObjectURL")
      .mockImplementation(() => undefined);

    const { rerender } = render(<RivetRunResult result={availableEmpty} />);

    expect(
      screen.getByTestId("rivet-run-result-value-output"),
    ).toHaveTextContent("Empty text (0 characters)");
    expect(screen.queryByText("No value")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Copy" }));
    expect(writeText).toHaveBeenCalledWith("");
    await user.click(screen.getByRole("button", { name: "Export JSON" }));
    const exported = createObjectURL.mock.calls[0]?.[0] as Blob;
    expect(JSON.parse(await exported.text())).toMatchObject({
      name: "output",
      evidence_state: "available",
      value: "",
    });
    expect(click).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:empty-output");

    rerender(<RivetRunResult result={noValue} />);
    expect(
      screen.getByTestId("rivet-run-result-value-missing"),
    ).toHaveTextContent("No value");
  });

  it("presents structured multiline text readably and copies the safe JSON value", async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    const markdown =
      "# CAD providers\n\n| Provider | Status |\n| --- | --- |\n| Onshape | Ready |";
    const result: RivetRunResultItem = {
      result_id: "final_output:cadProviderDocumentationChain",
      name: "cadProviderDocumentationChain",
      origin: "final_output",
      kind: "structured",
      data_type: "object",
      evidence_state: "available",
      value: { result: markdown },
      preview: JSON.stringify({ result: markdown }),
      complete: true,
      truncation_reason: null,
      original_bytes: markdown.length,
      retained_bytes: markdown.length,
      digest: "a".repeat(64),
      redaction_count: 0,
      artifact: null,
    };

    render(<RivetRunResult result={result} />);

    const displayed = screen.getByTestId(
      "rivet-run-result-value-cadProviderDocumentationChain",
    );
    expect(displayed.textContent).toBe(
      "result:\n  # CAD providers\n  \n  | Provider | Status |\n  | --- | --- |\n  | Onshape | Ready |",
    );
    expect(displayed.textContent).not.toContain("\\n");
    expect(displayed.textContent).not.toContain('"type"');

    await user.click(screen.getByRole("button", { name: "Copy" }));
    expect(writeText).toHaveBeenCalledWith(
      JSON.stringify({ result: markdown }, null, 2),
    );
  });

  it("renders legacy results without evidence metadata as unavailable", () => {
    const legacyResult = {
      result_id: "final_output:legacy",
      name: "legacy",
      origin: "workflow_output",
      kind: "text",
      data_type: "text",
      value: "retained value",
      preview: "retained value",
      complete: true,
      truncation_reason: null,
      original_bytes: 14,
      retained_bytes: 14,
      digest: "b".repeat(64),
      redaction_count: 0,
      artifact: null,
    } as unknown as RivetRunResultItem;

    render(<RivetRunResult result={legacyResult} />);

    expect(screen.getByTestId("rivet-run-result-legacy")).toHaveTextContent(
      "unavailable",
    );
    expect(
      screen.getByTestId("rivet-run-result-value-legacy"),
    ).toHaveTextContent("retained value");
  });
});
