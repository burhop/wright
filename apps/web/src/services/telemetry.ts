import { trace } from "@opentelemetry/api";
import type { Tracer } from "@opentelemetry/api";
import {
  WebTracerProvider,
  SimpleSpanProcessor,
  ConsoleSpanExporter,
} from "@opentelemetry/sdk-trace-web";
import type { TraceContext } from "../store/types";

export interface SpanHandle {
  end(): void;
  error(err: Error): void;
  traceId: string;
}

export interface TelemetryService {
  startSpan(actionName: string): SpanHandle;
  getActiveTraceId(): string | null;
  getRecentTraces(limit: number): TraceContext[];
}

class OpenTelemetryService implements TelemetryService {
  private tracer: Tracer;
  private recentTraces: TraceContext[] = [];
  private activeTraceId: string | null = null;
  private provider: WebTracerProvider;

  constructor() {
    this.provider = new WebTracerProvider({
      spanProcessors: [new SimpleSpanProcessor(new ConsoleSpanExporter())],
    });
    this.provider.register();
    this.tracer = trace.getTracer("wright-frontend", "1.0.0");
  }

  startSpan(actionName: string): SpanHandle {
    const span = this.tracer.startSpan(actionName);
    const spanContext = span.spanContext();
    const traceId = spanContext.traceId;
    const spanId = spanContext.spanId;

    this.activeTraceId = traceId;

    const traceCtx: TraceContext = {
      traceId,
      spanId,
      actionName,
      startTime: Date.now(),
      duration: null,
      status: "in-progress",
    };

    this.recentTraces.unshift(traceCtx);
    if (this.recentTraces.length > 50) {
      this.recentTraces.pop();
    }

    return {
      traceId,
      end: () => {
        span.end();
        traceCtx.duration = Date.now() - traceCtx.startTime;
        traceCtx.status = "ok";
        if (this.activeTraceId === traceId) {
          this.activeTraceId = null;
        }
      },
      error: (err: Error) => {
        span.recordException(err);
        span.setStatus({ code: 2, message: err.message }); // SpanStatusCode.ERROR is 2
        span.end();
        traceCtx.duration = Date.now() - traceCtx.startTime;
        traceCtx.status = "error";
        if (this.activeTraceId === traceId) {
          this.activeTraceId = null;
        }
      },
    };
  }

  getActiveTraceId(): string | null {
    return this.activeTraceId;
  }

  getRecentTraces(limit: number): TraceContext[] {
    return this.recentTraces.slice(0, limit);
  }
}

export const telemetry = new OpenTelemetryService();

/**
 * Start a UI-level OTel span for component or user interaction tracing.
 * Convenience wrapper that prefixes span names with "ui." for semantic hierarchy.
 *
 * Usage:
 *   const span = startUISpan('dashboard.load');
 *   try { ... span.end(); } catch (err) { span.error(err); }
 */
export function startUISpan(name: string): SpanHandle {
  return telemetry.startSpan(`ui.${name}`);
}

/**
 * Record a UI error boundary exception as an OTel span.
 * Used by React error boundaries to create ui.error.boundary spans.
 */
export function recordUIError(error: Error, componentStack?: string): void {
  const span = telemetry.startSpan("ui.error.boundary");
  if (componentStack) {
    // We can't set attributes directly on SpanHandle, but we log the context
    console.error("[telemetry] Error boundary triggered", {
      error: error.message,
      componentStack,
      traceId: span.traceId,
    });
  }
  span.error(error);
}

export default telemetry;
