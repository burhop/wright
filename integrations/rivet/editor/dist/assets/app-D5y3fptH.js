import { a as e } from "./chunk-J2IGCSS2-PBO8fx3x.js";
import { e as i } from "./tauri-C8v6hZOX.js";
var s = {};
i(s, { getName: () => t, getTauriVersion: () => o, getVersion: () => r, hide: () => a, show: () => n });
async function r() {
  return e({ __tauriModule: "App", message: { cmd: "getAppVersion" } });
}
async function t() {
  return e({ __tauriModule: "App", message: { cmd: "getAppName" } });
}
async function o() {
  return e({ __tauriModule: "App", message: { cmd: "getTauriVersion" } });
}
async function n() {
  return e({ __tauriModule: "App", message: { cmd: "show" } });
}
async function a() {
  return e({ __tauriModule: "App", message: { cmd: "hide" } });
}
const c = Object.freeze(Object.defineProperty({ __proto__: null, getName: t, getTauriVersion: o, getVersion: r, hide: a, show: n }, Symbol.toStringTag, { value: "Module" }));
export {
  c as a,
  s as u
};
