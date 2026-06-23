/**
 * Centralized API fetch wrapper with automatic OTel tracing and structured error capture.
 *
 * All frontend service modules SHOULD use this client instead of raw fetch().
 * This ensures every API call:
 *   1. Creates an `api.fetch` span as a child of the active UI span
 *   2. Propagates trace_id to the backend via X-Trace-Id header
 *   3. Logs structured error entries on failure (status, url, duration_ms, trace_id)
 */
import telemetry from "./telemetry";
import { hostAdapter } from "./host-adapter";

export interface ApiError {
  error_code: string;
  message: string;
  trace_id: string;
  details?: Record<string, unknown>;
}

export class ApiClientError extends Error {
  public status: number;
  public errorCode: string;
  public traceId: string;
  public details?: Record<string, unknown>;

  constructor(status: number, apiError: ApiError) {
    super(apiError.message);
    this.name = "ApiClientError";
    this.status = status;
    this.errorCode = apiError.error_code;
    this.traceId = apiError.trace_id;
    this.details = apiError.details;
  }
}

type HttpMethod = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";

interface RequestOptions {
  headers?: Record<string, string>;
  signal?: AbortSignal;
  timeout?: number;
}

async function apiRequest<T>(
  method: HttpMethod,
  url: string,
  body?: unknown,
  options: RequestOptions = {},
): Promise<T> {
  const spanHandle = telemetry.startSpan(`api.fetch ${method} ${url}`);
  const startTime = performance.now();

  const headers: Record<string, string> = {
    ...options.headers,
  };

  // Propagate trace_id to backend
  if (spanHandle.traceId) {
    headers["X-Trace-Id"] = spanHandle.traceId;
  }

  // Only set Content-Type for requests with body
  if (body !== undefined && body !== null) {
    headers["Content-Type"] = "application/json";
  }

  try {
    const fetchOptions: RequestInit = {
      method,
      headers,
      signal: options.signal,
    };

    if (body !== undefined && body !== null) {
      fetchOptions.body = JSON.stringify(body);
    }

    const response = await hostAdapter.fetch(url, fetchOptions);
    const durationMs = Math.round(performance.now() - startTime);

    if (!response.ok) {
      let apiError: ApiError;
      try {
        apiError = await response.json();
      } catch {
        apiError = {
          error_code: "UNKNOWN_ERROR",
          message: `HTTP ${response.status}: ${response.statusText}`,
          trace_id: spanHandle.traceId || "unknown",
        };
      }

      const clientError = new ApiClientError(response.status, apiError);
      spanHandle.error(clientError);

      console.error("[api-client] Request failed", {
        method,
        url,
        status: response.status,
        error_code: apiError.error_code,
        message: apiError.message,
        trace_id: apiError.trace_id,
        duration_ms: durationMs,
      });

      throw clientError;
    }

    spanHandle.end();

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T;
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }

    // Network errors, timeouts, etc.
    const durationMs = Math.round(performance.now() - startTime);
    const networkError =
      error instanceof Error ? error : new Error(String(error));
    spanHandle.error(networkError);

    console.error("[api-client] Network error", {
      method,
      url,
      error: networkError.message,
      trace_id: spanHandle.traceId,
      duration_ms: durationMs,
    });

    throw networkError;
  }
}

/**
 * Centralized API client with typed HTTP methods.
 *
 * Usage:
 *   import { apiClient } from './api-client';
 *   const data = await apiClient.get<WorkspaceList>('/api/workspace/list');
 */
export const apiClient = {
  get<T>(url: string, options?: RequestOptions): Promise<T> {
    return apiRequest<T>("GET", url, undefined, options);
  },

  post<T>(url: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return apiRequest<T>("POST", url, body, options);
  },

  put<T>(url: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return apiRequest<T>("PUT", url, body, options);
  },

  patch<T>(url: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return apiRequest<T>("PATCH", url, body, options);
  },

  delete<T>(url: string, options?: RequestOptions): Promise<T> {
    return apiRequest<T>("DELETE", url, undefined, options);
  },
};

export default apiClient;
