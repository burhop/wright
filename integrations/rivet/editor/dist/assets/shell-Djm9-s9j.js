import { a as o } from "./chunk-J2IGCSS2-PBO8fx3x.js";
import { s as d, e as u } from "./tauri-C8v6hZOX.js";
var c = {};
u(c, { Child: () => a, Command: () => h, EventEmitter: () => i, open: () => l });
async function p(e, t, s = [], r) {
  return typeof s == "object" && Object.freeze(s), o({ __tauriModule: "Shell", message: { cmd: "execute", program: t, args: s, options: r, onEventFn: d(e) } });
}
var i = class {
  constructor() {
    this.eventListeners = /* @__PURE__ */ Object.create(null);
  }
  addListener(e, t) {
    return this.on(e, t);
  }
  removeListener(e, t) {
    return this.off(e, t);
  }
  on(e, t) {
    return e in this.eventListeners ? this.eventListeners[e].push(t) : this.eventListeners[e] = [t], this;
  }
  once(e, t) {
    let s = (...r) => {
      this.removeListener(e, s), t(...r);
    };
    return this.addListener(e, s);
  }
  off(e, t) {
    return e in this.eventListeners && (this.eventListeners[e] = this.eventListeners[e].filter((s) => s !== t)), this;
  }
  removeAllListeners(e) {
    return e ? delete this.eventListeners[e] : this.eventListeners = /* @__PURE__ */ Object.create(null), this;
  }
  emit(e, ...t) {
    if (e in this.eventListeners) {
      let s = this.eventListeners[e];
      for (let r of s) r(...t);
      return true;
    }
    return false;
  }
  listenerCount(e) {
    return e in this.eventListeners ? this.eventListeners[e].length : 0;
  }
  prependListener(e, t) {
    return e in this.eventListeners ? this.eventListeners[e].unshift(t) : this.eventListeners[e] = [t], this;
  }
  prependOnceListener(e, t) {
    let s = (...r) => {
      this.removeListener(e, s), t(...r);
    };
    return this.prependListener(e, s);
  }
}, a = class {
  constructor(e) {
    this.pid = e;
  }
  async write(e) {
    return o({ __tauriModule: "Shell", message: { cmd: "stdinWrite", pid: this.pid, buffer: typeof e == "string" ? e : Array.from(e) } });
  }
  async kill() {
    return o({ __tauriModule: "Shell", message: { cmd: "killChild", pid: this.pid } });
  }
}, h = class extends i {
  constructor(e, t = [], s) {
    super(), this.stdout = new i(), this.stderr = new i(), this.program = e, this.args = typeof t == "string" ? [t] : t, this.options = s ?? {};
  }
  static sidecar(e, t = [], s) {
    let r = new h(e, t, s);
    return r.options.sidecar = true, r;
  }
  async spawn() {
    return p((e) => {
      switch (e.event) {
        case "Error":
          this.emit("error", e.payload);
          break;
        case "Terminated":
          this.emit("close", e.payload);
          break;
        case "Stdout":
          this.stdout.emit("data", e.payload);
          break;
        case "Stderr":
          this.stderr.emit("data", e.payload);
          break;
      }
    }, this.program, this.args, this.options).then((e) => new a(e));
  }
  async execute() {
    return new Promise((e, t) => {
      this.on("error", t);
      let s = [], r = [];
      this.stdout.on("data", (n) => {
        s.push(n);
      }), this.stderr.on("data", (n) => {
        r.push(n);
      }), this.on("close", (n) => {
        e({ code: n.code, signal: n.signal, stdout: s.join(`
`), stderr: r.join(`
`) });
      }), this.spawn().catch(t);
    });
  }
};
async function l(e, t) {
  return o({ __tauriModule: "Shell", message: { cmd: "open", path: e, with: t } });
}
const L = Object.freeze(Object.defineProperty({ __proto__: null, Child: a, Command: h, EventEmitter: i, open: l }, Symbol.toStringTag, { value: "Module" }));
export {
  c as m,
  L as s
};
