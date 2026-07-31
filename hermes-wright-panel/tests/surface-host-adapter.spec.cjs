const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const test = require('node:test');
const Module = require('node:module');

function loadPanel() {
  const handlers = new Map();
  const shellCalls = [];
  const electron = {
    nativeTheme: Object.assign(new EventEmitter(), { shouldUseDarkColors: false }),
    dialog: { showOpenDialog: async () => ({ canceled: true, filePaths: [] }) },
    Notification: class { static isSupported() { return false; } },
    ipcMain: {
      handle: (name, callback) => handlers.set(name, callback),
      removeHandler: (name) => handlers.delete(name),
    },
    shell: {
      openExternal: async (...args) => {
        shellCalls.push(args);
      },
    },
  };
  const original = Module._load;
  Module._load = function(request, parent, isMain) {
    if (request === 'electron') return electron;
    return original.call(this, request, parent, isMain);
  };
  const path = require.resolve('../panel.cjs');
  delete require.cache[path];
  const loaded = require(path);
  Module._load = original;
  return { ...loaded, handlers, shellCalls };
}

test('external-open IPC accepts only issued preview or allowlisted direct URLs', async () => {
  const { WrightPanel, handlers, shellCalls } = loadPanel();
  const panel = new WrightPanel({}, {
    wrightApiPort: 8000,
    previewDomain: 'localhost',
    allowedExternalOrigins: ['https://brep.example.test'],
  });
  panel.registerIpc();
  const open = handlers.get('wright:openExternal');
  await open({}, {
    url: 'http://s-presentation.localhost:8000/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345',
    options: { approvedDirectUrl: false },
  });
  await open({}, {
    url: 'https://brep.example.test/design/42',
    options: { approvedDirectUrl: true },
  });
  assert.equal(shellCalls.length, 2);
  await assert.rejects(
    open({}, {
      url: 'https://evil.example/design/42',
      options: { approvedDirectUrl: true },
    }),
    { code: 'SURFACE_HOST_URL_REJECTED' },
  );
  await assert.rejects(
    open({}, {
      url: 'file:///etc/passwd',
      options: { approvedDirectUrl: false },
    }),
    { code: 'SURFACE_HOST_URL_REJECTED' },
  );
  await assert.rejects(
    open({}, {
      url: 'http://localhost:8000/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz012345',
      options: { approvedDirectUrl: false },
    }),
    { code: 'SURFACE_HOST_URL_REJECTED' },
  );
  panel.destroy();
});

test('navigation and window-open policies deny escape from Wright control UI', () => {
  const { installNavigationPolicy } = loadPanel();
  const contents = new EventEmitter();
  let windowPolicy;
  contents.setWindowOpenHandler = (callback) => {
    windowPolicy = callback;
  };
  installNavigationPolicy(contents, 'http://localhost:8000/');
  const allowed = { prevented: false, preventDefault() { this.prevented = true; } };
  contents.emit('will-navigate', allowed, 'http://localhost:8000/workspace/one');
  assert.equal(allowed.prevented, false);
  const denied = { prevented: false, preventDefault() { this.prevented = true; } };
  contents.emit('will-navigate', denied, 'https://evil.example/');
  assert.equal(denied.prevented, true);
  assert.deepEqual(windowPolicy({ url: 'https://evil.example/' }), { action: 'deny' });
});

test('desktop return accelerator is narrow, repeat-safe, and removable', () => {
  const { installReturnToHostAccelerator } = loadPanel();
  const contents = Object.assign(new EventEmitter(), {
    sent: [],
    isDestroyed: () => false,
    send(channel) { this.sent.push(channel); },
  });
  const remove = installReturnToHostAccelerator(contents);
  const event = { prevented: false, preventDefault() { this.prevented = true; } };
  const modifier = process.platform === 'darwin' ? { meta: true } : { control: true };
  contents.emit('before-input-event', event, {
    type: 'keyDown', key: 'F6', shift: true, ...modifier,
  });
  assert.equal(event.prevented, true);
  assert.deepEqual(contents.sent, ['wright:return-to-host']);

  contents.emit('before-input-event', event, {
    type: 'keyDown', key: 'F6', shift: true, isAutoRepeat: true, ...modifier,
  });
  contents.emit('before-input-event', event, {
    type: 'keyDown', key: 'F6', shift: false, ...modifier,
  });
  assert.deepEqual(contents.sent, ['wright:return-to-host']);
  remove();
  contents.emit('before-input-event', event, {
    type: 'keyDown', key: 'F6', shift: true, ...modifier,
  });
  assert.deepEqual(contents.sent, ['wright:return-to-host']);
});

test('preload bridge is not exposed inside child frames', () => {
  const originalLoad = Module._load;
  const originalMainFrame = process.isMainFrame;
  let exposures = 0;
  Module._load = function(request, parent, isMain) {
    if (request === 'electron') {
      return {
        contextBridge: { exposeInMainWorld: () => { exposures += 1; } },
        ipcRenderer: {},
      };
    }
    return originalLoad.call(this, request, parent, isMain);
  };
  Object.defineProperty(process, 'isMainFrame', { configurable: true, value: false });
  const preload = require.resolve('../preload.cjs');
  delete require.cache[preload];
  require(preload);
  assert.equal(exposures, 0);
  Object.defineProperty(process, 'isMainFrame', { configurable: true, value: true });
  delete require.cache[preload];
  require(preload);
  assert.equal(exposures, 1);
  Object.defineProperty(process, 'isMainFrame', {
    configurable: true,
    value: originalMainFrame,
  });
  Module._load = originalLoad;
});

test('preload translates the desktop return channel into a removable callback', () => {
  const originalLoad = Module._load;
  const originalMainFrame = process.isMainFrame;
  const ipcRenderer = new EventEmitter();
  let bridge;
  Module._load = function(request, parent, isMain) {
    if (request === 'electron') {
      return {
        contextBridge: { exposeInMainWorld: (_name, value) => { bridge = value; } },
        ipcRenderer,
      };
    }
    return originalLoad.call(this, request, parent, isMain);
  };
  Object.defineProperty(process, 'isMainFrame', { configurable: true, value: true });
  const preload = require.resolve('../preload.cjs');
  delete require.cache[preload];
  require(preload);
  let calls = 0;
  const unsubscribe = bridge.onReturnToHost(() => { calls += 1; });
  ipcRenderer.emit('wright:return-to-host', {});
  assert.equal(calls, 1);
  unsubscribe();
  ipcRenderer.emit('wright:return-to-host', {});
  assert.equal(calls, 1);
  Object.defineProperty(process, 'isMainFrame', {
    configurable: true,
    value: originalMainFrame,
  });
  Module._load = originalLoad;
});
