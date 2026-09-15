import type { McpApp } from "@casys/mcp-server";
import type { ResumableSimulationService } from "./application/resumable-simulation-service.ts";
import { ValidationError } from "./domain/errors.ts";
import { sha256, stableJson } from "./domain/hashing.ts";
import { validateExportInput } from "./recorded-export.ts";

/** Derive engineering observations from native recorded results, never an ODE surrogate. */
export function observeCsv(source: string, parameters: Record<string, { value: number }>, target: number) {
  const rows = source.trim().split(/\r?\n/).map(line => line.split(",").map(cell => cell.replace(/^"|"$/g, "")));
  const names = ["time", "waterTemperatureC", "electricalPowerW", "electricalEnergyJ", "heaterPowerW", "heaterEnergyJ"];
  const indexes = names.map(name => rows[0].indexOf(name));
  if (indexes.some(index => index < 0)) throw new ValidationError("Native thermal/electrical CSV fields are missing.");
  const samples = rows.slice(1).map(row => indexes.map(index => Number(row[index])));
  if (samples.length < 2 || samples.some(row => row.some(value => !Number.isFinite(value)))) throw new ValidationError("Native CSV contains invalid observations.");
  let timeToTarget: number | null = samples[0][1] >= target ? samples[0][0] : null;
  let electricalIntegral = 0, thermalIntegral = 0, heatLoss = 0;
  const loss = parameters.heat_loss_conductance.value, ambient = parameters.ambient_temperature.value;
  for (let index = 1; index < samples.length; index++) {
    const previous = samples[index - 1], current = samples[index], dt = current[0] - previous[0];
    if (dt < 0) throw new ValidationError("Native time samples are not ordered.");
    electricalIntegral += dt * (previous[2] + current[2]) / 2;
    thermalIntegral += dt * (previous[4] + current[4]) / 2;
    heatLoss += dt * loss * ((previous[1] + current[1]) / 2 - ambient);
    if (timeToTarget === null && current[1] >= target && previous[1] < target) timeToTarget = previous[0] + dt * (target - previous[1]) / (current[1] - previous[1]);
  }
  const first = samples[0], last = samples.at(-1)!;
  const capacity = parameters.water_mass.value * 4180 + parameters.boiler_heat_capacity.value;
  const storedHeat = capacity * (last[1] - first[1]);
  return { samples, timeToTarget, electricalIntegral, thermalIntegral, heatLoss, storedHeat,
    electricalEnergy: last[3], thermalEnergy: last[5], finalTemperature: last[1],
    balanceErrorJ: last[5] - storedHeat - heatLoss, electricalIntegralErrorJ: electricalIntegral - last[3] };
}

export async function summarizeStudy(service: ResumableSimulationService, input: Record<string, unknown>) {
  const { dataset_id, attempt_id, requests, time_limit_s, candidate_powers_w, loss_conductances_w_per_k } = input;
  if (Object.keys(input).sort().join(",") !== "attempt_id,candidate_powers_w,dataset_id,loss_conductances_w_per_k,requests,time_limit_s" ||
    !Array.isArray(requests) || requests.length < 2 || requests.length > 18 ||
    typeof time_limit_s !== "number" || !Number.isFinite(time_limit_s) || time_limit_s < 30 || time_limit_s > 900 ||
    !Array.isArray(candidate_powers_w) || candidate_powers_w.length < 1 || candidate_powers_w.length > 6 || candidate_powers_w.some(p => typeof p !== "number" || p < 350 || p > 1800) ||
    !Array.isArray(loss_conductances_w_per_k) || loss_conductances_w_per_k.length < 1 || loss_conductances_w_per_k.length > 3 || loss_conductances_w_per_k.some(p => typeof p !== "number" || p < .6 || p > 5)) {
    throw new ValidationError("Invalid bounded study request.");
  }
  const observed: Array<{ request_id: string; run_id: unknown; manifest_sha256: string; source_csv_uri: string; source_csv_sha256: string; parameters: Record<string, { value: number }>; controls: { max_step_size_s: number; tolerance: number }; power: number; loss: number; result: ReturnType<typeof observeCsv> }> = [];
  for (const request of requests) {
    if (!request || typeof request !== "object" || Object.keys(request).sort().join(",") !== "expected_manifest_sha256,request_id") throw new ValidationError("Use exact native request/digest identities.");
    const identity = validateExportInput({ dataset_id, attempt_id, ...request });
    const evidence = await service.getCompletedEvidence(identity.request_id);
    const record = evidence.runJson.record;
    const manifest = record.manifest as { manifest_sha256: string; model: { id: string; version: string }; scenario: { public: { numerical_controls: { max_step_size_s: number; tolerance: number } } } };
    if (record.status !== "succeeded" || manifest.manifest_sha256 !== identity.expected_manifest_sha256 || manifest.model.id !== "wright-water-heater-v1" || manifest.model.version !== "0.1.0") throw new ValidationError("Study request is not the exact successful selected native run.");
    const artifact = evidence.artifacts.find(item => item.kind === "result")!;
    const verified = await service.store.readArtifact(identity.request_id, artifact);
    const parameters = record.resolved_parameters as Record<string, { value: number }>;
    const result = observeCsv(verified.source, parameters, 90);
    observed.push({ request_id: identity.request_id, run_id: record.run_id, manifest_sha256: identity.expected_manifest_sha256, source_csv_uri: artifact.uri, source_csv_sha256: artifact.sha256, parameters,
      controls: manifest.scenario.public.numerical_controls, power: parameters.electrical_power.value, loss: parameters.heat_loss_conductance.value, result });
  }
  if (new Set(observed.map(run => run.request_id)).size !== observed.length) throw new ValidationError("Duplicate study request.");
  const baseline = observed.filter(run => run.controls.max_step_size_s === 1);
  const invariantParameters = (parameters: Record<string, { value: number }>) => Object.fromEntries(Object.entries(parameters).filter(([name]) => name !== "electrical_power" && name !== "heat_loss_conductance"));
  if (!baseline.length || baseline.some(run => stableJson(invariantParameters(run.parameters)) !== stableJson(invariantParameters(baseline[0].parameters)))) throw new ValidationError("Candidate comparison changes undeclared physical parameters.");
  for (const power of candidate_powers_w) for (const loss of loss_conductances_w_per_k) {
    if (baseline.filter(run => run.power === power && run.loss === loss).length !== 1) throw new ValidationError("Study is missing an exact candidate/loss baseline or includes duplicate baselines.");
  }
  if (baseline.length !== candidate_powers_w.length * loss_conductances_w_per_k.length) throw new ValidationError("Study includes undeclared candidates or loss cases.");
  const comparisons = baseline.map(run => {
    const tighter = observed.find(candidate => candidate.controls.max_step_size_s === .25 && stableJson(candidate.parameters) === stableJson(run.parameters));
    const reached = run.result.timeToTarget !== null && run.result.timeToTarget <= time_limit_s;
    const delta = tighter && run.result.timeToTarget !== null && tighter.result.timeToTarget !== null ? tighter.result.timeToTarget - run.result.timeToTarget : null;
    const energyRelative = tighter ? Math.abs(tighter.result.electricalEnergy - run.result.electricalEnergy) / Math.max(1, run.result.electricalEnergy) : null;
    const energyConsistent = Math.abs(run.result.balanceErrorJ) <= Math.max(1, .01 * run.result.thermalEnergy) && Math.abs(run.result.electricalIntegralErrorJ) <= Math.max(1, .01 * run.result.electricalEnergy);
    const stable = delta !== null && Math.abs(delta) <= Math.max(1, .01 * run.result.timeToTarget!) && energyRelative !== null && energyRelative <= .01;
    return { run, tighter, reached, delta, energyRelative, energyConsistent, stable };
  });
  const chosen = [...candidate_powers_w].sort((a, b) => a - b).find(power => comparisons.filter(row => row.run.power === power).every(row => row.reached && row.energyConsistent && row.stable)) ?? null;
  const csv = (rows: unknown[][]) => rows.map(row => row.map(value => value === null || value === undefined ? "" : String(value)).join(",")).join("\n") + "\n";
  const times = [["request_id", "time_s", "temperature_C", "electrical_power_W", "electrical_energy_J", "thermal_power_W", "thermal_energy_J"], ...observed.flatMap(run => run.result.samples.map(row => [run.request_id, ...row]))];
  const powerRows = [["request_id", "electrical_power_W", "loss_W_per_K", "time_to_90C_s", "time_limit_s", "meets_time", "refined_request_id", "refined_delta_time_s", "refined_relative_energy_difference", "energy_consistent", "numerically_stable"], ...comparisons.map(row => [row.run.request_id, row.run.power, row.run.loss, row.run.result.timeToTarget, time_limit_s, row.reached, row.tighter?.request_id, row.delta, row.energyRelative, row.energyConsistent, row.stable])];
  const energyRows = [["request_id", "electrical_energy_J", "thermal_energy_J", "independent_integral_electrical_J", "independent_integral_thermal_J", "stored_heat_J", "ambient_loss_J", "thermal_balance_residual_J"], ...observed.map(run => [run.request_id, run.result.electricalEnergy, run.result.thermalEnergy, run.result.electricalIntegral, run.result.thermalIntegral, run.result.storedHeat, run.result.heatLoss, run.result.balanceErrorJ])];
  const maxTime = Math.max(...observed.map(run => run.result.samples.at(-1)![0]));
  const colors = ["#0a6caa", "#b6540f", "#14825c", "#703fc4", "#c83961", "#6d7134"];
  const polylines = baseline.map((run, index) => { const samples = run.result.samples.filter((_, i) => i % Math.max(1, Math.floor(run.result.samples.length / 900)) === 0); return `<polyline fill="none" stroke="${colors[index % colors.length]}" stroke-width="1.8" points="${samples.map(row => `${60 + row[0] / maxTime * 800},${380 - row[1] / 110 * 330}`).join(" ")}"/><text x="70" y="${440 + 20 * index}" fill="${colors[index % colors.length]}">${run.power} W electrical; UA ${run.loss} W/K</text>`; }).join("\n");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="920" height="${480 + baseline.length * 20}" viewBox="0 0 920 ${480 + baseline.length * 20}"><rect width="100%" height="100%" fill="white"/><g font-family="sans-serif" font-size="14"><text x="60" y="25">Native Modelica temperature curves — ${dataset_id}</text><path d="M60 50 V380 H860" fill="none" stroke="#333"/><text x="50" y="45">°C</text><text x="800" y="410">time (s)</text><text x="50" y="400">0</text><text x="830" y="400">${maxTime}</text><path d="M60 110 H860" stroke="#888" stroke-dasharray="5 5"/><text x="865" y="115">90°C</text>${polylines}</g></svg>\n`;
  const report = `# Heater selection from recorded Modelica runs\n\n${chosen === null ? "No setting has demonstrated every declared time, energy and numerical-stability criterion in the supplied completed runs." : `Lowest demonstrated electrical setting: **${chosen} W** across every supplied loss case.`}\n\nTarget90°C; time limit${time_limit_s}s. All ${baseline.length} declared candidate/loss baselines are present. Independent first-crossing interpolation, trapezoidal electrical/thermal energy integration and capacity-plus-ambient-loss balance use the actual sealed CSV samples. Refined simulations independently constrain DASSL maxStepSize to0.25s and tolerance1e-8; baseline1s/1e-6, with unchanged1s output grid. Engineering screening thresholds used here:1% energy consistency, time difference at most max(1s,1%), and1% final electrical-energy difference. These explicit numerical screening assumptions are not manufacturing approval or the campaign's future content-validation tests.\n\nThermal power equals electrical input times heater efficiency. Inverter efficiency is outside this thermal model; apply the supplied battery/inverter budget separately. The selected model retains upstream lumped storage, ambient losses and thermostat topology.\n\n| Power W | Loss W/K | Time to90°C s | Refined difference s | Time met | Energy consistent | Stable |\n|---|---|---|---|---|---|---|\n${comparisons.map(row => `| ${row.run.power} | ${row.run.loss} | ${row.run.result.timeToTarget ?? "not reached"} | ${row.delta ?? "not demonstrated"} | ${row.reached} | ${row.energyConsistent} | ${row.stable} |`).join("\n")}\n`;
  const files = new Map<string, string>([["temperature-time.csv", csv(times)], ["power-comparison.csv", csv(powerRows)], ["energy-summary.csv", csv(energyRows)], ["temperature-curve.svg", svg], ["heater-selection.md", report], ["kit-run-parameters.json", JSON.stringify({ selected_electrical_power_w: chosen, time_limit_s, candidate_powers_w, loss_conductances_w_per_k, runs: observed.map(({ result: _result, ...run }) => run) }, null, 2) + "\n"]]);
  const root = `/exports/${dataset_id}/${attempt_id}`;
  if ((await Deno.realPath(root)) !== root || !(await Deno.lstat(root)).isDirectory) throw new ValidationError("Study output root is missing or redirected.");
  const produced_files = [];
  for (const [name, source] of files) {
    const path = root + "/" + name, hash = await sha256(source), bytes = new TextEncoder().encode(source);
    try { const file = await Deno.open(path, { write: true, createNew: true }); try { let offset = 0; while (offset < bytes.length) offset += await file.write(bytes.subarray(offset)); await file.sync(); } finally { file.close(); } }
    catch (error) { if (!(error instanceof Deno.errors.AlreadyExists)) throw error; if ((await Deno.lstat(path)).isSymlink || (await Deno.realPath(path)) !== path || await sha256(await Deno.readTextFile(path)) !== hash) throw new ValidationError("Existing study artifact differs; refusing overwrite."); }
    produced_files.push({ output_path: `campaign/${dataset_id}/${attempt_id}/artifacts/${name}`, output_bytes: bytes.length, sha256: hash, output_format: name.endsWith(".csv") ? "csv" : name.endsWith(".svg") ? "svg" : name.endsWith(".json") ? "json" : "markdown" });
  }
  return { operation: "summarize_recorded_modelica_study", selected_electrical_power_w: chosen, source_requests: observed.map(run => ({ request_id: run.request_id, native_run_id: run.run_id, source_csv_uri: run.source_csv_uri, source_csv_sha256: run.source_csv_sha256 })), produced_files };
}

export function registerStudySummary(server: McpApp, service: ResumableSimulationService) {
  const name = "modelica_summarize_recorded_study";
  server.registerTools([{ name, description: "Compare all declared power/loss baselines and selected independent solver-refinement runs from sealed native Modelica CSVs; generate exact-source temperature/energy CSVs, SVG plot, numerical consistency and selection report. No model simulation, arbitrary file, source code or output content is accepted.",
    inputSchema: { type: "object", additionalProperties: false, properties: {
      dataset_id: { enum: ["water-heater-sizing-01", "water-heater-sizing-02", "water-heater-sizing-03"] }, attempt_id: { type: "string", pattern: "^attempt-[A-Za-z0-9-]{1,40}$" },
      requests: { type: "array", minItems: 2, maxItems: 18, items: { type: "object", additionalProperties: false, properties: { request_id: { type: "string" }, expected_manifest_sha256: { type: "string", pattern: "^[0-9a-f]{64}$" } }, required: ["request_id", "expected_manifest_sha256"] } },
      time_limit_s: { type: "number", minimum: 30, maximum: 900 }, candidate_powers_w: { type: "array", minItems: 1, maxItems: 6, items: { type: "number", minimum: 350, maximum: 1800 } }, loss_conductances_w_per_k: { type: "array", minItems: 1, maxItems: 3, items: { type: "number", minimum: .6, maximum: 5 } },
    }, required: ["dataset_id", "attempt_id", "requests", "time_limit_s", "candidate_powers_w", "loss_conductances_w_per_k"] },
  }], new Map([[name, async (input: Record<string, unknown>) => { const result = await summarizeStudy(service, input); return { content: [{ type: "text", text: JSON.stringify(result) }], structuredContent: result }; }]]));
}
