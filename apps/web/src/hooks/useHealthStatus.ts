import { useState, useEffect } from "react";
import healthService from "../services/health-service";
import useLogger from "./useLogger";
import type { ServiceStatus } from "../store/types";

export function useHealthStatus(intervalMs: number = 15000) {
  const [statuses, setStatuses] = useState<ServiceStatus[]>(
    healthService.getStatuses(),
  );
  const logger = useLogger("useHealthStatus");

  useEffect(() => {
    logger.info("Starting health status polling subscription");
    healthService.startPolling(intervalMs);

    const unsubscribe = healthService.onStatusChange((newStatuses) => {
      setStatuses(newStatuses);
      logger.info("Health status updated", { statuses: newStatuses });
    });

    return () => {
      logger.info("Stopping health status polling subscription");
      healthService.stopPolling();
      unsubscribe();
    };
  }, [intervalMs, logger]);

  return statuses;
}

export default useHealthStatus;
