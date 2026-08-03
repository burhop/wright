// Slice-057 lifecycle fixture.  It deliberately has no workflow/tool/network authority.
process.stdout.write(JSON.stringify({ type: "started", runId: process.env.WRIGHT_RIVET_RUN_ID }) + "\n");
const timer = setTimeout(() => process.exit(0), 60_000);
for (const signal of ["SIGINT", "SIGTERM"]) {
  process.once(signal, () => {
    clearTimeout(timer);
    process.stdout.write(JSON.stringify({ type: "cancelled" }) + "\n");
    process.exit(0);
  });
}
