import { BrowserView, BrowserWindow } from 'electron';

export interface WrightPanelOptions {
  wrightApiPort?: number;
  distPath?: string | null;
  workspacePath?: string | null;
}

export class WrightPanel {
  mainWindow: BrowserWindow;
  wrightApiPort: number;
  distPath: string | null;
  workspacePath: string | null;
  view: BrowserView | null;

  constructor(mainWindow: BrowserWindow, options?: WrightPanelOptions);
  createView(): BrowserView;
  destroy(): void;
}

export function validatePath(targetPath: string, workspacePath: string | null): void;
