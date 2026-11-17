
window.Poker4=(function(){
 const money=v=>v==null||v===0?'—':'$'+Number(v).toLocaleString('en-US');
 function fmt(el,on){[...el.querySelectorAll('tbody tr')].forEach(tr=>{tr.hidden=!on(tr);});}
 function count(bar,n,total){const c=bar.querySelector('[data-count]');if(c)c.textContent=n+' of '+total+' rows shown';}
 function initFilters(){
  const bar=document.getElementById('filters');if(!bar)return;
  const rows=[...document.querySelectorAll('table.data tbody tr')];
  const q=bar.querySelector('[data-filter=q]'),from=bar.querySelector('[data-filter=from]'),
        to=bar.querySelector('[data-filter=to]'),venue=bar.querySelector('[data-filter=venue]'),
        frozen=bar.querySelector('[data-filter=frozen]'),changed=bar.querySelector('[data-filter=changed]');
  const run=()=>{let n=0;rows.forEach(tr=>{
    const d=tr.dataset.date||'';const ok=!from.value||!d||d>=from.value;const ik=!to.value||!d||d<=to.value;
    const okv=!venue.value||tr.dataset.venue===venue.value;
    const okf=!frozen.checked||tr.dataset.frozen==='yes';
    const okc=!changed.checked||/SOURCE CHANGED/.test(tr.textContent);
    const needle=(q.value||'').toLowerCase().trim();
    const okq=!needle||tr.textContent.toLowerCase().includes(needle);
    const show=ok&&ik&&okv&&okf&&okc&&okq;tr.hidden=!show;if(show)n++;});
    count(bar,n,rows.length);};
  bar.addEventListener('input',run);bar.addEventListener('change',run);run();
 }
 function initTableSearch(){ /* header box filters every table on the page */
  const form=document.querySelector('.navsearch');if(!form)return;
  form.addEventListener('input',e=>{
    const v=(e.target.value||'').toLowerCase().trim();
    document.querySelectorAll('main table tbody tr').forEach(tr=>{tr.hidden=!!v&&!tr.textContent.toLowerCase().includes(v);});
  });
 }
 function navSearch(form){
  const v=(form.q.value||'').trim();
  location.href='@/search.html'+(v?'#'+encodeURIComponent(v):'');return false;
 }
 function initCalc(){
  const box=document.getElementById('calc');if(!box)return;
  const picks=[...box.querySelectorAll('input[data-buyin]')];
  const g=id=>Number(document.getElementById(id).value||0);
  const render=()=>{
   const chosen=picks.filter(p=>p.checked);
   const perEntry=g('c-entries')||1;
   const buy=chosen.reduce((a,p)=>a+Number(p.dataset.buyin),0);
   const gtd=chosen.reduce((a,p)=>a+Number(p.dataset.gtd||0),0);
   const pool=chosen.reduce((a,p)=>{const c=window.__P4CAND__.find(x=>String(x.id)===p.dataset.id);return a+((c&&c.to_pool)||Number(p.dataset.buyin));},0);
   const nights=g('c-nights'),rate=g('c-rate'),fee=g('c-fee'),tax=g('c-tax')/100,park=g('c-park');
   const entriesCost=buy*perEntry, lodging=nights*(rate+fee)*(1+tax)+nights*park;
   document.getElementById('c-total').textContent=money(Math.round(entriesCost+lodging));
   document.getElementById('c-lines').innerHTML=
     `<li>Events ticked: <b>${chosen.length}</b> × ${perEntry} entr${perEntry>1?'ies':'y'} = <b>${money(entriesCost)}</b></li>`+
     `<li>Guaranteed pools you are aiming at: ${money(gtd)} (descriptive, not expected value)</li>`+
     `<li>Money reaching those pools from your entries: ${money(pool*perEntry)} of ${money(entriesCost)}</li>`+
     `<li>Lodging: ${nights} night${nights>1?'s':''} × (${money(rate)} + ${money(fee)} fee) × ${(1+tax).toFixed(4)} + ${money(nights*park)} parking = <b>${money(Math.round(lodging))}</b></li>`+
     `<li>Cost per night all-in: ${money(Math.round(lodging/(nights||1)))}</li>`;
   const w=[];
   if(!chosen.length)w.push('No events selected — the total covers lodging only.');
   if(chosen.some(p=>!p.dataset.gtd||Number(p.dataset.gtd)===0))w.push('One or more selected events publish no guarantee, so no value ratio is available for them.');
   if(perEntry>1)w.push(`You assumed ${perEntry} entries per event. No structure sheet audited confirms whether re-entry is allowed — treat this as your own budget choice, not a verified rule.`);
   if(!window.__P4CONFIRMED__)w.push('Entry rules unverified for every listed event: no sheet read states "one entry per player".');
   w.push('The room rate is an input. It is not a dated quote; only the $55 fee is quoted from the property page.');
   document.getElementById('c-warn').innerHTML=w.map(x=>'! '+x).join('<br>');
  };
  picks.forEach((p,i)=>p.dataset.id=(window.__P4IDS__||[])[i]||'');
  box.addEventListener('input',render);render();
 }
 function initGlobalSearch(){
  const inp=document.getElementById('gs');if(!inp)return;
  const out=document.getElementById('gr');const all=window.__P4INDEX__||[];
  const go=()=>{const v=inp.value.toLowerCase().trim();
   if(!v){out.innerHTML='<p class="muted">Type to search all '+all.length+' indexed rows.</p>';return;}
   const hits=all.filter(r=>(r.t+' '+r.d+' '+r.k).toLowerCase().includes(v)).slice(0,80);
   out.innerHTML=hits.length?hits.map(h=>`<a href="${h.u}${h.a?'#'+h.a:''}"><span class="k">${h.k}</span><b>${h.t.replace(/</g,'&lt;')}</b><small>${(h.d||'').replace(/</g,'&lt;')}</small></a>`).join(''):'<p class="muted">No rows match that.</p>';};
  inp.addEventListener('input',go);
  if(location.hash){inp.value=decodeURIComponent(location.hash.slice(1));}
  go();
 }
 document.addEventListener('DOMContentLoaded',()=>{initFilters();initTableSearch();initCalc();initGlobalSearch();});
 return {navSearch};
})();
