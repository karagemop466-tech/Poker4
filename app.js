const OFFICIAL = {
  schedule: 'https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament/dse-nov-2026.html',
  main: 'https://www.venetianlasvegas.com/resort/casino/poker/deepstack-extravaganza-poker-tournament.html',
  pokerRates: 'https://www.venetianlasvegas.com/resort/casino/poker/suite-rates.html',
  resortFee: 'https://www.venetianlasvegas.com/resort/resort-fee.html',
  hotelTerms: 'https://www.venetianlasvegas.com/legal/hotel-terms-and-conditions.html',
  booking: 'https://www.venetianlasvegas.com/book',
  bellagioPoker: 'https://bellagio.mgmresorts.com/en/casino/poker.html'
};
const pdf = (n) => `https://www.venetianlasvegas.com/content/dam/vlvweb/casino/poker/deepstack/2026/structures/dse_nov_2026-structure_${n}.pdf`;
const events = [
  {date:'2026-11-17',time:'11:10 AM',id:'1C',name:'$300 NLH — Event 1C',buy:300,guarantee:75000,format:'Multi-flight / multiday',pdf:10,group:'review',note:'Event 1A–1D share event number 1; later flight entry/re-entry policy is not established in the public structure.'},
  {date:'2026-11-17',time:'5:10 PM',id:'1D',name:'$300 NLH — Event 1D',buy:300,guarantee:75000,format:'Multi-flight / multiday',pdf:9,group:'review',note:'Event 1A–1D share event number 1; later flight entry/re-entry policy is not established in the public structure.'},
  {date:'2026-11-18',time:'11:10 AM',id:'2',name:'$300 NLH (1 day)',buy:300,guarantee:10000,format:'One day',pdf:5,group:'candidate',note:'Event 1 Day 2 restart is scheduled at noon the same day, so the events can overlap. Re-entry policy is unverified.'},
  {date:'2026-11-19',time:'10:10 AM',id:'3',name:'$200 NLH RaceDay Stack (1 day)',buy:200,guarantee:null,format:'One day',pdf:18,group:'candidate',note:'Guarantee not listed in the schedule/structure consulted; single-entry is unverified.'},
  {date:'2026-11-20',time:'10:10 AM',id:'4',name:'$200 NLH RaceDay Stack (1 day)',buy:200,guarantee:null,format:'One day',pdf:18,group:'candidate',note:'Guarantee not listed in the schedule/structure consulted; single-entry is unverified.'},
  {date:'2026-11-21',time:'10:10 AM',id:'5',name:'$200 NLH RaceDay Stack (1 day)',buy:200,guarantee:null,format:'One day',pdf:18,group:'candidate',note:'Guarantee not listed in the schedule/structure consulted; single-entry is unverified.'},
  {date:'2026-11-22',time:'11:10 AM',id:'6',name:'$200 NLH (1 day)',buy:200,guarantee:null,format:'One day',pdf:29,group:'candidate',note:'Guarantee not listed in the schedule/structure consulted; single-entry is unverified.'},
  {date:'2026-11-23',time:'11:10 AM',id:'7A',name:'$400 NLH — Event 7, Flight 1A',buy:400,guarantee:75000,format:'Multi-flight / multiday',pdf:2,group:'review',note:'Flights 1A–1C combine on Day 2. Structure forbids a player who bags Day 2 from entering a later flight; re-entry before bagging is not stated.'},
  {date:'2026-11-24',time:'11:10 AM',id:'7B',name:'$400 NLH — Event 7, Flight 1B',buy:400,guarantee:75000,format:'Multi-flight / multiday',pdf:2,group:'review',note:'Flights 1A–1C combine on Day 2. Structure forbids a player who bags Day 2 from entering a later flight; re-entry before bagging is not stated.'},
  {date:'2026-11-25',time:'11:10 AM',id:'10',name:'$400 NLH (1 day)',buy:400,guarantee:15000,format:'One day',pdf:6,group:'candidate',note:'Event 7 Day 2 restart is scheduled at 11:00 AM, so the events overlap. Re-entry policy is unverified.'},
  {date:'2026-11-26',time:'11:10 AM',id:'12',name:'$300 NLH (1 day)',buy:300,guarantee:10000,format:'One day',pdf:5,group:'candidate',note:'No re-entry wording found in the linked structure; single-entry is unverified.'},
  {date:'2026-11-27',time:'11:10 AM',id:'14',name:'$600 NLH (1 day)',buy:600,guarantee:30000,format:'One day',pdf:7,group:'candidate',note:'No re-entry wording found in the linked structure; single-entry is unverified.'},
  {date:'2026-11-23',time:'5:10 PM',id:'8',name:'$200 NLH Progressive Knock-Out Bounty (1 day)',buy:200,guarantee:8000,format:'PKO bounty',pdf:30,group:'secondary',note:'Bounty payout model; $8,000 guarantee includes bounty amounts. Re-entry status unverified.'},
  {date:'2026-11-24',time:'5:10 PM',id:'9',name:'$200 NLH Bounty (1 day)',buy:200,guarantee:8000,format:'Bounty',pdf:1,group:'secondary',note:'$8,000 guarantee includes bounty amounts; separate from plain NLH shortlist. Re-entry status unverified.'},
  {date:'2026-11-28',time:'11:10 AM',id:'16',name:'$600 NLH Bounty (1 day)',buy:600,guarantee:30000,format:'Bounty',pdf:11,group:'secondary',note:'Bounty structure changes payout design; include only if bounty play is acceptable. Re-entry is unverified.'},
  {date:'2026-11-28',time:'5:10 PM',id:'18',name:'$200 PokerAtlas Valuetown Bounty',buy:200,guarantee:20000,format:'Bounty / conditional discount',pdf:8,group:'secondary',note:'PokerAtlas PRO membership + claiming the offer in its app is required; first $200 buy-in drops to $180; subsequent entries cost $200. Membership price is not stated.'},
  {date:'2026-11-29',time:'11:10 AM',id:'19A',name:'$400 NLH — Event 19, Flight 1A',buy:400,guarantee:75000,format:'Multi-flight / multiday',pdf:3,group:'review',note:'Flights 1A–1C combine on Day 2. Structure forbids a player who bags Day 2 from entering a later flight; re-entry before bagging is not stated.'},
  {date:'2026-11-30',time:'11:10 AM',id:'19B',name:'$400 NLH — Event 19, Flight 1B',buy:400,guarantee:75000,format:'Multi-flight / multiday',pdf:3,group:'review',note:'Flights 1A–1C combine on Day 2. Structure forbids a player who bags Day 2 from entering a later flight; re-entry before bagging is not stated.'},
  {date:'2026-12-01',time:'11:10 AM',id:'19C',name:'$400 NLH — Event 19, Flight 1C',buy:400,guarantee:75000,format:'Multi-flight / multiday',pdf:3,group:'review',note:'Flights 1A–1C combine on Day 2. Structure forbids a player who bags Day 2 from entering a later flight; re-entry before bagging is not stated.'},
  {date:'2026-12-03',time:'11:10 AM',id:'26A',name:'$800 NLH — Event 26, Flight 1A',buy:800,guarantee:500000,format:'Multi-flight / multiday',pdf:12,group:'review',note:'Multiple starting flights and a shared Day 2. Re-entry policy not established; high buy-in makes this poor fit for strict single-entry cost control.'},
  {date:'2026-12-03',time:'5:10 PM',id:'26B',name:'$800 NLH — Event 26, Flight 1B',buy:800,guarantee:500000,format:'Multi-flight / multiday',pdf:13,group:'review',note:'Multiple starting flights and a shared Day 2. Re-entry policy not established; high buy-in makes this poor fit for strict single-entry cost control.'},
  {date:'2026-12-04',time:'11:10 AM',id:'26C',name:'$800 NLH — Event 26, Flight 1C',buy:800,guarantee:500000,format:'Multi-flight / multiday',pdf:12,group:'review',note:'Multiple starting flights and a shared Day 2. Re-entry policy not established; high buy-in makes this poor fit for strict single-entry cost control.'},
  {date:'2026-12-04',time:'5:10 PM',id:'26D',name:'$800 NLH — Event 26, Flight 1D',buy:800,guarantee:500000,format:'Multi-flight / multiday',pdf:13,group:'review',note:'Multiple starting flights and a shared Day 2. Re-entry policy not established; high buy-in makes this poor fit for strict single-entry cost control.'},
  {date:'2026-12-05',time:'11:10 AM',id:'26E',name:'$800 NLH — Event 26, Flight 1E',buy:800,guarantee:500000,format:'Multi-flight / multiday',pdf:12,group:'review',note:'Multiple starting flights and a shared Day 2. Re-entry policy not established; high buy-in makes this poor fit for strict single-entry cost control.'},
  {date:'2026-12-05',time:'5:10 PM',id:'26F',name:'$800 NLH — Event 26, Flight 1F Turbo',buy:800,guarantee:500000,format:'Multi-flight / multiday',pdf:14,group:'review',note:'Turbo starting flight in a shared multi-flight event; re-entry policy not established. Higher spend and format risk; exclude from strict shortlist.'},
  {date:'2026-12-06',time:'11:10 AM',id:'28',name:'$600 NLH (1 day)',buy:600,guarantee:40000,format:'One day',pdf:7,group:'candidate',note:'Event 26 Day 2 restart is scheduled at noon, overlapping this start. Re-entry policy is unverified.'},
  {date:'2026-12-17',time:'10:10 AM',id:'56A',name:'$1,100 NLH — Event 56, Flight 1A',buy:1100,guarantee:500000,format:'Multi-flight / multiday',pdf:35,group:'review',note:'$500,000 guarantee; multiple flights / Day 2. Flight 1A offers $40 off house fee before start ($1,060 instead of $1,100). Higher buy-in; re-entry unverified.'},
  {date:'2026-12-17',time:'6:10 PM',id:'56B',name:'$1,100 NLH — Event 56, Flight 1B',buy:1100,guarantee:500000,format:'Multi-flight / multiday',pdf:36,group:'review',note:'$500,000 guarantee; multiple flights / Day 2. Flight 1B offers $40 off house fee before start ($1,060 instead of $1,100). Higher buy-in; re-entry unverified.'},
  {date:'2026-12-18',time:'10:10 AM',id:'56C',name:'$1,100 NLH — Event 56, Flight 1C',buy:1100,guarantee:500000,format:'Multi-flight / multiday',pdf:35,group:'review',note:'$500,000 event guarantee; multiple starting flights / Day 2. Higher buy-in, re-entry policy not established.'},
  {date:'2026-12-18',time:'6:10 PM',id:'56D',name:'$1,100 NLH — Event 56, Flight 1D',buy:1100,guarantee:500000,format:'Multi-flight / multiday',pdf:36,group:'review',note:'$500,000 guarantee; multiple flights / Day 2. Flight 1B/1D structure offers $40 off house fee before start ($1,060 instead of $1,100). Higher buy-in; re-entry unverified.'},
  {date:'2026-12-19',time:'10:10 AM',id:'56E',name:'$1,100 NLH — Event 56, Flight 1E',buy:1100,guarantee:500000,format:'Multi-flight / multiday',pdf:35,group:'review',note:'$500,000 event guarantee; multiple starting flights / Day 2. Higher buy-in, re-entry policy not established.'},
  {date:'2026-12-20',time:'11:10 AM',id:'59A',name:'$600 NLH — Event 59, Flight 1A',buy:600,guarantee:150000,format:'Multi-flight / multiday',pdf:4,group:'review',note:'Event 56 Day 2 starts at 11:00 AM (overlap). $150,000 guarantee; Flight 1A offers $20 off house fee before start ($580 instead of $600); re-entry unverified.'},
  {date:'2026-12-21',time:'11:10 AM',id:'59B',name:'$600 NLH — Event 59, Flight 1B',buy:600,guarantee:150000,format:'Multi-flight / multiday',pdf:4,group:'review',note:'$150,000 event guarantee; three starting flights and Day 2. Re-entry policy not established.'},
  {date:'2026-12-22',time:'11:10 AM',id:'59C',name:'$600 NLH — Event 59, Flight 1C',buy:600,guarantee:150000,format:'Multi-flight / multiday',pdf:4,group:'review',note:'$150,000 event guarantee; three starting flights and Day 2. Re-entry policy not established.'},
  {date:'2026-12-23',time:'11:10 AM',id:'63',name:'$600 NLH (1 day)',buy:600,guarantee:30000,format:'One day',pdf:7,group:'candidate',note:'Event 59 Day 2 starts at 11:00 AM, so the events overlap. Re-entry policy is unverified.'}
];
// Line-by-line re-verification stamps (UTC dates this session checked the official pages).
const SCHEDULE_CHECKED = '2026-11-17';   // official DSE schedule page re-read in full (all 4 chunks) on this date
const STRUCTURE_CHECKED = '2026-11-16';  // structure PDFs last fetched on this date (not re-fetched 17 Nov)
const RATES_CHECKED = '2026-11-17';      // resort-fee / hotel-terms / suite-rates pages re-read on this date
const wynnEvents = [
  {date:'2026-11-27',time:'11:00 AM',id:'WPT',name:'$600 NLH Day 1A (WPT World Championship series)',buy:600,guarantee:400000,format:'Multi-day',note:'From the official WPT schedule PDF. Re-entry status not reviewed; series runs Nov 27–Dec 21 per the official Wynn poker page.',src:'https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf'},
  {date:'2026-12-03',time:'11:00 AM',id:'WPT',name:'$1,600 NLH Day 1A',buy:1600,guarantee:1000000,format:'Multi-day',note:'Official WPT schedule PDF row; structure not reviewed.',src:'https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf'},
  {date:'2026-12-05',time:'11:00 AM',id:'WPT-Prime',name:'WPT Prime Championship $1,100 NLH Day 1A',buy:1100,guarantee:5000000,format:'Multi-day',note:'Official WPT schedule PDF row; multi-day, structure not reviewed.',src:'https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf'},
  {date:'2026-12-09',time:'11:00 AM',id:'WPT',name:'$1,600 NLH (2 Day)',buy:1600,guarantee:1000000,format:'Multi-day',note:'Official WPT schedule PDF row.',src:'https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf'},
  {date:'2026-12-10',time:'10:00 AM',id:'SGM',name:'$400 Super Gold Million Mystery Bounty Day 1A',buy:400,guarantee:3000000,format:'Multi-day / mystery bounty',note:'Official Wynn poker page confirms the $400 buy-in and $3,000,000 guarantee for 2026. Mystery-bounty format; re-entry terms not reviewed.',src:'https://www.wynnlasvegas.com/casino/poker'},
  {date:'2026-12-13',time:'11:00 AM',id:'WPT',name:'$10,400 WPT World Championship Day 1A',buy:10400,guarantee:null,format:'Multi-day',note:'Guarantee blank on the official schedule; not calculable.',src:'https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf'},
  {date:'2026-12-13',time:'11:00 AM',id:'WPT',name:'$800 NLH Day 1A',buy:800,guarantee:500000,format:'Multi-day',note:'Official WPT schedule PDF row.',src:'https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf'},
  {date:'2026-12-13',time:'11:00 AM',id:'WPT',name:'$1,100 Ladies NLH Championship (2 Day)',buy:1100,guarantee:250000,format:'Multi-day',note:'Schedule footnote elsewhere shows a conflicting $11,100 Ladies entry figure; flagged, not resolved.',src:'https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf'},
  {date:'2026-12-17',time:'12:00 PM',id:'WPT',name:'$3,000 NLH Day 1A',buy:3000,guarantee:2000000,format:'Multi-day',note:'Official WPT schedule PDF row.',src:'https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf'},
  {date:'2026-12-18',time:'1:00 PM',id:'WPT',name:'$25,800 NLH High Roller (2 Day)',buy:25800,guarantee:null,format:'Multi-day',note:'Guarantee blank on the official schedule; very high buy-in.',src:'https://cdn.wynnresorts.com/image/upload/v1757097329/visitwynn_pdfs_files/Poker/WPT/WPT_World_Championship_Schedule.pdf'},
  {date:null,time:'12:00 PM',id:'DAILY',name:'Wynn daily NLH Mon–Thu — $200 ($10,000 GTD)',buy:200,guarantee:10000,format:'Daily · re-entry allowed',note:'Re-entry allowed at $200 until level 9 per official structures — NOT single-entry.',src:'https://cdn.wynnresorts.com/image/upload/v1752011166/visitwynn_pdfs_files/Poker/Daily%20Tournaments/poker-daily-tournament-poster.pdf'},
  {date:null,time:'12:00 PM',id:'DAILY-FRI',name:'Wynn Friday NLH Rebuy & Add-on — $240 ($40,000 GTD)',buy:240,guarantee:40000,format:'Daily · rebuy + add-on',note:'Unlimited $200 rebuys while ≤15,000 chips plus one $100 add-on — NOT single-entry; separate spending section.',src:'https://cdn.wynnresorts.com/image/upload/v1752011166/visitwynn_pdfs_files/Poker/Daily%20Tournaments/poker-daily-tournament-poster.pdf'},
  {date:null,time:'6:00 PM',id:'NIGHTLY',name:'Wynn nightly NLH — $160 ($10,000 GTD)',buy:160,guarantee:10000,format:'Nightly · re-entry + add-on',note:'Re-entry allowed; one $100 add-on per entry until end of registration — NOT single-entry.',src:'https://cdn.wynnresorts.com/image/upload/v1752011166/visitwynn_pdfs_files/Poker/Daily%20Tournaments/poker-daily-tournament-poster.pdf'}
];
const otherVenueEvents = [
  {venue:'Caesars Palace',date:null,time:'10:00 AM',id:'DAILY',name:'Caesars Palace daily NLH — $100 entry',buy:100,guarantee:1000,format:'Daily · re-entry + add-on',note:'Re-entry allowed at first break ($100); optional $50 add-on for 15,000 chips — NOT single-entry. Undated 2026 flyer.',src:'https://www.caesars.com/content/dam/empire/clv/casino/poker/tournament-schedule/clv-poker-daily-nlh-tournament-flyer-2026.pdf'},
  {venue:'Caesars Palace',date:null,time:'2:00 PM',id:'DAILY',name:'Caesars Palace daily NLH — $160 entry',buy:160,guarantee:1000,format:'Daily · re-entry + add-on',note:'Re-entry at first break; optional $50 add-on — NOT single-entry. Undated 2026 flyer.',src:'https://www.caesars.com/content/dam/empire/clv/casino/poker/tournament-schedule/clv-poker-daily-nlh-tournament-flyer-2026.pdf'},
  {venue:'Caesars Palace',date:null,time:'6:00 PM',id:'DAILY',name:'Caesars Palace daily NLH — $100 entry',buy:100,guarantee:1000,format:'Daily · re-entry + add-on',note:'Same format as the 10:00 AM event. Undated 2026 flyer.',src:'https://www.caesars.com/content/dam/empire/clv/casino/poker/tournament-schedule/clv-poker-daily-nlh-tournament-flyer-2026.pdf'},
  {venue:'Caesars Palace',date:null,time:'9:00 PM',id:'DAILY',name:'Caesars Palace daily NLH — $160 entry',buy:160,guarantee:1000,format:'Daily · re-entry + add-on',note:'Same format as the 2:00 PM event. Undated 2026 flyer.',src:'https://www.caesars.com/content/dam/empire/clv/casino/poker/tournament-schedule/clv-poker-daily-nlh-tournament-flyer-2026.pdf'},
  {venue:'Bellagio',date:null,time:'11:00 AM',id:'FRI',name:'Bellagio Friday NLH — $600',buy:600,guarantee:null,format:'Weekly · re-entry + super stack',note:'Re-entry through end of level 8; optional $40 super stack — NOT single-entry. Guarantee not stated on the structure.',src:'https://assets.contentstack.io/v3/assets/bltc6ce635bc4868eb2/blt9cf95b0e60ec253e/6af491a3a9851d75c40be840/mgm-bellagio-poker-fridays-$600-nlh.pdf'},
  {venue:'Bellagio',date:null,time:'11:00 AM',id:'SAT',name:'Bellagio Saturday NLH — $1,000 file name / $1,100 PDF header',buy:null,guarantee:50000,format:'Weekly · re-entry + super stack',note:'IRREGULARITY: official file name says $1,000 while the PDF header says $1,100 — buy-in left blank pending resolution. Re-entry through level 8.',src:'https://assets.contentstack.io/v3/assets/bltc6ce635bc4868eb2/blt6d47974bf5a7d9b6/6af491a391a6e8e4230c9e07/mgm-bellagio-poker-saturdays-$1000-nlh.pdf'},
  {venue:'Bellagio',date:null,time:'11:00 AM',id:'SUN',name:'Bellagio Sunday H.O.R.S.E. — $400',buy:400,guarantee:null,format:'Weekly · re-entry + super stack',note:'Re-entry through end of level 8; optional $25 super stack — NOT single-entry. Guarantee not stated.',src:'https://assets.contentstack.io/v3/assets/bltc6ce635bc4868eb2/blt07fcf1244a6da661/6af491a339e2b4f6b76a86ad/mgm-bellagio-poker-sundays-$400-horse.pdf'}
];
const money = (v) => v == null ? '<span class="unknown" title="No official value confirmed">—</span>' : `$${Number(v).toLocaleString('en-US')}`;
const officialLink = (url,label='Official source') => `<a class="source-link" href="${url}" target="_blank" rel="noopener">${label} ↗</a>`;
const dateText = (s) => new Date(`${s}T12:00:00Z`).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'});
function renderEvents(targetId, group) {
  const root=document.getElementById(targetId); if(!root)return;
  const rows=events.filter(e=>group==='other'?e.group!=='candidate':(!group||e.group===group)).sort((a,b)=>a.date.localeCompare(b.date)||a.time.localeCompare(b.time)).map(e=>`<tr data-date="${e.date}" data-single-entry="unverified"><td>${dateText(e.date)}</td><td>${e.time}</td><td>${e.id}</td><td>${e.name}<small>${e.note}</small></td><td>${money(e.buy)}</td><td>${money(e.guarantee)}</td><td>${e.guarantee==null?'<span class="unknown" title="Not calculable without a published guarantee">—</span>':`${(e.guarantee/e.buy).toFixed(1)}×`}</td><td>${e.format}</td><td><span class="pill warn">Not verified</span></td><td><time datetime="${SCHEDULE_CHECKED}">${SCHEDULE_CHECKED}</time><small>Schedule row re-read this date; structure PDF last read ${STRUCTURE_CHECKED}.</small></td><td>${officialLink(OFFICIAL.schedule,'Schedule')}<br>${officialLink(pdf(e.pdf),'Structure')}</td></tr>`).join('');
  root.innerHTML=rows||'<tr><td colspan="11">No entries in this section.</td></tr>';
}
function renderReview() {
  const root=document.getElementById('review-events'); if(!root)return;
  root.innerHTML=events.filter(e=>e.group==='review'||e.group==='secondary').map(e=>`<tr><td>${dateText(e.date)} · ${e.time}</td><td>${e.name}</td><td>${e.note}</td><td>${officialLink(OFFICIAL.schedule,'Schedule')}<br>${officialLink(pdf(e.pdf),'Structure')}</td></tr>`).join('');
}
function setupFilters(){
  const input=document.querySelector('[data-table-search]');
  const dateInput=document.querySelector('[data-date-filter]');
  const seInput=document.querySelector('[data-single-entry-only]');
  const seNote=document.querySelector('[data-single-entry-note]');
  const apply=()=>{
    const q=(input&&input.value||'').toLowerCase();
    const d=dateInput&&dateInput.value?dateInput.value:'';
    const seOnly=seInput&&seInput.checked;
    if(seNote)seNote.hidden=!seOnly;
    document.querySelectorAll('main table tbody tr').forEach(row=>{
      let show=true;
      if(q&&!row.textContent.toLowerCase().includes(q))show=false;
      if(d&&row.dataset.date!==undefined&&row.dataset.date!==d)show=false;
      if(seOnly&&row.dataset.singleEntry!==undefined&&row.dataset.singleEntry!=='confirmed')show=false;
      row.hidden=!show;
    });
  };
  if(input)input.addEventListener('input',apply);
  if(dateInput)dateInput.addEventListener('input',apply);
  if(seInput)seInput.addEventListener('change',apply);
  const clear=document.querySelector('[data-filter-clear]');
  if(clear)clear.addEventListener('click',()=>{if(input)input.value='';if(dateInput)dateInput.value='';if(seInput)seInput.checked=false;apply();});
}
function renderOverlap(){
  const root=document.getElementById('overlap-events'); if(!root)return;
  const byDate={};
  events.forEach(e=>{if(!byDate[e.date])byDate[e.date]=[];byDate[e.date].push(e);});
  const rows=Object.keys(byDate).sort().filter(d=>byDate[d].length>1).map(d=>{
    const list=byDate[d].sort((a,b)=>a.time.localeCompare(b.time));
    const primary=list[0];
    const fallbacks=list.slice(1);
    const flag=list.some(e=>e.format.includes('Multi-flight')||e.format.includes('multiday'))?'Hard conflict: multi-flight / Day-2 restart shares the day':'Conditional: same-day sequence not guaranteed (no finish times published)';
    return `<tr data-date="${d}"><td>${dateText(d)}</td><td>${primary.time} · ${primary.id} — ${primary.name}</td><td>${fallbacks.map(e=>`${e.time} · ${e.id} — ${e.name}`).join('<br>')}</td><td><span class="pill warn">${flag}</span></td><td>${officialLink(OFFICIAL.schedule,'Official schedule')}</td></tr>`;
  }).join('');
  root.innerHTML=rows||'<tr><td colspan="5">No multi-event days in this dataset.</td></tr>';
}
function renderVenue(targetId, kind){
  const root=document.getElementById(targetId); if(!root)return;
  let list=[];
  if(kind==='venetian')list=events.map(e=>({...e,src:OFFICIAL.schedule,venue:'The Venetian (DSE IV)'}));
  else if(kind==='wynn')list=wynnEvents.map(e=>({...e,venue:'Wynn Las Vegas'}));
  else list=otherVenueEvents;
  list.sort((a,b)=>(a.date||'9999').localeCompare(b.date||'9999')||a.time.localeCompare(b.time));
  root.innerHTML=list.map(e=>`<tr${e.date?` data-date="${e.date}"`:''}><td>${e.date?dateText(e.date):'Daily / weekly'}</td><td>${e.time}</td><td>${e.id}</td><td>${e.name}<small>${e.note}</small></td><td>${money(e.buy)}</td><td>${money(e.guarantee)}</td><td>${e.format}</td><td><span class="pill warn">Not verified single-entry</span></td><td><time datetime="${SCHEDULE_CHECKED}">${kind==='venetian'?SCHEDULE_CHECKED:'2026-11-16'}</time></td><td>${officialLink(e.src,'Official source')}</td></tr>`).join('');
}
function initCalculator(){
  const pick=document.getElementById('calc-events'); if(!pick)return;
  const sorted=[...events].sort((a,b)=>a.date.localeCompare(b.date)||a.time.localeCompare(b.time));
  pick.innerHTML=sorted.map((e,i)=>`<label class="calc-row"><input type="checkbox" data-calc-buy="${e.buy}" data-calc-id="${e.id}" data-calc-date="${e.date}"><span><strong>${dateText(e.date)} · ${e.time} · ${e.id}</strong> — ${e.name}</span><b>${money(e.buy)}</b></label>`).join('');
  const nights=document.getElementById('calc-nights');
  const rate=document.getElementById('calc-rate');
  const parking=document.getElementById('calc-parking');
  const out=document.getElementById('calc-output');
  const preset=document.querySelectorAll('[data-rate-preset]');
  const FEE=55, TAX=0.1338; // official: $55 resort fee + 13.38% Clark County room tax
  const calc=()=>{
    const checked=[...pick.querySelectorAll('input:checked')];
    const entries=checked.length;
    const entryCost=checked.reduce((s,el)=>s+Number(el.dataset.calcBuy),0);
    const n=Number(nights.value)||0;
    const r=rate.value===''?null:Number(rate.value);
    const p=parking.value===''?0:Number(parking.value);
    let hotel='—', total=null, warn='';
    if(r!==null){
      const perNight=(r+FEE)*(1+TAX)+p;
      hotel=`$${perNight.toFixed(2)} / night × ${n} = $${(perNight*n).toFixed(2)}`;
      total=entryCost+perNight*n;
    }else{
      warn='Nightly base rate missing: hotel portion cannot be computed. Enter a rate verified for your dates (booking quote), or use a conditional preset below.';
    }
    out.innerHTML=`<table><tbody>
      <tr><td>Entries selected</td><td>${entries}</td></tr>
      <tr><td>Entry cost (Σ buy-ins)</td><td>$${entryCost.toLocaleString('en-US')}</td></tr>
      <tr><td>Hotel (rate + $55 fee + 13.38% tax + parking) × nights</td><td>${hotel}</td></tr>
      <tr><td><strong>Estimated trip cost</strong></td><td><strong>${total!==null?'$'+total.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}):'entries only — '+warn}</strong></td></tr>
    </tbody></table>${warn?`<p class="callout danger">${warn}</p>`:''}<p class="muted">Formula: entries × buy-ins + nights × true hotel cost/night. Presets are advertised starting endpoints, not quotes for any date.</p>`;
  };
  [nights,rate,parking].forEach(el=>el.addEventListener('input',calc));
  pick.addEventListener('change',calc);
  preset.forEach(b=>b.addEventListener('click',()=>{rate.value=b.dataset.ratePreset;calc();}));
  calc();
}
function loadRecheck(){
  const root=document.getElementById('recheck-body'); if(!root)return;
  fetch('data/recheck_log.json').then(r=>r.json()).then(log=>{
    const urls=log.urls||[];
    document.getElementById('recheck-meta').textContent=`Last run: ${log.checked_at} · ${urls.length} official URLs · ${urls.filter(u=>u.status==='changed').length} changed since previous run`;
    root.innerHTML=urls.map(u=>`<tr><td>${u.label}</td><td><a class="source-link" href="${u.url}" target="_blank" rel="noopener">${u.url}</a></td><td><span class="pill ${u.status==='changed'?'danger':''}">${u.status}</span></td><td><time datetime="${u.checked_at}">${u.checked_at}</time></td></tr>`).join('');
  }).catch(()=>{root.innerHTML='<tr><td colspan="4">recheck log not loaded (open this page over HTTP, e.g. the GitHub Pages site).</td></tr>';});
}
document.addEventListener('DOMContentLoaded',()=>{renderEvents('candidate-events','candidate');renderEvents('other-events','other');renderReview();setupFilters();renderOverlap();renderVenue('venetian-events','venetian');renderVenue('wynn-events','wynn');renderVenue('other-events-table','other');initCalculator();loadRecheck();});
