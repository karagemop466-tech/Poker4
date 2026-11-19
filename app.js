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
    /* The tournaments page stacks its event tables in tabs, so only the active
       tab's rows are filterable there. A page with a single table (the comparison
       table) has no tab panel, and all of its rows are filterable. */
    var panel = $(".tabpanel.active");
    return $$("tr.ev-row", panel || document);
  }

  var WD = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

  /* Which weekdays a date range covers. Recurring rows print weekdays ("Nightly Monday-Sunday"),
     never calendar dates, so they can only be matched against a range by the weekday names — and a
     range with one end missing is read as that single day, never as an open-ended sweep. */
  function weekdaysIn(from, to) {
    var a = from || to, b = to || from;
    if (!a || !b) return null;
    var start = new Date(a + "T00:00:00Z"), end = new Date(b + "T00:00:00Z");
    if (isNaN(start) || isNaN(end) || end < start) return null;
    var out = {}, n = 0;
    for (var d = new Date(start); d <= end && n < 400; d.setUTCDate(d.getUTCDate() + 1), n++) {
      out[WD[d.getUTCDay()]] = 1;
    }
    return out;
  }

  function val(id) { var el = $("#" + id); return el ? el.value : ""; }
  function chk(id) { var el = $("#" + id); return el ? el.checked : false; }

  function later(a, b) {
    if (!a) return b || "";
    if (!b) return a;
    return a > b ? a : b;
  }
  function iso(d) {
    var month = String(d.getMonth() + 1), day = String(d.getDate());
    if (month.length < 2) month = "0" + month;
    if (day.length < 2) day = "0" + day;
    return d.getFullYear() + "-" + month + "-" + day;
  }
  function addDaysISO(value, days) {
    var parts = value.split("-");
    var d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]), 12, 0, 0, 0);
    d.setDate(d.getDate() + days);
    return iso(d);
  }
  function hashId() {
    try { return decodeURIComponent(location.hash.slice(1)); }
    catch (_) { return location.hash.slice(1); }
  }
  function initializeUpcomingRange() {
    var root = $("#filters"), from = $("#f-from"), to = $("#f-to");
    if (!root || !from || !to) return;
    var windowStart = root.getAttribute("data-window-start") || from.min || "";
    var windowEnd = root.getAttribute("data-window-end") || to.max || "";
    var snapshotDay = root.getAttribute("data-snapshot-day") || "";
    var start = later(windowStart, later(snapshotDay, iso(new Date())));
    var end = windowEnd && windowEnd >= start ? windowEnd : start;
    if (windowStart) { from.min = windowStart; to.min = windowStart; }
    from.max = end;
    to.max = end;
    from.value = start;
    to.value = end;
  }
  function prepareDeepLink() {
    var row = document.getElementById(hashId());
    if (!row || !row.classList || !row.classList.contains("ev-row")) return;
    var panel = row.closest ? row.closest(".tabpanel") : null;
    if (panel) {
      var name = panel.getAttribute("data-panel");
      $$(".tabpanel").forEach(function (p) { p.classList.toggle("active", p === panel); });
      $$(".tab").forEach(function (t) { t.classList.toggle("active", t.getAttribute("data-tab") === name); });
    }
    // A search result or venue link is an explicit request for this row. Do not let
    // the upcoming-only default hide a historical or recurring event target.
    var from = $("#f-from"), to = $("#f-to");
    if (from) from.value = "";
    if (to) to.value = "";
  }

  function applyFilters() {
    var from = val("f-from"), to = val("f-to"), venue = val("f-venue");
    var singleOnly = chk("f-single"), hideUnconf = chk("f-hide-unconfirmed");
    var shown = 0, undated = 0, total = 0;
    activePanelRows().forEach(function (tr) {
      total++;
      var ev = byId[tr.getAttribute("data-id")] || {};
      var date = tr.getAttribute("data-date") || "";
      var days = (tr.getAttribute("data-days") || "").split(",").filter(Boolean);
      var ok = true;
      if (venue && tr.getAttribute("data-venue") !== venue) ok = false;
      if (ok && (from || to)) {
        if (date) {
          if (from && date < from) ok = false;
          if (to && date > to) ok = false;
        } else if (days.length) {
          var covered = weekdaysIn(from, to);
          if (!covered) { ok = false; undated++; }
          else {
            var hit = false;
            for (var di = 0; di < days.length; di++) if (covered[days[di]]) { hit = true; break; }
            if (!hit) ok = false;
          }
        } else { ok = false; undated++; }
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
        (undated ? " (" + undated + " row(s) hidden: no date and no printed weekday, so they cannot be placed on a day)" : "");
    }
  }

  ["f-from", "f-to", "f-venue", "f-single", "f-hide-unconfirmed"].forEach(function (id) {
    var el = $("#" + id);
    if (el) { el.addEventListener("change", applyFilters); el.addEventListener("input", applyFilters); }
  });
  $$(".btn-mini[data-preset]").forEach(function (b) {
    b.addEventListener("click", function () {
      var root = $("#filters"), from, to;
      var windowStart = root && root.getAttribute("data-window-start");
      var windowEnd = root && root.getAttribute("data-window-end");
      var snapshotDay = root && root.getAttribute("data-snapshot-day");
      if (b.getAttribute("data-preset") === "all") {
        setDates(windowStart || $("#f-from").min, windowEnd || $("#f-to").max);
        return;
      }
      var span = parseInt(b.getAttribute("data-preset"), 10);
      from = later(windowStart || "", later(snapshotDay || "", iso(new Date())));
      var endCap = windowEnd && windowEnd >= from ? windowEnd : from;
      to = addDaysISO(from, Math.max(0, span - 1));
      if (to > endCap) to = endCap;
      setDates(from, to);
    });
  });
  function setDates(a, b) {
    var f = $("#f-from"), t = $("#f-to"), root = $("#filters");
    var maxDate = root ? later(root.getAttribute("data-window-end") || "", b || "") : b;
    if (f) { if (maxDate) f.max = maxDate; f.value = a; }
    if (t) { if (maxDate) t.max = maxDate; t.value = b; }
    applyFilters();
  }
  initializeUpcomingRange();
  prepareDeepLink();
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
        if (!index.length) {
          // offline / missing index: build a page-local index from the rendered
          // rows so the search box still works against what is on screen
          var seen = {};
          $$("tr[data-id]").forEach(function (tr) {
            var n = tr.querySelector(".evname");
            var id = tr.getAttribute("data-id");
            if (n && id && !seen[id]) {
              seen[id] = 1;
              index.push({ t: n.textContent, u: "tournaments.html#" + id, k: "event", s: "" });
            }
          });
          $$("a[href*='tournaments.html#']").forEach(function (a) {
            var href = a.getAttribute("href") || "";
            if (!seen[href] && a.textContent.trim()) {
              seen[href] = 1;
              index.push({ t: a.textContent.trim(), u: href, k: "event", s: "" });
            }
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
      var shown = 0, provable = 0, failed = 0;
      cards.forEach(function (el) {
        var ok = true;
        var m = parseInt(el.getAttribute("data-walk-min"), 10);
        var onsite = el.getAttribute("data-onsite") === "1";
        if (mode === "onsite") ok = onsite;
        else if (mode === "measured") ok = onsite || (!isNaN(m) && m <= 30);
        el.classList.toggle("hidden", !ok);
        if (ok) shown++;
        if (!isNaN(m)) provable++;
        if (!isNaN(m) && m > 30) failed++;
      });
      if (wc) {
        wc.textContent = shown + " of " + cards.length + " properties" +
          (mode === "measured"
            ? " — " + provable + " measured with Google Maps walking directions, " + failed + " over the 30-minute line and hidden"
            : "");
      }
    }
    $$("input[name=walkf]", wf).forEach(function (r) { r.addEventListener("change", applyWalk); });
    applyWalk();
  }

  /* -------------------------------------------------------- deep-link rows */
  if (location.hash) {
    var row = document.getElementById(hashId());
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
        pSel = $("#calc-park"), nIn = $("#calc-nights"), rIn = $("#calc-rooms"),
        aIn = $("#calc-arrive"), gIn = $("#calc-guests");

    function hotelFor(id) {
      for (var i = 0; i < hotels.length; i++) if (hotels[i].id === id) return hotels[i];
      return hotels[0];
    }
    function fillRates(h) {
      var keep = rSel.value;
      rSel.innerHTML = "<option value=''>no official dated rate for this property</option>";
      // a rate-log line is only offered as a room rate if it IS one: a resort-fee
      // re-read (kind "fee_only") or a "value not published" line is an observation,
      // and pricing a stay off it would invent a rate the property never printed.
      var RATE_KINDS = { advertised_rate: 1, dated_rate: 1, quoted_rate: 1, all_in_per_night: 1 };
      (h.rate_log || []).forEach(function (e, i) {
        if (!e.amount_usd) return;
        var kind = e.kind || "advertised_rate";
        if (!RATE_KINDS[kind]) return;
        var allIn = kind === "all_in_per_night";
        var o = document.createElement("option");
        o.value = String(e.amount_usd);
        o.textContent = e.amount_usd + " USD · " + (e.observed_on || "date not stated") + " · " +
          (allIn ? "ALL-IN per night (fee + tax already inside) · " : "") +
          String(e.label || e.qualifier || "").slice(0, 58);
        o.setAttribute("data-note", String(e.qualifier || ""));
        o.setAttribute("data-src", e.source || "");
        if (allIn) o.setAttribute("data-allin", "1");
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
      var guests = num(gIn && gIn.value) || 2;
      var entries = 0, count = 0;
      $$(".ev-pick").forEach(function (c) {
        if (c.checked) { entries += num(c.getAttribute("data-cost")) || 0; count++; }
      });
      $("#t-entries").textContent = count ? money(entries) + " (" + count + " entr" + (count === 1 ? "y" : "ies") + ")" : "no events selected";
      var rOpt = rSel.options[rSel.selectedIndex];
      var allIn = !!(rOpt && rOpt.getAttribute("data-allin") === "1");
      var night = allIn && rate != null ? rate
        : (rate != null && fee != null) ? Math.round((rate + fee) * (1 + TAX) * 100) / 100 : null;
      var notes = [];
      if (night == null) {
        $("#t-night").textContent = "cannot compute";
        if (rate == null) notes.push("the property publishes room rates only inside its booking calendar for specific dates — pick a dated rate or use the booking link");
        if (fee == null) notes.push("the mandatory resort fee is not confirmed for this property (its official fee page is unreachable or contradicts itself)");
      } else {
        $("#t-night").textContent = allIn
          ? money(night) + " (all-in per night from the dated booking-engine capture — resort fee and room tax are already inside it)"
          : money(night) + " (" + money(rate) + " rate + " + money(fee) + " fee, ×1.1338 room tax)";
      }
      var occ = h.occupancy_charge && h.occupancy_charge.amount_usd;
      var occNight = (guests > 2 && occ) ? (guests - 2) * occ * (1 + TAX) : 0;
      var hotelTotal = night == null ? null
        : night * nights * rooms + (park == null ? 0 : park * nights) + occNight * nights * rooms;
      if (allIn && rate != null) notes.push("this rate is all-in — the resort fee and the 13.38% room tax are already inside the captured figure, so they are not added again");
      if (occNight) notes.push((guests - 2) + " extra occupant(s) at the published $" + occ +
        " each, per night, plus room tax = " + money(Math.round(occNight * 100) / 100) + " a night, x" +
        nights + " night(s) x " + rooms + " room(s) — the property's own terms, not an estimate");
      if (occNight && allIn) notes.push("the all-in capture prices the occupancy it was quoted for; a third or fourth guest is charged separately under the property's own terms, so that line is additive, not double-counted");
      if (guests > 2 && !occ) notes.push("more than two guests in the room, but this property publishes no per-occupant charge on the page read — nothing was added");
      var bookLink = $("#calc-booklink");
      if (bookLink) {
        var tpl = h.booking_dates_url && h.booking_dates_url.template;
        var arr = aIn && aIn.value;
        if (tpl && arr && nights) {
          var dep = new Date(arr + "T00:00:00Z"); dep.setUTCDate(dep.getUTCDate() + nights);
          var url = tpl.replace("{adults}", guests).replace("{arrival}", arr)
                       .replace("{departure}", dep.toISOString().slice(0, 10));
          bookLink.innerHTML = "<a href='" + esc(url) + "' target='_blank' rel='noopener'>open this property's own booking calendar for " +
            esc(arr) + " → " + esc(dep.toISOString().slice(0, 10)) + ", " + esc(String(guests)) + " guest(s) ↗</a>" +
            "<span class='mini-note'> " + esc((h.booking_dates_url && h.booking_dates_url.basis) || "") + "</span>";
        } else if (tpl && !arr) {
          bookLink.innerHTML = "<span class='mini-note'>add an arrival date and the link to this property's booking calendar is built for your dates and occupancy.</span>";
        } else {
          bookLink.innerHTML = "<span class='mini-note'>" + esc(h.property) + " publishes no date-carrying booking-link pattern on the pages read, so dates are typed into its own engine: " +
            (h.booking_link ? "<a href='" + esc(h.booking_link) + "' target='_blank' rel='noopener'>official booking engine ↗</a>" : "no official booking page reached") + "</span>";
        }
      }
      $("#t-hotel").textContent = hotelTotal == null ? "cannot compute"
        : money(Math.round(hotelTotal * 100) / 100) + " (" + nights + " night" + (nights === 1 ? "" : "s") + " × " + rooms + " room" + (rooms === 1 ? "" : "s") +
          (park == null ? "" : " + " + money(park * nights) + " parking") +
          (occNight ? " + " + money(Math.round(occNight * nights * rooms * 100) / 100) + " extra-occupant charge" : "") + ")";
      var grand = hotelTotal == null ? entries : hotelTotal + entries;
      $("#t-grand").textContent = money(Math.round(grand * 100) / 100) + (hotelTotal == null ? " (entries only — hotel incomplete)" : "");
      var rn = rSel.options[rSel.selectedIndex];
      if (rate != null && rn && rn.getAttribute("data-note")) notes.push("rate qualifier: " + rn.getAttribute("data-note"));
      $("#calc-note").innerHTML = notes.length ? notes.map(function (n) { return "<div>" + esc(n) + "</div>"; }).join("") : "";
      var book = $("#calc-book");
      if (book && h.booking_link) { book.href = h.booking_link; book.target = "_blank"; book.rel = "noopener"; }
    }
    hSel.addEventListener("change", function () { var h = hotelFor(hSel.value); fillRates(h); fillParking(h); recalc(); });
    [rSel, fSel, pSel, nIn, rIn, aIn, gIn].forEach(function (el) {
      if (el) { el.addEventListener("input", recalc); el.addEventListener("change", recalc); }
    });
    document.addEventListener("change", function (e) { if (e.target.classList.contains("ev-pick")) recalc(); });
    fillRates(hotelFor(hSel.value)); fillParking(hotelFor(hSel.value)); recalc();
  }
})();
