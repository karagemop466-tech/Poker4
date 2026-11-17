(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[character]);
  const sourceMap = new Map();
  let data;
  let activeFilter = 'all';

  const currency = (amount, decimals = 0) => {
    if (amount === null || amount === undefined || amount === '') return '—';
    return new Intl.NumberFormat('en-US', {
      style: 'currency', currency: 'USD', minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(amount);
  };

  const percent = (value) => `${Number(Number(value).toFixed(2))}%`;

  const dateLabel = (isoDate) => {
    const date = new Date(`${isoDate}T12:00:00Z`);
    return new Intl.DateTimeFormat('en-US', {
      timeZone: 'UTC', weekday: 'short', month: 'short', day: 'numeric'
    }).format(date);
  };

  function getSource(id) {
    return sourceMap.get(id);
  }

  function sourceLink(id, compact = false) {
    const source = getSource(id);
    if (!source) return '';
    const label = compact ? 'Official source' : source.label;
    return `<a class="source-link" href="${escapeHTML(source.url)}" target="_blank" rel="noopener noreferrer" aria-label="${escapeHTML(source.label)} (opens in a new tab)">${escapeHTML(label)} <span aria-hidden="true">↗</span></a>`;
  }

  function sourceLinks(ids = [], compact = false) {
    return `<div class="source-links">${ids.map((id) => sourceLink(id, compact)).join('')}</div>`;
  }

  function statusBadge(item) {
    const type = item.status === 'excluded' ? 'excluded' : 'unknown';
    return `<span class="status-badge ${type}">${escapeHTML(item.statusLabel || (type === 'excluded' ? 'Not single-entry' : 'Terms unknown'))}</span>`;
  }

  function renderHeader() {
    const date = data.meta.snapshotLabel;
    const formatted = date.toUpperCase();
    $('#hero-date').textContent = formatted;
    $('#sidebar-date').textContent = date;
    $('#footer-date').textContent = date;
    $('#snapshot-chip-text').textContent = `RESEARCH SNAPSHOT · ${formatted}`;
    $('#event-window').textContent = data.meta.eventWindow;
    $('#metric-qualified').textContent = String(data.summary.confirmedSingleEntry);
    $('#metric-events').textContent = String(data.summary.reviewedCandidateCount);
    $('#metric-event-note').textContent = `${data.summary.reviewedCandidateCount} event IDs · ${data.events.length} dated start rows`;
    $('#metric-eight').textContent = String(data.summary.eightAmVerified);
    $('#nav-event-count').textContent = String(data.events.length);
    $('#filter-all-count').textContent = String(data.events.length);
    $('#filter-unknown-count').textContent = String(data.events.filter((event) => event.status === 'unknown').length);
    $('#filter-excluded-count').textContent = String(data.events.filter((event) => event.status === 'excluded').length);
    $('#flag-count').textContent = String(data.flags.length).padStart(2, '0');
    $('#report-link').href = data.meta.reportUrl;
    $('#report-link').target = '_blank';
    $('#report-link').rel = 'noopener noreferrer';
    $('#full-report-link').href = data.meta.reportUrl;
  }

  function renderEvents() {
    const body = $('#event-table-body');
    const query = $('#event-search').value.trim().toLowerCase();
    const events = data.events.filter((event) => {
      const filterMatch = activeFilter === 'all' || event.status === activeFilter;
      const textMatch = !query || [
        event.name, event.series, event.venue, event.format, event.rule,
        event.details, event.date, event.time, event.statusLabel
      ].join(' ').toLowerCase().includes(query);
      return filterMatch && textMatch;
    });

    if (!events.length) {
      body.innerHTML = '<tr><td colspan="7" class="empty-cell">No events match this filter. Try another status or search term.</td></tr>';
      return;
    }

    body.innerHTML = events.map((event) => `
      <tr>
        <td><span class="event-date">${escapeHTML(dateLabel(event.date))}</span><span class="event-time">${escapeHTML(event.time)} · PT</span></td>
        <td><span class="event-name">${escapeHTML(event.name)}</span><span class="event-venue">${escapeHTML(event.venue)} · ${escapeHTML(event.series)}</span><span class="event-detail">${escapeHTML(event.details)}</span></td>
        <td class="money-cell">${currency(event.buyIn)}</td>
        <td class="guarantee-cell">${event.guarantee ? currency(event.guarantee) : '—'}</td>
        <td>${statusBadge(event)}<div class="event-detail">${escapeHTML(event.rule)}</div></td>
        <td class="share-cell">${event.poolShare === null ? '—' : `${Number(event.poolShare)}%`}<small>of base buy-in</small></td>
        <td>${sourceLinks(event.sources)}</td>
      </tr>`).join('');
  }

  function renderCriteria() {
    $('#criteria-list').innerHTML = data.criteria.map((criterion, index) => `
      <article class="criterion">
        <span class="criterion-number">${String(index + 1).padStart(2, '0')}</span>
        <div><h3>${escapeHTML(criterion)}</h3><p>Must be explicit in the official terms for this specific event.</p></div>
      </article>`).join('');
  }

  function renderRecurring() {
    $('#recurring-grid').innerHTML = data.recurring.map((item) => `
      <article class="recurring-card status-${escapeHTML(item.status)}">
        <div class="recurring-card-head"><h3>${escapeHTML(item.venue)}</h3>${statusBadge(item)}</div>
        <div class="schedule-time">${escapeHTML(item.schedule)}</div>
        <div class="buyin-line">${escapeHTML(item.buyIn)}</div>
        <p><b>${escapeHTML(item.headline)}.</b> ${escapeHTML(item.detail)}</p>
        ${sourceLinks(item.sources)}
      </article>`).join('');
  }

  function renderValue() {
    const sorted = [...data.value].sort((a, b) => b.share - a.share);
    $('#value-grid').innerHTML = sorted.map((item) => `
      <article class="value-card">
        <div><h3>${escapeHTML(item.name)}</h3><p>${escapeHTML(item.math)} · ${escapeHTML(item.note)}</p></div>
        <div class="value-bar" role="img" aria-label="${escapeHTML(item.share)} percent of the base buy-in goes to the prize pool"><span style="width:${Math.min(100, Number(item.share))}%"></span></div>
        <div class="value-share">${percent(item.share)}</div>
        ${sourceLinks(item.sources)}
      </article>`).join('');
    $('#value-caveat-text').textContent = data.valueCaveat;
  }

  function renderSpendAdvantages() {
    $('#spend-grid').innerHTML = data.spendAdvantages.map((item) => `
      <article class="spend-card">
        <div class="spend-card-top"><h3>${escapeHTML(item.name)}</h3><span class="spend-icon" aria-hidden="true">↗</span></div>
        <div class="spend-mechanic">${escapeHTML(item.advantage)}</div>
        <p>${escapeHTML(item.extra)}</p>
        ${sourceLinks(item.sources)}
      </article>`).join('');
  }

  function renderFestival() {
    $('#festival-grid').innerHTML = data.festivalEvents.map((event) => `
      <article class="festival-card">
        <span class="festival-date">${escapeHTML(event.date)} · WYNN LAS VEGAS</span>
        <h4>${escapeHTML(event.name)}</h4>
        <div class="festival-meta"><span>${escapeHTML(event.buyIn)}</span>${event.guarantee === 'Not repeated here' ? '' : `<span>${escapeHTML(event.guarantee)} GTD</span>`}</div>
        <p>${escapeHTML(event.rule)}</p>
        ${sourceLinks(event.sources)}
      </article>`).join('');
  }

  function renderHotels() {
    $('#hotel-grid').innerHTML = data.hotels.map((hotel, index) => `
      <article class="hotel-card ${index === 0 ? 'featured' : ''}">
        <div><h3>${escapeHTML(hotel.name)}</h3><div class="hotel-venue">${escapeHTML(hotel.venue)}</div></div>
        <div class="hotel-fee">${escapeHTML(hotel.feeLabel)}<small>${hotel.feeVerified ? 'OFFICIAL NIGHTLY FEE' : 'PORTFOLIO RANGE · NOT PROPERTY-SPECIFIC'}</small></div>
        <div class="hotel-attributes">
          <span><b>Rate:</b> ${escapeHTML(hotel.rate)}</span>
          <span><b>Property note:</b> ${escapeHTML(hotel.perk)}</span>
          <span class="hotel-warning"><b>Limit:</b> ${escapeHTML(hotel.caveat)}</span>
        </div>
        ${sourceLinks(hotel.sources)}
      </article>`).join('');
  }

  function renderRecommendations() {
    $('#recommendation-grid').innerHTML = data.recommendations.map((item) => {
      const target = item.section ? `href="#${escapeHTML(item.section)}"` : `href="${escapeHTML(getSource(item.source)?.url || '#sources')}" target="_blank" rel="noopener noreferrer"`;
      return `<article class="recommendation-card"><span class="rec-number">${escapeHTML(item.number)}</span><div><h3>${escapeHTML(item.title)}</h3><p>${escapeHTML(item.body)}</p><a class="text-link" ${target}>${escapeHTML(item.action)} <span>${item.section ? '→' : '↗'}</span></a></div></article>`;
    }).join('');
  }

  function renderFlags() {
    $('#flags-list').innerHTML = data.flags.map((flag) => `
      <article class="flag-card level-${escapeHTML(flag.level)}">
        <span class="flag-mark" aria-hidden="true">!</span>
        <div><h3>${escapeHTML(flag.title)}</h3><p>${escapeHTML(flag.body)}</p>${sourceLinks(flag.sources, true)}</div>
      </article>`).join('');
  }

  function renderSources() {
    const grouped = new Map();
    data.sources.forEach((source) => {
      if (!grouped.has(source.group)) grouped.set(source.group, []);
      grouped.get(source.group).push(source);
    });
    $('#source-groups').innerHTML = Array.from(grouped.entries()).map(([group, sources]) => `
      <section class="source-group" aria-label="${escapeHTML(group)}">
        <h3>${escapeHTML(group)}</h3>
        <ul>${sources.map((source) => `<li><a href="${escapeHTML(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(source.label)}</a></li>`).join('')}</ul>
      </section>`).join('');
  }

  function downloadCSV() {
    const rows = [
      ['Date', 'Start (Las Vegas PT)', 'Venue', 'Series', 'Event', 'Buy-in USD', 'Guarantee USD', 'Format', 'Entry status', 'Entry-rule note', 'Prize-pool share', 'Official evidence URLs']
    ];
    data.events.forEach((event) => {
      rows.push([
        event.date, event.time, event.venue, event.series, event.name, event.buyIn,
        event.guarantee ?? '', event.format, event.statusLabel, event.rule,
        event.poolShare === null ? '' : `${event.poolShare}%`,
        event.sources.map((id) => getSource(id)?.url || '').filter(Boolean).join(' | ')
      ]);
    });
    const csv = '\uFEFF' + rows.map((row) => row.map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(',')).join('\r\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `vegas-poker-events-${data.meta.snapshot}.csv`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function setupFilters() {
    $$('.filter-tab').forEach((button) => {
      button.addEventListener('click', () => {
        activeFilter = button.dataset.filter;
        $$('.filter-tab').forEach((tab) => {
          const selected = tab === button;
          tab.classList.toggle('is-selected', selected);
          tab.setAttribute('aria-pressed', String(selected));
        });
        renderEvents();
      });
    });
    $('#event-search').addEventListener('input', renderEvents);
    $('#download-csv').addEventListener('click', downloadCSV);
    $('#print-button').addEventListener('click', () => window.print());
  }

  function setupMobileNav() {
    const toggle = $('#menu-toggle');
    const sidebar = $('#sidebar');
    const scrim = $('#mobile-scrim');
    const close = () => {
      sidebar.classList.remove('is-open');
      scrim.hidden = true;
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', 'Open navigation');
    };
    toggle.addEventListener('click', () => {
      const open = !sidebar.classList.contains('is-open');
      sidebar.classList.toggle('is-open', open);
      scrim.hidden = !open;
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    });
    scrim.addEventListener('click', close);
    $$('.nav-link', sidebar).forEach((link) => link.addEventListener('click', close));
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') close();
    });
  }

  function setupActiveNavigation() {
    const links = $$('.nav-link');
    const sections = links.map((link) => $(link.getAttribute('href'))).filter(Boolean);
    if (!('IntersectionObserver' in window)) return;
    const observer = new IntersectionObserver((entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (!visible) return;
      links.forEach((link) => link.classList.toggle('is-active', link.getAttribute('href') === `#${visible.target.id}`));
    }, { rootMargin: '-15% 0px -70% 0px', threshold: [0, .1, .25] });
    sections.forEach((section) => observer.observe(section));
  }

  async function init() {
    try {
      const response = await fetch('data.json', { cache: 'no-store' });
      if (!response.ok) throw new Error(`Could not load the research dataset (${response.status}).`);
      data = await response.json();
      data.sources.forEach((source) => sourceMap.set(source.id, source));
      renderHeader();
      renderEvents();
      renderCriteria();
      renderRecurring();
      renderValue();
      renderSpendAdvantages();
      renderFestival();
      renderHotels();
      renderRecommendations();
      renderFlags();
      renderSources();
      setupFilters();
      setupMobileNav();
      setupActiveNavigation();
    } catch (error) {
      console.error(error);
      const message = escapeHTML(error.message || 'The research dataset could not be loaded.');
      $('#event-table-body').innerHTML = `<tr><td colspan="7" class="empty-cell">${message} Run the site through a local web server; do not open index.html directly.</td></tr>`;
      const banner = document.createElement('div');
      banner.className = 'load-error';
      banner.textContent = 'The verified research data could not be loaded. Please reload from the hosted dashboard.';
      $('.page-content').prepend(banner);
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
