import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { telemetry } from "./services/telemetry";
import { registerTraceIdProvider, logger } from "./services/logger";
import "./index.css";
import App, { createAppRouter } from "./App.tsx";
import { restoreCachedTheme } from "./services/ui-preferences";

restoreCachedTheme();

// Connect telemetry trace ID provider to logger
registerTraceIdProvider(() => telemetry.getActiveTraceId());

logger.info("Application initialized", { env: "browser" });

const router = createAppRouter();
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App router={router} />
  </StrictMode>,
);
