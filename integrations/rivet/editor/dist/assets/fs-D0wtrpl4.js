import { a } from "./chunk-J2IGCSS2-PBO8fx3x.js";
import { e as _ } from "./tauri-C8v6hZOX.js";
var g = {};
_(g, { BaseDirectory: () => c, Dir: () => c, copyFile: () => f, createDir: () => m, exists: () => D, readBinaryFile: () => n, readDir: () => l, readTextFile: () => p, removeDir: () => d, removeFile: () => F, renameFile: () => y, writeBinaryFile: () => u, writeFile: () => s, writeTextFile: () => s });
var c = ((e) => (e[e.Audio = 1] = "Audio", e[e.Cache = 2] = "Cache", e[e.Config = 3] = "Config", e[e.Data = 4] = "Data", e[e.LocalData = 5] = "LocalData", e[e.Desktop = 6] = "Desktop", e[e.Document = 7] = "Document", e[e.Download = 8] = "Download", e[e.Executable = 9] = "Executable", e[e.Font = 10] = "Font", e[e.Home = 11] = "Home", e[e.Picture = 12] = "Picture", e[e.Public = 13] = "Public", e[e.Runtime = 14] = "Runtime", e[e.Template = 15] = "Template", e[e.Video = 16] = "Video", e[e.Resource = 17] = "Resource", e[e.App = 18] = "App", e[e.Log = 19] = "Log", e[e.Temp = 20] = "Temp", e[e.AppConfig = 21] = "AppConfig", e[e.AppData = 22] = "AppData", e[e.AppLocalData = 23] = "AppLocalData", e[e.AppCache = 24] = "AppCache", e[e.AppLog = 25] = "AppLog", e))(c || {});
async function p(e, t = {}) {
  return a({ __tauriModule: "Fs", message: { cmd: "readTextFile", path: e, options: t } });
}
async function n(e, t = {}) {
  let r = await a({ __tauriModule: "Fs", message: { cmd: "readFile", path: e, options: t } });
  return Uint8Array.from(r);
}
async function s(e, t, r) {
  typeof r == "object" && Object.freeze(r), typeof e == "object" && Object.freeze(e);
  let o = { path: "", contents: "" }, i = r;
  return typeof e == "string" ? o.path = e : (o.path = e.path, o.contents = e.contents), typeof t == "string" ? o.contents = t ?? "" : i = t, a({ __tauriModule: "Fs", message: { cmd: "writeFile", path: o.path, contents: Array.from(new TextEncoder().encode(o.contents)), options: i } });
}
async function u(e, t, r) {
  typeof r == "object" && Object.freeze(r), typeof e == "object" && Object.freeze(e);
  let o = { path: "", contents: [] }, i = r;
  return typeof e == "string" ? o.path = e : (o.path = e.path, o.contents = e.contents), t && "dir" in t ? i = t : typeof e == "string" && (o.contents = t ?? []), a({ __tauriModule: "Fs", message: { cmd: "writeFile", path: o.path, contents: Array.from(o.contents instanceof ArrayBuffer ? new Uint8Array(o.contents) : o.contents), options: i } });
}
async function l(e, t = {}) {
  return a({ __tauriModule: "Fs", message: { cmd: "readDir", path: e, options: t } });
}
async function m(e, t = {}) {
  return a({ __tauriModule: "Fs", message: { cmd: "createDir", path: e, options: t } });
}
async function d(e, t = {}) {
  return a({ __tauriModule: "Fs", message: { cmd: "removeDir", path: e, options: t } });
}
async function f(e, t, r = {}) {
  return a({ __tauriModule: "Fs", message: { cmd: "copyFile", source: e, destination: t, options: r } });
}
async function F(e, t = {}) {
  return a({ __tauriModule: "Fs", message: { cmd: "removeFile", path: e, options: t } });
}
async function y(e, t, r = {}) {
  return a({ __tauriModule: "Fs", message: { cmd: "renameFile", oldPath: e, newPath: t, options: r } });
}
async function D(e, t = {}) {
  return a({ __tauriModule: "Fs", message: { cmd: "exists", path: e, options: t } });
}
const b = Object.freeze(Object.defineProperty({ __proto__: null, BaseDirectory: c, Dir: c, copyFile: f, createDir: m, exists: D, readBinaryFile: n, readDir: l, readTextFile: p, removeDir: d, removeFile: F, renameFile: y, writeBinaryFile: u, writeFile: s, writeTextFile: s }, Symbol.toStringTag, { value: "Module" }));
export {
  c as F,
  b as f,
  g as v
};
