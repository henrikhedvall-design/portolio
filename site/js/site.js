(function () {
  "use strict";
  var d = document, root = d.documentElement;
  var still = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  var $ = function (s, el) { return (el || d).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || d).querySelectorAll(s)); };

  /* Theme: the dot in the headline switches between light and dark */
  var dot = $(".dot");
  if (dot) dot.addEventListener("click", function () {
    var sysDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    var dark = root.classList.contains("dk") || (!root.classList.contains("lt") && sysDark);
    var next = dark ? "lt" : "dk";
    root.classList.remove("dk", "lt");
    root.classList.add(next);
    try { sessionStorage.setItem("theme", next); } catch (e) {}
  });

  /* Scroll: reveal, header, progress bar, films, parallax */
  var hdr = $(".hdr"), bar = $(".bar");
  var rvt = parseFloat(d.body.getAttribute("data-rvt")) || 1.02;
  var lastY = 0, raf = 0, up = false;
  function check() {
    var h = window.innerHeight || root.clientHeight;
    var se = d.scrollingElement || root;
    var y = window.scrollY || se.scrollTop || 0;
    $$("[data-rv]:not(.in)").forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < h * rvt && r.bottom > 0) { el.classList.add("in"); }
    });
    $$("[data-svc]:not([data-on])").forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < h * rvt && r.bottom > 0) { el.setAttribute("data-on", "1"); var ic = $(".ic", el); if (ic) ic.classList.add("in"); }
    });
    if (!still) {
      $$("[data-vid]").forEach(function (v) {
        var r = v.getBoundingClientRect();
        var on = r.top < h && r.bottom > 0;
        try {
          if (on && v.paused) { v.muted = true; var p = v.play(); if (p && p.catch) p.catch(function () {}); }
          else if (!on && !v.paused) v.pause();
        } catch (e) {}
      });
      $$("[data-px]").forEach(function (el) {
        var r = el.getBoundingClientRect();
        var t = Math.max(-1, Math.min(1, (r.top + r.height / 2 - h / 2) / (h / 2 + r.height / 2)));
        var img = $(".px", el);
        if (img) img.style.transform = "scale(1.03) translate(" + (t * parseFloat(el.getAttribute("data-px"))).toFixed(3) + "%, " + (t * -0.6).toFixed(3) + "%)";
      });
    }
    if (y > lastY + 4 && y > 160) up = true;
    else if (y < lastY - 4 || y <= 160) up = false;
    lastY = y;
    if (hdr) hdr.classList.toggle("up", up);
    if (bar) bar.style.transform = "scaleX(" + Math.min(1, Math.max(0, y / Math.max(1, se.scrollHeight - h))).toFixed(4) + ")";
  }
  function tick() { if (raf) return; raf = requestAnimationFrame(function () { raf = 0; check(); }); }
  window.addEventListener("scroll", tick, { passive: true });
  window.addEventListener("resize", tick);
  window.addEventListener("load", tick);
  check();
  setTimeout(check, 300);

  /* Start page: letters gain weight near the pointer */
  var top = $("#top");
  if (top && !still) {
    var hraf = 0, chars = $$("[data-c]", top);
    var setW = function (c, hv) { var p = c.getAttribute("data-c").split(","); c.style.fontWeight = Math.round(+p[0] + +p[1] * hv); };
    /* A soft glow lights up around the dot as the pointer comes near it */
    var pg = $(".pg"), gx = 0, gy = 0, tx = 0, ty = 0, graf = 0, gon = false;
    var glow = function () {
      graf = 0;
      gx += (tx - gx) * 0.16; gy += (ty - gy) * 0.16;
      pg.style.setProperty("--gx", gx.toFixed(1) + "px");
      pg.style.setProperty("--gy", gy.toFixed(1) + "px");
      if (Math.abs(tx - gx) + Math.abs(ty - gy) > 0.5) graf = requestAnimationFrame(glow);
    };
    var aim = function (x, y) {
      var pr = pg.getBoundingClientRect(), tr = top.getBoundingClientRect();
      var dr = dot.getBoundingClientRect(), cx = dr.left + dr.width / 2, cy = dr.top + dr.height * 0.72;
      tx = cx - pr.left; ty = cy - tr.top;
      if (!gon) {
        gon = true; gx = tx; gy = ty;
        pg.style.setProperty("--gt", (tr.top - pr.top).toFixed(0) + "px");
        pg.style.setProperty("--gh", tr.height.toFixed(0) + "px");
      }
      var near = Math.max(0, 1 - Math.hypot(x - cx, y - cy) / 380);
      pg.style.setProperty("--go", (0.31 * near * near).toFixed(3));
      if (!graf) graf = requestAnimationFrame(glow);
    };
    top.addEventListener("mousemove", function (e) {
      if (pg && dot) aim(e.clientX, e.clientY);
      if (hraf) return;
      var x = e.clientX, y = e.clientY;
      hraf = requestAnimationFrame(function () {
        hraf = 0;
        chars.forEach(function (c) {
          var r = c.getBoundingClientRect();
          var dist = Math.hypot(x - (r.left + r.width / 2), y - (r.top + r.height / 2));
          setW(c, 160 * Math.max(0, 1 - dist / 260));
        });
      });
    });
    top.addEventListener("mouseleave", function () {
      if (pg) { pg.style.setProperty("--go", "0"); gon = false; }
      if (hraf) { cancelAnimationFrame(hraf); hraf = 0; }
      chars.forEach(function (c) { setW(c, 0); });
    });
  }

  /* Image viewer */
  var lb = null, lbX = null, lbSkip = 0;
  function media(el) { return $$("img, video", el).filter(function (m) { return !m.classList.contains("fl") && !m.classList.contains("dt"); }); }
  function keyOf(m) { return m.getAttribute("data-e-data-lbsrc") || m.getAttribute("data-e-src") || m.getAttribute("data-lbsrc") || m.currentSrc || m.src || m.getAttribute("src") || ""; }
  function full(it) { return window.__full ? window.__full(it.el) : Promise.resolve(it.el.getAttribute("data-lbsrc") || it.el.currentSrc || it.el.src); }
  function show(i) {
    if (!lb) return;
    var n = lb.list.length;
    i = ((i % n) + n) % n;
    lb.i = i;
    var it = lb.list[i], img = $(".stg img", lb.el), vid = $(".stg video", lb.el);
    img.classList.remove("ok");
    vid.classList.remove("ok");
    var cur = lb;
    if (it.vid) {
      img.style.display = "none";
      vid.style.display = "";
      vid.poster = it.el.poster || "";
      vid.muted = true;
      vid.setAttribute("aria-label", it.alt);
      vid.onloadedmetadata = function () { if (lb === cur && lb.i === i) lb.place(); };
    } else {
      try { vid.pause(); } catch (e) {}
      vid.style.display = "none";
      img.style.display = "";
      img.alt = it.alt;
    }
    full(it).then(function (url) {
      if (lb !== cur || lb.i !== i) return;
      if (it.vid) {
        vid.src = url;
        try { var p = vid.play(); if (p && p.catch) p.catch(function () {}); } catch (e) {}
        requestAnimationFrame(function () { vid.classList.add("ok"); });
      } else {
        img.onload = function () { img.classList.add("ok"); if (lb === cur && lb.i === i) lb.place(); };
        img.src = url;
        if (img.complete && img.naturalWidth) requestAnimationFrame(function () { img.classList.add("ok"); });
      }
    }).catch(function () {});
    var cp = $(".cp", lb.el);
    var add = function (to, cls, text) { if (!text) return null; var e = d.createElement("span"); e.className = cls; e.textContent = text; to.appendChild(e); return e; };
    cp.textContent = "";
    cp.classList.toggle("has", !!it.cap);
    if (it.cap) { var left = add(cp, "cl", " "); left.textContent = ""; add(left, "cn", it.cap[0]); add(left, "cm", it.cap[1]); }
    add(cp, "cc", (i + 1) + " / " + n);
    // With a caption, line the text up with the image's left and right edges
    lb.place = function () {
      cp.style.left = cp.style.right = cp.style.padding = "";
      var el = it.vid ? vid : img;
      if (!it.cap || window.innerWidth <= 700 || !el.offsetWidth) return;
      var l = el.offsetLeft, w = el.offsetWidth;
      if (it.vid) { var vw = Math.min(w, el.offsetHeight * (el.videoWidth || 16) / (el.videoHeight || 10)); l += (w - vw) / 2; w = vw; }
      cp.style.left = l + "px";
      cp.style.right = (el.offsetParent.clientWidth - l - w) + "px";
      cp.style.padding = "0";
    };
    lb.place();
    [lb.list[(i + 1) % n], lb.list[(i - 1 + n) % n]].forEach(function (o) { if (!o.vid) full(o).then(function (u) { new Image().src = u; }).catch(function () {}); });
  }
  function close() {
    if (!lb) return;
    var o = lb;
    lb = null;
    o.el.classList.remove("on");
    try { $(".stg video", o.el).pause(); } catch (e) {}
    root.style.overflow = o.ov;
    setTimeout(function () { if (o.el.parentNode) o.el.parentNode.removeChild(o.el); }, 320);
    try { o.from.focus({ preventScroll: true }); } catch (e) {}
  }
  function open(tr) {
    var pg = $(".pg"), first = media(tr)[0];
    if (lb || !pg || !first) return;
    var list = [], seen = {}, h1 = $("h1", pg), title = h1 ? h1.textContent.trim() : "";
    media(pg).forEach(function (m) {
      var key = keyOf(m);
      if (!key || seen[key] != null) return;
      seen[key] = list.length;
      var fc = m.closest ? m.closest("figure") : null;
      var sp = fc ? $$("figcaption span", fc) : [];
      list.push({ el: m, vid: m.tagName === "VIDEO", alt: m.getAttribute("alt") || m.getAttribute("aria-label") || "",
        cap: sp.length ? [sp[0].textContent, sp[1] ? sp[1].textContent : ""] : (title ? [title, ""] : null) });
    });
    var i = seen[keyOf(first)];
    if (i == null) return;
    var el = d.createElement("div");
    el.className = "lbx";
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-modal", "true");
    el.setAttribute("aria-label", "Image viewer");
    var cs = getComputedStyle(pg);
    el.style.background = cs.backgroundColor;
    el.style.color = cs.color;
    var ic = function (p) { return '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="' + p + '"></path></svg>'; };
    el.innerHTML = '<div class="stg"><img alt="" draggable="false"><video muted loop playsinline style="display:none"></video><button type="button" class="x" aria-label="Close">' + ic("M5 5l10 10M15 5L5 15") + '</button><button type="button" class="pv" aria-label="Previous image">' + ic("M12 4.5L6.5 10l5.5 5.5") + '</button><button type="button" class="nx" aria-label="Next image">' + ic("M8 4.5l5.5 5.5L8 15.5") + '</button><p class="cp" aria-live="polite"></p></div>';
    d.body.appendChild(el);
    lb = { el: el, list: list, i: i, from: tr, ov: root.style.overflow };
    root.style.overflow = "hidden";
    show(i);
    requestAnimationFrame(function () { requestAnimationFrame(function () { el.classList.add("on"); }); });
    try { $(".x", el).focus({ preventScroll: true }); } catch (e) {}
  }
  d.addEventListener("click", function (e) {
    var t = e.target;
    if (!t || !t.closest) return;
    if (lb) {
      if (Date.now() - lbSkip < 450 || !t.closest(".lbx")) return;
      if (t.closest(".pv")) show(lb.i - 1);
      else if (t.closest(".nx")) show(lb.i + 1);
      else if (t.closest(".x") || (!t.closest("img, video") && !t.closest(".cp"))) close();
      return;
    }
    var tr = t.closest("[data-lb]");
    if (tr) open(tr);
  });
  d.addEventListener("keydown", function (e) {
    if (lb) {
      if (e.key === "Escape") { e.preventDefault(); close(); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); show(lb.i - 1); }
      else if (e.key === "ArrowRight") { e.preventDefault(); show(lb.i + 1); }
      else if (e.key === "Tab") {
        var b = $$("button", lb.el), k = b.indexOf(d.activeElement);
        b[(k + (e.shiftKey ? -1 : 1) + b.length) % b.length].focus();
        e.preventDefault();
      }
      return;
    }
    var tr = e.target && e.target.closest ? e.target.closest("[data-lb]") : null;
    if (tr && e.target === tr && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); open(tr); }
  });
  window.addEventListener("resize", function () { if (lb && lb.place) lb.place(); });
  d.addEventListener("pointerdown", function (e) { if (lb) lbX = e.clientX; });
  window.addEventListener("pointerup", function (e) {
    if (!lb) return;
    if (lbX != null) { var dx = e.clientX - lbX; if (Math.abs(dx) > 50) { lbSkip = Date.now(); show(lb.i + (dx < 0 ? 1 : -1)); } }
    lbX = null;
  });
})();
