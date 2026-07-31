// The with-dependencies entry keeps the packaged ui:// document offline and single-file.
import { App } from "@modelcontextprotocol/ext-apps/app-with-deps";
import "./style.css";

const status = document.querySelector<HTMLParagraphElement>("#status")!;
const width = document.querySelector<HTMLInputElement>("#width")!;
const height = document.querySelector<HTMLInputElement>("#height")!;
const shape = document.querySelector<SVGRectElement>("#shape")!;

function render(value: Record<string, unknown>): void {
  width.value = String(value.width ?? width.value);
  height.value = String(value.height ?? height.value);
  shape.setAttribute("width", String(Math.max(40, Number(width.value) * 4)));
  shape.setAttribute("height", String(Math.max(40, Number(height.value) * 4)));
  status.textContent = `Revision ${String(value.revision ?? "?")} is visible.`;
}

const app = new App({ name: "Wright reference design", version: "1.0.0" });
app.ontoolresult = (result) => {
  if (result.structuredContent) render(result.structuredContent);
};
app.onteardown = async () => {
  status.textContent = "View closed.";
  return {};
};

document.querySelector<HTMLFormElement>("#dimensions")!.addEventListener("submit", async (event) => {
  event.preventDefault();
  status.textContent = "Updating…";
  try {
    const result = await app.callServerTool({
      name: "resize_design",
      arguments: { width: Number(width.value), height: Number(height.value) },
    });
    if (result.structuredContent) render(result.structuredContent);
  } catch (error) {
    status.textContent = error instanceof Error ? error.message : "Update denied.";
  }
});

document.querySelector<HTMLButtonElement>("#denied")!.addEventListener("click", async () => {
  try {
    await app.callServerTool({ name: "model_only_status", arguments: {} });
    status.textContent = "Unexpectedly allowed.";
  } catch {
    status.textContent = "Correctly denied: this operation is model-only.";
  }
});
document.querySelector<HTMLButtonElement>("#close")!.addEventListener("click", () => app.requestTeardown());

await app.connect();
status.textContent = "Connected. Ask Wright to show_design, or resize it here.";
