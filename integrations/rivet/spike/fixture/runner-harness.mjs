import { resolve } from "node:path";
import { runGraphInFile } from "@valerypopoff/rivet2-node";
import { spikeRoot, writeEvidence } from "../scripts/evidence.mjs";

const fixture = resolve(spikeRoot, "fixture", "mock-workflow.rivet-project");
const slowFixture = resolve(spikeRoot, "fixture", "mock-slow-workflow.rivet-project");
const events = [];
const controller = new AbortController();
let externalCallCount = 0;
try {
  const outputs = await runGraphInFile(fixture, {
    graph: "Wright Spike Main",
    abortSignal: controller.signal,
    externalFunctions: {
      wright_mock_operation: async (_context, ...args) => {
        externalCallCount += 1;
        events.push({ kind: "external-call", argumentCount: args.length });
        return { type: "string", value: "mock-wright-result" };
      }
    },
    onStart: () => events.push({ kind: "start" }),
    onNodeStart: () => events.push({ kind: "node-start" }),
    onNodeFinish: () => events.push({ kind: "node-finish" }),
    onDone: () => events.push({ kind: "done" }),
    onAbort: () => events.push({ kind: "abort" })
  });
  const result = outputs.result?.value === "mock-wright-result" && externalCallCount === 1 ? "passed" : "blocked";
  const { target } = await writeEvidence("runner", result, { outputs, externalCallCount }, events);
  console.log(target);
  if (result !== "passed") process.exitCode = 1;
} catch (error) {
  const { target } = await writeEvidence("runner", "failed", { message: error instanceof Error ? error.message : String(error), externalCallCount }, events);
  console.error(target);
  process.exitCode = 1;
}

const cancellationEvents = [];
const cancellationController = new AbortController();
let cancellationExternalCallCount = 0;
setTimeout(() => cancellationController.abort("wright-spike-cancellation"), 25);
try {
  await runGraphInFile(slowFixture, {
    graph: "Wright Spike Cancellation",
    abortSignal: cancellationController.signal,
    externalFunctions: {
      wright_slow_operation: async () => {
        cancellationExternalCallCount += 1;
        await new Promise((resolveDelay) => setTimeout(resolveDelay, 150));
        return { type: "string", value: "should-not-complete-before-abort" };
      }
    },
    onAbort: () => cancellationEvents.push({ kind: "abort" }),
    onDone: () => cancellationEvents.push({ kind: "done" })
  });
  const observed = cancellationEvents.some((event) => event.kind === "abort");
  const { target } = await writeEvidence("runner", observed ? "passed" : "blocked", {
    cancellationAttempt: "AbortController aborted during slow external operation",
    cancellationObserved: observed,
    cancellationExternalCallCount
  }, cancellationEvents, "runner-cancellation");
  console.log(target);
} catch (error) {
  const observed = cancellationEvents.some((event) => event.kind === "abort");
  const { target } = await writeEvidence("runner", observed ? "passed" : "failed", {
    cancellationAttempt: "AbortController aborted during slow external operation",
    cancellationObserved: observed,
    cancellationExternalCallCount,
    message: error instanceof Error ? error.message : String(error)
  }, cancellationEvents, "runner-cancellation");
  console.log(target);
  if (!observed) process.exitCode = 1;
}
