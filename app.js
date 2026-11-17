/* Poker4 integrated dashboard — generated data is read from window.POKER4 (inlined)
   and data/search-index.json. No third-party endpoints are called. */
(function () {
  "use strict";
  var D = window.POKER4 || null;
  var IS_VENUE = /\/venues\//.test(location.pathname);
  var BASE = IS_VENUE ? "../" : "";
  var TAX = 0.1338;

  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }

  /* ---------------------------------------------------------------- tabs */
  $$(".tab").forEach(function (t) {
    t.addEventListener("click", function () {
      var name = t.getAttribute("data-tab");
      $$(".tab").forEach(function (x) { x.classList.toggle("active", x === t); });
      $$(".tabpanel").forEach(function (p) {
        p.classList.toggle("active", p.getAttribute("data-panel") === name);
      });
      applyFilters();
    });
  });

  /* -------------------------------------------------- event row disclosure */
  document.addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest(".disclose") : null;
    if (!b) return;
    var row = b.closest("tr.ev-row");
    var det = row && row.nextElementSibling;
    if (!det || !det.classList.contains("ev-detail")) return;
    var open = det.hasAttribute("hidden");
    if (open) { det.removeAttribute("hidden"); } else { det.setAttribute("hidden", ""); }
    b.setAttribute("aria-expanded", open ? "true" : "false");
    b.textContent = open ? "hide source text" : "source text";
  });

  /* -------------------------------------------------------------- filters */
  var byId = {};
  if (D && D.events) { D.events.forEach(function (ev) { byId[ev.id] = ev; }); }
  if (D && D.rowmeta) {
    Object.keys(D.rowmeta).forEach(function (k) {
      var m = D.rowmeta[k];
      byId[k] = { rankable: m.rankable, rules: { fee: { status: m.fee } }, single_entry_confirmed: m.single };
    });
  }

  function activePanelRows() {
    var panel = $(".tabpanel.active");
    return $$(panel ? "tr.ev-row" : ".nope", panel || document);
  }

  function val(id) { var el = $("#" + id); return el ? el.value : ""; }
  function chk(id) { var el = $("#" + id); return el ? el.checked : false; }

  function applyFilters() {
    var from = val("f-from"), to = val("f-to"), venue = val("f-venue");
    var singleOnly = chk("f-single"), hideUnconf = chk("f-hide-unconfirmed");
    var shown = 0, undated = 0, total = 0;
    activePanelRows().forEach(function (tr) {
      total++;
      var ev = byId[tr.getAttribute("data-id")] || {};
      var date = tr.getAttribute("data-date") || "";
      var ok = true;
      if (venue && tr.getAttribute("data-venue") !== venue) ok = false;
      if (ok && (from || to)) {
        if (!date) { ok = false; undated++; }
        else { if (from && date < from) ok = false; if (to && date > to) ok = false; }
      }
      if (ok && singleOnly && tr.getAttribute("data-single") !== "1") ok = false;
      if (ok && hideUnconf && !ev.rankable && !(ev.rules && ev.rules.fee && ev.rules.fee.status === "confirmed") && !ev.guarantee_usd) ok = false;
      tr.style.display = ok ? "" : "none";
      var det = tr.nextElementSibling;
      if (det && det.classList.contains("ev-detail")) {
        det.style.display = ok ? "" : "none";
        if (!ok) det.setAttribute("hidden", "");
      }
      if (ok) shown++;
    });
    var c = $("#f-count");
    if (c) {
      c.textContent = (total === 0 ? "no rows in this tab" : shown + " of " + total + " rows shown") +
        (undated ? " (" + undated + " row(s) hidden: no date printed on the calendar)" : "");
    }
  }

  ["f-from", "f-to", "f-venue", "f-single", "f-hide-unconfirmed"].forEach(function (id) {
    var el = $("#" + id);
    if (el) { el.addEventListener("change", applyFilters); el.addEventListener("input", applyFilters); }
  });
  $$(".btn-mini[data-preset]").forEach(function (b) {
    b.addEventListener("click", function () {
      var from = new Date(), to;
      if (b.getAttribute("data-preset") === "all") {
        setDates("2026-11-16", "2026-12-23"); return;
      }
      var span = parseInt(b.getAttribute("data-preset"), 10);
      from.setHours(0, 0, 0, 0);
      to = new Date(from.getTime() + span * 864e5);
      setDates(iso(from), iso(to));
    });
  });
  function iso(d) { return d.toISOString().slice(0, 10); }
  function setDates(a, b) {
    var f = $("#f-from"), t = $("#f-to");
    if (f) f.value = a;
    if (t) t.value = b;
    applyFilters();
  }
  if ($(".filters")) applyFilters();

  /* --------------------------------------------------------------- search */
  var searchInput = $("#global-search"), box = $("#search-results");
  var index = null;
  function loadIndex(cb) {
    if (index) return cb();
    fetch(BASE + "data/search-index.json").then(function (r) {
      if (!r.ok) throw 0;
      return r.json();
    }).then(function (j) { index = j.items || []; cb(); })
      .catch(function () {
        index = [];
        if (D && D.events) {
          D.events.forEach(function (e) {
            index.push({ t: e.name, u: "tournaments.html#" + e.id, k: "event", s: e.venue_name });
          });
        }
        cb();
      });
  }
  function render(q) {
    if (!q || q.length < 2) { box.setAttribute("hidden", ""); return; }
    var needle = q.toLowerCase();
    var hits = (index || []).filter(function (it) {
      return (it.t + " " + (it.s || "") + " " + (it.k || "")).toLowerCase().indexOf(needle) > -1;
    }).slice(0, 25);
    box.innerHTML = hits.length
      ? hits.map(function (h) {
          var href = h.u.indexOf("http") === 0 ? h.u : BASE + h.u.replace(/^\.\.\//, "");
          return "<a href='" + href + "'><b class='kind'>" + esc(h.k) + "</b><b>" + esc(h.t) + "</b><i>" + esc(h.s || "") + "</i></a>";
        }).join("")
      : "<a><i>no match in the captured official data — the search covers events, hotels, flags, questions and official sources</i></a>";
    box.removeAttribute("hidden");
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  if (searchInput) {
    searchInput.addEventListener("input", function () { loadIndex(function () { render(searchInput.value.trim()); }); });
    document.addEventListener("click", function (e) {
      if (!e.target.closest || !e.target.closest(".searchbox")) box.setAttribute("hidden", "");
    });
  }

  /* ------------------------------------------------- hotel walk filter (≤30 min) */
  var wf = $("#walk-filter");
  if (wf) {
    var cards = $$(".hotel"), wc = $("#walk-count");
    function applyWalk() {
      var mode = (wf.querySelector("input[name=walkf]:checked") || {}).value || "all";
      var shown = 0, provable = 0;
      cards.forEach(function (el) {
        var ok = true;
        if (mode === "onsite") ok = el.getAttribute("data-onsite") === "1";
        else if (mode === "measured") {
          var m = parseInt(el.getAttribute("data-walk-min"), 10);
          ok = !isNaN(m) && m <= 30;
        }
        el.classList.toggle("hidden", !ok);
        if (ok) shown++;
        if (!isNaN(parseInt(el.getAttribute("data-walk-min"), 10))) provable++;
      });
      if (wc) {
        wc.textContent = shown + " of " + cards.length + " properties" +
          (mode === "measured" && !provable ? " — no property has an official measured walking time yet, so nothing passes this filter" : "");
      }
    }
    $$("input[name=walkf]", wf).forEach(function (r) { r.addEventListener("change", applyWalk); });
    applyWalk();
  }

  /* -------------------------------------------------------- deep-link rows */
  if (location.hash) {
    var row = $("tr[data-id='" + CSS.escape(location.hash.slice(1)) + "']");
    if (row) {
      row.classList.add("hl");
      var det = row.nextElementSibling;
      if (det && det.classList.contains("ev-detail")) {
        det.removeAttribute("hidden");
        var btn = $(".disclose", row);
        if (btn) { btn.textContent = "hide source text"; btn.setAttribute("aria-expanded", "true"); }
      }
      setTimeout(function () { row.scrollIntoView({ block: "center" }); }, 30);
    }
  }

  /* ----------------------------------------------------------- calculator */
  var calc = $("#calc");
  if (calc && D && D.hotels) {
    var hotels = D.hotels || [];
    var hSel = $("#calc-hotel"), rSel = $("#calc-rate"), fSel = $("#calc-fee"),
        pSel = $("#calc-park"), nIn = $("#calc-nights"), rIn = $("#calc-rooms");

    function hotelFor(id) {
      for (var i = 0; i < hotels.length; i++) if (hotels[i].id === id) return hotels[i];
      return hotels[0];
    }
    function fillRates(h) {
      var keep = rSel.value;
      rSel.innerHTML = "<option value=''>no official dated rate for this property</option>";
      (h.rate_log || []).forEach(function (e, i) {
        if (!e.amount_usd) return;
        var o = document.createElement("option");
        o.value = String(e.amount_usd);
        o.textContent = e.amount_usd + " USD · " + (e.observed_on || "date not stated") + " · " +
          String(e.label || e.qualifier || "").slice(0, 58);
        o.setAttribute("data-note", String(e.qualifier || ""));
        o.setAttribute("data-src", e.source || "");
        rSel.appendChild(o);
      });
      rSel.value = keep && rSel.querySelector("option[value='" + keep + "']") ? keep : "";
    }
    function fillParking(h) {
      var pk = h.parking || {};
      pSel.innerHTML = "<option value=''>not confirmed</option>";
      [["self_usd", "self-parking"], ["valet_usd", "valet"], ["self_usd", "self-parking"]].slice(0,2).forEach(function (pair) {
        var v = pk[pair[0] + "_per_day"] !== undefined ? pk[pair[0] + "_per_day"] : pk[pair[0]];
        if (typeof v === "number") {
          var o = document.createElement("option");
          o.value = String(v); o.textContent = v + " USD · " + pair[1] + " (published per day)";
          pSel.appendChild(o);
        } else if (v) {
          var o2 = document.createElement("option");
          o2.value = ""; o2.textContent = pair[1] + ": " + v + " — not a number, not added";
          pSel.appendChild(o2);
        }
      });
    }
    function num(v) { var n = parseFloat(v); return isNaN(n) ? null : n; }
    function money(v) { return v == null ? null : "$" + v.toLocaleString("en-US", { maximumFractionDigits: 2 }); }

    function recalc() {
      var h = hotelFor(hSel.value);
      var rate = num(rSel.value), fee = num(fSel.options[fSel.selectedIndex] ? fSel.options[fSel.selectedIndex].getAttribute("data-fee") : "");
      var park = num(pSel.value), nights = num(nIn.value) || 0, rooms = num(rIn.value) || 1;
      var entries = 0, count = 0;
      $$(".ev-pick").forEach(function (c) {
        if (c.checked) { entries += num(c.getAttribute("data-cost")) || 0; count++; }
      });
      $("#t-entries").textContent = count ? money(entries) + " (" + count + " entr" + (count === 1 ? "y" : "ies") + ")" : "no events selected";
      var night = (rate != null && fee != null) ? Math.round((rate + fee) * (1 + TAX) * 100) / 100 : null;
      var notes = [];
      if (night == null) {
        $("#t-night").textContent = "cannot compute";
        if (rate == null) notes.push("the property publishes room rates only inside its booking calendar for specific dates — pick a dated rate or use the booking link");
        if (fee == null) notes.push("the mandatory resort fee is not confirmed for this property (its official fee page is unreachable or contradicts itself)");
      } else {
        $("#t-night").textContent = money(night) + " (" + money(rate) + " rate + " + money(fee) + " fee, ×1.1338 room tax)";
      }
      var hotelTotal = night == null ? null : night * nights * rooms + (park == null ? 0 : park * nights);
      $("#t-hotel").textContent = hotelTotal == null ? "cannot compute"
        : money(Math.round(hotelTotal * 100) / 100) + " (" + nights + " night" + (nights === 1 ? "" : "s") + " × " + rooms + " room" + (rooms === 1 ? "" : "s") +
          (park == null ? "" : " + " + money(park * nights) + " parking") + ")";
      var grand = hotelTotal == null ? entries : hotelTotal + entries;
      $("#t-grand").textContent = money(Math.round(grand * 100) / 100) + (hotelTotal == null ? " (entries only — hotel incomplete)" : "");
      var rn = rSel.options[rSel.selectedIndex];
      if (rate != null && rn && rn.getAttribute("data-note")) notes.push("rate qualifier: " + rn.getAttribute("data-note"));
      $("#calc-note").innerHTML = notes.length ? notes.map(function (n) { return "<div>" + esc(n) + "</div>"; }).join("") : "";
      var book = $("#calc-book");
      if (book && h.booking_link) { book.href = h.booking_link; book.target = "_blank"; book.rel = "noopener"; }
    }
    hSel.addEventListener("change", function () { var h = hotelFor(hSel.value); fillRates(h); fillParking(h); recalc(); });
    [rSel, fSel, pSel, nIn, rIn].forEach(function (el) {
      if (el) { el.addEventListener("input", recalc); el.addEventListener("change", recalc); }
    });
    document.addEventListener("change", function (e) { if (e.target.classList.contains("ev-pick")) recalc(); });
    fillRates(hotelFor(hSel.value)); fillParking(hotelFor(hSel.value)); recalc();
  }
})();
