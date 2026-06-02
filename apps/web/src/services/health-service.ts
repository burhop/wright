import type { ServiceStatus } from '../store/types';

const API_BASE = 'http://127.0.0.1:8000';

export class LiveHealthService {
  private statuses: ServiceStatus[] = [
    { serviceId: 'wright-api', name: 'Wright API', endpoint: '/api/health', state: 'unknown', lastChecked: null },
    { serviceId: 'hermes-agent', name: 'Hermes Agent', endpoint: '/api/agent/health', state: 'unknown', lastChecked: null },
    { serviceId: 'inference', name: 'LLM Inference', endpoint: '/api/inference/health', state: 'unknown', lastChecked: null },
  ];

  private callbacks: Set<(statuses: ServiceStatus[]) => void> = new Set();
  private intervalId: ReturnType<typeof setInterval> | null = null;

  startPolling(intervalMs: number = 15000): void {
    if (this.intervalId) return;

    const runChecks = async () => {
      const checks = this.statuses.map(async (svc) => {
        try {
          const response = await fetch(`${API_BASE}${svc.endpoint}`);
          if (response.ok) {
            const data = await response.json();
            return {
              ...svc,
              state: data.state as 'connected' | 'disconnected',
              lastChecked: Date.now(),
            };
          }
          return { ...svc, state: 'disconnected' as const, lastChecked: Date.now() };
        } catch {
          return { ...svc, state: 'disconnected' as const, lastChecked: Date.now() };
        }
      });

      const updated = await Promise.all(checks);
      this.statuses = updated;
      this.notify();
    };

    runChecks();
    this.intervalId = setInterval(runChecks, intervalMs);
  }

  stopPolling(): void {
    if (this.intervalId) {
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
