/* v2 dashboard behaviour: search across all tables, date filter, single-entry toggle,
   walk-30 filter, and the trip-cost calculator. No dependencies. */
(function () {
  "use strict";

  function tables() {
    return Array.prototype.slice.call(document.querySelectorAll("table[data-searchable]"));
  }

  function rowText(tr) {
    return (tr.getAttribute("data-search") || tr.textContent || "").toLowerCase();
  }

  function applyFilters() {
    var q = (document.getElementById("q") || {}).value || "";
    q = q.trim().toLowerCase();
    var from = (document.getElementById("dfrom") || {}).value || "";
    var to = (document.getElementById("dto") || {}).value || "";
    var seOnly = !!(document.getElementById("seOnly") || {}).checked;
    var walk30 = !!(document.getElementById("walk30") || {}).checked;
    var noSat = !!(document.getElementById("noSat") || {}).checked;

    tables().forEach(function (t) {
      var shown = 0;
      Array.prototype.slice.call(t.querySelectorAll("tbody tr")).forEach(function (tr) {
        var ok = true;
        if (q && rowText(tr).indexOf(q) === -1) ok = false;
        var d = tr.getAttribute("data-date");
        if (ok && d) {
          if (from && d < from) ok = false;
          if (to && d > to) ok = false;
        }
        if (ok && seOnly && tr.getAttribute("data-single-entry") !== "1") ok = false;
        if (ok && walk30 && tr.getAttribute("data-walk30") !== "1") ok = false;
        if (ok && noSat && tr.getAttribute("data-kind") === "satellite") ok = false;
        tr.style.display = ok ? "" : "none";
        if (ok) shown++;
      });
      var out = t.querySelector("[data-count]");
      if (out) out.textContent = shown + " rows shown";
      var empty = t.parentNode.querySelector("[data-empty]");
      if (empty) empty.style.display = shown ? "none" : "";
    });
    var n = document.getElementById("filterCount");
    if (n) n.textContent = q ? 'Filtering for "' + q + '"' : "";
  }

  function tripCost() {
    var entries = parseFloat((document.getElementById("c_entries") || {}).value || 0) || 0;
    var buyin = parseFloat((document.getElementById("c_buyin") || {}).value || 0) || 0;
    var nights = parseFloat((document.getElementById("c_nights") || {}).value || 0) || 0;
    var rate = parseFloat((document.getElementById("c_rate") || {}).value || 0) || 0;
    var fee = parseFloat((document.getElementById("c_fee") || {}).value || 0) || 0;
    var tax = parseFloat((document.getElementById("c_tax") || {}).value || 0) || 0;
    var parking = parseFloat((document.getElementById("c_parking") || {}).value || 0) || 0;

    var trueNight = (rate + fee) * (1 + tax / 100);
    var entryTotal = entries * buyin;
    var hotelTotal = nights * trueNight;
    var parkingTotal = parking * nights;
    var total = entryTotal + hotelTotal + parkingTotal;
    var box = document.getElementById("calcOut");
    if (!box) return;
    box.textContent =
      "ENTRIES      " + entries + " x $" + buyin.toFixed(2) + "  = $" + entryTotal.toFixed(2) + "\n" +
      "TRUE NIGHT   ($" + rate.toFixed(2) + " + $" + fee.toFixed(2) + ") x " + (1 + tax / 100).toFixed(4) + " = $" + trueNight.toFixed(2) + "\n" +
      "HOTEL        " + nights + " x $" + trueNight.toFixed(2) + " = $" + hotelTotal.toFixed(2) + "\n" +
      "PARKING      " + nights + " x $" + parking.toFixed(2) + " = $" + parkingTotal.toFixed(2) + "\n" +
      "------------------------------------------\n" +
      "TRIP TOTAL   $" + total.toFixed(2) + "\n" +
      "PER NIGHT    $" + (nights ? ((entryTotal / nights) + trueNight + parking).toFixed(2) : "0.00") + "  (entries spread over the stay)";
  }

  function wire() {
    ["q", "dfrom", "dto", "seOnly", "walk30", "noSat"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) { el.addEventListener("input", applyFilters); el.addEventListener("change", applyFilters); }
    });
    ["c_entries", "c_buyin", "c_nights", "c_rate", "c_fee", "c_tax", "c_parking"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) { el.addEventListener("input", tripCost); }
    });
    var reset = document.getElementById("resetFilters");
    if (reset) reset.addEventListener("click", function () {
      ["q", "dfrom", "dto"].forEach(function (id) { var e = document.getElementById(id); if (e) e.value = ""; });
      ["seOnly", "walk30", "noSat"].forEach(function (id) { var e = document.getElementById(id); if (e) e.checked = false; });
      applyFilters();
    });
    applyFilters();
    tripCost();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", wire);
  else wire();
})();
