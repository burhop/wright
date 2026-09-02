import { describe, expect, it } from "vitest";
import { canonicalLayoutBytes, canonicalLayoutPositionBytes } from "./canonical-wire";
import { cloneLayout, initialLayout, type RecoveryLayout } from "./model";

describe("canonical presentation identity", () => {
  it("survives nested JSON key reordering on save and reopen", () => {
    const original = cloneLayout(initialLayout);
    const reopened = Object.fromEntries(Object.entries(original).reverse()) as unknown as RecoveryLayout;
    reopened.positions = Object.fromEntries(Object.entries(original.positions).reverse().map(([id, point]) => [id, { y: point.y, x: point.x }]));
    reopened.viewport = { zoom: original.viewport.zoom, y: original.viewport.y, x: original.viewport.x };
    expect(JSON.stringify(reopened)).not.toBe(JSON.stringify(original));
    expect(canonicalLayoutBytes(reopened)).toBe(canonicalLayoutBytes(original));
    expect(canonicalLayoutPositionBytes(reopened)).toBe(canonicalLayoutPositionBytes(original));
  });

  it("still detects coordinate changes and includes layout authority in the full digest", () => {
    const original = cloneLayout(initialLayout);
    const moved = cloneLayout(original);
    moved.positions[Object.keys(moved.positions)[0]].x += 1;
    expect(canonicalLayoutBytes(moved)).not.toBe(canonicalLayoutBytes(original));
    expect(canonicalLayoutPositionBytes(moved)).not.toBe(canonicalLayoutPositionBytes(original));
    const rebased = cloneLayout(original);
    rebased.semanticRevision += 1;
    expect(canonicalLayoutBytes(rebased)).not.toBe(canonicalLayoutBytes(original));
    expect(canonicalLayoutPositionBytes(rebased)).toBe(canonicalLayoutPositionBytes(original));
  });
});
