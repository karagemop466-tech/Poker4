// Client-side filter for the single-entry table (no network calls).
(function () {
  var table = document.getElementById('main-table');
  if (!table) return;
  var q = document.getElementById('q'), venue = document.getElementById('venue'),
      maxbuy = document.getElementById('maxbuy'), count = document.getElementById('count');
  var rows = Array.prototype.slice.call(table.querySelectorAll('tbody tr'));
  function num(s) { var n = parseFloat((s || '').replace(/[^0-9.]/g, '')); return isNaN(n) ? null : n; }
  function apply() {
    var term = (q.value || '').toLowerCase(), v = venue.value, mb = parseFloat(maxbuy.value);
    var shown = 0;
    rows.forEach(function (tr) {
      var cells = tr.children, text = tr.textContent.toLowerCase();
      var ok = (!term || text.indexOf(term) !== -1) &&
               (!v || cells[2].textContent === v) &&
               (isNaN(mb) || (num(cells[4].textContent) !== null && num(cells[4].textContent) <= mb));
      tr.style.display = ok ? '' : 'none';
      if (ok) shown++;
    });
    count.textContent = shown + ' of ' + rows.length + ' rows shown';
  }
  [q, venue, maxbuy].forEach(function (el) { el.addEventListener('input', apply); el.addEventListener('change', apply); });
  apply();
})();
