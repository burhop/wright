import { expect, it } from "vitest";
import { cadOutputPresentation } from "./cad-output-presentation";
import { initialWorkflow, type RecoveryWorkflow } from "./model";
import { sourceKey } from "./prompt-settings";

it("keeps legacy native and export edges while removing duplicate unused presentation", () => {
  const w = structuredClone(initialWorkflow) as RecoveryWorkflow;
  const b = w.blocks[0];
  const native = {
    ...w.ports[0],
    id: "port.native",
    ownerBlockId: b.id,
    direction: "output" as const,
  };
  const exported = { ...native, id: "port.step" };
  w.ports.push(native, exported);
  b.configuration.cad = JSON.stringify({
    native_port: sourceKey(native.id),
    exports: [
      {
        port: sourceKey(exported.id),
        format: "step",
        path: "parts/bracket.step",
      },
    ],
  });
  const before = JSON.stringify(w);
  const display = cadOutputPresentation(w);
  expect(display.hidden.has(native.id)).toBe(true);
  expect(display.labels[exported.id]).toBe("parts/bracket.step");
  expect(display.groups[exported.id]).toBe("Exports");
  expect(JSON.stringify(w)).toBe(before);
  w.relationships.push({
    ...w.relationships[0],
    id: "rel.legacy-native",
    sourceId: native.id,
  });
  expect(cadOutputPresentation(w).hidden.has(native.id)).toBe(false);
  expect(cadOutputPresentation(w).labels[native.id]).toBe("Saved model file");
});
