const OFFICIAL = {
  schedule: 'https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html',
  main: 'https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament.html',
  pokerRates: 'https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html',
  resortFee: 'https://www.venetianlasvegas.com/resort/resort-fee.html',
  hotelTerms: 'https://www.venetianlasvegas.com/legal/hotel-terms-and-conditions.html',
  booking: 'https://www.venetianlasvegas.com/book',
  bellagioPoker: 'https://bellagio.mgmresorts.com/en/casino/poker.html'
};
const pdf = (n) => `https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_${n}.pdf`;

const events = [
  {date:'2026-11-17',time:'11:10 AM',id:'1C',name:'$300 NLH — Event 1C',buy:300,guarantee:75000,format:'Multi-flight / multiday',pdf:10,group:'review',venue:'The Venetian',note:'Event 1A–1D share event number 1; later flight entry/re-entry policy is not established in the public structure.'},
  {date:'2026-11-17',time:'5:10 PM',id:'1D',name:'$300 NLH — Event 1D',buy:300,guarantee:75000,format:'Multi-flight / multiday',pdf:9,group:'review',venue:'The Venetian',note:'Event 1A–1D share event number 1; later flight entry/re-entry policy is not established in the public structure.'},
  {date:'2026-11-18',time:'11:10 AM',id:'2',name:'$300 NLH (1 day)',buy:300,guarantee:10000,format:'One day',pdf:5,group:'candidate',venue:'The Venetian',note:'Event 1 Day 2 restart is scheduled at noon the same day, so the events can overlap. Re-entry policy is unverified.'},
  {date:'2026-11-19',time:'10:10 AM',id:'3',name:'$200 NLH RaceDay Stack (1 day)',buy:200,guarantee:null,format:'One day',pdf:18,group:'candidate',venue:'The Venetian',note:'Guarantee not listed in the schedule/structure consulted; single-entry is unverified.'},
  {date:'2026-11-20',time:'10:10 AM',id:'4',name:'$200 NLH RaceDay Stack (1 day)',buy:200,guarantee:null,format:'One day',pdf:18,group:'candidate',venue:'The Venetian',note:'Guarantee not listed in the schedule/structure consulted; single-entry is unverified.'},
  {date:'2026-11-21',time:'10:10 AM',id:'5',name:'$200 NLH RaceDay Stack (1 day)',buy:200,guarantee:null,format:'One day',pdf:18,group:'candidate',venue:'The Venetian',note:'Guarantee not listed in the schedule/structure consulted; single-entry is unverified.'},
  {date:'2026-11-22',time:'11:10 AM',id:'6',name:'$200 NLH (1 day)',buy:200,guarantee:null,format:'One day',pdf:29,group:'candidate',venue:'The Venetian',note:'Guarantee not listed in the schedule/structure consulted; single-entry is unverified.'},
  {date:'2026-11-23',time:'11:10 AM',id:'7A',name:'$400 NLH — Event 7, Flight 1A',buy:400,guarantee:75000,format:'Multi-flight / multiday',pdf:2,group:'review',venue:'The Venetian',note:'Flights 1A–1C combine on Day 2. Structure forbids a player who bags Day 2 from entering a later flight; re-entry before bagging is not stated.'},
  {date:'2026-11-24',time:'11:10 AM',id:'7B',name:'$400 NLH — Event 7, Flight 1B',buy:400,guarantee:75000,format:'Multi-flight / multiday',pdf:2,group:'review',venue:'The Venetian',note:'Flights 1A–1C combine on Day 2. Structure forbids a player who bags Day 2 from entering a later flight; re-entry before bagging is not stated.'},
  {date:'2026-11-25',time:'11:10 AM',id:'10',name:'$400 NLH (1 day)',buy:400,guarantee:15000,format:'One day',pdf:6,group:'candidate',venue:'The Venetian',note:'Event 7 Day 2 restart is scheduled at 11:00 AM, so the events overlap. Re-entry policy is unverified.'},
  {date:'2026-11-26',time:'11:10 AM',id:'12',name:'$300 NLH (1 day)',buy:300,guarantee:10000,format:'One day',pdf:5,group:'candidate',venue:'The Venetian',note:'No re-entry wording found in the linked structure; single-entry is unverified.'},
  {date:'2026-11-27',time:'11:10 AM',id:'14',name:'$600 NLH (1 day)',buy:600,guarantee:30000,format:'One day',pdf:7,group:'candidate',venue:'The Venetian',note:'No re-entry wording found in the linked structure; single-entry is unverified.'},
  {date:'2026-11-23',time:'5:10 PM',id:'8',name:'$200 NLH Progressive Knock-Out Bounty (1 day)',buy:200,guarantee:8000,format:'PKO bounty',pdf:30,group:'secondary',venue:'The Venetian',note:'Bounty payout model; $8,000 guarantee includes bounty amounts. Re-entry status unverified.'},
  {date:'2026-11-24',time:'5:10 PM',id:'9',name:'$200 NLH Bounty (1 day)',buy:200,guarantee:8000,format:'Bounty',pdf:1,group:'secondary',venue:'The Venetian',note:'$8,000 guarantee includes bounty amounts; separate from plain NLH shortlist. Re-entry status unverified.'},
  {date:'2026-11-28',time:'11:10 AM',id:'16',name:'$600 NLH Bounty (1 day)',buy:600,guarantee:30000,format:'Bounty',pdf:11,group:'secondary',venue:'The Venetian',note:'Bounty structure changes payout design; include only if bounty play is acceptable. Re-entry is unverified.'},
  {date:'2026-11-28',time:'5:10 PM',id:'18',name:'$200 PokerAtlas Valuetown Bounty',buy:200,guarantee:20000,format:'Bounty / conditional discount',pdf:8,group:'secondary',venue:'The Venetian',note:'PokerAtlas PRO membership + claiming the offer in its app is required; first $200 buy-in drops to $180; subsequent entries cost $200. Membership price is not stated.'},
  {date:'2026-11-29',time:'11:10 AM',id:'19A',name:'$400 NLH — Event 19, Flight 1A',buy:400,guarantee:75000,format:'Multi-flight / multiday',pdf:3,group:'review',venue:'The Venetian',note:'Flights 1A–1C combine on Day 2. Structure forbids a player who bags Day 2 from entering a later flight; re-entry before bagging is not stated.'},
  {date:'2026-11-30',time:'11:10 AM',id:'19B',name:'$400 NLH — Event 19, Flight 1B',buy:400,guarantee:75000,format:'Multi-flight / multiday',pdf:3,group:'review',venue:'The Venetian',note:'Flights 1A–1C combine on Day 2. Structure forbids a player who bags Day 2 from entering a later flight; re-entry before bagging is not stated.'},
  {date:'2026-12-01',time:'11:10 AM',id:'19C',name:'$400 NLH — Event 19, Flight 1C',buy:400,guarantee:75000,format:'Multi-flight / multiday',pdf:3,group:'review',venue:'The Venetian',note:'Flights 1A–1C combine on Day 2. Structure forbids a player who bags Day 2 from entering a later flight; re-entry before bagging is not stated.'},
  {date:'2026-12-03',time:'11:10 AM',id:'26A',name:'$800 NLH — Event 26, Flight 1A',buy:800,guarantee:500000,format:'Multi-flight / multiday',pdf:12,group:'review',venue:'The Venetian',note:'Multiple starting flights and a shared Day 2. Re-entry policy not established; high buy-in makes this poor fit for strict single-entry cost control.'},
  {date:'2026-12-03',time:'5:10 PM',id:'26B',name:'$800 NLH — Event 26, Flight 1B',buy:800,guarantee:500000,format:'Multi-flight / multiday',pdf:13,group:'review',venue:'The Venetian',note:'Multiple starting flights and a shared Day 2. Re-entry policy not established; high buy-in makes this poor fit for strict single-entry cost control.'},
  {date:'2026-12-04',time:'11:10 AM',id:'26C',name:'$800 NLH — Event 26, Flight 1C',buy:800,guarantee:500000,format:'Multi-flight / multiday',pdf:12,group:'review',venue:'The Venetian',note:'Multiple starting flights and a shared Day 2. Re-entry policy not established; high buy-in makes this poor fit for strict single-entry cost control.'},
  {date:'2026-12-04',time:'5:10 PM',id:'26D',name:'$800 NLH — Event 26, Flight 1D',buy:800,guarantee:500000,format:'Multi-flight / multiday',pdf:13,group:'review',venue:'The Venetian',note:'Multiple starting flights and a shared Day 2. Re-entry policy not established; high buy-in makes this poor fit for strict single-entry cost control.'},
  {date:'2026-12-05',time:'11:10 AM',id:'26E',name:'$800 NLH — Event 26, Flight 1E',buy:800,guarantee:500000,format:'Multi-flight / multiday',pdf:12,group:'review',venue:'The Venetian',note:'Multiple starting flights and a shared Day 2. Re-entry policy not established; high buy-in makes this poor fit for strict single-entry cost control.'},
  {date:'2026-12-05',time:'5:10 PM',id:'26F',name:'$800 NLH — Event 26, Flight 1F Turbo',buy:800,guarantee:500000,format:'Multi-flight / multiday',pdf:14,group:'review',venue:'The Venetian',note:'Turbo starting flight in a shared multi-flight event; re-entry policy not established. Higher spend and format risk; exclude from strict shortlist.'},
  {date:'2026-12-06',time:'11:10 AM',id:'28',name:'$600 NLH (1 day)',buy:600,guarantee:40000,format:'One day',pdf:7,group:'candidate',venue:'The Venetian',note:'Event 26 Day 2 restart is scheduled at noon, overlapping this start. Re-entry policy is unverified.'},
  {date:'2026-12-17',time:'10:10 AM',id:'56A',name:'$1,100 NLH — Event 56, Flight 1A',buy:1100,guarantee:500000,format:'Multi-flight / multiday',pdf:35,group:'review',venue:'The Venetian',note:'$500,000 guarantee; multiple flights / Day 2. Flight 1A offers $40 off house fee before start ($1,060 instead of $1,100). Higher buy-in; re-entry unverified.'},
  {date:'2026-12-17',time:'6:10 PM',id:'56B',name:'$1,100 NLH — Event 56, Flight 1B',buy:1100,guarantee:500000,format:'Multi-flight / multiday',pdf:36,group:'review',venue:'The Venetian',note:'$500,000 guarantee; multiple flights / Day 2. Flight 1B offers $40 off house fee before start ($1,060 instead of $1,100). Higher buy-in; re-entry unverified.'},
  {date:'2026-12-18',time:'10:10 AM',id:'56C',name:'$1,100 NLH — Event 56, Flight 1C',buy:1100,guarantee:500000,format:'Multi-flight / multiday',pdf:35,group:'review',venue:'The Venetian',note:'$500,000 event guarantee; multiple starting flights / Day 2. Higher buy-in, re-entry policy not established.'},
  {date:'2026-12-18',time:'6:10 PM',id:'56D',name:'$1,100 NLH — Event 56, Flight 1D',buy:1100,guarantee:500000,format:'Multi-flight / multiday',pdf:36,group:'review',venue:'The Venetian',note:'$500,000 guarantee; multiple flights / Day 2. Flight 1B/1D structure offers $40 off house fee before start ($1,060 instead of $1,100). Higher buy-in; re-entry unverified.'},
  {date:'2026-12-19',time:'10:10 AM',id:'56E',name:'$1,100 NLH — Event 56, Flight 1E',buy:1100,guarantee:500000,format:'Multi-flight / multiday',pdf:35,group:'review',venue:'The Venetian',note:'$500,000 event guarantee; multiple starting flights / Day 2. Higher buy-in, re-entry policy not established.'},
  {date:'2026-12-20',time:'11:10 AM',id:'59A',name:'$600 NLH — Event 59, Flight 1A',buy:600,guarantee:150000,format:'Multi-flight / multiday',pdf:4,group:'review',venue:'The Venetian',note:'Event 56 Day 2 starts at 11:00 AM (overlap). $150,000 guarantee; Flight 1A offers $20 off house fee before start ($580 instead of $600); re-entry unverified.'},
  {date:'2026-12-21',time:'11:10 AM',id:'59B',name:'$600 NLH — Event 59, Flight 1B',buy:600,guarantee:150000,format:'Multi-flight / multiday',pdf:4,group:'review',venue:'The Venetian',note:'$150,000 event guarantee; three starting flights and Day 2. Re-entry policy not established.'},
  {date:'2026-12-22',time:'11:10 AM',id:'59C',name:'$600 NLH — Event 59, Flight 1C',buy:600,guarantee:150000,format:'Multi-flight / multiday',pdf:4,group:'review',venue:'The Venetian',note:'$150,000 event guarantee; three starting flights and Day 2. Re-entry policy not established.'},
  {date:'2026-12-23',time:'11:10 AM',id:'63',name:'$600 NLH (1 day)',buy:600,guarantee:30000,format:'One day',pdf:7,group:'candidate',venue:'The Venetian',note:'Event 59 Day 2 starts at 11:00 AM, so the events overlap. Re-entry policy is unverified.'}
];

const money = (v) => v == null ? '<span class="unknown" title="No official value confirmed">—</span>' : `$${Number(v).toLocaleString('en-US')}`;
const officialLink = (url,label='Official source') => `<a class="source-link" href="${url}" target="_blank" rel="noopener">${label} ↗</a>`;
const dateText = (s) => new Date(`${s}T12:00:00Z`).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'});

// ---------- filter state ----------
let state = {
  date: '',        // 'YYYY-MM-DD' or ''
  singleEntry: false, // if true, show only rows confirmed single-entry (none currently)
  venue: '',       // venue name or ''
  q: ''            // search text
};

// ---------- source re-check / change monitoring ----------
const CHECK_STORAGE = 'poker4_source_checks';
const CHECK_INTERVAL_MS = 24 * 60 * 60 * 1000; // consider a cached check fresh for 24h

function getChecks(){
  try{ return JSON.parse(localStorage.getItem(CHECK_STORAGE) || '{}'); } catch(e){ return {}; }
}
function setChecks(c){ try{ localStorage.setItem(CHECK_STORAGE, JSON.stringify(c)); } catch(e){} }

let urlChecks = {};
async function loadUrlChecks(){
  try{
    const res = await fetch('data/url-checks.json', { cache: 'no-store' });
    if (res.ok) urlChecks = await res.json();
  } catch(e){
    urlChecks = getChecks();
  }
}

function rowChecks(e){
  return urlChecks[pdf(e.pdf)] || urlChecks[OFFICIAL.schedule] || { lastChecked: new Date().toISOString(), status: 'unchecked', changed: false };
}

async function httpHeaders(url){
  const ctrl = new AbortController();
  const to = setTimeout(()=>ctrl.abort(), 12000);
  try{
    const res = await fetch(url, { method:'HEAD', cache:'no-store', signal: ctrl.signal });
    const h = {};
    for (const k of ['etag','last-modified','content-length']) {
      const v = res.headers.get(k);
      if (v) h[k] = v;
    }
    return { ok: true, status: res.status, headers: h, url: res.url };
  } catch(e){
    return { ok: false, error: e && e.message ? e.message : 'request failed', status: null, headers: {} };
  } finally{ clearTimeout(to); }
}

// returns {lastChecked, status, changed, detail} for a source url, using cache when fresh
async function checkSource(url){
  const now = new Date().toISOString();
  const checks = getChecks();
  const prev = checks[url];
  const fresh = prev && prev.checkedAt && (Date.now() - new Date(prev.checkedAt).getTime()) < CHECK_INTERVAL_MS;
  if (fresh) return { lastChecked: prev.checkedAt, status: prev.status, changed: prev.changed, detail: prev.detail, cached: true };

  const result = await httpHeaders(url);
  let changed = false;
  let detail = '';
  let status;
  if (!result.ok){
    status = 'unavailable';
    detail = result.error || 'could not reach';
  } else {
    status = 'reachable';
    const keyFields = ['etag','last-modified'];
    if (prev && prev.headers){
      changed = keyFields.some(k => prev.headers[k] && result.headers[k] && prev.headers[k] !== result.headers[k]);
    }
    detail = `HTTP ${result.status}` + (result.headers['last-modified'] ? ` · modified ${result.headers['last-modified']}` : '');
  }
  const out = { url, lastChecked: now, status, changed, detail, cached: false };
  checks[url] = out;
  setChecks(checks);
  return out;
}

function statusPill(status, changed){
  if (!status || status === 'unchecked') return '<span class="pill warn">not yet checked</span>';
  if (status === 'unavailable') return '<span class="pill warn">re-check unavailable</span>';
  if (changed) return '<span class="pill danger">source changed</span>';
  return '<span class="pill">source unchanged</span>';
}

// ---------- rendering ----------
function rowFor(e){
  const check = rowChecks(e);
  const ratio = e.guarantee==null ? '<span class="unknown" title="Not calculable without a published guarantee">—</span>' : `${(e.guarantee/e.buy).toFixed(1)}×`;
  const singleEntryPill = '<span class="pill warn">single-entry unverified</span>';
  const venueChip = `<span class="tag" style="background:#edf4f0;color:#405650">${escapeHtml(e.venue)}</span>`;
  const sourcesCell = `${officialLink(OFFICIAL.schedule,'Schedule')}<br>${officialLink(pdf(e.pdf),'Structure')}`;
  const lastCheckedCell = `<div class="lastchecked"><small>Last checked ${new Date(check.lastChecked).toLocaleString()}</small><br>${statusPill(check.status,check.changed)}<br><button class="recheck" data-url="${escapeHtml(e ? (pdf(e.pdf)||OFFICIAL.schedule) : OFFICIAL.schedule)}" title="Re-check this source">Re-check</button></div>`;
  return `<tr><td>${dateText(e.date)}</td><td>${e.time}</td><td>${e.id}</td><td>${venueChip} ${e.name}<small>${e.note}</small></td><td>${money(e.buy)}</td><td>${money(e.guarantee)}</td><td>${ratio}</td><td>${e.format}</td><td>${singleEntryPill}</td><td>${lastCheckedCell}</td><td>${sourcesCell}</td></tr>`;
}

function escapeHtml(s){ const d=document.createElement('div'); d.textContent=s==null?'':String(s); return d.innerHTML; }

function renderEvents(targetId, group, list){
  const root=document.getElementById(targetId); if(!root)return;
  const groups = Array.isArray(group) ? group : [group];
  const rows=(list||events).filter(e=>groups.includes(e.group)).sort((a,b)=>a.date.localeCompare(b.date)||a.time.localeCompare(b.time));
  let html='';
  for (const e of rows){
    // venue filter
    if (state.venue && e.venue !== state.venue) continue;
    // single-entry filter: none confirmed, so show only confirmed single-entry -> none
    if (state.singleEntry && e.singleEntryConfirmed !== true) continue;
    // date filter
    if (state.date && e.date !== state.date) continue;
    // search
    if (state.q){
      const hay = `${e.date} ${e.time} ${e.id} ${e.name} ${e.note} ${e.venue} ${e.buy}`.toLowerCase();
      if (!hay.includes(state.q)) continue;
    }
    html += rowFor(e);
  }
  root.innerHTML = html || '<tr><td colspan="11">No entries match the current filters.</td></tr>';
}

function renderReview(){
  const root=document.getElementById('review-events'); if(!root)return;
  const list=[...events];
  html=list.filter(e=>e.group==='review'||e.group==='secondary').map(e=>`<tr><td>${dateText(e.date)} · ${e.time}</td><td>${e.name}</td><td>${e.note}</td><td>${officialLink(OFFICIAL.schedule,'Schedule')}<br>${officialLink(pdf(e.pdf),'Structure')}</td></tr>`).join('');
  root.innerHTML=html;
}

// ---------- re-entry / add-on events from data/tournaments.json ----------
let reentryEvents = [];
async function loadReentry(){
  try{
    const res = await fetch('data/tournaments.json', {cache:'no-store'});
    if (!res.ok) throw new Error('status '+res.status);
    const data = await res.json();
    reentryEvents = (data.reentry_or_addon || []).map(r=>({
      date: r.day,
      time: r.time,
      id: r.event,
      name: r.name,
      buy: r.buy_in,
      guarantee: r.guarantee,
      format: 'Recurring / weekly',
      group: 'reentry',
      venue: r.venue,
      note: (r.reentry_addon || '') + (r.notes ? ' · '+r.notes : ''),
      sources: (r.sources||[]).map(s=>data.sources[s]).filter(Boolean)
    }));
    renderReentry();
  } catch(e){
    console.warn('Could not load re-entry/add-on table:', e);
  }
}

function renderReentry(){
  const root=document.getElementById('reentry-events'); if(!root)return;
  let html='';
  for (const r of reentryEvents){
    if (state.venue && r.venue !== state.venue) continue;
    if (state.singleEntry) continue; // re-entry/add-on rows are explicitly not single-entry
    if (state.date && r.date !== state.date) continue;
    if (state.q){
      const hay = `${r.date} ${r.time} ${r.id} ${r.name} ${r.note} ${r.venue} ${r.buy}`.toLowerCase();
      if (!hay.includes(state.q)) continue;
    }
    const ratio = r.guarantee==null ? '<span class="unknown" title="No published guarantee">—</span>' : `${(r.guarantee/r.buy).toFixed(1)}×`;
    const sourcesCell = (r.sources||[]).map(s=>officialLink(s.url, s.label || 'Source')).join('<br>');
    html += `<tr><td>${r.date}</td><td>${r.time}</td><td>${r.id}</td><td><span class="tag danger">${escapeHtml(r.venue)}</span> ${escapeHtml(r.name)}<small>${escapeHtml(r.note)}</small></td><td>${money(r.buy)}</td><td>${money(r.guarantee)}</td><td>${ratio}</td><td>${r.format}</td><td><span class="pill danger">re-entry / add-on</span></td><td><span class="pill warn">separate section</span></td><td>${sourcesCell}</td></tr>`;
  }
  root.innerHTML = html || '<tr><td colspan="11">No entries match the current filters.</td></tr>';
}

// ---------- filter wiring ----------
function setupFilters(){
  const dateSel = document.querySelector('[data-filter-date]');
  const singleSel = document.querySelector('[data-filter-single]');
  const venueSel = document.querySelector('[data-filter-venue]');
  const searchIn = document.querySelector('[data-table-search]');

  // populate date options from Venetian events + re-entry events
  const dates = new Set();
  const venues = new Set(['The Venetian']);
  events.forEach(e=>{ dates.add(e.date); if(e.venue) venues.add(e.venue); });
  reentryEvents.forEach(r=>{ if(r.date) dates.add(r.date); if(r.venue) venues.add(r.venue); });
  if (dateSel){
    [...dates].sort().forEach(d=>{ const o=document.createElement('option'); o.value=d; o.textContent=dateText(d); dateSel.appendChild(o); });
  }
  if (venueSel){
    [...venues].sort().forEach(v=>{ const o=document.createElement('option'); o.value=v; o.textContent=v; venueSel.appendChild(o); });
  }

  const apply = ()=>{
    renderEvents('candidate-events','candidate');
    renderEvents('other-events',['review','secondary']);
    renderReentry();
    renderReview();
    updateBadge();
  };

  if (dateSel) dateSel.addEventListener('change', ()=>{ state.date = dateSel.value; apply(); });
  if (singleSel) singleSel.addEventListener('change', ()=>{ state.singleEntry = singleSel.checked; apply(); });
  if (venueSel) venueSel.addEventListener('change', ()=>{ state.venue = venueSel.value; apply(); });
  if (searchIn){
    searchIn.addEventListener('input', ()=>{ state.q = searchIn.value.toLowerCase(); apply(); });
  }
  // delegate re-check clicks
  document.addEventListener('click', async (ev)=>{
    const btn = ev.target.closest && ev.target.closest('.recheck');
    if (!btn) return;
    ev.preventDefault();
    const url = btn.getAttribute('data-url');
    btn.textContent = 'Checking…';
    await checkSource(url);
    btn.textContent = 'Re-check';
    apply();
  });

  return apply;
}

function updateBadge(){
  let visible = 0;
  document.querySelectorAll('.tournament-table tbody tr').forEach(tr=>{
    if (tr.hidden) return;
    visible++;
  });
  const el = document.getElementById('visible-count');
  if (el) el.textContent = visible;
}

// ---------- trip cost calculator (shared with hotels page) ----------
function setupTripCalculator(){
  const form = document.getElementById('trip-calculator');
  if (!form) return;
  const outTotal = document.getElementById('calc-total');
  const outBreakdown = document.getElementById('calc-breakdown');
  const calculate = ()=>{
    const entries = parseInt(form.entries.value) || 0;
    const buyin = parseFloat(form.buyin.value) || 0;
    const nights = parseInt(form.nights.value) || 0;
    const rate = parseFloat(form.rate.value) || 0;
    const resortFee = parseFloat(form.resortFee.value) || 0;
    const tax = parseFloat(form.tax.value) || 13.38;
    const parking = parseFloat(form.parking.value) || 0;
    const nightlyTotal = (rate + resortFee) * (1 + tax/100) + parking;
    const hotelTotal = nightlyTotal * nights;
    const entryTotal = entries * buyin;
    const grand = entryTotal + hotelTotal;
    outTotal.textContent = `$${grand.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}`;
    outBreakdown.innerHTML = `
      <strong>Entries × buy-in:</strong> ${entries} × $${buyin.toLocaleString()} = $${entryTotal.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}<br>
      <strong>Hotel:</strong> ($${rate.toLocaleString()} + $${resortFee.toLocaleString()} resort fee) × (1 + ${tax}% tax) = $${((rate+resortFee)*(1+tax/100)).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}/night + $${parking.toFixed(2)} parking<br>
      <strong>Hotel × ${nights} nights:</strong> $${hotelTotal.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}<br>
      <strong>Estimated trip total:</strong> $${entryTotal.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})} + $${hotelTotal.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})} = $${grand.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}<br>
      <small class="muted">Estimate only. Official room rates, fees and taxes must be confirmed for your exact dates.</small>`;
  };
  form.addEventListener('input', calculate);
  calculate();
}

document.addEventListener('DOMContentLoaded', async ()=>{
  await loadUrlChecks();
  renderEvents('candidate-events','candidate');
  renderEvents('other-events',['review','secondary']);
  renderReview();
  await loadReentry();
  setupFilters();
  setupSearch();
  setupTripCalculator();
});
