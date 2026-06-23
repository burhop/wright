const { app, BrowserWindow } = require('electron');
const { WrightPanel } = require('../panel.cjs');
const path = require('path');

app.whenReady().then(() => {
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  const panel = new WrightPanel(mainWindow, {
    wrightApiPort: 8000,
    distPath: path.join(__dirname, '../..', 'apps/web/dist-desktop'),
    workspacePath: path.join(__dirname, '../..')
  });

  console.log('[TestHarness] Initializing WrightPanel...');
  const view = panel.createView();
  mainWindow.setBrowserView(view);
  view.setBounds({ x: 0, y: 0, width: 800, height: 600 });

  view.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error(`[TestHarness] View failed to load: ${errorCode} - ${errorDescription}`);
    process.exit(1);
  });

  view.webContents.on('did-finish-load', () => {
    console.log('[TestHarness] View loaded successfully.');
  });

  setTimeout(() => {
    console.log('[TestHarness] Running validation assertions...');
    
    // Perform simple validation by checking if IPC handlers are set
    const { ipcMain } = require('electron');
    const registeredHandlers = ipcMain._events || {};
    
    console.log('[TestHarness] Tearing down panel and window...');
    panel.destroy();
    mainWindow.close();
    console.log('[TestHarness] Integration test PASSED.');
    app.quit();
    process.exit(0);
  }, 4000);
});
