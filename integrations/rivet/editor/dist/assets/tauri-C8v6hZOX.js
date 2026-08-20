var d = Object.defineProperty, f = (r, e) => {
  for (var t in e) d(r, t, { get: e[t], enumerable: true });
}, w = {};
f(w, { convertFileSrc: () => u, invoke: () => i, transformCallback: () => l });
function _() {
  return window.crypto.getRandomValues(new Uint32Array(1))[0];
}
function l(r, e = false) {
  let t = _(), n = `_${t}`;
  return Object.defineProperty(window, n, { value: (o) => (e && Reflect.deleteProperty(window, n), r == null ? void 0 : r(o)), writable: false, configurable: true }), t;
}
async function i(r, e = {}) {
  return new Promise((t, n) => {
    let o = l((c) => {
      t(c), Reflect.deleteProperty(window, `_${a}`);
    }, true), a = l((c) => {
      n(c), Reflect.deleteProperty(window, `_${o}`);
    }, true);
    window.__TAURI_IPC__({ cmd: r, callback: o, error: a, ...e });
  });
}
function u(r, e = "asset") {
  return window.__TAURI__.convertFileSrc(r, e);
}
const s = Object.freeze(Object.defineProperty({ __proto__: null, convertFileSrc: u, invoke: i, transformCallback: l }, Symbol.toStringTag, { value: "Module" }));
export {
  i as _,
  f as e,
  l as s,
  s as t,
  w as u
};
