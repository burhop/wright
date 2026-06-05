import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { telemetry } from "./services/telemetry";
import { registerTraceIdProvider, logger } from "./services/logger";
import "./index.css";
import App from "./App.tsx";

// Connect telemetry trace ID provider to logger
registerTraceIdProvider(() => telemetry.getActiveTraceId());

logger.info("Application initialized", { env: "browser" });

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
