import { describe, expect, it } from "vitest";
import {
  createProcessViewRecoveryStore,
  type ProcessViewMutation,
} from "./process-view-recovery";

const process = {
  workspace_id: "workspace",
  source_path: "workflows/example.wflow",
  source_digest: "a".repeat(64),
};
const subjectDigest = "b".repeat(64);
const intents: ProcessViewMutation[] = [
  {
    kind: "response",
    runId: "run-one",
    request: {
      checkpointId: "input-one",
      subjectDigest,
      requestId: "response-one",
      value: { selection: "a" },
    },
  },
  {
    kind: "review",
    runId: "run-one",
    request: {
      checkpointId: "review-one",
      subjectDigest,
      requestId: "review-one",
      decision: "changes_requested",
      reason: "Correct the units",
    },
  },
  {
    kind: "action",
    runId: "run-one",
    checkpointId: "action-one",
    request: {
      actionId: "continue-action-one",
      subjectDigest,
      requestId: "action-one",
    },
  },
];
function storage() {
  const values = new Map<string, string>();
  return {
    values,
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => {
      values.set(key, value);
    },
    removeItem: (key: string) => {
      values.delete(key);
    },
  };
}
describe("scoped interaction intent recovery", () => {
  it.each(intents)(
    "cold-reopens $kind intent without requiring browser-owned start state",
    (intent) => {
      const data = storage();
      createProcessViewRecoveryStore(process, "session", data).writeInteraction(
        intent,
      );
      const cold = createProcessViewRecoveryStore(process, "session", data);
      expect(cold.read()).toBeNull();
      expect(cold.readInteraction("run-one")).toEqual(intent);
      expect(cold.readInteraction("run-two")).toBeNull();
      expect(
        createProcessViewRecoveryStore(
          process,
          "another-session",
          data,
        ).readInteraction("run-one"),
      ).toBeNull();
      expect(
        createProcessViewRecoveryStore(
          { ...process, source_digest: "c".repeat(64) },
          "session",
          data,
        ).readInteraction("run-one"),
      ).toBeNull();
      expect(
        createProcessViewRecoveryStore(
          { ...process, workspace_id: "elsewhere" },
          "session",
          data,
        ).readInteraction("run-one"),
      ).toBeNull();
      cold.clearInteraction("run-one", "another-request");
      expect(cold.readInteraction("run-one")).toEqual(intent);
      cold.clearInteraction("run-one", intent.request.requestId);
      expect(cold.readInteraction("run-one")).toBeNull();
    },
  );
  it("retains exact duplicate intent and rejects changed payload or another request", () => {
    const data = storage(),
      store = createProcessViewRecoveryStore(process, "session", data);
    store.writeInteraction(intents[0]);
    store.writeInteraction(structuredClone(intents[0]));
    expect(() => store.writeInteraction(intents[1])).toThrow(
      /earlier interaction/,
    );
    expect(store.readInteraction("run-one")).toEqual(intents[0]);
  });
  it.each([
    { ...intents[0], principal_id: "invented-authority" },
    { ...intents[0], request: { ...intents[0].request, runId: "another-run" } },
    { ...intents[1], request: { ...intents[1].request, decision: "force" } },
    { ...intents[1], request: { ...intents[1].request, reason: " " } },
    {
      ...intents[2],
      request: { ...intents[2].request, subjectDigest: "invalid" },
    },
    {
      ...intents[0],
      request: { ...intents[0].request, value: "x".repeat(65536) },
    },
  ])("rejects malformed intent before storage", (intent) => {
    const data = storage(),
      store = createProcessViewRecoveryStore(process, "session", data);
    expect(() =>
      store.writeInteraction(intent as ProcessViewMutation),
    ).toThrow();
    expect(data.values.size).toBe(0);
  });
  it("checks retained run identity again on read and rejects corrupt intent", () => {
    const data = storage(),
      store = createProcessViewRecoveryStore(process, "session", data);
    store.writeInteraction(intents[2]);
    const key = [...data.values.keys()][0];
    data.values.set(key, JSON.stringify({ ...intents[2], runId: "elsewhere" }));
    expect(() => store.readInteraction("run-one")).toThrow();
    data.values.set(key, "broken json");
    expect(() => store.readInteraction("run-one")).toThrow();
  });
});
