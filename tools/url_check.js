// Scheduled official-source re-check for the Poker4 dashboard.
// Fetches each tracked official URL, records last-checked + change detection into
// data/url-checks.json. Runs server-side (GitHub Actions) so there is no CORS limit.
const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const OUT = path.join(ROOT, 'data', 'url-checks.json');
const PREV = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, 'utf8')) : {};

// Canonical official URLs referenced by the dashboard. Add/remove here as sources change.
const URLS = [
  'https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html',
  'https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament.html',
  'https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html',
  'https://www.venetianlasvegas.com/resort/resort-fee.html',
  'https://www.venetianlasvegas.com/legal/hotel-terms-and-conditions.html',
  'https://www.venetianlasvegas.com/book',
  'https://www.wynnlasvegas.com/casino/poker',
  'https://bellagio.mgmresorts.com/en/casino/poker.html',
  'https://www.caesars.com/caesars-palace/casino',
  'https://www.caesars.com/caesars-palace/resort-fee',
  'https://www.treasureisland.com/',
  'https://www.caesars.com/harrahs-las-vegas',
  'https://www.caesars.com/horseshoe-las-vegas',
  'https://www.wsop.com/schedule/'
];

// Structure PDFs linked from tournament rows (sampled set; the schedule page is the index).
const PDF_URLS = [
  'https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_1.pdf',
  'https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_5.pdf',
  'https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_6.pdf',
  'https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_7.pdf',
  'https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_29.pdf',
  'https://cdn.wynnresorts.com/image/upload/v1752011191/visitwynn_pdfs_files/Poker/Daily%20Tournaments/Poker-All_Daily_Structures.pdf',
  'https://cdn.wynnresorts.com/image/upload/v1752011166/visitwynn_pdfs_files/Poker/Daily%20Tournaments/poker-daily-tournament-poster.pdf'
];

const TIMEOUT_MS = 20000;

async function fetchHead(url){
  const ctrl = new AbortController();
  const t = setTimeout(()=>ctrl.abort(), TIMEOUT_MS);
  try{
    const res = await fetch(url, { method: 'HEAD', redirect: 'follow', signal: ctrl.signal });
    const h = (k)=>res.headers.get(k)||'';
    return { ok: true, status: res.status, url: res.url,
      etag: h('etag'), 'last-modified': h('last-modified'), 'content-length': h('content-length') };
  } catch(e){
    return { ok: false, status: null, error: String(e && e.message ? e.message : e) };
  } finally{ clearTimeout(t); }
}

function changed(a, b){
  if (!a || !b) return false;
  const keys = ['etag','last-modified','content-length'];
  return keys.some(k => a[k] && b[k] && a[k] !== b[k]);
}

(async ()=>{
  const now = new Date().toISOString();
  const out = {};
  let anyChanged = false;
  for (const url of [...URLS, ...PDF_URLS]){
    const prev = PREV[url];
    const cur = await fetchHead(url);
    const record = { url, checkedAt: now, ok: cur.ok, status: cur.status };
    if (cur.ok){
      record.etag = cur.etag; record['last-modified'] = cur['last-modified'];
      record['content-length'] = cur['content-length']; record.finalUrl = cur.url;
    } else {
      record.error = cur.error;
    }
    record.changed = changed(prev, cur);
    if (record.changed) anyChanged = true;
    out[url] = record;
  }
  fs.writeFileSync(OUT, JSON.stringify(out, null, 2) + '\n');
  console.log(`Checked ${Object.keys(out).length} URLs; changed=${anyChanged}`);
  process.exit(anyChanged ? 0 : 0);
})().catch(e=>{
  console.error(e);
  process.exit(1);
});
