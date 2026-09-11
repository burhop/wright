import React from "react";
import { createRoot } from "react-dom/client";
import { DevelopmentMetrics } from "./components/program-status/DevelopmentMetrics";
import "./index.css";

// Standalone embed has no AppShell to own scrolling.
document.documentElement.style.cssText = "height:auto;overflow:auto";
document.body.style.cssText = "height:auto;overflow:auto";
const root = document.getElementById("root")!;
root.style.cssText = "height:auto;width:100%;padding:16px";
createRoot(root).render(
  <React.StrictMode>
    <DevelopmentMetrics />
  </React.StrictMode>,
);
new ResizeObserver(() => {
  if (window.parent !== window)
    window.parent.postMessage(
      { type: "wright-metrics-height", height: root.scrollHeight + 24 },
      window.location.origin,
    );
}).observe(root);
