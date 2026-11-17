/* planner.js — shared rendering, filters, search, calculator, overlap.
   Reads window.PLANNER_DATA (data.js). No network calls; works from file://. */
(function () {
  const D = window.PLANNER_DATA;
  const $ = (s, r) => (r || document).querySelector(s);
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const money = (n) => n == null ? "" : "$" + Number(n).toLocaleString("en-US");
  const srcLink = (u, label) => `<a class="src" href="${esc(u)}" target="_blank" rel="noopener">${esc(label || u)}</a>`;
  function badgeForCat(cat) {
    const map = { single: ["b-info", "Single-day candidate"], bounty: ["b-warn", "Bounty"], pko: ["b-warn", "PKO"],
      flight: ["b-mute", "Flighted"], satellite: ["b-info", "Satellite"], seniors: ["b-info", "Seniors 50+"],
      ladies: ["b-info", "Ladies"], tag_team: ["b-info", "Tag Team"], raceday: ["b-info", "RaceDay"] };
    const m = map[cat] || ["b-mute", cat];
    return `<span class="badge ${m[0]}">${m[1]}</span>`;
  }
  function seBadge(ev) {
    if (ev.single_entry_confirmed) return `<span class="badge b-ok">Single-entry confirmed</span>`;
    if (/NOT single-entry/.test(ev.single_entry_status)) return `<span class="badge b-no">Not single-entry</span>`;
    return `<span class="badge b-warn">Single-entry unverified</span>`;
  }
  window.Planner = { D, $, esc, money, srcLink, badgeForCat, seBadge };
})();

/* ---------- Tournaments table ---------- */
function renderTournaments() {
  const P = window.Planner, D = P.D;
  const dateSel = P.$("#f-date"), catSel = P.$("#f-cat"), seChk = P.$("#f-single"), q = P.$("#f-q");
  const tbody = P.$("#t-body"), count = P.$("#row-count");
  function apply() {
    const d = dateSel.value, c = catSel.value, onlySE = seChk.checked, query = q.value.trim().toLowerCase();
    const rows = D.events.filter(ev => {
      if (d && ev.date !== d) return false;
      if (c && ev.category !== c) return false;
      if (onlySE && !ev.single_entry_confirmed) return false;
      if (query) {
        const hay = (ev.name + " " + ev.date + " " + ev.time + " " + ev.event_no + " " + (ev.guarantee || "") + " " + ev.category).toLowerCase();
        if (hay.indexOf(query) < 0) return false;
      }
      return true;
    });
    tbody.innerHTML = rows.map(ev => `
      <tr>
        <td>${esc(ev.date)}</td>
        <td>${esc(ev.time)}<div class="src">${esc(ev.start24)}</div></td>
        <td>#${esc(ev.event_no)}</td>
        <td>${esc(ev.name)}</td>
        <td>${P.badgeForCat(ev.category)}</td>
        <td class="ratio">${money(ev.buyin)}</td>
        <td class="ratio">${money(ev.house_fee)}</td>
        <td class="ratio">${money(ev.pool_per_entry)}</td>
        <td class="ratio">${ev.guarantee_num != null ? money(ev.guarantee_num) : "<span class='pill'>not stated</span>"}</td>
        <td class="ratio">${ev.guarantee_ratio != null ? ev.guarantee_ratio + "×" : "—"}</td>
        <td>${esc(ev.start_chips).toLocaleString()}</td>
        <td>${esc(ev.late_registration)}</td>
        <td>${P.seBadge(ev)}</td>
        <td>${ev.reentry ? esc(ev.reentry) : "<span class='pill'>not stated</span>"}</td>
        <td>${ev.addon ? esc(ev.addon) : "<span class='pill'>not stated</span>"}</td>
        <td>${esc(ev.last_checked)}</td>
        <td><div class="src">${P.srcLink(ev.sources[0], "Schedule")}<br>${P.srcLink(ev.structure_sheet, "Structure #" + ev.structure_no)}</div></td>
      </tr>`).join("");
    count.textContent = rows.length + " of " + D.events.length + " rows";
  }
  [dateSel, catSel, seChk, q].forEach(el => el.addEventListener("input", apply));
  // populate distinct dates + categories
  dateSel.innerHTML = "<option value=''>All dates</option>" + Array.from(new Set(D.events.map(e => e.date))).sort().map(d => `<option>${d}</option>`).join("");
  const cats = [["", "All formats"], ["single", "Single-day candidate"], ["bounty", "Bounty"], ["pko", "PKO"], ["flight", "Flighted"], ["satellite", "Satellite"], ["seniors", "Seniors 50+"], ["ladies", "Ladies"], ["tag_team", "Tag Team"], ["raceday", "RaceDay"]];
  catSel.innerHTML = cats.map(c => `<option value='${c[0]}'>${c[1]}</option>`).join("");
  apply();
}

/* ---------- Trip cost calculator ---------- */
function renderCalc() {
  const P = window.Planner, D = P.D;
  const form = P.$("#calc-form");
  const entries = P.$("#c-entries"), buyin = P.$("#c-buyin"), nights = P.$("#c-nights"),
        rate = P.$("#c-rate"), resortFee = P.$("#c-fee"), tax = P.$("#c-tax");
  // default resort fee/tax from the one verified hotel
  const venetian = D.hotels[0];
  resortFee.value = venetian.resort_fee;
  tax.value = venetian.tax_pct;
  const out = P.$("#calc-out");
  function compute(e) {
    if (e) e.preventDefault();
    const n = parseFloat(entries.value) || 0, b = parseFloat(buyin.value) || 0;
    const ni = parseFloat(nights.value) || 0, r = parseFloat(rate.value) || 0;
    const f = parseFloat(resortFee.value) || 0, t = (parseFloat(tax.value) || 0) / 100;
    const entryCost = n * b;
    const nightly = (r + f) * (1 + t);
    const hotelCost = ni * nightly;
    const total = entryCost + hotelCost;
    out.innerHTML = `
      <div class="rowline"><span>Entries × buy-in</span><b>${money(entryCost)}</b></div>
      <div class="rowline"><span>Nights</span><b>${ni}</b></div>
      <div class="rowline"><span>True cost / night (rate + fee, incl. tax)</span><b>${money(nightly)}</b></div>
      <div class="rowline"><span>Nights × true cost / night</span><b>${money(hotelCost)}</b></div>
      <div class="rowline" style="margin-top:10px"><span>Estimated trip total</span><b style="font-size:24px;color:#7ee2a8">${money(total)}</b></div>
      <p class="muted" style="margin-top:10px">Entry cost is entries × the buy-in you enter. Hotel uses the rate you enter plus the verified resort fee and ${t*100}% tax.
      Enter the room rate for your exact dates from the property's official booking link — rates are not stored as a single value and are not verified here.</p>`;
  }
  form.addEventListener("submit", compute);
  compute();
}

/* ---------- Hotels ---------- */
function renderHotels() {
  const P = window.Planner, D = P.D;
  const wrap = P.$("#hotel-rows");
  const walkChk = P.$("#f-walk");
  function apply() {
    const onlyWalk = walkChk.checked;
    wrap.innerHTML = D.hotels.map(h => {
      const walkOk = h.walk_to_venue_min != null && h.walk_to_venue_min <= 30;
      const walkBadge = h.walk_to_venue_min == null
        ? `<span class="badge b-warn">walk unverified</span>`
        : (walkOk ? `<span class="badge b-ok">≤30 min walk</span>` : `<span class="badge b-no">>30 min walk</span>`);
      const rate = (parseFloat(h.resort_fee || 0));
      const nightlyNote = h.resort_fee != null
        ? `Illustrative true cost/night at a $0 room = ${P.money(h.resort_fee * (1 + h.tax_pct / 100))} (fee + tax). Add your dated room rate for the real total.`
        : `Resort fee unverified — true cost/night cannot be computed.`;
      if (onlyWalk && h.walk_to_venue_min == null) return "";
      return `<div class="card">
        <h3>${esc(h.property)}</h3>
        <p>${esc(h.venue)} · ${walkBadge}</p>
        <p>Resort fee: <b>${h.resort_fee != null ? money(h.resort_fee) + " + tax" : "<span class='pill'>unverified</span>"}</b> · Room tax: <b>${h.tax_pct}%</b></p>
        <p class="muted">${esc(nightlyNote)}</p>
        <p class="muted">${esc(h.rate_status)}</p>
        <p>${esc(h.walk_status)}</p>
        <p><a class="button ghost" href="${esc(h.booking_link)}" target="_blank" rel="noopener">Official booking ↗</a>
           <span class="pill">fee source</span> <a class="src" href="${esc(h.fee_source)}" target="_blank" rel="noopener">${esc(h.fee_source)}</a></p>
      </div>`;
    }).join("");
  }
  walkChk.addEventListener("change", apply);
  apply();
}

/* ---------- Schedule overlap check (primary + conditional fallback per day) ---------- */
function renderSchedule() {
  const P = window.Planner, D = P.D;
  // group by date, sort by start24
  const byDay = {};
  D.events.forEach(e => { (byDay[e.date] = byDay[e.date] || []).push(e); });
  Object.keys(byDay).sort().forEach(date => {
    byDay[date].sort((a, b) => a.start24.localeCompare(b.start24));
  });
  const wrap = P.$("#schedule-days");
  wrap.innerHTML = Object.keys(byDay).sort().map(date => {
    const evs = byDay[date];
    // Primary = earliest single-day candidate (single/raceday) that is not bounty/flight; else earliest event
    const candidate = evs.find(e => e.category === "single" || e.category === "raceday");
    const primary = candidate || evs[0];
    const later = evs.filter(e => e.id !== primary.id);
    const fallback = later[0];
    const overlapNote = later.length
      ? `<p class="muted">Later same-day entries (${later.length}) cannot be confirmed playable in sequence: finish times are not published, so overlap cannot be ruled out. Treat as conditional only.</p>`
      : `<p class="muted">Only one listed entry this day.</p>`;
    return `<div class="dayplan">
      <h3>${esc(date)} · ${evs.length} listed entries</h3>
      <div class="primary">
        <span class="badge b-ok">Primary</span> <b>${esc(primary.name)}</b> — ${esc(primary.time)}
        <div class="muted">${esc(primary.format_detail)} · ${P.money(primary.buyin)} · ${primary.guarantee_num != null ? P.money(primary.guarantee_num) + " GTD" : "no stated guarantee"}</div>
      </div>
      ${fallback ? `<div class="fallback"><span class="badge b-warn">Conditional fallback</span> <b>${esc(fallback.name)}</b> — ${esc(fallback.time)}
        <div class="muted">Play only if the primary event ends or you are eliminated in time. Finish time unverified.</div></div>` : ""}
      ${overlapNote}
    </div>`;
  }).join("");
}

/* ---------- Monitoring ---------- */
function renderMonitoring() {
  const P = window.Planner, D = P.D;
  const wrap = P.$("#mon-sources");
  wrap.innerHTML = D.monitoring_sources.map(s => `
    <div class="card">
      <h3>${esc(s.label)}</h3>
      <p><span class="pill">${esc(s.type)}</span> <span class="badge ${s.status === "ok" ? "b-ok" : "b-warn"}">${esc(s.status)}</span></p>
      <p class="muted">Last checked: ${esc(s.last_checked)}</p>
      <p><a class="src" href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a></p>
    </div>`).join("");
  const cl = P.$("#change-log");
  cl.innerHTML = D.change_log.length
    ? D.change_log.map(c => `<div class="rowline"><span>${esc(c.date)} · ${esc(c.source)}</span><b>${esc(c.change)}</b></div>`).join("")
    : `<p class="muted">No changes detected yet. Run <code>python3 tools/check_sources.py</code> (or the scheduled workflow) to re-check every official URL; changes are appended here and rows are flagged.</p>`;
}

/* ---------- Flagged ---------- */
function renderFlagged() {
  const P = window.Planner, D = P.D;
  const items = [];
  const reentryEvts = D.events.filter(e => /NOT single-entry/.test(e.single_entry_status));
  reentryEvts.forEach(e => items.push({ t: "Confirmed NOT single-entry", d: `Event #${e.event_no} (${e.name}, ${e.date}): structure_8 states "All subsequent buy in's after the initial buy in will be $200" — re-buys permitted.`, s: e.structure_sheet }));
  const unverified = D.events.filter(e => !e.single_entry_confirmed && !/NOT single-entry/.test(e.single_entry_status));
  items.push({ t: "Single-entry unverified for " + unverified.length + " events", d: "No structure sheet states 'single entry only' or prohibits re-entry/add-on. Omission is not confirmation, so these remain flagged.", s: D.events[0].structure_sheet });
  D.hotels.forEach(h => {
    if (h.resort_fee == null) items.push({ t: "Resort fee unverified — " + h.property, d: h.rate_status, s: h.fee_source });
    if (h.walk_to_venue_min == null) items.push({ t: "Walking time unverified — " + h.property, d: h.walk_status, s: h.fee_source });
  });
  items.push({ t: "No date-specific room rates", d: "No official dated room quote was captured for any stay. Rates are kept as an empty dated log until one is verified.", s: D.hotels[0].booking_link });
  items.push({ t: "No 8:00 AM start in the verified set", d: "The earliest listed start across the verified Venetian DSE IV schedule is 9:10 AM (satellite #46, Dec 12). A strict 8 AM start is not available.", s: D.events[0].sources[0] });
  items.push({ t: "Event finish times not published", d: "Overlap between same-day entries cannot be confirmed; schedule shows a primary + conditional fallback only.", s: D.events[0].sources[0] });
  const wrap = P.$("#flag-list");
  wrap.innerHTML = items.map((it, i) => `
    <div class="card">
      <h3>${i + 1}. ${esc(it.t)}</h3>
      <p>${esc(it.d)}</p>
      <p><a class="src" href="${esc(it.s)}" target="_blank" rel="noopener">${esc(it.s)}</a></p>
    </div>`).join("");
}

document.addEventListener("DOMContentLoaded", function () {
  if (window.Planner.$("#t-body")) renderTournaments();
  if (window.Planner.$("#calc-form")) renderCalc();
  if (window.Planner.$("#hotel-rows")) renderHotels();
  if (window.Planner.$("#schedule-days")) renderSchedule();
  if (window.Planner.$("#mon-sources")) renderMonitoring();
  if (window.Planner.$("#flag-list")) renderFlagged();
});
