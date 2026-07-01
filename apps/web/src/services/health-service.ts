import type { ServiceStatus } from "../store/types";
import { hostAdapter } from "./host-adapter";

const API_BASE = hostAdapter.getApiBaseUrl();

export class LiveHealthService {
  private statuses: ServiceStatus[] = [
    {
      serviceId: "wright-api",
      name: "Wright API",
      endpoint: "/api/health",
      state: "unknown",
      lastChecked: null,
    },
    {
      serviceId: "hermes-agent",
      name: "Hermes Agent",
      endpoint: "/api/agent/health",
      state: "unknown",
      lastChecked: null,
    },
    {
      serviceId: "inference",
      name: "LLM Inference",
      endpoint: "/api/inference/health",
      state: "unknown",
      lastChecked: null,
    },
  ];

  private callbacks: Set<(statuses: ServiceStatus[]) => void> = new Set();
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private subscriberCount = 0;

  startPolling(intervalMs: number = 15000): void {
    this.subscriberCount++;
    if (this.intervalId) return;

    const runChecks = async () => {
      const checks = this.statuses.map(async (svc) => {
        const fetchWithRetry = async (
          retries = 1,
        ): Promise<"connected" | "disconnected"> => {
          try {
            const response = await hostAdapter.fetch(
              `${API_BASE}${svc.endpoint}`,
            );
            if (response.ok) {
              const data = await response.json();
              if (data.state === "connected" || data.state === "disconnected") {
                return data.state as "connected" | "disconnected";
              }
            }
          } catch (err) {
            // ignore and retry/fallback
          }
          if (retries > 0) {
            await new Promise((resolve) => setTimeout(resolve, 500));
            return fetchWithRetry(retries - 1);
          }
          return "disconnected";
        };

        const state = await fetchWithRetry();
        return {
          ...svc,
          state,
          lastChecked: Date.now(),
        };
      });

      const updated = await Promise.all(checks);
      this.statuses = updated;
      this.notify();
    };

    runChecks();
    this.intervalId = setInterval(runChecks, intervalMs);
  }

  stopPolling(): void {
    if (this.subscriberCount > 0) {
      this.subscriberCount--;
    }
    if (this.subscriberCount === 0 && this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  getStatuses(): ServiceStatus[] {
    return this.statuses;
  }

  onStatusChange(callback: (statuses: ServiceStatus[]) => void): () => void {
    this.callbacks.add(callback);
    callback(this.statuses);
    return () => {
      this.callbacks.delete(callback);
    };
  }

  private notify() {
    this.callbacks.forEach((cb) => cb(this.statuses));
  }
}

export const healthService = new LiveHealthService();
export default healthService;
