import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { EvidenceDetails } from "../components/program-status/EvidenceDetails";
import {
  decodeProgramStatusBundle,
  ProgramStatusDecodeError,
} from "../services/program-status";
import { makeProgramStatusBundle } from "./program-status-fixture";

describe("program status evidence", () => {
  it("exposes exact identity and keyboard-operable bounded detail", async () => {
    const user = userEvent.setup();
    const bundle = decodeProgramStatusBundle(
      makeProgramStatusBundle({ evidence: true }),
    );
    render(<EvidenceDetails bundle={bundle} />);
    const disclosure = screen.getByText(/^Dashboard snapshot · current$/);
    disclosure.focus();
    expect(disclosure).toHaveFocus();
    await user.click(disclosure);
    expect(screen.getByText(/dashboard\.json/)).toBeVisible();
    expect(
      screen.getAllByRole("link", { name: /exact committed evidence/i })[0],
    ).toHaveAttribute(
      "href",
      expect.stringMatching(/^https:\/\/github\.com\//),
    );
  });

  it("rejects traversal and non-exact GitHub links before rendering", () => {
    const traversal = makeProgramStatusBundle({ evidence: true }) as any;
    traversal.supplement.evidence_index[0].path = "docs/../secrets.txt";
    expect(() => decodeProgramStatusBundle(traversal)).toThrow(
      ProgramStatusDecodeError,
    );

    const unsafe = makeProgramStatusBundle({ evidence: true }) as any;
    unsafe.supplement.evidence_index[0].exact_url =
      "https://evil.example/dashboard.json";
    expect(() => decodeProgramStatusBundle(unsafe)).toThrow(
      "UNSAFE_EVIDENCE_URL",
    );
  });
});
