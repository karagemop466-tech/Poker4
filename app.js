/* Poker4 dashboard renderer. Loads only data/*.json built by tools/build_data.py (official-source values only). */
(function () {
"use strict";
const $ = (s, el) => (el || document).querySelector(s);
const $$ = (s, el) => Array.from((el || document).querySelectorAll(s));
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const money = v => (typeof v === "number" ? "$" + v.toLocaleString("en-US") : v == null ? "" : esc(v));
const blank = "—";
const TAX = 0.1338; // user-provided; unverified — see Flagged F9

let DATA = { events: [], satellites: [], meta: {}, venues: {} };
let HOTELS = { hotels: [], meta: {} };
let FLAGS = { items: [] };
let RATELOG = { entries: [], meta: {} };
let CHECKS = null; // data/url-checks.json if the scheduled job has run

const state = {
  q: "", date: "", venue: "", singleOnly: false, hideSeparate: true,
  venuePage: $("body").dataset.venue || "",
  walkVenue: "venetian", walkMax30: true
};

function badgeFor(e) {
  const out = [];
  (e.flags || []).forEach(f => out.push(`<span class="badge warn">${esc(f)}</span>`));
  if (e.eligibility) out.push(`<span class="badge">${esc(e.eligibility)}</span>`);
  if (e.special) out.push(`<span class="badge">${esc(e.special)}</span>`);
  if (e.discount_official) out.push(`<span class="badge acc">official discount</span>`);
  return out.join(" ");
}
function srcLinks(e, n) {
  const s = (e.sources || []).slice(0, n || 1);
  return s.map(x => `<a class="src" href="${esc(x.url)}" target="_blank" rel="noopener">official source</a>`).join(" · ");
}
function sessionsText(e) {
  if (!e.sessions) return "";
  return e.sessions.map(s => `${esc(s[0])}: ${esc(s[1])} ${esc(s[2])}`).join("<br>");
}
function rowMatchesDate(e, d) {
  if (!d) return true;
  return (e.sessions || []).some(s => (s[1] || "").startsWith(d));
}
function textOf(e) {
  return [e.name, e.venue, e.game, e.start_time, e.late_registration, e.buyin, e.guarantee,
    (e.flags || []).join(" "), e.eligibility, e.special, e.notes].join(" ").toLowerCase();
}
function baseRows() {
  let rows = DATA.events.slice();
  if (state.venuePage) rows = rows.filter(e => e.venue === state.venuePage);
  if (state.venue) rows = rows.filter(e => e.venue === state.venue);
  if (state.date) rows = rows.filter(e => rowMatchesDate(e, state.date));
  if (state.q) rows = rows.filter(e => textOf(e).includes(state.q.toLowerCase()));
  if (state.hideSeparate) rows = rows.filter(e => !(e.flags || []).includes("satellite"));
  if (state.singleOnly) rows = rows.filter(e => e.single_entry_confirmed === true);
  return rows;
}
function rankRows(rows) {
  // Rank only when buy-in + guarantee (prize-pool basis) are confirmed; ratio is descriptive, not a forecast.
  return rows.slice().sort((a, b) => {
    const ra = (typeof a.guarantee === "number" && a.guarantee_basis === "prize pool") ? a.guarantee / a.buyin : -1;
    const rb = (typeof b.guarantee === "number" && b.guarantee_basis === "prize pool") ? b.guarantee / b.buyin : -1;
    if (rb !== ra) return rb - ra;
    return (a.buyin || 0) - (b.buyin || 0);
  });
}

/* ---------------- tournaments table ---------------- */
function renderTournaments() {
  const host = $("#tournaments-body");
  if (!host) return;
  const rows = rankRows(baseRows());
  $("#t-count").textContent = rows.length;
  host.innerHTML = rows.map(e => {
    const ratio = (typeof e.guarantee === "number" && e.guarantee_basis === "prize pool")
      ? (e.guarantee / e.buyin).toFixed(1) + "×" : blank;
    const se = e.single_entry_confirmed ? `<span class="badge ok">confirmed</span>`
      : `<span class="badge warn">unverified</span>`;
    return `<tr>
      <td>${esc(e.venue)}<div class="small muted">${esc(e.room || "")}</div></td>
      <td><strong>${esc(e.name)}</strong>${(e.event_no ? ` <span class="muted small">#${e.event_no}</span>` : "")}
        <div>${badgeFor(e)}</div>
        ${e.bounty_text ? `<div class="excerpt">bounty: ${esc(e.bounty_text)}</div>` : ""}
        ${e.discount_official ? `<div class="excerpt">${esc(e.discount_official)}</div>` : ""}</td>
      <td class="small">${sessionsText(e) || esc(e.weekdays ? e.weekdays.join(", ") : "")}</td>
      <td>${esc(e.start_time || "")}</td>
      <td class="num">${money(e.buyin)}</td>
      <td class="num">${e.house_fee != null ? money(e.house_fee) : blank}<div class="small muted">${e.pool_contribution != null ? "pool " + money(e.pool_contribution) : "split unverified"}</div></td>
      <td class="num">${e.guarantee != null ? money(e.guarantee) : blank}<div class="small muted">${esc(e.guarantee_basis || "")}</div></td>
      <td class="num">${ratio}</td>
      <td class="small">${esc(e.starting_stack != null ? e.starting_stack.toLocaleString("en-US") : blank)}<div class="small muted">${esc(e.level_minutes ? e.level_minutes + " min lvls" : "")}</div></td>
      <td class="small">${esc(e.late_registration || blank)}</td>
      <td>${se}</td>
      <td class="small">${srcLinks(e)}<div class="small muted">last checked ${esc(e.last_checked || "")}</div></td>
    </tr>`;
  }).join("") || `<tr><td colspan="12" class="muted">No events match the current filters. (With the single-entry toggle ON this list is honestly empty — no event has official single-entry wording yet. See Flagged F1–F3.)</td></tr>`;

  // Separate section: officially confirmed re-entry / rebuy / add-on events
  const sep = DATA.events.filter(e =>
    (e.venue === "Wynn" && (e.id || "").startsWith("WYNN-DAILY")) ||
    /re-entry|rebuy|subsequent buy/i.test((e.reentry_official || "") + (e.addon_official || "") + (e.single_entry_status || "")));
  const sepHost = $("#reentry-body");
  if (sepHost) {
    sepHost.innerHTML = sep.map(e => `<tr>
      <td>${esc(e.venue)}</td><td><strong>${esc(e.name)}</strong></td>
      <td class="small">${sessionsText(e) || esc((e.weekdays || []).join(", "))}</td>
      <td class="num">${money(e.buyin)}</td>
      <td class="small">${esc((e.reentry_official || e.addon_official || "").slice(0, 300))}</td>
      <td class="small">${srcLinks(e, 2)}</td></tr>`).join("");
  }
  // Satellites section
  const satHost = $("#satellites-body");
  if (satHost) {
    const sats = (DATA.satellites || []).filter(s => !state.venuePage || s.venue === state.venuePage)
      .filter(s => !state.date || (s.sessions || []).some(x => (x[1] || "").startsWith(state.date)));
    satHost.innerHTML = sats.map(e => `<tr>
      <td>${esc(e.venue)}</td><td><strong>${esc(e.name)}</strong></td>
      <td class="small">${sessionsText(e)}</td>
      <td class="num">${money(e.buyin)}</td>
      <td class="num">${esc(typeof e.guarantee === "number" ? money(e.guarantee) : (e.guarantee || blank))}</td>
      <td class="small">${srcLinks(e)}</td></tr>`).join("");
  }
}

/* ---------------- schedule ---------------- */
function renderSchedule() {
  const host = $("#schedule-body");
  if (!host) return;
  const d = state.date;
  if (!d) { host.innerHTML = `<tr><td colspan="6" class="muted">Pick a date above to build that day's plan.</td></tr>`; return; }
  const dayRows = [];
  DATA.events.concat(DATA.satellites || []).forEach(e => {
    (e.sessions || []).forEach(s => { if ((s[1] || "") === d) dayRows.push({ e, s }); });
  });
  dayRows.sort((a, b) => (a.s[2] || "").localeCompare(b.s[2] || ""));
  if (!dayRows.length) {
    host.innerHTML = `<tr><td colspan="6" class="muted">No scheduled sessions on ${esc(d)} in the loaded official calendars (Venetian DSE IV runs Nov 16–Dec 23; WPT series Nov 27–Dec 21, 2026).</td></tr>`;
    return;
  }
  // Overlap check: two sessions that cannot be played in sequence are flagged.
  // No official finish times are published, so this uses start times + late-registration windows and is labeled "possible".
  const startMin = t => { const m = t.match(/(\d+):(\d+)\s*(AM|PM)/i); if (!m) return 0; let h = +m[1] % 12 + (m[3].toUpperCase() === "PM" ? 12 : 0); return h * 60 + +m[2]; };
  const flags = dayRows.map((r, i) => {
    const st = startMin(r.s[2]);
    let note = [];
    dayRows.forEach((o, j) => {
      if (i === j) return;
      const os = startMin(o.s[2]);
      if (os > st && os - st < 300 && (o.e.venue === r.e.venue)) note.push(`overlaps window of ${o.e.name} (${esc(o.s[2])}, same venue)`);
      else if (os > st && os - st < 240) note.push(`tight transfer to ${esc(o.e.name)} at ${esc(o.s[2])} (${esc(o.e.venue)})`);
    });
    return note;
  });
  const primary = dayRows[0];
  host.innerHTML = dayRows.map((r, i) => `<tr>
    <td>${i === 0 ? `<span class="badge acc">primary (earliest)</span>` : (r.e.venue !== primary.e.venue ? `<span class="badge">conditional fallback</span>` : "")}</td>
    <td>${esc(r.e.venue)}</td>
    <td><strong>${esc(r.e.name)}</strong>${(r.e.event_no ? ` <span class="muted small">#${r.e.event_no}</span>` : "")}<div>${badgeFor(r.e)}</div></td>
    <td>${esc(r.s[2])}<div class="small muted">${esc(r.s[0])}</div></td>
    <td class="small">${money(r.e.buyin)}${r.e.guarantee != null ? " · gtd " + money(r.e.guarantee) : ""}<div class="small muted">LR: ${esc(r.e.late_registration || "unverified")}</div></td>
    <td class="small">${flags[i].length ? `<span class="badge bad">possible overlap</span> ` + flags[i].join("; ") : `<span class="badge ok">no same-day conflict detected</span>`}<div class="small muted">finish times are not officially published — this is a start/LR-window check, not a confirmed-playable guarantee</div></td>
  </tr>`).join("");
}

/* ---------------- hotels ---------------- */
function walkCell(h) {
  const mins = state.walkVenue === "venetian" ? h.walk_to_venetian_min : h.walk_to_wynn_min;
  const linkKey = state.walkVenue === "venetian" ? "to_venetian_poker" : "to_wynn_poker";
  const link = (h.map_links || {})[linkKey] || (h.map_links || {})["to_venetian_poker"];
  return `${mins != null ? mins + " min (est.)" : blank} ${link ? `<a class="src" href="${esc(link)}" target="_blank" rel="noopener">maps</a>` : ""}`;
}
function renderHotels() {
  const host = $("#hotels-body");
  if (!host) return;
  let rows = HOTELS.hotels.slice();
  if (state.walkVenue === "wynn") rows = rows.filter(h => h.walk_to_wynn_min != null);
  if (state.walkMax30) rows = rows.filter(h => {
    const m = state.walkVenue === "venetian" ? h.walk_to_venetian_min : h.walk_to_wynn_min;
    return m != null && m <= 30;
  });
  rows.sort((a, b) => (a.walk_to_venetian_min || 0) - (b.walk_to_venetian_min || 0));
  $("#h-count").textContent = rows.length;
  host.innerHTML = rows.map(h => `<tr>
    <td><strong>${esc(h.property)}</strong><div class="small muted">${esc(h.brand || "")}</div></td>
    <td class="small">${esc(h.poker_room || blank)}</td>
    <td class="num">${walkCell(h)}</td>
    <td class="num">${esc(h.resort_fee || `<span class="badge warn">unverified</span>`)}
      <div class="small muted">${h.resort_fee_retrieved ? "checked " + esc(h.resort_fee_retrieved) : "official fee page not reachable — see Flagged F11"}</div></td>
    <td class="num">${esc(h.nightly_rate || `<span class="badge warn">unverified</span>`)}</td>
    <td class="small">${esc(h.parking || blank)}</td>
    <td class="small">${esc(h.cancellation || `<span class="badge warn">unverified</span>`)}</td>
    <td class="small"><a href="${esc(h.booking_link)}" target="_blank" rel="noopener">official booking</a>
      <div class="small muted">${(h.sources || []).slice(0, 1).map(s => `<a class="src" href="${esc(s)}" target="_blank" rel="noopener">source</a>`).join("")}</div></td>
    <td class="small">${esc(h.notes || "")}</td>
  </tr>`).join("");
}

/* ---------------- rate log ---------------- */
function renderRateLog() {
  const host = $("#ratelog-body");
  if (!host) return;
  host.innerHTML = RATELOG.entries.map(x => `<tr>
    <td>${esc(x.date)}</td><td>${esc(x.property)}</td><td>${esc(x.item)}</td>
    <td>${esc(x.value)}</td>
    <td class="small"><a href="${esc(x.source)}" target="_blank" rel="noopener">official source</a></td>
    <td class="small muted">${esc(x.method || "")}</td></tr>`).join("");
}

/* ---------------- flagged / review ---------------- */
function renderFlags() {
  const host = $("#flags-body");
  if (!host) return;
  host.innerHTML = FLAGS.items.map(f => `<tr>
    <td><span class="badge ${f.severity === "important" ? "bad" : f.severity === "moderate" ? "warn" : ""}">${esc(f.severity)}</span> <strong>${esc(f.id)}</strong></td>
    <td>${esc(f.title)}</td>
    <td class="small">${esc(f.detail)}</td>
    <td class="small">${(f.sources || []).map(s => `<a class="src" href="${esc(s)}" target="_blank" rel="noopener">source</a>`).join(" · ") || "—"}</td>
    <td class="small muted">${esc(f.action || "—")}</td></tr>`).join("");
}

/* ---------------- sources ---------------- */
function renderSources() {
  const host = $("#sources-body");
  if (!host) return;
  const seen = new Map();
  DATA.events.concat(DATA.satellites || []).forEach(e => (e.sources || []).forEach(s => {
    if (!seen.has(s.url)) seen.set(s.url, { label: s.label, excerpt: s.excerpt, retrieved: s.retrieved });
  }));
  HOTELS.hotels.forEach(h => (h.sources || []).forEach(s => {
    if (!seen.has(s)) seen.set(s, { label: "hotel official page", retrieved: HOTELS.meta && HOTELS.meta.built });
  }));
  FLAGS.items.forEach(f => (f.sources || []).forEach(s => { if (!seen.has(s)) seen.set(s, { label: "flag reference", retrieved: FLAGS.meta.updated }); }));
  RATELOG.entries.forEach(x => { if (!seen.has(x.source)) seen.set(x.source, { label: x.item, retrieved: x.date }); });
  const rows = Array.from(seen.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  $("#s-count").textContent = rows.length;
  host.innerHTML = rows.map(([url, s]) => {
    const c = CHECKS && CHECKS[url];
    return `<tr><td class="small"><a href="${esc(url)}" target="_blank" rel="noopener">${esc(url.length > 90 ? url.slice(0, 90) + "…" : url)}</a></td>
      <td class="small">${esc(s.label || "")}</td>
      <td class="small muted">${esc((s.excerpt || "").slice(0, 160))}</td>
      <td class="small">${esc(s.retrieved || "")}</td>
      <td class="small">${c ? (c.ok ? `<span class="badge ok">checked ${esc((c.checkedAt || "").slice(0, 10))}${c.changed ? " · CHANGED" : ""}</span>` : `<span class="badge bad">unreachable ${esc((c.checkedAt || "").slice(0, 10))}</span>`) : `<span class="badge">scheduled check pending</span>`}</td></tr>`;
  }).join("");
}

/* ---------------- calculators ---------------- */
function bindCalculators() {
  const nights = $("#c-nights"), rate = $("#c-rate"), fee = $("#c-fee"), entries = $("#c-entries"),
        buyin = $("#c-buyin"), outNight = $("#c-out-night"), outTrip = $("#c-out-trip");
  if (!nights) return;
  function calc() {
    const n = +nights.value || 0, r = +rate.value || 0, f = +fee.value || 0, en = +entries.value || 0, b = +buyin.value || 0;
    const trueNight = (r + f) * (1 + TAX);
    outNight.textContent = "$" + trueNight.toFixed(2);
    outTrip.textContent = "$" + (en * b + n * trueNight).toFixed(2);
  }
  [nights, rate, fee, entries, buyin].forEach(el => el.addEventListener("input", calc));
  fee.value = 55; calc(); // prefill Venetian verified fee
}

/* ---------------- filters ---------------- */
function bindFilters() {
  const q = $("#f-q"), date = $("#f-date"), venue = $("#f-venue"), single = $("#f-single"), hideS = $("#f-hide-sat");
  const upd = () => {
    state.q = q ? q.value.trim() : "";
    state.date = date ? date.value : "";
    state.venue = venue ? venue.value : "";
    state.singleOnly = single ? single.checked : false;
    state.hideSeparate = hideS ? hideS.checked : true;
    renderTournaments(); renderSchedule();
  };
  if (q) q.addEventListener("input", upd);
  if (date) date.addEventListener("input", upd);
  if (venue) venue.addEventListener("change", upd);
  if (single) single.addEventListener("change", upd);
  if (hideS) hideS.addEventListener("change", upd);

  const wv = $("#f-walk-venue"), w30 = $("#f-walk30");
  const updH = () => {
    state.walkVenue = wv ? wv.value : "venetian";
    state.walkMax30 = w30 ? w30.checked : true;
    renderHotels();
  };
  if (wv) wv.addEventListener("change", updH);
  if (w30) w30.addEventListener("change", updH);
}

function fillVenueSelect() {
  const sel = $("#f-venue");
  if (!sel) return;
  const venues = Array.from(new Set(DATA.events.map(e => e.venue)));
  sel.innerHTML = `<option value="">All venues</option>` + venues.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join("");
}

function renderKpis() {
  const set = (id, v) => { const el = $(id); if (el) el.textContent = v; };
  set("#k-events", DATA.events.length + (DATA.satellites || []).length);
  set("#k-venues", new Set(DATA.events.map(e => e.venue)).size);
  set("#k-single", DATA.events.filter(e => e.single_entry_confirmed).length);
  set("#k-flags", FLAGS.items.length);
  set("#k-sources", $("#sources-body") ? $("#sources-body").children.length : null);
}

async function loadJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(url + " " + res.status);
  return res.json();
}

async function init() {
  const jobs = [loadJSON("data/tournaments.json"), loadJSON("data/hotels.json"),
                loadJSON("data/flagged.json"), loadJSON("data/rate-log.json")];
  const results = await Promise.allSettled(jobs);
  if (results[0].status === "fulfilled") DATA = results[0].value;
  if (results[1].status === "fulfilled") HOTELS = results[1].value;
  if (results[2].status === "fulfilled") FLAGS = results[2].value;
  if (results[3].status === "fulfilled") RATELOG = results[3].value;
  try { CHECKS = await loadJSON("data/url-checks.json"); } catch (e) { CHECKS = null; }
  fillVenueSelect(); bindFilters(); bindCalculators();
  renderTournaments(); renderSchedule(); renderHotels(); renderRateLog(); renderFlags(); renderSources(); renderKpis();
}
document.addEventListener("DOMContentLoaded", init);
})();
