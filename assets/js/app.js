// Poker4 — simple table search filter + mobile nav
document.addEventListener('DOMContentLoaded', function () {
  // Table search
  var inputs = document.querySelectorAll('[data-table-filter]');
  inputs.forEach(function (input) {
    var table = document.getElementById(input.getAttribute('data-table-filter'));
    if (!table) return;
    var rows = table.querySelectorAll('tbody tr');
    input.addEventListener('input', function () {
      var q = input.value.toLowerCase().trim();
      var visible = 0;
      rows.forEach(function (row) {
        var text = row.textContent.toLowerCase();
        var show = text.indexOf(q) !== -1;
        row.style.display = show ? '' : 'none';
        if (show) visible++;
      });
      var msg = document.getElementById(input.getAttribute('data-table-filter') + '-count');
      if (msg) msg.textContent = visible + ' matching row' + (visible !== 1 ? 's' : '');
    });
  });

  // Mobile nav toggle (if used)
  var btn = document.getElementById('nav-toggle');
  var menu = document.getElementById('nav-menu');
  if (btn && menu) {
    btn.addEventListener('click', function () {
      menu.classList.toggle('open');
    });
  }
});
