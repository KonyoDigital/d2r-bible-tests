

(function(){
  function _fEsc(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function _fJs(s){ return String(s==null?'':s).replace(/\\/g,'\\\\').replace(/'/g,"\\'"); }
  function _fArt(n){ try { return (typeof artUrl==='function') ? (artUrl(n)||'') : ''; } catch(e){ return ''; } }
  function _has(g){ try { return typeof window[g]!=='undefined'; } catch(e){ return false; } }
  // v518 — in-game RARITY colour for any item reference (the SINGLE source of truth, _qHex):
  // runeword → orange · white base → white · unique gold · set green · magic blue. Konyo: "synced
  // ingame for each individual item reference" — so every forge card title / base chip uses it.
  function _qC(n){ try { return (typeof _qHex==='function') ? (_qHex(n)||'') : ''; } catch(e){ return ''; } }
  function _qName(n){ var c=_qC(n); return c ? '<span style="color:'+c+'">'+_fEsc(n)+'</span>' : _fEsc(n); }
  // v550 — name + INLINE HD art logo + floating HD-art hover tooltip (data-arttip), so every runeword & base name
  // in the Forge shows exactly what to hunt for in-game. Konyo: "so I know what I'm searching for and how it looks
  // exactly — it helps accuracy." Reuses the app-wide nameLogo() + #arttip system already active everywhere.
  function _qArt(n){
    if (!n) return '';
    var c=_qC(n), logo='';
    try { if (typeof window.nameLogo==='function') logo=window.nameLogo(n); } catch(e){}
    var body = c ? '<span style="color:'+c+'">'+_fEsc(n)+'</span>' : _fEsc(n);
    return '<span class="f-artname" data-arttip="'+_fEsc(n)+'" style="cursor:help">'+logo+body+'</span>';
  }
  // art-ify a "A / B / C" base list (the 🏆 best-base hints) — each base gets its own logo + hover art
  function _qArtList(s){ return String(s||'').split(/\s*\/\s*/).map(function(b){ b=b.trim(); return b?_qArt(b):''; }).filter(Boolean).join(' <span style="opacity:.5">/</span> '); }
  // v519 — role badges on a base option (Konyo: "say what's ideal, what's MERCenary gear, what's end-game"):
  //   ★ ideal (the top recommended pick) · 1H = your player weapon · merc = a 2H polearm/spear/bow (merc gear)
  //   · caster = staff · ◆ endgame = elite-tier base (found as a white drop, NOT upgraded to). From _baseHandClass + BASE_DB tier.
  function _baseRoleBadge(base, isFirst){
    var t=[]; var hc=(typeof _baseHandClass==='function')?_baseHandClass(base):'?';
    var tier=(typeof BASE_DB!=='undefined'&&BASE_DB[base])?BASE_DB[base].tier:'';
    if (isFirst) t.push('<span class="f-rb f-rb-ideal" title="the recommended base — grab this one">★ ideal</span>');
    if (hc==='1H') t.push('<span class="f-rb f-rb-1h" title="one-handed — YOUR player weapon">1H</span>');
    else if (hc==='merc') t.push('<span class="f-rb f-rb-merc" title="two-handed polearm/spear/bow — MERCENARY gear">merc</span>');
    else if (hc==='caster') t.push('<span class="f-rb f-rb-cast" title="staff — a caster two-hander">caster</span>');
    else if (hc==='2H') t.push('<span class="f-rb f-rb-2h" title="two-handed weapon">2H</span>');
    if (tier==='elite') t.push('<span class="f-rb f-rb-end" title="elite tier — best-stat endgame base (find it as a white drop; you don’t upgrade to it)">◆ endgame</span>');
    else if (tier==='exceptional') t.push('<span class="f-rb f-rb-exc" title="exceptional tier — for a higher-socket word, find the elite version (white bases can’t be cube-upgraded)">exc</span>');
    return t.length?'<span class="f-rbwrap">'+t.join('')+'</span>':'';
  }

  // ---- best-base reverse index (built once from RW_BASES) ----
  var _FORGE_BEST = (function(){
    var m = {};
    try {
      (typeof RW_BASES!=='undefined'?RW_BASES:[]).forEach(function(grp){
        var slot = String(grp.slot||'').replace(/^[^A-Za-z]+/,'').trim();
        (grp.items||[]).forEach(function(it){
          var bases = String(it.n).split(/\s*[\/·]\s*/).map(function(s){return s.trim();}).filter(Boolean);
          String(it.rw||'').split('·').forEach(function(rw){
            var name = rw.trim(); if (!name) return;
            var rec = { bases:bases, meta:it.meta||'', slot:slot };
            (m[name]=m[name]||[]).push(rec);
            var nk = name.replace(/['’]/g,''); if (nk!==name) (m[nk]=m[nk]||[]).push(rec);
          });
        });
      });
    } catch(e){}
    return m;
  })();
  function _bestFor(rw){ return _FORGE_BEST[rw] || _FORGE_BEST[String(rw||'').replace(/['’]/g,'')] || []; }
  // ── KONYO'S RULE: meta bases are 1-HANDED for the player's own weapons; 2-HANDED only for MERCENARY
  // weapons (Act-2 polearms/spears, Act-1 bows/xbows). No 2H player-weapon recommendations. Plus a TYPE-MATCH
  // safeguard so an armour/shield/helm word can NEVER recommend a weapon base (kills the Chains-of-Honor →
  // Colossus-Blade bug structurally). _baseCats backs the safeguard; a simulate test enforces it across all 100.
  var _BEST_1H=[
    {re:/\bsword|\bblade/,        base:'Phase Blade',   note:'1-handed · indestructible — your weapon'},
    {re:/\baxe/,                  base:'Berserker Axe', note:'1-handed · fastest elite axe — your weapon'},
    {re:/scepter|sceptre/,        base:'Caduceus',      note:'1-handed scepter — your weapon'},
    {re:/mace|hammer|club|flail/, base:'Flail',         note:'1-handed mace — your weapon'},
    {re:/dagger|knife/,           base:'Fanged Knife',  note:'1-handed dagger — your weapon'},
    {re:/katar|claw/,             base:'Runic Talons',  note:'1-handed claw — assassin'}
  ];
  var _MERC_BASE=[
    {re:/polearm/,       names:['Cryptic Axe','Thresher','Colossus Voulge'], note:'2-handed polearm — Act 2 mercenary'},
    {re:/spear/,         names:['War Pike','Ghost Spear'],                    note:'2-handed spear — mercenary'},
    {re:/crossbow/,      names:['Colossus Crossbow'],                         note:'2-handed crossbow — Act 1 mercenary'},
    {re:/\bbow|missile/, names:['Matriarchal Bow','Grand Matron Bow'],        note:'2-handed bow — Act 1 (Rogue) mercenary'}
  ];
  // v479 — SOCKET-CORRECT elite base, data-driven from BASE_DB: an ELITE base of the right hand-class whose
  // maxSockets === the runeword's socket count (so Larzuk gives EXACTLY the needed count — clean, no gamble),
  // lowest str = the meta/easiest pick. This is why Hand of Justice (4os) → Cryptic Sword (4os 1H), NOT the
  // 6os Phase Blade. Returns null when no clean-max elite exists (caller falls back to the popular base).
  function _eliteBaseFor(rw){
    if (typeof BASE_DB==='undefined') return null;
    var e=(typeof RUNEWORD_TIP!=='undefined'?RUNEWORD_TIP[rw]:null)||{}; var b=String(e.b||'').toLowerCase();
    var need=(Array.isArray(e.rec)?e.rec.length:0); if(!need) return null;
    var bw=b.replace(/missile weapons?/g,' missilew ').replace(/melee weapons?/g,' meleew ');
    var has1H=/\bsword|\bblade|\baxe|scepter|sceptre|mace|hammer|club|flail|dagger|knife|katar|claw|wand|\borb/.test(b);
    var generic=/\bweapon|meleew/.test(bw);
    var mercOnly=!has1H && !generic && /polearm|spear|missilew|\bbow|crossbow|javelin/.test(bw);
    var isCaster=!has1H && !generic && !mercOnly && /staff|stave/.test(b);   // a staff-only word = a 2-handed CASTER weapon (player-held, not a merc/1H)
    var cats=[];
    if(/\bsword|\bblade/.test(b))cats.push('sword'); if(/\baxe/.test(b))cats.push('axe');
    if(/scepter|sceptre/.test(b))cats.push('scepter'); if(/mace|hammer|club|flail/.test(b))cats.push('mace');
    if(/dagger|knife/.test(b))cats.push('dagger'); if(/katar|claw/.test(b))cats.push('katar'); if(/wand/.test(b))cats.push('wand'); if(/orb/.test(b))cats.push('orb');
    if(/polearm/.test(b))cats.push('polearm'); if(/spear/.test(b))cats.push('spear');
    if(/missile|\bbow|crossbow/.test(b))cats.push('missile weapon'); if(/staff|stave/.test(b))cats.push('staff');
    if(generic && !cats.length) cats=['sword','axe','mace'];
    if(mercOnly){ cats=cats.filter(function(k){return k!=='staff';});   // a merc holds the 2H weapon, not a caster staff
      if(cats.indexOf('polearm')>=0||cats.indexOf('spear')>=0) cats=cats.filter(function(k){return k!=='missile weapon';});  // prefer the Act-2 polearm/spear over a bow when a word allows both (Insight = merc polearm, not a bow)
      if(!cats.length) cats=['polearm']; }
    if(!cats.length) return null;
    var hits=[];
    for(var nm in BASE_DB){ if(!Object.prototype.hasOwnProperty.call(BASE_DB,nm)) continue;
      var d=BASE_DB[nm]; if(d.tier!=='elite'||d.maxSockets!==need) continue;
      var c=(typeof _baseCats==='function')?_baseCats(nm):{}; if(!cats.some(function(k){return c[k];})) continue;
      if(!mercOnly && !isCaster && (!d.oneH || d.twoH)) continue;     // player 1H word → PURE 1-handed only (exclude either-hand 2H like Zweihander); caster words allow 2H staves
      hits.push({name:nm, str:d.reqStr||0});
    }
    if(!hits.length) return null;
    hits.sort(function(a,c){ return a.str-c.str; });   // lowest str = the meta / easiest base
    return { names:hits.slice(0,3).map(function(h){return h.name;}), merc:mercOnly, hand:mercOnly?'2H merc':(isCaster?'2H caster':'1H'), need:need };
  }
  try { window._eliteBaseFor=_eliteBaseFor; } catch(e){}
  // v583 — THE BiS-HOME LAYER (Konyo: "the goal isn't just to make a runeword — these should be in their
  // Elite Item End Game gear"). Curated community-standard homes per word. The overlay PREPENDS these to the
  // engine's socket-correct names, so every consumer — the v576 endgame gate (_isIdealBase), best-base hints,
  // the loot filter's farm list, the spare logic, keep-reasons — inherits the true meta home automatically.
  var RW_BIS = {
    'Call to Arms':        { b:['Crystal Sword','Flail'],                n:'the classic switch stick — lightest 5os 1H' },
    'Heart of the Oak':    { b:['Flail'],                                n:'THE 4os caster mace' },
    'Grief':               { b:['Phase Blade','Berserker Axe'],          n:'PB never repairs · BA fastest axe' },
    'Breath of the Dying': { b:['Colossus Blade','Berserker Axe','Giant Thresher','War Pike'], n:'player CB/BA · merc GT/WP — eth is a bonus, never required' },
    'Death':               { b:['Colossus Blade','Ettin Axe'],           n:'eth Ettin Axe is the budget king' },
    'Oath':                { b:['Balrog Blade','Colossus Blade'],        n:'ethereal — Oath self-repairs' },
    'Silence':             { b:['Phase Blade','Berserker Axe'],          n:'' },
    'Kingslayer':          { b:['Phase Blade','Berserker Axe'],          n:'' },
    'Hand of Justice':     { b:['Phase Blade','Berserker Axe'],          n:'' },
    'Eternity':            { b:['Berserker Axe','Ettin Axe'],            n:'' },
    'Famine':              { b:['Berserker Axe'],                        n:'' },
    'Destruction':         { b:['Berserker Axe','Cryptic Axe'],          n:'' },
    'Doom':                { b:['Berserker Axe','Cryptic Axe'],          n:'eth Cryptic Axe for the merc' },
    'Voice of Reason':     { b:['Crystal Sword','Phase Blade'],          n:'' },
    'Unbending Will':      { b:['Phase Blade','Colossus Blade'],         n:'PB = the only true-1H 6os sword · barbs one-hand a CB' },
    'Infinity':            { b:['Cryptic Axe','Thresher','Giant Thresher'], n:'ETHEREAL merc polearm' },
    'Insight':             { b:['Colossus Voulge','Thresher'],           n:'merc polearm' },
    'Pride':               { b:['War Pike','Thresher'],                  n:'ETHEREAL merc polearm' },
    'Obedience':           { b:['Thresher','Cryptic Axe'],               n:'ETHEREAL merc polearm' },
    'Rift':                { b:['War Scythe','Thresher'],                n:'merc polearm' },
    'Spirit':              { b:['Monarch','Crystal Sword'],              n:'Monarch shield · CS weapon' },
    'Phoenix':             { b:['Monarch'],                              n:'' },
    'Exile':               { b:['Sacred Targe','Sacred Rondache'],       n:'ETHEREAL auric shield' },
    'Dream':               { b:['Bone Visage','Troll Nest'],             n:'' },
    'Delirium':            { b:['Bone Visage','Spired Helm'],            n:'' },
    'Enigma':              { b:['Archon Plate','Mage Plate','Dusk Shroud'], n:'light elite armor' },
    'Chains of Honor':     { b:['Archon Plate','Dusk Shroud'],           n:'' },
    'Fortitude':           { b:['Archon Plate','Sacred Armor'],          n:'eth Sacred Armor for the merc' },
    'Treachery':           { b:['Archon Plate','Dusk Shroud'],           n:'' },
    'Stone':               { b:['Archon Plate','Sacred Armor'],          n:'' },
    'Faith':               { b:['Grand Matron Bow'],                     n:'Act 1 merc / zon bow' },
    'Ice':                 { b:['Grand Matron Bow'],                     n:'' },
    'Brand':               { b:['Grand Matron Bow'],                     n:'' },
    'Wrath':               { b:['Grand Matron Bow'],                     n:'' },
    'Harmony':             { b:['Grand Matron Bow','Matriarchal Bow'],   n:'' },
    'Mist':                { b:['Grand Matron Bow'],                     n:'' }
  };
  try { window.RW_BIS = RW_BIS; } catch(e){}
  function _metaBaseFor(rw){
    var m = _metaBaseCore(rw);
    var bis = RW_BIS[rw];
    if (bis && bis.b && bis.b.length){
      var seen = {}; var names = [];
      bis.b.concat(m.names || []).forEach(function(n){ var k = String(n).toLowerCase(); if (!seen[k]){ seen[k] = 1; names.push(n); } });
      m.names = names;
      if (bis.n) m.note = bis.n + (m.note ? ' · ' + m.note : '');
      m.bis = bis.b.slice();
    }
    return m;
  }
  function _metaBaseCore(rw){
    var e=(typeof RUNEWORD_TIP!=='undefined'?RUNEWORD_TIP[rw]:null)||{}; var b=String(e.b||'').toLowerCase();
    var nonWeapon=/body armor|shield|aegis|\bward\b|targe|rondache|helm|circlet|\bcap\b|crown|diadem|tiara/.test(b);
    if (nonWeapon){
      // armour / shield / helm → use the curated RW_BASES list, TYPE-MATCHED (never a weapon base)
      // take the note from the FIRST rec that actually contributes a kept (non-weapon) base — not rec[0],
      // which for a "weapons OR shields" word (Phoenix/Spirit) is the weapon entry and would show the wrong blurb.
      var names=[], note='';
      // v503 — a "Paladin Shields" word (Exile) may ONLY be recommended on an AURIC shield, never a regular
      // one (Monarch etc.). _AURIC_SHIELD is the paladin-shield list (global, from the _baseRunewords block).
      var _auricOnly = /\bpaladin\b|\bauric\b/.test(b), _AS = (typeof _AURIC_SHIELD!=='undefined') ? _AURIC_SHIELD : null;
      _bestFor(rw).forEach(function(r){ r.bases.forEach(function(x){
        var c=(typeof _baseCats==='function')?_baseCats(x):{};
        if (c['weapon']) return;                                              // never a weapon base
        if (/^\s*(?:Circlet|Coronet|Tiara|Diadem)\s*$/i.test(x)) return;      // circlets can't host runewords
        if (_auricOnly && _AS && !_AS.test(x)) return;                        // Exile etc. → auric shields only
        if (names.indexOf(x)<0) names.push(x); if (!note) note=r.meta||'';
      }); });
      // v514 — FALLBACK: many RotW armour/helm/shield words have no curated meta base, so the card showed the
      // bare spec ("3 socket Helms"). Pick the socket-correct ENDGAME base from BASE_DB instead (Bone Visage,
      // Troll Nest, Archon Plate…): type-matched, prefer socket-exact + elite, lowest str. So it names a base.
      if (!names.length && typeof BASE_DB!=='undefined'){
        var _need=(/(\d+)\s*socket/.exec(b)||[])[1]; _need=_need?+_need:0;
        // CURATED any-class endgame bases per slot (NO class-locked pelts/barb-helms — BASE_DB has no class
        // field, so druid pelts look like generic helms; this list keeps it to bases ANY class can wear).
        // Ordered best→worst; grimoire/voodoo-head (necro-only words like Vigilance) get their necro bases.
        var _CUR={
          helm:['Bone Visage','Spired Helm','Corona','Armet','Winged Helm','Great Helm','Casque','Basinet'],
          'body armor':['Archon Plate','Dusk Shroud','Wire Fleece','Scarab Husk','Kraken Shell','Hellforge Plate','Sacred Armor','Wyrmhide'],
          shield:['Monarch','Troll Nest','Aegis','Ward','Blade Barrier','Tower Shield','Gothic Shield','Luna'],
          grimoire:['Blasphemous Grimoire','Possessed Grimoire','Occult Codex','Dark Tome'],
          'voodoo head':['Bloodlord Skull','Hierophant Trophy','Succubus Skull','Cantor Trophy']
        };
        var _slot = /helm|\bcap\b|crown/.test(b)?'helm':/body armor/.test(b)?'body armor':/grimoire/.test(b)?'grimoire':/shrunken head|voodoo head/.test(b)?'voodoo head':/shield|aegis|\bward\b|targe|rondache/.test(b)?'shield':'';
        if(_need && _slot && _CUR[_slot]){
          var _cand=_CUR[_slot].filter(function(nm){
            if(_auricOnly && _AS && !_AS.test(nm)) return false;
            var d=BASE_DB[nm]; var mx=parseInt((typeof _socketMaxFor==='function')?_socketMaxFor(nm):0,10)||(d&&d.maxSockets)||0;
            return mx>=_need;                                          // must be able to hold the count
          });
          // socket-exact (Larzuk hits it cleanly) sorts ahead of overshoot, otherwise keep curated order
          _cand.sort(function(a,c){ var ea=((parseInt(_socketMaxFor(a),10)||0)===_need)?0:1, ec=((parseInt(_socketMaxFor(c),10)||0)===_need)?0:1; return ea-ec; });
          names=_cand.slice(0,4);
          if(!note && names.length){ var _ex=((parseInt(_socketMaxFor(names[0]),10)||0)===_need); note=_ex?('socket-correct '+_slot+' — Larzuk → exactly '+_need):('endgame '+_slot+' — find one with '+_need+' sockets'); }
        }
      }
      return { names:names.slice(0,4), note:note, merc:false, hand:'' };
    }
    // WEAPON — prefer the SOCKET-CORRECT elite base (max === rune count, right hand → clean Larzuk).
    var eb=_eliteBaseFor(rw);
    if (eb && eb.names.length){
      return { names:eb.names, note:(eb.merc?'2-handed mercenary base':eb.hand==='2H caster'?'2-handed caster staff — your weapon':'1-handed — your weapon')+' · Larzuk → exactly '+eb.need+' sockets', merc:eb.merc, hand:eb.hand };
    }
    // fallback (no clean-max elite — e.g. a 5os word): the popular base, still hand-correct.
    var bw=b.replace(/missile weapons?/g,' missilew ').replace(/melee weapons?/g,' meleew ');
    var has1H=/\bsword|\bblade|\baxe|scepter|sceptre|mace|hammer|club|flail|dagger|knife|katar|claw|wand|\borb/.test(b);
    var generic1H=/\bweapon|meleew/.test(bw);    // bare "Weapons" / "melee weapons" → any melee → the player's 1H
    // staff-only word = a 2-handed CASTER weapon (player-held — sorc/druid self-cast), NOT a merc weapon.
    if (!has1H && !generic1H && /staff|stave/.test(b) && !/polearm|spear|missilew|\bbow|crossbow|javelin/.test(bw)){
      return {names:['Archon Staff','Elder Staff'], note:'2-handed caster staff — your weapon', merc:false, hand:'2H caster'};
    }
    if (!has1H && !generic1H){                    // merc-only word (polearm / spear / bow / crossbow) → 2H merc base
      for (var i=0;i<_MERC_BASE.length;i++){ if(_MERC_BASE[i].re.test(b)) return {names:_MERC_BASE[i].names.slice(),note:_MERC_BASE[i].note,merc:true,hand:'2H merc'}; }
      return {names:[],note:'2-handed mercenary weapon',merc:true,hand:'2H merc'};
    }
    for (var j=0;j<_BEST_1H.length;j++){ if(_BEST_1H[j].re.test(b)) return {names:[_BEST_1H[j].base],note:_BEST_1H[j].note,merc:false,hand:'1H'}; }
    return {names:['Phase Blade','Berserker Axe'],note:'1-handed — Phase Blade (sword) or Berserker Axe (axe)',merc:false,hand:'1H'};
  }
  function _isIdealBase(rw, base){
    // v614 (lockdown) — EXACT name match after quality-strip. The old bidirectional substring let a
    // plain Pike impersonate 'War Pike' (and Scythe→'War Scythe', Targe→'Sacred Targe'), bypassing the
    // v576 endgame gate and firing the ideal-base cube gamble on normal-tier bases. Owned labels can
    // carry a quality prefix ('Superior Flail'), so strip that side; meta names are already clean.
    var m=_metaBaseFor(rw);
    var b=String(base||'').replace(/\s*\([^)]*\)\s*$/,'').replace(/^(?:Superior|Ethereal|Eth|Cracked|Crude|Damaged|Low Quality)\s+/i,'').trim().toLowerCase();
    return (m.names||[]).some(function(x){ return String(x).toLowerCase()===b; });
  }
  function _bestBaseStr(rw){ return (_metaBaseFor(rw).names||[]).slice(0,4).join(' / '); }
  function _bestMeta(rw){ return _metaBaseFor(rw).note||''; }
  try { window._forgeMetaBase=_metaBaseFor; } catch(e){}

  // ---- runeword helpers ----
  function _runeReq(rw){
    var e=(typeof RUNEWORD_TIP!=='undefined'&&RUNEWORD_TIP[rw])||{}; var rec=Array.isArray(e.rec)?e.rec:[];
    var req={}; rec.forEach(function(r){ if(typeof RUNE_INDEX!=='undefined'&&(r in RUNE_INDEX)) req[r]=(req[r]||0)+1; });
    return req;
  }
  function _rwVal(rw){
    var e=(typeof RUNEWORD_TIP!=='undefined'&&RUNEWORD_TIP[rw])||{}; var rec=Array.isArray(e.rec)?e.rec:[];
    return rec.reduce(function(m,r){ return Math.max(m,(RUNE_INDEX[r]||0)); },0);
  }
  function _rwBlocked(rw){
    try { if (typeof rwMade!=='undefined'&&rwMade&&rwMade[rw]) return 'made'; } catch(e){}
    var lo=(typeof _rwIsLadderOnly==='function')?_rwIsLadderOnly(rw):false;
    if (lo && typeof rwLadderMode!=='undefined' && rwLadderMode==='nonladder') return 'ladder';
    return '';
  }
  function _missing(req){
    // v652 — SOCKET ORDER, not value order (Konyo socketed his last ladder Cham in the value-sorted
    // 'missing' order and the word failed — runes wasted). req is built by iterating rec[] in order,
    // and JS preserves string-key insertion order — so Object.keys(req) IS the socket order.
    return Object.keys(req).filter(function(r){ return _runeCount(r)<req[r]; })
      .map(function(r){ return (req[r]-_runeCount(r))+'× '+r; });
  }
  // full-coaching: cheapest way to get a missing rune (cube recipe + farm hint)
  function _runeSource(rn){
    if (!rn || typeof RUNE_INDEX==='undefined' || !(rn in RUNE_INDEX)) return 'farm Countess / Hellforge / TZ';
    var idx=RUNE_INDEX[rn], parts=[];
    if (idx>0 && RUNES[idx-1] && RUNES[idx-1].up) parts.push('cube '+RUNES[idx-1].up);
    parts.push(idx>=24?'or farm Hell Countess / TZ / Hellforge (rare)':idx>=16?'or Countess (Hell) / Travincal / TZ':'or Countess / Hellforge / any Hell run');
    return parts.join(' ');
  }
  // v479 — the badge follows KONYO'S RULE, not the raw game hand: a player weapon word → 1H, a merc word → 2H,
  // armour/shield/helm → '' (no hand). So Breath of the Dying shows 1H (not the game's "1H/2H").
  function _hand(rw){
    // _metaBaseFor is the authority: '' for armour/shield/helm words (NO hand badge — fixes Phoenix, a
    // "weapons OR shields" word, wrongly showing 1H/2H from the old _rwHand fallback that saw "Weapons").
    try { var m=_metaBaseFor(rw); if (!m || !m.hand) return ''; return m.hand==='1H' ? '1H' : '2H'; } catch(e){}
    return '';
  }

  function _ownedBases(){
    var out=[];
    try { Array.from(owned).forEach(function(n){
      var e=(window.EXTRA_ITEMS&&EXTRA_ITEMS[n])||null;
      if (e && e.cat==='Socketed bases'){ out.push({
        name:n, base:e.base||n,
        sockets:(typeof e.sockets==='number')?e.sockets:0,
        max:(typeof _socketMaxFor==='function')?(parseInt(_socketMaxFor(e.base||n),10)||0):0,
        eth:(typeof window._isEthereal==='function')?!!window._isEthereal(n):false,
        sup:(typeof window._isSuperior==='function')?!!window._isSuperior(n):false,
        count:(typeof copyCount==='function')?copyCount(n):1
      }); return; }
      // v545 — a base TAGGED for a runeword, e.g. "Flail (Heart of the Oak base)" — an owned UNSOCKETED white base
      // the user is keeping to make that word. Recognise it (was invisible → the word wrongly read "go get a base").
      var m=String(n).match(/^(.+?)\s*\(([^()]+?)\s+base\)\s*$/i);
      if (m && !/^larzuk$/i.test(m[2].trim())){
        var baseName=m[1].trim(), tag=m[2].trim();
        var mx=(typeof _socketMaxFor==='function')?(parseInt(_socketMaxFor(baseName),10)||0):0;
        var isBase=mx>0 || (typeof _baseCats==='function' && Object.keys(_baseCats(baseName)||{}).length>0);
        try { var _pr=/(\d+)\s*os/i.exec(tag); if(_pr && parseInt(_pr[1],10)>mx) mx=parseInt(_pr[1],10); } catch(e){}   // v614 — a real read above the stored max is PROOF (the 2os Wand principle)
        if (isBase){ var rw=(typeof findRuneword==='function')?(findRuneword(tag)||''):'';
          // v614 — '(Nos low base)' intake labels carry their REAL socket count in the tag: register it
          // socketed (sockets are fixed once socketed) instead of as a phantom Larzuk/cube candidate.
          var _tagSock=/(\d+)\s*os/i.exec(tag); var _tsN=_tagSock?parseInt(_tagSock[1],10):0;
          out.push({ name:n, base:baseName, sockets:(_tsN>=1&&_tsN<=6)?_tsN:0, max:mx,
            eth:(typeof window._isEthereal==='function')?!!window._isEthereal(n):false,
            sup:(typeof window._isSuperior==='function')?!!window._isSuperior(n):false,
            count:(typeof copyCount==='function')?copyCount(n):1, taggedRw:rw }); }
      }
    }); } catch(e){}
    return out;
  }

  // ── SAFEGUARD SOCKET RULES — the cross-reference that auto-cancels illogical socketing ──
  // A runeword needs EXACTLY `need` sockets (= its rune count). Larzuk gives a base's single fixed MAX,
  // guaranteed; and you can only socket an UNSOCKETED white base (an existing socket count is permanent).
  //   cur === need            → 'have'   the base already holds exactly the right count
  //   cur  >  0  (and ≠ need)  → null     socketed at a different count — FIXED, can't change  → CANCEL
  //   cur === 0  & need === mx → 'larzuk' Larzuk guarantees the max = exactly what's needed → clean path
  //   else (need≠mx, mx unknown, need>mx) → null  Larzuk would overshoot and the cube is a one-shot random
  //                                               gamble (consumes the base) → NOT a directive path → CANCEL.
  // This is why a 6-socket-max Crystal Sword no longer shows "Larzuk → 4os": Larzuk only ever gives 6 here,
  // so a 4-socket word must use a base whose MAX is 4 (surfaced as a "need a base" task instead).
  function _socketRule(cur, need, mx){
    if (cur === need) return 'have';
    if (cur > 0) return null;
    if (mx && need === mx) return 'larzuk';
    return null;
  }
  // v545 — cube-socket recipe by base slot (Ral+Amn+P.gem = a RANDOM 1→max sockets). Used only for the cube-socket
  // GAMBLE step on an owned, tagged, unsocketed base whose max overshoots the word (Larzuk can't hit the count).
  function _cubeGambleRecipe(base){
    var c={}; try { c=(typeof _baseCats==='function')?(_baseCats(base)||{}):{}; } catch(e){}
    if (c['body armor']||c['armor']) return 'Tal + Thul + Perfect Topaz';
    if (c['shield']) return 'Tal + Amn + Perfect Ruby';
    if (c['helm']) return 'Ral + Thul + Perfect Sapphire';
    return 'Ral + Amn + Perfect Amethyst';   // weapon (default)
  }
  // v546 — the Perfect gem the cube-socket recipe for this base slot consumes (for the "how many tries can I
  // afford" note). Mirrors _cubeGambleRecipe's slot logic.
  function _cubeGambleGem(base){
    var c={}; try { c=(typeof _baseCats==='function')?(_baseCats(base)||{}):{}; } catch(e){}
    if (c['body armor']||c['armor']) return 'Perfect Topaz';
    if (c['shield']) return 'Perfect Ruby';
    if (c['helm']) return 'Perfect Sapphire';
    return 'Perfect Amethyst';
  }
  // v546 — affordability note for a cube-socket gamble: how many attempts your gem stash covers (each try burns
  // one Perfect gem + a fresh base). Honest framing — the cube rolls a RANDOM count 1→max, so a below-max target
  // takes several tries on average. Factual on the gem count; soft on the odds.
  function _gambleAfford(base, need, mx){
    var gem=_cubeGambleGem(base); var have=(typeof _gemCount==='function')?_gemCount(gem):0;
    var span=(mx>1)?('random 1–'+mx):'';
    var afford = have>0 ? ('you hold <b>'+have+' '+_fEsc(gem)+'</b> → ~'+have+' tr'+(have===1?'y':'ies')) : ('no <b>'+_fEsc(gem)+'</b> in your gem stash yet');
    return '<span class="f-atomsub">🎲 '+span+', so keep a few spare '+_fEsc(base)+'s + gems — '+afford+'</span>';
  }
  // v546 — "Do this one thing" hero: the single highest-leverage next move, chosen from the live plan. Priority:
  // a Make-now (forge it) → a Pipeline (one socket/gamble away) → the top farm target → a one-step. Cuts the
  // "where do I even start" paralysis by naming ONE action.
  function _heroArt(name, kind){
    if (!name) return '<span class="f-glyph">📜</span>';
    if (kind==='base'){ var u=(typeof _fArt==='function')?_fArt(name):''; return u?'<img class="f-art" src="'+_fEsc(u)+'" alt="" loading="lazy">':'<span class="f-glyph">🛡️</span>'; }
    return _rwArt(name);
  }
  function _forgeHero(s){
    var pick=null;
    var live=(s.now||[]).filter(function(t){return !t.deferred;});
    if (live.length){ var b=live.slice().sort(function(a,c){return (c.val||0)-(a.val||0);})[0];
      // v557 — SHOW the how, don't describe it: the hero carries the rune recipe chips + the exact owned base.
      pick={icon:'⚒', tone:'now', art:(b.base&&b.base.base)||b.rw, artKind:(b.base&&b.base.base)?'base':'rw', lead:'forge it now', name:_qArt(b.rw),   // v680 — the hero wears the ACTUAL base's art (Peace in your Archon Plate → AP sprite)
        body:'in your <b>'+b.base.sockets+'os '+_fEsc(b.base.base)+'</b> · <span class="fh-recipe">'+_recipe(b.rw)+'</span>', act:"window.forgeSetFilter('now')", cta:'Make now',
        // v618 (Konyo: "the top one should also be able to be clicked on and created") — the hero
        // carries the SAME one-click ✓ as the list cards: forgeDoneAnim → rwToggleMade → Chronicle
        // tally + vault consume + celebration, identical sync path.
        done:'<button class="f-btn fh-cta fh-done" onclick="window.forgeDoneAnim(this,\''+_fJs(b.rw)+'\',\''+_fJs(b.base.name)+'\')" title="I forged it — tick it created (tallies the Chronicle, consumes the base from the vault)">✓ created</button>'};
    } else if ((s.pipeline||[]).length){ var p=s.pipeline.slice().sort(function(a,c){return (c.val||0)-(a.val||0);})[0]; var tgt=p.base?p.base.base:'';
      pick={icon:p.cubeGamble?'🎲':'🔧', tone:'pipe', art:p.rw, artKind:'rw', lead:p.cubeGamble?'one gamble away':'one socket away', name:_qArt(p.rw),
        body:(p.cubeGamble?'Cube-socket your <b>'+_qArt(tgt)+'</b> (gamble for '+p.need+'os)':'Larzuk your <b>'+_qArt(tgt)+'</b> → '+p.need+'os')+' → forge it', act:"window.forgeSetFilter('pipeline')", cta:'Pipeline'};
    } else {
      var fp=[]; try { fp=(typeof window._smartFarmPriority==='function')?window._smartFarmPriority():[]; } catch(e){}
      if (fp.length){ var f=fp[0];
      // v658 — WHERE to farm it, qlvl-aware (Konyo: "didn't we say cow level for bases is a gold mine?").
      // Cows ARE the density king — but ONLY for qlvl ≤ 81 bases; the hero must say which side this base is on.
      var _ci=(typeof window._cowInfo==='function')?window._cowInfo(f.base):null;
      var _where=_ci?(_ci.cows?' · 🐄 <b>Hell Cows CAN drop it</b> (qlvl '+_ci.q+' ≤ cow alvl 81) — the density gold mine':' · 🐄 <b>Cows can NEVER drop it</b> (qlvl '+_ci.q+' &gt; cow alvl 81) — farm <b>Pit / Ancient Tunnels / lvl-85 TZs</b>'):'';
      pick={icon:'🎯', tone:'step', art:f.base, artKind:'base', lead:'best thing to farm', name:_qArt(f.base), body:'unlocks <b>'+f.count+'</b> runeword'+(f.count>1?'s':'')+_where, act:"window.switchTab&&window.switchTab('tools');setTimeout(function(){var c=document.getElementById('smart-insights-card');if(c&&c.classList.contains('collapsed')&&window.toggleCardCollapse)window.toggleCardCollapse('smart-insights-card');window.renderSmartInsights&&window.renderSmartInsights();if(c)c.scrollIntoView({block:'start',behavior:'smooth'});},80)", cta:'Smart Insights'};
      } else { var os=(s.onestep||[])[0]; if (os) pick={icon:'🟡', tone:'step', art:os.rw, artKind:'rw', lead:'one step away', name:_qArt(os.rw), body:'do the one step to unlock it', act:"window.forgeSetFilter('onestep')", cta:'One step'}; }
    }
    if (!pick) return '';
    // v557 — after a filter-switch CTA, glide to the first task card so the click lands ON the action
    if (pick.act.indexOf('forgeSetFilter')===0 || pick.act.indexOf("window.forgeSetFilter")===0){
      pick.act += ";setTimeout(function(){var c=document.querySelector(':is(#tab-forge,#tab-funi,#tab-fsets) .f-card');if(c)c.scrollIntoView({block:'center',behavior:'smooth'});},180)";
    }
    return '<div class="forge-hero forge-hero-'+pick.tone+'">'
      + '<span class="fh-ember"></span><span class="fh-ember"></span><span class="fh-ember"></span><span class="fh-ember"></span>'   // v558 — living forge embers (decorative, reduced-motion-safe)
      + '<div class="fh-artwrap"><div class="fh-art">'+_heroArt(pick.art, pick.artKind)+'</div><div class="fh-icobadge">'+pick.icon+'</div></div>'
      + '<div class="fh-main"><div class="fh-lead">👉 DO THIS ONE THING · '+pick.lead+'</div>'
      + '<div class="fh-name">'+pick.name+'</div><div class="fh-body">'+pick.body+'</div></div>'
      + '<button class="f-btn fh-cta" onclick="'+pick.act+'">'+pick.cta+' <span class="fh-cta-arw">→</span></button>'+(pick.done||'')+'</div>';
  }

  // hand class of an owned base for the 1H-player / 2H-merc gate: 'gear' (armour/shield/helm), 'merc'
  // (polearm/spear/bow/xbow — a mercenary's 2H), '1H', '2H' (a 2H NON-merc weapon — forbidden for the player), '?'.
  function _baseHandClass(base){
    var c=(typeof _baseCats==='function')?_baseCats(base):{};
    if (c['body armor']||c['shield']||c['helm']) return 'gear';
    if (c['polearm']||c['spear']||c['missile weapon']) return 'merc';
    if (c['staff']) return 'caster';   // a staff is a player CASTER 2H weapon (not merc, not 1H)
    var d=(typeof BASE_DB!=='undefined')?BASE_DB[base]:null;
    // an "either-hand" base (oneH AND twoH — Zweihander, Bastard Sword…) counts as 2H: the endgame wants a
    // PURE 1-handed base (Phase Blade/Berserker Axe have oneH only). twoH present → treat as 2H.
    if (d && d.twoH) return '2H';
    if (d && d.oneH) return '1H';
    return '?';
  }
  // does an owned base's hand class satisfy what a runeword wants? (1H player word ⇒ 1H base; merc word ⇒ merc base)
  function _handOk(rw, base){
    var want=_metaBaseFor(rw).hand;                 // '1H' | '2H merc' | ''
    if (!want) return true;                         // armour/shield/helm word — no hand constraint
    var bh=_baseHandClass(base);
    if (want==='1H') return bh==='1H';
    if (want==='2H merc') return bh==='merc';
    if (want==='2H caster') return bh==='caster';
    return true;
  }

  function forgeScan(){
    var out={ now:[], pipeline:[], onestep:[], crafts:[], counts:{} };
    if (typeof RUNEWORD_TIP==='undefined' || typeof canMakeNow!=='function') return out;
    var bases=_ownedBases();
    // v614 — rank by GAP COUNT, not raw kind: an exact-fit socketed base whose runes just need cubing
    // (onestep sub:'cube' — 1 gap) must beat an unsocketed Larzuk base + cube (pipeline sub:'cube' —
    // 2 gaps); the old kind-only rank told the user to burn Larzuk while the ready base idled.
    var kindRank=function(t){
      if (t.kind==='now') return 0;
      if (t.kind==='pipeline') return t.sub==='cube'?3:1;
      return t.sub==='cube'||t.sub==='runes'?2:4;   // onestep cube/runes (base ready) > pipeline-cube; get-base last
    };
    var byRw={}, _nowCands={}, _pipeCands={};   // _nowCands / _pipeCands: rw → ALL owned bases (socketed / Larzuk) that can host it, so allocation can spread across every base, not just one
    // 1) cross owned bases × the runewords they can hold
    bases.forEach(function(b){
      var rws=(typeof _baseRunewords==='function')?_baseRunewords(b.base):[];
      rws.forEach(function(rw){
        var name=rw.n, need=rw.s;
        if (_rwBlocked(name)) return;
        // HAND GATE. Fresh-base recommendations stay strict (1H player / 2H merc, via _metaBaseFor). But a base
        // you ALREADY OWN that type-matches the word CAN host it — a 2H/merc owned base just makes it a MERCENARY
        // weapon (Konyo's "2H = merc" rule), so surface it tagged instead of dropping it. Genuinely-wrong hands
        // (e.g. a caster-staff word on a non-staff) still drop.
        var _mercOwn=false;
        if (!_handOk(name, b.base)){
          var _obh=_baseHandClass(b.base), _owant=_metaBaseFor(name).hand;
          // NOTE (v553 audit): a broad "accept owned caster staves" rescue was tried + REVERTED — _baseRunewords is
          // over-permissive for staves (it lists melee-only words like Honor / Hand of Justice for a staff), so
          // rescuing all caster staves would surface WRONG tasks (Honor-in-a-staff). The narrow, correct fix needs
          // reliable "which weapon words the RotW mod allows in a staff" data — deferred + flagged rather than guessed.
          if ((_obh==='2H'||_obh==='merc') && (_owant==='1H'||_owant==='')) _mercOwn=true; else return;
        }
        // v576 — ENDGAME-GEAR GATE (Konyo: "these runewords should not be in these white bases regardless of
        // the Chronicle — after created I use it on characters"). An EXPENSIVE word (top rune ≥ Ist) is only
        // planned on a base you'd actually WEAR: the word's IDEAL meta base (Crystal Sword for CtA counts) or
        // an ELITE base — and NEVER parked on a 2H/merc-rescued base (no Hand of Justice in a Colossus Voulge,
        // no Eternity in a plain Flail). Cheap words (Rhyme/Stealth/Honor…) keep using whatever you hold.
        var _egIst = (typeof RUNE_INDEX!=='undefined' && RUNE_INDEX['Ist']!=null) ? RUNE_INDEX['Ist'] : 23;
        if (_rwVal(name) >= _egIst){
          // v583 — the word's TRUE home (RW_BIS/ideal) always passes, even held as a 2H/merc stick (BotD in
          // an eth Colossus Blade is the classic); otherwise: never a merc-rescue, and elite-tier required.
          var _egIdeal = _isIdealBase(name, b.base);
          // v628 — an ALREADY-SOCKETED exact-fit base bypasses the gate: the word is makeable NOW at
          // zero cost (Konyo's 4os Double Bow → Faith). The gate still stops Larzuk/gamble PLANS on
          // non-ideal, non-elite bases (don't burn quests/runes on the wrong home).
          var _egFit = (b.sockets === need);
          if (!_egIdeal && !_egFit && _mercOwn) return;
          if (!_egIdeal && !_egFit && ((typeof window._baseTier==='function'?window._baseTier(b.base):'')!=='elite')) return;
        }
        // NOTE: do NOT gate on _socketMaxFor here — a base that ALREADY has `need` sockets proves it can hold
        // them, even when our max estimate is low (e.g. Wand reports max 1 but a 2os Wand is real). The max
        // guard belongs only on the socket-UP pipeline branch below, where reachability genuinely matters.
        var req=_runeReq(name); if (!Object.keys(req).length) return;
        var runesNow=canMakeNow(req);
        var runesCube=!runesNow && (typeof canMakeWithCubing==='function') && canMakeWithCubing(req);
        var rule=_socketRule(b.sockets, need, b.max);
        // v545 — CUBE-SOCKET GAMBLE: a base you OWN + TAGGED for THIS word (e.g. "Flail (Heart of the Oak base)"),
        // unsocketed, whose MAX overshoots the word's count (Larzuk can't hit it). Larzuk is out, but the cube
        // socket recipe (Ral+Amn+P.gem = random 1→max) CAN land it — so offer it as a gamble instead of dropping
        // the owned base to a "go get a base" one-step. Scoped to TAGGED bases only (b.taggedRw===name) so it never
        // floods untagged white bases with gamble tasks. (Untagged bases keep the strict Larzuk-clean rule.)
        // v575 — the gamble ALSO fires when the owned unsocketed base IS the word's IDEAL meta base (Konyo's
        // unsocketed Superior Flail must offer the HotO gamble: need 4 < max 5, Larzuk overshoots). Still no
        // flood — ideal-base matches only, arbitrary white bases keep the strict rule.
        // v575.1 — SUPERIOR EXCLUSION: the cube socket recipe only works on PLAIN NORMAL items (superior and
        // low-quality are excluded, game rule) — a superior base's ONLY socket path is Larzuk = guaranteed max.
        // So a Superior Flail can never reach HotO's 4os; offering the gamble on it would waste his runes.
        var _cubeGamble = (!rule && b.sockets===0 && !b.sup && (b.taggedRw===name || _isIdealBase(name, b.base)) && b.max && need>0 && need<b.max);
        if (!rule && !_cubeGamble) return;              // SAFEGUARD: not a legitimate path for this base → auto-cancelled
        var t=null;
        if (rule==='have'){                             // base already has EXACTLY the needed sockets
          if (runesNow){ t={kind:'now', rw:name, base:b, need:need, req:req}; (_nowCands[name]=_nowCands[name]||[]).push(b); }
          else if (runesCube) t={kind:'onestep', sub:'cube', rw:name, base:b, need:need, req:req, missing:_missing(req)};
          else t={kind:'onestep', sub:'runes', rw:name, base:b, need:need, req:req, missing:_missing(req)};
        } else {                                        // 'larzuk' (max===need) OR a cube-socket gamble (tagged, need<max)
          if (runesNow) t={kind:'pipeline', rw:name, base:b, need:need, req:req, cubeGamble:_cubeGamble};
          else if (runesCube) t={kind:'pipeline', sub:'cube', rw:name, base:b, need:need, req:req, missing:_missing(req), cubeGamble:_cubeGamble};
          // no runes + needs socket = 2 gaps → skip (lives in the Vault's Socketed Review)
          if (t && t.kind==='pipeline') (_pipeCands[name]=_pipeCands[name]||[]).push(b);   // v536 — every owned Larzuk base that can host it (spread allocation below)
        }
        if (!t) return;
        t.hand=_mercOwn?'2H merc':_hand(name); t.mercOwn=_mercOwn; t.val=_rwVal(name); t.ideal=_isIdealBase(name,b.base); t.bestStr=_bestBaseStr(name); t.bestMeta=_bestMeta(name);
        var cur=byRw[name];
        if (!cur){ byRw[name]=t; }
        else {
          var r1=kindRank(t), r0=kindRank(cur);
          if (r1<r0) byRw[name]=t;                          // better kind wins (now > pipeline > onestep)
          // v582 — tie → a HAND-CORRECT base beats a merc-rescued one (Konyo's Flail-vs-Zweihander for
          // Honor: the 1H Flail is the player home; the 2H rescue is the compromise), then the meta base.
          else if (r1===r0 && !t.mercOwn && cur.mercOwn) byRw[name]=t;
          else if (r1===r0 && !!t.mercOwn===!!cur.mercOwn && t.ideal && !cur.ideal) byRw[name]=t;
        }
      });
    });
    // 2) runeword-driven: runes fully in hand but NO matching base owned → "find a base"
    try { Object.keys(RUNEWORD_TIP).forEach(function(name){
      if (byRw[name] || _rwBlocked(name)) return;
      var req=_runeReq(name); if (!Object.keys(req).length || !canMakeNow(req)) return;
      var e=RUNEWORD_TIP[name]||{};
      byRw[name]={ kind:'onestep', sub:'base', rw:name, base:null, need:0, req:req, baseReq:e.b||'', hand:_hand(name), val:_rwVal(name), bestStr:_bestBaseStr(name), bestMeta:_bestMeta(name) };
    }); } catch(e){}
    // 2b) v604 — COVERAGE CATCH-ALL (Konyo's Katar/Pattern incident: "why is it not tasking me"): a word
    // with NO owned base AND runes not ready used to appear NOWHERE — silent. Every remaining unmade,
    // unblocked word now lands in out.farm ("furthest out": what base to find + which runes are missing),
    // so the Forge always answers "what's left" for the ENTIRE Chronicle. Invariant: unmade ∧ ¬blocked ⇒
    // present in now ∪ pipeline ∪ onestep ∪ farm — locked by v604_forge_coverage_invariant.spec.ts.
    out.farm=[];
    try { Object.keys(RUNEWORD_TIP).forEach(function(name){
      if (byRw[name] || _rwBlocked(name)) return;
      var req=_runeReq(name); if (!Object.keys(req).length) return;
      var e=RUNEWORD_TIP[name]||{};
      out.farm.push({ kind:'farm', rw:name, base:null, need:0, req:req, baseReq:e.b||'', missing:_missing(req), hand:_hand(name), val:_rwVal(name), bestStr:_bestBaseStr(name), bestMeta:_bestMeta(name) });
    }); out.farm.sort(function(a,b){ return b.val-a.val || a.rw.localeCompare(b.rw); }); } catch(e){}
    // v632 — LADDER-LOCKED VISIBILITY (Konyo's Death Mask: "lots of runewords to still create — why is
    // it not part of the forge"): the ladder rune-saver (v419, born from HIS Mania rune-waste on a
    // non-ladder char) HIDES the 9 mod-ladder words off-ladder — correctly un-taskable, but silently,
    // so the Chronicle counts them while the Forge pretends they don't exist. They now surface in a
    // dedicated read-only strip. Invariant upgrade: unmade ⇒ visible SOMEWHERE, blocked included.
    out.ladder=[];
    try { if (typeof rwLadderMode!=='undefined' && rwLadderMode==='nonladder') Object.keys(RUNEWORD_TIP).forEach(function(name){
      if (_rwBlocked(name)!=='ladder') return;
      var e=RUNEWORD_TIP[name]||{};
      out.ladder.push({ rw:name, baseReq:e.b||'', val:_rwVal(name) });
    }); out.ladder.sort(function(a,b){ return b.val-a.val || a.rw.localeCompare(b.rw); }); } catch(e){}
    // bucket
    Object.keys(byRw).forEach(function(k){ var t=byRw[k]; (t.kind==='now'?out.now:t.kind==='pipeline'?out.pipeline:out.onestep).push(t); });
    // v630 — EXCLUSIVITY RESERVATION (Konyo: "logic and priority — the sacred shield I have should task
    // me to create Exile with it instead of wasting that item for the Phoenix"). Before any allocation,
    // every word with an owned host reserves ONE copy — CLASS-LOCKED words (window._rwClassLocked) jump
    // the value queue, because their base class is the only home they will EVER have; broad words keep
    // the old value order among themselves. Downstream, a word may only claim a copy reserved for it
    // (or a spare beyond all reservations) — a denied broad word re-tasks as get-ANOTHER-base.
    var _rsv={};   // owned copy label → [rw names], one entry per reserved copy
    try {
      var _rw2cands={};
      Object.keys(byRw).forEach(function(n){ var t=byRw[n]; var c=(_nowCands[n]||[]).concat(_pipeCands[n]||[]); if(t&&t.base&&c.indexOf(t.base)<0) c.push(t.base); if(c.length) _rw2cands[n]=c; });
      var _rsvTaken={};
      Object.keys(_rw2cands)
        .sort(function(a,b){ var la=window._rwClassLocked(a)?0:1, lb=window._rwClassLocked(b)?0:1;
          if (la!==lb) return la-lb;
          // non-locked words reserve in the OLD claim order: readiness first (a make-now word must not
          // lose its base to a rune-blocked higher-value word — v535's Insight), then value
          var ka=kindRank(byRw[a]||{}), kb=kindRank(byRw[b]||{});
          return ka-kb || _rwVal(b)-_rwVal(a) || a.localeCompare(b); })
        .forEach(function(n){
          var cands=_rw2cands[n].slice().sort(function(a,c){ var ha=_handOk(n,a.base)?1:0,hc2=_handOk(n,c.base)?1:0; if(ha!==hc2) return hc2-ha; return (_isIdealBase(n,c.base)?1:0)-(_isIdealBase(n,a.base)?1:0); });
          for (var i=0;i<cands.length;i++){ var c=cands[i]; if(!c||!c.name) continue; if((_rsvTaken[c.name]||0) < (c.count||1)){ _rsvTaken[c.name]=(_rsvTaken[c.name]||0)+1; (_rsv[c.name]=_rsv[c.name]||[]).push(n); break; } }
        });
    } catch(e){}
    var _rsvOk=function(rwName, c){
      var r=_rsv[c.name]; if(!r || !r.length) return true;
      if (r.indexOf(rwName)>=0) return true;
      return (c.count||1) > r.length;   // copies to spare beyond every reservation
    };
    var _rsvHolder=function(t){ return (t&&t.base&&t.base.name&&_rsv[t.base.name]&&_rsv[t.base.name].indexOf(t.rw)>=0)?0:1; };
    // 3) conflict / auto-prioritise: value-sort, greedily allocate the shared rune + base pool
    out.now.sort(function(a,b){ return b.val-a.val || (b.ideal?1:0)-(a.ideal?1:0) || a.rw.localeCompare(b.rw); });
    var pool={}; (typeof RUNES!=='undefined'?RUNES:[]).forEach(function(r){ pool[r.n]=_runeCount(r.n); });
    var baseUsed={};   // base item-name → copies already consumed this pass
    out.now.forEach(function(t){
      var runeOk=Object.keys(t.req).every(function(r){ return (pool[r]||0)>=t.req[r]; });
      // pick an AVAILABLE base from EVERY owned base that can host this word (ideal/meta base first),
      // not just the one pre-chosen — so a 2nd 6os base lets a 2nd 6os word be made now (Konyo's Spetum case).
      var cands=(_nowCands[t.rw]||(t.base?[t.base]:[])).slice()
        // v582 — HAND-CORRECT bases first (Konyo's Flail-vs-Zweihander: Honor belongs in the 1H player
        // base; the 2H merc-rescue is the fallback), then the ideal/meta base among equals.
        .sort(function(a,c){
          var ha=_handOk(t.rw,a.base)?1:0, hc2=_handOk(t.rw,c.base)?1:0;
          if (ha!==hc2) return hc2-ha;
          return (_isIdealBase(t.rw,c.base)?1:0)-(_isIdealBase(t.rw,a.base)?1:0);
        });
      var chosen=null;
      for (var i=0;i<cands.length;i++){ var c=cands[i]; if (c && (baseUsed[c.name]||0) < (c.count||1) && _rsvOk(t.rw,c)){ chosen=c; break; } }   // v630 — never claim a copy earmarked for a class-locked word
      if (runeOk && chosen){
        Object.keys(t.req).forEach(function(r){ pool[r]-=t.req[r]; });
        baseUsed[chosen.name]=(baseUsed[chosen.name]||0)+1;
        t.base=chosen; t.ideal=_isIdealBase(t.rw,chosen.base); t.deferred=false;
        t.mercOwn=!_handOk(t.rw,chosen.base); t.hand=t.mercOwn?'2H merc':_hand(t.rw);   // v582 — flag follows the CHOSEN base
      } else {
        t.deferred=true;
        t.blockedBy=Object.keys(t.req).filter(function(r){ return (pool[r]||0)<t.req[r]; });
        if(!chosen && t.base) t.blockedBase=t.base.base;
        if(!chosen && t.base && t.base.name && _rsv[t.base.name] && _rsv[t.base.name].indexOf(t.rw)<0) t.rsvFor=_rsv[t.base.name][0];   // v630 — say WHO the copy is earmarked for
      }
    });
    // 4) crafts you can cube now (have the perfect gem + the slot rune)
    try { if (typeof CRAFTS!=='undefined' && CRAFTS) CRAFTS.forEach(function(c){
      if ((typeof _gemCount==='function'?_gemCount(c.gem):0)<1) return;
      var slots=(c.best&&c.best.length)?c.best:Object.keys(c.slots||{});
      slots.forEach(function(slot){
        var rec=c.slots&&c.slots[slot]; if(!rec) return;
        if ((typeof _runeCount==='function'?_runeCount(rec.rune):0)<1) return;
        out.crafts.push({ craft:c.key, slot:slot, rune:rec.rune, gem:c.gem, base:rec.base, color:c.color, star:!!c.star, tell:c.tell, bis:c.bis });
      });
    }); } catch(e){}
    // NOTE (v542): there is NO "base upgrade" concept anywhere in the Forge. A white / normal / superior / magic
    // base CANNOT be cube-upgraded to a higher tier — only unique/rare/set items can (game-file cubemain.txt;
    // Konyo confirmed in-game a Superior Bone Helm won't cube up). A base is usable for a runeword ONLY if its OWN
    // max sockets === the word's count (Larzuk gives that max). If your owned base can't reach the count, the word
    // surfaces as a "🛒 get the right base" one-step (find the elite/right-tier base as a white drop), not an upgrade.
    // _socketRule already cancels a base whose max ≠ need (no upgrade path exists).
    // rank the slower buckets
    out.pipeline.sort(function(a,b){ return b.val-a.val || (b.ideal?1:0)-(a.ideal?1:0) || a.rw.localeCompare(b.rw); });
    // v536 — SPREAD pipeline words across your DISTINCT owned Larzuk bases (shares the baseUsed pool with the
    // make-now pass above). Fixes: owning e.g. a Thresher AND a Cryptic Axe (both 5os merc) but the Forge piling
    // two 5os words onto ONE, leaving the other base idle. Value-sorted so the top word claims the ideal base
    // first; a word with no free base left keeps its base and groups as an alternative under it (prior behaviour).
    out.pipeline.forEach(function(t){
      var cands=(_pipeCands[t.rw]||(t.base?[t.base]:[])).slice()
        // v582 — hand-correct first, then ideal (mirrors the make-now allocation)
        .sort(function(a,c){
          var ha=_handOk(t.rw,a.base)?1:0, hc2=_handOk(t.rw,c.base)?1:0;
          if (ha!==hc2) return hc2-ha;
          return (_isIdealBase(t.rw,c.base)?1:0)-(_isIdealBase(t.rw,a.base)?1:0);
        });
      // v536.1 — prefer a base TYPE not yet used this pass over burning a 2nd COPY of an already-used base. So
      // owning 3× Thresher + 1 Cryptic Axe and needing two 5os words → Thresher + Cryptic Axe (each card names a
      // distinct base, no "Larzuk your Thresher ×2" confusion), instead of two Threshers. Falls back to a spare
      // copy only when no fresh base type is available.
      var pick=null, spare=null;
      for (var i=0;i<cands.length;i++){ var c=cands[i]; if(!c) continue;
        var u=baseUsed[c.name]||0, cap=c.count||1; if (u>=cap) continue;
        if (!_rsvOk(t.rw,c)) continue;          // v630 — reserved for a class-locked word, hands off
        if (u===0){ pick=c; break; }          // a base type not yet touched → clearest + uses your other bases
        if (!spare) spare=c;                    // else a base you own MORE than one of (copies to spare)
      }
      var chosen=pick||spare;
      if (!chosen && t.base && t.base.name && _rsv[t.base.name] && _rsv[t.base.name].indexOf(t.rw)<0) t.rsvFor=_rsv[t.base.name][0];   // v630
      if (chosen){ t.base=chosen; t.ideal=_isIdealBase(t.rw,chosen.base); baseUsed[chosen.name]=(baseUsed[chosen.name]||0)+1;
        t.mercOwn=!_handOk(t.rw,chosen.base); t.hand=t.mercOwn?'2H merc':_hand(t.rw);   // v582 — flag follows the CHOSEN base
        // v545 — recompute the cube-gamble flag against the ACTUAL chosen base (a clean Larzuk base has max===need
        // → false; a tagged unsocketed base whose max overshoots the count → true). Keeps flag ↔ base in sync even
        // when byRw picked a different candidate than the spread allocator lands on.
        t.cubeGamble = (chosen.sockets===0 && !chosen.sup && (chosen.taggedRw===t.rw || _isIdealBase(t.rw, chosen.base)) && chosen.max && t.need>0 && t.need < chosen.max);   // v614 — same eligibility as the original gate (superior NEVER cube-gambles)
      }
    });
    out.onestep.sort(function(a,b){ var o=function(t){return t.sub==='cube'?0:t.sub==='runes'?1:2;}; return o(a)-o(b) || b.val-a.val || a.rw.localeCompare(b.rw); });
    // v587 — CAPACITY TRUTH (Konyo's 1× Bone Visage): one physical base hosts ONE runeword, ever. The passes
    // above can still leave several words naming the SAME copy (a spread task with no free base "keeps its
    // base"; rune-blocked one-steps never allocate at all) — so re-walk every based task in plan-priority
    // order through a fresh ledger and flag the overflow (t.baseOver). Downstream, an over-subscribed task
    // must NOT count as "you own a base for this word" (vault spare/throw-out verdicts, the loot filter's
    // base-skip, smart insights) — else 3 unmade words all "covered by" one Bone Visage vendor the Demonhead
    // that two of them still need.
    try {
      var _capUsed={};
      var _capClaim=function(t){ if(!t||!t.base||!t.base.name) return;
        var _cu=_capUsed[t.base.name]||0;
        if (_cu >= (t.base.count||1)){ t.baseOver=true; if(!t.rsvFor && _rsv[t.base.name] && _rsv[t.base.name].indexOf(t.rw)<0) t.rsvFor=_rsv[t.base.name][0]; }
        else { t.baseOver=false; _capUsed[t.base.name]=_cu+1; }
      };
      // v630 — within each group, the copy's RESERVED word claims first (stable sort: everything else
      // keeps its order). Without this, a higher-value onestep (Phoenix) still out-claimed Exile here.
      var _rsvFirst=function(arr){ return arr.slice().sort(function(a,b){ return _rsvHolder(a)-_rsvHolder(b); }); };
      _rsvFirst(out.now.filter(function(t){return !t.deferred;})).forEach(_capClaim);   // real makes claim first (allocation already kept these within capacity)
      _rsvFirst(out.now.filter(function(t){return t.deferred;})).forEach(_capClaim);    // a rune-blocked make still HOLDS its base — it's the plan once the rune drops
      _rsvFirst(out.pipeline).forEach(_capClaim);
      _rsvFirst(out.onestep.filter(function(t){ return t.sub!=='base'; })).forEach(_capClaim);
    } catch(e){}
    out.counts={ now:out.now.filter(function(t){return !t.deferred;}).length, deferred:out.now.filter(function(t){return t.deferred;}).length, pipeline:out.pipeline.length, onestep:out.onestep.length, crafts:out.crafts.length };
    return out;
  }

  function _rwArt(rw){
    var a=(typeof _rwArtName==='function')?_rwArtName(rw):rw;
    var src=_fArt(a) || ((typeof _rwcCatArt==='function')?_rwcCatArt(((typeof RUNEWORD_TIP!=='undefined'&&RUNEWORD_TIP[rw])||{}).b):'');
    return src?'<img class="f-art" src="'+_fEsc(src)+'" alt="" loading="lazy">':'<span class="f-glyph">📜</span>';
  }
  function _recipe(rw){
    var e=(typeof RUNEWORD_TIP!=='undefined'&&RUNEWORD_TIP[rw])||{}; var rec=Array.isArray(e.rec)?e.rec:[];
    return (typeof _rwRecipeArt==='function')?_rwRecipeArt(rec.join(' + ')):_fEsc(rec.join(' + '));
  }
  // v624 (Konyo: "how can it propose Phoenix in the 4os Phase Blade I just used for Kingslayer?" —
  // the consume HAD fired, on one copy of his ×2 stack; the card just never said so): every task
  // card whose base label has consumed siblings narrates them, and multi-copy bases show ×N.
  function _consumedNote(baseLabel){
    try {
      var used = JSON.parse(window.LSR.getItem('d2r_rwBaseUsed')||'{}');
      var words = Object.keys(used).filter(function(k){ return used[k] && used[k].l === baseLabel; });
      if (!words.length) return '';
      var n = (typeof copyCount==='function') ? copyCount(baseLabel) : 1;
      return '<div class="f-atomsub" style="color:#8fb8a0">♻ ' + (n>1 ? 'you hold ×'+n+' — another copy' : 'its twin copy') + ' already became <b>' + _fEsc(words.join(', ')) + '</b>; this task uses a REMAINING one</div>';
    } catch(e){ return ''; }
  }
  function _handTag(h){ if(!h) return ''; var ti=h==='1H/2H'?'one- or two-handed depending on base':/2H merc/.test(h)?'two-handed → a mercenary weapon':/2H caster/.test(h)?'two-handed caster staff (your weapon)':h==='2H'?'two-handed':'one-handed'; return '<span class="f-hand" title="'+ti+'">'+_fEsc(h)+'</span>'; }
  function _baseLine(t){
    // v676 (Konyo's Crusader-Bow BotD: 'it tells me to create BotD in the crusader bow instead of
    // Berserker Axe / Colossus Blade… I need to know EXACTLY the best runeword home, locked and
    // hardcoded, even though the forge auto-tasks any legal host') — when the READY base is
    // OFF-META, the BIS homes get the full golden treatment and the ready base is demoted to
    // 'works, but off-meta'. The engine still tasks it (a legal host is a legal host); the CARD
    // now tells the truth about what to hunt.
    var idl;
    if (t.ideal) idl = '<span class="f-ideal" title="'+_fEsc(t.bestMeta)+'">✓ ideal base</span>';
    else if (t.bestStr){
      var _metaNames = String(t.bestStr).split(/\s*\/\s*/).map(function(x){ return x.trim(); }).filter(Boolean);
      var _onMeta = _metaNames.some(function(nm){ return nm.toLowerCase() === String(t.base.base||'').toLowerCase(); });
      if (_onMeta) idl = '<span class="f-alt" title="'+_fEsc(t.bestMeta)+'">meta base: '+_fEsc(t.bestStr)+'</span>';
      else idl = '<span class="f-offmeta" title="your ready base is a LEGAL host, but not the word\'s best home — forge there only if you won\'t hunt the 🏆">⚠ works, but OFF-META</span> '
        + '<span class="f-bisline">🏆 BIS home: '+_metaNames.map(function(nm,i){ return '<span class="f-getchip f-getchip-base'+(i===0?' f-getchip-ideal':'')+'" data-arttip="'+_fEsc(nm)+'" style="color:'+(_qC(nm)||'var(--q-normal)')+'">'+(i===0?'🏆 ':'')+_fEsc(nm)+((typeof _baseRoleBadge==='function')?_baseRoleBadge(nm, i===0):'')+'</span>'; }).join('')+'</span>';
    } else idl = '';
    return '<b>'+t.base.sockets+'os '+_fEsc(t.base.base)+'</b>'+(t.base.eth?' <span class="f-eth">⊘ eth</span>':'')+(t.base.sup?' <span class="f-sup">superior</span>':'')+' '+idl
      + _consumedNote(t.base.name);   // v624 — "its twin already became Kingslayer; this uses a REMAINING copy"
  }

  var _forgeFilter='all';   // mutually-exclusive sub-tab filter: all | now | pipeline | onestep | crafts
  window.forgeSetFilter=function(f){ _forgeFilter=(f===_forgeFilter && f!=='all')?'all':f; renderForge(); };
  // v660 — "✓ got the base" (Konyo: 'lets say i did get a runeword base… clicking i have the base with a
  // checkmark style and then it automatically ascends to MAKE NOW'). Registers the card's recommended base
  // at the word's exact socket count (the same registry the AI intake writes: owned + EXTRA_ITEMS socketed
  // entry), re-scans, and jumps the view to where the word ACTUALLY landed — ⚒ Make now when the engine
  // agrees, honestly elsewhere when reservations/base-sharing re-task it (v604/v612 no-false-claims doctrine).
  window.forgeGotBase=function(btn,rw,base,need){
    try {
      var label=base+' ('+need+'os)';
      if (typeof window._ensureSocketBaseEntry==='function') window._ensureSocketBaseEntry(label);
      try { owned.add(label); } catch(e){}
      try { window.LSR.setItem('d2r_owned', JSON.stringify(Array.from(owned))); } catch(e){}
      var landed=''; try { var sc=window.forgeScan();
        if ((sc.now||[]).some(function(t){return t.rw===rw && !t.deferred;})) landed='now';
        else if ((sc.pipeline||[]).some(function(t){return t.rw===rw;})) landed='pipeline';
        else if ((sc.onestep||[]).some(function(t){return t.rw===rw;})) landed='onestep'; } catch(e){}
      try { if (typeof _motionOK!=='function' || _motionOK()){
        var _t=document.createElement('div'); _t.className='forge-toast'; _t.innerHTML='🛒 <b>'+esc(label)+'</b> registered <span class="ft-sub">'+(landed==='now'?('⚒ '+esc(rw)+' ascended to MAKE NOW'):('the Forge re-tasked '+esc(rw)))+'</span>';
        (function(el){var st=document.getElementById('forge-toasts');if(!st){st=document.createElement('div');st.id='forge-toasts';document.body.appendChild(st);}st.appendChild(el);})(_t); setTimeout(function(){ _t.classList.add('out'); setTimeout(function(){ _t.remove(); },450); }, 2400);
      } } catch(e){}
      _forgeFilter=(landed==='now')?'now':'all'; renderForge();
    } catch(e){ try { renderForge(); } catch(e2){} }
  };

  // v542 — the "base upgrade chain" is GONE for good. White / normal / superior bases CANNOT be cube-upgraded to
  // a higher tier — only unique / rare / set can (game-file cubemain.txt). The Forge only ever Larzuk-sockets the
  // base you own (or names the right-tier base to FIND in a One-step). No _upgradeChainFor, no upgrade bucket.
  // step progress for multi-step chains (persisted): the current atomic step shown in Make Now.
  function _stepGet(k){ try{ return (JSON.parse(window.LSR.getItem('d2r_forgeStep')||'{}')[k])||0; }catch(e){ return 0; } }
  function _stepSet(k,v){ try{ var o=JSON.parse(window.LSR.getItem('d2r_forgeStep')||'{}'); if(v<=0)delete o[k]; else o[k]=v; window.LSR.setItem('d2r_forgeStep',JSON.stringify(o)); }catch(e){} }
  // v558 — MOTION LAYER (Fable-5 "lively" pass). All action buttons animate the card first, THEN act. Instant
  // under automation (navigator.webdriver) so specs stay deterministic, and inert under prefers-reduced-motion.
  function _motionOK(){ try { return !navigator.webdriver && !(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches); } catch(e){ return true; } }
  function _animThen(el, cls, ms, fn){
    if (!_motionOK()){ fn(); return; }
    try {
      var card = el && el.closest ? (el.closest('.f-card') || el.closest('.forge-hero')) : null;   // v618 — the hero celebrates like a card
      if (!card){ fn(); return; }
      card.classList.add(cls);
      if (cls==='f-anim-forged'){ // v606 — spark burst + golden shockwave ring on completion
        for (var i=0;i<12;i++){ var s=document.createElement('span'); s.className='f-spark'+(i%3===0?' f-ember':''); s.style.setProperty('--dx',(Math.random()*170-85)+'px'); s.style.setProperty('--dy',(-30-Math.random()*85)+'px'); s.style.animationDelay=(Math.random()*110)+'ms'; card.appendChild(s); }
        var rg=document.createElement('span'); rg.className='f-ring'; card.appendChild(rg);
      }
      setTimeout(fn, ms);
    } catch(e){ fn(); }
  }
  window.forgeDoneAnim=function(el,name,baseHint){ _animThen(el,'f-anim-forged',430,function(){ if(window.rwToggleMade) window.rwToggleMade(name,baseHint); }); };   // v626 — the clicked card's base rides along
  window.forgeForgedAnim=function(el,chainKey,word){ _animThen(el,'f-anim-forged',430,function(){ window.forgeForged(chainKey,word); }); };
  window.forgeSkipAnim=function(el,key){ _animThen(el,'f-anim-skip',260,function(){ window.forgeSkip(key); }); };
  window.forgeAdvanceAnim=function(el,k,total){ _animThen(el,'f-anim-step',230,function(){ window.forgeAdvance(k,total); }); };
  window.forgeAdvance=function(k,total){ var s=_stepGet(k)+1; _stepSet(k, s>=total?0:s); if(typeof renderForge==='function') renderForge(); };
  window.forgeStepBack=function(k){ _stepSet(k, Math.max(0,_stepGet(k)-1)); if(typeof renderForge==='function') renderForge(); };   // v597 — undo a mis-clicked "did it"
  // v531 — the FINAL step of a chain is "Forge <word>". Ticking it = the runeword is CREATED: mark it in the
  // Chronicle (so it leaves the Forge for good), reset the chain's step, and re-render. Was calling forgeAdvance
  // which just looped back to step 1 — a finished chain never actually completed (Konyo caught this).
  window.forgeForged=function(chainKey, word){ try{ _stepSet(chainKey,0); }catch(e){} var _hint=String(chainKey||'').replace(/^chain\|/,'');
    if(window.rwToggleMade){ window.rwToggleMade(word, _hint||undefined); } else if(typeof renderForge==='function'){ renderForge(); } };   // v626 — the chain IS the base: consume exactly it
  // skip / dismiss: ✕ a task you don't want now. Persisted in d2r_forgeSkip. Skipping a chain's forge-step word
  // (key 'rw|<word>') reveals the next word on that base; skipping a whole task hides it. Restorable.
  function _skipSet(){ try{ return new Set(JSON.parse(window.LSR.getItem('d2r_forgeSkip')||'[]')); }catch(e){ return new Set(); } }
  window.forgeSkip=function(key){ var s=_skipSet(); s.add(key); try{ window.LSR.setItem('d2r_forgeSkip', JSON.stringify(Array.from(s))); }catch(e){} if(typeof renderForge==='function') renderForge(); };
  window.forgeUnskipAll=function(){ try{ window.LSR.removeItem('d2r_forgeSkip'); }catch(e){} if(typeof renderForge==='function') renderForge(); };
  // v532 — ✓ COMPLETED tab. Created runewords live in the Chronicle (rwMade); the Completed tab mirrors them
  // as an end-of-storyline "done" list. "Clear" DISMISSES them from this view (d2r_forgeDone — NON-destructive,
  // they stay created in the Chronicle); "Restore" un-dismisses + un-skips. Per-row ↺ un-marks (back to tasks).
  function _doneSet(){ try{ return new Set(JSON.parse(window.LSR.getItem('d2r_forgeDone')||'[]')); }catch(e){ return new Set(); } }
  function _madeRw(){ try{ return Object.keys((typeof rwMade!=='undefined'&&rwMade)||{}).filter(function(n){ return typeof RUNEWORD_TIP!=='undefined'&&RUNEWORD_TIP[n]; }); }catch(e){ return []; } }
  window.forgeDismissDone=function(name){ var s=_doneSet(); s.add(name); try{ window.LSR.setItem('d2r_forgeDone', JSON.stringify(Array.from(s))); }catch(e){} if(typeof renderForge==='function') renderForge(); };
  window.forgeClearCompleted=function(){ try{ window.LSR.setItem('d2r_forgeDone', JSON.stringify(_madeRw())); }catch(e){} if(typeof renderForge==='function') renderForge(); };
  window.forgeRestoreCompleted=function(){ try{ window.LSR.removeItem('d2r_forgeDone'); window.LSR.removeItem('d2r_forgeSkip'); }catch(e){} if(typeof renderForge==='function') renderForge(); };
  function _forgeDate(s){ try{ return Date.parse(String(s||'').replace(/\s*·\s*/,' ').replace(/,/,'')) || 0; }catch(e){ return 0; } }
  // v537.3 — the "↩ Undo last" button is now SESSION-scoped: it names only what you've created THIS SESSION,
  // and disappears on reload. _sessDone is an in-memory stack of runewords marked created this session (via the
  // Forge "✓ created" / "✓ forged" buttons or the Chronicle toggle — all route through rwToggleMade → _noteForgeDone).
  // So the bar is a fresh "you just did that → undo it" prompt, NOT a permanent affordance hovering over your
  // genuinely-last-created runeword (Konyo: "make it only show after I complete something").
  var _sessDone=[];
  function _noteForgeDone(name, made){ if(!name) return; var i=_sessDone.indexOf(name); if(i>=0) _sessDone.splice(i,1); if(made) _sessDone.push(name); if(typeof renderForge==='function') renderForge(); }
  try{ window._noteForgeDone=_noteForgeDone; }catch(e){}
  function _lastDone(){ try{ var rm=(typeof rwMade!=='undefined'&&rwMade)||{};
    for(var i=_sessDone.length-1;i>=0;i--){ if(rm[_sessDone[i]]) return _sessDone[i]; }   // newest still-created this session
  }catch(e){} return null; }
  window.forgeUndoLastDone=function(){ var n=_lastDone(); if(n && window.rwToggleMade) window.rwToggleMade(n); };   // un-marks it → back into tasks (rwToggleMade → _noteForgeDone pops it off the stack) + re-renders

  // CRAFT ACCORDION (v495): a craft card opens an in-tab collapsing dropdown of its slots + recipes,
  // each marked ✓ make-now (gem + rune in hand) or "need <rune>". Never routes to the Workshop.
  var _craftOpen={};
  window.forgeCraftToggle=function(ck){ _craftOpen[ck]=!_craftOpen[ck]; if(typeof renderForge==='function') renderForge(); };
  window.forgeLegendToggle=function(){ var p=document.getElementById('forge-legend-pop'); if(p) p.classList.toggle('open'); };
  // full slot list for a craft type (from the CRAFTS table), with ready-now status per slot.
  function _craftSlots(ck){
    if (typeof CRAFTS==='undefined' || !CRAFTS) return null;
    var c=null; CRAFTS.forEach(function(x){ if(x.key===ck) c=x; });
    if (!c || !c.slots) return null;
    // Konyo: curate to the recommended/jackpot slots (c.best) — the crafts actually worth making —
    // not every possible slot. Falls back to all slots only if a craft has no curated list.
    var slotKeys=(c.best && c.best.length) ? c.best.filter(function(sl){ return c.slots[sl]; }) : Object.keys(c.slots);
    var rows=slotKeys.map(function(slot){
      var rec=c.slots[slot]||{}, has=(typeof _runeCount==='function'?_runeCount(rec.rune):0)>=1;
      return { slot:slot, rune:rec.rune, base:rec.base, ready:has };
    });
    rows.sort(function(a,b){ return (b.ready?1:0)-(a.ready?1:0) || a.slot.localeCompare(b.slot); });
    return { c:c, rows:rows, readyN:rows.filter(function(r){return r.ready;}).length, total:rows.length };
  }
  // v510 — HD item art per craft slot (Konyo: "HD art like in-game for Amulet/Belt/Gloves/Ring + all").
  // Representative HD sprite per slot type + a tooltip name that resolves to that art. Map the jewelry
  // slot names into D2IO_ART (additive) so their floating data-arttip tooltips resolve too.
  try { if (typeof D2IO_ART!=='undefined'){ if(!D2IO_ART['Amulet'])D2IO_ART['Amulet']='art/hd_amulet.png'; if(!D2IO_ART['Ring'])D2IO_ART['Ring']='art/hd_ring.png'; if(!D2IO_ART['Gloves'])D2IO_ART['Gloves']='art/hd_gloves_l.png';
    // v518 — jewel art (a magic-blue jewel sprite) so the craft "a jewel" ingredient shows an HD icon +
    // a magic-blue floating tooltip image, exactly like the Amulet/Ring slots. _tipTint already → magic blue.
    if(!D2IO_ART['any jewel'])D2IO_ART['any jewel']='art/jewel02_graphic.png'; if(!D2IO_ART['Jewel'])D2IO_ART['Jewel']='art/jewel02_graphic.png'; } } catch(e){}
  var _JEWEL_ART='art/jewel02_graphic.png';
  // v513 — all GOOD hd_ files (base_boots/base_belt were the v497 corrupt blue-gem placeholders). Tooltip
  // names point at the SAME good art so the floating cursor card matches the row image (not a blue gem).
  var _SLOT_REP={Amulet:'art/hd_amulet.png',Ring:'art/hd_ring.png',Gloves:'art/hd_gloves_l.png',Belt:'art/hd_light_belt.png',Boots:'art/hd_chain_boots.png',Helm:'art/hd_helm.png',Shield:'art/hd_kite_shield.png','Body Armor':'art/hd_light_plate.png',Weapon:'art/hd_crystal_sword.png'};
  var _SLOT_TIP={Amulet:'Amulet',Ring:'Ring',Gloves:'Gloves',Belt:'Light Belt',Boots:'Chain Boots',Helm:'Helm',Shield:'Kite Shield','Body Armor':'Light Plate',Weapon:'Crystal Sword'};
  // color = the craft type's colour (Caster=amethyst, Blood=ruby, Safety=emerald, Hit Power=sapphire) so the
  // slot art glows in that "caster colour" (Konyo: sync each craft slot to its gem colour).
  function _slotArtImg(slot,color){ var src=_SLOT_REP[slot]; if(!src) return ''; return '<span class="f-slotart" data-arttip="'+_fEsc(_SLOT_TIP[slot]||slot)+'"'+(color?' style="--sc:'+_fEsc(color)+'"':'')+'><img src="'+src+'" alt="" loading="lazy"></span>'; }
  // v516 — EVERY craft ingredient (rune · base options · jewel) gets its own HD art icon + a floating
  // cursor tooltip (Konyo: "all ingredients need image art0r HD and image floating cursor tooltips").
  // Bases reuse the GOOD slot HD sprite + a "magic <slot> base" rich tooltip (the corrupt base_*.png
  // blue-gem placeholders are never touched). Rune art = hd_<rune>_rune.png, resolves its rich rune card.
  function _cingRune(rune){
    var a=_fArt(rune);   // hd_<rune>_rune.png — good art
    var img = a ? '<img class="f-cing-img" src="'+a+'" alt="" loading="lazy">' : '<span class="f-cing-gl f-cing-gl-r">ᚱ</span>';
    return '<span class="f-cing f-cing-rune" data-arttip="'+_fEsc(rune)+'">'+img+'<b>'+_fEsc(rune)+'</b></span>';
  }
  function _cingBase(baseStr, slot){
    var src=_SLOT_REP[slot]||'';   // representative GOOD HD slot sprite (never a corrupt base_)
    var img = src ? '<img class="f-cing-img" src="'+src+'" alt="" loading="lazy">' : '';
    var names = String(baseStr).split('·').map(function(b){ return '<span class="f-cbn">'+_fEsc(b.trim())+'</span>'; }).join('<span class="f-cdot">·</span>');
    // data-arttip resolves to the rich "magic <slot> base" card (all options + gem icons), no corrupt art
    return '<span class="f-cing f-cing-base" data-arttip="'+_fEsc('magic '+slot+' base')+'">'+img+'<span class="f-cbnames">'+names+'</span></span>';
  }
  function _cingJewel(){
    // data-arttip "any jewel" → rich jewel card (magic-blue title via _tipTint) + HD jewel art image.
    var jimg = _JEWEL_ART ? '<img class="f-cing-img" src="'+_JEWEL_ART+'" alt="" loading="lazy">' : '<span class="f-cing-gl f-cing-gl-j">◈</span>';
    return '<span class="f-cing f-cing-jewel" data-arttip="any jewel">'+jimg+'a jewel</span>';
  }
  // one collapsible craft card (header always shown; body only when open).
  function _craftAccHtml(ck, col){
    var d=_craftSlots(ck); if(!d) return '';
    var c=d.c, open=!!_craftOpen[ck], cc=_fEsc(col||c.color||'#b48ce0');
    var art=(typeof artOr==='function')?artOr(c.gem,'<span style="font-size:22px;color:'+cc+'">💎</span>','lg'):'<span style="font-size:22px;color:'+cc+'">💎</span>';
    var h='<div class="f-craftacc'+(open?' open':'')+'" style="--cw-c:'+cc+'">';
    h+='<div class="f-craftacc-h" role="button" tabindex="0" aria-expanded="'+(open?'true':'false')+'" data-arttip="'+_fEsc(c.gem)+'" title="'+_fEsc(ck)+' craft — tap to '+(open?'collapse':'see every slot + recipe')+'" onclick="window.forgeCraftToggle(\''+_fJs(ck)+'\')">';
    h+='<span class="f-craftacc-chev">'+(open?'▾':'▸')+'</span>'+art;
    h+='<div class="f-craftacc-t"><span class="f-craftacc-name">Create '+_fEsc(ck)+(c.star?' <span class="cw-tile-star">★ YOURS</span>':'')+'</span><span class="f-craftacc-sub">'+_fEsc(c.gem)+' · '+_fEsc(c.tell||'')+'</span></div>';
    h+='<span class="f-craftacc-badge'+(d.readyN?' has':'')+'">'+d.readyN+' / '+d.total+' make now</span>';
    h+='<button class="f-skip" title="skip '+_fEsc(ck)+' crafts" onclick="event.stopPropagation();window.forgeSkip(\'craft|'+_fJs(ck)+'\')">✕</button>';
    h+='</div>';
    if (open){
      h+='<div class="f-craftacc-body">';
      d.rows.forEach(function(r){
        h+='<div class="f-craftrow'+(r.ready?' ready':' locked')+'">'
          +_slotArtImg(r.slot, cc)
          +'<span class="f-craftrow-slot" style="color:var(--q-orange,#ffa800)">'+_fEsc(r.slot)+'</span>'
          +'<span class="f-craftrow-rec">'+_cingRune(r.rune)+'<span class="f-cplus">+</span>magic '+_cingBase(r.base, r.slot)+'<span class="f-cplus">+</span>'+_cingJewel()+'</span>'
          +'<span class="f-craftrow-st">'+(r.ready?'✓ make now':'need '+_fEsc(r.rune))+'</span>'
          +'</div>';
      });
      h+='</div>';
    }
    return h+'</div>';
  }

  // DO-NOW feed: flatten the plan into an ordered, atomic next-move list (the login orientation).
  function _doNowItems(s){
    var items=[];
    s.now.filter(function(t){return !t.deferred;}).forEach(function(t){
      items.push({kind:'now', cta:t.rw, steps:['Forge <b>'+_fEsc(t.rw)+'</b> in your <b>'+t.base.sockets+'os '+_fEsc(t.base.base)+'</b> — runes in hand.']});
    });
    s.pipeline.forEach(function(t){
      var steps=[], target=t.base.base;
      if (t.cubeGamble) steps.push('🎲 Cube-socket your <b>'+_qArt(target)+'</b> — random 1–'+t.base.max+' sockets; re-roll until it hits <b>'+t.need+'os</b> (Larzuk overshoots to '+t.base.max+')');
      else steps.push('Larzuk-socket your <b>'+_qArt(target)+'</b> → <b>'+t.need+'os</b> (guaranteed max)');
      steps.push((t.sub==='cube'?'Cube up <b>'+_fEsc((t.missing||[]).join(', '))+'</b>, then forge ':'Forge ')+'<b>'+_qArt(t.rw)+'</b>');
      items.push({kind:'pipe', cta:t.rw, steps:steps});
    });
    s.crafts.slice(0,4).forEach(function(c){
      items.push({kind:'craft', steps:['Craft a <b>'+_fEsc(c.craft)+' '+_fEsc(c.slot)+'</b> — you hold <b>'+_fEsc(c.gem)+'</b> + <b>'+_fEsc(c.rune)+'</b>; buy a magic '+_qArt(c.base)+' from a vendor + add a jewel.']});
    });
    s.onestep.slice(0,3).forEach(function(t){
      var txt = t.sub==='base' ? 'Get a <b>'+_qArtList(t.bestStr||t.baseReq)+'</b> base for <b>'+_qArt(t.rw)+'</b> — runes already in hand'
              : t.sub==='cube' ? 'Cube up <b>'+_fEsc((t.missing||[]).join(', '))+'</b>, then forge <b>'+_qArt(t.rw)+'</b>'
              : 'Get <b>'+_fEsc((t.missing||[]).join(', '))+'</b> for <b>'+_qArt(t.rw)+'</b>';
      items.push({kind:'step', cta:t.rw, steps:[txt]});
    });
    return items;
  }

  function renderForge(){
    var box=document.getElementById('forge-body'); if(!box) return;
    var s=forgeScan(); var H=[];
    var liveNow=s.now.filter(function(t){return !t.deferred;});
    var deferred=s.now.filter(function(t){return t.deferred;});
    var total=liveNow.length+s.pipeline.length+s.onestep.length+s.crafts.length;
    // Make-now is now the ATOMIC feed: ready forges + crafts + ONE entry per pipeline base-group (the chain's current step)
    var skip=_skipSet();   // v532 — computed once so the restore bar shows on EVERY sub-tab, not just Make now (v684: moved up — the ⚒ pill must apply the SAME skip rules as the body)
    // v684 — pipeline groups key on base+NEED+mode, not base alone: one owned base can legally carry a
    // Larzuk task (need===max) AND a cube-gamble task (need<max); grouping them on one card mixed the
    // socket counts and could instruct a destructive wrong-count Larzuk (v597 chain-sanity class).
    var _pipeGroups={}; s.pipeline.forEach(function(t){ var gk=t.base.name+'|'+t.need+'|'+(t.cubeGamble?'g':'l'); (_pipeGroups[gk]=_pipeGroups[gk]||[]).push(t); });
    var _craftTypes={}; s.crafts.forEach(function(c){ _craftTypes[c.craft]=1; });   // group crafts by TYPE (Caster/Blood/…), not slot
    // v684 — the ⚒ pill counts EXACTLY what the section body will render (skip-filtered): skipped words,
    // skipped chains, chains whose every word is skipped, and skipped craft types all leave the count.
    var nowCount = liveNow.filter(function(t){ return !skip.has('rw|'+t.rw); }).length
      + Object.keys(_craftTypes).filter(function(ck){ return !skip.has('craft|'+ck); }).length
      + Object.keys(_pipeGroups).filter(function(gk){ if (skip.has('chain|'+gk)) return false; return _pipeGroups[gk].some(function(t){ return !skip.has('rw|'+t.rw); }); }).length;
    var F=_forgeFilter, show=function(k){ return F==='all'||F===k; };
    H.push('<div class="forge-head"><div class="forge-title">🔨 Forge</div>'
      +'<div class="forge-sub">Your live task plan — synced to Runes · Gems · Vault · Chronicle. Mark anything ✓ created and it leaves this list automatically.</div></div>');
    // v552 — slim Chronicle progress meter (at-a-glance "how far am I" — the dashboard's north-star bar)
    try {
      var _rwTotal=(typeof RUNEWORD_TIP!=='undefined')?Object.keys(RUNEWORD_TIP).length:100;
      var _rwMadeN=_madeRw().length, _rwPct=_rwTotal?Math.round(_rwMadeN/_rwTotal*100):0;
      H.push('<div class="forge-progress" title="'+_rwMadeN+' of '+_rwTotal+' runewords forged"><div class="fp-track"><div class="fp-fill" style="width:'+_rwPct+'%"></div></div>'
        +'<div class="fp-lbl">📜 <b>'+_rwMadeN+'</b> / '+_rwTotal+' forged<span class="fp-pct">'+_rwPct+'%</span></div></div>');
    } catch(e){}
    // toggle sub-tabs — mutually exclusive filter (pick one → only that bucket shows; click it again → All)
    var tab=function(key,emoji,label,cls,n){
      return '<button class="forge-tab '+cls+(F===key?' on':'')+(n===0?' ft-empty':'')+'" onclick="window.forgeSetFilter(\''+key+'\')" title="show only '+label+'">'
        +'<span class="ft-emoji">'+emoji+'</span><span class="ft-lbl">'+label+'</span><span class="ft-ct">'+n+'</span></button>';
    };
    var _doneHidden=_doneSet(), _doneN=_madeRw().filter(function(n){ return !_doneHidden.has(n); }).length;   // v532
    H.push('<div class="forge-tabs">'
      + tab('all','▦','All','ft-all',total+(s.farm||[]).length)   // v678 (swarm) — the v604 farm catch-all renders on ▦ All; the pill said 0 over 91 cards
      + tab('onestep','🟡','One step','ft-step',s.onestep.length+(s.farm||[]).length)   // v678 — farm rows ride the one-step view   // v531 — storyline order: one step →
      + tab('now','⚒','Make now','ft-now',nowCount)                 //   make now → pipeline (Konyo)
      + tab('pipeline','🔧','Pipeline','ft-pipe',s.pipeline.length)
      + tab('crafts','⚗️','Crafts','ft-craft',s.crafts.length)
      + tab('completed','✅','Completed','ft-done',_doneN)          // v532 — end of the storyline
      +'</div>');

    // v533 — ALWAYS-VISIBLE restore bar. Was buried inside the Make-now section, so skipping your last task
    // (which empties that section) "swallowed" the restore button too. Now it rides under the tabs on every view.
    // v537 — the bar now carries BOTH restores so they're reachable from Make now (not just the Completed tab):
    //   • skipped tasks → Restore skipped   • a just-created runeword → ↩ Undo last: <name> (one-click un-make)
    var _rbits='';
    if (skip.size) _rbits+='<span>↩ <b>'+skip.size+'</b> skipped task'+(skip.size>1?'s':'')+'</span><button class="f-btn f-btn-mini" onclick="window.forgeUnskipAll()">↺ Restore skipped</button>';
    if (F!=='completed'){ var _ld=_lastDone(); if (_ld) _rbits+='<span>✅ <b>'+_doneN+'</b> created</span><button class="f-btn f-btn-mini f-undo-last" title="put your most recently created runeword ('+_fEsc(_ld)+') back into the task list" onclick="window.forgeUndoLastDone()">↩ Undo last: '+_fEsc(_ld)+'</button><button class="f-btn f-btn-mini" onclick="window.forgeSetFilter(\'completed\')" title="see every created runeword — restore or clear any">✅ see all</button>'; }
    if (_rbits) H.push('<div class="forge-restore-top">'+_rbits+'</div>');
    // v546 — "Do this one thing" hero banner: one highest-leverage move, above the cards (not on the Completed view).
    if (F!=='completed'){ var _hero=_forgeHero(s); if (_hero) H.push(_hero); }
    // v634.2 — TOP-of-forge 🪜 pill (Konyo: "the toggle for ladder should be somewhere on the top"):
    // one glance says how many ladder words remain; click toggles the plan preview. v634.3 — when ON,
    // the WHOLE plan section renders right here (top of forge); OFF locks it back to the bottom chips.
    if (F!=='completed' && (s.ladder||[]).length){
      var _lpTop=false; try { _lpTop = localStorage.getItem('d2r_ladderPreview')==='1'; } catch(e){}
      H.push('<div class="forge-restore-top" style="margin-top:6px"><span>🪜 <b>'+s.ladder.length+'</b> ladder-only word'+(s.ladder.length>1?'s':'')+' remain (separate economy — made on your ladder char)</span>'
        +'<button class="f-btn f-btn-mini" onclick="try{localStorage.setItem(\'d2r_ladderPreview\',localStorage.getItem(\'d2r_ladderPreview\')===\'1\'?\'\':\'1\')}catch(e){};try{window.renderForge()}catch(e){}" title="view-only plan preview — nothing is promoted, consumed or re-tasked; toggle back any time">'+(_lpTop?'🪜 hide ladder plans (lock them back)':'🪜 show ladder plans')+'</button>'
        +'<button class="f-btn f-btn-mini" onclick="window.profileSwitch&&window.profileSwitch(\'ladder\')" title="ascend to your 🪜 LADDER account — its own vault, tallies and Chronicle; this main account stays untouched (full reload, zero bleed)">⤴ open the LADDER account</button></div>');
      if (_lpTop){
        H.push('<div class="forge-sec forge-sec-step" id="forge-ladder-strip"><div class="forge-sec-h">🪜 Ladder plans <span class="forge-sec-ct">'+s.ladder.length+'</span>'
          +'<span class="forge-sec-sub">view-only — separate ladder economy; nothing here touches your account. Toggle off to lock them back.</span>'
          +'<button class="f-btn" id="forge-ladder-preview-btn" style="font-size:11px;padding:2px 8px" onclick="try{localStorage.setItem(\'d2r_ladderPreview\',\'\')}catch(e){};try{window.renderForge()}catch(e){}">🪜 hide plans</button></div>');
        s.ladder.forEach(function(t){
          var e=(typeof RUNEWORD_TIP!=='undefined'&&RUNEWORD_TIP[t.rw])||{};
          var legacy=false;   // v651 — Hustle removed from the catalog; no legacy alias remains
          H.push('<div class="f-card f-step forge-ladder-plan" style="padding:7px 10px;opacity:'+(legacy?'.55':'.92')+'"><div class="f-cardbody">'
            +'<div class="f-cardtitle"><span data-arttip="'+_fEsc(t.rw)+'" style="cursor:help;color:'+(_qC(t.rw)||'')+'">'+((typeof window.nameLogo==='function')?window.nameLogo(t.rw):'')+_fEsc(t.rw)+'</span>'
            +' <span class="f-atomsub" style="color:#ffc14d">🪜 ladder-only — plan preview, needs a ladder character</span></div>'
            +(legacy
              ? '<div class="f-atomsub">legacy 3.0 rename — this IS <b>Mania</b> (weapon) / <b>Hysteria</b> (armor); never cube it separately</div>'
              : ('<div class="f-atomrecipe"><span class="f-reclbl">socket in order</span>'+_recipe(t.rw)+'</div>'
                +'<div class="f-atomsub">🛒 base: '+(function(){ var bs=String(_bestBaseStr(t.rw)||'').split(/\s*\/\s*/).map(function(x){return x.trim();}).filter(Boolean); return bs.length? bs.map(function(b){ return '<span class="f-getchip f-getchip-base" data-arttip="'+_fEsc(b)+'" style="color:'+(_qC(b)||'var(--q-normal)')+'" title="'+_fEsc(b)+' — hover for its full card">'+_fEsc(b)+'</span>'; }).join('') + ' <span style="opacity:.7">('+_fEsc(e.b||'')+')</span>' : '<b>'+_fEsc(e.b||'?')+'</b>'; })()+' — farm it AND the runes ON THE LADDER CHAR (separate stash; your tallies here don\'t transfer)</div>'))
            +'</div></div>');
        });
        H.push('</div>');
      }
    }
    // v532 — COMPLETED is a dedicated view (never mixed into 'all'): the done list + clear/restore.
    if (F==='completed'){
      var made=_madeRw().filter(function(n){ return !_doneHidden.has(n); })
        .map(function(n){ return {n:n, d:(rwMade&&rwMade[n])||''}; })
        .sort(function(a,b){ return _forgeDate(b.d)-_forgeDate(a.d) || a.n.localeCompare(b.n); });
      H.push('<div class="forge-sec forge-sec-done"><div class="forge-sec-h">✅ Completed <span class="forge-sec-ct">'+made.length+'</span><span class="forge-sec-sub">runewords you\'ve created — the end of the line</span></div>');
      if (skip.size) H.push('<div class="forge-note">↩ You have <b>'+skip.size+'</b> skipped task'+(skip.size>1?'s':'')+' — <button class="f-btn f-btn-mini" onclick="window.forgeUnskipAll()">↺ restore skipped</button></div>');
      H.push('<div class="f-donetools"><button class="f-btn f-btn-mini" onclick="window.forgeClearCompleted()">✕ Clear list</button><button class="f-btn f-btn-mini" onclick="window.forgeRestoreCompleted()">↺ Restore all</button></div>');
      if (!made.length){
        H.push('<div class="forge-empty">Nothing here yet — forge a runeword and tick <b>✓ created</b>, or hit <b>↺ Restore all</b> to bring back a cleared list.</div>');
      } else {
        made.forEach(function(m){
          H.push('<div class="f-donerow"><span class="f-doneck">✓</span><span class="f-donename" style="color:'+(_qC(m.n)||'')+'">'+_fEsc(m.n)+'</span><span class="f-donedate">'+_fEsc(m.d||'')+'</span>'
            +'<button class="f-donebtn" title="restore '+_fEsc(m.n)+' to your active tasks (un-mark created)" onclick="window.rwToggleMade&&window.rwToggleMade(\''+_fJs(m.n)+'\')">↺ restore</button>'
            +'<button class="f-skip" title="clear from this list (stays created in the Chronicle)" onclick="window.forgeDismissDone(\''+_fJs(m.n)+'\')">✕</button></div>');
        });
      }
      H.push('</div>');
      box.innerHTML=H.join(''); return;
    }
    if (!total && !(s.farm||[]).length){
      // v685 — a SEALED chronicle deserves a seal, not "Nothing queued" over a void where the only
      // visible control was the red erase button. Celebration + where the hunt lives now.
      var _sealedAll = false, _sealN = 0;
      try { var _sT = (typeof RUNEWORD_TIP!=='undefined')?Object.keys(RUNEWORD_TIP).length:0; _sealN = _madeRw().length; _sealedAll = (_sT > 0 && _sealN >= _sT); } catch(e){}
      if (_sealedAll){
        H.push('<div class="forge-sealed"><div class="fs-crest">⚒👑⚒</div>'
          +'<div class="fs-title">Chronicle Sealed</div>'
          +'<div class="fs-sub">Every one of the <b>'+_sealN+'</b> runewords stands forged. The Forge rests —<br>the hunt is pure grail now: bases for trade, uniques &amp; sets for the wall.</div>'
          +'<div class="fs-btns">'
          +'<button class="fs-btn" onclick="switchTab(\'funi\')">🏆 F·Uniques — the grail wall</button>'
          +'<button class="fs-btn" onclick="switchTab(\'fsets\')">🧩 F·Sets — finish the sets</button>'
          +'</div></div>');
      } else {
        H.push('<div class="forge-empty">✅ <b>Nothing queued.</b> Everything your runes, gems & bases can build is already ✓ created in the Chronicle.<br>Tally more runes/gems or intake bases in the Vault to unlock new tasks.</div>');
      }
      box.innerHTML=H.join(''); return;
    }
    // v604 — the empty state above is only TRUE when farm is empty too. With no actionable task but open
    // words remaining (fresh tallies / no bases), saying "everything is ✓ created" was the same lie class
    // as the throw-out "✓ forged" — fall through so 🌾 Furthest out still shows every remaining word.
    if (!total){
      H.push('<div class="forge-empty forge-empty-sm">No actionable task yet — no owned base or ready runes for the words below. Tally runes/gems or intake bases in the Vault; everything still open is listed under 🌾 Furthest out.</div>');
    }
    // ── MAKE NOW — atomic, one-at-a-time tasks. A multi-step chain shows ONLY its current step; tick "✓ did it"
    // and the next step replaces it. Crafts & ready forges are single "boom" tasks. Full chains live in 🔧 Pipeline.
    if (show('now')){
      var atomic=[];   // v532 — reuse the outer `skip` set (computed once, powers the Completed-tab restore too)
      liveNow.forEach(function(t){ if(skip.has('rw|'+t.rw)) return;
        // v540 — surface the BEST/ideal base per runeword even on an OWNED-base make-now, so the endgame isn't
        // framed as "only merc gear". You can still forge it now on the base you own; the card ALSO names the
        // ideal base (a 1H PLAYER weapon for merc-owned words, or the best armor base) — Konyo: "we had ideal /
        // what's best for each runeword". Hidden only when the base you own IS already the ideal.
        var _ownIsBest = t.ideal || (t.bestStr && t.bestStr.split(/\s*\/\s*/).some(function(b){ return b.trim().toLowerCase()===String(t.base.base).toLowerCase(); }));
        var _bestHint = (t.bestStr && !_ownIsBest) ? ' <span class="f-atomsub">· 🏆 best base for <b>'+_qArt(t.rw)+'</b>: <b>'+_qArtList(t.bestStr)+'</b>'+(t.bestMeta?' <span style="opacity:.7">('+_fEsc(t.bestMeta)+')</span>':'')+(t.mercOwn?' — you own the <b>2H merc</b> version; the ideal is a <b>1H player</b> weapon':'')+'</span>' : '';
        atomic.push({icon:'⚒', cls:'now', skipKey:'rw|'+t.rw, artName:t.rw,
        // v557 — LAYERED card (Fable-5 clarity pass): big action line → the RUNE RECIPE in order (the actual
        // in-game how, previously missing from the #1 action card) → dim sub-hints on their own row.
        atoms:[ '<div class="f-atomact">Forge <b class="f-rwbig">'+_qArt(t.rw)+'</b> <span class="f-in">in your</span> <b>'+t.base.sockets+'os '+_qArt(t.base.base)+'</b></div>'
          +'<div class="f-atomrecipe"><span class="f-reclbl">socket in order</span>'+_recipe(t.rw)+'</div>'
          +((t.mercOwn||_bestHint)?('<div class="f-atomsubrow">'+(t.mercOwn?'<span class="f-atomsub">2-handed → a <b>mercenary</b> weapon (you own the base + runes)</span>':'')+_bestHint+'</div>'):'') ],
        btn:'<button class="f-btn f-btn-go" onclick="window.forgeDoneAnim(this,\''+_fJs(t.rw)+'\',\''+_fJs(t.base.name)+'\')">✓ created</button>' }); });
      // upgrade/socket chains GROUPED by the owned base (you upgrade ONE base, then pick a word) → step-by-step.
      // Listed BEFORE crafts — endgame gear progression leads (Konyo's "Upgrade Crystal Sword" is example #1).
      // v684 — reuse the base+need+mode groups built for the pill: every card is internally consistent
      // (one socket count, one Larzuk-vs-cube mode); a mixed base renders one card per need.
      var byBase=_pipeGroups;
      Object.keys(byBase).forEach(function(bn){
        if (skip.has('chain|'+bn)) return;
        var grp=byBase[bn], t0=grp[0], target=t0.base.base, atoms=[];
        if (t0.cubeGamble){
          atoms.push('<div class="f-atomact">🎲 Cube-socket your <b>'+_qArt(target)+'</b> — random 1–'+t0.base.max+' sockets</div>'
            +'<div class="f-atomrecipe"><span class="f-reclbl">cube recipe</span><span class="f-cube">'+_cubeGambleRecipe(target)+'</span></div>'
            +'<div class="f-atomsubrow">gamble for <b>'+t0.need+'os</b> · Larzuk overshoots to '+t0.base.max+' · re-roll until it hits '+t0.need+'</div>');
        } else {
          var _forWords=grp.map(function(t){return t.rw;}).filter(function(w2){return !skip.has('rw|'+w2);}).slice(0,3);
          atoms.push('<div class="f-atomact">Larzuk-socket your <b>'+(t0.base.eth?'ethereal ':'')+_qArt(target)+'</b> → <b>'+t0.need+'os</b>'+(_forWords.length?' <span class="f-atomsub">— for <b>'+_forWords.map(function(w2){return _qArt(w2);}).join(', ')+'</b>'+(grp.length>_forWords.length?' +'+(grp.length-_forWords.length):'')+'</span>':'')+'</div>'
            +(t0.base.eth?'<div class="f-atomsubrow">⊘ ethereal — socket &amp; forge it as-is. An eth no-repair runeword is ideal for an <b>Act 5 (Barbarian) mercenary</b>.</div>':'')
            +_consumedNote(t0.base.name));   // v625 (Konyo: "I socketed a 6os blade… it just disappeared?!") — after a sibling forge resets this shared chain, SAY that the previous copy became that word: this step means Larzuk ANOTHER copy (or tap 'did it' if you already have one socketed in-game)
        }
        // final step: ONE word at a time (top non-skipped). ✕-ing it reveals the next word on this base.
        var words=grp.map(function(t){return t.rw;}).filter(function(w){return !skip.has('rw|'+w);});
        if(!words.length) return;   // every word for this base skipped → drop the chain
        var topWord=words[0];
        // v597 — the final step NAMES ITS BASE ("which item is this exactly referencing?" — Konyo couldn't
        // tell his step-2/2 "Forge Wisdom" card meant the Bone Visage; step 1 named it, step 2 didn't).
        atoms.push('<div class="f-atomact">Forge <b class="f-rwbig">'+_qArt(topWord)+'</b> <span class="f-in">in your Larzuk’d '+t0.need+'os</span> <b>'+_qArt(target)+'</b></div>'
          +'<div class="f-atomrecipe"><span class="f-reclbl">socket in order</span>'+_recipe(topWord)+'</div>'
          +(words.length>1?'<div class="f-atomsubrow">'+(words.length-1)+' more word'+(words.length>2?'s':'')+' fits this base — ✕ to see the next</div>':''));
        atomic.push({icon:'🔧', cls:'pipe', chainKey:'chain|'+bn, atoms:atoms, forgeWordKey:'rw|'+topWord, artName:topWord});
      });
      // crafts → grouped into ~4 gem-titled tiles (Caster/Blood/Safety/Hit Power), Workshop .cw-tile style.
      var craftGroups={}; s.crafts.forEach(function(c){ (craftGroups[c.craft]=craftGroups[c.craft]||[]).push(c); });
      var craftKeys=Object.keys(craftGroups).filter(function(ck){ return !skip.has('craft|'+ck); });
      if (atomic.length || craftKeys.length){
        H.push('<div class="forge-sec forge-sec-now"><div class="forge-sec-h">⚒ Make now <span class="forge-sec-ct">'+(atomic.length+craftKeys.length)+'</span><span class="forge-sec-sub">one task at a time — do it, tick it, the next appears · ✕ to skip</span></div>');
        atomic.forEach(function(a){
          var total=a.atoms.length, step=a.chainKey?Math.min(_stepGet(a.chainKey),total-1):0, isLast=step>=total-1;
          var prog = total>1 ? '<span class="f-atomprog">step '+(step+1)+' / '+total+'</span>' : '';
          var btn;
          if (a.chainKey){
            if (isLast && a.forgeWordKey){
              // last step = "Forge <word>" → ticking it CREATES the runeword (marks it made, it leaves the list)
              var _fw = a.forgeWordKey.replace(/^rw\|/,'');
              btn = '<button class="f-btn f-btn-go" onclick="window.forgeForgedAnim(this,\''+a.chainKey+'\',\''+_fJs(_fw)+'\')">✓ forged — done</button>';
            } else {
              btn = '<button class="f-btn f-btn-go" onclick="window.forgeAdvanceAnim(this,\''+a.chainKey+'\','+total+')">✓ did it → next</button>';
            }
          } else { btn = a.btn; }
          var sk = a.chainKey ? (isLast && a.forgeWordKey ? a.forgeWordKey : a.chainKey) : a.skipKey;
          var skipBtn = sk ? '<button class="f-skip" title="not now — skip this'+(isLast&&a.forgeWordKey?' word (show the next)':'')+'" onclick="window.forgeSkipAnim(this,\''+_fJs(sk)+'\')">✕</button>' : '';
          // v597 — a mis-advanced chain was UNFIXABLE in the UI (a stale "did it" left Konyo stuck at step
          // 2/2 with no way back). Any chain past step 1 gets a small ↺ to walk back one step.
          var backBtn = (a.chainKey && step>0) ? ' <button class="f-btn f-btn-mini" title="go back a step — I didn’t actually do the previous one" onclick="window.forgeStepBack(\''+a.chainKey+'\')">↺ back</button>' : '';
          var _atomArt = a.artName ? _rwArt(a.artName) : ('<span class="f-atomic-ic">'+a.icon+'</span>');
          H.push('<div class="f-card f-'+a.cls+' f-atom" data-arttip="'+_fEsc(a.artName||'')+'">'+skipBtn+'<div class="f-cardart f-cardart-hd">'+_atomArt+'<span class="f-cardart-badge">'+a.icon+'</span></div><div class="f-cardbody">'
            +'<div class="f-cardtitle">'+a.atoms[step]+'</div>'+prog
            +'<div class="f-cta">'+btn+backBtn+'</div></div></div>');
        });
        if (craftKeys.length){
          var ct='';
          craftKeys.forEach(function(ck){ var c0=craftGroups[ck][0]; ct+=_craftAccHtml(ck, c0&&c0.color); });
          H.push('<div class="forge-craftnow-lbl">⚗️ Crafts ready — tap one to see every slot + recipe (✓ = make now)</div><div class="forge-craftacc">'+ct+'</div>');
        }
        

        H.push('</div>');
      }
      if (deferred.length){
        H.push('<div class="forge-sec forge-sec-defer"><div class="forge-sec-h">⏸ Next up <span class="forge-sec-ct">'+deferred.length+'</span><span class="forge-sec-sub">ready too — frees up once a shared base/rune above is used</span></div>');
        deferred.forEach(function(t){ H.push('<div class="f-card f-defer"><div class="f-cardbody"><div class="f-cardtitle"><span data-arttip="'+_fEsc(t.rw)+'" style="cursor:help;color:'+(_qC(t.rw)||'')+'">'+_fEsc(t.rw)+'</span></div><div class="f-cardmeta">'+(t.rsvFor?('🛡 Your <b>'+_qName(t.blockedBase||'base')+'</b> is <b>earmarked for '+_qArt(t.rsvFor)+'</b> — the only base class that word can live in. This word has other homes: get another base.'):('Shares your <b>'+_qName(t.blockedBase||(t.blockedBy||[]).join(', ')||'resource')+'</b> with a higher-value forge above.'))+'</div></div></div>'); });
        H.push('</div>');
      }
    }
    // PIPELINE
    if (show('pipeline') && s.pipeline.length){
      H.push('<div class="forge-sec forge-sec-pipe"><div class="forge-sec-h">🔧 Forge pipeline <span class="forge-sec-ct">'+s.pipeline.length+'</span><span class="forge-sec-sub">socket the base, then forge</span></div>');
      // CONTENTION NOTE: several runewords that upgrade/consume the SAME owned base — you can make one per base.
      var _shareCount={}; s.pipeline.forEach(function(t){ _shareCount[t.base.name]=(_shareCount[t.base.name]||0)+1; });
      Object.keys(_shareCount).forEach(function(bn){ if(_shareCount[bn]>1){ var b=(s.pipeline.filter(function(t){return t.base.name===bn;})[0]||{}).base||{};
        H.push('<div class="forge-note">⚠ '+_shareCount[bn]+' of these consume your <b>'+_fEsc(b.base||bn)+'</b> (you own '+(b.count||1)+') — socketing it makes <b>one</b> runeword. Grab another '+_fEsc(b.base||'base')+' (common white drop) for each extra.</div>'); } });
      s.pipeline.forEach(function(t){
        // Pipeline = you own the socket-correct base; Larzuk it to max, then forge. (No cube-upgrade path exists —
        // white/normal/superior bases can't be tier-upgraded; the base you own already has the right max.)
        var target=t.base.base, n=1, steps='';
        if (t.cubeGamble){
          steps+='<div class="f-step"><span class="f-stepn">'+(n++)+'</span> 🎲 <b>Cube-socket</b> your <b>'+_qArt(target)+'</b> — <span class="f-cube">'+_cubeGambleRecipe(target)+'</span> gives a <b>random 1–'+t.base.max+'</b> sockets. Larzuk would overshoot to '+t.base.max+', so <b>re-roll the cube until it lands '+t.need+'os</b>. '+_gambleAfford(target, t.need, t.base.max)+'</div>';
        } else {
          steps+='<div class="f-step"><span class="f-stepn">'+(n++)+'</span> Larzuk-socket your <b>'+_qArt(target)+'</b>'+(t.ideal?' <span class="f-ideal">✓ ideal base</span>':'')+' → <b>'+t.need+'os</b> (guaranteed max — exactly '+t.need+').'+_consumedNote(t.base.name)+'</div>';
        }
        steps+='<div class="f-step"><span class="f-stepn">'+(n++)+'</span> Forge <b>'+_qArt(t.rw)+'</b> — '+(t.sub==='cube'?('cube up <b>'+_fEsc((t.missing||[]).join(', '))+'</b> first, then forge'):'runes already in hand')+'. <span class="f-recipe-inline">'+_recipe(t.rw)+'</span></div>';
        H.push('<div class="f-card f-pipe"><div class="f-cardart" data-arttip="'+_fEsc(t.base.base)+'">'+((typeof _fArt==='function'&&_fArt(t.base.base))?'<img class="f-art" src="'+_fEsc(_fArt(t.base.base))+'" alt="" loading="lazy">':_rwArt(t.rw))+'</div><div class="f-cardbody">'
          +'<div class="f-cardtitle">Forge <b data-arttip="'+_fEsc(t.rw)+'" style="cursor:help;color:'+(_qC(t.rw)||'')+'">'+((typeof window.nameLogo==='function')?window.nameLogo(t.rw):'')+_fEsc(t.rw)+'</b> '+_handTag(t.hand)+' <span class="f-need">needs '+t.need+'os</span>'+(t.baseOver?' <span class="f-atomsub" style="color:#e9b96e" title="'+(t.rsvFor?_fEsc('your '+t.base.name+' is the only base class '+t.rsvFor+' can ever live in — it is reserved for that word; get another '+t.base.base+' for this one'):'one copy, two words — forge the other word first; this one will re-task as GET another '+_fEsc(t.base.base)+' the moment that copy is consumed')+'">'+(t.rsvFor?'🛡 base earmarked for '+_fEsc(t.rsvFor):'⏳ shares the last copy')+'</span>':'')+'</div>'
          +'<div class="f-steps">'+steps+'</div>'
          +'<div class="f-cta"><button class="f-btn" onclick="window.openDrop&&window.openDrop(\''+_fJs(t.rw)+'\')">📜 card</button></div>'
          +'</div></div>');
      });
      H.push('</div>');
    }
    // ONE STEP AWAY — the directive "go get this → it becomes a Make-now" feed. Items are hover-tooltip chips.
    if (show('onestep') && s.onestep.length){
      H.push('<div class="forge-sec forge-sec-step"><div class="forge-sec-h">🟡 One step away <span class="forge-sec-ct">'+s.onestep.length+'</span><span class="forge-sec-sub">do one → it jumps straight to ⚒ Make now</span></div>');
      var _missChips=function(arr){ return (arr||[]).map(function(m){ var nm=String(m).replace(/^\d+×\s*/,'').trim(); return '<span class="f-getchip" data-arttip="'+_fEsc(nm)+'" title="'+_fEsc(nm)+' rune">'+_fEsc(m)+'</span>'; }).join(''); };
      s.onestep.forEach(function(t){
        // FULL JOURNEY: the whole remaining arc, first step highlighted (do this now) → downstream dimmed.
        var need=(((typeof RUNEWORD_TIP!=='undefined'&&RUNEWORD_TIP[t.rw])||{}).rec||[]).length, segs=[], note='';
        if (t.sub==='cube'){ segs.push('🧪 Cube up '+_missChips(t.missing)); segs.push('⚒ Forge <b>'+_qName(t.rw)+'</b>'); note='base ready ('+_baseLine(t)+')'; }
        else if (t.sub==='runes'){ var top=(t.missing&&t.missing[0])?t.missing[0].replace(/^\d+×\s*/,''):''; segs.push('🔨 Get '+_missChips(t.missing)); segs.push('⚒ Forge <b>'+_qName(t.rw)+'</b>'); note=_fEsc(_runeSource(top))+' · base ready ('+_baseLine(t)+')'; }   // v604 — NAME the ready base (the cube branch already did; Konyo must see WHICH item is waiting)
        else { var bases=String(t.bestStr||t.baseReq||'').split(/\s*\/\s*/); var chips=bases.map(function(bn,bi){ var b=bn.trim(); if(!b) return '';
          // v675 (Konyo: 'emphasize which base is the IDEAL elite best — like Make now does') — the
          // recommended home wears the full golden treatment, the alternates stay quiet chips.
          var _idealCls = bi===0 ? ' f-getchip-ideal' : '';
          return '<span class="f-getchip f-getchip-base'+_idealCls+'" data-arttip="'+_fEsc(b)+'" style="color:'+(_qC(b)||'var(--q-normal)')+'" title="'+_fEsc(b)+(bi===0?' — THE recommended home for this word':' — hover for its card')+'">'+(bi===0?'🏆 ':'')+_fEsc(b)+_baseRoleBadge(b, bi===0)+'</span>'; }).join(''); segs.push('🛒 Get '+chips);
          // v629 — the Forge KNOWS the vault too (Konyo's Stiletto/Ritual): a possible host already
          // read from his stash turns 'go get a base' into 'you may already own one — set its sockets'
          try { var _hm9=window._vaultHostMap();
            if (_hm9.maybe[t.rw]) segs.push('🧰 <b>you may already own a host</b>: <b>'+_fEsc(_hm9.maybe[t.rw][0])+'</b> was read from your stash — its sockets are unset; open its Vault review card and tap the real count');
          } catch(e){}
          if(need){
            // v545 — SOCKET STEP. Larzuk always gives a base's MAX. If that max === the word's count, Larzuk is clean.
            // If the max OVERSHOOTS (e.g. a Flail/Archon Plate maxes at 5/4 but the word needs 4/3), Larzuk can't hit
            // it — you either find a natural drop already at the right count, or cube-socket and gamble for it. Same
            // logic as the owned cube-gamble pipeline task, applied to the "go get a base" step.
            var _fb=(bases[0]||'').trim(); var _fbmax=_fb?(parseInt(_socketMaxFor(_fb),10)||0):0;
            if(_fbmax && _fbmax>need){ var _ghave=(typeof _gemCount==='function')?_gemCount(_cubeGambleGem(_fb)):0; segs.push('🎲 find a <b>'+need+'os</b> drop, or cube-gamble for '+need+' <span class="f-atomsub">(Larzuk gives its max '+_fbmax+'os — too many'+(_ghave>0?'; you hold '+_ghave+' '+_fEsc(_cubeGambleGem(_fb)):'')+')</span>'); }
            else segs.push('🔩 Larzuk → '+need+'os');
          }
          segs.push('⚒ Forge <b style="color:'+(_qC(t.rw)||'')+'">'+_fEsc(t.rw)+'</b>'); note=(t.bestMeta?_fEsc(t.bestMeta)+' · ':'')+'runes in hand'; }
        var journey=segs.map(function(sg,i){ return '<span class="f-jseg'+(i===0?' f-jseg-now':'')+'">'+sg+'</span>'; }).join('<span class="f-jarrow">→</span>');
        var _osBase=String(t.bestStr||'').split(/\s*\/\s*/)[0].trim();   // the FIRST recommended base — what this card actually tells you to get (1H-correct), NOT RW_BEST_BASE (which can be a 2H best-damage base)
        H.push('<div class="f-card f-step"><div class="f-cardart" data-arttip="'+_fEsc(_osBase||t.rw)+'">'+((_osBase && typeof _fArt==='function' && _fArt(_osBase))?'<img class="f-art" src="'+_fEsc(_fArt(_osBase))+'" alt="" loading="lazy">':_rwArt(t.rw))+'</div><div class="f-cardbody">'
          +'<div class="f-cardtitle"><span data-arttip="'+_fEsc(t.rw)+'" style="cursor:help;color:'+(_qC(t.rw)||'')+'">'+((typeof window.nameLogo==='function')?window.nameLogo(t.rw):'')+_fEsc(t.rw)+'</span> '+_handTag(t.hand)+'</div>'
          +'<div class="f-journey">'+journey+'</div>'
          +'<div class="f-getsub">'+note+' · <b>'+segs.length+' step'+(segs.length>1?'s':'')+' to go</b></div>'
          +'<div class="f-recipe">'+_recipe(t.rw)+'</div>'
          +'<div class="f-cta"><button class="f-btn" onclick="window.openDrop&&window.openDrop(\''+_fJs(t.rw)+'\')">📜 card</button>'
          +((t.sub==='base'&&_osBase)?'<button class="f-btn f-btn-go" title="I found/farmed this base — one click registers '+_fEsc(_osBase)+' ('+need+'os) to the vault and the word ascends to ⚒ Make now" onclick="window.forgeGotBase(this,\''+_fJs(t.rw)+'\',\''+_fJs(_osBase)+'\','+need+')">✓ got the base</button>':'')   // v660 — got-the-base ascension
          +'</div>'
          +'</div></div>');
      });
      H.push('</div>');
    }
    // v632 — 🪜 LADDER-LOCKED strip: the Chronicle's remaining count includes these; the Forge must
    // never silently disagree. Read-only chips + the mode toggle for when his character IS ladder.
    // v604 — 🌾 FURTHEST OUT: the coverage catch-all (see forgeScan 2b). Words with NO base owned AND
    // runes not ready used to be SILENT — Konyo's "why is it not tasking me" class. Compact rows, not
    // full cards: every remaining word names the base to find + the runes still missing. Nothing hides.
    if (show('onestep') && (s.farm||[]).length){
      H.push('<div class="forge-sec forge-sec-step"><div class="forge-sec-h">🌾 Furthest out <span class="forge-sec-ct">'+s.farm.length+'</span><span class="forge-sec-sub">need BOTH the base and runes — farm these last; nothing is ever hidden</span></div>');
      var _missChips2=function(arr){ return (arr||[]).slice(0,4).map(function(m){ var nm=String(m).replace(/^\d+×\s*/,'').trim(); return '<span class="f-getchip" data-arttip="'+_fEsc(nm)+'" title="'+_fEsc(nm)+' rune">'+_fEsc(m)+'</span>'; }).join('')+((arr||[]).length>4?' <span class="f-atomsub">+'+((arr||[]).length-4)+' more</span>':''); };
      s.farm.forEach(function(t){
        var b1=String(t.bestStr||t.baseReq||'').split(/\s*\/\s*/)[0].trim();
        // v625 (Konyo's idle-time doctrine: "gambling for the sockets is good when I don't have
        // anything to do") — when the word needs FEWER sockets than the base's max, the plain-white
        // cube gamble is the acquisition path; name it on the row instead of implying Larzuk.
        var _gm=b1?(parseInt(_socketMaxFor(b1),10)||0):0;
        var _gNote=(_gm&&t.need>0&&t.need<_gm)?' · 🎲 <span title="Larzuk would overshoot to '+_gm+'os — cube-gamble a PLAIN WHITE copy ('+_fEsc(_cubeGambleRecipe(b1))+') until it rolls '+t.need+'os — a perfect nothing-else-to-do activity">gamble a plain white for '+t.need+'os</span>':'';
        try { var _hmF=window._vaultHostMap(); if(_hmF.maybe[t.rw]) _gNote+=' · 🧰 <span style="color:#e9b96e" title="a possible host was read from your stash with unknown sockets — set its real count on its Vault review card">possible host in vault: '+_fEsc(_hmF.maybe[t.rw][0])+'</span>'; } catch(e){}   // v629
        H.push('<div class="f-card f-step" style="padding:7px 10px"><div class="f-cardbody">'
          +'<div class="f-cardtitle"><span data-arttip="'+_fEsc(t.rw)+'" style="cursor:help;color:'+(_qC(t.rw)||'')+'">'+((typeof window.nameLogo==='function')?window.nameLogo(t.rw):'')+_fEsc(t.rw)+'</span> '+_handTag(t.hand)+'</div>'
          +'<div class="f-getsub">🛒 base: <span class="f-getchip f-getchip-base" data-arttip="'+_fEsc(b1)+'" style="color:'+(_qC(b1)||'var(--q-normal)')+'">'+_fEsc(b1||t.baseReq||'?')+'</span> · 🔨 runes missing: '+_missChips2(t.missing)+_gNote+'</div>'
          +'</div><div class="f-cta"><button class="f-btn f-btn-go" onclick="window.forgeDoneAnim(this,\''+_fJs(t.rw)+'\',\'\')">✓ created</button></div></div>');   // v655 — farm rows get the full ✓ lifecycle (Konyo forged ladder words off-platform; the Chronicle sync must be one click away EVERYWHERE)
      });
      H.push('</div>');
    }
    if ((s.ladder||[]).length){
      // v634 — TIER-1 LADDER PREVIEW · v634.3 placement (Konyo: "full control of the back-and-forth"):
      // COLLAPSED → this locked chip strip lives here at the bottom. EXPANDED → the whole section
      // (same id, same read-only cards) renders at the TOP of the forge instead (below the 🪜 pill),
      // so toggling visually floods the top and toggling off locks everything back down here.
      // Pure render-order — zero state writes either way (spec-pinned byte-identical).
      var _lpOn2 = false; try { _lpOn2 = localStorage.getItem('d2r_ladderPreview')==='1'; } catch(e){}
      if (!_lpOn2){
        H.push('<div class="forge-sec forge-sec-step" id="forge-ladder-strip"><div class="forge-sec-h">🪜 Ladder-locked <span class="forge-sec-ct">'+s.ladder.length+'</span>'
          +'<span class="forge-sec-sub">these mod runewords only FORM on a ladder character — ladder is a SEPARATE economy (your tallies here are non-ladder). Preview the plans without touching your account: </span>'
          +'<button class="f-btn" id="forge-ladder-preview-btn" style="font-size:11px;padding:2px 8px" onclick="try{localStorage.setItem(\'d2r_ladderPreview\',\'1\')}catch(e){};try{window.renderForge()}catch(e){};setTimeout(function(){var el=document.getElementById(\'forge-ladder-strip\');if(el)el.scrollIntoView({block:\'center\',behavior:\'smooth\'});},180)" title="view-only: expand the plans at the TOP of the forge — nothing is promoted, consumed or re-tasked">🪜 show ladder plans</button></div>'
          +'<div style="padding:6px 10px;display:flex;flex-wrap:wrap;gap:6px">'
          +s.ladder.map(function(t){ return '<span class="f-getchip" data-arttip="'+_fEsc(t.rw)+'" style="color:'+(_qC(t.rw)||'var(--q-normal)')+'" title="'+_fEsc(t.baseReq||'')+' — ladder-only in the mod">'+((typeof window.nameLogo==='function')?window.nameLogo(t.rw):'')+_fEsc(t.rw)+'</span>'; }).join('')
          +'</div></div>');
      }
    }
    

    // CRAFTS (own section) — v495: a collapsing accordion per craft TYPE. Click a card → drops down its
    // slots + recipes, each marked ✓ make-now (gem + rune in hand) or "need <rune>". Stays in-tab.
    if (show('crafts') && s.crafts.length){
      H.push('<div class="forge-sec forge-sec-craft"><div class="forge-sec-h">⚗️ Crafts <span class="forge-sec-ct">'+s.crafts.length+'</span><span class="forge-sec-sub">tap a craft → every slot + recipe, ✓ marks what you can make now</span></div>');
      // one card per craft TYPE that has a ready slot; ordered by how many slots are make-now.
      var seen={}, order=[]; s.crafts.forEach(function(c){ if(!seen[c.craft]){ seen[c.craft]=1; order.push(c.craft); } });
      H.push('<div class="forge-craftacc">');
      order.forEach(function(ck){
        var c0=null; s.crafts.forEach(function(c){ if(c.craft===ck && !c0) c0=c; });
        H.push(_craftAccHtml(ck, c0&&c0.color));
      });
      H.push('</div></div>');
    }
    // per-filter empty hint (a bucket the user filtered to that has nothing in it)
    var bc = F==='now'?(liveNow.length+deferred.length):F==='pipeline'?s.pipeline.length:F==='onestep'?(s.onestep.length+(s.farm||[]).length):F==='crafts'?s.crafts.length:(total+(s.farm||[]).length);   // v678 — farm rows count where they render
    if (F!=='all' && !bc){
      H.push('<div class="forge-empty forge-empty-sm">Nothing in this bucket right now — tap <b>▦ All</b>, or tally more runes / gems / bases.</div>');
    }
    // v512 — FORGE LEGEND lives on document.body (NOT inside #tab-forge) so its position:fixed isn't trapped
    // by an ancestor's containment (it was rendering off-screen). Created once; shown only on the Forge tab
    // via CSS body:has(#tab-forge.active). Toggle adds .open. Answers Konyo's "ideal base → what else" + key.
    if (!document.getElementById('forge-legend-fab')){
      var _lw=document.createElement('div');
      _lw.innerHTML='<button class="forge-legend-fab" id="forge-legend-fab" title="Forge legend — what the badges mean" onclick="window.forgeLegendToggle&&window.forgeLegendToggle()"><img src="art/hd_hellforge_hammer.png" alt="Forge legend" loading="lazy"></button>'
        +'<div class="forge-legend-pop" id="forge-legend-pop">'
        +'<div class="flp-h">🔨 Forge — legend</div>'
        +'<div class="flp-sec"><b>The sub-tabs</b><div>🟡 <b>One step</b> — one action away: go FIND the right-tier base, or cube missing runes up</div><div>⚒ <b>Make now</b> — forge it right now (base + sockets + runes all in hand)</div><div>🔧 <b>Pipeline</b> — Larzuk-socket the base you own, then forge</div><div>⚗️ <b>Crafts</b> — gem crafts, every slot + recipe</div><div>✅ <b>Completed</b> — runewords you\'ve created · restore any</div></div>'
        +'<div class="flp-sec"><b>Which base — the badges</b><div><span class="f-ideal">✓ ideal base</span> the socket-correct best base for this word (Larzuk hits the exact count)</div><div><span class="f-alt">meta base: X</span> a valid alternative when you don\'t have the ideal one</div><div>🏆 <b>best base for &lt;word&gt;</b> — shown on a base you already OWN (e.g. a 2H merc base): names the base you\'d IDEALLY want (a 1H player weapon)</div></div>'
        +'<div class="flp-sec"><b>Hand (Konyo\'s rule)</b><div><span class="f-hand">1H</span> a one-handed <b>player</b> weapon · <span class="f-hand">2H merc</span> a two-handed <b>mercenary</b> weapon · <span class="f-hand">2H caster</span> a caster staff</div></div>'
        +'<div class="flp-sec"><b>Sockets &amp; quality</b><div><span class="f-need">needs Nos</span> the exact socket count the word needs — Larzuk gives a base\'s MAX</div><div><span class="f-eth">⊘ eth</span> ethereal: Larzuk to max <b>or cube-socket</b> like a plain white base (eth works in the cube — superior doesn\'t)</div><div><span class="f-sup">superior</span> valid runeword base, keeps its bonus — but <b>Larzuk-max is its ONLY socket path</b> (no cube recipe on superior)</div></div>'
        +'<div class="flp-sec" style="border:none"><b>No cube-upgrades</b><div>White / normal / superior bases <b>can\'t</b> be cube-upgraded (only unique / rare / set can). If a base you own can\'t reach a word\'s socket count, <b>One step</b> names the right-tier base to <b>FIND</b> — you don\'t upgrade to it.</div></div>'
        +'</div>';
      while(_lw.firstChild) document.body.appendChild(_lw.firstChild);
    }
    box.innerHTML=H.join('');
    // v558 — COMPLETION CELEBRATION: when the forged count RISES, pulse the meter fill and pop an "✨ Forged!"
    // toast with the new N/100 (the dopamine tick for finishing a task). Silent under automation/reduced-motion.
    try {
      var _mN=_madeRw().length;
      if (typeof window.__forgeMadeN==='number' && _mN>window.__forgeMadeN && _motionOK()){
        var _fill=box.querySelector('.fp-fill'); if(_fill){ _fill.classList.remove('fp-celebrate'); void _fill.offsetWidth; _fill.classList.add('fp-celebrate'); }
        var _t=document.createElement('div'); _t.className='forge-toast'; _t.innerHTML='✨ <b>Forged!</b> '+_mN+' / '+(typeof RUNEWORD_TIP!=='undefined'?Object.keys(RUNEWORD_TIP).length:100)+' <span class="ft-sub">the Chronicle grows</span>';
        (function(el){var st=document.getElementById('forge-toasts');if(!st){st=document.createElement('div');st.id='forge-toasts';document.body.appendChild(st);}st.appendChild(el);})(_t); setTimeout(function(){ _t.classList.add('out'); setTimeout(function(){ _t.remove(); },450); }, 2400);
        // v606 — ASCEND: the next tasks rise to meet you (staggered, first card leads)
        try { var _asc=box.querySelectorAll('.forge-sec-now .f-card');
          for (var _ai=0;_ai<Math.min(3,_asc.length);_ai++){ _asc[_ai].classList.add('f-ascend'); if(_ai===1)_asc[_ai].classList.add('f-a2'); if(_ai===2)_asc[_ai].classList.add('f-a3'); }
        } catch(e){}
        // v618 — FIRST-FORGE epic (Konyo: "this logic also for the FIRST runeword, very colorful, so it
        // paves the way… making clear what powers the Forge has"): count 0→1 gets its own, LOUDER moment —
        // a rainbow-edged golden overlay that teaches what the tool does. Fires once (fresh profiles).
        try {
          if (_mN===1 && window.__forgeMadeN===0){
            var _fe=document.createElement('div'); _fe.className='forge-epic forge-epic-first';
            var _fg='✦✧★✶✷✸', _fin='';
            for (var _fi=0;_fi<18;_fi++){ _fin+='<span class="fe-rune" style="left:'+(3+Math.random()*94)+'%;animation-delay:'+Math.round(Math.random()*700)+'ms;font-size:'+(14+Math.round(Math.random()*22))+'px;color:hsl('+Math.round(Math.random()*360)+',85%,72%)">'+_fg[_fi%_fg.length]+'</span>'; }
            _fin+='<div class="fe-txt">⚒ YOUR FIRST RUNEWORD ⚒<div class="fe-sub">the Forge remembers every word you create — it plans your bases, runes and next steps from here</div></div>';
            _fe.innerHTML=_fin; document.body.appendChild(_fe); setTimeout(function(){ try{_fe.remove();}catch(e){} }, 2900);
          }
        } catch(e){}
        // v606 — MILESTONE EPIC: every 10th forge + the 100% finish get the full golden moment
        try { var _tot=(typeof RUNEWORD_TIP!=='undefined')?Object.keys(RUNEWORD_TIP).length:100;
          if (_mN===_tot || _mN%10===0){
            var _ep=document.createElement('div'); _ep.className='forge-epic';
            var _gl='ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛏᛒᛖ', _in='';
            for (var _gi=0;_gi<14;_gi++){ _in+='<span class="fe-rune" style="left:'+(4+Math.random()*92)+'%;animation-delay:'+Math.round(Math.random()*550)+'ms;font-size:'+(18+Math.round(Math.random()*18))+'px">'+_gl[_gi%_gl.length]+'</span>'; }
            _in+='<div class="fe-txt">'+(_mN===_tot?'⚒ CHRONICLE COMPLETE ⚒':'⚒ '+_mN+' FORGED ⚒')+'<div class="fe-sub">'+(_mN===_tot?'every runeword — made by your hand':'milestone — the anvil remembers')+'</div></div>';
            _ep.innerHTML=_in; document.body.appendChild(_ep); setTimeout(function(){ try{_ep.remove();}catch(e){} }, 2350);
          }
        } catch(e){}
      }
      window.__forgeMadeN=_mN;
    } catch(e){}
  }

  window.forgeScan=forgeScan;
  window.renderForge=renderForge;
  try { window._ownedBases=_ownedBases; } catch(e){}   // v545 — debug/spec hook for the tagged-base parser
  try { window._baseHandClass=_baseHandClass; } catch(e){}  // v547 — so the Socketed/throw-out review can word 1H/2H-merc/caster IN SYNC with the Forge
  // v546.1 — do NOT re-expose _baseTier here: the canonical window._baseTier already exists (defined ~L8022; it
  // quality-strips + uses _baseRec, so it resolves Superior/unique bases correctly). An earlier v546 override
  // clobbered it with a BASE_DB-only version and broke v380/v450. Smart Insights' _baseFarmWhere uses the good one.
})();
