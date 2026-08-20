const d = /* @__PURE__ */ new Map(), r = /* @__PURE__ */ new Map();
function l(e) {
  return encodeURIComponent((e == null ? void 0 : e.trim()) || "none");
}
function a(e) {
  return `project:${l(e)}|`;
}
function f(e) {
  return `inmemory://rivet/node-editor/${encodeURIComponent(e)}`;
}
function C(e) {
  const { cacheKey: t, text: o, createModel: i, getExistingModel: c } = e;
  if (!t) return { model: i(), isCached: false };
  const n = d.get(t);
  if (n) return d.delete(t), d.set(t, n), n.lastInputText !== o && n.model.getValue() !== o && (n.model.setValue(o), r.delete(t)), n.lastInputText = o, { model: n.model, isCached: true };
  const s = (c == null ? void 0 : c()) ?? i();
  return d.set(t, { model: s, lastInputText: o }), u(), { model: s, isCached: true };
}
function E(e) {
  const t = a(e);
  for (const [o, i] of d) o.startsWith(t) && (i.model.dispose(), d.delete(o));
  for (const o of r.keys()) o.startsWith(t) && r.delete(o);
}
function m(e) {
  return e ? r.get(e) : void 0;
}
function M(e, t) {
  e && (t ? r.set(e, t) : r.delete(e));
}
function u() {
  var _a;
  for (; d.size > 12; ) {
    const e = d.keys().next().value;
    if (!e) return;
    (_a = d.get(e)) == null ? void 0 : _a.model.dispose(), d.delete(e), r.delete(e);
  }
}
export {
  E as clearCodeEditorModelCacheForProject,
  f as getCodeEditorModelUri,
  m as getCodeEditorViewState,
  C as getOrCreateCodeEditorModel,
  M as saveCodeEditorViewState
};
