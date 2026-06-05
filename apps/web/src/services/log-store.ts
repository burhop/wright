/**
 * IndexedDB-backed log persistence store for frontend logs.
 *
 * Per data-model.md: LogEntry schema with indexes on level, component, traceId, timestamp.
 * Per research.md Decision 1: Uses `idb` library for Promise-based IndexedDB access.
 * Per research.md Decision 7: FIFO eviction at configurable max entries (default: 10,000).
 *
 * Graceful fallback to no-op if IndexedDB is unavailable (incognito mode).
 */
import { openDB, type IDBPDatabase } from "idb";

export interface LogEntry {
  id?: number;
  timestamp: string;
  level: "debug" | "info" | "warn" | "error";
  message: string;
  component: string;
  traceId: string | null;
  sessionId: string | null;
  metadata: Record<string, unknown>;
}

export interface LogFilter {
  level?: LogEntry["level"];
  component?: string;
  traceId?: string;
  startTime?: string;
  endTime?: string;
}

const DB_NAME = "wright-logs";
const DB_VERSION = 1;
const STORE_NAME = "entries";
const DEFAULT_MAX_ENTRIES = 10_000;
const PRUNE_CHECK_INTERVAL = 100; // Check prune every N writes

class LogStore {
  private db: IDBPDatabase | null = null;
  private dbPromise: Promise<IDBPDatabase | null> | null = null;
  private writeCount = 0;
  private maxEntries: number;
  private available = true;

  // Batch buffer for non-blocking writes
  private buffer: LogEntry[] = [];
  private flushTimer: ReturnType<typeof setTimeout> | null = null;
  private readonly FLUSH_INTERVAL = 500;
  private readonly FLUSH_SIZE = 50;

  constructor(maxEntries = DEFAULT_MAX_ENTRIES) {
    this.maxEntries = maxEntries;
  }

  /**
   * Initialize the IndexedDB connection. Called lazily on first write.
   * Returns null if IndexedDB is unavailable.
   */
  private async getDb(): Promise<IDBPDatabase | null> {
    if (this.db) return this.db;
    if (!this.available) return null;
    if (this.dbPromise) return this.dbPromise;

    this.dbPromise = this.initDb();
    return this.dbPromise;
  }

  private async initDb(): Promise<IDBPDatabase | null> {
    try {
      const db = await openDB(DB_NAME, DB_VERSION, {
        upgrade(db) {
          if (!db.objectStoreNames.contains(STORE_NAME)) {
            const store = db.createObjectStore(STORE_NAME, {
              keyPath: "id",
              autoIncrement: true,
            });
            store.createIndex("level", "level", { unique: false });
            store.createIndex("component", "component", { unique: false });
            store.createIndex("traceId", "traceId", { unique: false });
            store.createIndex("timestamp", "timestamp", { unique: false });
            store.createIndex("sessionId", "sessionId", { unique: false });
          }
        },
      });
      this.db = db;
      return db;
    } catch (err) {
      console.warn(
        "[log-store] IndexedDB unavailable, falling back to console-only:",
        err,
      );
      this.available = false;
      return null;
    }
  }

  /**
   * Add a log entry to the buffer. Flushes periodically or when buffer is full.
   */
  async addEntry(entry: LogEntry): Promise<void> {
    if (!this.available) return;

    this.buffer.push(entry);

    if (this.buffer.length >= this.FLUSH_SIZE) {
      await this.flush();
    } else if (!this.flushTimer) {
      this.flushTimer = setTimeout(() => this.flush(), this.FLUSH_INTERVAL);
    }
  }

  /**
   * Flush buffered entries to IndexedDB in a single transaction.
   */
  async flush(): Promise<void> {
    if (this.flushTimer) {
      clearTimeout(this.flushTimer);
      this.flushTimer = null;
    }

    if (this.buffer.length === 0) return;

    const entries = [...this.buffer];
    this.buffer = [];

    const db = await this.getDb();
    if (!db) return;

    try {
      const tx = db.transaction(STORE_NAME, "readwrite");
      for (const entry of entries) {
        await tx.store.add(entry);
      }
      await tx.done;

      this.writeCount += entries.length;
      if (this.writeCount >= PRUNE_CHECK_INTERVAL) {
        this.writeCount = 0;
        // Non-blocking prune
        this.prune().catch(() => {});
      }
    } catch (err) {
      console.warn("[log-store] Failed to write log entries:", err);
    }
  }

  /**
   * Query log entries with optional filters.
   */
  async query(filters: LogFilter = {}): Promise<LogEntry[]> {
    const db = await this.getDb();
    if (!db) return [];

    try {
      let results: LogEntry[];

      // Use index-based query if a single filter matches an index
      if (filters.traceId) {
        results = await db.getAllFromIndex(
          STORE_NAME,
          "traceId",
          filters.traceId,
        );
      } else if (filters.level) {
        results = await db.getAllFromIndex(STORE_NAME, "level", filters.level);
      } else if (filters.component) {
        results = await db.getAllFromIndex(
          STORE_NAME,
          "component",
          filters.component,
        );
      } else {
        results = await db.getAll(STORE_NAME);
      }

      // Apply remaining filters in memory
      return results.filter((entry) => {
        if (filters.level && entry.level !== filters.level) return false;
        if (filters.component && entry.component !== filters.component)
          return false;
        if (filters.traceId && entry.traceId !== filters.traceId) return false;
        if (filters.startTime && entry.timestamp < filters.startTime)
          return false;
        if (filters.endTime && entry.timestamp > filters.endTime) return false;
        return true;
      });
    } catch (err) {
      console.warn("[log-store] Query failed:", err);
      return [];
    }
  }

  /**
   * Delete oldest entries beyond the retention limit (FIFO eviction).
   */
  async prune(maxEntries?: number): Promise<void> {
    const limit = maxEntries ?? this.maxEntries;
    const db = await this.getDb();
    if (!db) return;

    try {
      const count = await db.count(STORE_NAME);
      if (count <= limit) return;

      const deleteCount = count - limit;
      const tx = db.transaction(STORE_NAME, "readwrite");
      let cursor = await tx.store.openCursor();
      let deleted = 0;

      while (cursor && deleted < deleteCount) {
        await cursor.delete();
        deleted++;
        cursor = await cursor.continue();
      }

      await tx.done;
    } catch (err) {
      console.warn("[log-store] Prune failed:", err);
    }
  }

  /**
   * Get recent log entries for the future Log Viewer.
   */
  async getRecentEntries(limit = 100): Promise<LogEntry[]> {
    const db = await this.getDb();
    if (!db) return [];

    try {
      const all = await db.getAll(STORE_NAME);
      return all.slice(-limit).reverse();
    } catch (err) {
      console.warn("[log-store] getRecentEntries failed:", err);
      return [];
    }
  }

  /**
   * Check if IndexedDB is available for this instance.
   */
  isAvailable(): boolean {
    return this.available;
  }

  /**
   * Update the maximum entry retention count.
   */
  setMaxEntries(max: number): void {
    this.maxEntries = max;
  }
}

// Singleton instance
export const logStore = new LogStore();
export default logStore;
