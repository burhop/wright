import type { ServiceStatus } from "../store/types";
import { hostAdapter } from "./host-adapter";

const API_BASE = hostAdapter.getApiBaseUrl();
type HealthCheckResult = Pick<
  ServiceStatus,
  "state" | "latencyMs" | "baseUrl" | "error"
>;

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
      serviceId: "llm-backend",
      name: "LLM Backend",
      endpoint: "/api/inference/health",
      state: "unknown",
      lastChecked: null,
    },
  ];

  private callbacks: Set<(statuses: ServiceStatus[]) => void> = new Set();
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private subscriberCount = 0;
  private checksInFlight = new Set<string>();

  private async checkService(svc: ServiceStatus): Promise<void> {
    if (this.checksInFlight.has(svc.serviceId)) return;
    this.checksInFlight.add(svc.serviceId);

    const fetchWithRetry = async (
      retries = 1,
    ): Promise<HealthCheckResult> => {
      try {
        const response = await hostAdapter.fetch(`${API_BASE}${svc.endpoint}`);
        if (response.ok) {
          const data = await response.json();
          if (
            data.state === "connected" ||
            data.state === "disconnected" ||
            data.state === "unknown"
          ) {
            return {
              state: data.state as "connected" | "disconnected" | "unknown",
              latencyMs: data.latencyMs ?? null,
              baseUrl: data.baseUrl ?? null,
              error: data.error ?? null,
            };
          }
        }
      } catch {
        // Ignore and retry before reporting the request as unavailable.
      }
      if (retries > 0) {
        await new Promise((resolve) => setTimeout(resolve, 500));
        return fetchWithRetry(retries - 1);
      }
      return {
        state: "disconnected",
        latencyMs: null,
        baseUrl: null,
        error: "Health check request failed",
      };
    };

    try {
      const result = await fetchWithRetry();
      this.statuses = this.statuses.map((current) =>
        current.serviceId === svc.serviceId
          ? {
              ...current,
              ...result,
              lastChecked: Date.now(),
            }
          : current,
      );
      this.notify();
    } finally {
      this.checksInFlight.delete(svc.serviceId);
    }
  }

  private runChecks(): void {
    this.statuses.forEach((svc) => {
      void this.checkService(svc);
    });
  }

  startPolling(intervalMs: number = 15000): void {
    this.subscriberCount++;
    if (this.intervalId) return;

    this.runChecks();
    this.intervalId = setInterval(() => this.runChecks(), intervalMs);
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
