/* Poker4 render layer — all content comes from window.POKER4_DATA (assets/data.js).
   Policy enforced upstream in scripts/build_site2.py: no row renders without an official source + last-checked. */
(function () {
  "use strict";
  var D = window.POKER4_DATA;
  if (!D) { document.body.insertAdjacentHTML("afterbegin", "<div class='callout danger'>data failed to load</div>"); return; }
  var SRC = {}; (D.sources || []).forEach(function (s) { SRC[s.id] = s; });

  function esc(x) { return String(x == null ? "" : x).replace(/[&<>"]/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]; }); }
  function money(x) { return x == null ? '<span class="badge warn">blank</span>' : "$" + Number(x).toLocaleString("en-US", { maximumFractionDigits: 2 }); }
  function num(x) { return x == null ? "" : Number(x).toLocaleString("en-US"); }
  function $(id) { return document.getElementById(id); }
  function fmtRatio(r) { return r == null ? "—" : r.toFixed(1) + "×"; }

  function srcLinks(ids, extraUrl) {
    var out = [];
    (ids || []).forEach(function (id) {
      var s = SRC[id];
      if (s) out.push('<a class="src-link" href="' + esc(s.url) + '" target="_blank" rel="noopener">' + esc(id) + " · official ↗</a>");
    });
    if (extraUrl) out.push('<a class="src-link" href="' + esc(extraUrl) + '" target="_blank" rel="noopener">structure PDF ↗</a>');
    return out.join("<br>");
  }
  function ruleBadge(st) {
    if (st === "confirmed") return '<span class="badge ok">confirmed</span>';
    if (st === "confirmed-no") return '<span class="badge bad">not allowed</span>';
    return '<span class="badge warn">unverified</span>';
  }
  function ruleCell(rules, key) {
    var r = (rules || {})[key] || { status: "unverified" };
    var h = ruleBadge(r.status);
    if (r.value === true) h += ' <span class="small">yes</span>';
    else if (r.value === false) h += ' <span class="small">no</span>';
    else if (r.value != null && typeof r.value !== "object") h += ' <span class="small">' + esc(r.value) + "</span>";
    if (r.excerpt) {
      h += '<details class="rulebox"><summary>source excerpt</summary><div class="body"><span class="excerpt">' + esc(r.excerpt) + "</span><br>" +
        '<span class="small">retrieved ' + esc(r.retrieved || D.retrieved) + (r.source ? " · " + esc(r.source) : "") + "</span>" +
        (r.note ? "<br><span class='small'>" + esc(r.note) + "</span>" : "") + "</div></details>";
    } else if (r.note) {
      h += '<details class="rulebox"><summary>note</summary><div class="body"><span class="small">' + esc(r.note) + "</span></div></details>";
    }
    return h;
  }
  function statusBadge(e) {
    if (e.status === "past") return '<span class="badge">past</span>';
    return '<span class="badge ok">upcoming</span>';
  }
  function sectionLabel(e) {
    var lbl = { "standard": "Standard", "flighted": "Flighted", "bounty": "Bounty/PKO", "satellite": "Satellite", "multi-entry": "Multi-entry" }[e.section] || e.section;
    var cls = { "standard": "blue", "flighted": "blue", "bounty": "gold", "satellite": "", "multi-entry": "bad" }[e.section] || "";
    return '<span class="badge ' + cls + '">' + lbl + "</span>";
  }

  /* ---------- global page search ---------- */
  function wireSearch() {
    var box = $("gsearch");
    if (!box) return;
    box.addEventListener("input", function () {
      var q = box.value.toLowerCase().trim();
      document.querySelectorAll("tr[data-search]").forEach(function (tr) {
        tr.style.display = (!q || tr.dataset.search.indexOf(q) !== -1) ? "" : "none";
      });
    });
  }

  /* ---------- event tables ---------- */
  function eventRow(e) {
    var srch = [e.venue, e.name, e.date, e.date_note, e.days, e.time, e.flight, e.buy_in, e.guarantee, e.kind, e.section, e.note].join(" ").toLowerCase();
    var rules = e.entry_rules || {};
    var se = rules.single_entry || {};
    var kindTags = (e.kind || []).map(function (k) { return '<span class="badge">' + esc(k) + "</span>"; }).join(" ");
    var gtdCell = e.guarantee == null ? '<span class="badge warn">blank</span>'
      : money(e.guarantee) + (e.guarantee_includes_bounties ? '<br><span class="badge gold">incl. bounties</span>' : (e.guarantee_includes_bounties === null ? '<br><span class="badge warn">bounty split n/s</span>' : ""));
    return '<tr data-search="' + esc(srch) + '">' +
      "<td>" + esc(e.venue) + '<br><span class="small">' + esc(e.series) + "</span></td>" +
      "<td>" + (e.date ? esc(e.date) + (e.flight ? ' <span class="badge blue">' + esc(e.flight) + "</span>" : "") : '<span class="badge blue">' + esc(e.days || "recurring") + "</span>") +
      (e.restart ? '<br><span class="badge gold">restart day</span>' : "") + "</td>" +
      "<td>" + esc(e.time) + "</td>" +
      "<td>" + esc(e.name) + '<div class="pill-row">' + sectionLabel(e) + kindTags + "</div>" +
      (e.note ? '<div class="small">' + esc(e.note) + "</div>" : "") + "</td>" +
      '<td class="num">' + money(e.buy_in) + "</td>" +
      '<td class="num">' + (e.prize_pool_per_entry == null ? '<span class="badge warn">blank</span>' : money(e.prize_pool_per_entry)) +
      (e.house_fee != null ? '<br><span class="small">house ' + money(e.house_fee) + (e.staff_fee ? " + staff " + money(e.staff_fee) : "") + "</span>" : "") + "</td>" +
      '<td class="num">' + gtdCell + "</td>" +
      '<td class="num">' + (e.ratio == null ? "—" : '<span class="badge gold">' + fmtRatio(e.ratio) + "</span>") + "</td>" +
      "<td>" + (e.chips ? num(e.chips) + " chips<br>" : "") + (e.level_min ? e.level_min + " min" : "") + "</td>" +
      "<td>" + esc(e.late_reg || "—") + (e.late_reg_time ? '<br><span class="small">cutoff ' + esc(e.late_reg_time) + "</span>" : "") + "</td>" +
      "<td>" + ruleCell(rules, "single_entry") + "</td>" +
      "<td>" + ruleCell(rules, "re_entry") + "</td>" +
      "<td>" + ruleCell(rules, "addon") + (rules.entry_fee && rules.entry_fee.status === "confirmed" ? '<div class="small">fee split: confirmed</div>' : '<div class="small flagged-cell">fee split: ' + esc((rules.entry_fee || {}).status || "unverified") + "</div>") + "</td>" +
      "<td>" + srcLinks(e.sources, e.structure_url) + '<div class="small">checked ' + esc(e.last_checked) + "</div></td>" +
      "</tr>";
  }
  var EVENT_HEAD = "<tr><th>Venue / series</th><th>Date</th><th>Start</th><th>Event</th><th class='num'>Buy-in</th><th class='num'>Pool $/entry</th><th class='num'>Guarantee</th><th class='num'>Gtd ÷ fee</th><th>Stack / levels</th><th>Late reg</th><th>Single entry</th><th>Re-entry</th><th>Add-on / fee</th><th>Sources (official) / last checked</th></tr>";
  function fillEventTable(tableId, rows) {
    var t = $(tableId); if (!t) return;
    t.innerHTML = "<thead>" + EVENT_HEAD + "</thead><tbody>" + rows.map(eventRow).join("") + "</tbody>";
  }
  function sortEvents(rows, by) {
    var r = rows.slice();
    r.sort(function (a, b) {
      if (by === "ratio") return (b.ratio || -1) - (a.ratio || -1);
      if (by === "buyin") return (a.buy_in || 1e9) - (b.buy_in || 1e9);
      if (by === "guarantee") return (b.guarantee || -1) - (a.guarantee || -1);
      if (by === "date") return String(a.date || a.date_note || "zzz").localeCompare(String(b.date || b.date_note || "zzz"));
      return 0;
    });
    return r;
  }

  /* ---------- tournaments page ---------- */
  function initTournaments() {
    var all = D.events || [];
    function selected() {
      var f = {
        venue: $("f-venue") ? $("f-venue").value : "all",
        date: $("f-date") ? $("f-date").value : "",
        confirmedOnly: $("f-confirmed") ? $("f-confirmed").checked : false,
        sort: $("f-sort") ? $("f-sort").value : "date",
        kind: $("f-kind") ? $("f-kind").value : "all"
      };
      return all.filter(function (e) {
        if (f.venue !== "all" && e.venue !== f.venue) return false;
        if (f.date && e.date !== f.date) return false;
        if (f.confirmedOnly && (e.entry_rules.single_entry || {}).status !== "confirmed") return false;
        if (f.kind !== "all" && (e.kind || []).indexOf(f.kind) === -1 && e.section !== f.kind) return false;
        return true;
      });
    }
    function render() {
      var rows = selected();
      var mains = rows.filter(function (e) { return e.section === "standard" || e.section === "flighted"; });
      var bounties = rows.filter(function (e) { return e.section === "bounty"; });
      var multi = rows.filter(function (e) { return e.section === "multi-entry"; });
      var sats = rows.filter(function (e) { return e.section === "satellite"; });
      fillEventTable("t-main", sortEvents(mains, $("f-sort").value));
      fillEventTable("t-bounty", sortEvents(bounties, $("f-sort").value));
      fillEventTable("t-multi", sortEvents(multi, $("f-sort").value));
      fillEventTable("t-sat", sortEvents(sats, $("f-sort").value));
      $("cnt-main").textContent = mains.length; $("cnt-bounty").textContent = bounties.length;
      $("cnt-multi").textContent = multi.length; $("cnt-sat").textContent = sats.length;
      $("empty-confirmed").style.display = $("f-confirmed").checked && rows.length === 0 ? "block" : "none";
      // ratio ranking — descriptive only
      var rank = rows.filter(function (e) { return e.ratio != null; }).sort(function (a, b) { return b.ratio - a.ratio; }).slice(0, 12);
      $("t-rank").innerHTML = "<thead><tr><th>#</th><th>Event</th><th class='num'>Buy-in</th><th class='num'>Guarantee</th><th class='num'>Guarantee ÷ fee</th><th>Caveat</th></tr></thead><tbody>" +
        rank.map(function (e, i) {
          return "<tr data-search='" + esc((e.venue + " " + e.name).toLowerCase()) + "'><td>" + (i + 1) + "</td><td>" + esc(e.venue) + " — " + esc(e.name) +
            (e.date ? " (" + esc(e.date) + ")" : " (" + esc(e.days || "") + ")") + "</td><td class='num'>" + money(e.buy_in) + "</td><td class='num'>" + money(e.guarantee) +
            "</td><td class='num'><span class='badge gold'>" + fmtRatio(e.ratio) + "</span></td><td class='small'>" +
            (e.guarantee_includes_bounties ? "guarantee includes bounty money — not comparable to pure prize pools" :
              e.guarantee_includes_bounties === null ? "bounty inclusion not stated on source" :
                (e.section === "satellite" ? "pays seats, not cash" : e.section === "multi-entry" ? "multi-entry event — spend can exceed the listed fee" : "descriptive ratio only — not a forecast")) +
            "</td></tr>";
        }).join("") + "</tbody>";
    }
    ["f-venue", "f-date", "f-confirmed", "f-sort", "f-kind"].forEach(function (id) {
      if ($(id)) $(id).addEventListener("change", render);
    });
    render();
  }

  /* ---------- schedule page ---------- */
  var WEEKDAY = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  function parseISO(s) { var p = s.split("-"); return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])); }
  function recurrencesFor(dateStr) {
    // returns dated + recurring events active on that date
    var dt = parseISO(dateStr), dow = dt.getUTCDay(), out = [];
    (D.events || []).forEach(function (e) {
      if (e.date === dateStr) { out.push(e); return; }
      if (e.date) return;
      var d = (e.days || "") + "";
      var match = false;
      if (/Daily/.test(d) && /Mon/.test(d) === false && /Mon–Thu/.test(d) === false) match = true; // plain "Daily"
      if (/Nightly/.test(d)) match = true;
      if (/Mon–Thu/.test(d) && dow >= 1 && dow <= 4) match = true;
      if (/Friday/.test(d) && dow === 5) match = true;
      if (/Saturday/.test(d) && dow === 6) match = true;
      if (/Sunday/.test(d) && dow === 0) match = true;
      if (/Sat & Sun/.test(d) && (dow === 6 || dow === 0)) match = true;
      if (/Daily/.test(d) && e.venue === "Caesars Palace") match = true;
      if (match) out.push(e);
    });
    return out;
  }
  function estDurationMin(e) {
    if ((e.kind || []).indexOf("turbo") !== -1) return 300;
    if (e.section === "satellite") return 240;
    if (e.restart) return 0; // restart days handled as labels
    if ((e.kind || []).indexOf("flight") !== -1) return 480;
    return e.time >= "17:00" ? 330 : 480;
  }
  function toMin(hhmm) { var p = hhmm.split(":"); return +p[0] * 60 + +p[1]; }
  function fromMin(m) { m = ((m % 1440) + 1440) % 1440; return String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0"); }

  function initSchedule() {
    if (!$("s-date")) return;
    var input = $("s-date");
    input.value = D.retrieved > "2026-12-23" ? "2026-11-17" : (D.retrieved >= "2026-11-16" ? D.retrieved : "2026-11-17");
    input.min = "2026-11-16"; input.max = "2026-12-23";
    function render() {
      var dateStr = input.value; if (!dateStr) return;
      var dt = parseISO(dateStr), dow = dt.getUTCDay();
      var evs = recurrencesFor(dateStr).filter(function (e) { return !e.restart; });
      evs.sort(function (a, b) { return toMin(a.time) - toMin(b.time); });
      $("s-dayname").textContent = WEEKDAY[dow] + ", " + dateStr;
      // 8 AM goal gap
      var earliest = evs.length ? evs[0] : null;
      $("s-goal").innerHTML = earliest
        ? '<div class="callout warn"><div class="t">8:00 AM start goal</div>No verified event starts at 8:00 AM anywhere on the Strip (checked ' + esc(D.retrieved) +
          '). Earliest verified start on this day: <b>' + esc(earliest.time) + "</b> — " + esc(earliest.venue) + " " + esc(earliest.name) + ". Morning gap is a data gap, not a scheduling choice.</div>"
        : '<div class="callout"><div class="t">No verified events on this date.</div>Only rows backed by official sources appear; see Flagged &amp; Questions for rooms not yet verified.</div>';

      // day plan: primary = earliest non-satellite; fallback = next event that plausibly starts after exit; flag overlaps
      var slots = [];
      var primaries = evs.filter(function (e) { return e.section !== "satellite" && e.time < "17:00"; });
      var primary = primaries[0] || evs[0];
      var plan = [];
      if (primary) {
        plan.push({ role: "primary", e: primary, note: "Play from the start. Plausible duration " + Math.round(estDurationMin(primary) / 60 * 10) / 10 + " h (estimate only). Late-reg cutoff " + (primary.late_reg || "not stated") + "." });
        var pend = toMin(primary.time) + estDurationMin(primary);
        evs.forEach(function (e) {
          if (e === primary) return;
          var st = toMin(e.time);
          var lrClose = e.late_reg_time ? toMin(e.late_reg_time) : st + 180;
          if (st >= pend) {
            plan.push({ role: "fallback", e: e, note: "Conditional fallback — only if you exit " + primary.venue + " (bust or late exit). Starts after the primary's plausible end (" + fromMin(pend) + " estimate)." });
          } else if (lrClose > pend && st < pend) {
            plan.push({ role: "conditional-late", e: e, note: "Conditional (late entry) — its late registration (" + (e.late_reg_time ? "cutoff " + e.late_reg_time : e.late_reg) + ") is still open around the primary's plausible end (" + fromMin(pend) + " estimate), but you cannot play both from the start." });
          } else {
            slots.push(e);
          }
        });
      }
      $("s-plan").innerHTML = plan.map(function (p) {
        var e = p.e;
        return '<div class="slot ' + (p.role === "fallback" ? "fallback" : "") + '">' +
          '<div class="when">' + (p.role === "primary" ? "PRIMARY" : p.role === "fallback" ? "FALLBACK (conditional)" : "CONDITIONAL (late entry)") +
          " · " + esc(e.time) + " · " + esc(e.venue) + " — " + esc(e.name) + "</div>" +
          '<div class="small">' + esc(p.note) + " Buy-in " + (e.buy_in == null ? "blank/flagged" : "$" + num(e.buy_in)) +
          (e.guarantee != null ? " · guarantee $" + num(e.guarantee) : "") + "</div>" +
          '<div class="small">' + ruleBadge((e.entry_rules.single_entry || {}).status) + " single-entry status · sources checked " + esc(e.last_checked) + "</div></div>";
      }).join("") +
        (slots.length ? '<div class="callout warn"><div class="t">Overlap flags — not presented as a playable sequence</div><ul class="tight">' +
          slots.map(function (e) {
            return "<li>" + esc(e.time) + " " + esc(e.venue) + " — " + esc(e.name) + ": overlaps the primary block's plausible duration (start-time + late-reg + duration logic). Playable only if you exit the primary early.</li>";
          }).join("") + "</ul></div>" : "");

      fillEventTable("t-day", evs);
    }
    input.addEventListener("change", render);
    render();
  }

  /* ---------- hotels page ---------- */
  function trueNightly(h) {
    // true cost per night = rate + resort fee + tax(13.38% on rate+fee) — uses logged rate if present
    var log = (h.rate_log || [])[0];
    if (log && log.nightly_avg_room != null && h.resort_fee != null) {
      return { value: (log.nightly_avg_room + h.resort_fee) * (1 + (h.tax_rate || D.tax_rate)), basis: "dated quote " + log.captured + " (" + log.checkin + "→" + log.checkout + ", " + log.nights + " nts avg)" };
    }
    if (h.poker_rate && h.poker_rate.rate_from != null && h.resort_fee != null) {
      return { value: (h.poker_rate.rate_from + h.resort_fee) * (1 + (h.tax_rate || D.tax_rate)), basis: "poker rate from $" + h.poker_rate.rate_from + " (conditional — see note), not a dated quote", approx: true };
    }
    return null;
  }
  function hotelRow(h) {
    var tc = trueNightly(h);
    var logRows = (h.rate_log || []).map(function (r) {
      return "<tr><td>" + esc(r.captured) + "</td><td>" + esc(r.checkin) + " → " + esc(r.checkout) + "</td><td class='num'>" + esc(r.nights) + "</td>" +
        "<td class='num'>" + r.nightly.map(function (n) { return "$" + n.toFixed(2); }).join(" / ") + "</td>" +
        "<td class='num'>" + money(r.resort_fee_per_night) + "</td><td class='num'>" + money(r.taxes) + "</td><td class='num'>" + money(r.checkout_total) + "</td>" +
        "<td>" + (r.src ? '<a class="src-link" href="' + esc((SRC[r.src] || {}).url || "#") + '" target="_blank" rel="noopener">' + esc(r.src) + " ↗</a>" : "") + "</td></tr>";
    }).join("");
    var walkOk = h.walk_to_venetian != null && h.walk_to_venetian <= 30;
    return '<tr data-search="' + esc((h.name + " " + (h.parking || "") + " " + (h.cancellation || "")).toLowerCase()) + '">' +
      "<td><b>" + esc(h.name) + "</b><div class='small'>checked " + esc(h.last_checked) + "</div></td>" +
      "<td class='num'>" + (h.resort_fee == null ? '<span class="badge warn">blank + flagged</span>' : money(h.resort_fee) + "+tax") + "</td>" +
      "<td class='num'>" + (h.tax_rate ? (h.tax_rate * 100).toFixed(2) + "%" : "—") + "</td>" +
      "<td class='num'>" + (tc ? "$" + tc.value.toFixed(2) + (tc.approx ? '<br><span class="badge warn">approx.</span>' : "") : '<span class="badge warn">no verified rate</span>') +
      (tc ? '<div class="small">' + esc(tc.basis) + "</div>" : "") + "</td>" +
      "<td class='small'>" + (h.parking ? esc(h.parking) : '<span class="badge warn">blank + flagged</span>') + (h.parking_src ? "<br>" + srcLinks([h.parking_src]) : "") + "</td>" +
      "<td class='small'>" + (h.cancellation ? esc(h.cancellation) : '<span class="badge warn">blank + flagged</span>') + (h.cancellation_src ? "<br>" + srcLinks([h.cancellation_src]) : "") + "</td>" +
      "<td>" + (h.walk_to_venetian != null ? '<span class="badge ok">' + h.walk_to_venetian + " min walk</span>" : '<span class="badge warn">walk time unverified</span>') +
      '<div class="small">' + esc(h.walk_note || "") + '</div><a class="src-link" href="https://www.google.com/maps/dir/?api=1&origin=' + encodeURIComponent(h.name + ", Las Vegas NV") + '&destination=' + encodeURIComponent("The Venetian Poker Room, Las Vegas NV") + '&travelmode=walking" target="_blank" rel="noopener">verify walking route ↗ (Google Maps)</a></td>' +
      "<td>" + (h.booking_link ? '<a class="src-link" href="' + esc(h.booking_link) + '" target="_blank" rel="noopener">official booking ↗</a>' : "") + (h.resort_fee_src ? "<br>" + srcLinks([h.resort_fee_src]) : "") + "</td>" +
      "</tr>" +
      (logRows ? '<tr data-search="' + esc(h.name.toLowerCase()) + '"><td colspan="8"><details class="rulebox" open><summary>dated rate log — ' + esc(h.name) + " (" + (h.rate_log || []).length + " capture" + ((h.rate_log || []).length === 1 ? "" : "s") + ")</summary><div class='body'>" +
        "<table class='data'><tr><th>Captured</th><th>Stay</th><th class='num'>Nights</th><th class='num'>Nightly (verbatim)</th><th class='num'>Resort fee/nt</th><th class='num'>Taxes</th><th class='num'>Checkout total</th><th>Source</th></tr>" + logRows + "</table>" +
        (h.poker_rate ? '<div class="small">Poker rate (conditional): $' + h.poker_rate.rate_from + "–$" + h.poker_rate.rate_to + ". " + esc(h.poker_rate.note) + "</div>" : "") +
        "</div></details></td></tr>" : "");
  }
  function initHotels() {
    if (!$("t-hotels")) return;
    function render() {
      var walkOnly = $("f-walk") && $("f-walk").checked;
      var rows = (D.hotels || []).filter(function (h) { return !walkOnly || (h.walk_to_venetian != null && h.walk_to_venetian <= 30); });
      rows.sort(function (a, b) {
        var ta = trueNightly(a), tb = trueNightly(b);
        return (ta ? ta.value : 1e9) - (tb ? tb.value : 1e9);
      });
      $("t-hotels").innerHTML = "<thead><tr><th>Hotel</th><th class='num'>Resort fee</th><th class='num'>Tax</th><th class='num'>True cost / night</th><th>Parking</th><th>Cancellation</th><th>Walk to Venetian poker room</th><th>Sources</th></tr></thead><tbody>" +
        rows.map(hotelRow).join("") + "</tbody>";
      $("hotels-note").innerHTML = walkOnly && rows.length < (D.hotels || []).length
        ? '<div class="callout warn">≤30-minute filter is ON. Rows without a verified walking time are excluded (walking times cannot be inferred — see Flagged F8). ' + rows.length + " of " + (D.hotels || []).length + " hotels shown.</div>"
        : "";
    }
    if ($("f-walk")) $("f-walk").addEventListener("change", render);
    render();
  }

  /* ---------- trip calculator ---------- */
  function initTrip() {
    if (!$("trip-out")) return;
    var hsel = $("trip-hotel");
    (D.hotels || []).forEach(function (h) {
      var opt = document.createElement("option");
      opt.value = h.id; opt.textContent = h.name; hsel.appendChild(opt);
    });
    var esel = $("trip-event");
    (D.events || []).filter(function (e) { return e.buy_in != null; }).sort(function (a, b) { return String(a.date || a.date_note).localeCompare(String(b.date || b.date_note)); })
      .forEach(function (e) {
        var opt = document.createElement("option");
        opt.value = e.buy_in;
        opt.textContent = (e.date || e.days || "") + " · " + e.venue + " — " + e.name + " ($" + num(e.buy_in) + ")";
        esel.appendChild(opt);
      });
    function calc() {
      var h = (D.hotels || []).filter(function (x) { return x.id === hsel.value; })[0] || (D.hotels || [])[0];
      var nights = parseFloat($("trip-nights").value);
      var entries = parseFloat($("trip-entries").value);
      var buyin = parseFloat($("trip-buyin").value || esel.value);
      var tc = trueNightly(h);
      var out = $("trip-out");
      if (!(nights > 0) || !(entries > 0) || !(buyin > 0)) {
        out.innerHTML = "<div class='callout warn'>Enter nights, entries and a buy-in. The calculator never uses assumed values — every input must come from a verified row or your own entry.</div>";
        return;
      }
      if (!tc) {
        out.innerHTML = "<div class='callout warn'>No verified rate for " + esc(h.name) + " (rate fields blank + flagged). Book via the official link on the Hotels page; a dated quote is required before a total can be shown.</div>";
        return;
      }
      var hotelCost = tc.value * nights;
      var entriesCost = entries * buyin;
      var total = hotelCost + entriesCost;
      out.innerHTML = "<div class='calc-out'><div class='small'>Estimated trip total (transparent assumptions)</div><div class='big'>$" + total.toLocaleString("en-US", { maximumFractionDigits: 2 }) + "</div>" +
        "<dl class='kv'>" +
        "<dt>Entries cost</dt><dd>" + entries + " × $" + num(buyin) + " = <b>$" + entriesCost.toLocaleString("en-US") + "</b> <span class='small'>(re-entries/add-ons not included — verify rules per event)</span></dd>" +
        "<dt>Hotel cost</dt><dd>" + nights + " nights × $" + tc.value.toFixed(2) + " true cost/night = <b>$" + hotelCost.toLocaleString("en-US", { maximumFractionDigits: 2 }) + "</b></dd>" +
        "<dt>True cost basis</dt><dd>rate + resort fee + " + ((h.tax_rate || D.tax_rate) * 100).toFixed(2) + "% tax on rate+fee. Basis: " + esc(tc.basis) + "</dd>" +
        "<dt>Not included (blank/unverified)</dt><dd>airfare, transport, food, parking variance beyond verified figures, add-ons, re-entries</dd>" +
        "</dl></div>";
    }
    ["trip-nights", "trip-entries", "trip-buyin", "trip-hotel", "trip-event"].forEach(function (id) {
      if ($(id)) $(id).addEventListener("input", calc);
    });
    if (esel) esel.addEventListener("change", function () { $("trip-buyin").value = esel.value; calc(); });
    calc();
  }

  /* ---------- venue pages ---------- */
  function initVenue() {
    if (!$("venue-events")) return;
    var v = $("venue-name").dataset.venue;
    var evs = (D.events || []).filter(function (e) { return v === "Others" ? ["Bellagio", "Caesars Palace", "ARIA", "MGM Grand", "Horseshoe", "Harrah's", "Golden Nugget", "Treasure Island"].indexOf(e.venue) !== -1 : e.venue === v; });
    fillEventTable("venue-events", sortEvents(evs, "date"));
    $("venue-count").textContent = evs.length;
    var hs = (D.hotels || []).slice(0, 12);
    $("venue-hotels").innerHTML = "<thead><tr><th>Hotel</th><th class='num'>Resort fee</th><th class='num'>True cost/night</th><th>Walk status</th><th>Booking</th></tr></thead><tbody>" +
      hs.map(function (h) {
        var tc = trueNightly(h);
        return "<tr data-search='" + esc(h.name.toLowerCase()) + "'><td>" + esc(h.name) + "</td><td class='num'>" + (h.resort_fee == null ? '<span class="badge warn">blank</span>' : money(h.resort_fee) + "+tax") + "</td>" +
          "<td class='num'>" + (tc ? "$" + tc.value.toFixed(2) : '<span class="badge warn">no verified rate</span>') + "</td>" +
          "<td>" + (h.walk_to_venetian != null ? '<span class="badge ok">' + h.walk_to_venetian + " min (to Venetian room)</span>" : '<span class="badge warn">unverified</span>') + "</td>" +
          "<td>" + (h.booking_link ? '<a class="src-link" href="' + esc(h.booking_link) + '" target="_blank" rel="noopener">official ↗</a>' : "") + "</td></tr>";
      }).join("") + "</tbody>";
  }

  /* ---------- flagged / questions / suggestions / sources / changelog ---------- */
  function initFlagged() {
    if (!$("t-flagged")) return;
    $("t-flagged").innerHTML = (D.flagged || []).map(function (f) {
      var sev = { high: "bad", medium: "warn", low: "" }[f.severity] || "";
      return '<div class="callout"><div class="t"><span class="badge ' + sev + '">' + esc(f.severity) + "</span> " + esc(f.id) + " — " + esc(f.title) + ' <span class="small">(checked ' + esc(f.checked) + ")</span></div>" +
        "<div>" + esc(f.detail) + "</div>" +
        (f.sources && f.sources.length ? '<div class="small" style="margin-top:6px">' + srcLinks(f.sources) + "</div>" : "") + "</div>";
    }).join("");
  }
  function initQuestions() {
    if (!$("t-questions")) return;
    $("t-questions").innerHTML = "<thead><tr><th>ID</th><th>Question</th><th>Status</th><th>Why it matters</th><th>How to resolve</th></tr></thead><tbody>" +
      (D.questions || []).map(function (q) {
        return "<tr data-search='" + esc((q.q + " " + q.status).toLowerCase()) + "'><td>" + esc(q.id) + "</td><td><b>" + esc(q.q) + "</b>" + (q.a ? '<div class="small">current answer: ' + esc(q.a) + "</div>" : "") + "</td>" +
          "<td><span class='badge " + (/open/.test(q.status) ? "warn" : "ok") + "'>" + esc(q.status) + "</span></td><td class='small'>" + esc(q.why) + "</td><td class='small'>" + esc(q.how_to_resolve) + "</td></tr>";
      }).join("") + "</tbody>";
  }
  function initSuggestions() {
    if (!$("t-suggestions")) return;
    $("t-suggestions").innerHTML = (D.suggestions || []).map(function (s) {
      return '<div class="callout"><div class="t">' + esc(s.id) + " — " + esc(s.title) + ' <span class="badge">effort: ' + esc(s.effort) + '</span> <span class="badge gold">impact: ' + esc(s.impact) + '</span> <span class="badge warn">' + esc(s.status) + "</span></div><div>" + esc(s.detail) + "</div></div>";
    }).join("");
  }
  function initSources() {
    if (!$("t-sources")) return;
    $("t-sources").innerHTML = "<thead><tr><th>ID</th><th>Official source</th><th>URL</th><th>Last checked</th></tr></thead><tbody>" +
      (D.sources || []).map(function (s) {
        return "<tr data-search='" + esc((s.id + " " + s.title + " " + s.url).toLowerCase()) + "'><td class='mono'>" + esc(s.id) + "</td><td>" + esc(s.title) + "</td>" +
          "<td><a href='" + esc(s.url) + "' target='_blank' rel='noopener'>" + esc(s.url) + "</a></td><td>" + esc(s.last_checked) + "</td></tr>";
      }).join("") + "</tbody>";
  }
  function initChangelog() {
    if (!$("t-changes")) return;
    $("t-changes").innerHTML = (D.changes || []).map(function (c) {
      return '<div class="callout warn"><div class="t">' + esc(c.date) + " — " + esc(c.field) + "</div>" +
        "<div><b>Change detected:</b> " + esc(c.change) + "</div><div><b>Action:</b> " + esc(c.action) + "</div>" +
        '<div class="small" style="margin-top:6px">' + srcLinks([], c.source) + "</div></div>";
    }).join("");
  }
  function initIndex() {
    if (!$("idx-cards")) return;
    var evs = D.events || [], hs = D.hotels || [];
    var upcoming = evs.filter(function (e) { return e.status !== "past"; }).length;
    var multi = evs.filter(function (e) { return e.section === "multi-entry"; }).length;
    var conf = evs.filter(function (e) { return (e.entry_rules.single_entry || {}).status === "confirmed"; }).length;
    $("idx-cards").innerHTML =
      '<div class="card"><div class="num">' + evs.length + '</div><div class="lbl">verified event rows (all carry official sources + last-checked)</div></div>' +
      '<div class="card"><div class="num">' + upcoming + '</div><div class="lbl">upcoming rows (incl. recurring dailies)</div></div>' +
      '<div class="card"><div class="num">' + conf + '</div><div class="lbl">confirmed single-entry / freezeout events (toggle exists — set is empty)</div></div>' +
      '<div class="card"><div class="num">' + multi + '</div><div class="lbl">multi-entry (re-entry/rebuy/add-on) events in the separate section</div></div>' +
      '<div class="card"><div class="num">' + hs.length + '</div><div class="lbl">hotels with fee/tax/parking/cancellation captured or flagged</div></div>' +
      '<div class="card"><div class="num">' + ((D.hotels || [])[0].rate_log || []).length + '</div><div class="lbl">dated rate captures in the rate log (never overwritten)</div></div>';
  }

  document.addEventListener("DOMContentLoaded", function () {
    wireSearch();
    [initIndex, initTournaments, initSchedule, initHotels, initTrip, initVenue, initFlagged, initQuestions, initSuggestions, initSources, initChangelog].forEach(function (f) { try { f(); } catch (e) { console.error(e); } });
  });
})();
