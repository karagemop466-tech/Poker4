/* Poker4 dashboard: table search, date filter, freezeout toggle, ≤30 walk filter,
   trip-cost calculator, per-date official booking links. No data leaves the browser. */
(function () {
  function rows(tbl) { return Array.prototype.slice.call(tbl.tBodies[0].rows); }

  function applyFilters() {
    document.querySelectorAll('table.tbl').forEach(function (tbl) {
      if (tbl.hasAttribute('data-walktable')) return; // handled with the walk toggle
      var scope = tbl.closest('main');
      var q = ((scope && scope.querySelector('[data-search]')) ? scope.querySelector('[data-search]').value : '') || '';
      q = q.trim().toLowerCase();
      var dateSel = scope && scope.querySelector('[data-datefilter]');
      var dateVal = dateSel ? dateSel.value : '';
      var fo = scope && scope.querySelector('[data-freezeout]');
      var foOn = fo ? fo.checked : false;
      var shown = 0;
      rows(tbl).forEach(function (r) {
        var ok = !q || r.innerText.toLowerCase().indexOf(q) !== -1;
        if (ok && dateVal) {
          var cells = r.cells;
          var hit = false;
          for (var i = 0; i < cells.length; i++) if (cells[i].innerText.indexOf(dateVal) !== -1) { hit = true; break; }
          ok = hit;
        }
        if (ok && foOn) {
          ok = r.innerText.toLowerCase().indexOf('freezeout') !== -1 ||
               r.innerText.toLowerCase().indexOf('single-entry') !== -1;
        }
        r.style.display = ok ? '' : 'none';
        if (ok) shown++;
      });
      var cnt = scope && scope.querySelector('[data-rowcount]');
      if (cnt) cnt.textContent = shown + ' rows visible in this table (of ' + rows(tbl).length + ')';
    });
  }

  function applyWalkFilter() {
    var cb = document.querySelector('[data-walkfilter]');
    var tbl = document.querySelector('table[data-walktable]');
    if (!tbl) return;
    rows(tbl).forEach(function (r) {
      var txt = r.innerText;
      var measured = txt.indexOf('min') !== -1 && txt.indexOf('not measured') === -1;
      var ok30 = txt.indexOf('≤30 OK') !== -1;
      r.style.display = (!cb || !cb.checked || (measured && ok30)) ? '' : 'none';
    });
  }

  document.addEventListener('input', function (e) {
    if (e.target.matches('[data-search]')) applyFilters();
    if (e.target.matches('#bk-in,#bk-out')) renderBookingLinks();
  });
  document.addEventListener('change', function (e) {
    if (e.target.matches('[data-datefilter],[data-freezeout]')) applyFilters();
    if (e.target.matches('[data-walkfilter]')) applyWalkFilter();
    if (e.target.matches('#c-hotel')) {
      var opt = e.target.selectedOptions[0];
      if (opt) {
        if (opt.dataset.rate) document.getElementById('c-rate').value = opt.dataset.rate;
        if (opt.dataset.fee) document.getElementById('c-fee').value = opt.dataset.fee;
      }
    }
    if (e.target.matches('#c-entries,#c-buyin,#c-nights,#c-rate,#c-fee,#c-tax,#c-park,#c-hotel')) calc();
  });

  /* ---------------- trip calculator ---------------- */
  function calc() {
    var g = function (id) { return parseFloat((document.getElementById(id) || {}).value || 0); };
    var entries = g('c-entries'), buyin = g('c-buyin'), nights = g('c-nights');
    var rate = g('c-rate'), fee = g('c-fee'), tax = g('c-tax') / 100, park = g('c-park');
    var out = document.getElementById('c-out');
    if (!out) return;
    var tourney = entries * buyin;
    var checkout = nights * (rate + fee) * (1 + tax);      // rate + resort fee, both taxed (Venetian terms)
    var nightly = nights ? checkout / nights : 0;
    var parking = nights * park;
    var total = tourney + checkout + parking;
    out.innerHTML =
      '<table>' +
      '<tr><td>Entries × buy-ins</td><td>' + entries + ' × $' + buyin.toFixed(2) + '</td><td><b>$' + tourney.toFixed(2) + '</b></td></tr>' +
      '<tr><td>True hotel cost / night</td><td>($' + rate.toFixed(2) + ' + $' + fee.toFixed(2) + ') × (1 + ' + (tax * 100).toFixed(2) + '%)</td><td><b>$' + nightly.toFixed(2) + '</b></td></tr>' +
      '<tr><td>Checkout total (' + nights + ' nights)</td><td>nights × (rate + fee) × (1 + tax)</td><td><b>$' + checkout.toFixed(2) + '</b></td></tr>' +
      '<tr><td>Nightly average</td><td>checkout ÷ nights</td><td>$' + nightly.toFixed(2) + '</td></tr>' +
      '<tr><td>Parking (optional)</td><td>' + nights + ' nights × $' + park.toFixed(2) + '</td><td>$' + parking.toFixed(2) + '</td></tr>' +
      '<tr><td colspan="2" class="total">Estimated trip cost</td><td class="total">$' + total.toFixed(2) + '</td></tr>' +
      '</table><p class="muted">Formula per project spec: entries × buy-ins + nights × true hotel cost' +
      (park ? ' (+ optional parking shown separately)' : '') + '. Not a forecast of actual spend.</p>';
  }

  /* ---------------- booking-link generator ---------------- */
  var BOOKINGS = [];
  function renderBookingLinks() {
    var box = document.getElementById('bk-links');
    if (!box) return;
    var i = document.getElementById('bk-in').value, o = document.getElementById('bk-out').value;
    if (!i || !o) { box.innerHTML = '<p class="muted">Pick both dates.</p>'; return; }
    box.innerHTML = BOOKINGS.map(function (b) {
      var u = b.url.replace('{in}', i).replace('{out}', o);
      return '<p>' + b.name + ': <a href="' + u + '" target="_blank" rel="noopener">official booking link for ' + i + ' → ' + o + '</a></p>';
    }).join('');
  }

  window.poker4InitBooking = function (list) { BOOKINGS = list; renderBookingLinks(); };

  applyFilters(); applyWalkFilter(); calc();
})();
