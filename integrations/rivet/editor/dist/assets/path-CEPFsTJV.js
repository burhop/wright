import { F as i } from "./fs-D0wtrpl4.js";
import { a as e } from "./chunk-J2IGCSS2-PBO8fx3x.js";
import { e as W } from "./tauri-C8v6hZOX.js";
function o() {
  return navigator.appVersion.includes("Win");
}
var $ = {};
W($, { BaseDirectory: () => i, appCacheDir: () => s, appConfigDir: () => t, appDataDir: () => u, appDir: () => n, appLocalDataDir: () => c, appLogDir: () => a, audioDir: () => d, basename: () => S, cacheDir: () => h, configDir: () => m, dataDir: () => l, delimiter: () => k, desktopDir: () => p, dirname: () => R, documentDir: () => _, downloadDir: () => y, executableDir: () => D, extname: () => O, fontDir: () => P, homeDir: () => f, isAbsolute: () => T, join: () => F, localDataDir: () => g, logDir: () => L, normalize: () => B, pictureDir: () => v, publicDir: () => M, resolve: () => w, resolveResource: () => x, resourceDir: () => b, runtimeDir: () => j, sep: () => A, templateDir: () => z, videoDir: () => C });
async function n() {
  return t();
}
async function t() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 21 } });
}
async function u() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 22 } });
}
async function c() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 23 } });
}
async function s() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 24 } });
}
async function d() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 1 } });
}
async function h() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 2 } });
}
async function m() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 3 } });
}
async function l() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 4 } });
}
async function p() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 6 } });
}
async function _() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 7 } });
}
async function y() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 8 } });
}
async function D() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 9 } });
}
async function P() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 10 } });
}
async function f() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 11 } });
}
async function g() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 5 } });
}
async function v() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 12 } });
}
async function M() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 13 } });
}
async function b() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 17 } });
}
async function x(r) {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: r, directory: 17 } });
}
async function j() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 14 } });
}
async function z() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 15 } });
}
async function C() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 16 } });
}
async function L() {
  return a();
}
async function a() {
  return e({ __tauriModule: "Path", message: { cmd: "resolvePath", path: "", directory: 25 } });
}
var A = o() ? "\\" : "/", k = o() ? ";" : ":";
async function w(...r) {
  return e({ __tauriModule: "Path", message: { cmd: "resolve", paths: r } });
}
async function B(r) {
  return e({ __tauriModule: "Path", message: { cmd: "normalize", path: r } });
}
async function F(...r) {
  return e({ __tauriModule: "Path", message: { cmd: "join", paths: r } });
}
async function R(r) {
  return e({ __tauriModule: "Path", message: { cmd: "dirname", path: r } });
}
async function O(r) {
  return e({ __tauriModule: "Path", message: { cmd: "extname", path: r } });
}
async function S(r, V) {
  return e({ __tauriModule: "Path", message: { cmd: "basename", path: r, ext: V } });
}
async function T(r) {
  return e({ __tauriModule: "Path", message: { cmd: "isAbsolute", path: r } });
}
const G = Object.freeze(Object.defineProperty({ __proto__: null, BaseDirectory: i, appCacheDir: s, appConfigDir: t, appDataDir: u, appDir: n, appLocalDataDir: c, appLogDir: a, audioDir: d, basename: S, cacheDir: h, configDir: m, dataDir: l, delimiter: k, desktopDir: p, dirname: R, documentDir: _, downloadDir: y, executableDir: D, extname: O, fontDir: P, homeDir: f, isAbsolute: T, join: F, localDataDir: g, logDir: L, normalize: B, pictureDir: v, publicDir: M, resolve: w, resolveResource: x, resourceDir: b, runtimeDir: j, sep: A, templateDir: z, videoDir: C }, Symbol.toStringTag, { value: "Module" }));
export {
  o as n,
  G as p,
  $ as q
};
