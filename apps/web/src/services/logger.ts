import type { LogEntry } from '../store/types';
import { logStore, type LogEntry as StoreLogEntry } from './log-store';

export interface Logger {
  debug(message: string, metadata?: Record<string, unknown>): void;
  info(message: string, metadata?: Record<string, unknown>): void;
  warn(message: string, metadata?: Record<string, unknown>): void;
  error(message: string, metadata?: Record<string, unknown>): void;
  child(component: string): Logger;
}

let activeTraceIdProvider: () => string | null = () => null;
let activeSessionId: string | null = null;

export function registerTraceIdProvider(provider: () => string | null) {
  activeTraceIdProvider = provider;
}

export function setActiveSessionId(sessionId: string | null) {
  activeSessionId = sessionId;
}

export class ConsoleLogger implements Logger {
  private component: string;

  constructor(component: string = 'App') {
    this.component = component;
  }

  private log(level: LogEntry['level'], message: string, metadata: Record<string, unknown> = {}) {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      component: this.component,
      traceId: activeTraceIdProvider(),
      metadata,
    };
    
    const formatted = JSON.stringify(entry);
    switch (level) {
      case 'debug':
        console.debug(formatted);
        break;
      case 'info':
        console.info(formatted);
        break;
      case 'warn':
        console.warn(formatted);
        break;
      case 'error':
        console.error(formatted);
        break;
    }

    // Persist to IndexedDB for future Log Viewer
    const storeEntry: StoreLogEntry = {
      timestamp: entry.timestamp,
      level: entry.level,
      message: entry.message,
      component: entry.component,
      traceId: entry.traceId,
      sessionId: activeSessionId,
      metadata: entry.metadata,
    };
    logStore.addEntry(storeEntry).catch(() => {
      // Silently ignore persistence failures
    });
  }

  debug(message: string, metadata?: Record<string, unknown>): void {
    this.log('debug', message, metadata);
  }

  info(message: string, metadata?: Record<string, unknown>): void {
    this.log('info', message, metadata);
  }

  warn(message: string, metadata?: Record<string, unknown>): void {
    this.log('warn', message, metadata);
  }

  error(message: string, metadata?: Record<string, unknown>): void {
    this.log('error', message, metadata);
  }

  child(component: string): Logger {
    return new ConsoleLogger(component);
  }
}

export const logger = new ConsoleLogger();
export default logger;

