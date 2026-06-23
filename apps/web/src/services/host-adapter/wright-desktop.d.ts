export interface FileEntry {
  name: string;
  path: string;
  isDirectory: boolean;
  size?: number;
}

export interface FileFilter {
  name: string;
  extensions: string[];
}

export interface SelectOptions {
  title?: string;
  filters?: FileFilter[];
  multiple?: boolean;
  directory?: boolean;
}

export interface NotifyPayload {
  title: string;
  body: string;
}

export interface WrightApiRequest {
  path: string;
  method?: string;
  body?: any;
  headers?: Record<string, string>;
  timeoutMs?: number;
}

export interface TerminalSession {
  id: string;
  pid: number;
}

export interface WrightConfig {
  apiPort: number;
  workspacePath: string | null;
}

export interface WrightDesktopBridge {
  api: <T>(request: WrightApiRequest) => Promise<T>;
  readFile: (path: string) => Promise<string>;
  writeFile: (path: string, content: string) => Promise<void>;
  listDirectory: (path: string) => Promise<FileEntry[]>;
  selectFiles: (options?: SelectOptions) => Promise<string[]>;
  notify: (payload: NotifyPayload) => Promise<boolean>;
  getConfig: () => Promise<WrightConfig>;
  onThemeChange: (callback: (payload: { theme: 'dark' | 'light' }) => void) => () => void;
  terminal: {
    start: (options?: { cols?: number; rows?: number; cwd?: string }) => Promise<TerminalSession>;
    write: (id: string, data: string) => Promise<void>;
    resize: (id: string, size: { cols: number; rows: number }) => Promise<void>;
    dispose: (id: string) => Promise<boolean>;
    onData: (id: string, callback: (data: string) => void) => () => void;
    onExit: (id: string, callback: (payload: { exitCode: number; signal?: number }) => void) => () => void;
  };
}

declare global {
  interface Window {
    wrightDesktop?: WrightDesktopBridge;
  }
}
