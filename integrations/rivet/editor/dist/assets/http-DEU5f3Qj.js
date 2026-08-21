import { a as l } from "./chunk-J2IGCSS2-PBO8fx3x.js";
import { e as d } from "./tauri-C8v6hZOX.js";
var m = {};
d(m, { Body: () => i, Client: () => p, Response: () => y, ResponseType: () => u, fetch: () => f, getClient: () => c });
var u = ((e) => (e[e.JSON = 1] = "JSON", e[e.Text = 2] = "Text", e[e.Binary = 3] = "Binary", e))(u || {});
async function h(e) {
  let r = {}, a = async (s, t) => {
    if (t !== null) {
      let n;
      typeof t == "string" ? n = t : t instanceof Uint8Array || Array.isArray(t) ? n = Array.from(t) : t instanceof File ? n = { file: Array.from(new Uint8Array(await t.arrayBuffer())), mime: t.type, fileName: t.name } : typeof t.file == "string" ? n = { file: t.file, mime: t.mime, fileName: t.fileName } : n = { file: Array.from(t.file), mime: t.mime, fileName: t.fileName }, r[String(s)] = n;
    }
  };
  if (e instanceof FormData) for (let [s, t] of e) await a(s, t);
  else for (let [s, t] of Object.entries(e)) await a(s, t);
  return r;
}
var i = class {
  constructor(e, r) {
    this.type = e, this.payload = r;
  }
  static form(e) {
    return new i("Form", e);
  }
  static json(e) {
    return new i("Json", e);
  }
  static text(e) {
    return new i("Text", e);
  }
  static bytes(e) {
    return new i("Bytes", Array.from(e instanceof ArrayBuffer ? new Uint8Array(e) : e));
  }
}, y = class {
  constructor(e) {
    this.url = e.url, this.status = e.status, this.ok = this.status >= 200 && this.status < 300, this.headers = e.headers, this.rawHeaders = e.rawHeaders, this.data = e.data;
  }
}, p = class {
  constructor(e) {
    this.id = e;
  }
  async drop() {
    return l({ __tauriModule: "Http", message: { cmd: "dropClient", client: this.id } });
  }
  async request(e) {
    var _a;
    let r = !e.responseType || e.responseType === 1;
    return r && (e.responseType = 2), ((_a = e.body) == null ? void 0 : _a.type) === "Form" && (e.body.payload = await h(e.body.payload)), l({ __tauriModule: "Http", message: { cmd: "httpRequest", client: this.id, options: e } }).then((a) => {
      let s = new y(a);
      if (r) {
        try {
          s.data = JSON.parse(s.data);
        } catch (t) {
          if (s.ok && s.data === "") s.data = {};
          else if (s.ok) throw Error(`Failed to parse response \`${s.data}\` as JSON: ${t};
              try setting the \`responseType\` option to \`ResponseType.Text\` or \`ResponseType.Binary\` if the API does not return a JSON response.`);
        }
        return s;
      }
      return s;
    });
  }
  async get(e, r) {
    return this.request({ method: "GET", url: e, ...r });
  }
  async post(e, r, a) {
    return this.request({ method: "POST", url: e, body: r, ...a });
  }
  async put(e, r, a) {
    return this.request({ method: "PUT", url: e, body: r, ...a });
  }
  async patch(e, r) {
    return this.request({ method: "PATCH", url: e, ...r });
  }
  async delete(e, r) {
    return this.request({ method: "DELETE", url: e, ...r });
  }
};
async function c(e) {
  return l({ __tauriModule: "Http", message: { cmd: "createClient", options: e } }).then((r) => new p(r));
}
var o = null;
async function f(e, r) {
  return o === null && (o = await c()), o.request({ url: e, method: (r == null ? void 0 : r.method) ?? "GET", ...r });
}
const g = Object.freeze(Object.defineProperty({ __proto__: null, Body: i, Client: p, Response: y, ResponseType: u, fetch: f, getClient: c }, Symbol.toStringTag, { value: "Module" }));
export {
  m as T,
  g as h
};
