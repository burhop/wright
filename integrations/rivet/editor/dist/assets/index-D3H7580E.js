import { E as m, D as d, _ as f, S as H } from "./window-B44KXyjy.js";
import { W as X } from "./window-B44KXyjy.js";
import { e as o, s as l } from "./tauri-C8v6hZOX.js";
import { u as Z } from "./tauri-C8v6hZOX.js";
import { a as r } from "./chunk-J2IGCSS2-PBO8fx3x.js";
import { n as p } from "./path-CEPFsTJV.js";
import { q as et } from "./path-CEPFsTJV.js";
import { m as at } from "./shell-Djm9-s9j.js";
import { u as ot } from "./app-D5y3fptH.js";
import { c as it } from "./dialog-CkiWQ55D.js";
import { v as ct } from "./fs-D0wtrpl4.js";
import { T as lt } from "./http-DEU5f3Qj.js";
var h = {};
o(h, { exit: () => _, relaunch: () => g });
async function _(t = 0) {
  return r({ __tauriModule: "Process", message: { cmd: "exit", exitCode: t } });
}
async function g() {
  return r({ __tauriModule: "Process", message: { cmd: "relaunch" } });
}
var y = {};
o(y, { checkUpdate: () => $, installUpdate: () => w, onUpdaterEvent: () => c });
async function c(t) {
  return m("tauri://update-status", (e) => {
    t(e == null ? void 0 : e.payload);
  });
}
async function w() {
  let t;
  function e() {
    t && t(), t = void 0;
  }
  return new Promise((s, i) => {
    function u(n) {
      if (n.error) {
        e(), i(n.error);
        return;
      }
      n.status === "DONE" && (e(), s());
    }
    c(u).then((n) => {
      t = n;
    }).catch((n) => {
      throw e(), n;
    }), d("tauri://update-install").catch((n) => {
      throw e(), n;
    });
  });
}
async function $() {
  let t;
  function e() {
    t && t(), t = void 0;
  }
  return new Promise((s, i) => {
    function u(a) {
      e(), s({ manifest: a, shouldUpdate: true });
    }
    function n(a) {
      if (a.error) {
        e(), i(a.error);
        return;
      }
      a.status === "UPTODATE" && (e(), s({ shouldUpdate: false }));
    }
    f("tauri://update-available", (a) => {
      u(a == null ? void 0 : a.payload);
    }).catch((a) => {
      throw e(), a;
    }), c(n).then((a) => {
      t = a;
    }).catch((a) => {
      throw e(), a;
    }), d("tauri://update").catch((a) => {
      throw e(), a;
    });
  });
}
var M = {};
o(M, { isPermissionGranted: () => v, requestPermission: () => x, sendNotification: () => b });
async function v() {
  return window.Notification.permission !== "default" ? Promise.resolve(window.Notification.permission === "granted") : r({ __tauriModule: "Notification", message: { cmd: "isNotificationPermissionGranted" } });
}
async function x() {
  return window.Notification.requestPermission();
}
function b(t) {
  typeof t == "string" ? new window.Notification(t) : new window.Notification(t.title, t);
}
var P = {};
o(P, { EOL: () => N, arch: () => S, locale: () => A, platform: () => O, tempdir: () => U, type: () => G, version: () => T });
var N = p() ? `\r
` : `
`;
async function O() {
  return r({ __tauriModule: "Os", message: { cmd: "platform" } });
}
async function T() {
  return r({ __tauriModule: "Os", message: { cmd: "version" } });
}
async function G() {
  return r({ __tauriModule: "Os", message: { cmd: "osType" } });
}
async function S() {
  return r({ __tauriModule: "Os", message: { cmd: "arch" } });
}
async function U() {
  return r({ __tauriModule: "Os", message: { cmd: "tempdir" } });
}
async function A() {
  return r({ __tauriModule: "Os", message: { cmd: "locale" } });
}
var E = {};
o(E, { getMatches: () => C });
async function C() {
  return r({ __tauriModule: "Cli", message: { cmd: "cliMatches" } });
}
var q = {};
o(q, { readText: () => R, writeText: () => D });
async function D(t) {
  return r({ __tauriModule: "Clipboard", message: { cmd: "writeText", data: t } });
}
async function R() {
  return r({ __tauriModule: "Clipboard", message: { cmd: "readText", data: null } });
}
var k = {};
o(k, { isRegistered: () => j, register: () => L, registerAll: () => W, unregister: () => z, unregisterAll: () => B });
async function L(t, e) {
  return r({ __tauriModule: "GlobalShortcut", message: { cmd: "register", shortcut: t, handler: l(e) } });
}
async function W(t, e) {
  return r({ __tauriModule: "GlobalShortcut", message: { cmd: "registerAll", shortcuts: t, handler: l(e) } });
}
async function j(t) {
  return r({ __tauriModule: "GlobalShortcut", message: { cmd: "isRegistered", shortcut: t } });
}
async function z(t) {
  return r({ __tauriModule: "GlobalShortcut", message: { cmd: "unregister", shortcut: t } });
}
async function B() {
  return r({ __tauriModule: "GlobalShortcut", message: { cmd: "unregisterAll" } });
}
export {
  ot as app,
  E as cli,
  q as clipboard,
  it as dialog,
  X as event,
  ct as fs,
  k as globalShortcut,
  lt as http,
  M as notification,
  P as os,
  et as path,
  h as process,
  at as shell,
  Z as tauri,
  y as updater,
  H as window
};
