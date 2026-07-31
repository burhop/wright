const path = require('path');
const fs = require('fs/promises');
const http = require('http');
const { nativeTheme, dialog, Notification, ipcMain, shell } = require('electron');

let ptyModule = null;
try {
  ptyModule = require('node-pty');
} catch (e) {
  console.warn('[WrightPanel] node-pty not found. Terminal support is disabled.');
}

function validatePath(targetPath, workspacePath) {
  if (!workspacePath) return; // No workspace path configured, skip check
  
  const resolvedTarget = path.resolve(targetPath);
  const resolvedWorkspace = path.resolve(workspacePath);
  
  const relative = path.relative(resolvedWorkspace, resolvedTarget);
  const isInside = relative && !relative.startsWith('..') && !path.isAbsolute(relative);
  const isEqual = resolvedTarget === resolvedWorkspace;
  
  if (!isInside && !isEqual) {
    const err = new Error("Access Denied: Path is outside the workspace root.");
    err.code = "EACCES";
    throw err;
  }
}

function proxyRequest(port, options) {
  return new Promise((resolve, reject) => {
    const { path: apiPath, method = 'GET', body, headers = {}, timeoutMs = 30000 } = options;
    
    const proxyHeaders = { ...headers };
    delete proxyHeaders['host'];
    delete proxyHeaders['connection'];
    
    const requestOptions = {
      hostname: 'localhost',
      port: port,
      path: apiPath,
      method: method.toUpperCase(),
      headers: proxyHeaders,
      timeout: timeoutMs,
    };
    
    const req = http.request(requestOptions, (res) => {
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      res.on('end', () => {
        const isJson = res.headers['content-type'] && res.headers['content-type'].includes('application/json');
        let parsed = data;
        if (isJson) {
          try {
            parsed = JSON.parse(data);
          } catch (e) {
            // Keep as raw text
          }
        }
        
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(parsed);
        } else {
          reject({
            status: res.statusCode,
            code: 'API_ERROR',
            message: `API request failed with status ${res.statusCode}`,
            details: parsed
          });
        }
      });
    });
    
    req.on('error', (err) => {
      reject({
        status: 503,
        code: 'FETCH_FAILED',
        message: `Failed to connect to Wright API: ${err.message}`,
        details: err
      });
    });
    
    req.on('timeout', () => {
      req.destroy();
      reject({
        status: 504,
        code: 'TIMEOUT',
        message: 'Request to Wright API timed out',
      });
    });
    
    if (body !== undefined && body !== null) {
      const bodyStr = typeof body === 'string' ? body : JSON.stringify(body);
      req.setHeader('Content-Type', 'application/json');
      req.setHeader('Content-Length', Buffer.byteLength(bodyStr));
      req.write(bodyStr);
    }
    
    req.end();
  });
}

function validateExternalUrl(rawUrl, options = {}) {
  let url;
  try {
    url = new URL(rawUrl);
  } catch {
    const error = new Error('External URL must be absolute.');
    error.code = 'SURFACE_HOST_URL_REJECTED';
    throw error;
  }
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) {
    const error = new Error('External URL must use HTTP(S) without credentials.');
    error.code = 'SURFACE_HOST_URL_REJECTED';
    throw error;
  }
  if (options.approvedDirectUrl === true) {
    const allowed = new Set(options.allowedExternalOrigins || []);
    if (!allowed.has(url.origin)) {
      const error = new Error('Direct external origin is not allowlisted.');
      error.code = 'SURFACE_HOST_URL_REJECTED';
      throw error;
    }
    return url.toString();
  }
  const previewDomain = String(options.previewDomain || 'localhost').toLowerCase();
  const expectedPort = String(options.previewPort || 8000);
  const expectedProtocol = `${options.previewScheme || 'http'}:`;
  // A presentation must never share the control-plane/apex origin. The
  // backend-issued opaque label is a mandatory origin-isolation boundary.
  const previewHost = url.hostname.endsWith(`.${previewDomain}`);
  const port = url.port || (url.protocol === 'https:' ? '443' : '80');
  if (
    !previewHost ||
    url.protocol !== expectedProtocol ||
    port !== expectedPort ||
    url.pathname !== '/__wright/bootstrap' ||
    url.search ||
    url.hash.slice(1).length < 32
  ) {
    const error = new Error('External URL is not an issued Wright preview URL.');
    error.code = 'SURFACE_HOST_URL_REJECTED';
    throw error;
  }
  return url.toString();
}

function installNavigationPolicy(webContents, controlUrl) {
  const allowed = new URL(controlUrl);
  webContents.on('will-navigate', (event, target) => {
    let destination;
    try {
      destination = new URL(target);
    } catch {
      event.preventDefault();
      return;
    }
    const permitted = allowed.protocol === 'file:'
      ? destination.protocol === 'file:' && destination.pathname === allowed.pathname
      : destination.origin === allowed.origin;
    if (!permitted) event.preventDefault();
  });
  webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
}

class WrightPanel {
  constructor(mainWindow, options = {}) {
    this.mainWindow = mainWindow;
    this.wrightApiPort = options.wrightApiPort || 8000;
    this.distPath = options.distPath || null;
    this.workspacePath = options.workspacePath || null;
    this.previewDomain = options.previewDomain || 'localhost';
    this.previewScheme = options.previewScheme || 'http';
    this.previewPort = options.previewPort || this.wrightApiPort;
    this.allowedExternalOrigins = Object.freeze([...(options.allowedExternalOrigins || [])]);
    this.view = null;
    this.themeListener = null;
    this.terminalSessions = new Map();

    this.ipcHandlers = {
      api: (event, options) => proxyRequest(this.wrightApiPort, options),
      readFile: (event, path) => this.handleReadFile(path),
      writeFile: (event, payload) => this.handleWriteFile(payload),
      listDirectory: (event, path) => this.handleListDirectory(path),
      selectFiles: (event, options) => this.handleSelectFiles(options),
      notify: (event, payload) => this.handleNotify(payload),
      openExternal: (event, payload) => this.handleOpenExternal(payload),
      getConfig: () => Promise.resolve({
        apiPort: this.wrightApiPort,
        workspacePath: this.workspacePath,
      }),
      terminalStart: (event, options) => this.handleTerminalStart(options),
      terminalWrite: (event, payload) => this.handleTerminalWrite(payload),
      terminalResize: (event, payload) => this.handleTerminalResize(payload),
      terminalDispose: (event, id) => this.handleTerminalDispose(id),
    };
  }

  createView() {
    const { BrowserView } = require('electron');
    const view = new BrowserView({
      webPreferences: {
        preload: path.join(__dirname, 'preload.cjs'),
        contextIsolation: true,
        nodeIntegration: false,
        sandbox: true,
        webSecurity: true,
        allowRunningInsecureContent: false,
      }
    });
    
    this.view = view;
    this.registerIpc();
    
    if (this.distPath) {
      const { pathToFileURL } = require('url');
      const indexUrl = pathToFileURL(path.resolve(this.distPath, 'index.html')).toString();
      installNavigationPolicy(view.webContents, indexUrl);
      view.webContents.loadURL(indexUrl);
    } else {
      const controlUrl = `http://localhost:${this.wrightApiPort}`;
      installNavigationPolicy(view.webContents, controlUrl);
      view.webContents.loadURL(controlUrl);
    }
    
    const handleThemeChange = () => {
      if (view && !view.webContents.isDestroyed()) {
        const theme = nativeTheme.shouldUseDarkColors ? 'dark' : 'light';
        view.webContents.send('wright:theme-changed', { theme });
      }
    };
    nativeTheme.on('updated', handleThemeChange);
    this.themeListener = handleThemeChange;
    
    view.webContents.on('did-finish-load', () => {
      handleThemeChange();
    });
    
    return view;
  }

  registerIpc() {
    ipcMain.handle('wright:api', this.ipcHandlers.api);
    ipcMain.handle('wright:readFile', this.ipcHandlers.readFile);
    ipcMain.handle('wright:writeFile', this.ipcHandlers.writeFile);
    ipcMain.handle('wright:listDirectory', this.ipcHandlers.listDirectory);
    ipcMain.handle('wright:selectFiles', this.ipcHandlers.selectFiles);
    ipcMain.handle('wright:notify', this.ipcHandlers.notify);
    ipcMain.handle('wright:openExternal', this.ipcHandlers.openExternal);
    ipcMain.handle('wright:getConfig', this.ipcHandlers.getConfig);
    ipcMain.handle('wright:terminal:start', this.ipcHandlers.terminalStart);
    ipcMain.handle('wright:terminal:write', this.ipcHandlers.terminalWrite);
    ipcMain.handle('wright:terminal:resize', this.ipcHandlers.terminalResize);
    ipcMain.handle('wright:terminal:dispose', this.ipcHandlers.terminalDispose);
  }

  unregisterIpc() {
    ipcMain.removeHandler('wright:api');
    ipcMain.removeHandler('wright:readFile');
    ipcMain.removeHandler('wright:writeFile');
    ipcMain.removeHandler('wright:listDirectory');
    ipcMain.removeHandler('wright:selectFiles');
    ipcMain.removeHandler('wright:notify');
    ipcMain.removeHandler('wright:openExternal');
    ipcMain.removeHandler('wright:getConfig');
    ipcMain.removeHandler('wright:terminal:start');
    ipcMain.removeHandler('wright:terminal:write');
    ipcMain.removeHandler('wright:terminal:resize');
    ipcMain.removeHandler('wright:terminal:dispose');
  }

  destroy() {
    this.unregisterIpc();
    
    if (this.themeListener) {
      nativeTheme.off('updated', this.themeListener);
      this.themeListener = null;
    }
    
    for (const [id, ptyProcess] of this.terminalSessions.entries()) {
      try {
        ptyProcess.kill();
      } catch (e) {}
    }
    this.terminalSessions.clear();
    
    this.view = null;
  }

  // Implementation helpers for files and capabilities
  async handleReadFile(filePath) {
    validatePath(filePath, this.workspacePath);
    try {
      return await fs.readFile(filePath, 'utf8');
    } catch (err) {
      throw {
        code: err.code || 'FS_ERROR',
        message: `Failed to read file: ${err.message}`,
      };
    }
  }

  async handleWriteFile(payload) {
    const { path: filePath, content } = payload;
    validatePath(filePath, this.workspacePath);
    try {
      await fs.writeFile(filePath, content, 'utf8');
    } catch (err) {
      throw {
        code: err.code || 'FS_ERROR',
        message: `Failed to write file: ${err.message}`,
      };
    }
  }

  async handleListDirectory(dirPath) {
    validatePath(dirPath, this.workspacePath);
    try {
      const entries = await fs.readdir(dirPath, { withFileTypes: true });
      const result = [];
      for (const entry of entries) {
        const fullPath = path.join(dirPath, entry.name);
        let size = 0;
        if (entry.isFile()) {
          try {
            const stat = await fs.stat(fullPath);
            size = stat.size;
          } catch (e) {}
        }
        result.push({
          name: entry.name,
          path: fullPath,
          isDirectory: entry.isDirectory(),
          size: entry.isFile() ? size : undefined,
        });
      }
      return result;
    } catch (err) {
      throw {
        code: err.code || 'FS_ERROR',
        message: `Failed to list directory: ${err.message}`,
      };
    }
  }

  async handleSelectFiles(options = {}) {
    const properties = [];
    if (options.multiple) properties.push('multiSelections');
    if (options.directory) {
      properties.push('openDirectory');
    } else {
      properties.push('openFile');
    }
    
    const filters = [];
    if (options.filters) {
      for (const f of options.filters) {
        filters.push({ name: f.name, extensions: f.extensions });
      }
    }
    
    try {
      const res = await dialog.showOpenDialog(this.mainWindow, {
        title: options.title || 'Select Files',
        properties,
        filters,
      });
      return res.canceled ? [] : res.filePaths;
    } catch (err) {
      throw {
        code: 'DIALOG_ERROR',
        message: err.message,
      };
    }
  }

  async handleNotify(payload) {
    const { title, body } = payload;
    try {
      if (!Notification.isSupported()) return false;
      const notification = new Notification({ title, body });
      notification.show();
      return true;
    } catch (err) {
      return false;
    }
  }

  async handleOpenExternal(payload = {}) {
    const validated = validateExternalUrl(payload.url, {
      approvedDirectUrl: payload.options?.approvedDirectUrl === true,
      allowedExternalOrigins: this.allowedExternalOrigins,
      previewDomain: this.previewDomain,
      previewScheme: this.previewScheme,
      previewPort: this.previewPort,
    });
    await shell.openExternal(validated, { activate: true });
    return true;
  }

  async handleTerminalStart(options = {}) {
    if (!ptyModule) {
      throw {
        code: 'NOT_IMPLEMENTED',
        message: 'Terminal integration is disabled (node-pty is missing on host)',
      };
    }
    
    if (this.terminalSessions.size >= 10) {
      throw {
        code: 'EACCES',
        message: 'Maximum terminal sessions limit (10) reached.',
      };
    }
    
    const id = Math.random().toString(36).substring(2, 11);
    const shell = process.platform === 'win32' ? 'powershell.exe' : 'bash';
    
    try {
      const ptyProcess = ptyModule.spawn(shell, [], {
        name: 'xterm-color',
        cols: options.cols || 80,
        rows: options.rows || 24,
        cwd: options.cwd || process.env.HOME || process.env.USERPROFILE,
        env: process.env
      });
      
      this.terminalSessions.set(id, ptyProcess);
      
      ptyProcess.onData((data) => {
        if (this.view && !this.view.webContents.isDestroyed()) {
          this.view.webContents.send(`wright:terminal:data:${id}`, data);
        }
      });
      
      ptyProcess.onExit(({ exitCode, signal }) => {
        if (this.view && !this.view.webContents.isDestroyed()) {
          this.view.webContents.send(`wright:terminal:exit:${id}`, { exitCode, signal });
        }
        this.terminalSessions.delete(id);
      });
      
      return { id, pid: ptyProcess.pid };
    } catch (err) {
      throw {
        code: 'PTY_ERROR',
        message: `Failed to start terminal: ${err.message}`,
      };
    }
  }

  async handleTerminalWrite({ id, data }) {
    const ptyProcess = this.terminalSessions.get(id);
    if (!ptyProcess) {
      throw { code: 'ENOENT', message: 'Terminal session not found' };
    }
    ptyProcess.write(data);
  }

  async handleTerminalResize({ id, cols, rows }) {
    const ptyProcess = this.terminalSessions.get(id);
    if (!ptyProcess) {
      throw { code: 'ENOENT', message: 'Terminal session not found' };
    }
    ptyProcess.resize(cols, rows);
  }

  async handleTerminalDispose(id) {
    const ptyProcess = this.terminalSessions.get(id);
    if (!ptyProcess) return false;
    try {
      ptyProcess.kill();
      this.terminalSessions.delete(id);
      return true;
    } catch (err) {
      return false;
    }
  }
}

module.exports = {
  WrightPanel,
  validatePath,
  validateExternalUrl,
  installNavigationPolicy
};
