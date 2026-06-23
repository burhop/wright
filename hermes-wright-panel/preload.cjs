const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('wrightDesktop', {
  api: (request) => ipcRenderer.invoke('wright:api', request),
  readFile: (path) => ipcRenderer.invoke('wright:readFile', path),
  writeFile: (path, content) => ipcRenderer.invoke('wright:writeFile', { path, content }),
  listDirectory: (path) => ipcRenderer.invoke('wright:listDirectory', path),
  selectFiles: (options) => ipcRenderer.invoke('wright:selectFiles', options),
  notify: (payload) => ipcRenderer.invoke('wright:notify', payload),
  getConfig: () => ipcRenderer.invoke('wright:getConfig'),
  onThemeChange: (callback) => {
    const subscription = (_event, payload) => callback(payload);
    ipcRenderer.on('wright:theme-changed', subscription);
    return () => {
      ipcRenderer.removeListener('wright:theme-changed', subscription);
    };
  },
  terminal: {
    start: (options) => ipcRenderer.invoke('wright:terminal:start', options),
    write: (id, data) => ipcRenderer.invoke('wright:terminal:write', { id, data }),
    resize: (id, size) => ipcRenderer.invoke('wright:terminal:resize', { id, ...size }),
    dispose: (id) => ipcRenderer.invoke('wright:terminal:dispose', id),
    onData: (id, callback) => {
      const channel = `wright:terminal:data:${id}`;
      const subscription = (_event, data) => callback(data);
      ipcRenderer.on(channel, subscription);
      return () => {
        ipcRenderer.removeListener(channel, subscription);
      };
    },
    onExit: (id, callback) => {
      const channel = `wright:terminal:exit:${id}`;
      const subscription = (_event, payload) => callback(payload);
      ipcRenderer.on(channel, subscription);
      return () => {
        ipcRenderer.removeListener(channel, subscription);
      };
    }
  }
});
