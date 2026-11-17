const fs = require('fs');
const path = require('path');
const { JSDOM } = require(path.join('/tmp/smoke', 'node_modules', 'jsdom'));

const ROOT = '/home/user/Poker4';
let failures = 0;
function ok(cond, label) {
  if (cond) { console.log('  ok  ' + label); }
  else { failures++; console.log('  FAIL ' + label); }
}
function load(file) {
  const html = fs.readFileSync(path.join(ROOT, file), 'utf8');
  const dom = new JSDOM(html, { runScripts: 'dangerously', url: 'https://karagemop466-tech.github.io/Poker4/' + file });
  dom.window.fetch = function () { return Promise.reject(new Error('offline')); };
  dom.window.eval(fs.readFileSync(path.join(ROOT, 'app.js'), 'utf8'));
  return dom;
}
const fire = (dom, el, ev) => el.dispatchEvent(new dom.window.Event(ev, { bubbles: true }));

// ---------- tournaments.html ----------
console.log('tournaments.html');
{
  const dom = load('tournaments.html');
  const d = dom.window.document;
  const activeRows = () => Array.from(d.querySelectorAll('.tabpanel.active tbody tr'));
  const shown = () => activeRows().filter(tr => tr.style.display !== 'none');

  // date filter
  const dateFrom = d.querySelector('#f-from'), dateTo = d.querySelector('#f-to');
  ok(!!dateFrom && !!dateTo, 'date filter exists');
  const before = shown().length;
  ok(before > 50, 'active panel rows visible before filtering (' + before + ')');
  if (dateFrom) {
    dateFrom.value = '2026-12-17'; fire(dom, dateFrom, 'input');
    dateTo.value = '2026-12-17'; fire(dom, dateTo, 'input');
    const day = shown();
    ok(day.length > 0 && day.length < before, 'date filter narrows rows (' + before + ' -> ' + day.length + ')');
    ok(day.filter(tr => tr.className.indexOf('ev-detail') === -1).every(tr => tr.getAttribute('data-date') === '2026-12-17'), 'every visible event row is on the selected date');
    dateFrom.value = ''; fire(dom, dateFrom, 'input');
    dateTo.value = ''; fire(dom, dateTo, 'input');
    ok(shown().length === before, 'clearing dates restores rows');
  }

  // single-entry toggle: only data-single="1" (confirmed) may survive — verified answer is 0
  const single = d.querySelector('#f-single');
  ok(!!single, 'single-entry toggle exists');
  if (single) {
    single.checked = true; fire(dom, single, 'change');
    const s = shown();
    ok(s.every(tr => tr.getAttribute('data-single') === '1'), 'toggle keeps only confirmed single-entry rows');
    ok(s.length === 0, 'toggle shows 0 rows — matches the verified fact that 0 events are confirmed single-entry');
    single.checked = false; fire(dom, single, 'change');
    ok(shown().length === before, 'toggle off restores rows');
  }

  // global search (renders result links, offline index fallback from embedded data)
  const q = d.querySelector('#global-search'), box = d.querySelector('#search-results');
  ok(!!q && !!box, 'global search box + results panel exist');
  if (q) {
    q.value = 'LIPS';
    fire(dom, q, 'input');
    return new Promise((res) => setTimeout(() => {
      const links = box.querySelectorAll('a');
      ok(!box.hasAttribute('hidden') && links.length > 0, 'search shows results (' + links.length + ')');
      ok(Array.from(links).some(a => a.textContent.toLowerCase().indexOf('lips') !== -1), 'results match the query');
      q.value = 'zzzz-no-such-thing'; fire(dom, q, 'input');
      setTimeout(() => {
        ok(box.textContent.indexOf('no match') !== -1, 'no-match query says so');
        // ---------- calculator.html ----------
        console.log('calculator.html');
        const cdom = load('calculator.html');
        const cd = cdom.window.document;
        ok(typeof cdom.window.POKER4 === 'object', 'embedded POKER4 data loaded');
        ok(!!cd.querySelector('#t-grand'), 'trip total output exists');
        const hSel = cd.querySelector('#calc-hotel'), rSel = cd.querySelector('#calc-rate'),
              fSel = cd.querySelector('#calc-fee'), pSel = cd.querySelector('#calc-park'),
              nIn = cd.querySelector('#calc-nights'), rIn = cd.querySelector('#calc-rooms');
        ok(hSel && rSel && fSel && pSel && nIn && rIn, 'all calculator inputs exist');
        hSel.value = 'venetian'; fire(cdom, hSel, 'change');
        const rateOpts = Array.from(rSel.options).filter(o => o.value && !isNaN(parseFloat(o.value)));
        ok(rateOpts.length >= 3, 'rate options rendered from the dated rate log (' + rateOpts.length + ')');
        rSel.value = rateOpts.length ? rateOpts[rateOpts.length - 1].value : '300';
        fire(cdom, rSel, 'change');
        const feeOpt = Array.from(fSel.options).find(o => o.getAttribute('data-fee'));
        ok(!!feeOpt, 'resort fee option carries data-fee');
        if (feeOpt) { fSel.value = feeOpt.value; fire(cdom, fSel, 'change'); }
        nIn.value = '2'; fire(cdom, nIn, 'input');
        rIn.value = '1'; fire(cdom, rIn, 'input');
        const picks = Array.from(cd.querySelectorAll('.ev-pick'));
        ok(picks.length > 10, 'event checkboxes rendered (' + picks.length + ')');
        picks.slice(0, 2).forEach(c => { c.checked = true; fire(cdom, c, 'change'); });

        const num = s => { const m = String(s).replace(/,/g, '').match(/-?\d+(\.\d+)?/); return m ? parseFloat(m[0]) : NaN; };
        const rate = parseFloat(rSel.value), fee = feeOpt ? parseFloat(feeOpt.getAttribute('data-fee')) : NaN;
        const park = pSel.value && !isNaN(parseFloat(pSel.value)) ? parseFloat(pSel.value) : 0;
        const entries = picks.slice(0, 2).reduce((a, c) => a + (parseFloat(c.getAttribute('data-cost')) || 0), 0);
        const night = Math.round((rate + fee) * 1.1338 * 100) / 100;
        const expectHotel = Math.round((night * 2 + park * 2) * 100) / 100;
        const expectGrand = Math.round((expectHotel + entries) * 100) / 100;
        const tNight = cd.querySelector('#t-night').textContent, tHotel = cd.querySelector('#t-hotel').textContent,
              tGrand = cd.querySelector('#t-grand').textContent, tEntries = cd.querySelector('#t-entries').textContent;
        console.log('    night=' + tNight + ' | hotel=' + tHotel + ' | grand=' + tGrand);
        ok(Math.abs(num(tNight) - night) < 0.02, 'true night cost = (rate + fee) x 1.1338 = ' + night);
        ok(Math.abs(num(tHotel) - expectHotel) < 0.02, 'hotel total = night x nights + parking = ' + expectHotel);
        ok(Math.abs(num(tGrand) - expectGrand) < 0.02, 'trip total = entries x buy-ins + nights x true cost = ' + expectGrand);
        ok(Math.abs(num(tEntries) - entries) < 0.02, 'entries total = sum of picked entry costs = ' + entries);
        rSel.value = ''; fire(cdom, rSel, 'change');
        ok(cd.querySelector('#t-night').textContent.indexOf('cannot compute') !== -1, 'missing rate -> "cannot compute", no guessing');
        ok(cd.querySelector('#t-grand').textContent.indexOf('entries only') !== -1, 'grand falls back to entries-only with a note');

        // ---------- hotels.html walk filter ----------
        console.log('hotels.html (walk filter)');
        const hdom = load('hotels.html');
        const hd = hdom.window.document;
        const wf = hd.querySelector('#walk-filter');
        ok(!!wf, 'walk filter exists');
        if (wf) {
          const measured = Array.from(wf.querySelectorAll('input[name=walkf]')).find(r => r.value === 'measured');
          if (measured) {
            measured.checked = true; fire(hdom, measured, 'change');
            const visibleHotels = Array.from(hd.querySelectorAll('.hotel')).filter(c => !c.classList.contains('hidden'));
            ok(visibleHotels.length === 0, 'measured ≤30-min filter shows nothing while no walk time is officially measured');
            const wc = hd.querySelector('#walk-count');
            ok(wc && wc.textContent.indexOf('no property has an official measured walking time') !== -1, 'filter explains why nothing passes');
          }
        }

        console.log(failures === 0 ? 'SMOKE OK' : 'SMOKE FAILURES: ' + failures);
        process.exit(failures === 0 ? 0 : 1);
      }, 30);
    }, 30));
  }
}
