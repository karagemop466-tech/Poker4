/* Shared dashboard behaviour: search, filters, trip calculator. */
(function () {
  function q(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  // ---- generic text search over tables marked data-searchable
  q('input.search-box').forEach(function (box) {
    var targetId = box.getAttribute('data-target');
    var table = document.getElementById(targetId);
    if (!table) return;
    box.addEventListener('input', function () {
      var needle = box.value.toLowerCase().trim();
      q('tbody tr', table).forEach(function (tr) {
        tr.style.display = !needle || tr.textContent.toLowerCase().indexOf(needle) !== -1 ? '' : 'none';
      });
    });
  });

  // ---- date filter (tournaments page)
  var dateSel = document.getElementById('date-filter');
  if (dateSel) {
    var table = document.getElementById('events-table');
    var apply = function () {
      var d = dateSel.value;
      q('tbody tr', table).forEach(function (tr) {
        var ok = !d || tr.getAttribute('data-date') === d;
        if (ok && tr.style.display === 'none-date') tr.style.display = '';
        if (!ok) tr.style.display = 'none-date';
        if (!ok) tr.style.display = 'none';
        if (ok && tr.getAttribute('data-hidden') !== '1') tr.style.display = '';
      });
    };
    dateSel.addEventListener('change', apply);
    window.__dateApply = apply;
  }

  // ---- entry-rule toggles (tournaments page)
  var toggles = q('input.entry-toggle');
  if (toggles.length) {
    var table = document.getElementById('events-table');
    var applyToggles = function () {
      var show = {};
      toggles.forEach(function (t) { show[t.getAttribute('data-kind')] = t.checked; });
      q('tbody tr', table).forEach(function (tr) {
        var kind = tr.getAttribute('data-entry') || 'unverified';
        var vis = !!show[kind];
        tr.setAttribute('data-hidden', vis ? '0' : '1');
        tr.style.display = vis ? '' : 'none';
      });
      if (window.__dateApply) window.__dateApply();
    };
    toggles.forEach(function (t) { t.addEventListener('change', applyToggles); });
    applyToggles();
  }

  // ---- walk filter (hotels page)
  var walkChk = document.getElementById('walk30');
  if (walkChk) {
    var wt = document.getElementById('walks-table');
    walkChk.addEventListener('change', function () {
      q('tbody tr', wt).forEach(function (tr) {
        var ok = !walkChk.checked || tr.getAttribute('data-within30') === '1';
        tr.style.display = ok ? '' : 'none';
      });
    });
  }

  // ---- trip cost calculator: entries x buy-ins + nights x true hotel cost
  var calc = document.getElementById('trip-calc');
  if (calc) {
    var out = {
      entries: document.getElementById('out-entries'),
      hotel: document.getElementById('out-hotel'),
      trip: document.getElementById('out-trip'),
      detail: document.getElementById('out-detail'),
      ratio: document.getElementById('out-ratio')
    };
    var run = function () {
      var nEntries = parseFloat(document.getElementById('calc-entries').value) || 0;
      var buyIn = parseFloat(document.getElementById('calc-buyin').value) || 0;
      var nights = parseFloat(document.getElementById('calc-nights').value) || 0;
      var rate = parseFloat(document.getElementById('calc-rate').value) || 0;
      var fee = parseFloat(document.getElementById('calc-fee').value) || 0;
      var tax = parseFloat(document.getElementById('calc-tax').value) || 0.1338;
      var park = parseFloat(document.getElementById('calc-parking').value) || 0;
      var gtd = parseFloat(document.getElementById('calc-gtd').value) || 0;
      var entriesTotal = nEntries * buyIn;
      var trueNight = (rate + fee) * (1 + tax);
      var hotelTotal = trueNight * nights + park * nights;
      var trip = entriesTotal + hotelTotal;
      out.entries.textContent = '$' + entriesTotal.toLocaleString(undefined, { maximumFractionDigits: 2 });
      out.hotel.textContent = '$' + hotelTotal.toLocaleString(undefined, { maximumFractionDigits: 2 });
      out.trip.textContent = '$' + trip.toLocaleString(undefined, { maximumFractionDigits: 2 });
      out.detail.textContent =
        'true cost/night = ($' + rate.toFixed(2) + ' rate + $' + fee.toFixed(2) + ' resort fee) x 1.1338 = $' +
        trueNight.toFixed(2) + ' ; parking $' + park.toFixed(2) + '/night ; entries ' + nEntries + ' x $' + buyIn.toFixed(2);
      out.ratio.textContent = gtd > 0 && buyIn > 0
        ? (gtd / buyIn).toFixed(1) + 'x  (guaranteed pool ÷ entry fee — descriptive arithmetic only, not a forecast)'
        : '—';
    };
    q('input,select', calc).forEach(function (el) { el.addEventListener('input', run); });
    var hotelSel = document.getElementById('calc-hotel');
    if (hotelSel && window.HOTEL_FEES) {
      hotelSel.addEventListener('change', function () {
        var h = window.HOTEL_FEES[hotelSel.value];
        if (h) {
          document.getElementById('calc-fee').value = h.fee != null ? h.fee : 0;
          if (h.rate != null) document.getElementById('calc-rate').value = h.rate;
        }
        run();
      });
    }
    run();
  }
})();
