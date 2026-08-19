import { r as t, u as w, e as u, j as C, c as F } from "./vendor-CRPgzvoS.js";
import { t as I, r as S } from "./index-DP_wohYo.js";
const v = 20, M = 56, z = 720, O = F`
  height: min(58vh, var(--project-compare-monaco-diff-height));
  min-height: ${M}px;
  overflow: hidden;
  position: relative;

  &::before {
    background: var(--settings-collapsible-border);
    bottom: 0;
    content: '';
    left: 50%;
    pointer-events: none;
    position: absolute;
    top: 0;
    width: 1px;
    z-index: 3;
  }

  .monaco-diff-editor,
  .monaco-editor,
  .monaco-editor .margin,
  .monaco-editor-background,
  .monaco-editor .inputarea.ime-input,
  .monaco-editor .overflow-guard {
    background: transparent !important;
  }

  .monaco-sash,
  .monaco-scrollable-element > .shadow,
  .monaco-editor .scroll-decoration {
    box-shadow: none !important;
    display: none !important;
  }

  .monaco-editor .decorationsOverviewRuler {
    opacity: 0.85;
  }

  .monaco-scrollable-element > .scrollbar.vertical {
    opacity: 0.8;
  }

  .monaco-scrollable-element > .scrollbar.horizontal {
    display: none !important;
  }

  .original-in-monaco-diff-editor .decorationsOverviewRuler,
  .original-in-monaco-diff-editor .monaco-scrollable-element > .scrollbar.vertical {
    display: none !important;
  }
`, V = ({ currentText: e, previousText: n }) => {
  const m = t.useRef(null), c = t.useRef(), l = t.useRef(), d = t.useRef(), D = w(I), f = S(void 0, D), [p, g] = t.useState(() => b(n, e)), i = t.useCallback(() => {
    const o = c.current;
    if (!o) return;
    const a = _(o);
    g((s) => s === a ? s : a);
  }, []);
  return t.useEffect(() => {
    const o = m.current;
    if (!o) return;
    const a = u.createModel(n, "plaintext"), s = u.createModel(e, "plaintext"), r = u.createDiffEditor(o, { theme: f, readOnly: true, originalEditable: false, renderSideBySide: true, renderSideBySideInlineBreakpoint: 0, enableSplitViewResizing: false, automaticLayout: false, scrollBeyondLastLine: false, minimap: { enabled: false }, lineNumbers: "on", lineNumbersMinChars: 2, lineHeight: v, padding: { bottom: 0, top: 0 }, folding: true, foldingStrategy: "auto", showFoldingControls: "mouseover", overviewRulerBorder: false, wordWrap: "off", ignoreTrimWhitespace: false, renderIndicators: true, scrollbar: { alwaysConsumeMouseWheel: false, horizontal: "hidden", horizontalScrollbarSize: 0 } });
    c.current = r;
    const h = new ResizeObserver(() => r.layout()), H = [r.onDidUpdateDiff(i), r.getModifiedEditor().onDidContentSizeChange(i), r.getOriginalEditor().onDidContentSizeChange(i)];
    return r.setModel({ modified: s, original: a }), h.observe(o), r.layout(), i(), l.current = a, d.current = s, () => {
      h.disconnect(), H.forEach((R) => R.dispose()), c.current = void 0, l.current = void 0, d.current = void 0, r.dispose(), a.dispose(), s.dispose();
    };
  }, []), t.useEffect(() => {
    u.setTheme(f);
  }, [f]), t.useEffect(() => {
    if (l.current && l.current.getValue() !== n && l.current.setValue(n), d.current && d.current.getValue() !== e && d.current.setValue(e), !c.current) {
      g(b(n, e));
      return;
    }
    i();
    const o = requestAnimationFrame(i);
    return () => cancelAnimationFrame(o);
  }, [e, n, i]), t.useEffect(() => {
    const o = requestAnimationFrame(() => {
      var _a;
      return (_a = c.current) == null ? void 0 : _a.layout();
    });
    return () => cancelAnimationFrame(o);
  }, [p]), C("div", { ref: m, css: O, className: "project-compare-monaco-diff-editor", style: { "--project-compare-monaco-diff-height": `${p}px` } });
};
function _(e) {
  return y(Math.max(e.getOriginalEditor().getContentHeight(), e.getModifiedEditor().getContentHeight()));
}
function b(e, n) {
  const m = Math.max(E(e), E(n));
  return y(m * v);
}
function y(e) {
  return Math.min(z, Math.max(M, Math.ceil(e)));
}
function E(e) {
  return Math.max(1, e.split(/\r\n|\r|\n/).length);
}
export {
  V as ProjectComparisonDiffEditor,
  V as default
};
