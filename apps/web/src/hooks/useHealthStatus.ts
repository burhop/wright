import { useState, useEffect } from "react";
import healthService from "../services/health-service";
import useLogger from "./useLogger";
import type { ServiceStatus } from "../store/types";

export function useHealthStatus(intervalMs: number = 15000, includeAgent = true) {
  const [statuses, setStatuses] = useState<ServiceStatus[]>(
    healthService.getStatuses(),
  );
  const logger = useLogger("useHealthStatus");

  useEffect(() => {
    logger.info("Starting health status polling subscription");
    const serviceIds = includeAgent ? undefined : ["wright-api"];
    healthService.startPolling(intervalMs, serviceIds);

    const unsubscribe = healthService.onStatusChange((newStatuses) => {
      setStatuses(newStatuses);
      logger.info("Health status updated", { statuses: newStatuses });
    });

    return () => {
      logger.info("Stopping health status polling subscription");
      healthService.stopPolling(serviceIds);
      unsubscribe();
    };
  }, [intervalMs, logger, includeAgent]);

  return includeAgent ? statuses : statuses.filter((svc) => svc.serviceId === "wright-api");
}

export default useHealthStatus;
