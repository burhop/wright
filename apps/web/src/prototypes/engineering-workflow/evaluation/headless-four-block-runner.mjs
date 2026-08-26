function nowIso(clock) {
  return new Date(clock()).toISOString();
}

/**
 * Execute four semantic workflow blocks without importing React or a graph
 * library. Adapters own provider/tool details; this runner owns only ordering,
 * stop behavior, and inspectable step evidence.
 */
export async function runHeadlessFourBlockChain({
  request,
  validateInput,
  generate,
  invoke,
  evaluate,
  clock = Date.now,
  onStep = () => undefined,
}) {
  const run = {
    schemaVersion: "wright-headless-four-block-run/0.1",
    startedAt: nowIso(clock),
    finishedAt: null,
    status: "running",
    steps: [],
  };

  const executeStep = async (block, action) => {
    const step = {
      block,
      startedAt: nowIso(clock),
      finishedAt: null,
      status: "running",
      output: null,
      evidence: null,
      error: null,
    };
    run.steps.push(step);
    onStep(structuredClone(step));
    try {
      const result = await action();
      step.status = "completed";
      step.output = result.output;
      step.evidence = result.evidence ?? null;
      step.finishedAt = nowIso(clock);
      onStep(structuredClone(step));
      return result.output;
    } catch (error) {
      step.status = "failed";
      if (error && typeof error === "object") {
        step.output = error.stepOutput ?? null;
        step.evidence = error.stepEvidence ?? null;
      }
      step.error = error instanceof Error ? error.message : String(error);
      step.finishedAt = nowIso(clock);
      run.status = "failed";
      run.finishedAt = nowIso(clock);
      onStep(structuredClone(step));
      throw Object.assign(new Error(step.error), { run });
    }
  };

  const validatedRequest = await executeStep("request", () =>
    validateInput(request),
  );
  const generatedArguments = await executeStep("ai", () =>
    generate(validatedRequest),
  );
  const toolResult = await executeStep("mcp", () => invoke(generatedArguments));
  const outcome = await executeStep("evaluation", () =>
    evaluate(toolResult, generatedArguments),
  );

  run.status = outcome.accepted ? "passed" : "failed";
  run.finishedAt = nowIso(clock);
  run.outcome = outcome;
  return run;
}
