import { useMemo } from "react";
import { logger } from "../services/logger";
import type { Logger } from "../services/logger";

export function useLogger(componentName: string): Logger {
  return useMemo(() => logger.child(componentName), [componentName]);
}

export default useLogger;
