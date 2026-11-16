(function () {
  "use strict";
  var P = window.__P, d = document;
  var gate = d.getElementById("gate"), form = d.getElementById("gate-form"), pw = d.getElementById("gate-pw"), msg = d.getElementById("gate-msg");
  var app = d.getElementById("app"), btn = form.querySelector("button");
  var MIME = { jpg: "image/jpeg", png: "image/png", mp4: "video/mp4" };
  var STORE = "hh_key", key = null, cache = {};

  function unb64(s) { var b = atob(s), a = new Uint8Array(b.length); for (var i = 0; i < b.length; i++) a[i] = b.charCodeAt(i); return a; }
  function b64(buf) { var a = new Uint8Array(buf), s = ""; for (var i = 0; i < a.length; i++) s += String.fromCharCode(a[i]); return btoa(s); }
  function importKey(raw) { return crypto.subtle.importKey("raw", raw, { name: "AES-GCM" }, false, ["decrypt"]); }
  function derive(pass) {
    return crypto.subtle.importKey("raw", new TextEncoder().encode(pass), "PBKDF2", false, ["deriveBits"]).then(function (k) {
      return crypto.subtle.deriveBits({ name: "PBKDF2", salt: unb64(P.salt), iterations: P.iter, hash: "SHA-256" }, k, 256);
    });
  }
  function fetchDec(url, k) {
    return fetch(url).then(function (r) { if (!r.ok) throw new Error("load"); return r.arrayBuffer(); }).then(function (buf) {
      return crypto.subtle.decrypt({ name: "AES-GCM", iv: new Uint8Array(buf, 0, 12) }, k, new Uint8Array(buf, 12));
    });
  }
  function asset(ref) {
    if (!cache[ref]) {
      var p = ref.split(".");
      cache[ref] = fetchDec(P.root + "a/" + p[0] + ".bin", key).then(function (buf) { return URL.createObjectURL(new Blob([buf], { type: MIME[p[1]] || "application/octet-stream" })); });
    }
    return cache[ref];
  }
  function render(data) {
    d.title = data.title;
    app.innerHTML = data.html;
    gate.parentNode.removeChild(gate);
    ["src", "poster", "href", "data-lbsrc"].forEach(function (attr) {
      Array.prototype.forEach.call(app.querySelectorAll("[data-e-" + attr + "]"), function (el) {
        asset(el.getAttribute("data-e-" + attr)).then(function (url) {
          el.setAttribute(attr, url);
          window.dispatchEvent(new Event("scroll"));
        }).catch(function () {});
      });
    });
    var s = d.createElement("script");
    s.src = P.root + "js/site.js";
    d.body.appendChild(s);
    if (location.hash.length > 1) {
      var t = d.getElementById(location.hash.slice(1));
      if (t) setTimeout(function () { t.scrollIntoView(); }, 60);
    }
  }
  function open(k) {
    return fetchDec(P.root + "p/" + P.page + ".bin", k).then(function (buf) { key = k; render(JSON.parse(new TextDecoder().decode(buf))); });
  }
  function ask() { gate.hidden = false; try { pw.focus(); } catch (e) {} }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!pw.value) return;
    btn.disabled = true;
    msg.textContent = "Checking…";
    var pass = pw.value.normalize("NFKC").trim().toLowerCase().replace(/[\u2010-\u2015\u2212\s_]+/g, "-");
    derive(pass).then(function (raw) {
      return importKey(raw).then(open).then(function () {
        try { localStorage.setItem(STORE, JSON.stringify({ k: b64(raw), exp: Date.now() + P.days * 864e5 })); } catch (e) {}
      });
    }).catch(function (err) {
      btn.disabled = false;
      msg.textContent = err && err.name === "OperationError" ? "Wrong password." : "Could not load the page. Check your connection and try again.";
      pw.select();
    });
  });

  if (location.protocol === "http:" && !/^(localhost|127\.|\[::1\])/.test(location.host)) { location.replace("https:" + location.href.slice(5)); return; }
  if (!(window.crypto && crypto.subtle)) { gate.hidden = false; msg.textContent = "This browser cannot open the site."; btn.disabled = true; return; }
  var saved = null;
  try { saved = JSON.parse(localStorage.getItem(STORE) || "null"); } catch (e) {}
  if (saved && saved.k && saved.exp > Date.now()) {
    importKey(unb64(saved.k)).then(open).catch(function () { try { localStorage.removeItem(STORE); } catch (e) {} ask(); });
  } else ask();
})();
