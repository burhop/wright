import { g as Br } from "./vendor-CRPgzvoS.js";
function Tr(u, s) {
  for (var i = 0; i < s.length; i++) {
    const a = s[i];
    if (typeof a != "string" && !Array.isArray(a)) {
      for (const n in a) if (n !== "default" && !(n in u)) {
        const r = Object.getOwnPropertyDescriptor(a, n);
        r && Object.defineProperty(u, n, r.get ? r : { enumerable: true, get: () => a[n] });
      }
    }
  }
  return Object.freeze(Object.defineProperty(u, Symbol.toStringTag, { value: "Module" }));
}
/*!
* Determine if an object is a Buffer
*
* @author   Feross Aboukhadijeh <https://feross.org>
* @license  MIT
*/
var z, lr;
function Wr() {
  return lr || (lr = 1, z = function(s) {
    return s != null && s.constructor != null && typeof s.constructor.isBuffer == "function" && s.constructor.isBuffer(s);
  }), z;
}
var Y, cr;
function Sr() {
  if (cr) return Y;
  cr = 1, Y = s;
  var u = [];
  function s(i, a) {
    var n = 0, r;
    if (!a) return u;
    if (i.FLAG === "long") {
      for (r = new Array(Math.ceil(a.length / 2)); n < a.length; ) r[n / 2] = a.slice(n, n + 2), n += 2;
      return r;
    }
    return a.split(i.FLAG === "num" ? "," : "");
  }
  return Y;
}
var j, hr;
function zr() {
  if (hr) return j;
  hr = 1;
  var u = Sr();
  j = r;
  var s = [].push, i = "etaoinshrdlcumwfgypbvkjxqz".split(""), a = /\s+/, n = ["qwertzuop", "yxcvbnm", "qaw", "say", "wse", "dsx", "sy", "edr", "fdc", "dx", "rft", "gfv", "fc", "tgz", "hgb", "gv", "zhu", "jhn", "hb", "uji", "kjm", "jn", "iko", "lkm"];
  function r(t) {
    var f = /* @__PURE__ */ Object.create(null), p = /* @__PURE__ */ Object.create(null), l = /* @__PURE__ */ Object.create(null), q = [], C = { in: [], out: [] }, N = [], g = t.toString("utf8"), v = [], m = 0, d = g.indexOf(`
`), c, x, h, R, F, _, A, y, E, b, w, S, O;
    for (l.KEY = []; d > -1; ) L(g.slice(m, d)), m = d + 1, d = g.indexOf(`
`, m);
    for (L(g.slice(m)), d = -1; ++d < v.length; ) if (x = v[d], c = x.split(a), h = c[0], h === "REP") {
      for (R = d + parseInt(c[1], 10); ++d <= R; ) c = v[d].split(a), q.push([c[1], c[2]]);
      d--;
    } else if (h === "ICONV" || h === "OCONV") {
      for (R = d + parseInt(c[1], 10), y = C[h === "ICONV" ? "in" : "out"]; ++d <= R; ) c = v[d].split(a), y.push([new RegExp(c[1], "g"), c[2]]);
      d--;
    } else if (h === "COMPOUNDRULE") {
      for (R = d + parseInt(c[1], 10); ++d <= R; ) for (b = v[d].split(a)[1], E = -1, N.push(b); ++E < b.length; ) p[b.charAt(E)] = [];
      d--;
    } else if (h === "PFX" || h === "SFX") {
      for (R = d + parseInt(c[3], 10), b = { type: h, combineable: c[2] === "Y", entries: [] }, f[c[1]] = b; ++d <= R; ) {
        c = v[d].split(a), F = c[2], _ = c[3].split("/"), A = c[4], y = { add: "", remove: "", match: "", continuation: u(l, _[1]) }, _ && _[0] !== "0" && (y.add = _[0]);
        try {
          F !== "0" && (y.remove = h === "SFX" ? o(F) : F), A && A !== "." && (y.match = h === "SFX" ? o(A) : e(A));
        } catch {
          y = null;
        }
        y && b.entries.push(y);
      }
      d--;
    } else if (h === "TRY") {
      for (A = c[1], S = -1, w = []; ++S < A.length; ) O = A.charAt(S), O.toLowerCase() === O && w.push(O);
      for (S = -1; ++S < i.length; ) A.indexOf(i[S]) < 0 && w.push(i[S]);
      l[h] = w;
    } else h === "KEY" ? s.apply(l[h], c[1].split("|")) : h === "COMPOUNDMIN" ? l[h] = Number(c[1]) : h === "ONLYINCOMPOUND" ? (l[h] = c[1], p[c[1]] = []) : l[h] = c[1];
    return isNaN(l.COMPOUNDMIN) && (l.COMPOUNDMIN = 3), l.KEY.length || (l.KEY = n), l.TRY || (l.TRY = i.concat()), l.KEEPCASE || (l.KEEPCASE = false), { compoundRuleCodes: p, replacementTable: q, conversion: C, compoundRules: N, rules: f, flags: l };
    function L(D) {
      D = D.trim(), D && D.charCodeAt(0) !== 35 && v.push(D);
    }
  }
  function o(t) {
    return new RegExp(t + "$");
  }
  function e(t) {
    return new RegExp("^" + t);
  }
  return j;
}
var K, vr;
function Lr() {
  if (vr) return K;
  vr = 1, K = u;
  function u(s, i) {
    for (var a = -1; ++a < i.length; ) s = s.replace(i[a][0], i[a][1]);
    return s;
  }
  return K;
}
var $, dr;
function B() {
  if (dr) return $;
  dr = 1, $ = u;
  function u(s, i, a) {
    return a && i in s && a.indexOf(s[i]) > -1;
  }
  return $;
}
var G, pr;
function Yr() {
  if (pr) return G;
  pr = 1;
  var u = B();
  G = s;
  function s(i, a) {
    var n = -1;
    if (i.data[a]) return !u(i.flags, "ONLYINCOMPOUND", i.data[a]);
    if (a.length >= i.flags.COMPOUNDMIN) {
      for (; ++n < i.compoundRules.length; ) if (i.compoundRules[n].test(a)) return true;
    }
    return false;
  }
  return G;
}
var X, gr;
function ur() {
  if (gr) return X;
  gr = 1;
  var u = Lr(), s = Yr(), i = B();
  X = a;
  function a(r, o, e) {
    var t = o.trim(), f;
    if (!t) return null;
    if (t = u(t, r.conversion.in), s(r, t)) return !e && i(r.flags, "FORBIDDENWORD", r.data[t]) ? null : t;
    if (t.toUpperCase() === t) {
      if (f = t.charAt(0) + t.slice(1).toLowerCase(), n(r.flags, r.data[f], e)) return null;
      if (s(r, f)) return f;
    }
    if (f = t.toLowerCase(), f !== t) {
      if (n(r.flags, r.data[f], e)) return null;
      if (s(r, f)) return f;
    }
    return null;
  }
  function n(r, o, e) {
    return i(r, "KEEPCASE", o) || e || i(r, "FORBIDDENWORD", o);
  }
  return X;
}
var k, mr;
function jr() {
  if (mr) return k;
  mr = 1;
  var u = ur();
  k = s;
  function s(i) {
    return !!u(this, i);
  }
  return k;
}
var V, Cr;
function Kr() {
  if (Cr) return V;
  Cr = 1, V = u;
  function u(i) {
    var a = s(i.charAt(0)), n = i.slice(1);
    return !n || (n = s(n), a === n) ? a : a === "u" && n === "l" ? "s" : null;
  }
  function s(i) {
    return i === i.toLowerCase() ? "l" : i === i.toUpperCase() ? "u" : null;
  }
  return V;
}
var H, Rr;
function $r() {
  if (Rr) return H;
  Rr = 1;
  var u = Kr(), s = Lr(), i = B(), a = ur();
  H = r;
  var n = [].push;
  function r(e) {
    var t = this, f = {}, p = [], l = {}, q, C, N = [], g, v, m, d, c, x, h, R, F, _, A, y, E, b, w, S, O, L, D, M, T, W, P;
    if (e = s(e.trim(), t.conversion.in), !e || t.correct(e)) return [];
    for (P = u(e), v = -1; ++v < t.replacementTable.length; ) for (C = t.replacementTable[v], m = e.indexOf(C[0]); m > -1; ) N.push(e.replace(C[0], C[1])), m = e.indexOf(C[0], m + 1);
    for (v = -1; ++v < e.length; ) for (R = e.charAt(v), _ = e.slice(0, v), A = e.slice(v + 1), E = R.toLowerCase(), y = E !== R, f = {}, m = -1; ++m < t.flags.KEY.length; ) if (F = t.flags.KEY[m], d = F.indexOf(E), !(d < 0)) {
      for (x = -1; ++x < F.length; ) if (x !== d) {
        if (h = F.charAt(x), f[h]) continue;
        f[h] = true, y && (h = h.toUpperCase()), N.push(_ + h + A);
      }
    }
    for (v = -1, O = e.charAt(0), g = [""], L = 1, D = 0; ++v < e.length; ) {
      for (R = O, O = e.charAt(v + 1), _ = e.slice(0, v), C = R === O ? "" : R + R, m = -1, c = g.length; ++m < c; ) m <= L && g.push(g[m] + C), g[m] += R;
      ++D < 3 && (L = g.length);
    }
    for (n.apply(N, g), g = [e], C = e.toLowerCase(), (e === C || P === null) && g.push(e.charAt(0).toUpperCase() + C.slice(1)), C = e.toUpperCase(), e !== C && g.push(C), q = { state: {}, weighted: l, suggestions: p }, b = o(t, q, g, N), w = 0, L = Math.min(b.length, Math.pow(Math.max(15 - e.length, 3), 3)), M = Math.max(Math.pow(10 - e.length, 3), 1); !p.length && w < L; ) S = w + M, o(t, q, b.slice(w, S)), w = S;
    for (p.sort(Ir), g = [], T = [], v = -1; ++v < p.length; ) W = s(p[v], t.conversion.out), C = W.toLowerCase(), T.indexOf(C) < 0 && (g.push(W), T.push(C));
    return g;
    function Ir(I, U) {
      return Ur(I, U) || Mr(I, U) || Pr(I, U);
    }
    function Ur(I, U) {
      return l[I] === l[U] ? 0 : l[I] > l[U] ? -1 : 1;
    }
    function Mr(I, U) {
      var or = u(I), fr = u(U);
      return or === fr ? 0 : or === P ? -1 : fr === P ? 1 : void 0;
    }
    function Pr(I, U) {
      return I.localeCompare(U);
    }
  }
  function o(e, t, f, p) {
    var l = e.flags.TRY, q = e.data, C = e.flags, N = [], g = -1, v, m, d, c, x, h, R, F, _, A, y, E, b;
    if (p) for (; ++g < p.length; ) w(p[g], true);
    for (g = -1; ++g < f.length; ) for (v = f[g], m = "", d = "", c = v.charAt(0), x = v, h = v.slice(1), R = c.toLowerCase() !== c, F = u(v), _ = -1; ++_ <= v.length; ) for (m += d, A = x, x = h, h = x.slice(1), d = c, c = v.charAt(_ + 1), y = R, c && (R = c.toLowerCase() !== c), x && y !== R && (w(m + S(x)), w(m + S(c) + S(d) + h)), w(m + x), x && w(m + c + d + h), b = -1; ++b < l.length; ) E = l[b], y && E !== E.toUpperCase() ? (F !== "s" && (w(m + E + A), w(m + E + x)), E = E.toUpperCase(), w(m + E + A), w(m + E + x)) : (w(m + E + A), w(m + E + x));
    return N;
    function w(O, L) {
      var D = t.state[O], M;
      D !== !!D && (N.push(O), M = a(e, O), D = M && !i(C, "NOSUGGEST", q[M]), t.state[O] = D, D && (t.weighted[O] = L ? 10 : 0, t.suggestions.push(O))), D && t.weighted[O]++;
    }
    function S(O) {
      var L = O.charAt(0);
      return (L.toLowerCase() === L ? L.toUpperCase() : L.toLowerCase()) + O.slice(1);
    }
  }
  return H;
}
var J, wr;
function Gr() {
  if (wr) return J;
  wr = 1;
  var u = ur(), s = B();
  J = i;
  function i(a) {
    var n = this, r = u(n, a, true);
    return { correct: n.correct(a), forbidden: !!(r && s(n.flags, "FORBIDDENWORD", n.data[r])), warn: !!(r && s(n.flags, "WARN", n.data[r])) };
  }
  return J;
}
var Q, Or;
function Xr() {
  if (Or) return Q;
  Or = 1, Q = u;
  function u(s, i, a, n) {
    for (var r = -1, o, e, t, f, p; ++r < i.entries.length; ) if (o = i.entries[r], f = o.continuation, p = -1, (!o.match || o.match.test(s)) && (e = o.remove ? s.replace(o.remove, "") : s, e = i.type === "SFX" ? e + o.add : o.add + e, n.push(e), f && f.length)) for (; ++p < f.length; ) t = a[f[p]], t && u(e, t, a, n);
    return n;
  }
  return Q;
}
var Z, xr;
function _r() {
  if (xr) return Z;
  xr = 1;
  var u = Xr();
  Z = n;
  var s = [].push, i = [];
  function a(r, o, e) {
    var t = r[o];
    o in r ? t === i ? r[o] = e.concat() : s.apply(t, e) : r[o] = e.concat();
  }
  function n(r, o, e, t) {
    var f = -1, p, l, q, C, N, g, v;
    for ((!("NEEDAFFIX" in t.flags) || e.indexOf(t.flags.NEEDAFFIX) < 0) && a(r, o, e); ++f < e.length; ) if (p = t.rules[e[f]], e[f] in t.compoundRuleCodes && t.compoundRuleCodes[e[f]].push(o), p) {
      for (g = u(o, p, t.rules, []), l = -1; ++l < g.length; ) if (g[l] in r || (r[g[l]] = i), p.combineable) {
        for (q = f; ++q < e.length; ) if (N = t.rules[e[q]], N && N.combineable && p.type !== N.type) for (v = u(g[l], N, t.rules, []), C = -1; ++C < v.length; ) v[C] in r || (r[v[C]] = i);
      }
    }
  }
  return Z;
}
var rr, Er;
function kr() {
  if (Er) return rr;
  Er = 1;
  var u = _r();
  rr = i;
  var s = [];
  function i(a, n) {
    var r = this;
    return u(r.data, a, r.data[n] || s, r), r;
  }
  return rr;
}
var er, Ar;
function Vr() {
  if (Ar) return er;
  Ar = 1, er = u;
  function u(s) {
    var i = this;
    return delete i.data[s], i;
  }
  return er;
}
var tr, qr;
function Hr() {
  if (qr) return tr;
  qr = 1, tr = u;
  function u() {
    return this.flags.WORDCHARS || null;
  }
  return tr;
}
var ir, Nr;
function Jr() {
  if (Nr) return ir;
  Nr = 1;
  var u = Sr(), s = _r();
  ir = a;
  var i = /\s/g;
  function a(r, o, e) {
    for (var t = r.toString("utf8"), f = t.indexOf(`
`) + 1, p = t.indexOf(`
`, f); p > -1; ) t.charCodeAt(f) !== 9 && n(t.slice(f, p), o, e), f = p + 1, p = t.indexOf(`
`, f);
    n(t.slice(f), o, e);
  }
  function n(r, o, e) {
    for (var t = r.indexOf("/"), f = r.indexOf("#"), p = "", l, q; t > -1 && r.charCodeAt(t - 1) === 92; ) r = r.slice(0, t - 1) + r.slice(t), t = r.indexOf("/", t);
    f > -1 ? t > -1 && t < f ? (l = r.slice(0, t), i.lastIndex = t + 1, q = i.exec(r), p = r.slice(t + 1, q ? q.index : void 0)) : l = r.slice(0, f) : t > -1 ? (l = r.slice(0, t), p = r.slice(t + 1)) : l = r, l = l.trim(), l && s(e, l, u(o.flags, p.trim()), o);
  }
  return ir;
}
var nr, yr;
function Qr() {
  if (yr) return nr;
  yr = 1;
  var u = Jr();
  nr = s;
  function s(i) {
    var a = this, n = -1, r, o, e, t;
    for (u(i, a, a.data); ++n < a.compoundRules.length; ) {
      for (r = a.compoundRules[n], o = "", t = -1; ++t < r.length; ) e = r.charAt(t), o += a.compoundRuleCodes[e].length ? "(?:" + a.compoundRuleCodes[e].join("|") + ")" : e;
      a.compoundRules[n] = new RegExp(o, "i");
    }
    return a;
  }
  return nr;
}
var ar, Dr;
function Zr() {
  if (Dr) return ar;
  Dr = 1, ar = u;
  function u(s) {
    var i = this, a = s.toString("utf8").split(`
`), n = -1, r, o, e, t;
    for (i.flags.FORBIDDENWORD === void 0 && (i.flags.FORBIDDENWORD = false), t = i.flags.FORBIDDENWORD; ++n < a.length; ) r = a[n].trim(), r && (r = r.split("/"), e = r[0], o = e.charAt(0) === "*", o && (e = e.slice(1)), i.add(e, r[1]), o && i.data[e].push(t));
    return i;
  }
  return ar;
}
var sr, br;
function re() {
  if (br) return sr;
  br = 1;
  var u = Wr(), s = zr();
  sr = a;
  var i = a.prototype;
  i.correct = jr(), i.suggest = $r(), i.spell = Gr(), i.add = kr(), i.remove = Vr(), i.wordCharacters = Hr(), i.dictionary = Qr(), i.personal = Zr();
  function a(n, r) {
    var o = -1, e;
    if (!(this instanceof a)) return new a(n, r);
    if (typeof n == "string" || u(n) ? (typeof r == "string" || u(r)) && (e = [{ dic: r }]) : n && ("length" in n ? (e = n, n = n[0] && n[0].aff) : (n.dic && (e = [n]), n = n.aff)), !n) throw new Error("Missing `aff` in dictionary");
    if (n = s(n), this.data = /* @__PURE__ */ Object.create(null), this.compoundRuleCodes = n.compoundRuleCodes, this.replacementTable = n.replacementTable, this.conversion = n.conversion, this.compoundRules = n.compoundRules, this.rules = n.rules, this.flags = n.flags, e) for (; ++o < e.length; ) e[o].dic && this.dictionary(e[o].dic);
  }
  return sr;
}
var Fr = re();
const ee = Br(Fr), ie = Tr({ __proto__: null, default: ee }, [Fr]);
export {
  ie as i
};
