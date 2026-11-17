
function applyFilter(tableId){
  const tbl=document.getElementById(tableId); if(!tbl) return;
  const page=tbl.closest('.filterable');
  const q=(page.querySelector('[data-search]')?.value||'').toLowerCase();
  const dt=page.querySelector('[data-date]')?.value||'';
  const entry=page.querySelector('[data-entry]')?.value||'';
  const kind=page.querySelector('[data-kind]')?.value||'';
  const walkMax=page.querySelector('[data-walkmax]');
  tbl.querySelectorAll('tbody tr').forEach(tr=>{
    let ok=(!q)||tr.innerText.toLowerCase().includes(q);
    if(ok&&dt){const d=tr.getAttribute('data-date')||''; ok=(d===dt)||(d===''&&tr.getAttribute('data-weekly')==='1');}
    if(ok&&entry){ok=(tr.getAttribute('data-entry')||'')===entry;}
    if(ok&&kind){ok=(tr.getAttribute('data-kind')||'')===kind;}
    if(ok&&walkMax&&walkMax.checked){const w=tr.getAttribute('data-walk');ok=(w!==null&&w!==''&&Number(w)<=30);}
    tr.style.display=ok?'':'none';
  });
}
document.addEventListener('input',e=>{const p=e.target.closest('.filterable');if(p)applyFilter(p.querySelector('table').id);});
document.addEventListener('change',e=>{const p=e.target.closest('.filterable');if(p)applyFilter(p.querySelector('table').id);});
function trueCost(rate,fee){return ((Number(rate)||0)+(Number(fee)||0))*1.1338;}
function bindCalc(){
  const c=document.getElementById('tripcalc'); if(!c) return;
  const upd=()=>{
    const n=Number(c.querySelector('#entries').value)||0;
    const b=Number(c.querySelector('#buyin').value)||0;
    const extra=Number(c.querySelector('#extraentries').value)||0;
    const nights=Number(c.querySelector('#nights').value)||0;
    const rate=Number(c.querySelector('#rate').value)||0;
    const fee=Number(c.querySelector('#fee').value)||0;
    const entriesTotal=n*b+extra;
    const perNight=trueCost(rate,fee);
    const stay=nights*perNight;
    c.querySelector('#r-entries').textContent='$'+entriesTotal.toLocaleString(undefined,{maximumFractionDigits:0});
    c.querySelector('#r-night').textContent='$'+perNight.toLocaleString(undefined,{maximumFractionDigits:2});
    c.querySelector('#r-stay').textContent='$'+stay.toLocaleString(undefined,{maximumFractionDigits:0});
    c.querySelector('#r-total').textContent='$'+(entriesTotal+stay).toLocaleString(undefined,{maximumFractionDigits:0});
  };
  c.addEventListener('input',upd); upd();
}
function bindHotelCalcs(){
  document.querySelectorAll('.hotelcalc').forEach(h=>{
    const upd=()=>{
      const rate=Number(h.querySelector('.h-rate').value)||0;
      const fee=Number(h.dataset.fee||0)||0;
      h.querySelector('.h-out').textContent='True cost/night: $'+trueCost(rate,fee).toLocaleString(undefined,{maximumFractionDigits:2})+'  = ($'+rate+' + $'+fee+') × 1.1338';
    };
    h.addEventListener('input',upd); upd();
  });
}
function monitorRefresh(){
  const el=document.getElementById('monitor-live'); if(!el) return;
  fetch('data/0f6c627b/monitor/status.json',{cache:'no-store'}).then(r=>r.json()).then(j=>{
    if(j && j.last_run){el.textContent='Live monitor file last run: '+j.last_run+' ('+(j.entries||[]).length+' URLs tracked). Any row marked "changed" below needs review.';}
  }).catch(()=>{el.textContent='Live monitor file not reachable (offline view) — showing the built snapshot.';});
}
document.addEventListener('DOMContentLoaded',()=>{bindCalc();bindHotelCalcs();monitorRefresh();});
