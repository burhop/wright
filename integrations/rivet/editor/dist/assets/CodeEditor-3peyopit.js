var __defProp = Object.defineProperty;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __publicField = (obj, key, value) => __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);
import { e as f, R as P, y as M, z as X, A as ge, B as me, M as he, r as d, D as U, U as ve, j as Ee } from "./vendor-CRPgzvoS.js";
import { g as re, i as ke, M as Me, a as Se, J as Z, v as ye, b as Oe, c as Ne, s as Te, d as Ae, S as Q, e as $ } from "./index-DP_wohYo.js";
import { getCodeEditorModelUri as Re, getOrCreateCodeEditorModel as Ce, getCodeEditorViewState as Le, saveCodeEditorViewState as be } from "./codeEditorModelCache-0CJKNP2F.js";
const ie = { ":": "colon", ",": "comma", "{": "leftBrace", "}": "rightBrace", "[": "leftBracket", "]": "rightBracket" };
function se(e, t) {
  const n = Ie(e), o = [];
  for (const r of n) K(r, o);
  return o.find((r) => t >= r.requiredStringStart && t <= r.requiredStringEnd);
}
function Ie(e) {
  const t = new je(_e(e)), n = [];
  for (; !t.isAtEnd(); ) {
    const o = t.parseValue();
    o ? n.push(o) : t.advance();
  }
  return n;
}
function _e(e) {
  const t = [], n = re(e);
  let o = 0, r = 0;
  for (; r < e.length; ) {
    const i = Pe(n, o, r);
    if (i) {
      t.push({ type: "interpolation", start: i.start, end: i.end }), r = i.end, o += 1;
      continue;
    }
    const a = e[r];
    if (/\s/.test(a)) {
      r += 1;
      continue;
    }
    if (a === '"') {
      const g = we(e, r);
      t.push(g), r = g.end;
      continue;
    }
    const m = ie[a];
    if (m) {
      t.push({ type: m, start: r, end: r + 1 }), r += 1;
      continue;
    }
    const h = De(e, r);
    t.push(h), r = h.end;
  }
  return t;
}
function Pe(e, t, n) {
  for (let o = t; o < e.length; o += 1) {
    const r = e[o];
    if (n < r.start) return;
    if (n >= r.start && n < r.end) return r;
  }
}
function we(e, t) {
  let n = t + 1;
  for (; n < e.length; ) {
    const o = e[n];
    if (o === "\\") {
      n += 2;
      continue;
    }
    if (o === '"') {
      const r = n + 1;
      return { type: "string", decoded: Ve(e.slice(t, r)), start: t, end: r };
    }
    n += 1;
  }
  return { type: "string", decoded: void 0, start: t, end: e.length };
}
function De(e, t) {
  let n = t + 1;
  for (; n < e.length; ) {
    const o = e[n];
    if (o === '"' || /\s/.test(o) || ie[o]) break;
    n += 1;
  }
  return { type: "other", start: t, end: n };
}
function Ve(e) {
  try {
    const t = JSON.parse(e);
    return typeof t == "string" ? t : void 0;
  } catch {
    return;
  }
}
class je {
  constructor(t) {
    __publicField(this, "index", 0);
    this.tokens = t;
  }
  isAtEnd() {
    return this.index >= this.tokens.length;
  }
  advance() {
    const t = this.peek();
    return t && (this.index += 1), t;
  }
  parseValue() {
    const t = this.peek();
    if (t) {
      if (t.type === "leftBrace") return this.parseObject();
      if (t.type === "leftBracket") return this.parseArray();
      if (t.type === "string") return this.advance(), { type: "string", start: t.start, end: t.end, token: t };
      if (!(t.type === "rightBrace" || t.type === "rightBracket" || t.type === "comma" || t.type === "colon")) return this.advance(), { type: "other", start: t.start, end: t.end };
    }
  }
  parseObject() {
    const t = this.advance(), n = [];
    let o = t.end;
    for (; !this.isAtEnd(); ) {
      const r = this.peek();
      if (!r) break;
      if (r.type === "rightBrace") {
        o = this.advance().end;
        break;
      }
      if (r.type !== "string") {
        this.skipToNextObjectEntry();
        continue;
      }
      const i = this.advance();
      if (!this.consume("colon")) {
        this.skipToNextObjectEntry();
        continue;
      }
      const a = this.parseValue() ?? { type: "other", start: i.end, end: i.end };
      n.push({ key: i, value: a }), o = a.end, this.consume("comma");
    }
    return { type: "object", properties: n, start: t.start, end: o };
  }
  parseArray() {
    const t = this.advance(), n = [];
    let o = t.end;
    for (; !this.isAtEnd(); ) {
      const r = this.peek();
      if (!r) break;
      if (r.type === "rightBracket") {
        o = this.advance().end;
        break;
      }
      const i = this.parseValue();
      i ? (n.push(i), o = i.end) : this.advance(), this.consume("comma");
    }
    return { type: "array", elements: n, start: t.start, end: o };
  }
  consume(t) {
    var _a;
    return ((_a = this.peek()) == null ? void 0 : _a.type) !== t ? false : (this.advance(), true);
  }
  peek() {
    return this.tokens[this.index];
  }
  skipToNextObjectEntry() {
    for (; !this.isAtEnd(); ) {
      const t = this.peek();
      if ((t == null ? void 0 : t.type) === "comma") {
        this.advance();
        return;
      }
      if ((t == null ? void 0 : t.type) === "rightBrace") return;
      this.advance();
    }
  }
}
function K(e, t) {
  if (e.type === "array") {
    for (const n of e.elements) K(n, t);
    return;
  }
  if (e.type === "object") {
    Je(e, t);
    for (const n of e.properties) K(n.value, t);
  }
}
function Je(e, t) {
  const n = x(e, "required"), o = x(e, "properties");
  if (!((n == null ? void 0 : n.value.type) !== "array" || (o == null ? void 0 : o.value.type) !== "object")) for (const r of n.value.elements) {
    if (r.type !== "string" || r.token.decoded == null) continue;
    const i = x(o.value, r.token.decoded);
    i && t.push({ requiredStringStart: r.token.start, requiredStringEnd: r.token.end, targetKeyStart: i.key.start, targetKeyEnd: i.key.end });
  }
}
function x(e, t) {
  return e.properties.find((n) => n.key.decoded === t);
}
const Ue = { brackets: [["{", "}"]], autoClosingPairs: [{ open: "{", close: "}" }], surroundingPairs: [{ open: "{", close: "}" }] }, xe = { molten: { foreground: "ff9900", base: "vs-dark" }, grapefruit: { foreground: "ff8862", base: "vs-dark" }, taffy: { foreground: "d6c2ff", base: "vs-dark" }, bright: { foreground: "1769e0", base: "vs" }, custom: { foreground: "ff9900", base: "vs-dark" } };
function ae(e) {
  return M.getLanguages().some((t) => t.id === e);
}
function Ke() {
  ae("prompt-interpolation") || (M.register({ id: "prompt-interpolation" }), M.setMonarchTokensProvider("prompt-interpolation", { tokenizer: { root: [[/\{\{[^}]+\}\}/, "prompt-replacement"]] } }), M.setLanguageConfiguration("prompt-interpolation", Ue));
}
function qe() {
  if (ae("prompt-interpolation-markdown")) return;
  const e = X(ge), t = X(me);
  t.tokenizer.root.unshift([/\{\{[^{}]+\}\}/, "prompt-replacement"]), M.register({ id: "prompt-interpolation-markdown" }), M.setMonarchTokensProvider("prompt-interpolation-markdown", t), M.setLanguageConfiguration("prompt-interpolation-markdown", e);
}
function Be() {
  for (const [e, { base: t, foreground: n }] of Object.entries(xe)) f.defineTheme(`prompt-interpolation-${e}`, { base: t, inherit: true, rules: [{ token: "prompt-replacement", foreground: n }], colors: {} });
}
let ee = false, te = false;
function Fe() {
  if (!ee) {
    ee = true;
    for (const e of Me) M.registerFoldingRangeProvider(e, { provideFoldingRanges(t) {
      return Se(t.getValue()).map(({ start: n, end: o }) => ({ start: n, end: o, kind: M.FoldingRangeKind.Region }));
    } });
  }
}
function q(e, t, n) {
  const o = e.getPositionAt(t), r = e.getPositionAt(n);
  return new P(o.lineNumber, o.column, r.lineNumber, r.column);
}
function Ge() {
  te || (te = true, M.registerDefinitionProvider("json", { provideDefinition(e, t) {
    const n = se(e.getValue(), e.getOffsetAt(t));
    if (!n) return;
    const o = q(e, n.targetKeyStart, n.targetKeyEnd);
    return [{ uri: e.uri, originSelectionRange: q(e, n.requiredStringStart, n.requiredStringEnd), range: o, targetSelectionRange: o }];
  } }));
}
const We = "rivet-json-schema-definition-hover-suppressed";
function ne(e) {
  return e.altKey || e.shiftKey ? false : ke() ? e.metaKey && !e.ctrlKey : e.ctrlKey && !e.metaKey;
}
function He(e) {
  var _a;
  if (((_a = e.getModel()) == null ? void 0 : _a.getLanguageId()) !== "json") return { dispose() {
  } };
  let t = false;
  const n = (i) => {
    var _a2;
    t !== i && (t = i, (_a2 = e.getDomNode()) == null ? void 0 : _a2.classList.toggle(We, i), e.updateOptions({ hover: { enabled: !i } }));
  }, o = (i) => {
    var _a2;
    return ((_a2 = e.getModel()) == null ? void 0 : _a2.getLanguageId()) === "json" && ne(i);
  }, r = [e.onMouseMove((i) => {
    n(o(i.event));
  }), e.onMouseLeave(() => {
    n(false);
  }), e.onKeyDown((i) => {
    n(o(i));
  }), e.onKeyUp((i) => {
    n(o(i));
  }), e.onDidChangeModel(() => {
    n(false);
  }), e.onDidBlurEditorWidget(() => {
    n(false);
  }), e.onMouseDown((i) => {
    const a = e.getModel(), m = i.target.position;
    if (!a || a.getLanguageId() !== "json" || !m || !i.event.leftButton || !ne(i.event)) return;
    const h = se(a.getValue(), a.getOffsetAt(m));
    if (!h) return;
    const g = q(a, h.targetKeyStart, h.targetKeyEnd);
    i.event.preventDefault(), i.event.stopPropagation(), e.focus(), e.setSelection(g, "rivet.jsonSchemaRequiredDefinitionNavigation"), e.revealRangeInCenterIfOutsideViewport(g, f.ScrollType.Smooth);
  })];
  return { dispose() {
    n(false), r.forEach((i) => i.dispose());
  } };
}
function Ye() {
  Ke(), qe(), Fe(), Ge(), Be();
}
const ze = /* @__PURE__ */ new Set(["markdown", "plain-text", "plaintext", "prompt-interpolation", "prompt-interpolation-markdown"]);
function Xe(e, t) {
  return t === 0 ? true : e.charAt(t - 1) !== ":";
}
function Ze(e, t) {
  let n = t;
  for (; n < e.length && e[n] !== `
` && e[n] !== "\r"; ) n += 1;
  return n;
}
function Qe(e) {
  return e != null && ze.has(e);
}
function $e(e) {
  const t = [];
  let n = 0;
  for (; n < e.length - 1; ) {
    const o = e[n], r = e[n + 1];
    if (o === "/" && r === "*") {
      const i = e.indexOf("*/", n + 2), a = i === -1 ? e.length : i + 2;
      t.push({ start: n, end: a }), n = a;
      continue;
    }
    if (o === "/" && r === "/" && Xe(e, n)) {
      const i = Ze(e, n + 2);
      t.push({ start: n, end: i }), n = i;
      continue;
    }
    n += 1;
  }
  return t;
}
const et = "rivet-editor-js-style-comment";
function tt(e, t) {
  const n = e.getPositionAt(t.start), o = e.getPositionAt(t.end);
  return new P(n.lineNumber, n.column, o.lineNumber, o.column);
}
function nt(e) {
  const t = e.getModel();
  if (!t) return { dispose: () => {
  } };
  const n = e.createDecorationsCollection(), o = () => {
    n.set($e(t.getValue()).map((i) => ({ range: tt(t, i), options: { inlineClassName: et, stickiness: f.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges } })));
  }, r = t.onDidChangeContent(o);
  return o(), { dispose: () => {
    n.clear(), r.dispose();
  } };
}
function ot(e) {
  return e.replace(/\r\n?/g, `
`);
}
function rt(e) {
  return JSON.stringify(ot(e)).slice(1, -1);
}
function it(e) {
  try {
    const t = JSON.parse(`"${e}"`);
    return typeof t == "string" ? t : void 0;
  } catch {
    return;
  }
}
const st = "rivet-editor-interpolation-token", at = { "js-value": Ne, "json-template": Oe };
function ct(e, t) {
  const n = e.getPositionAt(t.start), o = e.getPositionAt(t.end);
  return new P(n.lineNumber, n.column, o.lineNumber, o.column);
}
function ut(e, t) {
  const n = e.getOffsetAt({ lineNumber: t.startLineNumber, column: t.startColumn }), o = e.getOffsetAt({ lineNumber: t.endLineNumber, column: t.endColumn });
  return { start: n, end: o };
}
function lt(e) {
  return { code: e.code, severity: e.severity, message: e.message, source: e.source, startLineNumber: e.startLineNumber, startColumn: e.startColumn, endLineNumber: e.endLineNumber, endColumn: e.endColumn, modelVersionId: e.modelVersionId, relatedInformation: e.relatedInformation, tags: e.tags };
}
function dt(e, t, n) {
  const o = e.getPositionAt(t.start), r = e.getPositionAt(t.end);
  return { severity: he.Error, message: n, source: "Rivet JSON template validation", startLineNumber: o.lineNumber, startColumn: o.column, endLineNumber: r.lineNumber, endColumn: r.column };
}
function ft(e, t) {
  const n = e.getModel();
  if (!n) return { dispose: () => {
  } };
  const o = e.createDecorationsCollection(), r = [], i = [];
  let a = false;
  const m = () => re(n.getValue()), h = () => {
    for (; i.length > 0; ) {
      const u = i.pop();
      u && clearTimeout(u);
    }
  }, g = () => {
    if (t !== "json-template") return;
    const u = ye(n.getValue()).map((v) => dt(n, v, v.message));
    f.setModelMarkers(n, Z, u);
  }, w = () => {
    const u = m();
    o.set(u.map((v) => ({ range: ct(n, v), options: { inlineClassName: st, stickiness: f.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges } })));
  }, A = () => {
    if (a || e.getModel() !== n) return;
    const u = m();
    for (const v of at[t]) {
      const k = f.getModelMarkers({ owner: v, resource: n.uri }), S = t === "json-template" ? [] : k.filter((R) => !Te(ut(n, R), u));
      S.length !== k.length && f.setModelMarkers(n, v, S.map(lt));
    }
  }, y = () => {
    if (A(), t === "json-template") {
      h(), queueMicrotask(A);
      for (const u of [0, 50, 250]) i.push(setTimeout(A, u));
    }
  }, T = () => {
    a || e.getModel() !== n || (w(), g(), y());
  };
  return r.push(n.onDidChangeContent(T)), r.push(f.onDidChangeMarkers((u) => {
    u.some((v) => v.toString() === n.uri.toString()) && y();
  })), T(), { dispose: () => {
    a = true, o.clear(), f.setModelMarkers(n, Z, []), h(), r.forEach((u) => u.dispose());
  } };
}
class ce {
  constructor() {
    __publicField(this, "disposables", []);
  }
  add(t) {
    return t && this.disposables.push(t), t;
  }
  dispose() {
    for (const t of this.disposables.splice(0).reverse()) t.dispose();
  }
}
function pt(e, t) {
  const n = new ce();
  return t.interpolation && n.add(ft(e, t.interpolation)), t.commentHighlighting && n.add(nt(e)), t.definitionNavigation && n.add(He(e)), t.textTools && vt(e).forEach((o) => n.add(o)), n;
}
function gt(e, t) {
  return e.addAction({ id: "rivet.checkSpelling", label: "Check spelling", contextMenuGroupId: "navigation", contextMenuOrder: 1.5, run: async () => {
    try {
      await (t ? t() : Ae(e));
    } catch {
    }
  } });
}
function mt(e) {
  const t = e.getModel(), n = e.getSelection();
  if (!(!t || !n || n.isEmpty())) return { selection: n, text: t.getValueInRange(n) };
}
function oe(e, t) {
  if (e.getOption(f.EditorOption.readOnly)) return;
  const n = mt(e), o = n && t(n.text);
  !n || o == null || o === n.text || (e.pushUndoStop(), e.executeEdits("rivet.textTools", [{ range: n.selection, text: o, forceMoveMarkers: true }]), e.pushUndoStop());
}
async function ht(e) {
  if (e.getOption(f.EditorOption.readOnly)) return;
  const t = e.getSelection(), n = e.getAction(t && !t.isEmpty() ? "editor.action.formatSelection" : "editor.action.formatDocument");
  (n == null ? void 0 : n.isSupported()) && await n.run();
}
function vt(e) {
  return [e.addAction({ id: "rivet.prettify", label: "Prettify", contextMenuGroupId: "navigation", contextMenuOrder: 1.6, run: () => ht(e) }), e.addAction({ id: "rivet.jsonEscapeSelection", label: "JSON escape", contextMenuGroupId: "navigation", contextMenuOrder: 1.7, run: () => oe(e, rt) }), e.addAction({ id: "rivet.jsonUnescapeSelection", label: "JSON unescape", contextMenuGroupId: "navigation", contextMenuOrder: 1.8, run: () => oe(e, it) })];
}
function Et(e) {
  const { capabilities: t, enableSpellcheckAction: n, interpolationSyntax: o, language: r } = e;
  return { commentHighlighting: (t == null ? void 0 : t.commentHighlighting) ?? Qe(r), definitionNavigation: (t == null ? void 0 : t.definitionNavigation) ?? true, interpolation: (t == null ? void 0 : t.interpolation) === false ? void 0 : (t == null ? void 0 : t.interpolation) ?? o, spellcheckAction: (t == null ? void 0 : t.spellcheckAction) ?? n, textTools: (t == null ? void 0 : t.textTools) ?? true };
}
const kt = "vs-dark", Mt = 14;
Ye();
const Nt = ({ text: e, isReadonly: t, onChange: n, language: o, interpolationSyntax: r, theme: i, autoFocus: a, onKeyDown: m, onBlur: h, editorRef: g, onEditorMount: w, scrollBeyondLastLine: A, enableFolding: y, wordWrap: T = "on", scrollbar: u, displayOptions: v, onContentHeightChange: k, errorLineHighlight: S, fontSize: R = Mt, onFontSizeKeyDown: B, onFontSizeWheel: D, isNodeEditorResizing: L = false, modelCacheKey: O, enableSpellcheckAction: ue = true, onSpellcheckAction: le, capabilities: de }) => {
  const V = d.useRef(null), E = d.useRef(), F = d.useRef([]), b = d.useRef(false), N = d.useRef(), I = U(n), _ = U(k), G = U(le), W = d.useRef(L), j = Et({ capabilities: de, enableSpellcheckAction: ue, interpolationSyntax: r, language: o });
  return W.current = L, d.useEffect(() => {
    var _a;
    const s = V.current;
    if (!s) return;
    const p = O ? ve.parse(Re(O)) : void 0, { model: l, isCached: fe } = Ce({ cacheKey: O, text: e, getExistingModel: p ? () => f.getModel(p) : void 0, createModel: () => f.createModel(e, o, p) }), c = f.create(s, { theme: i ?? kt, lineNumbers: "on", glyphMargin: false, folding: y ?? false, foldingStrategy: y ? "auto" : void 0, showFoldingControls: y ? "mouseover" : void 0, foldingHighlight: y ? true : void 0, unfoldOnClickAfterEndOfLine: y ? false : void 0, lineNumbersMinChars: 2, minimap: { enabled: false }, ...v, fontSize: R, wordWrap: T, readOnly: t, model: l, scrollBeyondLastLine: A, scrollbar: { ...u, alwaysConsumeMouseWheel: false } });
    c.__rivetSpellcheckMarkers = { clear: () => {
      f.setModelMarkers(l, Q, []);
    }, setMarkers: (J) => {
      f.setModelMarkers(l, Q, [...J]);
    } };
    const H = Le(O);
    H && c.restoreViewState(H), c.layout(), (_a = _.current) == null ? void 0 : _a.call(_, c.getContentHeight());
    const C = new ce();
    C.add(pt(c, j));
    const pe = () => {
      if (W.current) {
        b.current = true;
        return;
      }
      b.current = false, c.layout();
    }, Y = new ResizeObserver(pe);
    Y.observe(s), C.add(c.onDidContentSizeChange((J) => {
      var _a2;
      J.contentHeightChanged && ((_a2 = _.current) == null ? void 0 : _a2.call(_, c.getContentHeight()));
    })), C.add(c.onDidChangeModelContent(() => {
      var _a2;
      $(c), (_a2 = I.current) == null ? void 0 : _a2.call(I, c.getValue());
    })), C.add(c.onDidBlurEditorWidget(() => {
      h == null ? void 0 : h();
    })), E.current = c, g && (g.current = c), w == null ? void 0 : w(c);
    const z = I.current;
    return l.getValue() !== e && (z == null ? void 0 : z(l.getValue())), () => {
      var _a2;
      z == null ? void 0 : z(c.getValue()), be(O, c.saveViewState()), (_a2 = N.current) == null ? void 0 : _a2.dispose(), N.current = void 0, E.current = void 0, g && (g.current = void 0), Y == null ? void 0 : Y.disconnect(), C.dispose(), $(c), delete c.__rivetSpellcheckMarkers, c.dispose(), fe || l.dispose();
    };
  }, []), d.useEffect(() => {
    var _a;
    const s = E.current;
    if ((_a = N.current) == null ? void 0 : _a.dispose(), N.current = void 0, !(!s || !j.spellcheckAction)) return N.current = gt(s, G.current ?? void 0), () => {
      var _a2;
      (_a2 = N.current) == null ? void 0 : _a2.dispose(), N.current = void 0;
    };
  }, [G, j.spellcheckAction]), d.useEffect(() => {
    const s = E.current;
    if (!s) return;
    const p = s.onKeyDown((l) => {
      if (B == null ? void 0 : B(l.browserEvent)) {
        l.preventDefault(), l.stopPropagation();
        return;
      }
      m == null ? void 0 : m(l);
    });
    return () => {
      p.dispose();
    };
  }, [B, m]), d.useEffect(() => {
    const s = V.current;
    if (!s || !D) return;
    const p = (l) => {
      D(l);
    };
    return s.addEventListener("wheel", p, { capture: true, passive: false }), () => {
      s.removeEventListener("wheel", p, true);
    };
  }, [D]), d.useEffect(() => {
    var _a;
    a && ((_a = E.current) == null ? void 0 : _a.focus());
  }, [a]), d.useEffect(() => {
    var _a;
    const s = E.current, p = s == null ? void 0 : s.getModel();
    !s || !p || !t || I.current || O || p.getValue() !== e && (p.setValue(e), s.layout(), (_a = _.current) == null ? void 0 : _a.call(_, s.getContentHeight()));
  }, [t, O, I, _, e]), d.useEffect(() => {
    const s = E.current;
    s && (s.updateOptions({ fontSize: R }), s.layout(), k == null ? void 0 : k(s.getContentHeight()));
  }, [R, k]), d.useEffect(() => {
    const s = E.current;
    s && (s.updateOptions({ wordWrap: T }), s.layout(), k == null ? void 0 : k(s.getContentHeight()));
  }, [k, T]), d.useEffect(() => {
    const s = E.current;
    s && (s.updateOptions({ scrollbar: { ...u, alwaysConsumeMouseWheel: false } }), s.layout(), k == null ? void 0 : k(s.getContentHeight()));
  }, [k, u]), d.useEffect(() => {
    const s = E.current, p = s == null ? void 0 : s.getModel();
    if (!s || !p) return;
    const l = S && e === S.source && S.line >= 1 && S.line <= p.getLineCount() ? S.line : void 0;
    F.current = s.deltaDecorations(F.current, l ? [{ range: new P(l, 1, l, 1), options: { className: "code-node-runtime-error-line", isWholeLine: true, stickiness: f.TrackedRangeStickiness.NeverGrowsWhenTypingAtEdges } }] : []);
  }, [S, e]), d.useEffect(() => {
    var _a;
    L || b.current && (b.current = false, (_a = E.current) == null ? void 0 : _a.layout());
  }, [L]), Ee("div", { ref: V, className: "editor-container" });
};
export {
  Nt as CodeEditor,
  Nt as default
};
