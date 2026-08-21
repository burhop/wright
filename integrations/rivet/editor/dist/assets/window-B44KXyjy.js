import { a as t } from "./chunk-J2IGCSS2-PBO8fx3x.js";
import { s as L, e as W } from "./tauri-C8v6hZOX.js";
var S = {};
W(S, { TauriEvent: () => E, emit: () => x, listen: () => I, once: () => O });
async function M(e, a) {
  return t({ __tauriModule: "Event", message: { cmd: "unlisten", event: e, eventId: a } });
}
async function f(e, a, i) {
  await t({ __tauriModule: "Event", message: { cmd: "emit", event: e, windowLabel: a, payload: i } });
}
async function c(e, a, i) {
  return t({ __tauriModule: "Event", message: { cmd: "listen", event: e, windowLabel: a, handler: L(i) } }).then((n) => async () => M(e, n));
}
async function z(e, a, i) {
  return c(e, a, (n) => {
    i(n), M(e, n.id).catch(() => {
    });
  });
}
var E = ((e) => (e.WINDOW_RESIZED = "tauri://resize", e.WINDOW_MOVED = "tauri://move", e.WINDOW_CLOSE_REQUESTED = "tauri://close-requested", e.WINDOW_CREATED = "tauri://window-created", e.WINDOW_DESTROYED = "tauri://destroyed", e.WINDOW_FOCUS = "tauri://focus", e.WINDOW_BLUR = "tauri://blur", e.WINDOW_SCALE_FACTOR_CHANGED = "tauri://scale-change", e.WINDOW_THEME_CHANGED = "tauri://theme-changed", e.WINDOW_FILE_DROP = "tauri://file-drop", e.WINDOW_FILE_DROP_HOVER = "tauri://file-drop-hover", e.WINDOW_FILE_DROP_CANCELLED = "tauri://file-drop-cancelled", e.MENU = "tauri://menu", e.CHECK_UPDATE = "tauri://update", e.UPDATE_AVAILABLE = "tauri://update-available", e.INSTALL_UPDATE = "tauri://update-install", e.STATUS_UPDATE = "tauri://update-status", e.DOWNLOAD_PROGRESS = "tauri://update-download-progress", e))(E || {});
async function I(e, a) {
  return c(e, null, a);
}
async function O(e, a) {
  return z(e, null, a);
}
async function x(e, a) {
  return f(e, void 0, a);
}
var R = {};
W(R, { CloseRequestedEvent: () => p, LogicalPosition: () => y, LogicalSize: () => m, PhysicalPosition: () => o, PhysicalSize: () => r, UserAttentionType: () => h, WebviewWindow: () => l, WebviewWindowHandle: () => _, WindowManager: () => g, appWindow: () => u, availableMonitors: () => C, currentMonitor: () => A, getAll: () => d, getCurrent: () => v, primaryMonitor: () => T });
var m = class {
  constructor(e, a) {
    this.type = "Logical", this.width = e, this.height = a;
  }
}, r = class {
  constructor(e, a) {
    this.type = "Physical", this.width = e, this.height = a;
  }
  toLogical(e) {
    return new m(this.width / e, this.height / e);
  }
}, y = class {
  constructor(e, a) {
    this.type = "Logical", this.x = e, this.y = a;
  }
}, o = class {
  constructor(e, a) {
    this.type = "Physical", this.x = e, this.y = a;
  }
  toLogical(e) {
    return new y(this.x / e, this.y / e);
  }
}, h = ((e) => (e[e.Critical = 1] = "Critical", e[e.Informational = 2] = "Informational", e))(h || {});
function v() {
  return new l(window.__TAURI_METADATA__.__currentWindow.label, { skip: true });
}
function d() {
  return window.__TAURI_METADATA__.__windows.map((e) => new l(e.label, { skip: true }));
}
var w = ["tauri://created", "tauri://error"], _ = class {
  constructor(e) {
    this.label = e, this.listeners = /* @__PURE__ */ Object.create(null);
  }
  async listen(e, a) {
    return this._handleTauriEvent(e, a) ? Promise.resolve(() => {
      let i = this.listeners[e];
      i.splice(i.indexOf(a), 1);
    }) : c(e, this.label, a);
  }
  async once(e, a) {
    return this._handleTauriEvent(e, a) ? Promise.resolve(() => {
      let i = this.listeners[e];
      i.splice(i.indexOf(a), 1);
    }) : z(e, this.label, a);
  }
  async emit(e, a) {
    if (w.includes(e)) {
      for (let i of this.listeners[e] || []) i({ event: e, id: -1, windowLabel: this.label, payload: a });
      return Promise.resolve();
    }
    return f(e, this.label, a);
  }
  _handleTauriEvent(e, a) {
    return w.includes(e) ? (e in this.listeners ? this.listeners[e].push(a) : this.listeners[e] = [a], true) : false;
  }
}, g = class extends _ {
  async scaleFactor() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "scaleFactor" } } } });
  }
  async innerPosition() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "innerPosition" } } } }).then(({ x: e, y: a }) => new o(e, a));
  }
  async outerPosition() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "outerPosition" } } } }).then(({ x: e, y: a }) => new o(e, a));
  }
  async innerSize() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "innerSize" } } } }).then(({ width: e, height: a }) => new r(e, a));
  }
  async outerSize() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "outerSize" } } } }).then(({ width: e, height: a }) => new r(e, a));
  }
  async isFullscreen() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "isFullscreen" } } } });
  }
  async isMinimized() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "isMinimized" } } } });
  }
  async isMaximized() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "isMaximized" } } } });
  }
  async isFocused() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "isFocused" } } } });
  }
  async isDecorated() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "isDecorated" } } } });
  }
  async isResizable() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "isResizable" } } } });
  }
  async isMaximizable() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "isMaximizable" } } } });
  }
  async isMinimizable() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "isMinimizable" } } } });
  }
  async isClosable() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "isClosable" } } } });
  }
  async isVisible() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "isVisible" } } } });
  }
  async title() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "title" } } } });
  }
  async theme() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "theme" } } } });
  }
  async center() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "center" } } } });
  }
  async requestUserAttention(e) {
    let a = null;
    return e && (e === 1 ? a = { type: "Critical" } : a = { type: "Informational" }), t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "requestUserAttention", payload: a } } } });
  }
  async setResizable(e) {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setResizable", payload: e } } } });
  }
  async setMaximizable(e) {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setMaximizable", payload: e } } } });
  }
  async setMinimizable(e) {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setMinimizable", payload: e } } } });
  }
  async setClosable(e) {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setClosable", payload: e } } } });
  }
  async setTitle(e) {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setTitle", payload: e } } } });
  }
  async maximize() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "maximize" } } } });
  }
  async unmaximize() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "unmaximize" } } } });
  }
  async toggleMaximize() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "toggleMaximize" } } } });
  }
  async minimize() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "minimize" } } } });
  }
  async unminimize() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "unminimize" } } } });
  }
  async show() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "show" } } } });
  }
  async hide() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "hide" } } } });
  }
  async close() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "close" } } } });
  }
  async setDecorations(e) {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setDecorations", payload: e } } } });
  }
  async setAlwaysOnTop(e) {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setAlwaysOnTop", payload: e } } } });
  }
  async setContentProtected(e) {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setContentProtected", payload: e } } } });
  }
  async setSize(e) {
    if (!e || e.type !== "Logical" && e.type !== "Physical") throw new Error("the `size` argument must be either a LogicalSize or a PhysicalSize instance");
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setSize", payload: { type: e.type, data: { width: e.width, height: e.height } } } } } });
  }
  async setMinSize(e) {
    if (e && e.type !== "Logical" && e.type !== "Physical") throw new Error("the `size` argument must be either a LogicalSize or a PhysicalSize instance");
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setMinSize", payload: e ? { type: e.type, data: { width: e.width, height: e.height } } : null } } } });
  }
  async setMaxSize(e) {
    if (e && e.type !== "Logical" && e.type !== "Physical") throw new Error("the `size` argument must be either a LogicalSize or a PhysicalSize instance");
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setMaxSize", payload: e ? { type: e.type, data: { width: e.width, height: e.height } } : null } } } });
  }
  async setPosition(e) {
    if (!e || e.type !== "Logical" && e.type !== "Physical") throw new Error("the `position` argument must be either a LogicalPosition or a PhysicalPosition instance");
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setPosition", payload: { type: e.type, data: { x: e.x, y: e.y } } } } } });
  }
  async setFullscreen(e) {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setFullscreen", payload: e } } } });
  }
  async setFocus() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setFocus" } } } });
  }
  async setIcon(e) {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setIcon", payload: { icon: typeof e == "string" ? e : Array.from(e) } } } } });
  }
  async setSkipTaskbar(e) {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setSkipTaskbar", payload: e } } } });
  }
  async setCursorGrab(e) {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setCursorGrab", payload: e } } } });
  }
  async setCursorVisible(e) {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setCursorVisible", payload: e } } } });
  }
  async setCursorIcon(e) {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setCursorIcon", payload: e } } } });
  }
  async setCursorPosition(e) {
    if (!e || e.type !== "Logical" && e.type !== "Physical") throw new Error("the `position` argument must be either a LogicalPosition or a PhysicalPosition instance");
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setCursorPosition", payload: { type: e.type, data: { x: e.x, y: e.y } } } } } });
  }
  async setIgnoreCursorEvents(e) {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "setIgnoreCursorEvents", payload: e } } } });
  }
  async startDragging() {
    return t({ __tauriModule: "Window", message: { cmd: "manage", data: { label: this.label, cmd: { type: "startDragging" } } } });
  }
  async onResized(e) {
    return this.listen("tauri://resize", (a) => {
      a.payload = P(a.payload), e(a);
    });
  }
  async onMoved(e) {
    return this.listen("tauri://move", (a) => {
      a.payload = D(a.payload), e(a);
    });
  }
  async onCloseRequested(e) {
    return this.listen("tauri://close-requested", (a) => {
      let i = new p(a);
      Promise.resolve(e(i)).then(() => {
        if (!i.isPreventDefault()) return this.close();
      });
    });
  }
  async onFocusChanged(e) {
    let a = await this.listen("tauri://focus", (n) => {
      e({ ...n, payload: true });
    }), i = await this.listen("tauri://blur", (n) => {
      e({ ...n, payload: false });
    });
    return () => {
      a(), i();
    };
  }
  async onScaleChanged(e) {
    return this.listen("tauri://scale-change", e);
  }
  async onMenuClicked(e) {
    return this.listen("tauri://menu", e);
  }
  async onFileDropEvent(e) {
    let a = await this.listen("tauri://file-drop", (s) => {
      e({ ...s, payload: { type: "drop", paths: s.payload } });
    }), i = await this.listen("tauri://file-drop-hover", (s) => {
      e({ ...s, payload: { type: "hover", paths: s.payload } });
    }), n = await this.listen("tauri://file-drop-cancelled", (s) => {
      e({ ...s, payload: { type: "cancel" } });
    });
    return () => {
      a(), i(), n();
    };
  }
  async onThemeChanged(e) {
    return this.listen("tauri://theme-changed", e);
  }
}, p = class {
  constructor(e) {
    this._preventDefault = false, this.event = e.event, this.windowLabel = e.windowLabel, this.id = e.id;
  }
  preventDefault() {
    this._preventDefault = true;
  }
  isPreventDefault() {
    return this._preventDefault;
  }
}, l = class extends g {
  constructor(e, a = {}) {
    super(e), (a == null ? void 0 : a.skip) || t({ __tauriModule: "Window", message: { cmd: "createWebview", data: { options: { label: e, ...a } } } }).then(async () => this.emit("tauri://created")).catch(async (i) => this.emit("tauri://error", i));
  }
  static getByLabel(e) {
    return d().some((a) => a.label === e) ? new l(e, { skip: true }) : null;
  }
  static async getFocusedWindow() {
    for (let e of d()) if (await e.isFocused()) return e;
    return null;
  }
}, u;
"__TAURI_METADATA__" in window ? u = new l(window.__TAURI_METADATA__.__currentWindow.label, { skip: true }) : (console.warn(`Could not find "window.__TAURI_METADATA__". The "appWindow" value will reference the "main" window label.
Note that this is not an issue if running this frontend on a browser instead of a Tauri window.`), u = new l("main", { skip: true }));
function b(e) {
  return e === null ? null : { name: e.name, scaleFactor: e.scaleFactor, position: D(e.position), size: P(e.size) };
}
function D(e) {
  return new o(e.x, e.y);
}
function P(e) {
  return new r(e.width, e.height);
}
async function A() {
  return t({ __tauriModule: "Window", message: { cmd: "manage", data: { cmd: { type: "currentMonitor" } } } }).then(b);
}
async function T() {
  return t({ __tauriModule: "Window", message: { cmd: "manage", data: { cmd: { type: "primaryMonitor" } } } }).then(b);
}
async function C() {
  return t({ __tauriModule: "Window", message: { cmd: "manage", data: { cmd: { type: "availableMonitors" } } } }).then((e) => e.map(b));
}
const U = Object.freeze(Object.defineProperty({ __proto__: null, CloseRequestedEvent: p, LogicalPosition: y, LogicalSize: m, PhysicalPosition: o, PhysicalSize: r, UserAttentionType: h, WebviewWindow: l, WebviewWindowHandle: _, WindowManager: g, get appWindow() {
  return u;
}, availableMonitors: C, currentMonitor: A, getAll: d, getCurrent: v, primaryMonitor: T }, Symbol.toStringTag, { value: "Module" }));
export {
  x as D,
  I as E,
  R as S,
  S as W,
  O as _,
  U as w
};
