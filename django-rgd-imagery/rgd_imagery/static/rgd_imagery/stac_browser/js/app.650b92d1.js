(function (e) { function t(t) { for (var r, n, i = t[0], u = t[1], s = t[2], l = 0, p = []; l < i.length; l++)n = i[l], Object.prototype.hasOwnProperty.call(c, n) && c[n] && p.push(c[n][0]), c[n] = 0; for (r in u) Object.prototype.hasOwnProperty.call(u, r) && (e[r] = u[r]); d && d(t); while (p.length) p.shift()(); return o.push.apply(o, s || []), a() } function a() { for (var e, t = 0; t < o.length; t++) { for (var a = o[t], r = !0, n = 1; n < a.length; n++) { var i = a[n]; 0 !== c[i] && (r = !1) } r && (o.splice(t--, 1), e = u(u.s = a[0])) } return e } var r = {}, n = { app: 0 }, c = { app: 0 }, o = []; function i(e) { return u.p + "js/" + ({ "catalog~item": "catalog~item", catalog: "catalog", item: "item", "metadata-sidebar": "metadata-sidebar", "zarr-metadata-tab": "zarr-metadata-tab", multiselect: "multiselect" }[e] || e) + "." + { "catalog~item": "4c640490", catalog: "d1b04ce7", item: "ed3889ff", "metadata-sidebar": "f591a1fc", "zarr-metadata-tab": "f8c0fd16", multiselect: "9e42f51a" }[e] + ".js" } function u(t) { if (r[t]) return r[t].exports; var a = r[t] = { i: t, l: !1, exports: {} }; return e[t].call(a.exports, a, a.exports, u), a.l = !0, a.exports } u.e = function (e) { var t = [], a = { catalog: 1, item: 1, "metadata-sidebar": 1 }; n[e] ? t.push(n[e]) : 0 !== n[e] && a[e] && t.push(n[e] = new Promise((function (t, a) { for (var r = "css/" + ({ "catalog~item": "catalog~item", catalog: "catalog", item: "item", "metadata-sidebar": "metadata-sidebar", "zarr-metadata-tab": "zarr-metadata-tab", multiselect: "multiselect" }[e] || e) + "." + { "catalog~item": "31d6cfe0", catalog: "72eff2e0", item: "f1e97330", "metadata-sidebar": "fcfbc03a", "zarr-metadata-tab": "31d6cfe0", multiselect: "31d6cfe0" }[e] + ".css", c = u.p + r, o = document.getElementsByTagName("link"), i = 0; i < o.length; i++) { var s = o[i], l = s.getAttribute("data-href") || s.getAttribute("href"); if ("stylesheet" === s.rel && (l === r || l === c)) return t() } var p = document.getElementsByTagName("style"); for (i = 0; i < p.length; i++) { s = p[i], l = s.getAttribute("data-href"); if (l === r || l === c) return t() } var d = document.createElement("link"); d.rel = "stylesheet", d.type = "text/css", d.onload = t, d.onerror = function (t) { var r = t && t.target && t.target.src || c, o = new Error("Loading CSS chunk " + e + " failed.\n(" + r + ")"); o.code = "CSS_CHUNK_LOAD_FAILED", o.request = r, delete n[e], d.parentNode.removeChild(d), a(o) }, d.href = c; var f = document.getElementsByTagName("head")[0]; f.appendChild(d) })).then((function () { n[e] = 0 }))); var r = c[e]; if (0 !== r) if (r) t.push(r[2]); else { var o = new Promise((function (t, a) { r = c[e] = [t, a] })); t.push(r[2] = o); var s, l = document.createElement("script"); l.charset = "utf-8", l.timeout = 120, u.nc && l.setAttribute("nonce", u.nc), l.src = i(e); var p = new Error; s = function (t) { l.onerror = l.onload = null, clearTimeout(d); var a = c[e]; if (0 !== a) { if (a) { var r = t && ("load" === t.type ? "missing" : t.type), n = t && t.target && t.target.src; p.message = "Loading chunk " + e + " failed.\n(" + r + ": " + n + ")", p.name = "ChunkLoadError", p.type = r, p.request = n, a[1](p) } c[e] = void 0 } }; var d = setTimeout((function () { s({ type: "timeout", target: l }) }), 12e4); l.onerror = l.onload = s, document.head.appendChild(l) } return Promise.all(t) }, u.m = e, u.c = r, u.d = function (e, t, a) { u.o(e, t) || Object.defineProperty(e, t, { enumerable: !0, get: a }) }, u.r = function (e) { "undefined" !== typeof Symbol && Symbol.toStringTag && Object.defineProperty(e, Symbol.toStringTag, { value: "Module" }), Object.defineProperty(e, "__esModule", { value: !0 }) }, u.t = function (e, t) { if (1 & t && (e = u(e)), 8 & t) return e; if (4 & t && "object" === typeof e && e && e.__esModule) return e; var a = Object.create(null); if (u.r(a), Object.defineProperty(a, "default", { enumerable: !0, value: e }), 2 & t && "string" != typeof e) for (var r in e) u.d(a, r, function (t) { return e[t] }.bind(null, r)); return a }, u.n = function (e) { var t = e && e.__esModule ? function () { return e["default"] } : function () { return e }; return u.d(t, "a", t), t }, u.o = function (e, t) { return Object.prototype.hasOwnProperty.call(e, t) }, u.p = "/static/rgd_imagery/stac_browser/", u.oe = function (e) { throw console.error(e), e }; var s = window["webpackJsonp"] = window["webpackJsonp"] || [], l = s.push.bind(s); s.push = t, s = s.slice(); for (var p = 0; p < s.length; p++)t(s[p]); var d = l; o.push([0, "chunk-vendors"]), a() })({ 0: function (e, t, a) { e.exports = a("56d7") }, 1: function (e, t) { }, "56d7": function (e, t, a) { "use strict"; a.r(t), function (e) { a.d(t, "FULL_CATALOG_URL", (function () { return M })); var r = a("ade3"), n = a("5530"), c = a("1da1"), o = (a("e260"), a("e6cf"), a("cca6"), a("a79d"), a("96cf"), a("d3b7"), a("3ca3"), a("ddb0"), a("a15b"), a("fb6a"), a("ac1f"), a("1276"), a("99af"), a("5319"), a("25f0"), a("2b3d"), a("d81d"), a("df7c")), i = a.n(o), u = a("0b16"), s = a.n(u), l = a("3003"), p = a("cca8"), d = a("3c97"), f = a("7049"), m = a("a7e2"), h = a("498a"), b = a("d435"), g = a("b519"), v = a("1f1a"), y = a("700c"), w = a("0774"), O = a.n(w), j = a("58ca"), x = a("76a0"), E = a.n(x), k = a("a026"), L = a("8c4f"), S = a("2f62"), _ = (a("f9e3"), a("2dd8"), a("6cc5"), a("db49")), A = a("e0eb"), R = function () { return Promise.all([a.e("catalog~item"), a.e("catalog")]).then(a.bind(null, "556b")) }, C = function () { return Promise.all([a.e("catalog~item"), a.e("item")]).then(a.bind(null, "5e7d")) }, M = window.location.protocol + "//" + window.location.host + "/" + _["a"]; k["a"].use(l["a"]), k["a"].use(p["a"]), k["a"].use(d["a"]), k["a"].use(f["a"]), k["a"].use(m["a"]), k["a"].use(h["a"]), k["a"].use(b["a"]), k["a"].use(g["a"]), k["a"].use(v["a"]), k["a"].use(y["a"]), k["a"].use(j["a"]), k["a"].use(L["a"]), k["a"].use(S["a"]); var P = function (e) { var t = s.a.parse(window.location.hostname + "/" + M), a = s.a.parse(e); if (t.hostname !== a.hostname) return e; var r = t.path.split("/").slice(0, -1).join("/"); return i.a.relative(r, "".concat(a.path).concat(a.hash || "")) }, D = function (t) { return O.a.encode(e.from(P(t))) }, I = function (e) { var t = arguments.length > 1 && void 0 !== arguments[1] ? arguments[1] : M, a = Object(A["b"])(e), r = a.replace(":", encodeURIComponent(":")).replace(encodeURIComponent(":") + "//", "://"); return new URL(r, t).toString() }; function T(e) { try { return I(O.a.decode(e).toString()) } catch (t) { return console.warn(t), M } } var N = function () { var e = Object(c["a"])(regeneratorRuntime.mark((function e() { var t, a, o, i, u, s; return regeneratorRuntime.wrap((function (e) { while (1) switch (e.prev = e.next) { case 0: if (t = {}, a = document.querySelector("script.state[type='application/json']"), null != a) try { t = JSON.parse(a.text) } catch (l) { console.warn("Unable to parse rendered state:", l) } return o = [{ path: "/item/(.*)", component: C, props: function (e) { var t = [M]; e.params.pathMatch && (t = t.concat(e.params.pathMatch.split("/").map(T))); var a = null; return e.hash && (a = e.hash.slice(1).split("/")), { ancestors: t, center: a, path: e.path, resolve: I, slugify: D, url: t.slice(-1).pop() } } }, { path: "/collection/(.*)", component: R, props: function (e) { var t = [M]; return e.params.pathMatch && (t = t.concat(e.params.pathMatch.split("/").map(T))), { ancestors: t, path: e.path, resolve: I, slugify: D, url: t.slice(-1).pop() } } }, { path: "/(.*)", component: R, props: function (e) { var t = [M]; return e.params.pathMatch && (t = t.concat(e.params.pathMatch.split("/").map(T))), { ancestors: t, path: e.path, resolve: I, slugify: D, url: t.slice(-1).pop() } } }], i = new S["a"].Store({ state: { entities: {}, loading: {} }, getters: { getEntity: function (e) { return function (t) { return e.entities[t] } } }, mutations: { FAILED: function (e, t) { var a = t.err, c = t.url; e.entities = Object(n["a"])(Object(n["a"])({}, e.entities), {}, Object(r["a"])({}, c, a)), e.loading = Object(n["a"])(Object(n["a"])({}, e.loading), {}, Object(r["a"])({}, c, !1)) }, LOADING: function (e, t) { e.loading = Object(n["a"])(Object(n["a"])({}, e.loading), {}, Object(r["a"])({}, t, !0)) }, LOADED: function (e, t) { var a = t.entity, c = t.url; e.entities = Object(n["a"])(Object(n["a"])({}, e.entities), {}, Object(r["a"])({}, c, a)), e.loading = Object(n["a"])(Object(n["a"])({}, e.loading), {}, Object(r["a"])({}, c, !1)) } }, actions: { load: function (e, t) { return Object(c["a"])(regeneratorRuntime.mark((function a() { var r, n, c, o; return regeneratorRuntime.wrap((function (a) { while (1) switch (a.prev = a.next) { case 0: if (r = e.commit, n = e.state, null == n.entities[t] && !0 !== n.loading[t]) { a.next = 3; break } return a.abrupt("return"); case 3: return r("LOADING", t), a.prev = 4, a.next = 7, Object(A["a"])(t); case 7: if (c = a.sent, !c.ok) { a.next = 15; break } return a.next = 11, c.json(); case 11: o = a.sent, r("LOADED", { entity: o, url: t }), a.next = 24; break; case 15: return a.t0 = r, a.t1 = Error, a.next = 19, c.text(); case 19: a.t2 = a.sent, a.t3 = new a.t1(a.t2), a.t4 = t, a.t5 = { err: a.t3, url: a.t4 }, (0, a.t0)("FAILED", a.t5); case 24: a.next = 30; break; case 26: a.prev = 26, a.t6 = a["catch"](4), console.warn(a.t6), r("FAILED", { err: a.t6, url: t }); case 30: case "end": return a.stop() } }), a, null, [[4, 26]]) })))() } }, strict: !1 }), u = new L["a"]({ base: "/rgd_imagery/stac_browser/", mode: _["b"], routes: o }), window.router = u, e.next = 9, i.dispatch("load", M); case 9: u.beforeEach(function () { var e = Object(c["a"])(regeneratorRuntime.mark((function e(a, r, n) { var c; return regeneratorRuntime.wrap((function (e) { while (1) switch (e.prev = e.next) { case 0: if (r.path !== a.path) { e.next = 2; break } return e.abrupt("return", n()); case 2: if (null == t.path || t.path === a.path.replace(/\/$/, "") || t.path.toLowerCase() !== a.path.toLowerCase().replace(/\/$/, "")) { e.next = 4; break } return e.abrupt("return", n(t.path)); case 4: if (null == a.params.pathMatch) { e.next = 8; break } return c = a.params.pathMatch.split("/").reverse().map(T), e.next = 8, E()(c, i.dispatch.bind(i, "load"), { concurrency: 10 }); case 8: return e.abrupt("return", n()); case 9: case "end": return e.stop() } }), e) }))); return function (t, a, r) { return e.apply(this, arguments) } }()), s = document.getElementById("app"), null != document.getElementById("rendered") && (s = document.getElementById("rendered")), new k["a"]({ el: s, router: u, store: i, template: '<router-view id="rendered" />' }); case 13: case "end": return e.stop() } }), e) }))); return function () { return e.apply(this, arguments) } }(); N() }.call(this, a("b639").Buffer) }, db49: function (e, t, a) { "use strict"; a.d(t, "a", (function () { return r })), a.d(t, "e", (function () { return n })), a.d(t, "c", (function () { return c })), a.d(t, "d", (function () { return o })), a.d(t, "b", (function () { return i })); var r = "api/stac", n = "/api/rgd_imagery/tiles/{z}/{x}/{y}.png?url={ASSET_HREF}", c = "undefined", o = "undefined", i = "hash" }, e0eb: function (e, t, a) { "use strict"; a.d(t, "b", (function () { return c })), a.d(t, "a", (function () { return o })), a.d(t, "c", (function () { return s })); var r = a("1da1"), n = (a("96cf"), a("ac1f"), a("5319"), a("1276"), a("d3b7"), a("db49")), c = function (e) { return n["c"] ? e.replace(n["c"].split("|")[0], n["c"].split("|")[1]) : e }; function o(e) { return i.apply(this, arguments) } function i() { return i = Object(r["a"])(regeneratorRuntime.mark((function e(t) { var a; return regeneratorRuntime.wrap((function (e) { while (1) switch (e.prev = e.next) { case 0: return a = c(t), e.abrupt("return", fetch(a)); case 2: case "end": return e.stop() } }), e) }))), i.apply(this, arguments) } var u = function (e) { return n["d"] ? e.replace(n["d"].split("|")[0], n["d"].split("|")[1]) : e }, s = function (e) { var t = u(e); return n["e"].replace("{ASSET_HREF}", t) } } });
//# sourceMappingURL=app.650b92d1.js.map
