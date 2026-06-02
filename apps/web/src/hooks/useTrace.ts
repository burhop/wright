import { useCallback } from 'react';
import { telemetry } from '../services/telemetry';
import type { SpanHandle } from '../services/telemetry';

export function useTrace() {
  const startSpan = useCallback((actionName: string): SpanHandle => {
    return telemetry.startSpan(actionName);
  }, []);

  const traceAction = useCallback(async <T>(
    actionName: string,
    actionFn: (span: SpanHandle) => Promise<T>
  ): Promise<T> => {
    const span = telemetry.startSpan(actionName);
    try {
      const result = await actionFn(span);
      span.end();
      return result;
    } catch (err) {
      span.error(err instanceof Error ? err : new Error(String(err)));
      throw err;
    }
  }, []);

  return { startSpan, traceAction };
}

export default useTrace;
