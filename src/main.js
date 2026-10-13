(function () {
  "use strict";
  var RM = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var FINE = window.matchMedia && window.matchMedia("(pointer: fine)").matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  // ---------- Countdown to midnight, 1 January 2027 in Sydney (AEDT, UTC+11) ----------
  var TARGET = Date.parse("2027-01-01T00:00:00+11:00");
  var pad = function (n) { return n < 10 ? "0" + n : String(n); };
  function setNum(el, v) {
    if (!el || el.textContent === v) return;
    el.textContent = v;
    if (RM) return;
    el.classList.remove("roll"); void el.offsetWidth; el.classList.add("roll");
  }
  function tick() {
    var diff = TARGET - Date.now();
    $$("[data-countdown]").forEach(function (el) {
      if (diff <= 0) {
        if (!el.dataset.done) { el.dataset.done = 1; el.innerHTML = '<span class="cd-n">Happy New Year 2027</span>'; }
        return;
      }
      setNum($('[data-u="d"]', el), String(Math.floor(diff / 864e5)));
      setNum($('[data-u="h"]', el), pad(Math.floor(diff / 36e5) % 24));
      setNum($('[data-u="m"]', el), pad(Math.floor(diff / 6e4) % 60));
      setNum($('[data-u="s"]', el), pad(Math.floor(diff / 1e3) % 60));
    });
  }
  tick();
  setInterval(tick, 1000);

  // ---------- Nav: solid once the page scrolls, mobile menu ----------
  var nav = $("[data-nav]"), sentinel = $(".nav-sentinel");
  if (nav && sentinel && "IntersectionObserver" in window) {
    new IntersectionObserver(function (en) { nav.classList.toggle("is-solid", !en[0].isIntersecting); }).observe(sentinel);
  }
  var menuBtn = $(".menu-btn"), menu = $("#menu");
  if (menuBtn && menu) {
    menuBtn.addEventListener("click", function () {
      var open = menu.classList.toggle("open");
      menuBtn.setAttribute("aria-expanded", open);
      menuBtn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      if (nav) nav.classList.toggle("is-solid", open || window.scrollY > 100);
    });
    menu.addEventListener("click", function (e) { if (e.target.closest("a")) { menu.classList.remove("open"); menuBtn.setAttribute("aria-expanded", "false"); } });
  }

  // ---------- Scroll reveals (IntersectionObserver, once) ----------
  var reveals = $$(".reveal");
  function settle(el) {
    var i = parseFloat(getComputedStyle(el).getPropertyValue("--i")) || 0;
    setTimeout(function () { el.classList.add("settled"); }, 850 + i * 70);
  }
  if ("IntersectionObserver" in window && !RM) {
    var rio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("in"); settle(en.target); rio.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });
    reveals.forEach(function (el) { rio.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("in", "settled"); });
  }

  // ---------- Fireworks engine ----------
  var PALETTE = ["#f2c46b", "#ffe2a8", "#fff6e6", "#e8955a", "#d9b26a", "#f7d58f"];
  function Fireworks(canvas, opts) {
    this.c = canvas; this.ctx = canvas.getContext("2d"); this.o = opts || {};
    this.rockets = []; this.sparks = []; this.running = false; this.visible = true; this.auto = this.o.auto || 0;
    var self = this;
    this.resize = function () {
      var r = Math.min(window.devicePixelRatio || 1, 2);
      self.W = canvas.clientWidth; self.H = canvas.clientHeight;
      canvas.width = self.W * r; canvas.height = self.H * r; self.ctx.setTransform(r, 0, 0, r, 0, 0);
    };
    this.resize();
    window.addEventListener("resize", this.resize);
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (en) { self.visible = en[0].isIntersecting; if (self.visible) self.start(); }).observe(canvas);
    }
    document.addEventListener("visibilitychange", function () { if (!document.hidden) self.start(); });
  }
  Fireworks.prototype.horizon = function () { return this.o.reflect ? this.H * (1 - this.o.reflect) : this.H; };
  Fireworks.prototype.launch = function (x, ty, type) {
    var hz = this.horizon();
    x = x != null ? x : this.W * (this.o.xMin || 0.1) + Math.random() * this.W * ((this.o.xMax || 0.9) - (this.o.xMin || 0.1));
    ty = ty != null ? ty : hz * (0.14 + Math.random() * 0.4);
    var dist = hz - ty;
    this.rockets.push({ x: x, y: hz, ty: ty, vx: (Math.random() - 0.5) * 0.6, vy: -Math.sqrt(2 * 0.06 * dist) * 1.05,
      c: PALETTE[(Math.random() * PALETTE.length) | 0], type: type || (Math.random() < 0.35 ? "willow" : Math.random() < 0.3 ? "ring" : "peony") });
    this.start();
  };
  Fireworks.prototype.burst = function (r) {
    var n = r.type === "willow" ? 90 : r.type === "ring" ? 64 : 110;
    var scale = Math.min(1.25, Math.max(0.65, this.W / 900));
    for (var i = 0; i < n; i++) {
      var a = (Math.PI * 2 * i) / n + Math.random() * 0.05;
      var sp = (r.type === "ring" ? 3.3 : r.type === "willow" ? 1.6 + Math.random() * 2.4 : 0.6 + Math.random() * 4.2) * scale;
      this.sparks.push({ x: r.x, y: r.y, px: r.x, py: r.y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, life: 1,
        decay: r.type === "willow" ? 0.006 + Math.random() * 0.004 : 0.011 + Math.random() * 0.012,
        g: r.type === "willow" ? 0.045 : 0.03, drag: r.type === "willow" ? 0.975 : 0.982,
        c: Math.random() < 0.18 ? "#fff6e6" : r.c, w: r.type === "willow" ? 1.4 : 1.8 });
    }
  };
  Fireworks.prototype.show = function (kind) {
    var self = this, n = kind === "midnight" ? 22 : 7, span = kind === "midnight" ? 3200 : 1600;
    for (var i = 0; i < n; i++) {
      (function (k) {
        setTimeout(function () {
          var t = kind === "midnight" && k > n - 6 ? "willow" : null;
          self.launch(self.W * (0.12 + Math.random() * 0.76), null, t);
        }, (k / n) * span + Math.random() * 120);
      })(i);
    }
  };
  Fireworks.prototype.start = function () {
    if (this.running || !this.visible || document.hidden) return;
    this.running = true; this.last = 0;
    var self = this;
    requestAnimationFrame(function f(t) { if (self.frame(t)) requestAnimationFrame(f); else self.running = false; });
  };
  Fireworks.prototype.frame = function (t) {
    var ctx = this.ctx, W = this.W, H = this.H, hz = this.horizon();
    if (!this.visible || document.hidden) return false;
    if (this.auto && t - (this.last || 0) > this.auto) { this.last = t + Math.random() * this.auto * 0.6; this.launch(); }
    ctx.globalCompositeOperation = "destination-out";
    ctx.fillStyle = "rgba(0,0,0,0.2)"; ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = "lighter";
    for (var i = this.rockets.length - 1; i >= 0; i--) {
      var r = this.rockets[i]; r.x += r.vx; r.y += r.vy; r.vy += 0.06;
      ctx.globalAlpha = 0.9; ctx.fillStyle = r.c; ctx.beginPath(); ctx.arc(r.x, r.y, 1.6, 0, 6.3); ctx.fill();
      ctx.globalAlpha = 0.35; ctx.beginPath(); ctx.arc(r.x - r.vx * 2, r.y - r.vy * 2, 1.2, 0, 6.3); ctx.fill();
      if (r.y <= r.ty || r.vy >= -0.4) { this.burst(r); this.rockets.splice(i, 1); }
    }
    ctx.lineCap = "round";
    for (var j = this.sparks.length - 1; j >= 0; j--) {
      var s = this.sparks[j];
      s.px = s.x; s.py = s.y; s.x += s.vx; s.y += s.vy; s.vx *= s.drag; s.vy = s.vy * s.drag + s.g; s.life -= s.decay;
      if (s.life <= 0 || s.y > hz) { this.sparks.splice(j, 1); continue; }
      var a = s.life * (s.life > 0.3 || Math.random() > 0.3 ? 1 : 0.2);
      ctx.globalAlpha = a; ctx.strokeStyle = s.c; ctx.lineWidth = s.w;
      ctx.beginPath(); ctx.moveTo(s.px, s.py); ctx.lineTo(s.x, s.y); ctx.stroke();
      if (this.o.reflect) {
        var ry = hz + (hz - s.y) * 0.55, wob = Math.sin(s.y * 0.08 + t * 0.004) * 3;
        if (ry < H) { ctx.globalAlpha = a * 0.28; ctx.beginPath(); ctx.moveTo(s.px + wob, hz + (hz - s.py) * 0.55); ctx.lineTo(s.x + wob, ry); ctx.stroke(); }
      }
    }
    ctx.globalAlpha = 1;
    return this.auto || this.rockets.length || this.sparks.length;
  };

  if (!RM) {
    // Hero: gentle ambient bursts over the photo, kept to the right of the headline. Click to launch your own.
    $$(".hero [data-fireworks]").forEach(function (cv) {
      var wide = window.innerWidth > 900;
      var fw = new Fireworks(cv, { auto: 1500, xMin: wide ? 0.5 : 0.1, xMax: 0.94 });
      setTimeout(function () { fw.launch(); }, 700);
      cv.closest(".hero").addEventListener("click", function (e) {
        if (e.target.closest("a,button,input,select,label")) return;
        var rect = cv.getBoundingClientRect();
        fw.launch(e.clientX - rect.left, Math.max(40, e.clientY - rect.top));
      });
    });
  }

  // ---------- Night story: sky shifts and fireworks fire as you scroll through the timeline ----------
  var stage = $(".stage");
  if (stage) {
    var storyFw = !RM && $("[data-fireworks]", stage) ? new Fireworks($("[data-fireworks]", stage), { reflect: 0.3 }) : null;
    var clock = $("[data-stage-clock]", stage), steps = $$("[data-step]");
    var activate = function (st) {
      steps.forEach(function (s) { s.classList.toggle("on", s === st); });
      stage.setAttribute("data-sky", st.dataset.sky);
      if (clock && clock.textContent !== st.dataset.clock) {
        clock.textContent = st.dataset.clock;
        if (!RM) { clock.classList.remove("roll"); void clock.offsetWidth; clock.classList.add("roll"); }
      }
      if (storyFw && st.dataset.burst) storyFw.show(st.dataset.burst);
    };
    stage.setAttribute("data-sky", "0");
    if (steps[0]) steps[0].classList.add("on");
    if ("IntersectionObserver" in window) {
      var sio = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { if (en.isIntersecting) activate(en.target); });
      }, { rootMargin: "-48% 0px -48% 0px" });
      steps.forEach(function (s) { sio.observe(s); });
    }
  }

  // ---------- Featured rail ----------
  var track = $("[data-rail-track]");
  $$("[data-rail]").forEach(function (b) {
    b.addEventListener("click", function () {
      if (track) track.scrollBy({ left: parseInt(b.dataset.rail, 10) * track.clientWidth * 0.8, behavior: RM ? "auto" : "smooth" });
    });
  });

  // ---------- Card spotlight (fine pointers only) ----------
  if (FINE && !RM) {
    document.addEventListener("pointermove", function (e) {
      var card = e.target.closest && e.target.closest(".ev");
      if (!card) return;
      var r = card.getBoundingClientRect();
      card.style.setProperty("--mx", (e.clientX - r.left) + "px");
      card.style.setProperty("--my", (e.clientY - r.top) + "px");
    }, { passive: true });
  }

  // ---------- Directory filters ----------
  var dir = $("[data-directory]");
  if (dir && $(".chips", dir)) {
    var cards = $$(".ev", dir), grid = $(".ev-grid", dir), q = $("#q", dir), area = $("#area", dir), sort = $("#sort", dir),
        countEl = $(".count", dir), empty = $(".empty", dir), cat = "all";
    var apply = function () {
      var term = (q.value || "").trim().toLowerCase(), a = area.value, shown = 0;
      cards.forEach(function (c) {
        var ok = (cat === "all" || c.dataset.cats.split(" ").indexOf(cat) > -1) && (a === "all" || c.dataset.area === a) &&
                 (!term || c.dataset.search.indexOf(term) > -1);
        c.hidden = !ok; if (ok) shown++;
        if (ok) c.classList.add("in", "settled");
      });
      var key = sort.value;
      cards.slice().sort(function (x, y) {
        if (key === "featured") return (y.dataset.featured - x.dataset.featured) || (x.dataset.order - y.dataset.order);
        var px = parseFloat(x.dataset.price), py = parseFloat(y.dataset.price);
        if (isNaN(px)) px = key === "low" ? 1e9 : -1; if (isNaN(py)) py = key === "low" ? 1e9 : -1;
        return key === "low" ? px - py : py - px;
      }).forEach(function (c) { grid.appendChild(c); });
      countEl.textContent = shown + " event" + (shown === 1 ? "" : "s");
      empty.style.display = shown ? "none" : "block";
    };
    var run = function () {
      if (document.startViewTransition && !RM) document.startViewTransition(apply); else apply();
    };
    $$(".chip", dir).forEach(function (ch) {
      ch.addEventListener("click", function () {
        $$(".chip", dir).forEach(function (o) { o.setAttribute("aria-pressed", "false"); });
        ch.setAttribute("aria-pressed", "true"); cat = ch.dataset.cat; run();
      });
    });
    var debounce;
    q.addEventListener("input", function () { clearTimeout(debounce); debounce = setTimeout(apply, 120); });
    area.addEventListener("change", run); sort.addEventListener("change", run);
    var params = new URLSearchParams(location.search);
    if (params.get("q")) q.value = params.get("q");
    if (params.get("area")) { area.value = params.get("area"); if (area.value !== params.get("area")) area.value = "all"; }
    if (params.get("cat")) { var pre = $('.chip[data-cat="' + params.get("cat") + '"]', dir); if (pre) { $$(".chip", dir).forEach(function (o) { o.setAttribute("aria-pressed", "false"); }); pre.setAttribute("aria-pressed", "true"); cat = pre.dataset.cat; } }
    apply();
    // Marquee area links on the same page filter in place instead of reloading.
    $$(".marquee a").forEach(function (l) {
      l.addEventListener("click", function (e) {
        if (location.pathname !== "/") return;
        var v = new URL(l.href).searchParams.get("area"); if (!v) return;
        e.preventDefault(); area.value = v; run();
        history.replaceState(null, "", "/?area=" + encodeURIComponent(v) + "#directory");
        dir.scrollIntoView({ behavior: RM ? "auto" : "smooth" });
      });
    });
  }

  // ---------- Vantage map (Leaflet, CARTO dark tiles) ----------
  var mapEl = $("#vmap"), dataEl = $("#vp-data");
  if (mapEl && dataEl && window.L) {
    var pts = JSON.parse(dataEl.textContent), L = window.L;
    var map = L.map(mapEl, { scrollWheelZoom: false, zoomSnap: 0.5 });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, className: "tiles-dark",
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    var btns = $$(".vp"), markers = [];
    var select = function (i, fly) {
      btns.forEach(function (b, k) { b.classList.toggle("on", k === i); });
      markers.forEach(function (m, k) { var el = m.getElement && m.getElement(); if (el) el.firstChild.classList.toggle("on", k === i); });
      if (fly) map.flyTo([pts[i].lat, pts[i].lng], 15, { duration: RM ? 0 : 1.1 });
      markers[i].openPopup();
    };
    pts.forEach(function (p, i) {
      var m = L.marker([p.lat, p.lng], {
        icon: L.divIcon({ className: "", html: '<span class="mk mk--' + p.k + '"></span>', iconSize: [16, 16], iconAnchor: [8, 8] }),
        title: p.n, alt: p.n
      }).addTo(map).bindPopup("<b>" + p.n + "</b><br>" + p.a + ". " + p.t + "<br>" + p.note);
      m.on("click", function () { select(i, false); btns[i].scrollIntoView({ block: "nearest", behavior: RM ? "auto" : "smooth" }); });
      markers.push(m);
    });
    map.fitBounds(L.latLngBounds(pts.map(function (p) { return [p.lat, p.lng]; })), { padding: [30, 30] });
    btns.forEach(function (b) { b.addEventListener("click", function () { select(parseInt(b.dataset.vp, 10), true); }); });
  }

  // ---------- Listing form: email the details, then go to payment if configured ----------
  var form = $("form.listing");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var endpoint = form.dataset.endpoint, pay = form.dataset.payment, status = $(".form-status", form), btn = $("button[type=submit]", form);
      btn.disabled = true; status.textContent = "Sending your listing request…";
      fetch(endpoint, { method: "POST", body: new FormData(form), headers: { Accept: "application/json" } })
        .then(function (r) {
          if (!r.ok) throw new Error();
          if (!pay || pay.indexOf("YOUR_") > -1) {
            form.reset();
            status.textContent = "Thanks! Your listing request has been sent. We'll email you within one business day with your invoice and next steps.";
            btn.disabled = false; return;
          }
          status.textContent = "Done. Taking you to secure checkout…";
          var email = encodeURIComponent(($("[name=email]", form) || {}).value || "");
          window.location.href = pay + (pay.indexOf("?") > -1 ? "&" : "?") + "prefilled_email=" + email;
        })
        .catch(function () { status.textContent = "Something went wrong. Please email us at " + form.dataset.email; btn.disabled = false; });
    });
  }
})();

// ---------- Floating WhatsApp + email contact, and email/WhatsApp choice on the listing form ----------
(function () {
  var WA = "61488898835";
  var ENDPOINT = "https://formsubmit.co/ajax/aj@metatapdigital.com";
  var EMAIL = "aj@metatapdigital.com";
  var logo = document.querySelector(".logo");
  var SITE = logo ? logo.textContent.replace(/\s+/g, " ").trim() : document.title;
  var waLink = function (text) { return "https://wa.me/" + WA + "?text=" + encodeURIComponent(text); };
  var WA_ICON = '<svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true"><path fill="currentColor" d="M16 3C9 3 3.3 8.6 3.3 15.6c0 2.4.7 4.7 1.9 6.6L3 29l7-2.2c1.8 1 3.9 1.6 6 1.6 7 0 12.7-5.6 12.7-12.6S23 3 16 3zm0 23.1c-1.9 0-3.8-.5-5.4-1.5l-.4-.2-4.1 1.3 1.3-4-.3-.4c-1.1-1.7-1.7-3.6-1.7-5.6C5.4 9.9 10.1 5.3 16 5.3s10.6 4.6 10.6 10.4S21.9 26.1 16 26.1zm5.8-7.8c-.3-.2-1.9-.9-2.2-1-.3-.1-.5-.2-.7.2-.2.3-.8 1-1 1.2-.2.2-.4.2-.7.1-.3-.2-1.3-.5-2.6-1.6-1-.9-1.6-1.9-1.8-2.2-.2-.3 0-.5.1-.7l.5-.6c.2-.2.2-.4.3-.6.1-.2 0-.4 0-.6l-1-2.4c-.3-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.4-.3.3-1.2 1.1-1.2 2.7s1.2 3.1 1.4 3.4c.2.2 2.4 3.6 5.7 5 .8.3 1.4.5 1.9.7.8.3 1.5.2 2.1.1.6-.1 1.9-.8 2.2-1.5.3-.7.3-1.4.2-1.5-.1-.2-.3-.3-.6-.4z"/></svg>';
  var MAIL_ICON = '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path fill="currentColor" d="M3 5h18a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm1 2.4V17h16V7.4l-8 5.3-8-5.3zM5.4 7l6.6 4.4L18.6 7H5.4z"/></svg>';

  // Floating buttons
  var box = document.createElement("div");
  box.className = "cf";
  box.innerHTML =
    '<div class="cf-panel" id="cf-panel" role="dialog" aria-modal="false" aria-labelledby="cf-title" hidden>' +
      '<button type="button" class="cf-close" aria-label="Close">×</button>' +
      '<h3 id="cf-title">Send us a message</h3>' +
      '<p class="muted">Questions about an event or listing on ' + SITE + '? We reply within one business day.</p>' +
      '<form class="cf-form">' +
        '<label for="cf-name">Name *</label><input id="cf-name" name="name" required autocomplete="name">' +
        '<label for="cf-email">Email *</label><input id="cf-email" name="email" type="email" required autocomplete="email">' +
        '<label for="cf-phone">Phone</label><input id="cf-phone" name="phone" type="tel" autocomplete="tel">' +
        '<label for="cf-msg">Message *</label><textarea id="cf-msg" name="message" required rows="4"></textarea>' +
        '<input type="hidden" name="_subject" value="New enquiry from ' + SITE + '">' +
        '<input type="hidden" name="_template" value="table">' +
        '<input type="text" name="_honey" style="display:none" tabindex="-1" autocomplete="off" aria-hidden="true">' +
        '<button class="btn btn-gold" type="submit">Send message</button>' +
        '<p class="cf-status muted" aria-live="polite"></p>' +
      '</form>' +
    '</div>' +
    '<button type="button" class="cf-btn cf-mail" aria-label="Email us" aria-controls="cf-panel" aria-expanded="false">' + MAIL_ICON + '</button>' +
    '<a class="cf-btn cf-wa" aria-label="Chat on WhatsApp" target="_blank" rel="noopener" href="' + waLink("Hi, I'm getting in touch from " + SITE + ".") + '">' + WA_ICON + '</a>';
  document.body.appendChild(box);

  var panel = box.querySelector(".cf-panel"), mailBtn = box.querySelector(".cf-mail");
  var toggle = function (open) {
    panel.hidden = !open; mailBtn.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) { var f = panel.querySelector("input"); if (f) f.focus(); }
  };
  mailBtn.addEventListener("click", function () { toggle(panel.hidden); });
  box.querySelector(".cf-close").addEventListener("click", function () { toggle(false); mailBtn.focus(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !panel.hidden) { toggle(false); mailBtn.focus(); } });

  var cform = box.querySelector(".cf-form");
  cform.addEventListener("submit", function (e) {
    e.preventDefault();
    var st = cform.querySelector(".cf-status"), b = cform.querySelector("button[type=submit]");
    b.disabled = true; st.textContent = "Sending…";
    fetch(ENDPOINT, { method: "POST", body: new FormData(cform), headers: { Accept: "application/json" } })
      .then(function (r) { if (!r.ok) throw new Error(); cform.reset(); st.textContent = "Thanks, your message has been sent. We'll be in touch soon."; b.disabled = false; })
      .catch(function () { st.innerHTML = 'Something went wrong. Please email <a href="mailto:' + EMAIL + '">' + EMAIL + '</a> or message us on WhatsApp.'; b.disabled = false; });
  });

  // Listing form: let buyers choose email or WhatsApp
  var lf = document.querySelector("form.listing");
  if (lf) {
    var sub = lf.querySelector("button[type=submit]");
    if (sub) {
      var paid = /payment/i.test(sub.textContent);
      sub.innerHTML = MAIL_ICON + "<span>" + (paid ? "Email &amp; pay by card" : "Send by email") + "</span>";
      var wa = document.createElement("button");
      wa.type = "button"; wa.className = "btn btn-wa";
      wa.innerHTML = WA_ICON + "<span>Send by WhatsApp</span>";
      var row = document.createElement("div"); row.className = "send-choice";
      var hint = document.createElement("p"); hint.className = "muted send-hint";
      hint.textContent = "Choose how to send your listing: email, or WhatsApp us on +61 488 898 835.";
      sub.parentNode.insertBefore(hint, sub);
      sub.parentNode.insertBefore(row, sub);
      row.appendChild(sub); row.appendChild(wa);
      wa.addEventListener("click", function () {
        if (!lf.reportValidity()) return;
        var skip = { _subject: 1, _template: 1, _honey: 1 };
        var lines = ["Hi, I'd like to list my event on " + SITE + ".", ""];
        Array.from(new FormData(lf).entries()).forEach(function (p) {
          if (skip[p[0]] || !String(p[1]).trim()) return;
          var k = p[0].replace(/_/g, " "); lines.push(k.charAt(0).toUpperCase() + k.slice(1) + ": " + p[1]);
        });
        window.open(waLink(lines.join("\n")), "_blank", "noopener");
        var st = lf.querySelector(".form-status");
        if (st) st.textContent = "WhatsApp should open with your details filled in. Press send and we'll reply with your invoice.";
      });
    }
  }
})();
