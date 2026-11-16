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
    try { localStorage.setItem("theme", next); } catch (e) {}
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
      if (r.top < h * rvt && r.bottom > 0) { el.classList.add("in"); if (el.hasAttribute("data-sl")) nudge(); }
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
    top.addEventListener("mousemove", function (e) {
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
      if (hraf) { cancelAnimationFrame(hraf); hraf = 0; }
      chars.forEach(function (c) { setW(c, 0); });
    });
  }

  /* Before/after slider */
  var sl = $("[data-sl]"), pos = 50, drag = null, pend = null, n1, n2, n3;
  function setPos(p, ez) {
    pos = Math.max(0, Math.min(100, p));
    sl.classList.toggle("ez", !!ez);
    $(".bf", sl).style.clipPath = "inset(0 " + (100 - pos).toFixed(3) + "% 0 0)";
    $(".hd", sl).style.left = pos.toFixed(3) + "%";
    var tg = $$(".tg", sl);
    tg[0].style.opacity = pos > 12 ? 1 : 0;
    tg[1].style.opacity = pos < 88 ? 1 : 0;
    $(".kb", sl).setAttribute("aria-valuenow", String(Math.round(pos)));
  }
  function posAt(x) { var r = sl.getBoundingClientRect(); if (r.width) setPos(((x - r.left) / r.width) * 100, false); }
  function nudge() {
    if (still || !sl) return;
    n1 = setTimeout(function () { setPos(64, true); }, 700);
    n2 = setTimeout(function () { setPos(50, true); }, 1800);
    n3 = setTimeout(function () { sl.classList.remove("ez"); }, 2900);
  }
  if (sl) {
    d.addEventListener("pointerdown", function (e) {
      if (lb || !e.target.closest || !e.target.closest("[data-sl]")) return;
      clearTimeout(n1); clearTimeout(n2); clearTimeout(n3);
      if (e.pointerType === "mouse") { drag = sl; posAt(e.clientX); e.preventDefault(); return; }
      pend = { x: e.clientX, y: e.clientY };
    });
    window.addEventListener("pointermove", function (e) {
      if (pend) {
        var dx = Math.abs(e.clientX - pend.x), dy = Math.abs(e.clientY - pend.y);
        if (dx > 6 && dx > dy) { drag = sl; pend = null; }
        else if (dy > 10) pend = null;
      }
      if (drag) posAt(e.clientX);
    });
    var end = function (e) { if (pend && e.type === "pointerup") posAt(e.clientX); pend = null; drag = null; };
    window.addEventListener("pointerup", end);
    window.addEventListener("pointercancel", end);
    d.addEventListener("keydown", function (e) {
      if (lb || !e.target.closest || !e.target.closest("[data-kb]")) return;
      var k = { ArrowLeft: -4, ArrowRight: 4, Home: -100, End: 100 }[e.key];
      if (!k) return;
      e.preventDefault();
      setPos(pos + k, false);
    });
  }

  /* Image viewer */
  var lb = null, lbX = null, lbSkip = 0;
  function media(el) { return $$("img, video", el).filter(function (m) { return !m.classList.contains("fl") && !m.classList.contains("dt"); }); }
  function srcOf(m) { return m.getAttribute("data-lbsrc") || m.currentSrc || m.src || m.getAttribute("src") || ""; }
  function show(i) {
    if (!lb) return;
    var n = lb.list.length;
    i = ((i % n) + n) % n;
    lb.i = i;
    var it = lb.list[i], img = $(".stg img", lb.el), vid = $(".stg video", lb.el);
    img.classList.remove("ok");
    vid.classList.remove("ok");
    if (it.vid) {
      img.style.display = "none";
      vid.style.display = "";
      vid.poster = it.poster;
      vid.src = it.src;
      vid.muted = true;
      vid.setAttribute("aria-label", it.alt);
      try { var p = vid.play(); if (p && p.catch) p.catch(function () {}); } catch (e) {}
      requestAnimationFrame(function () { vid.classList.add("ok"); });
    } else {
      try { vid.pause(); } catch (e) {}
      vid.style.display = "none";
      img.style.display = "";
      img.onload = function () { img.classList.add("ok"); };
      img.alt = it.alt;
      img.src = it.src;
      if (img.complete && img.naturalWidth) requestAnimationFrame(function () { img.classList.add("ok"); });
    }
    $(".cp", lb.el).textContent = (i + 1) + " / " + n;
    [lb.list[(i + 1) % n], lb.list[(i - 1 + n) % n]].forEach(function (o) { if (!o.vid) new Image().src = o.src; });
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
    var list = [], seen = {};
    media(pg).forEach(function (m) {
      var src = srcOf(m);
      if (!src || seen[src] != null) return;
      seen[src] = list.length;
      list.push({ src: src, vid: m.tagName === "VIDEO", poster: m.getAttribute("poster") || "", alt: m.getAttribute("alt") || m.getAttribute("aria-label") || "" });
    });
    var i = seen[srcOf(first)];
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
  d.addEventListener("pointerdown", function (e) { if (lb) lbX = e.clientX; });
  window.addEventListener("pointerup", function (e) {
    if (!lb) return;
    if (lbX != null) { var dx = e.clientX - lbX; if (Math.abs(dx) > 50) { lbSkip = Date.now(); show(lb.i + (dx < 0 ? 1 : -1)); } }
    lbX = null;
  });
})();
