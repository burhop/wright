import { a } from "./chunk-J2IGCSS2-PBO8fx3x.js";
import { e as g } from "./tauri-C8v6hZOX.js";
var c = {};
g(c, { ask: () => l, confirm: () => s, message: () => r, open: () => n, save: () => i });
async function n(e = {}) {
  return typeof e == "object" && Object.freeze(e), a({ __tauriModule: "Dialog", message: { cmd: "openDialog", options: e } });
}
async function i(e = {}) {
  return typeof e == "object" && Object.freeze(e), a({ __tauriModule: "Dialog", message: { cmd: "saveDialog", options: e } });
}
async function r(e, o) {
  var _a, _b;
  let t = typeof o == "string" ? { title: o } : o;
  return a({ __tauriModule: "Dialog", message: { cmd: "messageDialog", message: e.toString(), title: (_a = t == null ? void 0 : t.title) == null ? void 0 : _a.toString(), type: t == null ? void 0 : t.type, buttonLabel: (_b = t == null ? void 0 : t.okLabel) == null ? void 0 : _b.toString() } });
}
async function l(e, o) {
  var _a, _b, _c;
  let t = typeof o == "string" ? { title: o } : o;
  return a({ __tauriModule: "Dialog", message: { cmd: "askDialog", message: e.toString(), title: (_a = t == null ? void 0 : t.title) == null ? void 0 : _a.toString(), type: t == null ? void 0 : t.type, buttonLabels: [((_b = t == null ? void 0 : t.okLabel) == null ? void 0 : _b.toString()) ?? "Yes", ((_c = t == null ? void 0 : t.cancelLabel) == null ? void 0 : _c.toString()) ?? "No"] } });
}
async function s(e, o) {
  var _a, _b, _c;
  let t = typeof o == "string" ? { title: o } : o;
  return a({ __tauriModule: "Dialog", message: { cmd: "confirmDialog", message: e.toString(), title: (_a = t == null ? void 0 : t.title) == null ? void 0 : _a.toString(), type: t == null ? void 0 : t.type, buttonLabels: [((_b = t == null ? void 0 : t.okLabel) == null ? void 0 : _b.toString()) ?? "Ok", ((_c = t == null ? void 0 : t.cancelLabel) == null ? void 0 : _c.toString()) ?? "Cancel"] } });
}
const p = Object.freeze(Object.defineProperty({ __proto__: null, ask: l, confirm: s, message: r, open: n, save: i }, Symbol.toStringTag, { value: "Module" }));
export {
  c,
  p as d
};
