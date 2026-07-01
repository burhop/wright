import type { FileEntry, SelectOptions } from "./wright-desktop";

export interface HostAdapter {
  readonly mode: "browser" | "desktop";
  fetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response>;
  readFile(path: string): Promise<string>;
  writeFile(path: string, content: string): Promise<void>;
  listDirectory(path: string): Promise<FileEntry[]>;
  selectFiles(options?: SelectOptions): Promise<string[]>;
  getApiBaseUrl(): string;
  getRouterType(): "browser" | "hash";
  notify(title: string, body: string): Promise<boolean>;
  hasTerminal(): boolean;
  dispose(): void;
}
