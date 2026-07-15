

(function(){
  function esc(x){ return String(x==null?'':x).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  function jsq(x){ return String(x).replace(/\\/g,'\\\\').replace(/'/g,"\\'"); }
  function motionOK(){ try { return !navigator.webdriver && !(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches); } catch(e){ return true; } }
  function art(n, glyph){ try { var u=(typeof artUrl==='function')?artUrl(n):''; return u?'<img class="f-art" src="'+esc(u)+'" alt="" loading="lazy">':'<span class="f-glyph">'+glyph+'</span>'; } catch(e){ return '<span class="f-glyph">'+glyph+'</span>'; } }
  function chipLogo(n){ try { return (typeof nameLogo==='function')?nameLogo(n):''; } catch(e){ return ''; } }
  function fmtOdds(c){ if(c==null) return ''; return '1:'+(c>=1000?(Math.round(c/100)/10)+'k':c); }
  // v644 — THE GRAIL LEDGER: dated found-chronicle shared by both grail forges (d2r_foundLog,
  // written by toggleOwned/toggleSetPiece — the single sources of truth — so a tick ANYWHERE dates it).
  function _flog(){ try { return JSON.parse(window.LSR.getItem('d2r_foundLog')||'{}'); } catch(e){ return {}; } }
  // v664 (army audit) — the display stamps ('Jul 12, 2026 · 22:41') were compared LEXICALLY, and month
  // names sort alphabetically (May > Jun > Jul) — so May seeds permanently outranked fresh July ticks and
  // the ↩ undo bar targeted the WRONG item. Parse to epoch; the display string stays untouched.
  function _flogTime(s){ var t=Date.parse(String(s||'').replace(/\s*\u00b7\s*imported\s*$/i,'').replace(/\u00b7/g,' ')); return isFinite(t)?t:0; }  

  function _flogSort(names){ var fl=_flog(); return names.slice().sort(function(a,b){ var da=_flogTime(fl[a]), db=_flogTime(fl[b]); if(da!==db) return db-da; if(fl[a]&&!fl[b]) return -1; if(fl[b]&&!fl[a]) return 1; return a.localeCompare(b); }); }
  function _undoBar(kind){
    var fl=_flog(); var keys=Object.keys(fl);
    var _L=(typeof ITEMS!=='undefined')?ITEMS:(window.ITEMS||[]);   // v644.1 — ITEMS is const-scoped elsewhere; the bare typeof check silently emptied the 'uni' ledger
    var mine=keys.filter(function(n){ var isU=_L.some(function(i){return i.n===n;}) || !!(window._UNI_EXTRA && window._UNI_EXTRA[n]); return kind==='uni'?isU:!isU; });   // v664 (army audit) — the 62 mod-chronicle uniques bucketed as 'set' and the F·Sets undo bar walked them INTO d2r_setPieces
    if(!mine.length) return '';
    mine=_flogSort(mine); var last=mine[0];
    var fn=kind==='uni'?'grailFoundUni':'grailTogglePiece';
    return '<div class="gf-undo-bar forge-restore-top" style="margin:6px 0"><span>✅ last found: <b data-arttip="'+esc(last)+'">'+esc(last)+'</b> <span class="gp-date">'+esc(fl[last])+'</span></span>'
      +'<button class="f-btn f-btn-mini" onclick="window.'+fn+'(this,\''+jsq(last)+'\')" title="mis-tick? un-mark it — the ledger entry is erased and it returns to the hunt">↩ undo</button></div>';
  }
  function _tickBtn(name, fn){ return '<span class="gf-tick" role="button" tabindex="0" data-gf-tick="'+esc(name)+'" onclick="event.stopPropagation();window.'+fn+'(this,\''+jsq(name)+'\')" title="✓ mark '+esc(name)+' FOUND — tallies the Calculator + grail meters instantly">✓</span>'; }
  // v646 — THE GRAIL WALL is a DRAWER, not an avalanche (Konyo: "it takes up the whole page —
  // needs to be intelligently and proportionally built, dropdown expandable"). Collapsed by
  // default behind a flagship summary bar; open = a type-to-filter box + a CONTAINED scroll
  // panel (~5 rows) with a styled scrollbar. One renderer, BOTH grail forges, same position.
  function _allGrid(title, sub, entries, fn){
    if(!entries.length) return '';
    var openAttr=''; try { if(localStorage.getItem('d2r_grailWallOpen')==='1') openAttr=' open'; } catch(e){}
    var H=['<details class="gf-wall"'+openAttr+' ontoggle="try{localStorage.setItem(\'d2r_grailWallOpen\',this.open?\'1\':\'\')}catch(e){}">'
      +'<summary class="gf-wall-sum"><span class="gf-wall-emblem">📿</span><span class="gf-wall-hd"><span class="gf-wall-t">'+title+'</span><span class="gf-wall-sub">'+sub+'</span></span><span class="gf-wall-ct">'+entries.length+'</span><span class="gf-wall-chev">▾</span></summary>'
      +'<div class="gf-wall-body"><input class="gf-wall-filter" type="text" placeholder="🔍 type to filter '+entries.length+'…" oninput="window.gfWallFilter(this)">'
      +'<div class="gf-allgrid">'];
    entries.forEach(function(e){ H.push('<span class="gf-piece gf-miss" data-arttip="'+esc(e.tip||e.n)+'">'+_tickBtn(e.key||e.n, fn)+chipLogo(e.n)+'<span class="gp-nm">'+esc(e.n)+'</span>'+(e.badge?'<span class="gq">'+esc(e.badge)+'</span>':'')+'</span>'); });
    H.push('</div></div></details>');
    return H.join('');
  }
  // v647 — SEE-MORE EXPANDER (Konyo: 'how do i see all quick wins — it needs a dropdown
  // collapsable see-more thing'): every capped card list shows its head, and the ENTIRE tail
  // lives inside a collapsed drawer — nothing is ever unreachable, nothing floods the page.
  function _moreWrap(cards, shown, label){
    if(!cards.length) return '';
    if(cards.length<=shown) return cards.join('');
    var head=cards.slice(0,shown).join(''), tail=cards.slice(shown);
    return head+'<details class="gf-more"><summary class="gf-more-sum">▾ see all '+cards.length+' '+esc(label)+' <span class="gf-more-ct">+'+tail.length+' more</span></summary><div class="gf-more-body">'+tail.join('')+'</div></details>';
  }
  window.gfWallFilter=function(inp){
    try { var q=(inp.value||'').toLowerCase().trim(); var grid=inp.parentElement.querySelector('.gf-allgrid');
      [].forEach.call(grid.children, function(ch){ ch.style.display = (!q || (ch.textContent||'').toLowerCase().indexOf(q)>=0) ? '' : 'none'; });
    } catch(e){}
  };

  

  function _uniItems(){ var L=(typeof ITEMS!=='undefined')?ITEMS:(window.ITEMS||[]); var base=L.filter(function(x){ return x.tier==='grail'||x.tier==='high'||x.tier==='common'; });
    // v659 — the mod Chronicle tracks uniques beyond the calculator DB (low vanilla uniques, Latent charms …).
    // Append them to the F·Uniques universe ONLY (never the calculator/boss tables) so every in-game find has
    // a card and the found % tracks the in-game Chronicle. Cached objects so funiScan identity stays stable.
    var xc=(window._uniExtraCache=window._uniExtraCache||{});
    var ex=Object.keys(window._UNI_EXTRA||{}).map(function(n){ return xc[n]||(xc[n]={ n:n, tier:'common', sources:[] }); });
    return base.concat(ex); }
  function _ownedNames(){ try { var s=new Set(JSON.parse(window.LSR.getItem('d2r_owned')||'[]')); Object.keys(JSON.parse(window.LSR.getItem('d2r_foundLog')||'{}')).forEach(function(n){ s.add(n); }); return s; } catch(e){ return new Set(); } }   // v677 — found = ledger ∪ legacy owned
  function _bestSrc(it){
    var best=null, bestR=-1;
    (it.sources||[]).forEach(function(s){ if(!s||s.blocked||s.chance==null) return; var rate=(s.kph||30)/s.chance; if(rate>bestR){ bestR=rate; best=s; } });
    return best && { s:best, rate:bestR };
  }
  window.funiScan=function(){
    var own=_ownedNames(), items=_uniItems();
    var missing=[], found=0;
    items.forEach(function(x){ if(own.has(x.n)) found++; else missing.push(x); });
    var bySrc={};
    missing.forEach(function(x){
      var b=_bestSrc(x); var key=b?b.s.boss:'Anywhere — no verified source yet';
      var g=(bySrc[key]=bySrc[key]||{boss:key, bossId:b&&b.s.bossId, items:[], ev:0}); g.items.push(x);
      if(b){ g.ev+=b.rate; x._bs=b; }   // per-run expected missing-unique drops per HOUR (Σ kph/chance) — the true farm metric
    });
    var runs=Object.keys(bySrc).map(function(k){return bySrc[k];}).sort(function(a,b){ return b.ev-a.ev || b.items.length-a.items.length; });
    // v559.2 — chips inside a run lead with the most-likely drops (best odds first)
    runs.forEach(function(r){ r.items.sort(function(a,b){ var ca=(a._bs?a._bs.s.chance:9e9), cb=(b._bs?b._bs.s.chance:9e9); return ca-cb; }); });
    var low=missing.filter(function(x){ return (x.qlvl||99)<=35; }).sort(function(a,b){ return (a.qlvl||0)-(b.qlvl||0); });
    // v619 (Konyo: F-Uniques gets the same smart sync + stamps) — SEALED GROUNDS: group EVERY verified-
    // source item (found or not) by its best boss; a run whose whole pool is found earns the horizontal
    // seal. Only fixed-pool runs can seal honestly — the run must have ≥2 verified items so a lone drop
    // doesn't stamp a whole zone (the Hell TC85 caveat lives on the runs that never fill).
    var byAll={};
    items.forEach(function(x){ var b=_bestSrc(x); if(!b) return; var k=b.s.boss;
      var g=(byAll[k]=byAll[k]||{boss:k, total:0, found:0, names:[]}); g.total++; if(own.has(x.n)) g.found++; else g.names.push(x.n); });
    var sealed=Object.keys(byAll).map(function(k){return byAll[k];}).filter(function(g){ return g.total>=2 && g.found===g.total; })
      .sort(function(a,b){ return b.total-a.total; });
    var lowTotal=items.filter(function(x){ return (x.qlvl||99)<=35; }).length;
    // v663 — GAME-TRUE DENOMINATOR (Konyo: 'calibrate and fix the percentages'). The in-game Chronicle
    // counts 403 unique entries (uniqueitems.txt, spawnable, extracted from the live RotW CASC store
    // 2026-07-12) — the site's 364 named cards are a subset (39 gap entries: internal-typo aliases,
    // 8 Rainbow Facet rows, quest uniques, RotW customs). The headline % must use the GAME's math:
    // found/403, or the site reads 63% while the game says 59%. The remaining drift is real missing
    // data — his 56-shot scroll had gaps (~8 found rows never on screen) — NOT a counting bug.
    return { total:items.length, found:found, missing:missing, runs:runs, low:low, sealed:sealed, lowTotal:lowTotal, chronTotal:403 };
  };
  var _fuF='all';
  window.funiSetFilter=function(f){ _fuF=(_fuF===f&&f!=='all')?'all':f; window.renderForgeUni(); };
  window.grailFoundUni=function(el,name){
    var wasOwned=_ownedNames().has(name);   // v559.1 — un-marking must not celebrate
    var act=function(){ try { if(typeof window.toggleOwned==='function') window.toggleOwned(name); } catch(e){} window.renderForgeUni(); if(!wasOwned) _grailToast('🏆','<b>'+esc(name)+'</b> found!','the unique grail grows'); };
    _cardAnim(el, wasOwned?'':'f-anim-forged', wasOwned?0:430, act);
  };
  function _cardAnim(el,cls,ms,fn){
    if(!motionOK()){ fn(); return; }
    try { var card=el&&el.closest?el.closest('.f-card'):null; if(!card){ fn(); return; }
      card.classList.add(cls);
      if(cls==='f-anim-forged'){ for(var i=0;i<12;i++){ var sp=document.createElement('span'); sp.className='f-spark'+(i%3===0?' f-ember':''); sp.style.setProperty('--dx',(Math.random()*170-85)+'px'); sp.style.setProperty('--dy',(-30-Math.random()*85)+'px'); sp.style.animationDelay=(Math.random()*110)+'ms'; card.appendChild(sp); } var rg=document.createElement('span'); rg.className='f-ring'; card.appendChild(rg); }   // v606 — grail-find gets the shockwave too
      setTimeout(fn,ms);
    } catch(e){ fn(); }
  }
  function _grailToast(ico,main,sub){
    if(!motionOK()) return;
    try { var t=document.createElement('div'); t.className='forge-toast'; t.innerHTML=ico+' '+main+' <span class="ft-sub">'+sub+'</span>';
      (function(el){var st=document.getElementById('forge-toasts');if(!st){st=document.createElement('div');st.id='forge-toasts';document.body.appendChild(st);}st.appendChild(el);})(t); setTimeout(function(){ t.classList.add('out'); setTimeout(function(){ t.remove(); },450); },2400); } catch(e){}
  }
  window._grailToast=_grailToast;   // v615 — the consume sync narrates vault exits through the same toast
  function _meter(found,total,color){
    var pct=total?Math.round(found/total*100):0;
    return '<div class="forge-progress" title="'+found+' of '+total+'"><div class="fp-track"><div class="fp-fill" style="width:'+pct+'%'+(color?';background:linear-gradient(90deg,'+color+')':'')+'"></div></div>'
      +'<div class="fp-lbl">🏆 <b>'+found+'</b> / '+total+' found<span class="fp-pct">'+pct+'%</span></div></div>';
  }
  function _tile(key,emoji,label,cls,n,F,setter){
    return '<button class="forge-tab '+cls+(F===key?' on':'')+(n===0?' ft-empty':'')+'" onclick="'+setter+'(\''+key+'\')" title="show '+esc(label)+'">'
      +'<span class="ft-emoji">'+emoji+'</span><span class="ft-lbl">'+esc(label)+'</span><span class="ft-ct">'+n+'</span></button>';
  }
  function _itemChip(n,q){
    return '<span class="gf-chip" data-arttip="'+esc(n)+'" onclick="window.navigateToItem&&window.navigateToItem(\''+jsq(n)+'\')" title="open '+esc(n)+'’s card">'+_tickBtn(n,'grailFoundUni')+chipLogo(n)+'<span>'+esc(n)+'</span>'+(q?'<span class="gq">q'+q+'</span>':'')+'</span>';
  }
  function _runCard(r,i){
    // v647.1 — the '+N more from this run' dead-end becomes an in-card drawer: EVERY drop of the
    // run is visible + tickable in place (Konyo: 'there should be 300+ in all — i dont see them').
    var _all=r.items.map(function(x){ return _itemChip(x.n,x.qlvl); });
    var chips=_all.slice(0,10).join('');
    var more=_all.length>10?'<details class="gf-more gf-more-inline"><summary class="gf-more-sum">▾ all '+_all.length+' drops from this run <span class="gf-more-ct">+'+(_all.length-10)+' more</span></summary><div class="gf-more-body gf-chips">'+_all.slice(10).join('')+'</div></details>':'';
    var bossBtn=r.bossId?'<div class="f-cta"><button class="f-btn" onclick="window.openBossDetail&&window.openBossDetail(\''+jsq(r.bossId)+'\')">📜 boss card</button></div>':'';
    return '<div class="f-card f-pipe"><div class="f-cardart f-cardart-hd">'+art(r.items[0]?r.items[0].n:'','🎯')+'<span class="f-cardart-badge">'+(i+1)+'</span></div><div class="f-cardbody">'
      +'<div class="f-cardtitle"><div class="f-atomact">Run <b class="f-rwbig">'+esc(r.boss)+'</b></div>'
      +'<div class="f-atomsubrow">drops <b>'+r.items.length+'</b> of your missing uniques'+(r.ev>0?' · expected <b>~1 every '+(r.ev>=1?(Math.round(10/r.ev)/10)+'h':Math.round(1/r.ev)+'h')+'</b> of running':'')+'</div>'
      +'<div class="gf-chips">'+chips+'</div>'+more+'</div>'+bossBtn+'</div></div>';
  }
  function _uniItemCard(x){
    var bb=_bestSrc(x); var b=bb&&bb.s;
    var src=b?('<div class="gf-src">📍 best run: <b>'+esc(b.boss)+'</b> <span class="gf-odds">'+fmtOdds(b.chance)+'</span>'+(b.kph?'<span class="gf-odds">~'+b.kph+' kph</span>':'')+'</div>')
             :'<div class="gf-note">no verified source — drops broadly</div>';
    return '<div class="f-card f-step f-atom"><div class="f-cardart f-cardart-hd">'+art(x.n,'🏆')+'<span class="f-cardart-badge">🏆</span></div><div class="f-cardbody">'
      +'<div class="f-cardtitle"><div class="f-atomact">Find <b class="f-rwbig" data-arttip="'+esc(x.n)+'">'+esc(x.n)+'</b> <span class="f-need">qlvl '+(x.qlvl||'?')+'</span></div>'+src+'</div>'
      +'<div class="f-cta"><button class="f-btn f-btn-go" onclick="window.grailFoundUni(this,\''+jsq(x.n)+'\')">✓ found it</button></div></div></div>';
  }
  window.renderForgeUni=function(){
    var box=document.getElementById('funi-body'); if(!box) return;
    var s=window.funiScan(); var F=_fuF; var H=[];
    // v682.1 — the HEADLINE meter is the IN-GAME truth (Konyo: 'Uniques is at 60% for chronicle..
    // uniques isnt synced'): found / the mod's 403-entry chronicle, the same number the game shows.
    // The 368 named cards stay the working grid below; the ~35 still-dark mod uniques are unknowable
    // until found (the game silhouettes them as bare base types), so 403 is the only honest total.
    H.push(_meter(s.found,s.chronTotal||s.total,''));
    // v663 — the IN-GAME line: the mod chronicle counts 403 entries, the game's % is found/403.
    // Keeping both numbers visible kills the '63% here, 59% in game' confusion at the source.
    // v682.1 — the headline meter above IS the in-game number now; this line explains the named-card grid
    if (s.chronTotal) H.push('<div class="f-atomsub" style="margin:-4px 0 8px;opacity:.85" title="the in-game Chronicle counts '+s.chronTotal+' unique entries (game-file truth: uniqueitems.txt) — the '+s.total+' cards here are the named subset; the remaining rows are still dark silhouettes in-game (bare base types), unknowable until they drop">🗂 named cards: <b>'+s.found+' / '+s.total+'</b> ticked · <b>'+(s.chronTotal-s.total)+'</b> chronicle rows still dark (names reveal on find)</div>');
    H.push(_undoBar('uni'));   // v644 — mis-ticks are one ↩ away, forge-style
    // v560 — UNIFIED sub-tabs across BOTH grail forges (Konyo: same names, same logic, set or unique):
    // ▦ All missing · 🎯 Best runs · ⚡ Quick wins (low-level uniques / 1-piece sets) · ✅ Found
    H.push('<div class="forge-tabs">'
      +_tile('all','▦','All missing','ft-all',(s.chronTotal?s.chronTotal-s.found:s.missing.length),F,'window.funiSetFilter')   // v682.2 — SAME universe as the headline (403): named missing + still-dark rows
      +_tile('runs','🎯','Best runs','ft-pipe',s.runs.length,F,'window.funiSetFilter')
      +_tile('low','⚡','Quick wins','ft-step',s.low.length,F,'window.funiSetFilter')
      +_tile('found','✅','Found','ft-done',s.found,F,'window.funiSetFilter')
      +'</div>');

    // v646 — THE GRAIL WALL: identical drawer, identical position on BOTH grail forges
    if(F==='all'){
      var _ownA=_ownedNames();
      var _missAll=_uniItems().filter(function(x){ return !_ownA.has(x.n); }).sort(function(a,b){ return (a.qlvl||99)-(b.qlvl||99) || a.n.localeCompare(b.n); })
        .map(function(x){ return { n:x.n, key:x.n, badge:(x.qlvl>0?'q'+x.qlvl:'') }; });
      H.push(_allGrid('Every missing unique — tick as you find', 'the complete pool, qlvl-sorted · ✓ tallies the Calculator + meters instantly', _missAll, 'grailFoundUni'));
      // v682.2 — the still-dark remainder: these chronicle rows exist in-game as bare base-type
      // silhouettes; a dark row's unique NAME is hidden until it drops, so it can't be carded yet.
      // They count in the All-missing number so every meter tells the same 403-story.
      var _darkN=(s.chronTotal||0)-s.total;
      if(_darkN>0) H.push('<div class="rw-stamp-mini rw-band" style="margin:8px 0"><span class="rw-band-t">🌑 + '+_darkN+' still-dark chronicle rows</span><span class="rw-band-s">the game hides their names until they drop — they reveal (and card here) on find · counted in All missing</span></div>');
    }
    // HERO: the single best run
    var top=s.runs[0];
    if(top&&F!=='found'){
      H.push('<div class="forge-hero forge-hero-pipe"><span class="fh-ember"></span><span class="fh-ember"></span><span class="fh-ember"></span><span class="fh-ember"></span>'
        +'<div class="fh-artwrap"><div class="fh-art">'+art(top.items[0]?top.items[0].n:'','🎯')+'</div><div class="fh-icobadge">🎯</div></div>'
        +'<div class="fh-main"><div class="fh-lead">👉 DO THIS ONE THING · best farm</div><div class="fh-name">'+esc(top.boss)+'</div>'
        +'<div class="fh-body">best expected yield — <b>'+top.items.length+'</b> missing uniques'+(top.ev>0?' · <b>~1 every '+(top.ev>=1?(Math.round(10/top.ev)/10)+'h':Math.round(1/top.ev)+'h')+'</b>':'')+' — '+top.items.slice(0,3).map(function(x){return esc(x.n);}).join(' · ')+(top.items.length>3?' …':'')+'</div></div>'
        +'<button class="f-btn fh-cta" onclick="window.funiSetFilter(\'runs\')">Best runs <span class="fh-cta-arw">→</span></button></div>');
    }
    var show=function(k){ return F==='all'||F===k; };
    if(show('runs')&&s.runs.length){
      H.push('<div class="forge-sec forge-sec-pipe"><div class="forge-sec-h">🎯 Best runs <span class="forge-sec-ct">'+s.runs.length+'</span><span class="forge-sec-sub">each run ranked by how many missing uniques it can drop</span></div>');
      H.push(_moreWrap(s.runs.map(function(r,i){ return _runCard(r,i); }), F==='runs'?12:6, 'runs'));   // v647
      H.push('</div>');
    }
    // v619 — 🏆 SEALED GROUNDS: runs whose ENTIRE verified pool is found wear the horizontal seal band
    // (the vault's trade-keeper language) — farm these for trade/friends only, never for your grail.
    if(show('runs')&&(s.sealed||[]).length){
      H.push('<div class="forge-sec forge-sec-done"><div class="forge-sec-h">🏆 Sealed grounds <span class="forge-sec-ct">'+s.sealed.length+'</span><span class="forge-sec-sub">every verified unique from these runs is FOUND — nothing left here for your grail</span></div>');
      H.push(_moreWrap(s.sealed.map(function(g){
        return '<div class="rw-stamp-mini rw-band" style="margin:6px 0"><span class="rw-band-t">✓ '+esc(g.boss)+' — grounds sealed</span><span class="rw-band-s">all '+g.total+' verified uniques found · runs here are trade loot now</span></div>';
      }), 6, 'sealed grounds'));   // v647

      H.push('</div>');
    }
    if(F==='runs'&&!s.runs.length&&!(s.sealed||[]).length){
      H.push('<div class="forge-empty forge-empty-sm">Nothing in this bucket right now — no missing unique maps to a ranked run. Tap <b>▦ All</b> for the full missing grid, or <b>⚡ Quick wins</b> for the fastest crosses.</div>');   // v681 — same 0-count fall-through class as the v678 quick-wins fix
    }
    if(show('low')&&!s.low.length&&s.lowTotal>0){
      // v619 — every quick-win (qlvl ≤35, the Normal/Nightmare hunts) found → the seal, not an empty tab
      H.push('<div class="forge-sec forge-sec-done"><div class="rw-stamp-mini rw-band" style="margin:6px 0"><span class="rw-band-t">✓ quick wins complete</span><span class="rw-band-s">all '+s.lowTotal+' low-level (qlvl ≤35) uniques found — the early game is sealed</span></div></div>');
    }
    if(show('low')&&s.low.length){
      H.push('<div class="forge-sec forge-sec-step"><div class="forge-sec-h">⚡ Quick wins <span class="forge-sec-ct">'+s.low.length+'</span><span class="forge-sec-sub">qlvl ≤ 35 — the early uniques skipped on the way to Hell, fastest to cross off</span></div>');
      H.push(_moreWrap(s.low.map(function(x){ return _uniItemCard(x); }), F==='low'?12:6, 'quick wins'));   // v647 — ALL of them, drawer-tailed
      H.push('</div>');
    }
    if(F==='found'){
      H.push('<div class="forge-sec forge-sec-now"><div class="forge-sec-h">✅ Found <span class="forge-sec-ct">'+s.found+'</span><span class="forge-sec-sub">the grail ledger — dated, newest first, synced with the Calculator ✓ — tap to un-mark</span></div><div class="gf-chips">');
      var own=_ownedNames();
      var _flU=_flog(); var _ownF=_ownedNames();
      _flogSort(_uniItems().filter(function(x){return _ownF.has(x.n);}).map(function(x){return x.n;})).forEach(function(n){
        H.push('<span class="gf-piece have" data-arttip="'+esc(n)+'" onclick="window.grailFoundUni(this,\''+jsq(n)+'\')"><span class="gp-ck">✓</span>'+chipLogo(n)+esc(n)+(_flU[n]?'<span class="gp-date">'+esc(_flU[n])+'</span>':'')+'</span>');
      });
      H.push('</div></div>');
      if(!s.found) H.push('<div class="forge-empty">Nothing marked found yet — tick uniques here or in the Calculator (they sync).</div>');
    }
    box.innerHTML=H.join('');
  };

  

  function _setHave(){ try { return new Set(JSON.parse(window.LSR.getItem('d2r_setPieces')||'[]')); } catch(e){ return new Set(); } }
  window.fsetsScan=function(){
    var have=_setHave(); var sets=(typeof window.__allSets==='function')?window.__allSets():[];
    var totalP=0, haveP=0;
    var rows=sets.map(function(st){
      var pieces=(st.pieces||[]).map(function(pn){ return { name:pn, have:have.has(pn) }; });
      totalP+=pieces.length; var got=pieces.filter(function(p){return p.have;}).length; haveP+=got;
      return { name:st.name, pieces:pieces, got:got, left:pieces.length-got };
    });
    return { totalPieces:totalP, havePieces:haveP, sets:rows,
      oneAway:rows.filter(function(r){return r.left===1;}),
      working:rows.filter(function(r){return r.left>0;}).sort(function(a,b){ return a.left-b.left || b.pieces.length-a.pieces.length; }),
      done:rows.filter(function(r){return r.left===0;}) };
  };
  // v560 — a set's farm source comes from its AGGREGATE entry in ITEMS (tier 'set'), stem-matched by name.
  function _setAggSrc(setName){
    try {
      var stem=String(setName).replace(/\s*\((set|Sorc|Necro|Barb|Ama|Sin|Pala|Druid)\)\s*$/i,'').trim().toLowerCase();
      var L=(typeof ITEMS!=='undefined')?ITEMS:(window.ITEMS||[]);
      var agg=L.find(function(x){ return x.tier==='set' && String(x.n).toLowerCase().indexOf(stem.slice(0,12))===0; });
      if(!agg) return null;
      var best=null,bestR=-1; (agg.sources||[]).forEach(function(src){ if(!src||src.blocked||src.chance==null) return; var r=(src.kph||30)/src.chance; if(r>bestR){bestR=r;best=src;} });
      return best;
    } catch(e){ return null; }
  }
  var _fsF='all';
  window.fsetsSetFilter=function(f){ _fsF=(_fsF===f&&f!=='all')?'all':f; window.renderForgeSets(); };
  window.grailTogglePiece=function(el,piece){
    var wasHave=_setHave().has(piece);
    try { if(typeof window.toggleSetPiece==='function') window.toggleSetPiece(piece); } catch(e){}
    if(!wasHave){
      // did this COMPLETE a set? celebrate accordingly
      var s=window.fsetsScan(); var doneSet=s.done.find(function(r){ return r.pieces.some(function(p){return p.name===piece;}); });
      if(doneSet) _grailToast('🧩','<b>'+esc(doneSet.name)+'</b> COMPLETE!','full set assembled');
      else _grailToast('🧩','<b>'+esc(piece)+'</b> found!','the set grail grows');
    }
    window.renderForgeSets();
  };
  function _setArt(name, pieces){
    try { var rep=(typeof window._setRepArtName==='function')?window._setRepArtName(name):''; if(rep){ var u=(typeof artUrl==='function')?artUrl(rep):''; if(u) return '<img class="f-art" src="'+esc(u)+'" alt="" loading="lazy">'; } } catch(e){}
    // v560 — HD fallback: the first PIECE's art (piece names resolve art even when the set aggregate doesn't)
    try { var ps=pieces||[]; for(var i=0;i<ps.length;i++){ var pn=String(ps[i].name||ps[i]).replace(/\s*\([^)]+\)\s*$/,''); var pu=(typeof artUrl==='function')?artUrl(pn):''; if(pu) return '<img class="f-art" src="'+esc(pu)+'" alt="" loading="lazy">'; } } catch(e){}
    return '<span class="f-glyph">🧩</span>';
  }
  function _pieceChip(p){
    var nm=p.name, clean=nm.replace(/\s*\(([^)]+)\)\s*$/,''), slot=(nm.match(/\(([^)]+)\)\s*$/)||[])[1]||'';
    return '<span class="gf-piece'+(p.have?' have':'')+'" data-arttip="'+esc(clean)+'" onclick="window.grailTogglePiece(this,\''+jsq(nm)+'\')" title="'+(p.have?'un-mark':'mark found')+'"><span class="gp-ck">'+(p.have?'✓':'○')+'</span>'+chipLogo(clean)+esc(clean)+(slot?'<span class="gq">'+esc(slot)+'</span>':'')+'</span>';
  }
  function _setCard(r,cls){
    var pct=r.pieces.length?Math.round(r.got/r.pieces.length*100):0;
    return '<div class="f-card '+cls+'"><div class="f-cardart f-cardart-hd">'+_setArt(r.name,r.pieces)+'<span class="f-cardart-badge">'+(r.left===0?'✅':r.left)+'</span></div><div class="f-cardbody">'
      +'<div class="f-cardtitle"><div class="f-atomact"><b class="f-rwbig">'+esc(r.name)+'</b> <span class="f-need">'+r.got+' / '+r.pieces.length+'</span>'+(r.left===1?' <span class="f-ideal">1 piece left!</span>':'')+'</div>'
      +'<div class="gf-setbar"><i style="width:'+pct+'%"></i></div>'
      +'<div class="gf-chips">'+r.pieces.map(_pieceChip).join('')+'</div></div></div></div>';
  }
  window.renderForgeSets=function(){
    var box=document.getElementById('fsets-body'); if(!box) return;
    var s=window.fsetsScan(); var F=_fsF; var H=[];
    H.push(_undoBar('set'));   // v644 — mis-ticks are one ↩ away, forge-style
    // v560.1 — Konyo: "I already have item trackers — F·Sets should be the F·Uniques coding logic." So this is
    // PIECE-centric, identical to Forge·Uniques: every missing PIECE is a farm item (Find → best run → ✓ found),
    // the tally syncs silently to the Item Set Tracker (d2r_setPieces), and the checklist wall stays in Tools.
    var missingP=[];
    s.sets.forEach(function(r){ var src=_setAggSrc(r.name);
      r.pieces.forEach(function(p){ if(!p.have) missingP.push({ name:p.name, set:r.name, left:r.left, src:src }); }); });
    var pct=s.totalPieces?Math.round(s.havePieces/s.totalPieces*100):0;
    H.push('<div class="forge-progress" title="'+s.havePieces+' of '+s.totalPieces+' pieces"><div class="fp-track"><div class="fp-fill" style="width:'+pct+'%;background:linear-gradient(90deg,#4ade80,#86efac)"></div></div>'
      +'<div class="fp-lbl">🧩 <b>'+s.havePieces+'</b> / '+s.totalPieces+' pieces · <b>'+s.done.length+'</b> / '+s.sets.length+' sets<span class="fp-pct">'+pct+'%</span></div></div>');
    // group missing pieces by best run (same shape as Forge·Uniques)
    var bySrc={};
    missingP.forEach(function(mp){ var key=mp.src?mp.src.boss:'Drops broadly — no single best run';
      var g=(bySrc[key]=bySrc[key]||{boss:key,bossId:mp.src&&mp.src.bossId,items:[],ev:0}); g.items.push(mp); if(mp.src)g.ev+=(mp.src.kph||30)/mp.src.chance; });
    var runs=Object.keys(bySrc).map(function(k){return bySrc[k];}).sort(function(a,b){return b.ev-a.ev||b.items.length-a.items.length;});
    var quick=missingP.filter(function(mp){return mp.left===1;}).sort(function(a,b){return String(a.set).localeCompare(String(b.set));});
    // UNIFIED tiles — identical names to Forge·Uniques
    H.push('<div class="forge-tabs">'
      +_tile('all','▦','All missing','ft-all',missingP.length,F,'window.fsetsSetFilter')
      +_tile('runs','🎯','Best runs','ft-pipe',runs.length,F,'window.fsetsSetFilter')
      +_tile('near','⚡','Quick wins','ft-step',quick.length,F,'window.fsetsSetFilter')
      +_tile('done','✅','Found','ft-done',s.havePieces,F,'window.fsetsSetFilter')
      +'</div>');

    // v646 — THE GRAIL WALL: identical drawer, identical position on BOTH grail forges
    if(F==='all'){
      var _missP=[];
      (s.sets||[]).forEach(function(st){ (st.pieces||[]).forEach(function(pp){ if(!pp.have){ var _cl=pp.name.replace(/\s*\(([^)]+)\)\s*$/,''); var _sl=(pp.name.match(/\(([^)]+)\)\s*$/)||[])[1]||''; _missP.push({ n:_cl, key:pp.name, tip:_cl, badge:_sl }); } }); });
      _missP.sort(function(a,b){ return a.n.localeCompare(b.n); });
      H.push(_allGrid('Every missing piece — tick as you find', 'all '+_missP.length+' missing set pieces · ✓ tallies the Set Tracker + meters instantly', _missP, 'grailTogglePiece'));
    }

    // v619 — ⚔ COMPLETED SETS wear the horizontal seal (the platform's done-forever language): a full
    // set means its pieces stop being farm targets everywhere — the run lists above already exclude
    // them (piece-centric missing scan), the seal makes the achievement readable.
    if((F==='all'||F==='done')&&(s.done||[]).length){
      H.push('<div class="forge-sec forge-sec-done"><div class="forge-sec-h">⚔ Completed sets <span class="forge-sec-ct">'+s.done.length+'</span><span class="forge-sec-sub">every piece found — these no longer appear in any farm list</span></div>');
      H.push(_moreWrap(s.done.map(function(r){
        return '<div class="rw-stamp-mini rw-band" style="margin:6px 0"><span class="rw-band-t">✓ '+esc(r.name.replace(/\s*\(set\)$/i,''))+' — set complete</span><span class="rw-band-s">all '+r.pieces.length+' pieces found · spares are trade loot</span></div>';
      }), F==='done'?12:5, 'complete sets'));   // v647
      H.push('</div>');
    }
    // HERO — a quick-win piece if one exists, else the top run (same priority spirit as uniques)
    if(F!=='done'){
      if(quick.length){
        var q0=quick[0], qClean=q0.name.replace(/\s*\([^)]+\)\s*$/,'');
        H.push('<div class="forge-hero forge-hero-step"><span class="fh-ember"></span><span class="fh-ember"></span><span class="fh-ember"></span><span class="fh-ember"></span>'
          +'<div class="fh-artwrap"><div class="fh-art">'+art(qClean,'🧩')+'</div><div class="fh-icobadge">⚡</div></div>'
          +'<div class="fh-main"><div class="fh-lead">👉 DO THIS ONE THING · quick win</div><div class="fh-name">'+esc(qClean)+'</div>'
          +'<div class="fh-body">the LAST piece of <b>'+esc(q0.set.replace(/\s*\(set\)$/,''))+'</b>'+(q0.src?' · best run: <b>'+esc(q0.src.boss)+'</b> <span class="gf-odds">'+fmtOdds(q0.src.chance)+'</span>':'')+'</div></div>'
          +'<button class="f-btn fh-cta" onclick="window.fsetsSetFilter(\'near\')">Quick wins <span class="fh-cta-arw">→</span></button></div>');
      } else if(runs.length){
        var t0=runs[0], tClean=(t0.items[0]?t0.items[0].name:'').replace(/\s*\([^)]+\)\s*$/,'');
        H.push('<div class="forge-hero forge-hero-pipe"><span class="fh-ember"></span><span class="fh-ember"></span><span class="fh-ember"></span><span class="fh-ember"></span>'
          +'<div class="fh-artwrap"><div class="fh-art">'+art(tClean,'🎯')+'</div><div class="fh-icobadge">🎯</div></div>'
          +'<div class="fh-main"><div class="fh-lead">👉 DO THIS ONE THING · best farm</div><div class="fh-name">'+esc(t0.boss)+'</div>'
          +'<div class="fh-body">drops <b>'+t0.items.length+'</b> of your missing set pieces</div></div>'
          +'<button class="f-btn fh-cta" onclick="window.fsetsSetFilter(\'runs\')">Best runs <span class="fh-cta-arw">→</span></button></div>');
      }
    }
    var show=function(k){ return F==='all'||F===k; };
    // BEST RUNS — run cards listing the missing pieces they can drop (chips tick on click)
    if(show('runs')&&runs.length){
      H.push('<div class="forge-sec forge-sec-pipe"><div class="forge-sec-h">🎯 Best runs <span class="forge-sec-ct">'+runs.length+'</span><span class="forge-sec-sub">where your missing set pieces actually drop</span></div>');
      var _rCards=runs.map(function(g,i){
        var chips=g.items.slice(0,12).map(function(mp){ return _pieceChip({name:mp.name,have:false}); }).join('');
        var more=g.items.length>12?'<span class="gf-note">+ '+(g.items.length-12)+' more pieces</span>':'';
        var bossBtn=g.bossId?'<div class="f-cta"><button class="f-btn" onclick="window.openBossDetail&&window.openBossDetail(\''+jsq(g.bossId)+'\')">📜 boss card</button></div>':'';
        return ('<div class="f-card f-pipe"><div class="f-cardart f-cardart-hd">'+art((g.items[0]?g.items[0].name:'').replace(/\s*\([^)]+\)\s*$/,''),'🎯')+'<span class="f-cardart-badge">'+(i+1)+'</span></div><div class="f-cardbody">'
          +'<div class="f-cardtitle"><div class="f-atomact">Run <b class="f-rwbig">'+esc(g.boss)+'</b></div>'
          +'<div class="f-atomsubrow">can drop <b>'+g.items.length+'</b> of your missing pieces — tap a piece the moment it drops</div>'
          +'<div class="gf-chips">'+chips+more+'</div></div>'+bossBtn+'</div></div>');
      });
      H.push(_moreWrap(_rCards, F==='runs'?12:6, 'runs'));   // v647

      H.push('</div>');
    }
    if(F==='runs'&&!runs.length){
      H.push('<div class="forge-empty forge-empty-sm">Nothing in this bucket right now — no missing set piece maps to a ranked run. Tap <b>▦ All</b> for every missing piece, or <b>⚡ Quick wins</b> for the one-piece finishes.</div>');   // v681 — same 0-count fall-through class as the v678 quick-wins fix
    }
    // QUICK WINS — piece cards, F·Uniques style ("Find X → ✓ found it")
    if(show('near')&&quick.length){
      H.push('<div class="forge-sec forge-sec-step"><div class="forge-sec-h">⚡ Quick wins <span class="forge-sec-ct">'+quick.length+'</span><span class="forge-sec-sub">one piece finishes the whole set</span></div>');
      var _qCards=[];
      quick.slice(0,99999).forEach(function(mp){
        var clean=mp.name.replace(/\s*\(([^)]+)\)\s*$/,''), slot=(mp.name.match(/\(([^)]+)\)\s*$/)||[])[1]||'';
        var src=mp.src?('<div class="gf-src">📍 best run: <b>'+esc(mp.src.boss)+'</b> <span class="gf-odds">'+fmtOdds(mp.src.chance)+'</span></div>'):'<div class="gf-note">drops broadly — any high-MF run</div>';
        _qCards.push('<div class="f-card f-step f-atom"><div class="f-cardart f-cardart-hd">'+art(clean,'🧩')+'<span class="f-cardart-badge">⚡</span></div><div class="f-cardbody">'
          +'<div class="f-cardtitle"><div class="f-atomact">Find <b class="f-rwbig" data-arttip="'+esc(clean)+'">'+esc(clean)+'</b>'+(slot?' <span class="f-need">'+esc(slot)+'</span>':'')+'</div>'
          +'<div class="f-atomsubrow">completes <b>'+esc(mp.set.replace(/\s*\(set\)$/,''))+'</b></div>'+src+'</div>'
          +'<div class="f-cta"><button class="f-btn f-btn-go" onclick="window.grailTogglePiece(this,\''+jsq(mp.name)+'\')">✓ found it</button></div></div></div>');
      });
      H.push(_moreWrap(_qCards, F==='near'?12:6, 'quick wins'));   // v647
      H.push('</div>');
    }
    if(F==='near'&&!quick.length){
      H.push('<div class="forge-empty forge-empty-sm">Nothing in this bucket right now — no set is 1 piece away yet. Tap <b>▦ All</b> for every missing piece, or <b>🎯 Best runs</b> to farm toward one.</div>');   // v678 (swarm) — the 0-count filter fell through to a blank page
    }
    // FOUND — green chips (tap to un-mark), synced to the Item Set Tracker
    if(F==='done'){
      H.push('<div class="forge-sec forge-sec-now"><div class="forge-sec-h">✅ Found <span class="forge-sec-ct">'+s.havePieces+'</span><span class="forge-sec-sub">synced with the Item Set Tracker — tap to un-mark</span></div><div class="gf-chips">');
      s.sets.forEach(function(r){ r.pieces.forEach(function(pp){ if(pp.have) H.push(_pieceChip(pp)); }); });
      H.push('</div></div>');
      if(!s.havePieces) H.push('<div class="forge-empty">Nothing marked found yet — tick pieces here or in the Item Set Tracker (they sync).</div>');
    }
    if(F==='all') H.push('<div class="forge-note">full per-set checklists live in 🧰 Tools → Item Set Tracker (same tally, always in sync)</div>');
    box.innerHTML=H.join('');
  };

  

  function _gDownscale(file){
    return new Promise(function(resolve,reject){
      var img=new Image(), url=URL.createObjectURL(file);
      img.onload=function(){ var MAX=1568, sc=Math.min(1,MAX/Math.max(img.width,img.height));
        var c=document.createElement('canvas'); c.width=Math.round(img.width*sc); c.height=Math.round(img.height*sc);
        c.getContext('2d').drawImage(img,0,0,c.width,c.height); URL.revokeObjectURL(url);
        resolve(c.toDataURL('image/jpeg',0.85).split(',')[1]); };
      img.onerror=reject; img.src=url;
    });
  }
  function _grailVocab(){
    var uniq=_uniItems().map(function(x){return x.n;});
    var pieceMap={};   // clean name → full "(slot)" piece name
    ((typeof window.__allSets==='function')?window.__allSets():[]).forEach(function(st){ (st.pieces||[]).forEach(function(pn){ pieceMap[String(pn).replace(/\s*\([^)]+\)\s*$/,'')]=pn; }); });
    return { vocab: uniq.concat(Object.keys(pieceMap)), uniq:new Set(uniq), pieceMap:pieceMap };
  }
  window.grailIntake=async function(files){
    if(!files||!files.length) return;
    var rep=document.getElementById('grail-intake-report');
    var show=function(html){ if(rep){ rep.style.display='block'; rep.innerHTML=html; } };
    var endpoint=localStorage.getItem('d2r_intakeUrl')||(location.protocol==='file:'?'https://bull-4-u.com/api/intake':'/api/intake');
    var V=_grailVocab(); var found=new Set(); var unknown=new Set(); var errs=0;
    for(var i=0;i<files.length;i++){
      show('📸 reading grail screenshot <b>'+(i+1)+' / '+files.length+'</b>… ('+found.size+' found so far)');
      try {
        var b64=await _gDownscale(files[i]);
        var resp=await fetch(endpoint,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({image:b64,media_type:'image/jpeg',kind:'grail',names:V.vocab})});
        var d=await resp.json();
        (d&&d.items||[]).forEach(function(n){ found.add(n); });
        (d&&d.unrecognized||[]).forEach(function(n){ unknown.add(n); });
      } catch(e){ errs++; }
    }
    if(!found.size){ show('😕 no FOUND items could be read'+(errs?' ('+errs+' image error'+(errs>1?'s':'')+')':'')+' — make sure the names + found-marks are legible and try again.'); return; }
    // batch-apply straight to the shared stores, then reload so every view (Calculator, Vault, Set Tracker,
    // both grail forges, AI snapshot) rebuilds from the same state — the one-time import path.
    var owned=[]; try{ owned=JSON.parse(window.LSR.getItem('d2r_owned')||'[]'); }catch(e){}
    var setP=[]; try{ setP=JSON.parse(window.LSR.getItem('d2r_setPieces')||'[]'); }catch(e){}
    var oSet=new Set(owned), pSet=new Set(setP), addU=0, addP=0;
    var flI={}; try{ flI=JSON.parse(window.LSR.getItem('d2r_foundLog')||'{}'); }catch(e){}
    found.forEach(function(n){
      if(V.uniq.has(n)){ if(!flI[n] && !oSet.has(n)){ flI[n]=(window._grailStamp?window._grailStamp():'')+' · imported'; addU++; } }   // v677 — imports land in the LEDGER, not the vault
      else if(V.pieceMap[n]){ if(!pSet.has(V.pieceMap[n])){ pSet.add(V.pieceMap[n]); addP++; } if(!flI[V.pieceMap[n]]){ flI[V.pieceMap[n]]=(window._grailStamp?window._grailStamp():'')+' · imported'; } }   // v684 — set pieces chronicle into the ledger like uniques (they silently skipped it)
      else unknown.add(n);
    });
    try {
      window.LSR.setItem('d2r_foundLog', JSON.stringify(flI));
      window.LSR.setItem('d2r_setPieces', JSON.stringify(Array.from(pSet)));
      window.LSR.setItem('d2r_grailImportReport', JSON.stringify({u:addU,p:addP,unk:Array.from(unknown).slice(0,20),t:Date.now()}));
    } catch(e){}
    show('✅ imported — reloading to sync every view…');
    setTimeout(function(){ location.reload(); },600);
  };
  function _grailImportToastOnce(){
    var raw=null; try{ raw=window.LSR.getItem('d2r_grailImportReport'); }catch(e){}
    if(!raw) return;
    try{ window.LSR.removeItem('d2r_grailImportReport'); }catch(e){}
    try {
      var r=JSON.parse(raw);
      var t=document.createElement('div'); t.className='forge-toast';
      t.innerHTML='📸 <b>Grail imported!</b> +'+r.u+' uniques · +'+r.p+' set pieces'+(r.unk&&r.unk.length?' <span class="ft-sub">'+r.unk.length+' unrecognized</span>':'')+' <span class="ft-sub">synced everywhere</span>';
      (function(el){var st=document.getElementById('forge-toasts');if(!st){st=document.createElement('div');st.id='forge-toasts';document.body.appendChild(st);}st.appendChild(el);})(t); setTimeout(function(){ t.classList.add('out'); setTimeout(function(){ t.remove(); },450); },5200);
      var rep=document.getElementById('grail-intake-report');
      if(rep&&r.unk&&r.unk.length){ rep.style.display='block'; rep.innerHTML='📸 import note — unrecognized names (check spelling/mod items): '+r.unk.map(function(n){return '<b>'+esc(n)+'</b>';}).join(', '); }
    } catch(e){}
  }
  try { if(document.readyState!=='loading') setTimeout(_grailImportToastOnce,900); else document.addEventListener('DOMContentLoaded',function(){ setTimeout(_grailImportToastOnce,900); }); } catch(e){}

  

  var _origSwitch=window.switchTab;
  window.switchTab=function(name){
    var r=_origSwitch.apply(this,arguments);
    try { if(name==='funi') window.renderForgeUni(); if(name==='fsets') window.renderForgeSets(); } catch(e){}
    return r;
  };
})();
