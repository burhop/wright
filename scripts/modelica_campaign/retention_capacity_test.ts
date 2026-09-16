// Isolated storage/application tests only: no OMC, MCP listener or campaign store.
import { deepStrictEqual as assertEquals, rejects } from "node:assert/strict";
import { CapacityCoordinator, MAX_STORED_RUNS } from "/app/src/storage/capacity-coordinator.ts";
import { ResumableSimulationService } from "/app/src/application/resumable-simulation-service.ts";
import { createModelicaService } from "/app/src/domain/service.ts";
import { QUALIFIED_KIT_RUNTIME } from "/app/src/domain/runtime-compatibility.ts";
import { FileRequestLockPort } from "/app/src/storage/request-lock.ts";
import { RequestStore } from "/app/src/storage/request-store.ts";
import { FileSimulationWorkspace } from "/app/src/storage/simulation-workspace.ts";

async function assertRejects(action: () => Promise<unknown>, type: typeof Error, message: string) {
  await rejects(action, (error: unknown) => error instanceof type && error.message.includes(message));
}

async function populate(directory: string, count: number) {
  for (let index = 0; index < count; index++) {
    const path = `${directory}/run_${crypto.randomUUID()}`;
    await Deno.mkdir(path);
    await Deno.writeTextFile(`${path}/preserved.txt`, "unit-test evidence; no simulation\n");
  }
}

Deno.test("selected retention keeps a finite hundred-slot bound and prior bytes", async () => {
  const directory = await Deno.makeTempDir();
  try {
    assertEquals(MAX_STORED_RUNS, 100);
    await populate(directory, 20);
    const paths: string[] = [];
    for await (const entry of Deno.readDir(directory)) paths.push(`${directory}/${entry.name}/preserved.txt`);
    const coordinator = new CapacityCoordinator(directory);
    const admitted = await coordinator.reserve("request", "twenty-first");
    await admitted.release();
    for (const path of paths) assertEquals(await Deno.readTextFile(path), "unit-test evidence; no simulation\n");
    await populate(directory, 79);
    const outcomes = await Promise.allSettled([
      coordinator.reserve("request", "last-slot-a"),
      coordinator.reserve("request", "last-slot-b"),
    ]);
    assertEquals(outcomes.filter((result) => result.status === "fulfilled").length, 1);
    assertEquals(outcomes.filter((result) => result.status === "rejected").length, 1);
    await assertRejects(() => coordinator.reserve("legacy", "blocked"), Error, "limit 100");
  } finally {
    await Deno.remove(directory, { recursive: true });
  }
});

Deno.test("malformed claims still reserve capacity conservatively", async () => {
  const directory = await Deno.makeTempDir();
  try {
    await populate(directory, 99);
    const claims = `${directory}/.resumable/capacity-claims`;
    await Deno.mkdir(claims, { recursive: true });
    await Deno.writeTextFile(`${claims}/unknown.json`, "{torn");
    await assertRejects(() => new CapacityCoordinator(directory).reserve("request", "blocked"), Error, "limit 100");
  } finally {
    await Deno.remove(directory, { recursive: true });
  }
});

Deno.test("application preserves completed-request identity at capacity without replay", async () => {
  const directory = await Deno.makeTempDir();
  let executions = 0;
  let probes = 0;
  // Explicit unit fixture: this runner never launches a simulator or publishes campaign data.
  const runner = {
    getRuntimeEngineIdentity() {
      probes++;
      return Promise.resolve({ ...QUALIFIED_KIT_RUNTIME });
    },
    execute() {
      executions++;
      return Promise.resolve({
        status: "succeeded" as const,
        diagnostics: "UNIT TEST ONLY: no physical simulation performed",
        resultCsv: "time,waterTemperatureC,heaterPowerW,heaterEnergyJ,heaterOn\n0,20,1500,0,1\n100,65,1500,150000,1\n200,90.5,1500,300000,1\n300,94,0,315000,0\n",
      });
    },
  };
  try {
    await populate(directory, 99);
    const legacy = await createModelicaService({ runsDirectory: directory, runner });
    const store = new RequestStore(directory);
    const service = new ResumableSimulationService(legacy, store,
      new FileRequestLockPort(store.locksDirectory), new FileSimulationWorkspace(directory, runner));
    const identity = { model_id: "coffee-machine-v1", model_version: "0.1.0", scenario_id: "heat-up-nominal" };
    const manifest = await service.getManifest(identity);
    const parameters = Object.fromEntries(legacy.listKits()[0].parameters.map(p => [p.id, p.default]));
    const input = { ...identity, parameters, request_id: "retained-identity", manifest_sha256: manifest.manifest_sha256, timeout_ms: 30000 };
    const completed = await service.submit(input);
    assertEquals(completed.request.status, "completed");
    const sealed = await Deno.readTextFile(store.runRecordPath(input.request_id));
    const before = { executions, probes };
    const restarted = new ResumableSimulationService(legacy, new RequestStore(directory),
      new FileRequestLockPort(store.locksDirectory), new FileSimulationWorkspace(directory, runner));
    const same = await restarted.submit(input);
    assertEquals(same.request.run, completed.request.run);
    assertEquals(executions, before.executions);
    assertEquals(await Deno.readTextFile(store.runRecordPath(input.request_id)), sealed);
    await assertRejects(() => restarted.submit({ ...input, request_id: "capacity-rejected" }), Error, "limit 100");
    assertEquals(await store.readClaim("capacity-rejected"), undefined);
    assertEquals({ executions, probes }, before);
    await assertRejects(() => restarted.submit({ ...input, parameters: { ...parameters, water_mass: { value: 0.7, unit: "kg" } } }), Error, "different canonical request bytes");
    assertEquals(executions, 1);
  } finally {
    await Deno.remove(directory, { recursive: true });
  }
});
