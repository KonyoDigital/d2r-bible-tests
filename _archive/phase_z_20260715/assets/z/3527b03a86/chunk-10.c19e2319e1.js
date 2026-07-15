
(function(){
  'use strict';
  var RK='d2r_muleRoster', AK='d2r_muleAssign';
  var DEFAULT_ROSTER=[
    {id:'sets-major', name:'SETS-TAL-IK', icon:'🛡️', note:'Tal Rasha · Immortal King · Griswold — never split a set'},
    {id:'sets-rest',  name:'SETS-REST',   icon:'🧩', note:'every other set — partials live here'},
    {id:'uni-weap',   name:'UNI-WEAPONS', icon:'⚔️', note:'unique melee + caster weapons'},
    {id:'uni-armor',  name:'UNI-ARMOR',   icon:'🪖', note:'body armor · helms · shields · belts · boots · gloves'},
    {id:'uni-small',  name:'UNI-SMALL',   icon:'💍', note:'rings · amulets · jewels · charms'},
    {id:'runewords',  name:'RUNEWORDS',   icon:'📜', note:'forged runewords — Enigma · Spirit · Call to Arms · Insight · Infinity… every runeword lives here, weapon or armor'},
    {id:'bases',      name:'SOCKETED',    icon:'🔩', note:'socketed bases — white / magic / rare bases for runewords & crafts (they look like junk, they are not)'},
    {id:'magic-rare', name:'MAGIC & RARE',icon:'🔮', note:'skillers · magic / rare charms · jewels · rings · amulets · crafts (rolled-name keepers)'},
    {id:'shared',     name:'SHARED STASH',icon:'📦', note:'worth-keeping-close keepers shared across all your characters — auto-sorted here (SoJ · Anni · Shako · top charms) · 5 shared tabs'},
    {id:'dupes',      name:'GRAIL-DUPES', icon:'♻️', note:'second copies — trade stock'},
    {id:'wip',        name:'WIP',         icon:'🛠️', note:'next-build staging — the only locker that churns'}
  ];
  function load(k,f){ try{ var v=JSON.parse(window.LSR.getItem(k)); return v||f; }catch(e){ return f; } }
  var roster = load(RK, null) || DEFAULT_ROSTER.map(function(m){ return Object.assign({}, m); });
  var assign = load(AK, {});
  // v230 migration: runes / essences / Worldstone shards / statues live in RoW's
  // infinite shared stash, so the RUNES-HIGH + MATS lockers are retired. Strip them
  // from any roster saved before this version and drop every assignment that pointed
  // at them, so existing users converge on the new shelf without re-doing the vault.
  (function(){
    var DEAD = {'runes-high':1, 'mats':1};
    var had = roster.some(function(m){ return DEAD[m.id]; });
    roster = roster.filter(function(m){ return !DEAD[m.id]; });
    var prunedAssign = false;
    Object.keys(assign).forEach(function(n){ if (DEAD[assign[n]]){ delete assign[n]; prunedAssign = true; } });
    if (had){ try{ window.LSR.setItem(RK, JSON.stringify(roster)); }catch(e){} }
    if (prunedAssign){ try{ window.LSR.setItem(AK, JSON.stringify(assign)); }catch(e){} }
  })();
  // v404 migration — inject the RUNEWORDS mule into rosters saved before it existed (Konyo: "just a
  // mule for runewords, regardless of armor or weapon"). Insert it just before SOCKETED ('bases').
  (function(){
    if (roster.some(function(m){ return m.id === 'runewords'; })) return;
    var rw = {id:'runewords', name:'RUNEWORDS', icon:'📜', note:'forged runewords — Enigma · Spirit · Call to Arms · Insight · Infinity… every runeword lives here, weapon or armor'};
    var bi = roster.findIndex(function(m){ return m.id === 'bases'; });
    if (bi >= 0) roster.splice(bi, 0, rw); else roster.push(rw);
    try{ window.LSR.setItem(RK, JSON.stringify(roster)); }catch(e){}
  })();
  // v322: rename the legacy BASES locker → SOCKETED (same id 'bases', so assignments survive) for
  // rosters saved before this version, and refresh its icon/note to the socketed-base wording.
  (function(){
    var b = roster.find(function(m){ return m.id==='bases'; });
    if (b && b.name !== 'SOCKETED'){
      b.name='SOCKETED'; b.icon='🔩';
      b.note='socketed bases — white / magic / rare bases for runewords & crafts (they look like junk, they are not)';
      try{ window.LSR.setItem(RK, JSON.stringify(roster)); }catch(e){}
    }
  })();
  // v342.5 — ensure the MAGIC & RARE locker exists on rosters saved before it (holds the magicFinds keepers)
  (function(){
    if (!roster.some(function(m){ return m.id==='magic-rare'; })){
      var mr={id:'magic-rare', name:'MAGIC & RARE', icon:'🔮', note:'skillers · magic / rare charms · jewels · rings · amulets · crafts (rolled-name keepers)'};
      var idx=roster.findIndex(function(m){ return m.id==='bases'; });
      if (idx>=0) roster.splice(idx+1, 0, mr); else roster.push(mr);
      try{ window.LSR.setItem(RK, JSON.stringify(roster)); }catch(e){}
    }
    // v360 — ensure the SHARED STASH locker exists on rosters saved before it (holds the never-muled items)
    if (!roster.some(function(m){ return m.id==='shared'; })){
      var sh={id:'shared', name:'SHARED STASH', icon:'📦', note:'worth-keeping-close keepers shared across all your characters — auto-sorted here (SoJ · Anni · Shako · top charms) · 5 shared tabs'};
      var mi=roster.findIndex(function(m){ return m.id==='magic-rare'; });
      if (mi>=0) roster.splice(mi+1, 0, sh); else roster.push(sh);
      try{ window.LSR.setItem(RK, JSON.stringify(roster)); }catch(e){}
    }
  })();
  function saveR(){ window.LSR.setItem(RK, JSON.stringify(roster)); }
  function saveA(){ window.LSR.setItem(AK, JSON.stringify(assign)); }
  var selectedChip = null;
  // v322 polish: each locker carries a rarity ACCENT (like the Crafted Workshop's per-craft gem
  // colours) — tinted plate + top stripe + gauge, keyed to what the locker HOLDS. Sets green,
  // uniques gold, SOCKETED white, dupes cyan, WIP muted — coherent with the in-game palette.
  var MULE_ACCENT = { 'sets-major':'vm-a-set','sets-rest':'vm-a-set','uni-weap':'vm-a-uni','uni-armor':'vm-a-uni','uni-small':'vm-a-uni','bases':'vm-a-basic','magic-rare':'vm-a-magic','dupes':'vm-a-dupe','wip':'vm-a-wip' };
  function _muleAccent(id){ return MULE_ACCENT[id] || ''; }

  // ── taxonomy brain ──
  var MAJOR_SETS = /^(Tal Rasha|Immortal King|Griswold)/i;
  var JEWELRY_RE = /\b(ring|amulet|charm|jewel)\b/i;
  var ARMOR_RE = /\b(armor|plate|mail|hauberk|tunic|jupon|cuirass|husk|hide|pelt|shell|carapace|wyrmhide|helm|cap|crown|casque|basinet|mask|circlet|coronet|tiara|diadem|sallet|armet|shako|visor|shield|buckler|rondache|aegis|ward|monarch|luna|defender|gauntlets?|gloves?|grasp|bracers?|vambraces?|boots?|greaves|sabatons?|treads?|trek|spurs?|belt|sash|cord|girdle|buckle)\b/i;
  // ITEM_CODEX = {base, rarity, setName} (lexical, not on window) · ITEM_TIP = {b, t}
  function tipOf(n){
    try{
      var c = (typeof ITEM_CODEX!=='undefined' && ITEM_CODEX[n]) || null;
      var t = (typeof ITEM_TIP!=='undefined' && ITEM_TIP[n]) || null;
      if (!c && !t) return null;
      return {
        base: (c && c.base) || (t && t.b) || '',
        rarity: ((c && c.rarity) || (t && t.t) || '').toLowerCase(),
        setName: (c && c.setName) || null
      };
    }catch(e){ return null; }
  }
  // RoW shared-stash items never get a mule — runes, essences, Worldstone shards,
  // and the 5 Colossal statues all live in one infinite shared stash, so the
  // assembler must never route them. (They aren't in ITEMS either, so this is a
  // belt-and-suspenders guard that also documents the intent.)
  // v425 — "rune" must match ONLY as a trailing type word ("Ist rune", "Jah/Ber/Sur rune"), NEVER as a
  // base-NAME prefix: "Rune Sword / Rune Bow / Rune Staff / Rune Scepter" (real socketable runeword bases) and
  // "Rune Master" were wrongly flagged shared-stash (never-muled) by the old bare \brune\b. The (?!\s+[a-z])
  // lookahead drops the match when another word follows, so those bases route to SOCKETED/uni-* as intended.
  var SHARED_STASH_RE = /\brunes?\b(?!\s+[a-z])|\b(essence|worldstone shard|colossal ancient statue|cold rupture|flame rift|crack of the heavens|rotting fissure|bone break|black cleft)\b|^(talic's anguish|korlic's pain|madawc's ire|bul-kathos' nightmare|worusk's end)$/i;
  function isSharedStash(n){ return SHARED_STASH_RE.test(String(n||'')); }
  try { window.isSharedStash = isSharedStash; } catch(e){}   // v425 — expose for the vault audit (null route = shared, not a bug)
  // v409 — NEVER-MULE keepers: Annihilus, Hellfire Torch, Gheed's Fortune (the 6 Sunder charms are already
  // caught by isSharedStash). These uniques ONLY function in the inventory of the character you're actively
  // playing — a mule/alt can't use them. The "Don't mule to your alt" advisory flags them, so the auto-assign
  // MUST match that and never route them to a mule. {id:'__keep'} → muleById() can't resolve it → the item is
  // still registered/owned + shown in the keep advisory, but it is NOT assigned to any mule.
  var KEEP_IN_INVENTORY = /^(Annihilus|Hellfire Torch|Gheed's Fortune)$/i;
  function suggestMule(name){
    if (isSharedStash(name)) return null;
    if (KEEP_IN_INVENTORY.test(String(name||'').trim())) return {id:'__keep', why:'keep in your inventory — only works on the character you are actively playing'};
    // v394 — KEEP only the genuinely good sets; the low/junk partial sets (Sigon's, Sander's, Hsarus',
    // Cleglaw's, Iratha's, Angelic, Arctic, Cathan's, Death's, Vidala's, Berserker's, Milabrega's, Isenhart's,
    // Civerb's, Infernal, Bul-Kathos, Cow King's, Tancred's…) are NOT worth muling — Konyo: identify them for
    // the grail then THROW THEM OUT. {id:'__throwout'} routes the piece to the throw-out pile, not a mule.
    // v440 — the class ENDGAME sets that ARE worth muling. Tal Rasha (sorc) · Immortal King (barb) · Griswold
    // (pala) · Aldur (druid) · Trang-Oul (necro) · Natalya (sin) · M'avina (ama) — PLUS Horazon's Splendor, the
    // RotW WARLOCK class set (was falling through to throw-out as "junk" — Konyo's 4 Horazon's pieces wrongly
    // discarded; it's the Warlock's Tal-Rasha-tier set, so it MULES to SETS-REST now, not the throw-out pile).
    var _KEEP_SET = /Tal Rasha|Immortal King|Griswold|Aldur|Trang.?Oul|Natalya|M.?avina|Horazon/i;
    try{
      var spm = window.findSetPiece && window.findSetPiece(name);
      if (spm){
        var psn = (spm.set && spm.set.name) || name;
        if (!_KEEP_SET.test(psn)) return {id:'__throwout', why:'low set piece — track for grail, discard: '+psn};
        return MAJOR_SETS.test(psn) ? {id:'sets-major', why:'set piece: '+psn} : {id:'sets-rest', why:'set piece: '+psn};
      }
    }catch(e){}
    var it = (typeof ITEMS!=='undefined') ? ITEMS.find(function(i){return i.n===name;}) : null;
    var tip = tipOf(name);
    var isSet = (tip && tip.rarity==='set') || (it && it.tier==='set') || /\bset\b|\(any/i.test(name);
    if (isSet){
      var sn = (tip && tip.setName) || name;
      if (!_KEEP_SET.test(sn)) return {id:'__throwout', why:'low set — track for grail, discard: '+sn};
      return MAJOR_SETS.test(sn) ? {id:'sets-major', why:'major set: '+sn} : {id:'sets-rest', why:'set: '+sn};
    }
    // v404 — a FORGED RUNEWORD (Enigma, Spirit, Call to Arms…) is real gear, not a misread. ALL runewords go
    // to their OWN dedicated RUNEWORDS mule regardless of slot (Konyo: "just a mule for runewords, regardless
    // of armor or weapon"). Was previously split UNI-WEAPONS / UNI-ARMOR by base type.
    try {
      if (typeof findRuneword === 'function'){ var _rwk = findRuneword(name);
        if (_rwk) return {id:'runewords', why:'runeword: '+_rwk};
      }
    } catch(e){}
    // v524 — CIRCLETS (Circlet/Coronet/Tiara/Diadem) are type 'circ' → they socket GEMS/JEWELS ONLY, they
    // CANNOT hold a runeword (verified in game data). So a WHITE or MAGIC circlet base is vendor trash — the
    // ONLY circlet worth keeping is a RARE one (rolls +skills / FCR / res / life + facet sockets). Konyo:
    // "only rare circlets — no white, no magic." Catches both the bare base name and a rolled rare's base.
    try {
      var _CIRC = /^\s*(?:Circlet|Coronet|Tiara|Diadem)\s*$/i;
      var _ccl = (typeof _artSlotClean === 'function') ? _artSlotClean(name) : String(name).replace(/\s*\([^)]*\)\s*$/,'');
      var _cbase = (typeof _mfBase === 'function' && typeof magicFinds !== 'undefined' && magicFinds && magicFinds[name]) ? _mfBase(name) : '';
      if (_CIRC.test(_ccl) || _CIRC.test(_cbase)){
        var _cq = (typeof _mfQual === 'function' && typeof magicFinds !== 'undefined' && magicFinds && magicFinds[name]) ? _mfQual(name) : 'white';
        if (_cq === 'rare') return {id:'magic-rare', why:'RARE circlet — keep (+skills/FCR/res + facet sockets)'};
        return {id:'__throwout', why:'circlet — can’t hold runewords; only RARE circlets are keepers (this is '+_cq+') → vendor it'};
      }
    } catch(e){}
    // v364 — AUTO-SORT to the SHARED cross-account stash: items "worth keeping close" (High / Very-High
    // trade value, from the maxroll tier data) route to SHARED — accessible by every character, trade-ready —
    // simultaneously with the rest going to their mule by slot. Runes/gems/materials are NOT here (own planners).
    var _tv = (typeof _itemValue === 'function') ? _itemValue(name) : '';
    if (_tv === 'high' || _tv === 'vhigh') return {id:'shared', why:'high trade value — keep close in the shared stash'};
    // v325: EXTRA_ITEMS (reference finds) carry an authoritative CATEGORY — route by it so the
    // keyword fallback below can't mis-file them. Konyo caught skillers ("...Skiller (GC)") landing
    // in UNI-WEAPONS: a Grand Charm has no "charm" in its name, so JEWELRY_RE missed it. Now charms/
    // skillers → UNI-SMALL, runeword + socketed bases → SOCKETED, jewelry → UNI-SMALL, crafted by slot.
    var ex = (typeof EXTRA_ITEMS!=='undefined') ? EXTRA_ITEMS[name] : null;
    if (ex){
      var xcat = (ex.cat||'').toLowerCase();
      var xb = (ex.base||'').toLowerCase();
      // GENERIC socketed junk-bases ("Socketed Body Armor/Helm/Shield/1H-2H Weapon") → SOCKETED mule.
      if (/socketed bases/.test(xcat)){
        // v563 — REGISTERED socketed bases route through THIS branch (not the socket-label regex below),
        // so the Chronicle + spare sync must live here too, for entries that resolve to a REAL base.
        // Generic "Socketed <Slot>" / "Larzuk <Slot> Base" placeholders don't resolve and keep old routing.
        try {
          var _xGeneric = /^(?:socketed|larzuk)\s/i.test(String(name));   // "Socketed <Slot>" / "Larzuk <Slot> Base" placeholders
          var _xclean = (typeof _artSlotClean==='function') ? _artSlotClean(ex.base || name) : String(ex.base || name);
          if (!_xGeneric && typeof _isRunewordBase==='function' && typeof _baseUnmadeRunewords==='function' && _isRunewordBase(_xclean)){
            var _xs = (typeof ex.sockets==='number') ? ex.sockets : (function(){ var m2=/\((\d+)\s*os/i.exec(name); return m2?+m2[1]:0; })();
            var _xUn = _baseUnmadeRunewords(name, _xs);   // v582.2 — FULL label: the Superior prefix must drive the Larzuk-max-only rule
            if (!_xUn.length){
              // v602 — honest empty-list verdict: unmade words at OTHER counts are "wrong sockets", not "✓ forged"
              var _xWS = (_xs>=1 && typeof _baseUnmadeWrongSock==='function') ? _baseUnmadeWrongSock(name, _xs) : [];
              return {id:'__throwout', why: _xWS.length
                ? 'socketed '+_xclean+' — '+_xWS[0].n+' ('+_xWS[0].s+'os) is still unmade but this '+_xs+'os copy can never host it (sockets are fixed) → vendor it, hunt a '+_xWS[0].s+'os/unsocketed copy'
                : 'socketed '+_xclean+' — nothing left for it: its runewords are ✓ forged or belong in endgame bases → vendor it'};
            }
            var _xsp = (typeof _spareBaseInfo==='function') ? _spareBaseInfo(name, _xUn) : null;
            if (_xsp && !_xsp.uncovered.length){
              var _xw = Object.keys(_xsp.covered);
              return {id:'__throwout', why:'spare '+_xclean+' — you already hold a base for '+_xw.slice(0,2).join(', ')+(_xw.length>2?' +'+(_xw.length-2)+' more':'')+' (your '+_xsp.covered[_xw[0]][0]+') → vendor it'};
            }
            var _xk = (_xsp && _xsp.uncovered.length) ? _xsp.uncovered : _xUn.map(function(r){return r.n;});
            _xk = (typeof window._bisSortFor==='function') ? window._bisSortFor(_xclean, _xk) : _xk;   // v583
            var _xkBis = (typeof window._isBisBaseFor==='function') && window._isBisBaseFor(_xclean, _xk[0]);
            return {id:'bases', why:'socketed base — still needed for '+_xk.slice(0,3).join(', ')+(_xk.length>3?' +'+(_xk.length-3)+' more':'')+(_xkBis?' · 🏆 its classic '+_xk[0]+' base':'')};
          }
        } catch(e){}
        return {id:'bases', why:'generic socketed base'};
      }
      if (/charm/.test(xcat) || /\bskiller\b|\(gc\)|\(sc\)|grand charm|small charm/i.test(name)) return {id:'uni-small', why:'charm/skiller'};
      if (/jewel/.test(xcat)) return {id:'uni-small', why:ex.cat};
      if (/crafted/.test(xcat)){
        if (/ring|amulet/.test(xb)) return {id:'uni-small', why:'crafted jewelry'};
        return {id:'uni-armor', why:'crafted armor piece'};
      }
      // NAMED elite runeword bases ("Eth Giant Thresher (Infinity base)", "4-socket Monarch"…) are
      // real gear you keep to MAKE a runeword — route by SLOT here, NOT the generic SOCKETED junk
      // mule (Konyo: an Infinity polearm belongs in UNI-WEAPONS). Must return BEFORE the socket-name
      // regex below, or "4-socket Monarch" would mis-file to SOCKETED on the word "socket".
      if (/runeword bases/.test(xcat)){
        if (JEWELRY_RE.test(xb)) return {id:'uni-small', why:'runeword base — '+ex.base};
        if (ARMOR_RE.test(xb))   return {id:'uni-armor', why:'runeword base — '+(ex.base||'armor')};
        return {id:'uni-weap', why:'runeword base — '+(ex.base||'weapon')};
      }
      // cat 'Uniques' falls through to the slot routing below (uses ex.base).
    }
    // v362 — prefer the AUTHORITATIVE ITEM_TIP base (verified per-item) over tipOf(), which mis-resolves
    // some names via loose matching (Jalal's Mane → "Dream Spirit" runeword collision → mis-filed to weapons).
    var itip = (typeof ITEM_TIP !== 'undefined') ? ITEM_TIP[name] : null;
    var base = (itip && itip.b) || (tip && tip.base) || (ex && ex.base) || '';
    var probe = base + ' ' + name;
    // v322: socketed bases (generic "Socketed <Slot>" buckets, or any item literally named with
    // sockets) get their own home — the SOCKETED mule — BEFORE the jewelry/armor/weapon fallbacks.
    // v413 — also catch the INTAKE LABEL format ("Grim Scythe (6os)", "Circlet (Larzuk base)", "Trident (3os low base)"):
    // the word "socket" isn't in those, so without this a kept socketed base would mis-route to UNI-WEAPONS if
    // _ensureSocketBaseEntry hadn't pre-filed it in EXTRA_ITEMS. Belt-and-suspenders → SOCKETED.
    if (/\bsocket(ed|s)?\b/i.test(name) || /\((?:\d+\s*os(?:\s+low base)?|larzuk base)\)\s*$/i.test(name)){
      // v524 — a socketed/Larzuk-labelled base is only a keeper if it can hold a runeword (single source of
      // truth). A non-RW base (circlet already handled above; any other 500+ base) → vendor, not SOCKETED.
      var _sclean = (typeof _artSlotClean==='function') ? _artSlotClean(name) : String(name).replace(/\s*\([^)]*\)\s*$/,'');
      if (typeof _isRunewordBase==='function' && !_isRunewordBase(_sclean)) return {id:'__throwout', why:'socketed '+_sclean+' — can’t hold a runeword → vendor it'};
      // v562 — CHRONICLE SYNC: it can hold runewords, but are any still UNMADE? A base whose every fitting
      // word is already ✓ forged (or ladder-blocked) serves nothing — throw it out, don't mule it. When it
      // IS a keeper, say WHICH unmade words it's being kept for (same knowledge the Forge/Smart AI has).
      try {
        var _skM = /\((\d+)\s*os/i.exec(name);
        var _skN = _skM ? parseInt(_skM[1],10) : 0;   // "(Larzuk base)" / no tag → 0 = unsocketed
        var _sUn = (typeof _baseUnmadeRunewords==='function') ? _baseUnmadeRunewords(name, _skN) : null;
        if (_sUn && !_sUn.length){
          // v602 — honest empty-list verdict: unmade words at OTHER counts are "wrong sockets", not "✓ forged"
          var _sWS = (_skN>=1 && typeof _baseUnmadeWrongSock==='function') ? _baseUnmadeWrongSock(name, _skN) : [];
          return {id:'__throwout', why: _sWS.length
            ? 'socketed '+_sclean+' — '+_sWS[0].n+' ('+_sWS[0].s+'os) is still unmade but this '+_skN+'os copy can never host it (sockets are fixed) → vendor it, hunt a '+_sWS[0].s+'os/unsocketed copy'
            : 'socketed '+_sclean+' — nothing left for it: its runewords are ✓ forged or belong in endgame bases → vendor it'};
        }
        if (_sUn && _sUn.length){
          // v563 — SPARE: its unmade words are all covered by a DIFFERENT base you already hold → don't keep two
          var _ssp = (typeof _spareBaseInfo==='function') ? _spareBaseInfo(name, _sUn) : null;
          if (_ssp && !_ssp.uncovered.length){
            var _sw = Object.keys(_ssp.covered);
            return {id:'__throwout', why:'spare '+_sclean+' — you already hold a base for '+_sw.slice(0,2).join(', ')+(_sw.length>2?' +'+(_sw.length-2)+' more':'')+' (your '+_ssp.covered[_sw[0]][0]+') → vendor it'};
          }
          var _sk = (_ssp && _ssp.uncovered.length) ? _ssp.uncovered : _sUn.map(function(r){return r.n;});
          _sk = (typeof window._bisSortFor==='function') ? window._bisSortFor(_sclean, _sk) : _sk;   // v583 — this base's TRUE home word headlines
          var _skBis = (typeof window._isBisBaseFor==='function') && window._isBisBaseFor(_sclean, _sk[0]);
          return {id:'bases', why:'socketed base — still needed for '+_sk.slice(0,3).join(', ')+(_sk.length>3?' +'+(_sk.length-3)+' more':'')+(_skBis?' · 🏆 its classic '+_sk[0]+' base':'')};
        }
      } catch(e){}
      return {id:'bases', why:'socketed base'};
    }
    // v430 — a BARE BASE: an exact game-data base name (BASE_CLASS) that matched NO unique/set/runeword/EXTRA
    // above is a plain WHITE base → the SOCKETED locker (runeword/craft base), NOT uni-weap. Without this,
    // "Cryptic Axe"/"Monarch"/"Quilted Armor" etc. fell through to the uni-weap default — correct for a unique
    // weapon, wrong for a white base. (Surfaced when the full 1297-catalog audit included all 498 bases.)
    var _bareBaseClean = (typeof _artSlotClean==='function') ? _artSlotClean(name) : String(name).replace(/\s*\([^)]*\)\s*$/,'');
    var _bareQ = _bareBaseClean.replace(/^(?:Superior|Ethereal|Eth|Cracked|Crude|Damaged|Low Quality)\s+/i,'').trim();   // v574 — "Superior Flail" is a Flail
    if (typeof BASE_CLASS!=='undefined' && (BASE_CLASS[name] || BASE_CLASS[_bareBaseClean] || BASE_CLASS[_bareQ]) && !it && !ex && !itip){
      // v524 — GENERALISED (was v502 orb/throwing-only): a white base is a SOCKETED keeper ONLY if it can hold
      // a runeword. The single source of truth _isRunewordBase (= _baseRunewords>0, same as the Forge) covers
      // ALL 500+ bases — circlets (gems/jewels only), orbs, throwing weapons, javelins, and any other non-RW
      // type → vendor trash, not the SOCKETED locker. No hardcoded type list, no platform mismatch.
      if (typeof _isRunewordBase==='function' && !_isRunewordBase(_bareBaseClean))
        return {id:'__throwout', why:'white '+_bareBaseClean+' — can’t hold a runeword (no runeword/craft value) → vendor it'};
      // v562 — CHRONICLE SYNC (same rule as the socketed branch): a white base whose every hostable runeword
      // is already ✓ forged has no job left — vendor it instead of muling it to SOCKETED.
      try {
        var _bUn = (typeof _baseUnmadeRunewords==='function') ? _baseUnmadeRunewords(_bareBaseClean, 0) : null;
        if (_bUn && !_bUn.length) return {id:'__throwout', why:'white '+_bareBaseClean+' — nothing left for it: its runewords are ✓ forged or belong in endgame bases → vendor it'};
        if (_bUn && _bUn.length){
          var _bsp = (typeof _spareBaseInfo==='function') ? _spareBaseInfo(name, _bUn) : null;
          if (_bsp && !_bsp.uncovered.length){
            var _bw = Object.keys(_bsp.covered);
            return {id:'__throwout', why:'spare '+_bareBaseClean+' — you already hold a base for '+_bw.slice(0,2).join(', ')+(_bw.length>2?' +'+(_bw.length-2)+' more':'')+' (your '+_bsp.covered[_bw[0]][0]+') → vendor it'};
          }
          var _bk = (_bsp && _bsp.uncovered.length) ? _bsp.uncovered : _bUn.map(function(r){return r.n;});
          _bk = (typeof window._bisSortFor==='function') ? window._bisSortFor(_bareBaseClean, _bk) : _bk;   // v583
          var _bkBis = (typeof window._isBisBaseFor==='function') && window._isBisBaseFor(_bareBaseClean, _bk[0]);
          return {id:'bases', why:'white base — still needed for '+_bk.slice(0,3).join(', ')+(_bk.length>3?' +'+(_bk.length-3)+' more':'')+(_bkBis?' · 🏆 its classic '+_bk[0]+' base':'')};
        }
      } catch(e){}
      return {id:'bases', why:'white base → socketed / craft'};
    }
    // v362 — ARMOR before JEWELRY: body armor like "Ring Mail" contains the word "ring", so it must be
    // caught as armor (via "mail") FIRST, or it mis-files to UNI-SMALL (Konyo: Darkglow Ring Mail → jewelry).
    if (ARMOR_RE.test(probe))   return {id:'uni-armor', why:'armor slot — base: '+(base||'name match')};
    if (JEWELRY_RE.test(probe)) return {id:'uni-small', why:'jewelry/charm — base: '+(base||'name match')};
    return {id:'uni-weap', why: base ? 'weapon — base: '+base : 'default: weapons'};
  }

  function muleById(id){ return roster.find(function(m){return m.id===id;}); }
  // v227: "X set (any piece)" rows are grail ODDS rows, not physical items —
  // they have no base, no size, nothing to pack. They keep their calc ✓ but
  // never appear in the vault. Exact set pieces (findSetPiece) are first-class.
  function isAggregate(n){ return /\((any piece|any|set)\)\s*$/i.test(n); }
  function ownedPool(){
    try{
      if (typeof owned==='undefined' || typeof ITEMS==='undefined') return [];
      return Array.from(owned).filter(function(n){
        if (isAggregate(n)) return false;
        // v324: EXTRA_ITEMS (socketed bases + reference finds) are real owned items too — they MUST
        // survive ownedPool or renderVault prunes their mule assignment every render (the bug behind
        // "socketed items don't stick to a mule"). Shared-stash items (runes/essences/statues) stay out.
        if (typeof EXTRA_ITEMS!=='undefined' && EXTRA_ITEMS[n] && !isSharedStash(n)) return true;
        // v404 — a FORGED RUNEWORD (Enigma, Spirit, CtA…) is real owned gear but is NOT a grail ITEM,
        // EXTRA_ITEM or set piece, so it was falling out of the pool → its mule assignment got pruned every
        // render → it vanished from all lockers (Konyo: "where did the Enigma go?"). Keep runewords in.
        if (window.findRuneword && window.findRuneword(n)) return true;
        return ITEMS.some(function(i){return i.n===n;}) || !!(window.findSetPiece && window.findSetPiece(n));
      }).sort();
    }catch(e){ return []; }
  }
  function art(n, glyph, size){ try{ return (typeof artOr==='function') ? artOr(n, glyph||'◆', size||'sm') : ''; }catch(e){ return ''; } }
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;'); }
  function jsArg(t){ return String(t).replace(/\\/g,'\\\\').replace(/'/g,"\\'"); }
  function status(msg){ var el=document.getElementById('vault-status'); if(el){ el.textContent=msg; setTimeout(function(){ if(el.textContent===msg) el.textContent=''; }, 4200); } }
  // v236 — vault item finder: type a name → which alt (mule) holds it. Searches
  // everything you've ✓ owned + vaulted; click a hit to open that mule's card.
  window.vaultFind = function(q){
    var res = document.getElementById('vault-find-results');
    if (!res) return;
    q = String(q||'').trim().toLowerCase();
    if (!q){ res.hidden = true; res.innerHTML = ''; return; }
    var pool = ownedPool();
    var matches = pool.filter(function(n){ return n.toLowerCase().indexOf(q) !== -1; }).sort();
    res.hidden = false;
    if (!matches.length){
      res.innerHTML = '<div class="vfr-empty">no vaulted item matches "<b>'+esc(q)+'</b>" — only items you’ve ✓ owned show here</div>';
      return;
    }
    var rows = matches.slice(0,30).map(function(n){
      var mid = assign[n], m = mid ? muleById(mid) : null;
      var loc = m
        ? '<span class="vfr-arrow">→</span><span class="vfr-mule">'+esc(m.icon+' '+m.name)+'</span>'
        : '<span class="vfr-arrow">→</span><span style="color:var(--text-dim)">unsorted · in the dock</span>';
      var click = mid ? ' onclick="window.openMuleCard&&window.openMuleCard(\''+jsArg(mid)+'\')"' : '';
      return '<div class="vfr-row"'+click+' title="'+(mid?'open this mule’s ID card':'still unsorted — assign it to a mule')+'">'
        + art(n) + '<span class="vfr-name"'+(typeof _qStyle==='function'?_qStyle(n,'unique'):'')+'>'+esc(n)+'</span><span class="vfr-loc">'+loc+'</span></div>';
    }).join('');
    res.innerHTML = '<div class="vfr-head">'+matches.length+' match'+(matches.length===1?'':'es')+(matches.length>30?' · showing 30':'')+' — click to open the mule</div>' + rows;
  };

  // ── render ──
  // v307: the AI's "don't mule to your alt account" advisory — reads your live rune/gem/
  // material tallies + owned charms and flags what belongs on your MAIN (a separate account
  // can't reach your shared stash, and charms only work in your playing inventory).
  function renderVaultKeep(){
    var el = document.getElementById('vault-keep'); if (!el) return;
    function sum(o){ var t=0; try{ Object.keys(o||{}).forEach(function(k){ var v=parseInt(o[k],10); if(isFinite(v)&&v>0) t+=v; }); }catch(e){} return t; }
    var shared=[], ingred=[], charm=[];
    var rc=(typeof runeStash!=='undefined')?sum(runeStash):0; if(rc) shared.push(rc+' rune'+(rc===1?'':'s'));
    var gc=(typeof gemStash!=='undefined')?sum(gemStash):0; if(gc) shared.push(gc+' gem'+(gc===1?'':'s'));
    try{ Object.keys(typeof materialStash!=='undefined'?materialStash:{}).forEach(function(k){
      var v=parseInt(materialStash[k],10); if(!(isFinite(v)&&v>0)) return; var lk=k.toLowerCase(); var tag=k+' ×'+v;
      if(/sunder/.test(lk)) charm.push(tag);
      else if(/shard|statue/.test(lk)) shared.push(tag);
      else if(/key|horn|brain|\beye\b|essence|wirt|leg/.test(lk)) ingred.push(tag);
      else shared.push(tag);
    }); }catch(e){}
    try{ if(typeof owned!=='undefined') ['Annihilus','Hellfire Torch',"Gheed's Fortune"].forEach(function(n){ if(_gFound(n)) charm.push(n); }); }catch(e){}
    var rows=[];
    if(shared.length) rows.push({ic:'🏦', t:'Account-shared stash', items:shared, count:true, r:"runes, gems, essences, Worldstone shards & Colossal statues sit in your shared stash — reachable by every character instantly. A separate alt ACCOUNT can't see it, so keep them here."});
    if(charm.length) rows.push({ic:'💠', t:'Charms — keep in your inventory', items:charm, r:"Sunders, Annihilus, Torch, Gheed's & skillers only do anything in the inventory of the character you're playing — never bury them on an alt."});
    if(ingred.length) rows.push({ic:'🗝️', t:'Active cube / uber ingredients', items:ingred, r:"Pandemonium keys, uber organs, Token essences & Wirt's Leg — you need these on-hand to cube portals / a Token. Keep them reachable."});
    if(!rows.length){ el.hidden=true; el.innerHTML=''; return; }
    el.hidden=false;
    el.innerHTML='<div class="vk-head">🚫 <strong>Don’t mule to your alt account</strong> — keep these on your main:</div>'
      + rows.map(function(r){ return '<div class="vk-row"><div class="vk-row-h"><span class="vk-ic">'+r.ic+'</span><span class="vk-title">'+esc(r.t)+'</span></div>'
        + '<div class="vk-items">'+r.items.map(function(s){return '<span class="vk-chip'+(r.count?' vk-chip-count':'')+'">'+esc(s)+'</span>';}).join('')+'</div>'
        + '<div class="vk-reason">'+esc(r.r)+'</div></div>'; }).join('');
  }
  // v342.28 — Multi-copy keepers: resolve a typed name to its canonical grail entry, and render the
  // editable panel (have/want steppers + add/remove). Targets persist; have-counts come from `copies`.
  function _grailVocab(){
    var v=[];
    try { if (typeof ITEMS!=='undefined') v=ITEMS.map(function(i){return i.n;}).filter(function(n){ return !/\((any piece|any|set)\)\s*$/i.test(n); }); } catch(e){}
    try { if (window.EXTRA_ITEMS) v=v.concat(Object.keys(window.EXTRA_ITEMS)); } catch(e){}
    return v;
  }
  function _resolveGrailName(input){
    var q=String(input||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim(); if(!q) return null;
    var v=_grailVocab(), pref=null;
    for(var i=0;i<v.length;i++){ var nl=v[i].toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
      if(nl===q) return v[i];
      if(!pref && q.length>=4 && nl.indexOf(q)===0) pref=v[i];
    }
    return pref;
  }
  function renderMultiKeep(){
    var el=document.getElementById('vault-multikeep'); if(!el) return;
    var names=Object.keys(multiKeep||{}).filter(function(n){ return multiKeep[n]>1; }).sort();
    el.hidden=false;
    var rows=names.map(function(n){
      var have=copyCount(n), want=multiKeep[n], s=(typeof _qStyle==='function'?_qStyle(n,'unique'):'');
      return '<div class="vmk-row" data-mk="'+esc(n)+'">'+art(n)
        +'<span class="vmk-name" data-arttip="'+esc(n)+'"'+s+' onclick="window.openDrop&&window.openDrop(\''+jsArg(n)+'\')">'+esc(n)+'</span>'
        +'<span class="vmk-grp"><span class="vmk-grp-lbl">have</span><button class="vmk-step" onclick="window.vaultCopyAdjust(\''+jsArg(n)+'\',-1)"'+(have<=0?' disabled':'')+'>−</button><span class="vmk-num'+(have>=want?' vmk-have-full':'')+'">'+have+'</span><button class="vmk-step" onclick="window.vaultCopyAdjust(\''+jsArg(n)+'\',1)"'+(have>=want?' disabled':'')+'>+</button></span>'
        +'<span class="vmk-grp"><span class="vmk-grp-lbl">want</span><button class="vmk-step" onclick="window.vaultTargetBump(\''+jsArg(n)+'\',-1)">−</button><span class="vmk-num">'+want+'</span><button class="vmk-step" onclick="window.vaultTargetBump(\''+jsArg(n)+'\',1)">+</button></span>'
        +'<button class="vmk-rm" onclick="window.vaultMultiKeepRemove(\''+jsArg(n)+'\')" title="remove from multi-copy keepers (back to single)">✕</button></div>';
    }).join('');
    el.innerHTML='<details class="vmk-det"><summary class="vmk-sum to-sum"><span class="to-emblem">📦</span><span class="to-hd"><span class="to-hd-top"><span class="to-st">Multi-copy Keepers</span></span><span class="to-subt">staples you want several of — targets editable; a re-read under target is kept as a spare, not a discard</span></span><span class="to-rule"></span><span class="to-chev">▾</span></summary><div class="vmk-body">'
      +(rows||'<div style="padding:8px 4px;color:#8a9aa8;font-size:12px">No multi-copy items yet — add one below.</div>')
      +'<div class="vmk-add"><input id="vmk-add-input" type="text" autocomplete="off" placeholder="Add an item to collect spares of (e.g. Gore Rider)" onkeydown="if(event.key===\'Enter\')window.vaultMultiKeepAdd()"><button onclick="window.vaultMultiKeepAdd()">+ Add</button></div></div></details>';
  }
  window.vaultCopyAdjust=function(n,d){ var want=multiTarget(n), nv=Math.max(0,Math.min(want,copyCount(n)+d)); if(nv<=1){ delete copies[n]; } else { copies[n]=nv; } try{ (typeof persist==='function')?persist():persistOwned(); }catch(e){} renderMultiKeep(); renderVaultRegistered(); };
  window.vaultTargetBump=function(n,d){ var nt=multiTarget(n)+d; if(nt<2){ window.vaultMultiKeepRemove(n); return; } multiKeep[n]=nt; if(copies[n]&&copies[n]>nt) copies[n]=nt; try{ (typeof persist==='function')?persist():persistOwned(); }catch(e){} renderMultiKeep(); renderVaultRegistered(); };
  window.vaultMultiKeepRemove=function(n){ delete multiKeep[n]; delete copies[n]; try{ (typeof persist==='function')?persist():persistOwned(); }catch(e){} renderMultiKeep(); renderVaultRegistered(); };
  window.vaultMultiKeepAdd=function(){ var inp=document.getElementById('vmk-add-input'); if(!inp) return; var raw=(inp.value||'').trim(); if(!raw) return; var n=_resolveGrailName(raw); if(!n){ status('“'+raw+'” isn’t a grail item — check the spelling'); return; } if(multiKeep[n]>1){ status(n+' is already a multi-copy keeper'); } else { multiKeep[n]=2; } inp.value=''; try{ (typeof persist==='function')?persist():persistOwned(); }catch(e){} renderMultiKeep(); renderVaultRegistered(); };
  // scrollable "Registered" triage panel — every ✓owned item tagged muled / unsorted / not-muled
  // (account-shared stash), each with a ✕ throw-out, so the AI read is observable and the intake
  // count reconciles (Konyo: "scrollbar for registered · muled / not muled · throw out").
  function renderVaultRegistered(){
    var el=document.getElementById('vault-registered'); if(!el) return;
    var poolM=ownedPool();
    var all=Array.from(owned).filter(function(n){ return !isAggregate(n) && (isSharedStash(n) || poolM.indexOf(n)>=0); }).sort();
    var findNames=(typeof magicFinds==='object'&&magicFinds)?Object.keys(magicFinds).sort():[];
    var _unkCount=(typeof unknownReads!=='undefined'&&unknownReads)?unknownReads.size:0;
    if(!all.length && !findNames.length && !_unkCount){ el.hidden=true; el.innerHTML=''; return; }
    el.hidden=false;
    var muled=[], notMuled=[], loose=[];
    all.forEach(function(n){
      if(isSharedStash(n)){ notMuled.push(n); return; }
      var m=assign[n]?muleById(assign[n]):null;
      if(m) muled.push([n,m]); else loose.push(n);
    });
    function row(n, tag){
      var s=(typeof _qStyle==='function'?_qStyle(n,'unique'):'');
      var _cc=copyCount(n), _ct=multiTarget(n);
      // v347 — ×N badge: multi-keep shows "×have/target"; a normal item with duplicates shows "×N"
      // (you own more than one — duplicate shots are counted, not silently collapsed).
      var _badge=(_ct>1)
        ? '<span class="vrg-copies'+(_cc>=_ct?' vrg-copies-full':'')+'" title="'+_cc+' of '+_ct+' wanted copies">×'+_cc+'<span class="vrg-copies-t">/'+_ct+'</span></span>'
        : (_cc>1 ? '<span class="vrg-copies vrg-copies-dup" title="you own '+_cc+' of this — '+(_cc-1)+' duplicate'+(_cc-1===1?'':'s')+' read">×'+_cc+'</span>' : '');
      // v351 — trade-value tier badge (maxroll/DarkHumility): instantly see if an owned item is High … Trash.
      var _vt=(typeof _itemValue==='function')?_itemValue(n):'';
      var _vb=_vt?'<span class="vrg-val vrg-val-'+_vt+'" title="trade value: '+((_VAL_LABEL&&_VAL_LABEL[_vt])||_vt)+' (maxroll tier list)">'+((_VAL_LABEL&&_VAL_LABEL[_vt])||_vt)+'</span>':'';
      return '<div class="vrg-row" data-vault-item="'+esc(n)+'" data-arttip="'+esc(n)+'" style="cursor:pointer" onclick="window.openDrop&&window.openDrop(\''+jsArg(n)+'\')">'+art(n)
        +'<span class="vrg-name"'+s+'>'+esc(n)+'</span>'+_badge+_vb+tag
        +'<button class="vrg-x" onclick="event.stopPropagation();window.vaultUnown(\''+jsArg(n)+'\')" title="throw out — remove from ✓ owned (AI misread / junk)">✕</button></div>';
    }
    // v342.21 — render each bucket as its OWN COLUMN (header + independent scrollbar) so all sections are
    // visible side-by-side at once, per Konyo. Responsive grid wraps on narrow screens.
    var unkNames=(typeof unknownReads!=='undefined'&&unknownReads)?_dedupCanon(Array.from(unknownReads).filter(function(n){ return !owned.has(n) && !(magicFinds&&magicFinds[n]); }).sort()):[];   // v439 — collapse OCR-variant dupes
    var _qcol={magic:'#7aa2ff',rare:'#ffd54a',crafted:'var(--q-orange,#ffa800)'};
    function _col(cls, title, count, rowsHtml){
      return '<div class="vrg-col"><div class="vrg-col-h '+cls+'">'+title+'<span class="vrg-col-ct">'+count+'</span></div>'
        +'<div class="vrg-col-body">'+rowsHtml+'</div></div>';
    }
    var cols=[];
    if(muled.length) cols.push(_col('vrg-gh-mule','🏦 Muled',muled.length, muled.map(function(p){ return row(p[0],'<span class="vrg-tag vrg-tag-mule">→ '+esc(p[1].name)+'</span>'); }).join('')));
    if(loose.length) cols.push(_col('vrg-gh-loose','🎒 Unsorted',loose.length, loose.map(function(n){ return row(n,'<span class="vrg-tag vrg-tag-loose">in dock</span>'); }).join('')));
    if(notMuled.length) cols.push(_col('vrg-gh-shared','📦 Not muled',notMuled.length, notMuled.map(function(n){ return row(n,'<span class="vrg-tag vrg-tag-shared">shared</span>'); }).join('')));
    if(findNames.length) cols.push(_col('vrg-gh-magic','🔮 Magic &amp; Rare',findNames.length, findNames.map(function(n){
        var q=_mfQual(n), col=_qcol[q]||_qcol.magic, _src=(typeof _magicArtSrc==='function')?_magicArtSrc(_mfBase(n)||n):null;
        var _icon=_src?'<span class="d2art-wrap sm" role="img" aria-label="'+esc(n)+'"><img class="d2art-img" src="'+_src+'" alt="" loading="lazy"></span>':'<span class="vrg-mdot" style="background:'+col+'"></span>';
        return '<div class="vrg-row" data-magic-find="'+esc(n)+'" data-arttip="'+esc(n)+'" style="cursor:pointer" onclick="window.openDrop&&window.openDrop(\''+jsArg(n)+'\')">'+_icon
          +'<span class="vrg-name" style="color:'+col+'" data-arttip="'+esc(n)+'">'+esc(n)+'</span>'
          +'<span class="vrg-tag" style="color:'+col+'">'+q+'</span>'
          +'<button class="vrg-x" onclick="event.stopPropagation();window.vaultThrowFind(\''+jsArg(n)+'\')" title="throw out — remove from Magic &amp; Rare">✕</button></div>';
      }).join('')));
    if(unkNames.length) cols.push(_col('vrg-gh-unknown','🗑 Throw-out',unkNames.length, unkNames.map(function(n){
        // v348 — show HD art + hover for throw-out items so you can SEE what's being discarded (a real
        // unique vs a junk base). Strip the " (Nos low base)" / "(rare)" suffix to a clean name, then
        // resolve grail art (real unique) → base sprite. data-arttip floats the in-game card on hover.
        var _clean=String(n).replace(/\s*\((?:[?\d]+os\s+)?low base\)\s*$/i,'').replace(/\s*\((?:rare|magic|crafted)\)\s*$/i,'').trim();
        var _src=(typeof artUrl==='function'?artUrl(_clean):'')||(typeof _magicArtSrc==='function'?_magicArtSrc(_clean):'')||'';
        var _icon=_src?'<span class="d2art-wrap sm" role="img" aria-label="'+esc(_clean)+'"><img class="d2art-img" src="'+_src+'" alt="" loading="lazy"></span>':'<span class="vrg-mdot" style="background:#9aa6b2"></span>';
        // v349 — data-arttip uses the FULL name (resolves to the rich throw-out card); whole row is
        // clickable → opens the review card, like every other section.
        return '<div class="vrg-row" data-unknown-read="'+esc(n)+'" data-arttip="'+esc(n)+'" title="'+esc(n)+'" style="cursor:pointer" onclick="window.openDrop&&window.openDrop(\''+jsArg(n)+'\')">'+_icon
          +'<span class="vrg-name" style="color:#aeb8c4" data-arttip="'+esc(n)+'">'+esc(n)+'</span>'
          +'<button class="vrg-keep" onclick="event.stopPropagation();window.vaultKeepUnknown(\''+jsArg(n)+'\')" title="keep — move to 🔮 Magic &amp; Rare">🔮</button>'
          +'<button class="vrg-x" onclick="event.stopPropagation();window.vaultDismissUnknown(\''+jsArg(n)+'\')" title="dismiss — discard this read">✕</button></div>';
      }).join('')));
    var h='<div class="vrg-cols">'+cols.join('')+'</div>';
    // v342.20 — the GRAND total counts EVERYTHING read (grail + magic + throw-out), distinguished into
    // sections below. Konyo: "register the item regardless… distinguished but still a total amount."
    var _regTot=all.length+findNames.length+unkNames.length;
    el.innerHTML='<details class="vrg-det"><summary class="vrg-sum to-sum to-acc-blue"><span class="to-emblem">📋</span><span class="to-hd"><span class="to-hd-top"><span class="to-st">Registered</span><span class="to-ct">'+_regTot+'</span></span><span class="to-subt">grail · magic &amp; rare · throw-out — everything read, sorted</span></span><span class="to-rule"></span><span class="to-chev">▾</span></summary><div class="vrg-body">'+h+'</div></details>';
  }
  // v366 — DEDICATED Throw-Out Review: its own section that VISUALLY shows each discarded read paired with
  // the SOURCE SCREENSHOT it came from (synced from the per-screenshot breakdown) + a description, so Konyo
  // can see exactly what's being thrown out and recover a misread (🔮 keep) or confirm a discard (✕).
  function renderThrowoutReview(){
    var el=document.getElementById('vault-throwout'); if(!el) return;
    // v396.2 — RESCUE any RUNEWORD that's sitting in the throw-out pile from an OLD read (before runewords
    // were recognized). A runeword is NEVER junk: register it (owned), mark it forged in the Chronicle, mule
    // it by slot, and drop it from unknownReads. Konyo: "most certainly not throw out an Enigma."
    try {
      if (typeof unknownReads !== 'undefined' && unknownReads && typeof findRuneword === 'function'){
        var _rwOf = (typeof _rwResolve === 'function') ? _rwResolve : findRuneword;
        var _migr = [];
        unknownReads.forEach(function(n){ if (_rwOf(n)) _migr.push(n); });
        if (_migr.length){
          _migr.forEach(function(n){
            // v539 — a read that resolves to a runeword is recognized so it's NEVER thrown out, but it is NOT
            // auto-registered to owned (the RUNEWORDS locker) OR the Chronicle. OCR'd runeword NAMES are too
            // ambiguous — they come from UI text, a base's "can-make" list, or a Forge-tab screenshot — and kept
            // injecting phantom runewords into the RUNEWORDS locker + false "created" ticks (Konyo: "I didn't
            // upload these runewords"). Forged runewords are managed ONLY via the Chronicle ✓ (which has undo).
            unknownReads.delete(n);
          });
          try { persistOwned && persistOwned(); saveA && saveA(); } catch(e){}   // rwMade intentionally NOT written here (v538)
        }
      }
    } catch(e){}
    var names=(typeof unknownReads!=='undefined'&&unknownReads)
      ? _dedupCanon(Array.from(unknownReads).filter(function(n){ return !owned.has(n) && !(magicFinds&&magicFinds[n]); }).sort())   // v439 — collapse OCR-variant dupes
      : [];
    if(!names.length){ el.hidden=true; el.innerHTML=''; return; }
    el.hidden=false;
    // map each throw-out name → the screenshot it was read from (newest stored thumb wins)
    // v571 — keep the FILENAME even when the thumb was pruned: the card then loads the ORIGINAL file from
    // the linked folder (native HD) via _vHydrateShots. "no shot" only remains when the filename is unknown.
    var shotOf={}, shotOfClean={};
    try { var _sK=function(x){ return String(x||'').replace(/\s*\([^)]*\)\s*$/,'').toLowerCase().trim(); };
      journal().forEach(function(s){ (s.pf||[]).forEach(function(f){ if(f.unr && f.unr.length){ f.unr.forEach(function(u){
        var rec={th:(f.th||''), ff:(f.ff||f.f||'')};
        if(!shotOf[u] || (!shotOf[u].th && f.th)) shotOf[u]=rec;
        var ck=_sK(u); if(!shotOfClean[ck] || (!shotOfClean[ck].th && f.th)) shotOfClean[ck]=rec;   // v572.1 — OCR-variant names ("Blade Bow" vs "Blade Bow (4os low base)") still find their shot
      }); } }); }); } catch(e){}
    var cardFor=function(n){
      var clean=(typeof _throwClean==='function')?_throwClean(n):n;
      // v573 — Konyo's Superior Flail case: a name-only read of a QUALITY-PREFIXED base ("Superior Flail")
      // must still be recognised as the base TYPE (Flail — the ideal HotO base!), not dismissed as a misread.
      var cleanB=clean.replace(/^(?:Superior|Ethereal|Eth|Cracked|Crude|Damaged|Low Quality)\s+/i,'').trim();
      var _wasSup=/^Superior\s+/i.test(clean);
      var isBase=/low base\)\s*$/i.test(n);
      var sock=/\((\d+)os/i.exec(n);
      var src=(typeof artUrl==='function'?artUrl(clean):'')||(typeof _magicArtSrc==='function'?_magicArtSrc(clean):'')||'';
      var artH=src?'<span class="d2art-wrap sm" role="img" aria-label="'+esc(clean)+'"><img class="d2art-img" src="'+esc(src)+'" alt="" loading="lazy"></span>':'<span class="to-glyph">🗑</span>';
      var nm=(typeof _vColorName==='function')?_vColorName(n):('<span style="color:#aeb8c4">'+esc(n)+'</span>');
      var sh=shotOf[n] || shotOfClean[String(n||'').replace(/\s*\([^)]*\)\s*$/,'').toLowerCase().trim()];
      // v571 — three-way: stored thumb → img now; filename only → placeholder hydrated from the LINKED
      // FOLDER's original file (native HD, _vHydrateShots); nothing known → "no shot".
      var shotH=(sh && sh.th)
        ? '<img class="to-shot" src="'+esc(sh.th)+'" loading="lazy" data-shot="'+esc(sh.ff)+'" title="click to open this screenshot full-size — '+esc(sh.ff)+'" onclick="window._shotLightbox&&window._shotLightbox(this.dataset.shot,this.src)">'
        : (sh && sh.ff)
        ? '<div class="to-shot to-noshot" data-ffsrc="'+esc(sh.ff)+'" data-artfb="'+esc(src)+'" title="loading the screenshot from your linked folder — '+esc(sh.ff)+'">📂 …</div>'
        : (src
        ? '<div class="to-shot to-artshot" title="no screenshot exists for this item — showing its in-game HD art · click to enlarge" onclick="window._shotLightbox&&window._shotLightbox(\'\', this.querySelector(\'img\').src)"><img src="'+esc(src)+'" alt="" loading="lazy"></div>'
        : '<div class="to-shot to-noshot" title="no screenshot stored for this read (older scan)">no shot</div>');   // v609 — Konyo: "no shot where it should be HD photos of that specific item"
      // v368 — even when the AI read only the NAME (no socket text → not flagged a base), recognise a
      // known weapon/armor base TYPE so a real runeword base (e.g. "Dimensional Blade", a sword) shows its
      // runeword potential instead of a bare "non-grail/misread" — so Konyo doesn't dismiss a good base.
      var _isKnownBase = (typeof _baseCats==='function') && Object.keys(_baseCats(cleanB)).length>0;
      // v394 — a LOW set piece routed here on purpose (Sigon's/Sander's/etc.): it's tracked for the grail,
      // just not worth muling. Show the right message instead of the generic "misread".
      var _loSet = (typeof findSetPiece==='function') && findSetPiece(clean);
      var why = _loSet
        ? ('Low set piece — <b>'+esc(((_loSet.set&&_loSet.set.name)||'')||'set')+'</b>. Already ticked for your grail/set tracker; not worth muling — safe to <b>sell or throw out</b>.'
            )
        : (isBase
        ? 'A white/grey socketed base'+(sock?' ('+sock[1]+' sockets)':'')+' — low bases are filtered out of grail. Keep only if it’s a runeword / craft base.'
        : (_isKnownBase
            ? 'Read as a base item, not a grail unique — if it has good sockets, keep it as a runeword / craft base (5-6 sockets are always worth keeping).'
            : 'Read but not in your tracked grail — a non-grail unique/rare, or a misread. Recover it or discard.'));
      // v562 — CHRONICLE SYNC: for a known base, the keep-or-toss advice reads your Chronicle (d2r_rwMade),
      // the same way the Forge/Smart AI does. All fitting words ✓ forged → say "throw it out" plainly;
      // words still unmade → name them, so the generic "keep if good sockets" hedge never contradicts the plan.
      try {
        if ((isBase||_isKnownBase) && !_loSet && typeof _baseUnmadeRunewords==='function' && typeof _isRunewordBase==='function' && _isRunewordBase(cleanB)){
          var _tun=_baseUnmadeRunewords(clean, sock ? +sock[1] : 0);   // v614 — FULL quality-carrying name: the Superior Larzuk-max-only rule must fire here like it does in routing
          // v602 — Konyo's 1os Suwayyah / Pattern bug: an empty exact-fit list does NOT mean "✓ forged" —
          // unmade words may exist at OTHER socket counts (Pattern is 3os). Say the honest thing: the word
          // is still to create, THIS copy just can't host it (sockets are fixed) — hunt the right-count copy.
          var _tws=(sock && !_tun.length && typeof _baseUnmadeWrongSock==='function') ? _baseUnmadeWrongSock(clean, +sock[1]) : [];
          // v563 — spare split: unmade words all covered by an owned base → "you already hold one" verdict
          var _tsp=(_tun.length && typeof _spareBaseInfo==='function') ? _spareBaseInfo(n, _tun) : null;
          why = !_tun.length
            ? (_tws.length
                ? '<span style="color:#e9b96e">A '+esc(clean)+' ('+sock[1]+' socket'+(+sock[1]===1?'':'s')+') — <b>'+esc(_tws[0].n)+' ('+_tws[0].s+'os) is STILL UNMADE</b>'+(_tws.length>1?' (+'+(_tws.length-1)+' more)':'')+', but sockets are fixed once socketed: this '+sock[1]+'os copy can never host it → this copy is <b>safe to throw out</b> — hunt an <b>unsocketed or '+_tws[0].s+'os '+esc(clean)+'</b> instead.</span>'
                : '<span style="color:#f0c060">A '+esc(clean)+(sock?' ('+sock[1]+' sockets)':'')+' — nothing left for it: its runewords are <span style="color:#8fd0a0">✓ forged</span> or belong in endgame bases → <b>safe to throw out</b>.</span>')
            : (_tsp && !_tsp.uncovered.length)
            ? '<span style="color:#f0c060">A '+esc(clean)+(sock?' ('+sock[1]+' sockets)':'')+' — <b>spare</b>: its runewords ('+esc(Object.keys(_tsp.covered).slice(0,3).join(', '))+') are already covered by <b>'+esc(_tsp.covered[Object.keys(_tsp.covered)[0]][0])+'</b>, a base you hold → safe to throw out.</span>'
            : 'A '+esc(clean)+(sock?' ('+sock[1]+' sockets)':'')+' — <b>still needed</b>: it can host <b>'+esc(((_tsp&&_tsp.uncovered.length)?_tsp.uncovered:_tun.map(function(r){return r.n;})).slice(0,3).join(', '))+(_tun.length>3?' +'+(_tun.length-3)+' more':'')+'</b>, unmade in your Chronicle. Keep it if the sockets are right.';
        }
      } catch(e){}
      var rwl=((isBase||_isKnownBase) && typeof _baseRWLine==='function')?_baseRWLine(cleanB, sock ? +sock[1] : 0, _wasSup):'';
      // v602 — Larzuk/cube guide = UNSOCKETED items only: an already-socketed copy is fixed at its count
      if ((isBase||_isKnownBase) && !sock && typeof _socketGuideLine==='function'){ var _sgl=_socketGuideLine(cleanB, _wasSup?'superior':'normal'); if(_sgl) rwl+=_sgl; }
      // v397.2 — one-click socket fix: when a KNOWN base was read name-only (the AI missed the faint "Socketed
      // (N)" line — Konyo's Elder Staff / Superior Trident / Wrist Sword), let him set the real count in one tap.
      // It registers "<Base> (Nos)" as a socketed runeword/craft base + mules it. No re-scan needed.
      var _setter = (_isKnownBase && !sock && !_loSet)
        ? '<div class="to-sockset" style="margin-top:5px;font-size:10px;color:#b5a48a">🔩 AI missed the sockets? set the real count: '
            + [1,2,3,4,5,6].map(function(s){ return '<button onclick="event.stopPropagation();window.vaultSetSockets(\''+jsArg(n)+'\','+s+')" title="register as a '+s+'-socket '+esc(clean)+'" style="margin:0 1px;padding:1px 6px;border:1px solid rgba(127,212,255,.45);background:rgba(127,212,255,.1);color:#9fd4ff;border-radius:4px;cursor:pointer;font-size:10px">'+s+'</button>'; }).join('')
            + ' <button onclick="event.stopPropagation();window.vaultKeepAsBase(\''+jsArg(n)+'\')" title="it really is UNSOCKETED — keep it as a Larzuk / cube-gamble base" style="margin-left:4px;padding:1px 7px;border:1px solid rgba(240,192,96,.5);background:rgba(240,192,96,.1);color:#f0c060;border-radius:4px;cursor:pointer;font-size:10px">⚒ keep unsocketed</button>'
            + '</div>'
        : '';
      return '<div class="to-card">'
        + shotH
        + '<div class="to-body">'
        +   '<div class="to-top">'+artH+'<span class="to-name" data-arttip="'+esc(n)+'" style="cursor:pointer" onclick="window.openDrop&&window.openDrop(\''+jsArg(n)+'\')">'+nm+'</span>'+(sock?'<span class="to-sock">🔩 '+sock[1]+'os</span>':'')+((typeof copyCount==='function'&&copyCount(n)>1)?'<span class="to-sock" style="border-color:rgba(240,192,96,.5);color:#f0c060" title="you have '+copyCount(n)+' of these — separate screenshots, each a distinct item">×'+copyCount(n)+'</span>':'')+'</div>'
        +   '<div class="to-why">'+why+'</div>'+rwl+_setter
        +   '<div class="to-acts"><button class="vrg-keep" onclick="window.vaultKeepUnknown(\''+jsArg(n)+'\')" title="keep — move to 🔮 Magic &amp; Rare">🔮 keep</button>'
        +     '<button class="vrg-x" onclick="window.vaultDismissUnknown(\''+jsArg(n)+'\')" title="dismiss — discard this read">✕ dismiss</button></div>'
        + '</div></div>';
    };
    // v440 — QUIETER throw-out: the repetitive low-set-piece cards ("track for grail, throw out") collapse under
    // ONE sub-header so the review reads as the few items that actually need a decision, not a wall of sets.
    var _loSetN=[], _otherN=[];
    names.forEach(function(n){ var _c=(typeof _throwClean==='function')?_throwClean(n):n; if((typeof findSetPiece==='function')&&findSetPiece(_c)) _loSetN.push(n); else _otherN.push(n); });
    var cards=_otherN.map(cardFor).join('');
    var _loBlock=_loSetN.length?('<details class="to-subgroup"><summary class="to-subsum">🧩 Low set pieces — tracked for grail, safe to sell/throw <span class="to-ct">'+_loSetN.length+'</span><span class="to-chev">▾</span></summary><div class="to-grid">'+_loSetN.map(cardFor).join('')+'</div></details>'):'';
    el.innerHTML='<details class="to-det" open><summary class="to-sum"><span class="to-emblem">🗑</span><span class="to-hd"><span class="to-hd-top"><span class="to-st">Throw-Out Review</span><span class="to-ct">'+names.length+'</span></span><span class="to-subt">what you’re discarding — each read shown with the screenshot it came from</span></span><span class="to-rule"></span><span class="to-chev">▾</span></summary>'
      + (cards?'<div class="to-grid">'+cards+'</div>':'')+_loBlock+'</details>';
    try { window._vHydrateShots(el); } catch(e){}   // v571 — pull pruned shots back from the linked folder
  }
  // v455 — SOCKETED / LARZUK REVIEW: the EXACT runeword tool from the throw-out review (_baseRWLine), now for the
  // MULED socketed + Larzuk bases. Konyo: socketed items got muled (good) but never showed their runeword potential
  // inline like throw-out items do. This surfaces — without a click — what runeword each socketed base can make
  // (exact socket count + base TYPE match, multi-base AND specialized words, already-created split via the Chronicle)
  // and, for an unsocketed Larzuk base, what it unlocks once socketed to its max. Throw-out section is untouched.
  function renderSocketedReview(){
    var el=document.getElementById('vault-socketed'); if(!el) return;
    // owned items that are socketed / Larzuk bases (routing key cat:'Socketed bases' — both already-socketed
    // "<Base> (Nos)" keepers AND unsocketed "<Base> (Larzuk base)" candidates; nothing else qualifies).
    var names=[];
    try { Array.from(owned).forEach(function(n){ if(window.EXTRA_ITEMS && EXTRA_ITEMS[n] && EXTRA_ITEMS[n].cat==='Socketed bases') names.push(n); }); } catch(e){}
    names.sort();
    if(!names.length){ el.hidden=true; el.innerHTML=''; return; }
    el.hidden=false;
    // map each socketed read → the screenshot it was registered from (f.nw = newly-recognised reads; newest thumb wins)
    var shotOf={};
    try { journal().forEach(function(s){ (s.pf||[]).forEach(function(f){ if(f.nw && f.nw.length){ f.nw.forEach(function(u){ if(!shotOf[u] || (!shotOf[u].th && f.th)) shotOf[u]={th:(f.th||''), ff:(f.ff||f.f||'')}; }); } }); }); } catch(e){}   // v571 — filename kept even when the thumb was pruned
    var cardFor=function(n){
      var ent=(window.EXTRA_ITEMS&&EXTRA_ITEMS[n])||{};
      var base=ent.base||n;
      var sockets=(typeof ent.sockets==='number')?ent.sockets:0;   // 0 = unsocketed Larzuk candidate
      var isSup=(typeof window._isSuperior==='function')&&window._isSuperior(n);
      // SAME engine as the throw-out card: exact-socket (when known) + base-TYPE match + already-created split.
      // For a 0-socket Larzuk base _baseRWLine falls back to its "socket to max" guidance automatically.
      var rwl=(typeof _baseRWLine==='function')?_baseRWLine(base, sockets, isSup):'';
      // v602 — Larzuk/cube guide = UNSOCKETED (Larzuk-candidate) entries only; a socketed copy is fixed
      if (sockets<1 && typeof _socketGuideLine==='function'){ var _sgl=_socketGuideLine(base, isSup?'superior':'normal'); if(_sgl) rwl+=_sgl; }
      var src=(typeof artUrl==='function'?(artUrl(n)||artUrl(base)):'')||'';
      var artH=src?'<span class="d2art-wrap sm" role="img" aria-label="'+esc(n)+'"><img class="d2art-img" src="'+esc(src)+'" alt="" loading="lazy"></span>':'<span class="to-glyph">🔩</span>';
      var nm=(typeof _vColorName==='function')?_vColorName(n):('<span style="color:#aeb8c4">'+esc(n)+'</span>');
      var sh=shotOf[n];
      // v571 — three-way: stored thumb → img now; filename only → placeholder hydrated from the LINKED
      // FOLDER's original file (native HD, _vHydrateShots); nothing known → "no shot".
      var shotH=(sh && sh.th)
        ? '<img class="to-shot" src="'+esc(sh.th)+'" loading="lazy" data-shot="'+esc(sh.ff)+'" title="click to open this screenshot full-size — '+esc(sh.ff)+'" onclick="window._shotLightbox&&window._shotLightbox(this.dataset.shot,this.src)">'
        : (sh && sh.ff)
        ? '<div class="to-shot to-noshot" data-ffsrc="'+esc(sh.ff)+'" data-artfb="'+esc(src)+'" title="loading the screenshot from your linked folder — '+esc(sh.ff)+'">📂 …</div>'
        : (src
        ? '<div class="to-shot to-artshot" title="no screenshot exists for this item — showing its in-game HD art · click to enlarge" onclick="window._shotLightbox&&window._shotLightbox(\'\', this.querySelector(\'img\').src)"><img src="'+esc(src)+'" alt="" loading="lazy"></div>'
        : '<div class="to-shot to-noshot" title="no screenshot stored for this read (older scan)">no shot</div>');   // v609 — Konyo: "no shot where it should be HD photos of that specific item"
      var m=(typeof assign!=='undefined'&&assign[n]&&typeof muleById==='function')?muleById(assign[n]):null;
      var muleTag=m?'<span class="to-sock" style="border-color:rgba(127,212,255,.5);color:#9fd4ff" title="muled to '+esc(m.name)+'">🏦 '+esc(m.name)+'</span>':'';
      var sockBadge=sockets?('<span class="to-sock">🔩 '+sockets+'os</span>'):'<span class="to-sock" style="border-color:rgba(240,192,96,.5);color:#f0c060" title="unsocketed elite base — Larzuk/cube it">⚒ Larzuk</span>';
      var ethBadge=((typeof window._isEthereal==='function')&&window._isEthereal(n))?'<span class="to-sock" style="border-color:rgba(127,212,255,.5);color:#9fd4ff" title="ethereal — +50% damage/defense, can’t be repaired (best on a merc / static piece)">⊘ ETH</span>':'';
      // v463 — show the base TIER (Normal / Exceptional / Elite) right on the card. Konyo: "how do I know if it's
      // normal/exceptional/elite already?" — now it's answered at a glance, no need to open the detail card.
      var tlbl=(typeof _itemTierLabel==='function')?_itemTierLabel(n):'';
      var tierH=tlbl?'<div class="att-meta" style="font-size:10px;color:#9c8d6b;margin-bottom:3px">'+esc(tlbl)+'</div>':'';
      var why=sockets
        ? 'A <b>'+sockets+'-socket '+esc(base)+'</b> — kept &amp; muled. Runewords it can hold right now:'
        : 'An <b>unsocketed '+esc(base)+'</b> base — kept &amp; muled. Socket it to its max for:';
      // v562 — CHRONICLE VERDICT: this base was kept when it still served a word, but the Chronicle moved on.
      // If every runeword it can host is now ✓ forged, say so loudly — it's mule space you can free up.
      // v563 — SPARE VERDICT: still-unmade words, but every one is covered by a DIFFERENT base you hold
      // (the Forge already assigned it) → this copy is a spare, also free to go. Self-exclusion by label
      // means the assigned base itself never flags — with two Monarchs, exactly one stays, one flags spare.
      try {
        var _unm=(typeof _baseUnmadeRunewords==='function')?_baseUnmadeRunewords(n, sockets):null;   // v614 — the owned LABEL (carries Superior/Ethereal) drives the quality rules; ent.base is stripped
        // v603.1 — audit sweep caught the SAME empty-list lie here (4th surface): a muled wrong-count copy
        // (1os Suwayyah, Pattern unmade) must not claim "✓ forged" — name the word + the copy to hunt.
        var _uws=(_unm && !_unm.length && sockets>=1 && typeof _baseUnmadeWrongSock==='function')?_baseUnmadeWrongSock(n, sockets):[];
        if (_unm && !_unm.length) why=_uws.length
          ? '<span style="color:#e9b96e">🗑 <b>Free to throw out</b> — <b>'+esc(_uws[0].n)+' ('+_uws[0].s+'os) is STILL UNMADE</b>'+(_uws.length>1?' (+'+(_uws.length-1)+' more)':'')+', but sockets are fixed once socketed: this '+sockets+'os copy can never host it. Free the mule space — hunt an <b>unsocketed or '+_uws[0].s+'os '+esc(base)+'</b> instead:</span>'
          : '<span style="color:#f0c060">🗑 <b>Free to throw out</b> — nothing left for this '
          + (sockets?sockets+'-socket ':'')+esc(base)+' can host: its runewords are <span style="color:#8fd0a0">✓ forged</span> or belong in endgame bases. No job left:</span>';
        else if (_unm && _unm.length && typeof _spareBaseInfo==='function'){
          var _spv=_spareBaseInfo(n, _unm);
          if (!_spv.uncovered.length){
            var _svw=Object.keys(_spv.covered);
            why='<span style="color:#f0c060">🗑 <b>Spare — free to throw out</b> — its runeword'+(_svw.length>1?'s':'')+' ('
              + esc(_svw.slice(0,3).join(', '))+') '+(_svw.length>1?'are':'is')+' already covered by <b>'+esc(_spv.covered[_svw[0]][0])
              + '</b>, another base you hold. The Forge plans around that one, not this copy:</span>';
          }
        }
      } catch(e){}
      // v462 — one-tap socket-count FIX: the AI sometimes misreads a faint "Socketed (N)" as 0 (Konyo's Superior
      // Champion Axe). Let him correct an already-registered base in place without re-uploading.
      var fixRow='<div class="to-sockset" style="margin-top:6px;font-size:10px;color:#b5a48a">🔩 wrong count? set the real sockets: '
        + [1,2,3,4,5,6].map(function(s){ return '<button onclick="event.stopPropagation();window.vaultFixSockets(\''+jsArg(n)+'\','+s+')" title="re-register '+esc(base)+' as a '+s+'-socket base" style="margin:0 1px;padding:1px 6px;border:1px solid rgba(127,212,255,.45);background:rgba(127,212,255,.1);color:#9fd4ff;border-radius:4px;cursor:pointer;font-size:10px">'+s+'</button>'; }).join('')
        + '</div>';
      return '<div class="to-card">'
        + shotH
        + '<div class="to-body">'
        +   '<div class="to-top">'+artH+'<span class="to-name" data-arttip="'+esc(n)+'" style="cursor:pointer" onclick="window.openDrop&&window.openDrop(\''+jsArg(n)+'\')">'+nm+'</span>'+sockBadge+ethBadge+muleTag+((typeof copyCount==='function'&&copyCount(n)>1)?'<span class="to-sock" style="border-color:rgba(240,192,96,.5);color:#f0c060" title="you have '+copyCount(n)+' of these">×'+copyCount(n)+'</span>':'')+'</div>'
        +   tierH+'<div class="to-why">'+why+'</div>'+rwl+fixRow
        + '</div></div>';
    };
    var cards=names.map(cardFor).join('');
    el.innerHTML='<details class="to-det" open><summary class="to-sum"><span class="to-emblem">🔩</span><span class="to-hd"><span class="to-hd-top"><span class="to-st">Socketed &amp; Larzuk Review</span><span class="to-ct">'+names.length+'</span></span><span class="to-subt">muled socketed / Larzuk bases — what runewords each can still make (✓ created cancelled out)</span></span><span class="to-rule"></span><span class="to-chev">▾</span></summary>'
      + '<div class="to-grid">'+cards+'</div></details>';
    try { window._vHydrateShots(el); } catch(e){}   // v571 — pull pruned shots back from the linked folder
  }
  // v571 — swap "no shot" placeholders for the ORIGINAL screenshot file from the linked folder (object URL,
  // native 1920×1080). Runs after the review grids render; a file no longer on disk keeps the plain box.
  window._vHydrateShots = function(root){
    try {
      if (!root || typeof window._vShotFromFolder !== 'function') return;
      root.querySelectorAll('.to-noshot[data-ffsrc]').forEach(function(ph){
        var ff = ph.getAttribute('data-ffsrc');
        window._vShotFromFolder(ff).then(function(u){
          if (!ph.parentNode) return;
          if (u){
            var img = document.createElement('img');
            img.className = 'to-shot'; img.loading = 'lazy'; img.src = u;
            img.setAttribute('data-shot', ff);
            img.title = 'click to open this screenshot full-size — ' + ff;
            img.onclick = function(){ if (window._shotLightbox) window._shotLightbox(ff, u); };
            ph.parentNode.replaceChild(img, ph);
            return;
          }
          // v609.1 — hydration failed. Permission lapsed after a restart → ONE-TAP re-authorize that
          // re-hydrates every card and opens the tapped screenshot (the exact one it's tagged to).
          // Folder unlinked / file deleted → the item's own HD art (click-to-enlarge) — never a dead box.
          var pfn = (typeof window._vFolderPerm === 'function') ? window._vFolderPerm() : Promise.resolve('none');
          pfn.then(function(perm){
            if (!ph.parentNode) return;
            if (perm === 'prompt'){
              ph.textContent = '📂 tap to load';
              ph.title = 'browser restarted — one tap re-links your screenshot folder and opens this exact shot (' + ff + ')';
              ph.style.cursor = 'pointer'; ph.style.color = '#7fd4ff';
              ph.onclick = function(ev){ ev.stopPropagation();
                window._vFolderReauth().then(function(ok){
                  if (!ok) return;
                  window._vHydrateShots(document);
                  window._vShotFromFolder(ff).then(function(u2){ if (u2 && window._shotLightbox) window._shotLightbox(ff, u2); });
                });
              };
              return;
            }
            var art = ph.getAttribute('data-artfb');
            if (art){
              var d = document.createElement('div');
              d.className = 'to-shot to-artshot';
              d.title = 'original screenshot unavailable (' + ff + ') — showing this item\'s in-game HD art · click to enlarge';
              d.innerHTML = '<img src="' + art + '" alt="" loading="lazy">';
              d.onclick = function(){ if (window._shotLightbox) window._shotLightbox('', art); };
              ph.parentNode.replaceChild(d, ph);
            } else { ph.textContent = 'no shot'; ph.removeAttribute('data-ffsrc'); }
          });
        });
      });
    } catch(e){}
  };
  function renderVault(){
    var dock=document.getElementById('vault-dock'), shelf=document.getElementById('vault-shelf');
    if (!dock || !shelf) return;
    var poolAll=ownedPool();
    // account-shared-stash items (runes/essences/shards/statues) are recorded but NEVER muled —
    // keep them OUT of the dock/mules (they live in the Registered panel's "not muled" group).
    var pool=poolAll.filter(function(n){ return !isSharedStash(n); });
    renderMultiKeep();
    renderVaultRegistered();
    renderThrowoutReview();
    renderSocketedReview();   // v455 — runeword tool for the muled socketed/Larzuk bases (same _baseRWLine engine)
    // prune assignments of items no longer owned or mules deleted (v409 — but KEEP the '__keep' sentinel:
    // Anni/Torch/Gheed's are "kept in inventory", recorded as handled so they don't nag in the dock; muleById
    // can't resolve '__keep', so without this guard the prune would wrongly delete it every render).
    Object.keys(assign).forEach(function(n){ if(pool.indexOf(n)<0 || (assign[n]!=='__keep' && !muleById(assign[n]))) delete assign[n]; });
    // v360 — shared-stash items (runes · essences · Worldstone shards · Colossal statues · sunders) are
    // NEVER muled, so they don't belong in the draggable "unsorted" dock — they live in the SHARED STASH locker.
    var unsorted = pool.filter(function(n){ return !assign[n] && !isSharedStash(n); });
    // v251: the dock's own "Auto-Sort" widget — appears only when items are unsorted,
    // sends every loose item back to its proper mule/alt in one click (vaultAutoAssign).
    var dbar=document.getElementById('vault-dock-bar');
    if (dbar){
      if (unsorted.length){
        dbar.hidden=false;
        dbar.innerHTML='<span class="vdb-label">🎒 Unsorted dock<span class="vdb-count">'+unsorted.length+'</span></span>'
          +'<span class="vdb-actions">'
          +'<button class="vault-clear-btn" onclick="window.vaultClearUnsorted()" title="Delete every UNSORTED item from the dock — items already filed in a mule are NOT touched">'
          +'<span class="vcb-x">🗑</span><span>Delete unsorted</span></button>'
          +'<button class="vault-resort-btn" onclick="window.vaultAutoAssign()" title="Auto-Sort: send every unsorted item back to its proper mule / alt">'
          +'<span class="vrb-wand">🪄</span><span>Auto-Sort to Mules</span><span class="vrb-go">→</span></button>'
          +'</span>';
      } else { dbar.hidden=true; dbar.innerHTML=''; }
    }
    renderVaultKeep();
    dock.innerHTML = unsorted.map(function(n){
      var _vr = (typeof _artRarity==='function') ? _artRarity(n) : '';
      return '<span class="vault-chip'+(_vr?' vc-r-'+_vr:'')+(selectedChip===n?' vc-selected':'')+'" draggable="true" data-vault-item="'+esc(n)+'" title="drag onto a locker — or click, then click a locker">'+art(n)+'<span class="vault-chip-name"'+(typeof _qStyle==='function'?_qStyle(n,'unique'):'')+'>'+esc(n)+'</span>'
        +'<button class="vc-unown" onclick="event.stopPropagation();window.vaultUnown(\''+jsArg(n)+'\')" title="not mine — remove from ✓ owned (AI misread? this erases it)">✕</button></span>';
    }).join('');
    var byMule={};
    Object.keys(assign).forEach(function(n){ (byMule[assign[n]]=byMule[assign[n]]||[]).push(n); });
    shelf.innerHTML = roster.map(function(m){
      var items=(byMule[m.id]||[]).sort();
      // v364 — SHARED STASH = general cross-account storage (5 in-game shared tabs) you fill MANUALLY by
      // assigning items here; it's a normal assignable locker (runes/gems/materials are NOT synced here —
      // they have their own planners). Items come from byMule['shared'] like any other locker.
      // v342.5 — the MAGIC & RARE locker also holds the magicFinds keepers (rolled-name items kept OUT
      // of grail `owned`/`assign`, so they render straight from the magicFinds map, not from byMule).
      var magicItems=(m.id==='magic-rare' && typeof magicFinds==='object' && magicFinds) ? Object.keys(magicFinds).sort() : [];
      var total=items.length+magicItems.length;
      var cap=40, pct=Math.min(100, Math.round(total/cap*100));
      // v230: runes + materials (essences/shards/keys/organs/statues) live in RoW's
      // infinite shared stash — they are no longer muled, so no linked-tally lockers.
      var linked='';
      // set-completion rows for set lockers
      var setRows='';
      if (/^sets/.test(m.id) && typeof ITEMS!=='undefined'){
        var bySet={};
        items.forEach(function(n){ var t=tipOf(n); if(t && t.setName) (bySet[t.setName]=bySet[t.setName]||[]).push(n); });
        // group labels only — the bible tracks set AGGREGATES, so an X/Y fraction
        // here would lie; real per-piece completion lives in the Item-Set tracker
        setRows = Object.keys(bySet).sort().map(function(sn){
          return '<div class="vm-set-row"><span class="vs-done">✦</span> '+esc(sn)+'</div>';
        }).join('');
      }
      // v252: keep lockers compact — show the first 4 items, tuck the rest behind a
      // native "+ N more" expander (the hidden rows stay in the DOM, just collapsed).
      // v324: each item is now a D2 INVENTORY CELL TILE — sized by its footprint (1x1 up to 2x4)
      // and packed into a stash-style grid, like the in-game inventory (Konyo: "1x1 unit cell based
      // … 1x1 1-8x"). Rarity tints the frame; socketed bases show their os-count / 1H-2H badge.
      var SHOWN = 8;
      var itemRows = items.map(function(n){
        var cl = (typeof _itemCells === 'function') ? _itemCells(n) : {w:1,h:2};
        var rr = (typeof _artRarity === 'function') ? _artRarity(n) : '';
        var ex = (typeof EXTRA_ITEMS !== 'undefined') ? EXTRA_ITEMS[n] : null;
        var badge = (ex && ex.sockets) ? (ex.sockets + 'os')
          : (ex && ex.hand) ? (ex.hand === '1h' ? '1H' : '2H') : '';
        var osTag = badge ? '<span class="vm-cell-os">' + badge + '</span>' : '';
        // v347 — duplicate/multi-keep count badge on the locker cell (top-right)
        var _cc = (typeof copyCount === 'function') ? copyCount(n) : 1;
        var _cntTag = (_cc > 1) ? '<span class="vm-cell-cnt" title="you own ' + _cc + ' of this">×' + _cc + '</span>' : '';
        return '<div class="vm-cell' + (rr ? ' vmc-' + rr : '') + '" style="grid-column:span ' + cl.w + ';grid-row:span ' + cl.h + '"'
          + ' data-vault-item="' + esc(n) + '" data-arttip="' + esc(n) + '" title="' + esc(n) + (_cc>1?' ×'+_cc:'') + '"'
          + ' onclick="window.openDrop&&window.openDrop(\'' + jsArg(n) + '\')">'
          + '<span class="vm-cell-art">' + (((typeof artUrl==='function'&&artUrl(n)) || typeof _magicArtSrc!=='function' || !_magicArtSrc(n)) ? art(n, '◆', 'lg') : '<span class="d2art-wrap lg" role="img" aria-label="'+esc(n)+'"><img class="d2art-img" src="'+_magicArtSrc(n)+'" alt="" loading="lazy"></span>') + '</span>' + osTag + _cntTag
          + '<span class="vm-item-name vm-cell-name"' + (typeof _qStyle === 'function' ? _qStyle(n, 'unique') : '') + '>' + esc(n) + '</span>'
          + '<button class="vm-unassign vm-cell-x" onclick="event.stopPropagation();window.vaultUnassign(\'' + jsArg(n) + '\')" title="send back to the unsorted dock">✕</button></div>';
      });
      // v342.5 — append the Magic & Rare keepers as their own coloured cells (no art/openDrop — they're
      // rolled-name items with no grail card; ✕ here = throw-out from magicFinds).
      if (magicItems.length){
        var _mqcol={magic:'#7aa2ff',rare:'#ffd54a',crafted:'var(--q-orange,#ffa800)'};
        itemRows = itemRows.concat(magicItems.map(function(n){
          var q=_mfQual(n), col=_mqcol[q]||_mqcol.magic, base=_mfBase(n);
          var src=(typeof _magicArtSrc==='function')?_magicArtSrc(base||n):null;
          var artHtml = src
            ? '<span class="vm-cell-art d2art-wrap lg d2art-r-'+(q==='magic'?'magic':q==='rare'?'rare':'rw')+'" role="img" aria-label="'+esc(n)+'"><img class="d2art-img" src="'+src+'" alt="" loading="lazy"></span>'
            : '<span class="vm-cell-art vmc-gemfallback" style="color:'+col+'">◆</span>';
          return '<div class="vm-cell vmc-magicfind" style="grid-column:span 2;grid-row:span 1;border-color:'+col+';cursor:pointer" data-magic-find="'+esc(n)+'" data-arttip="'+esc(n)+'" title="'+esc(n)+(base?' · '+esc(base):'')+' ('+q+')" onclick="window.openDrop&&window.openDrop(\''+jsArg(n)+'\')">'
            + artHtml
            + '<span class="vm-item-name vm-cell-name" data-arttip="'+esc(n)+'" style="color:'+col+'">'+esc(n)+'</span>'
            + '<button class="vm-unassign vm-cell-x" onclick="event.stopPropagation();window.vaultThrowFind(\''+jsArg(n)+'\')" title="throw out — remove from Magic &amp; Rare">✕</button></div>';
        }));
      }
      function _gridWrap(arr){ return '<div class="vm-grid">' + arr.join('') + '</div>'; }
      var itemsHtml;
      if (!itemRows.length){ itemsHtml = (linked?'':'<div class="vm-empty">empty locker</div>'); }
      else if (itemRows.length > SHOWN){
        itemsHtml = _gridWrap(itemRows.slice(0,SHOWN))
          + '<details class="vm-more"><summary class="vm-more-sum"><span class="vmm-open">+ '+(itemRows.length-SHOWN)+' more ▾</span><span class="vmm-close">show less ▴</span></summary>'
          + _gridWrap(itemRows.slice(SHOWN)) + '</details>';
      } else { itemsHtml = _gridWrap(itemRows); }
      // v365 — SHARED STASH is its OWN emphasized section ABOVE the mules (full-width, bigger), so it's
      // clearly distinguished as the cross-account storage — not just another mule.
      return '<div class="vault-mule '+_muleAccent(m.id)+(m.id==='shared'?' vm-shared':'')+(total===0?' vm-empty':'')+'" data-vault-mule="'+esc(m.id)+'">'
        + '<div class="vm-plate" title="'+(m.id==='shared'?'SHARED STASH — accessible by ALL characters · click to open the fullscreen 5-page view':'click: open the in-game ID card of this mule · with a chip selected: assign it here')+'">'
        + '<span class="vm-icon">'+(m.icon||'📦')+'</span><span class="vm-name">'+esc(m.name)+'</span>'
        + '<span class="vm-count">'+total+'</span>'
        + '<span class="vm-tools"><button class="vm-tool" onclick="event.stopPropagation();window.vaultRenameMule(\''+jsArg(m.id)+'\')" title="rename">✏️</button><button class="vm-tool" onclick="event.stopPropagation();window.vaultDeleteMule(\''+jsArg(m.id)+'\')" title="delete">🗑</button></span>'
        + '</div>'
        + '<div class="vm-gauge"><div class="vm-gauge-fill'+(pct>=85?' vg-hot':'')+'" style="width:'+pct+'%"></div></div>'
        + (m.note?'<div class="vm-note">'+esc(m.note)+'</div>':'')
        + '<div class="vm-body">'
        + setRows
        + itemsHtml
        + '</div>' + linked + '</div>';
    }).join('');
  }

  // ── actions ──
  function assignItem(name, muleId){
    if (!muleById(muleId)) return;
    assign[name]=muleId; saveA(); selectedChip=null; renderVault(); refreshOpenCard();
    var card=document.querySelector('[data-vault-mule="'+(window.CSS&&CSS.escape?CSS.escape(muleId):muleId)+'"]');
    if (card){ card.classList.remove('vm-flash'); void card.offsetWidth; card.classList.add('vm-flash'); }
    status('🏦 '+name+' → '+muleById(muleId).name);
  }
  window.vaultAssign = assignItem;
  // v598 — auto-register a "<Base> (Nos low base)" intake read as a FULL vault entry — no clicks.
  // Returns {label, mode:'new'|'copy'} when handled, null when it must stay a human call (not a
  // runeword base, or the vault verdict already says vendor). The label keeps the read's quality
  // prefix (Superior/Eth) and exact socket count; _ensureSocketBaseEntry builds the tier/art/RW
  // description; the mule assignment + forge-step reset mirror the normal data.items path.
  window._autoRegisterLowBase = function(n){
    try {
      var m = /^(.+?)\s*\((\d+)\s*os\s+low base\)\s*$/i.exec(String(n||'')); if (!m) return null;
      var b = m[1].trim(), s = parseInt(m[2], 10);
      var q = (typeof _qualStrip === 'function') ? (_qualStrip(b) || b) : b;
      if (!(typeof _isRunewordBase === 'function' && _isRunewordBase(q))) return null;
      var lbl = b + ' (' + s + 'os)';
      var sg = suggestMule(lbl);
      if (sg && sg.id === '__throwout') return null;   // nothing left for it → review, not auto-keep
      if (owned.has(lbl)){
        copies[lbl] = ((copies[lbl] && copies[lbl] > 0) ? copies[lbl] : 1) + 1;   // 2nd physical copy → ×N
        persistOwned(); saveA();
        return { label: lbl, mode: 'copy' };
      }
      owned.add(lbl);
      if (typeof _ensureSocketBaseEntry === 'function') _ensureSocketBaseEntry(lbl, true);
      if (sg && muleById(sg.id) && !assign[lbl]) assign[lbl] = sg.id;
      try { var _st = JSON.parse(window.LSR.getItem('d2r_forgeStep')||'{}');
        if (_st['chain|'+lbl] != null){ delete _st['chain|'+lbl]; window.LSR.setItem('d2r_forgeStep', JSON.stringify(_st)); } } catch(e){}
      persistOwned(); saveA();
      return { label: lbl, mode: 'new' };
    } catch(e){ return null; }
  };
  window.vaultUnassign = function(name){ delete assign[name]; saveA(); renderVault(); refreshOpenCard(); };
  // v226: erase an AI misread in one click — removes the ✓ owned mark itself
  // (not just the locker assignment). Recoverable: re-✓ on the item's card.
  window.vaultUnown = function(name){
    try { owned.delete(name); } catch(e){}
    delete assign[name];
    persistOwned(); saveA(); renderVault(); refreshOpenCard();
    try { if (typeof renderAll === 'function') renderAll(); } catch(e){}
    status('🗑 "'+name+'" removed from owned — if that was wrong, re-✓ it on its item card');
  };
  // v342.3 — throw out a Magic & Rare keeper (rolled-name item; lives in magicFinds, not grail `owned`)
  window.vaultThrowFind = function(name){
    try { delete magicFinds[name]; } catch(e){}
    persistOwned(); renderVault();
    status('🗑 "'+name+'" removed from Magic & Rare');
  };
  // v342.4 — promote an unmatched read into the Magic & Rare bucket (it WAS a keeper after all)
  window.vaultKeepUnknown = function(name){
    try { magicFinds[name] = magicFinds[name] || { q: 'rare', base: '' }; unknownReads.delete(name); } catch(e){}
    persistOwned(); renderVault();
    status('🔮 "'+name+'" kept → Magic & Rare');
  };
  // v397.2 — manual socket fix for a name-only base the AI missed sockets on: register "<Base> (Nos)" as a
  // socketed runeword/craft base (own card + exact-count runewords) + auto-mule it, and drop the name-only read.
  window.vaultSetSockets = function(name, n){
    try {
      n = parseInt(n, 10); if (!(n >= 1 && n <= 6)) return;
      var clean = (typeof _throwClean === 'function') ? _throwClean(name) : name;
      // v582.1 — strip ANY existing socket/Larzuk suffixes (repeatedly) so re-registering an already-
      // labelled read can't produce "Flail (5os) (5os)" (live incident during the Flail rescue).
      while (/\s*\((?:Larzuk base|\d+\s*os(?:\s+low base)?|low base)\)\s*$/i.test(clean)) clean = clean.replace(/\s*\((?:Larzuk base|\d+\s*os(?:\s+low base)?|low base)\)\s*$/i, '').trim();
      var label = clean + ' (' + n + 'os)';
      if (typeof unknownReads !== 'undefined') unknownReads.delete(name);
      if (typeof _ensureSocketBaseEntry === 'function') _ensureSocketBaseEntry(label);
      owned.add(label);
      var sg = suggestMule(label); if (sg && sg.id !== '__throwout' && muleById(sg.id) && !assign[label]) assign[label] = sg.id;
      persistOwned(); saveA(); renderVault(); refreshOpenCard();
      status('🔩 ' + clean + ' → ' + n + ' sockets — registered as a runeword/craft base');
    } catch(e){}
  };
  // v575 — keep an UNSOCKETED base from the throw-out review as a Larzuk/cube-gamble candidate (Konyo's
  // unsocketed Superior Flail = the ideal HotO base). Registers "<Name> (Larzuk base)" → SOCKETED locker →
  // the Forge picks it up (Larzuk-to-max words + the v575 ideal-base cube gamble).
  window.vaultKeepAsBase = function(name){
    try {
      var clean = (typeof _throwClean === 'function') ? _throwClean(name) : name;
      while (/\s*\((?:Larzuk base|\d+\s*os(?:\s+low base)?|low base)\)\s*$/i.test(clean)) clean = clean.replace(/\s*\((?:Larzuk base|\d+\s*os(?:\s+low base)?|low base)\)\s*$/i, '').trim();   // v582.1
      var label = clean + ' (Larzuk base)';
      if (typeof unknownReads !== 'undefined') unknownReads.delete(name);
      if (typeof _ensureSocketBaseEntry === 'function') _ensureSocketBaseEntry(label);
      owned.add(label);
      var sg = suggestMule(label); if (sg && sg.id !== '__throwout' && muleById(sg.id) && !assign[label]) assign[label] = sg.id;
      persistOwned(); saveA(); renderVault(); refreshOpenCard();
      status('⚒ ' + clean + ' kept UNSOCKETED — Larzuk / cube-gamble base, the Forge will plan around it');
    } catch(e){}
  };
  // v462 — FIX the socket count of an ALREADY-REGISTERED socketed / Larzuk base (Konyo's Superior Champion Axe
  // that the AI read as 0-socket). A prompt fix only helps a NEW read; this RENAMES the existing entry in place
  // → "<Base> (Nos)" (or "(Larzuk base)" for 0), preserving the Superior prefix, the ethereal flag, and the mule
  // assignment, and removes the stale entry so there's no duplicate. One-tap from the Socketed Review card.
  window.vaultFixSockets = function(name, n){
    try {
      n = parseInt(n, 10); if (!(n >= 0 && n <= 6)) return;
      var stem = String(name); while (/\s*\((?:Larzuk base|\d+\s*os(?:\s+low base)?|low base)\)\s*$/i.test(stem)) stem = stem.replace(/\s*\((?:Larzuk base|\d+\s*os(?:\s+low base)?|low base)\)\s*$/i, '').trim();   // v582.1 — strip repeated suffixes
      var newLabel = stem + ' (' + (n >= 1 ? (n + 'os') : 'Larzuk base') + ')';
      if (newLabel === name && owned.has(name)) {
        if (typeof _ensureSocketBaseEntry === 'function') _ensureSocketBaseEntry(newLabel, true);
        renderVault(); refreshOpenCard(); status('🔩 ' + newLabel + ' — already set'); return;
      }
      var wasEth = (typeof etherealItems !== 'undefined') && etherealItems.has(name);
      var oldMule = assign[name];
      try { owned.delete(name); } catch(e){}
      delete assign[name];
      try { if (typeof etherealItems !== 'undefined') { etherealItems.delete(name); if (wasEth) etherealItems.add(newLabel); } } catch(e){}
      try { if (typeof superiorBases !== 'undefined' && superiorBases.has(name)) { superiorBases.delete(name); superiorBases.add(newLabel); } } catch(e){}
      if (typeof _ensureSocketBaseEntry === 'function') _ensureSocketBaseEntry(newLabel, true);
      owned.add(newLabel);
      if (oldMule && typeof muleById === 'function' && muleById(oldMule)) assign[newLabel] = oldMule;
      else { var sg = suggestMule(newLabel); if (sg && sg.id !== '__throwout' && muleById(sg.id)) assign[newLabel] = sg.id; }
      try { LS.setItem('d2r_ethereal', JSON.stringify([...etherealItems])); } catch(e){}
      try { LS.setItem('d2r_superiorBases', JSON.stringify([...superiorBases])); } catch(e){}
      persistOwned(); saveA(); renderVault(); refreshOpenCard();
      status('🔩 ' + stem + ' → ' + (n >= 1 ? n + ' sockets' : 'Larzuk base') + ' — fixed');
    } catch(e){}
  };
  // ============================================================================================
  // v466 — 🔬 AI ITEM CHECKER (flagship): a dedicated, ISOLATED tool to judge a MAGIC/RARE item.
  // Drop a screenshot (the AI reads what it can of the affixes) OR enter/edit by hand, then get a
  // TRANSPARENT keep / borderline / toss verdict that cross-references the slot's runeword/value bar.
  // Magic/Rare ONLY (the items that actually need affix judgement). All the verdict logic lives HERE,
  // so the regular cards stay clean (Konyo). Actions: 🏦 Mule it (keep) · 🗑 Cancel out (toss).
  // ============================================================================================
  var _aicItem = (function(){ try { var d=_safeJsonParse(LS.getItem('d2r_aicDraft'), null); return (d && typeof d==='object' && !Array.isArray(d)) ? d : null; }catch(e){ return null; } })()
    || { name:'', base:'', q:'rare', mods:[] };
  function _aicSave(){ try { LS.setItem('d2r_aicDraft', JSON.stringify(_aicItem)); }catch(e){} }
  // transparent affix value table — each affix line scores its HIGHEST matching weight (no double-count)
  // v553 — magic/rare affix value table, reordered around what magic/RARE items actually roll (an expert's keep
  // bar). Each affix line scores its HIGHEST matching weight (no double-count). NOTE: +All Skills / −Enemy Resist /
  // Chance-to-Cast / +All Attributes never roll on magic/rare — kept only as high-weight "you mislabeled a
  // unique/set as rare" catches (they contribute 0 when they don't match). The real prime affixes are IAS, +skills,
  // FCR, all-res, leech, life.
  var _AIC_W = [
    {re:/\+\s*\d+\s+to all skills/i, w:10, label:'+X All Skills'},
    {re:/-\s*\d+%?\s*(to )?(enemy|target)[^.]{0,16}resist/i, w:8, label:'− Enemy Resist'},
    {re:/\+\s*\d+\s+to [a-z' ]*\bskills?\b/i, w:8, label:'+X Class/Tree Skills'},   // v553 6→8: the top caster magic/rare affix
    {re:/increased attack speed|\bias\b/i, w:4, label:'Increased Attack Speed'},      // v553 NEW — was entirely unscored (P0). Moderate flat weight: IAS value is slot+amount-dependent (20% on gloves is prime, 10% on a weapon is minor); a good IAS item keeps via its SUPPORT affixes (resists/life), a lone weak roll still tosses. (Full slot/amount awareness = future refinement.)
    {re:/faster cast rate|\bfcr\b/i, w:7, label:'Faster Cast Rate'},
    {re:/all resist|to all resistances|resist all/i, w:6, label:'All Resistances'},
    {re:/(life|mana) stolen|life leech|mana leech/i, w:5, label:'Leech'},
    {re:/\+\s*\d+\s+(to )?(maximum )?life\b/i, w:5, label:'+ Life'},                  // v553 4→5, split from replenish
    {re:/deadly strike|crushing blow|open wounds/i, w:4, label:'Deadly Strike / CB / OW'},
    {re:/\d+%\s*chance to cast/i, w:4, label:'Chance to Cast'},
    {re:/faster hit recovery|\bfhr\b/i, w:4, label:'Faster Hit Recovery'},
    {re:/faster block rate|\bfbr\b/i, w:3, label:'Faster Block Rate'},               // v553 NEW — a prime shield affix
    {re:/magic find|better chance of getting magic/i, w:3, label:'Magic Find'},
    {re:/all attributes/i, w:3, label:'+ All Attributes'},
    {re:/replenish life/i, w:2, label:'Replenish Life'},                             // v553 downweighted vs +max life
    {re:/\+\s*\d+\s+to (strength|dexterity|vitality|energy)\b/i, w:2, label:'+ Stat'}, // v553 NEW — individual attributes
    {re:/\bresist(ance)?s?\b|cannot be frozen/i, w:2, label:'Resist / CBF'},
    {re:/faster run|\bfrw\b/i, w:2, label:'Faster Run/Walk'},
    {re:/increase maximum mana|\+\s*\d+\s+(to )?mana\b/i, w:2, label:'+ Mana'},
    {re:/enhanced damage/i, w:1, label:'Enhanced Damage'},
    {re:/attack rating|to (minimum|maximum) damage|adds \d+\s*[-–]\s*\d+/i, w:1, label:'Damage / AR'},
  ];
  function _aicScoreAffix(s){ s=String(s||''); var best=null; for(var i=0;i<_AIC_W.length;i++){ if(_AIC_W[i].re.test(s)){ if(!best || _AIC_W[i].w>best.w) best=_AIC_W[i]; } } return best; }
  function _aicBench(base){
    var c=(typeof _baseCats==='function')?_baseCats(base):{};
    if(c['body armor']) return 'Enigma / Fortitude / Chains of Honor / Treachery';
    if(c['shield']) return 'Spirit / Exile / Dragon';
    if(c['helm']) return 'Lore / Delirium / Dream';
    if(c['weapon']) return 'Spirit / Grief / Heart of the Oak (caster)';
    return '';
  }
  function _aicVerdict(it){
    it = it || {};
    var mods=(it.mods||[]).filter(function(m){ return String(m||'').trim(); });
    var bk=[], score=0;
    mods.forEach(function(m){ var b=_aicScoreAffix(m); if(b){ score+=b.w; bk.push({label:b.label, w:b.w, src:m}); } });
    // v553 — PREMIUM-AFFIX FLOOR: a single elite affix (skills / IAS / FCR / all-res, w≥6) is never an auto-toss —
    // an expert always takes a second look at a lone +2 class-skills or 20% IAS roll. Floor those to at least borderline.
    var _hasPremium = bk.some(function(x){ return x.w>=6; });
    var tier = score>=14 ? 'keep' : ((score>=7 || _hasPremium) ? 'border' : 'toss');
    var ctx=[];
    var qn=(it.q==='rare'?'Rare':it.q==='crafted'?'Crafted':'Magic');
    ctx.push('<b>'+qn+'</b> — <b>cannot be a runeword base</b> (Larzuk gives '+(it.q==='magic'?'1–2 sockets':'1 socket')+', gems / jewels only).');
    var bench=_aicBench(it.base);
    if(bench) ctx.push('Slot benchmark to beat: <b>'+bench+'</b> — keep only if your roll out-values it.');
    var bt=(typeof _baseTier==='function')?_baseTier(it.base):'';
    // v542 — cube tier-upgrade KEEPS affixes for RARE only (game-file cubemain.txt: unique/rare/set). Magic &
    // crafted items CANNOT be tier-upgraded, so this note is gated to rare (was wrongly shown for magic/crafted).
    if(it.q==='rare' && (bt==='normal'||bt==='exceptional')) ctx.push('⬆ <b>Rare</b> '+bt+' base — you CAN cube-up its tier and it KEEPS the affixes (weapon: Sapphire line · armor: Amethyst line). Never adds sockets / runeword ability.');
    return { tier:tier, score:score, breakdown:bk, ctx:ctx };
  }
  window._aicVerdict = _aicVerdict;   // exposed for tests
  function _aicVerdictHtml(){
    var it=_aicItem;
    var hasMods=(it.mods||[]).some(function(m){ return String(m).trim(); });
    if(!String(it.base||'').trim() && !hasMods){ return '<div class="aic-verdict" style="opacity:.7">Drop a magic/rare screenshot or fill the item above to get a verdict.</div>'; }
    var v=_aicVerdict(it);
    var head=v.tier==='keep'?'✅ WORTH KEEPING':(v.tier==='border'?'🤔 BORDERLINE':'🗑 NOT WORTH IT');
    var bk=v.breakdown.length
      ? '<div class="aic-break">'+v.breakdown.map(function(b){ return '<div class="aic-bk"><span>'+esc(b.src)+'</span><span class="w">+'+b.w+'</span></div>'; }).join('')+'</div>'
      : '<div class="aic-vctx" style="opacity:.8">No valued affixes detected — almost certainly a toss.</div>';
    return '<div class="aic-verdict '+v.tier+'"><div class="aic-vhead '+v.tier+'">'+head+' <span style="opacity:.65;font-size:12px;font-weight:600">· score '+v.score+'</span></div>'
      + '<div class="aic-vctx">'+v.ctx.join('<br>')+'</div>' + bk + '</div>';
  }
  function _aicRenderVerdict(){ var el=document.getElementById('aic-verdict'); if(el) el.innerHTML=_aicVerdictHtml(); }
  function renderAIItemChecker(){
    var wrap=document.getElementById('aic-wrap'); if(!wrap) return;
    var it=_aicItem;
    var affixRows=(it.mods||[]).map(function(m,i){ return '<div class="aic-affix-row"><input class="aic-input" value="'+esc(m)+'" oninput="window.aicSetAffix('+i+',this.value)" placeholder="e.g. +2 to All Skills"><button class="aic-x" onclick="window.aicDelAffix('+i+')" title="remove">✕</button></div>'; }).join('');
    var artSrc=(typeof _magicArtSrc==='function')?(_magicArtSrc(it.base||it.name||'')||''):'';
    wrap.innerHTML=''
      + '<div class="aic-drop" id="aic-drop" onclick="var f=document.getElementById(\'aic-file\');f&&f.click()">📥 <b>Drop a magic/rare item screenshot</b> here, or click to pick a file — the AI reads what it can; edit anything below.</div>'
      + '<input type="file" id="aic-file" accept="image/*" style="display:none" onchange="window.aicUpload(this.files&&this.files[0])">'
      + '<div id="aic-msg" class="aic-vctx" style="display:none;margin:0"></div>'
      + '<div class="aic-grid">'
      +   '<div class="aic-panel"><h4>Item</h4>'
      +     (artSrc?'<img class="aic-art" src="'+esc(artSrc)+'" alt="" loading="lazy">':'')
      +     '<div class="aic-field"><label>Name</label><input class="aic-input" value="'+esc(it.name||'')+'" oninput="window.aicSetField(\'name\',this.value)" placeholder="rolled name (optional)"></div>'
      +     '<div class="aic-field"><label>Base</label><input class="aic-input" value="'+esc(it.base||'')+'" oninput="window.aicSetField(\'base\',this.value)" placeholder="e.g. Crystal Sword"></div>'
      +     '<div class="aic-field"><label>Quality</label><select class="aic-input" onchange="window.aicSetField(\'q\',this.value)">'
      +        ['magic','rare','crafted'].map(function(q){ return '<option value="'+q+'"'+(it.q===q?' selected':'')+'>'+q+'</option>'; }).join('')
      +     '</select></div>'
      +   '</div>'
      +   '<div class="aic-panel"><h4>Affixes</h4>'+affixRows+'<button class="aic-add" onclick="window.aicAddAffix()">+ add affix</button></div>'
      + '</div>'
      + '<div id="aic-verdict"></div>'
      + '<div class="aic-acts"><button class="aic-btn mule" onclick="window.aicMule()">🏦 Mule it (keep)</button><button class="aic-btn toss" onclick="window.aicToss()">🗑 Cancel out (toss)</button></div>';
    _aicRenderVerdict();
    try { var dz=document.getElementById('aic-drop');
      if(dz){ dz.ondragover=function(e){ e.preventDefault(); dz.classList.add('drag'); }; dz.ondragleave=function(){ dz.classList.remove('drag'); };
        dz.ondrop=function(e){ e.preventDefault(); dz.classList.remove('drag'); var f=e.dataTransfer&&e.dataTransfer.files&&e.dataTransfer.files[0]; if(f) window.aicUpload(f); }; } } catch(e){}
  }
  window.renderAIItemChecker = renderAIItemChecker;
  window.aicSetField = function(f,v){ _aicItem[f]=v; _aicSave(); _aicRenderVerdict(); };
  window.aicSetAffix = function(i,v){ if(!_aicItem.mods) _aicItem.mods=[]; _aicItem.mods[i]=v; _aicSave(); _aicRenderVerdict(); };
  window.aicAddAffix = function(){ if(!_aicItem.mods) _aicItem.mods=[]; _aicItem.mods.push(''); _aicSave(); renderAIItemChecker(); };
  window.aicDelAffix = function(i){ if(_aicItem.mods) _aicItem.mods.splice(i,1); _aicSave(); renderAIItemChecker(); };
  window.aicToss = function(){ _aicItem={ name:'', base:'', q:'rare', mods:[] }; _aicSave(); renderAIItemChecker(); status('🗑 cleared — not kept'); };
  window._aicSetDraft = function(o){ _aicItem = o || { name:'', base:'', q:'rare', mods:[] }; _aicSave(); };   // exposed for tests
  window._aicGetDraft = function(){ return _aicItem; };
  window.aicMule = function(){
    var it=_aicItem; var base=String(it.base||'').trim();
    var hasMods=(it.mods||[]).some(function(m){ return String(m).trim(); });
    if(!base && !hasMods){ status('🔬 nothing to keep — drop or enter an item first'); return; }
    var nm=String(it.name||'').trim() || ((it.q==='rare'?'Rare ':it.q==='crafted'?'Crafted ':'Magic ')+(base||'Item'));
    var mods=(it.mods||[]).map(function(m){ return String(m).trim(); }).filter(Boolean);
    try { magicFinds[nm]={ q:it.q||'magic', base:base, mods:mods }; } catch(e){}
    try { var sg=suggestMule(nm); if(sg && sg.id!=='__throwout' && muleById(sg.id) && !assign[nm]) assign[nm]=sg.id; } catch(e){}
    try { LS.setItem('d2r_magicFinds', JSON.stringify(magicFinds)); } catch(e){}
    persistOwned(); saveA(); renderVault(); refreshOpenCard();
    var mu=(assign[nm]&&muleById(assign[nm]))?(' → '+muleById(assign[nm]).name):'';
    status('🏦 '+nm+' kept in 🔮 Magic & Rare'+mu);
    _aicItem={ name:'', base:'', q:'rare', mods:[] }; _aicSave(); renderAIItemChecker();
  };
  function _aicMsg(html, show){ var el=document.getElementById('aic-msg'); if(el){ el.innerHTML=html; el.style.display=(show===false?'none':'block'); } try{ status(String(html).replace(/<[^>]+>/g,'')); }catch(e){} }
  // v468 — testable response handler: takes the parsed /api/intake JSON, fills the draft from the RICHEST
  // magic/rare find (most affixes = almost always the hovered tooltip, not a bare grid icon). Falls back to a
  // name from unrecognized/items. Returns {ok, msg/counts} so aicUpload can render the right feedback.
  function _aicApplyIntake(data){
    data = data || {};
    var finds = Array.isArray(data.finds) ? data.finds : [];
    var f = finds.slice().sort(function(a,b){ return (b&&b.mods?b.mods.length:0) - (a&&a.mods?a.mods.length:0); })[0];
    if(f){ _aicItem={ name:f.name||'', base:f.base||'', q:f.q||'magic', mods:(f.mods||[]).map(String) }; _aicSave(); return { ok:true, name:(_aicItem.name||_aicItem.base||'item'), extra:Math.max(0, finds.length-1) }; }
    var alt = (data.unrecognized||[])[0] || (data.items||[])[0];
    if(alt){ _aicItem={ name:String(alt), base:'', q:'rare', mods:[] }; _aicSave(); return { ok:true, nameOnly:true, name:String(alt) }; }
    return { ok:false, counts:{ items:(data.items||[]).length, finds:0, unrec:(data.unrecognized||[]).length, sockets:(data.sockets||[]).length } };
  }
  window._aicApplyIntake = _aicApplyIntake;   // exposed for tests
  window.aicUpload = async function(file){
    var fi=document.getElementById('aic-file');
    if(!file){ if(fi) fi.value=''; return; }
    _aicMsg('🔬 reading the item… (a few seconds — talking to the AI)');
    try {
      // resize like the main intake (downscale: max 1568px, JPEG 0.85) so the payload isn't huge.
      var b64 = (typeof downscale === 'function')
        ? await downscale(file)
        : await new Promise(function(res,rej){ var r=new FileReader(); r.onload=function(){ res(String(r.result||'').split(',')[1]||''); }; r.onerror=rej; r.readAsDataURL(file); });
      var endpoint=localStorage.getItem('d2r_intakeUrl')||(location.protocol==='file:'?'https://bull-4-u.com/api/intake':'/api/intake');
      var vocab=[]; try { if(typeof __setPieceNames==='function') vocab=__setPieceNames(); } catch(e){}
      var resp;
      try { resp=await fetch(endpoint,{ method:'POST', headers:{'content-type':'application/json'}, credentials:'same-origin', body:JSON.stringify({ image:b64, media_type:'image/jpeg', names:vocab, cropped:false }) }); }
      catch(netErr){ _aicMsg('🔬 couldn’t reach the AI (network). Check your connection and try again — or enter the item by hand below.'); if(fi) fi.value=''; return; }
      if(!resp.ok){
        var hint = resp.status===401 ? ' — you may be signed out of the site; reload the page, sign in, then retry.' : (resp.status>=500 ? ' — the AI server hiccuped; try again in a moment.' : '');
        _aicMsg('🔬 read failed (server '+resp.status+')'+hint+' You can still enter the item by hand below.'); if(fi) fi.value=''; return;
      }
      var data; try { data=await resp.json(); } catch(e){ _aicMsg('🔬 the AI reply was unreadable — try again, or enter by hand.'); if(fi) fi.value=''; return; }
      try { console.log('[aic] intake response:', data); } catch(e){}
      var r=_aicApplyIntake(data);
      if(r.ok){ renderAIItemChecker(); _aicMsg('🔬 read <b>'+esc(r.name)+'</b>'+(r.nameOnly?' — set its base + affixes below.':((r.extra?' (+'+r.extra+' other magic/rare in the shot — showing the most detailed)':'')+'. Check/edit the affixes, then judge it.'))); if(fi) fi.value=''; return; }
      var c=r.counts;
      _aicMsg('🔬 the AI read the shot but found no magic/rare item (items:'+c.items+' · finds:0 · unrec:'+c.unrec+' · sockets:'+c.sockets+'). Tip: hover the item so its TOOLTIP shows, screenshot THAT, and re-upload — or enter it by hand below.');
      if(fi) fi.value='';
    } catch(e){ _aicMsg('🔬 read failed ('+(e&&e.message?esc(String(e.message)):'unknown')+') — enter the item by hand below.'); if(fi) fi.value=''; }
  };
  // v342.4 — dismiss an unmatched read (junk / bad transcription) so it stops showing
  window.vaultDismissUnknown = function(name){
    try { unknownReads.delete(name); } catch(e){}
    persistOwned(); renderVault();
    status('🗑 "'+name+'" dismissed');
  };
  window.vaultAutoAssign = function(){
    var n=0;
    ownedPool().forEach(function(name){ if(!assign[name]){ var sg=suggestMule(name); if(sg && muleById(sg.id)){ assign[name]=sg.id; n++; } else if(sg && sg.id==='__keep'){ assign[name]='__keep'; n++; } } });   // v409 — __keep items (Anni/Torch/Gheed's) are "handled" (kept in inventory), not left nagging in the dock
    saveA(); renderVault(); status('⚖️ auto-assigned '+n+' item'+(n===1?'':'s'));
  };
  // v327: nuke the unsorted dock — removes every UNSORTED item from ✓ owned. Items already filed
  // in a mule are untouched (only `!assign[name]`). Konyo wanted this beside the Auto-Sort button.
  window.vaultClearUnsorted = async function(){
    var unsorted = ownedPool().filter(function(name){ return !assign[name] && !isSharedStash(name); });
    if (!unsorted.length){ status('nothing unsorted to clear'); return; }
    if (!(await uiConfirm('Delete all '+unsorted.length+' UNSORTED item'+(unsorted.length===1?'':'s')+' from the dock?\n\nThis removes them from ✓ owned. Items already filed in a mule are NOT touched. You can re-✓ any of them later from its item card.'))) return;
    unsorted.forEach(function(name){ try{ owned.delete(name); }catch(e){} delete assign[name]; });
    persistOwned(); saveA(); renderVault(); refreshOpenCard();
    try { if (typeof renderAll === 'function') renderAll(); } catch(e){}
    status('🗑 cleared '+unsorted.length+' unsorted item'+(unsorted.length===1?'':'s')+' from the dock');
  };
  window.vaultAddMule = function(){
    var name=prompt('New mule name (this IS your in-game character name — make it say what it holds):','UNI-WEAP-2');
    if (!name) return;
    var id='m'+Date.now().toString(36);
    roster.push({id:id, name:name.toUpperCase().slice(0,15), icon:'📦', note:''}); saveR(); renderVault();
  };
  window.vaultRenameMule = function(id){
    var m=muleById(id); if(!m) return;
    var name=prompt('Rename mule:', m.name); if(!name) return;
    m.name=name.toUpperCase().slice(0,15); saveR(); renderVault();
  };
  window.vaultDeleteMule = async function(id){
    var m=muleById(id); if(!m) return;
    if (!(await uiConfirm('Delete locker '+m.name+'? Its items return to the unsorted dock.'))) return;
    roster=roster.filter(function(x){return x.id!==id;});
    Object.keys(assign).forEach(function(n){ if(assign[n]===id) delete assign[n]; });
    saveR(); saveA(); renderVault();
  };
  window.vaultReset = async function(){
    if (!(await uiConfirm('Clear ALL vault assignments? (The mule roster stays; every item returns to the unsorted dock.)'))) return;
    assign={}; saveA(); renderVault();
  };
  window.vaultExport = function(){
    var byMule={};
    Object.keys(assign).forEach(function(n){ (byMule[assign[n]]=byMule[assign[n]]||[]).push(n); });
    var md='# The Vault — mule manifests\n';
    roster.forEach(function(m){
      var items=(byMule[m.id]||[]).sort();
      md+='\n## '+m.name+' ('+items.length+')\n'+(m.note?'_'+m.note+'_\n':'');
      items.forEach(function(n){ md+='- '+n+'\n'; });
    });
    var unsorted=ownedPool().filter(function(n){return !assign[n];});
    if (unsorted.length){ md+='\n## UNSORTED ('+unsorted.length+')\n'; unsorted.forEach(function(n){ md+='- '+n+'\n'; }); }
    navigator.clipboard.writeText(md).then(function(){ status('📋 manifests copied — paste anywhere'); }, function(){ status('clipboard blocked — copy manually'); });
  };
  // ── v204: in-game size taxonomy (approximate, from base type) ──
  var SIZE_RULES=[
    [/\b(small charm|annihilus)\b/i,[1,1]],
    [/\b(large charm|torch)\b/i,[1,2]],
    [/\b(grand charm|sunder|gheed)\b/i,[1,3]],
    [/\b(ring|amulet|jewel|essence|organ|eye|brain|horn)\b/i,[1,1]],
    [/\b(key)\b/i,[1,2]],
    [/\b(wand|orb|eagle orb|fang|swirling crystal)\b/i,[1,2]],
    [/\b(dagger|dirk|kris|stiletto|blade of|cinquedeas?)\b/i,[1,3]],
    [/\b(javelin|pilum|glaive|spiculum|katar|claws?|talons?|cestus|fist|knuckles?|scepter|caduceus|rod|club|cudgel|truncheon)\b/i,[1,3]],
    [/\b(gloves?|gauntlets?|grasp|bracers?|vambraces?|boots?|greaves|sabatons?|treads?|trek|belt|sash|cord|girdle|buckle|helm|cap|crown|casque|basinet|bonnet|mask|circlet|coronet|tiara|diadem|sallet|armet|shako|visor|pelt|buckler)\b/i,[2,2]],
    [/\b(maul|great maul|thunder maul|stave|staff|bow|crossbow|matriarchal|grand matron|spear|pike|lance|trident|brandistock|spetum|poleaxe|polearm|halberd|scythe|thresher|cromachan|war pike|colossus|executioner|decapitator|champion|balrog blade|glorious)\b/i,[2,4]],
    [/\b(armor|plate|mail|hauberk|tunic|jupon|cuirass|husk|hide|shell|carapace|wyrmhide|leather|splint|gothic|ornate|embossed|templar|shadow plate|kraken|hellforge|balrog skin|archon|dusk shroud|wire fleece|scarab husk|loricated|shield|rondache|aegis|ward|monarch|luna|hyperion|defender|targe|scutum|pavise|tower|royal|kite|dragon)\b/i,[2,3]],
    [/\b(sword|sabre|scimitar|falchion|tulwar|crystal|axe|hammer|mace|flail|morning star|war hammer)\b/i,[2,3]]
  ];
  function vaultSize(name){
    var tip=tipOf(name);
    var probe=((tip&&tip.base)||'')+' '+name;
    try{ var spz=window.findSetPiece && window.findSetPiece(name); if (spz && spz.slot) probe = spz.slot + ' ' + probe; }catch(e){}
    for (var i=0;i<SIZE_RULES.length;i++){ if (SIZE_RULES[i][0].test(probe)) return SIZE_RULES[i][1]; }
    return [2,2];
  }
  // first-fit-decreasing packer over a w×h grid
  var _MULE_COPY_CAP = 3;   // v403 — mule shows at most 3 of the same base, each in its own slot
  function packGrid(items, gw, gh){
    var grid=[], placed=[], left=[];
    for (var y=0;y<gh;y++){ grid.push(new Array(gw).fill(false)); }
    function fits(x,y,w,h){
      if (x+w>gw||y+h>gh) return false;
      for (var dy=0;dy<h;dy++) for (var dx=0;dx<w;dx++) if (grid[y+dy][x+dx]) return false;
      return true;
    }
    function mark(x,y,w,h){ for (var dy=0;dy<h;dy++) for (var dx=0;dx<w;dx++) grid[y+dy][x+dx]=true; }
    items.forEach(function(it){
      for (var y=0;y<gh;y++) for (var x=0;x<gw;x++){
        if (fits(x,y,it.w,it.h)){ mark(x,y,it.w,it.h); placed.push({n:it.n,x:x,y:y,w:it.w,h:it.h}); return; }
      }
      left.push(it);
    });
    return {placed:placed, left:left};
  }
  function gridHtml(placed, gw, gh, cell){
    var cells=''; for (var i=0;i<gw*gh;i++) cells+='<div class="vd-cell"></div>';
    var blocks=placed.map(function(p){
      var _vr=(window._artRarity?window._artRarity(p.n):'');
      return '<div class="vd-item'+(_vr?' vd-r-'+_vr:'')+'" style="left:'+(3+p.x*(cell+2))+'px;top:'+(3+p.y*(cell+2))+'px;width:'+(p.w*cell+(p.w-1)*2)+'px;height:'+(p.h*cell+(p.h-1)*2)+'px" title="'+esc(p.n)+' ('+p.w+'×'+p.h+')" onclick="window.openDrop&&window.openDrop(\''+jsArg(p.n)+'\')">'+art(p.n,'◆', p.w>1&&p.h>1?'':'sm')+'</div>';
    }).join('');
    return '<div class="vd-grid" style="grid-template-columns:repeat('+gw+','+cell+'px);grid-auto-rows:'+cell+'px">'+cells+blocks+'</div>';
  }
  // v364/v367 — SHARED STASH = D2R's 5 shared-stash tabs = GENERAL cross-account storage for high-value
  // "worth keeping close" keepers (Konyo's corrected scheme): Pg1 💎 Trade = the auto-sorted keepers,
  // value-sorted; Pg2-5 📦 Spare = empty looting room. Runes/gems/materials are NOT here — they live in
  // their own dedicated planners (already individually synced). (v363's runes/materials pages were wrong.)
  var _sharedPage = 0;
  // v367 — removed dead _HIGH_RUNE_RE / _MAT_RE / _runeOrder / _isRuneName helpers (leftover from v363's
  // runes/materials pages, never referenced after v364 made SHARED general high-value storage).
  // v364 — the 5 SHARED tabs = general cross-account storage. Auto-sorted items (high/very-high trade
  // value, "worth keeping close") distribute best-first: Pg1 💎 Trade = Very-High, Pg2 ⭐ High, Pg3 📦 Keep
  // = anything else assigned here, Pg4+Pg5 📦 Spare = left empty as looting room. Runes/gems/mats live in
  // their own planners — never here.
  function _sharedStashPages(names){
    // Pg1 holds the auto-sorted keep-close items (value-sorted vhigh→high→rest); Pg2-5 are spare
    // looting room. (Item value tiers from the maxroll data: uniques top out at 'high'.)
    var rank = { vhigh: 0, high: 1, med: 2, low: 3, none: 4, trash: 5 };
    var sorted = names.slice().sort(function(a, b){
      var ra = rank[(typeof _itemValue === 'function' ? _itemValue(a) : '') || 'none'];
      var rb = rank[(typeof _itemValue === 'function' ? _itemValue(b) : '') || 'none'];
      return (ra == null ? 9 : ra) - (rb == null ? 9 : rb) || a.localeCompare(b);
    });
    return [
      { icon: '💎', label: 'Trade', items: sorted },
      { icon: '📦', label: 'Spare', items: [] },
      { icon: '📦', label: 'Spare', items: [] },
      { icon: '📦', label: 'Spare', items: [] },
      { icon: '📦', label: 'Spare', items: [] },
    ];
  }
  window._sharedSetPage = function(i){ _sharedPage = Math.max(0, Math.min(4, i | 0)); window.openMuleCard('shared'); };
  function _renderSharedStash(box){
    // v364 — SHARED holds items ASSIGNED here (auto-sorted by value during intake, or dragged manually).
    var names = (function(){ try { return Object.keys(assign).filter(function(n){ return assign[n] === 'shared'; }).sort(); } catch(e){ return []; } })();
    var pages = _sharedStashPages(names);
    var pg = pages[_sharedPage] || pages[0];
    var sized = pg.items.map(function(n){ var s = vaultSize(n); return { n: n, w: s[0], h: s[1], area: s[0] * s[1] }; })
                        .sort(function(a, b){ return b.area - a.area || b.h - a.h; });
    var vw = window.innerWidth || 1440, vh = window.innerHeight || 900;
    var cell = Math.max(28, Math.min(64, Math.floor(Math.min((vw * 0.46) / 10, (vh - 300) / 10))));
    var packed = packGrid(sized, 10, 10);
    var slotName = function(p){ return 'col ' + (p.x + 1) + ' · row ' + (p.y + 1); };
    var tabs = pages.map(function(p, i){ return '<div class="vd-tab' + (i === _sharedPage ? ' vt-on' : '') + '" onclick="window._sharedSetPage(' + i + ')">' + p.icon + ' ' + p.label + '</div>'; }).join('');
    var list = packed.placed.map(function(p){ return '<div>' + esc(p.n) + ' → <span class="vl-slot">' + esc(pg.label.toUpperCase()) + ' ' + slotName(p) + '</span></div>'; }).join('');
    var totalAll = names.length;
    box.hidden = false; box.scrollTop = 0;
    box.innerHTML = '<div class="vd-head"><span class="vd-icon">📦</span><span class="vd-name">SHARED STASH</span>'
      + '<span class="vd-sub" style="margin:0 14px 0 6px">' + totalAll + ' never-muled item' + (totalAll === 1 ? '' : 's') + ' · auto-assorted across the 5 shared tabs</span>'
      + '<button class="vd-close" onclick="window.vaultCloseCard()">✕ close (Esc)</button></div>'
      + '<div class="vd-game-row">'
      +   '<div class="vd-panel" style="margin:0 auto"><div class="vd-panel-title">Shared Stash</div>'
      +     '<div class="vd-tabs">' + tabs + '</div>'
      +     gridHtml(packed.placed, 10, 10, cell).replace(/class="vd-cell"/g, 'class="vd-cell vd-red"')
      +     '<div class="vd-pagebar"><span class="vp-arrow" style="cursor:pointer" onclick="window._sharedSetPage(' + ((_sharedPage + 4) % 5) + ')">◄</span><span>' + pg.icon + ' ' + pg.label + ' · Page ' + (_sharedPage + 1) + ' / 5</span><span class="vp-arrow" style="cursor:pointer" onclick="window._sharedSetPage(' + ((_sharedPage + 1) % 5) + ')">►</span></div>'
      +     '<div class="vd-goldbox">' + pg.icon + ' ' + pg.items.length + ' on this page · ' + totalAll + ' total</div>'
      +   '</div>'
      + '</div>'
      + (packed.left.length ? '<div class="vd-overflow">⚠ <strong>' + packed.left.length + ' item' + (packed.left.length === 1 ? '' : 's') + ' overflow this page</strong> — D2R shared tabs hold 100 slots; this is the 10×10 preview: ' + packed.left.map(function(i){ return esc(i.n); }).join(' · ') + '</div>' : '')
      + (pg.items.length ? '<div class="vd-list">' + list + '</div>'
         : '<div class="vm-empty" style="padding:8px 2px">' + (_sharedPage >= 3 ? '📦 spare page — kept empty as room for fresh loot while hunting' : 'nothing on this page yet') + '</div>');
  }
  var openMuleId = null, _muleReturnTab = null, _mulePage = 0;
  // v405 — one D2R mule character = personal stash (10×10 = 100 cells) + inventory (10×4 = 40 cells) = 140
  // cells. A category that overflows 140 cells SPILLS onto the next mule of the same kind (Mule 2, 3…), so
  // "97 items in one mule" can never happen — they auto-distribute across as many mule toons as it takes.
  window._muleSetPage = function(i){ var n = _muleTotalPages || 1; _mulePage = ((i % n) + n) % n; window.openMuleCard(openMuleId); };
  var _muleTotalPages = 1;
  window.openMuleCard = function(muleId){
    var m=muleById(muleId); var box=document.getElementById('vault-detail');
    if (!m||!box) return;
    if (muleId !== openMuleId) _mulePage = 0;   // v405 — reset to the first mule when switching lockers
    openMuleId = muleId;
    // v235: remember the tab the card was opened from (the vault lives in Tools)
    // so closing returns here, not wherever a stray hotkey routed to.
    try { var _at=document.querySelector('.tab.active'); if (_at && _at.dataset && _at.dataset.tab) _muleReturnTab=_at.dataset.tab; } catch(e){}
    // a display:none ancestor (collapsed card) kills fixed children — live on <body>
    if (box.parentElement !== document.body) document.body.appendChild(box);
    box.classList.add('vd-fs');
    document.documentElement.classList.add('vd-lock');
    // v363 — SHARED STASH gets its own 5-page auto-assorted view (not the mule stash+inventory layout).
    if (muleId === 'shared'){ _renderSharedStash(box); return; }
    var names = Object.keys(assign).filter(function(n){return assign[n]===muleId;}).sort();
    // v211: same-set pieces pack as NEIGHBORS — sort groups sets together first
    // (first-fit places consecutive items adjacently), then big-first within a group
    // v403 — a QUANTITY base owned ×N takes N SEPARATE grid slots: each physical copy packs on its own,
    // assorted alongside the other units (Konyo's 3 Threshers = 3 cells). Expand by copyCount (mule cap 3).
    var sized=[];
    names.forEach(function(n){
      var s=vaultSize(n); var t=tipOf(n); var cc=Math.max(1, Math.min(copyCount(n)||1, _MULE_COPY_CAP));
      for (var _ci=0; _ci<cc; _ci++){ sized.push({n:n,w:s[0],h:s[1],area:s[0]*s[1],set:(t&&t.setName)||'',ct:cc}); }
    });
    sized.sort(function(a,b){
      if (a.set !== b.set) return a.set ? (b.set ? (a.set<b.set?-1:1) : -1) : 1;
      if (a.n !== b.n) return b.area-a.area || (a.n<b.n?-1:1);   // keep copies of the same base adjacent
      return b.area-a.area || b.h-a.h;
    });
    var _physN = sized.length;   // total PHYSICAL items (copies counted) for the header/goldbox
    // v405 — pack EVERY item across as many mule characters as needed: each mule = stash(10×10) then
    // inventory(10×4). Greedily fill mule 1 fully, spill the rest onto mule 2, and so on. `_muleTotalPages`
    // is the number of mule toons this category needs; `_mulePage` is the one currently shown.
    var _mules = [], _rem = sized.slice(), _guard = 0;
    do {
      var _st = packGrid(_rem, 10, 10);
      var _iv = packGrid(_st.left, 10, 4);
      _mules.push({ stash: _st.placed, inv: _iv.placed });
      _rem = _iv.left;
    } while (_rem.length && ++_guard < 80);
    _muleTotalPages = _mules.length || 1;
    if (_mulePage >= _muleTotalPages) _mulePage = _muleTotalPages - 1;
    if (_mulePage < 0) _mulePage = 0;
    var _cur = _mules[_mulePage] || { stash: [], inv: [] };
    var stash = { placed: _cur.stash, left: [] };
    var inv = { placed: _cur.inv, left: (_mulePage === _muleTotalPages - 1 ? _rem : []) };   // only the LAST page can carry a (capped) remainder
    var _thisMuleN = _cur.stash.length + _cur.inv.length;
    // v214: fullscreen game calibration — both panels sized like 1920×1080 D2R
    box.hidden = false;
    var vw = window.innerWidth || 1440, vh = window.innerHeight || 900;
    var cell = Math.max(26, Math.min(60, Math.floor(Math.min((vw * 0.30) / 10, (vh - 330) / 10))));
    var eqc = cell;   // v235: equipment cells = the SAME unit cell as stash/inventory (was 0.72 → misaligned)
    var slotName=function(p){ return 'col '+(p.x+1)+' · row '+(p.y+1); };
    var list = stash.placed.map(function(p){ return '<div>'+esc(p.n)+' → <span class="vl-slot">STASH '+slotName(p)+'</span></div>'; })
      .concat(inv.placed.map(function(p){ return '<div>'+esc(p.n)+' → <span class="vl-slot">INVENTORY '+slotName(p)+'</span></div>'; })).join('');
    var TABS=['Personal','Shared','Gems','Materials','Runes'];
    var EQ=[['eq-w1','🗡'],['eq-helm','⛑'],['eq-amu','📿'],['eq-body','🛡'],['eq-w2','🛡'],['eq-glove','🧤'],['eq-ring1','💍'],['eq-belt','〰'],['eq-ring2','💍'],['eq-boot','🥾']];
    var _muleLabel = _muleTotalPages > 1 ? (' #' + (_mulePage + 1)) : '';
    var _muleTag = _muleTotalPages > 1 ? '<span class="vd-mule-nav" title="this category spans '+_muleTotalPages+' mule characters (each = 100-cell stash + 40-cell inventory = 140 cells). Click the arrows — or press ← → — to step through the mules.">'
      + '<button class="vd-mule-arrow" onclick="window._muleSetPage('+(_mulePage-1)+')" title="previous mule (←)">◄</button>'
      + '🧍 Mule '+(_mulePage+1)+' / '+_muleTotalPages
      + '<button class="vd-mule-arrow" onclick="window._muleSetPage('+(_mulePage+1)+')" title="next mule (→)">►</button>'
      + '</span>' : '';
    var _muleArrows = _muleTotalPages > 1
      ? '<span class="vp-arrow" style="cursor:pointer" onclick="window._muleSetPage('+(_mulePage-1)+')">◄</span><span>🧍 Mule '+(_mulePage+1)+' / '+_muleTotalPages+'</span><span class="vp-arrow" style="cursor:pointer" onclick="window._muleSetPage('+(_mulePage+1)+')">►</span>'
      : '<span class="vp-arrow">◄</span><span>Page 1 / 1</span><span class="vp-arrow">►</span>';
    box.innerHTML = '<div class="vd-head"><span class="vd-icon">'+(m.icon||'📦')+'</span><span class="vd-name">'+esc(m.name)+_muleLabel+'</span>'
      + '<span class="vd-sub" style="margin:0 14px 0 6px">'+_physN+' item'+(_physN===1?'':'s')+' total'+(_muleTotalPages>1?(' across '+_muleTotalPages+' mules · '+_thisMuleN+' on this one'):'')+' · pack in-game EXACTLY like this (sizes approximated)</span>'
      + _muleTag
      + '<button class="vd-close" onclick="window.vaultCloseCard()">✕ close (Esc)</button></div>'
      + '<div class="vd-game-row">'
      +   '<div class="vd-panel"><div class="vd-panel-title">Stash</div>'
      +     '<div class="vd-tabs">' + TABS.map(function(t,i){ return '<div class="vd-tab'+(i===0?' vt-on':'')+'">'+t+'</div>'; }).join('') + '</div>'
      +     gridHtml(stash.placed,10,10,cell).replace(/class="vd-cell"/g,'class="vd-cell vd-red"')
      +     '<div class="vd-pagebar">' + _muleArrows + '</div>'
      +     '<div class="vd-goldbox">🪙 ' + stash.placed.length + ' in stash · ' + _thisMuleN + ' on this mule</div>'
      +   '</div>'
      +   '<div class="vd-panel"><div class="vd-panel-title">Inventory</div>'
      +     '<div class="vd-equip" style="--eqc:'+eqc+'px">' + EQ.map(function(e){ return '<div class="vd-eq '+e[0]+'"><span>'+e[1]+'</span></div>'; }).join('') + '</div>'
      +     gridHtml(inv.placed,10,4,cell)
      +     '<div class="vd-goldbox">🪙 ' + inv.placed.length + ' in inventory</div>'
      +   '</div>'
      + '</div>'
      + (_muleTotalPages > 1 ? '<div class="vd-overflow" style="border-color:rgba(240,192,96,.5);color:#f0c060">📦 <strong>'+esc(m.name)+'</strong> holds <strong>'+_physN+'</strong> items — too many for one character, so they fill <strong>'+_muleTotalPages+' mules</strong> (140 cells each). Use ◄ ► above to step through Mule 1…'+_muleTotalPages+'.</div>' : '')
      + (inv.left.length ? '<div class="vd-overflow">⚠ <strong>'+inv.left.length+' item'+(inv.left.length===1?'':'s')+'</strong> exceed even '+_muleTotalPages+' mules (cap reached) — split this category further.</div>' : '')
      + (names.length ? '<div class="vd-list">'+(_muleTotalPages>1?'<div style="opacity:.7;font-size:11px;margin-bottom:4px">— showing Mule '+(_mulePage+1)+' of '+_muleTotalPages+' —</div>':'')+list+'</div>' : '<div class="vm-empty" style="padding:8px 2px">empty locker — assign items above, then this card shows exactly where each one sits</div>');
    box.scrollTop = 0;
  };
  window.vaultCloseCard = function(){
    var b=document.getElementById('vault-detail');
    if(b){ b.hidden=true; b.classList.remove('vd-fs'); }
    document.documentElement.classList.remove('vd-lock');
    openMuleId=null;
    // v235: route back to where the card was opened from (Tools/vault), not TZ zones.
    if (_muleReturnTab && window.switchTab) { try { window.switchTab(_muleReturnTab); } catch(e){} }
  };
  document.addEventListener('keydown', function(e){
    if (e.key==='Escape' && openMuleId){ window.vaultCloseCard(); }
    // v437 — ← / → step through a multi-mule locker (only when a non-shared mule card with >1 page is open)
    else if (openMuleId && openMuleId!=='shared' && _muleTotalPages>1 && (e.key==='ArrowLeft'||e.key==='ArrowRight')){
      e.preventDefault(); window._muleSetPage(_mulePage + (e.key==='ArrowRight'?1:-1));
    }
  });
  // v210: live re-pack — any assignment change re-tetrises an OPEN mule card
  function refreshOpenCard(){
    var box=document.getElementById('vault-detail');
    if (openMuleId && box && !box.hidden && muleById(openMuleId)) window.openMuleCard(openMuleId);
  }
  window.vaultSize = vaultSize;
  window.vaultSuggest = suggestMule;
  window.renderVault = renderVault;
  window.suggestMule = suggestMule;  // v322: exposed for the socketed-routing test + external callers
  // the detail-card badge (renderItemDetailCard calls this)
  window._vaultBadge = function(name){
    var id=assign[name]; var m=id&&muleById(id);
    return m ? '<span class="vault-loc-badge" onclick="window.vaultJump&&window.vaultJump()" title="stored in your vault — click to open it">🏦 '+esc(m.name)+'</span>' : '';
  };
  window.vaultJump = function(){
    if (typeof switchTab==='function') switchTab('tools');
    var card=document.getElementById('mule-vault-card');
    if (card && card.classList.contains('collapsed') && typeof window.toggleCardCollapse==='function') window.toggleCardCollapse('mule-vault-card');
    renderVault();
    setTimeout(function(){ card&&card.scrollIntoView({behavior:'smooth', block:'start'}); }, 120);
  };

  // ── drag & drop + click-assign (delegated) ──
  document.addEventListener('dragstart', function(e){
    var chip=e.target&&e.target.closest&&e.target.closest('.vault-chip');
    if (chip){ e.dataTransfer.setData('text/vault-item', chip.dataset.vaultItem); e.dataTransfer.effectAllowed='move'; }
    // v608 — a native drag swallows mouseout, so the #arttip hover card froze on screen mid-drag
    // (Konyo's stuck Katar card). Force-hide it the moment ANY drag starts.
    try { var _at=document.getElementById('arttip'); if(_at) _at.classList.remove('on'); } catch(err){}
  });
  document.addEventListener('dragover', function(e){
    var mule=e.target&&e.target.closest&&e.target.closest('.vault-mule');
    if (mule){ e.preventDefault(); e.dataTransfer.dropEffect='move'; mule.classList.add('vm-over'); }
  });
  document.addEventListener('dragleave', function(e){
    var mule=e.target&&e.target.closest&&e.target.closest('.vault-mule');
    if (mule) mule.classList.remove('vm-over');
  });
  document.addEventListener('drop', function(e){
    var mule=e.target&&e.target.closest&&e.target.closest('.vault-mule');
    if (!mule) return;
    e.preventDefault(); mule.classList.remove('vm-over');
    var name=e.dataTransfer.getData('text/vault-item');
    if (name) assignItem(name, mule.dataset.vaultMule);
  });
  document.addEventListener('click', function(e){
    var chip=e.target&&e.target.closest&&e.target.closest('.vault-chip');
    if (chip){ selectedChip = (selectedChip===chip.dataset.vaultItem) ? null : chip.dataset.vaultItem; renderVault(); return; }
    var plate=e.target&&e.target.closest&&e.target.closest('.vm-plate');
    if (plate){
      var mule=plate.closest('.vault-mule');
      if (selectedChip) assignItem(selectedChip, mule.dataset.vaultMule);
      else window.openMuleCard(mule.dataset.vaultMule); // v204: click a locker → its in-game ID card
    }
  });

  // ── v205: 📸 AI intake — screenshots → Claude vision (via the same-origin
  // /api/intake Pages Function; the API key lives server-side) → ✓ owned + assigned
  function downscale(file){
    return new Promise(function(resolve, reject){
      var img = new Image();
      var url = URL.createObjectURL(file);
      img.onload = function(){
        var MAX = 1568; // Anthropic vision max useful long edge — 4K fullscreen shots at 1344 made tooltip text unreadably small (Tyrael hallucination, 2026-06-13)
        var scale = Math.min(1, MAX / Math.max(img.width, img.height));
        var c = document.createElement('canvas');
        c.width = Math.round(img.width * scale); c.height = Math.round(img.height * scale);
        c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
        URL.revokeObjectURL(url);
        resolve(c.toDataURL('image/jpeg', 0.85).split(',')[1]);
      };
      img.onerror = reject;
      img.src = url;
    });
  }
  // ── v342: VAULT loot intake calibrated like the runes/gems tally (crop + enlarge for clarity).
  // A loot screenshot is normally ONE item hovered → ONE floating description tooltip. We LOCATE that
  // tooltip (server 'locate' pass), crop GENEROUSLY around it (Konyo: "10x10 or more, as long as it's
  // not cut"), and ENLARGE it to a 1568 long edge at JPEG 0.95 with high smoothing — so the stat text
  // reads crisp instead of being one small region of a downscaled full screen (the over-read / misread
  // cause). The runes/gems grid has a FIXED crop; a tooltip floats, so the crop box comes from 'locate'.
  function _vLoadImg(file){
    return new Promise(function(res, rej){
      var im = new Image(), u = URL.createObjectURL(file);
      im.onload = function(){ res({ im: im, u: u }); };
      im.onerror = rej; im.src = u;
    });
  }
  // v569 — a File whose backing file was DELETED mid-batch (Konyo wiped the folder while 5 shots were
  // queued) can hang the <img> blob load with NEITHER onload NOR onerror → every worker awaits a ghost →
  // "reading 0/5" forever and _vIntakeBusy wedges the auto-watch until reload. Two guards:
  //   _vPreflight — touch the first bytes; a deleted/moved file rejects instantly (NotFound/NotReadable);
  //   _vTimed     — hard ceiling on any image-decode promise so nothing awaits forever.
  function _vPreflight(file){ return file.slice(0, 16).arrayBuffer(); }
  function _vTimed(p, ms, label){
    return Promise.race([ p, new Promise(function(_, rej){ setTimeout(function(){ rej(new Error((label||'read') + ' timed out')); }, ms); }) ]);
  }
  // v342.17 — fetch with a hard TIMEOUT so a stalled AI call can't freeze the whole intake (worker pool
  // would otherwise await a hung request forever → "stuck"). Aborts after `ms` and rejects, caught per-shot.
  function _vFetch(url, opts, ms){
    var ac = (typeof AbortController !== 'undefined') ? new AbortController() : null;
    if (ac) opts = Object.assign({}, opts, { signal: ac.signal });
    var t = ac ? setTimeout(function(){ try { ac.abort(); } catch(e){} }, ms || 75000) : null;
    return fetch(url, opts).finally(function(){ if (t) clearTimeout(t); });
  }
  // enlarge a (sub)region to a long edge at a given quality; box = [x0,y0,x1,y1] fractions, or null = whole image.
  // maxEdge/q default to the high-fidelity READ settings (1568 @ 0.95); the cheap LOCATE pass passes small values.
  function _vEnlarge(im, box, maxEdge, q, boost){
    maxEdge = maxEdge || 1568; q = q || 0.95;
    var W = im.naturalWidth || im.width, H = im.naturalHeight || im.height;
    var sx = 0, sy = 0, sw = W, sh = H;
    if (box){ sx = Math.round(box[0]*W); sy = Math.round(box[1]*H); sw = Math.round((box[2]-box[0])*W); sh = Math.round((box[3]-box[1])*H); }
    if (!(sw > 0) || !(sh > 0)){ sx = 0; sy = 0; sw = W; sh = H; }
    var scale = Math.min(box ? 3.2 : 1, maxEdge / Math.max(sw, sh));   // upscale only a crop (cap 3.2×); whole image only ever downscales
    var c = document.createElement('canvas');
    c.width = Math.max(1, Math.round(sw*scale)); c.height = Math.max(1, Math.round(sh*scale));
    var ctx = c.getContext('2d'); try { ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high'; } catch(e){}
    // v415 — optional CONTRAST BOOST: a FAINT / semi-transparent tooltip overlapping the stash (Konyo's
    // Superior Grim Scythe) is near-impossible OCR. Pumping contrast + brightness + saturation makes the
    // light tooltip text separate from the dark see-through background. Used only as the last-resort retry.
    if (boost){ try { ctx.filter = 'contrast(1.6) brightness(1.25) saturate(1.4)'; } catch(e){} }
    ctx.drawImage(im, sx, sy, sw, sh, 0, 0, c.width, c.height);
    return c.toDataURL('image/jpeg', q).split(',')[1];
  }
  // v417 — TEXT ISOLATION (the strongest OCR-rescue lever for a faint tooltip over a busy background, e.g.
  // Konyo's Superior Grim Scythe sitting half-transparent over the stash grid). Unlike _vEnlarge's global
  // contrast filter — which lifts the busy background as much as the text — this crops to the LOCATED tooltip,
  // upscales hard (≤4×), then does a real per-pixel BINARIZE on the HSV *value* channel: every D2R text colour
  // (white name · blue magic · gold unique · yellow rare) is BRIGHT on V, while the darkened see-through
  // background is LOW. Crush V<floor to black, lift the rest → glyphs pop off a clean black field. Grayscale
  // (rarity is recoverable from the base name); fires only as the last empty-read retry, so cost is one call.
  function _vTextIso(im, box, maxEdge, floor){
    maxEdge = maxEdge || 1568; floor = (floor == null ? 92 : floor);
    var W = im.naturalWidth || im.width, H = im.naturalHeight || im.height;
    var sx = 0, sy = 0, sw = W, sh = H;
    if (box){ sx = Math.round(box[0]*W); sy = Math.round(box[1]*H); sw = Math.round((box[2]-box[0])*W); sh = Math.round((box[3]-box[1])*H); }
    if (!(sw > 0) || !(sh > 0)){ sx = 0; sy = 0; sw = W; sh = H; }
    var scale = Math.min(box ? 4 : 1, maxEdge / Math.max(sw, sh));   // a cropped tooltip gets a big upscale; whole image only downscales
    var c = document.createElement('canvas');
    c.width = Math.max(1, Math.round(sw*scale)); c.height = Math.max(1, Math.round(sh*scale));
    var ctx = c.getContext('2d'); try { ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high'; } catch(e){}
    ctx.drawImage(im, sx, sy, sw, sh, 0, 0, c.width, c.height);
    try {
      var id = ctx.getImageData(0, 0, c.width, c.height), d = id.data;
      for (var p = 0; p < d.length; p += 4){
        var v = d[p] > d[p+1] ? d[p] : d[p+1]; if (d[p+2] > v) v = d[p+2];   // V = max(R,G,B) — bright for ALL text colours
        var o = (v - floor) * 2.6; o = o < 0 ? 0 : (o > 255 ? 255 : o);       // crush the see-through background, lift glyph pixels
        d[p] = d[p+1] = d[p+2] = o;
      }
      ctx.putImageData(id, 0, 0);
    } catch(e){}
    return c.toDataURL('image/jpeg', 0.95).split(',')[1];
  }
  // GENEROUS box padding — bias BIG so the tooltip is NEVER clipped (Konyo: "as long as it's not cut").
  // Pads each side, clamps to the image, and enforces a sane MINIMUM span so a too-tight box can't shrink-clip.
  function _vPadBox(box){
    if (!box || box.length !== 4) return null;
    var x0 = +box[0], y0 = +box[1], x1 = +box[2], y1 = +box[3];
    if (!(x1 > x0) || !(y1 > y0)) return null;
    var padX = (x1-x0)*0.40 + 0.05, padY = (y1-y0)*0.32 + 0.05;   // generous margin around the located box
    x0 = Math.max(0, x0-padX); y0 = Math.max(0, y0-padY); x1 = Math.min(1, x1+padX); y1 = Math.min(1, y1+padY);
    if ((x1-x0) < 0.32){ var cx=(x0+x1)/2; x0=Math.max(0,cx-0.16); x1=Math.min(1,cx+0.16); }
    if ((y1-y0) < 0.36){ var cy=(y0+y1)/2; y0=Math.max(0,cy-0.18); y1=Math.min(1,cy+0.18); }
    return [x0, y0, x1, y1];
  }
  // ── v215: intake journal — persists what was registered, when, across sessions
  var JOURNAL_KEY='d2r_intakeLog';
  function journal(){ try { return JSON.parse(window.LSR.getItem(JOURNAL_KEY)||'[]'); } catch(e){ return []; } }
  // v320: clear the intake history so the SAME screenshots can be re-read (for test runs).
  // v328: FULL RESET — a true blank start (Konyo: "delete history + unsorted should register
  // as a blank start"). Empties the log + scan-ledger AND every ✓ owned / vaulted item, set
  // pieces, and mule assignments. The mule ROSTER + rune/gem/material tallies are kept.
  window.vaultClearHistory = async function(){
    if (!(await uiConfirm('Clear intake history — FULL RESET to a blank start?\n\nThis empties the “Recently registered” log, forgets which screenshots were scanned, AND removes EVERY ✓ owned / vaulted item + mule assignments + set-piece checks. Your mule roster and rune/gem tallies stay. This cannot be undone.'))) return;
    try { window.LSR.removeItem(JOURNAL_KEY); } catch(e){}
    try { window.LSR.removeItem('d2r_intakeSeen'); } catch(e){}
    try { owned.clear(); } catch(e){}
    try { magicFinds = {}; window.LSR.removeItem('d2r_magicFinds'); } catch(e){}
    try { unknownReads.clear(); window.LSR.removeItem('d2r_unknownReads'); } catch(e){}
    try { copies = {}; window.LSR.removeItem('d2r_copies'); } catch(e){} // have-counts reset; multiKeep TARGETS (config) kept
    try { if (typeof setPieces !== 'undefined') setPieces.clear(); } catch(e){}
    try { Object.keys(assign).forEach(function(k){ delete assign[k]; }); } catch(e){}
    try { if (typeof persist === 'function') persist(); else persistOwned(); } catch(e){ try{ persistOwned(); }catch(e2){} }
    try { saveA(); } catch(e){}
    var rep = document.getElementById('vault-intake-report'); if (rep){ rep.hidden = true; rep.innerHTML=''; }
    // v569 — Konyo: "if I reset, how come it still shows linked to folder?" A FULL reset now also UNLINKS
    // the watched folder: forget the stored handle (IndexedDB), drop the session handle, stop the auto-watch
    // poll, and flip the UI back to 📂 Connect. A blank start is genuinely blank.
    try { if (typeof window._vUnlinkFolder === 'function') await window._vUnlinkFolder(); } catch(e){}
    try { renderJournal(); } catch(e){}
    try { renderVault(); } catch(e){}
    try { if (typeof renderAll === 'function') renderAll(); } catch(e){}
    status('🧹 full reset — 0 owned, folder unlinked, blank start');
  };
  // v342.25 — LIGHT reset: wipe ONLY the seen-files scan ledger (d2r_intakeSeen) so the folder
  // watch re-reads every screenshot as fresh. Does NOT touch owned items, mules, Magic & Rare,
  // or the registered vault — the safeguard Konyo built is "don't re-scan a seen file"; this is
  // the dedicated wipe-slate for that safeguard alone (the 🧹 full reset clears it too, but nukes
  // everything else with it).
  window.vaultClearScanHistory = async function(){
    var seenN = 0; try { seenN = Object.keys(seenLedger()).length; } catch(e){}
    if (!seenN){ status('🧽 scan slate already empty — nothing to clear'); return; }
    if (!(await uiConfirm('Clear scan history (wipe the slate)?\n\nThis forgets the '+seenN+' screenshot file'+(seenN===1?'':'s')+' the vault has already read, so the NEXT folder scan treats every file as fresh and re-reads them.\n\nYour ✓ owned items, mules, Magic & Rare, and the registered vault are NOT touched — only the seen-files ledger.'))) return;
    try { window.LSR.removeItem(SEEN_KEY); } catch(e){}
    status('🧽 scan slate wiped — '+seenN+' file'+(seenN===1?'':'s')+' forgotten; next scan re-reads everything');
  };
  // v342.23 — also persist the PER-SCREENSHOT breakdown (file → what it read) so the "Recently registered"
  // history keeps the deep per-shot detail across reloads, not just the item chips. Compact + short filenames.
  function journalAdd(items, perFile){
    if (!items.length && !(perFile && perFile.length)) return;
    var j = journal();
    var sf = function(s){ return String(s||'').replace(/^Screenshot\s+\d{4}-\d{2}-\d{2}\s+at\s+/i,'').replace(/\.(png|jpe?g|webp)$/i,''); };
    var pf = (perFile||[]).map(function(f){ return { f:sf(f.file), ff:(f.file||''), nw:(f.nw||[]), mf:(f.mf||[]), own:(f.own||[]), unr:(f.unr||[]), e:!!f.err, th:(f.thumb||'') }; });
    j.unshift({ ts: Date.now(), u: (typeof intakeLogger !== 'undefined' ? intakeLogger : 'Konyo'), items: items.slice(0, 30), pf: pf });   // v397 — tag the logger
    // v359 — thumbnails are heavy: bound storage by stripping them from OLD sessions.
    // v570 — but keep them on the newest SIX sessions, not just one: the auto-watch reads arrive as many
    // small sessions (8 shots, then the late 9th on the next tick…), and stripping all-but-newest left every
    // earlier card showing "no shot" (Konyo: cards need the expandable screenshot like the rest). ~6×5 thumbs
    // ≈ a few hundred KB, far under quota; the quota-fallback below still sheds them if storage runs out.
    for (var _k = 6; _k < j.length; _k++){ if (j[_k] && j[_k].pf){ j[_k].pf.forEach(function(p){ if (p) delete p.th; }); } }
    try { window.LSR.setItem(JOURNAL_KEY, JSON.stringify(j.slice(0, 20))); }
    catch(e){
      // quota hit — drop thumbnails from the newest entry too, then retry smaller
      try { (j[0].pf||[]).forEach(function(p){ if (p) delete p.th; }); window.LSR.setItem(JOURNAL_KEY, JSON.stringify(j.slice(0, 20))); }
      catch(e2){ try { window.LSR.setItem(JOURNAL_KEY, JSON.stringify(j.slice(0, 5))); } catch(e3){} }
    }
  }
  function renderJournal(){
    var el = document.getElementById('vault-journal');
    if (!el) return;
    var j = journal();
    if (!j.length){ el.style.display='none'; return; }
    el.style.display='';
    var Q = { unique:'#c7b377', set:'#00ff00', rw:'#ffa800', rune:'#ff7d3c', magic:'#6969ff', rare:'#ffff64' };
    var sessions = j.slice(0, 8).map(function(e){
      var d = new Date(e.ts);
      var when = d.toLocaleDateString(undefined,{month:'short',day:'numeric'}) + ' ' + d.toLocaleTimeString(undefined,{hour:'2-digit',minute:'2-digit'});
      var chips = e.items.map(function(n){
        var r = (typeof _artRarity === 'function') ? _artRarity(n) : '';
        var col = Q[r] || 'var(--gold-bright,#f0c060)';
        var logo = (typeof nameLogo === 'function') ? nameLogo(n) : '';
        return '<span class="vj-chip" data-arttip="' + esc(n) + '" style="color:' + col + '" onclick="window.openDrop&&window.openDrop(\'' + jsArg(n) + '\')" title="open ' + esc(n) + '">' + logo + esc(n) + '</span>';
      }).join('');
      // v342.23 — persistent per-screenshot breakdown (collapsible), reconstructed from the stored pf
      var pfHtml = '';
      if (e.pf && e.pf.length){
        var rows = e.pf.map(function(f){
          var c = [];
          var _cn = function(x){ return (typeof _vColorName==='function') ? _vColorName(x) : esc(x); };   // v349 — rarity colour + hover
          if (f.nw && f.nw.length) c.push('<span class="pf-chip pf-new">✓ '+f.nw.length+'</span><span class="pf-names">'+f.nw.map(_cn).join(', ')+'</span>');
          if (f.mf && f.mf.length) c.push('<span class="pf-chip pf-magic">🔮 '+f.mf.length+'</span><span class="pf-names">'+f.mf.map(_cn).join(', ')+'</span>');
          if (f.own && f.own.length) c.push('<span class="pf-chip pf-own">↻ '+f.own.length+'</span><span class="pf-names">'+f.own.map(_cn).join(', ')+'</span>');
          if (f.unr && f.unr.length) c.push('<span class="pf-chip pf-throw">🗑 '+f.unr.length+'</span><span class="pf-names">'+f.unr.map(_cn).join(', ')+'</span>');
          if (f.e) c.push('<span class="pf-chip pf-err">⚠ failed</span>');
          var empty = !c.length; if (empty) c.push('<span class="pf-chip pf-empty">∅</span><span class="pf-names pf-dim">no tooltip text</span>');
          // v405 — the thumbnail is ALWAYS clickable → opens the screenshot full-size, so Konyo can see what
          // the AI couldn't register (esp. the ∅ "no tooltip text" shots). If no thumb was stored (older
          // session), still render a 🔍 tile that tries to pull the full-res shot from IndexedDB by filename.
          var _shotF = esc(f.ff || f.f || '');
          var _th = f.th
            ? '<img class="pf-thumb" src="'+f.th+'" loading="lazy" title="🔍 click to enlarge the screenshot (full size)" data-shot="'+_shotF+'" onclick="window._shotLightbox&&window._shotLightbox(this.dataset.shot,this.src)">'
            : '<span class="pf-thumb pf-thumb-empty" role="button" tabindex="0" title="🔍 click to open this screenshot full-size" data-shot="'+_shotF+'" onclick="window._shotLightbox&&window._shotLightbox(this.dataset.shot,\'\')">🔍</span>';
          return '<div class="pf-row'+(empty?' pf-row-dim':'')+'">'+_th+'<span class="pf-time">'+esc(f.f)+'</span><span class="pf-st">'+c.join('')+'</span></div>';
        }).join('');
        pfHtml = '<details class="vir-pf vj-pf"><summary>📂 per-screenshot breakdown <span class="vir-pf-ct">'+e.pf.length+' file'+(e.pf.length===1?'':'s')+'</span></summary><div class="vir-pf-body">'+rows+'</div></details>';
      }
      var _uBadge = e.u ? '<span class="vj-user" title="logged by ' + esc(e.u) + '" style="font-size:9px;font-weight:700;color:#c9b88f;border:1px solid rgba(201,184,143,.45);border-radius:3px;padding:0 4px;margin-left:6px">👤 ' + esc(e.u) + '</span>' : '';
      return '<div class="vj-session"><div class="vj-meta"><span class="vj-when">' + when + '</span><span class="vj-count">' + e.items.length + ' item' + (e.items.length===1?'':'s') + '</span>' + _uBadge + '</div><div class="vj-items">' + chips + '</div>' + pfHtml + '</div>';
    }).join('');
    // v328: collapsible by default + symmetric grid chips + scroll (Konyo: "droppeeable
    // expandable scrollable more symmetric and by default not expanded").
    var totalItems = j.reduce(function(a,e){ return a + (e.items?e.items.length:0); }, 0);
    // v342.9 — authoritative GRAND TOTAL currently registered (same reconciliation as the 📋 Registered
    // panel): grail owned + Magic & Rare keepers. The session count is the AI-intake history.
    var _poolJ = ownedPool();
    var _grailReg = Array.from(owned).filter(function(n){ return !isAggregate(n) && (isSharedStash(n) || _poolJ.indexOf(n)>=0); }).length;
    var _magicReg = Object.keys(magicFinds||{}).length;
    var _throwReg = (typeof unknownReads!=='undefined' && unknownReads) ? unknownReads.size : 0;
    var _totalReg = _grailReg + _magicReg + _throwReg;
    el.innerHTML = '<details class="vj-details">'
      + '<summary class="vj-head to-sum to-acc-blue"><span class="to-emblem">🕘</span>'
      +   '<span class="to-hd"><span class="to-hd-top"><span class="to-st">Recently Registered</span><span class="to-ct">' + totalItems + '</span>'
      +     '<span class="vj-logger" onclick="event.preventDefault();event.stopPropagation();window.cycleIntakeLogger&&window.cycleIntakeLogger()" title="who is logging these uploads — click to switch (Konyo / your cousin). Each session is tagged with this name." style="cursor:pointer;font-size:10px;color:#9fc9e2;border:1px solid rgba(127,212,255,.4);border-radius:4px;padding:1px 6px">👤 ' + esc(typeof intakeLogger!=='undefined'?intakeLogger:'Konyo') + ' ⇄</span></span>'
      +   '<span class="to-subt">AI-intake history — every session, and which screenshot produced which read</span></span>'
      +   '<span class="to-rule"></span><span class="vj-gt-lbl" style="opacity:.7;font-size:10.5px;letter-spacing:.05em;color:#7fa8c4;flex:0 0 auto">history &amp; per-shot</span><span class="to-chev">▾</span>'
      + '</summary>'
      + '<div class="vj-summary">'
      +   '<span class="vj-sum-chip vj-sum-sess">🕘 ' + totalItems + ' logged · ' + j.length + ' session' + (j.length===1?'':'s') + '</span>'
      +   (function(){ try { var by={}; j.forEach(function(e){ var u=e.u||'Konyo'; by[u]=(by[u]||0)+1; }); var ks=Object.keys(by); return (ks.length>1)?('<span class="vj-sum-chip" style="color:#c9b88f">'+ks.map(function(u){ return '👤 '+esc(u)+' ·'+by[u]; }).join('  ')+'</span>'):''; } catch(e){ return ''; } })()
      + '</div>'
      + ((!j.some(function(e){ return e.pf && e.pf.length; })) ? '<div class="vj-pf-hint">📂 the per-screenshot breakdown (which shot → which items) saves under each session after your <strong>next intake</strong> — older sessions above were logged before this was added</div>' : '')
      + '<div class="vj-scroll">' + sessions + (j.length>8 ? '<div class="vj-more">… and ' + (j.length-8) + ' older session' + (j.length-8===1?'':'s') + '</div>' : '') + '</div>'
      + '</details>';
  }
  function persistOwned(){
    try { window.LSR.setItem('d2r_owned', JSON.stringify(Array.from(owned))); } catch(e){}
    try { window.LSR.setItem('d2r_magicFinds', JSON.stringify(magicFinds)); } catch(e){}
    try { window.LSR.setItem('d2r_unknownReads', JSON.stringify(Array.from(unknownReads))); } catch(e){}
    try { window.LSR.setItem('d2r_copies', JSON.stringify(copies)); } catch(e){}
    try { window.LSR.setItem('d2r_multiKeep', JSON.stringify(multiKeep)); } catch(e){}
  }
  // v323: a cooler scanning/loading UI — animated progress bar + sweeping scan-line + rotating
  // verb (reading→scanning→analyzing→matching) so it's visibly WORKING, not a static text line.
  function _scanUI(done, total, nw){
    var pct = total ? Math.round(done/total*100) : 0;
    var verbs = ['Reading','Scanning','Analyzing','Matching'];
    var verb = verbs[done % verbs.length];
    return '<div class="ai-load vintake-ai">'
      + '<div class="ai-load-orb">📸</div>'
      + '<div class="ai-load-body">'
      + '<div class="ai-load-title">' + verb + ' your loot'
      + '<span class="ai-load-dots"><i>.</i><i>.</i><i>.</i></span>'
      + '<span class="vintake-ai-meta"><b>' + done + '</b> / <b>' + total + '</b> screenshots · <span class="vintake-ai-new">' + nw + ' new</span></span></div>'
      + '<div class="ai-load-sub">✨ ' + verb.toLowerCase() + ' item names · matching the database…</div>'
      + '<div class="ai-load-bar"><span style="width:' + pct + '%"></span></div>'
      + '</div></div>';
  }
  window.vaultIntake = async function(files, opts){
    opts = opts || {};
    var report = document.getElementById('vault-intake-report');
    if (!files || !files.length || !report) return;
    window._vIntakeBusy = true;   // v396.3 — folder poll skips while a read is in flight
    try {   // v405 — EVERYTHING below runs inside try/finally so _vIntakeBusy is ALWAYS cleared, even on an
            // early return (e.g. "nothing new") or a thrown error. A stuck busy flag was wedging the folder
            // auto-watch (it skips while busy) → new screenshots silently stopped auto-registering.
    // v342.26 — snapshot the registered total BEFORE this batch so the report can show the running
    // accumulation ("N already in vault → +M new this scan → T total"). The vault persists `owned`
    // across sessions, so a NEW batch already dedups against everything registered — from the very
    // first screenshot. This just makes that ongoing, multi-batch process VISIBLE in the report.
    var _preReg = (function(){ try {
      var pm = ownedPool();
      var g = Array.from(owned).filter(function(n){ return !isAggregate(n) && (isSharedStash(n) || pm.indexOf(n)>=0); }).length;
      var m = Object.keys(magicFinds||{}).length;
      var u = (typeof unknownReads!=='undefined' && unknownReads) ? unknownReads.size : 0;
      return g + m + u;
    } catch(e){ return 0; } })();
    report.hidden = false;
    report.innerHTML = _scanUI(0, files.length, 0);
    try { report.scrollIntoView({ behavior:'smooth', block:'center' }); } catch(e){}
    var vocab = (typeof ITEMS!=='undefined') ? ITEMS.map(function(i){return i.n;}).filter(function(n){ return !/\((any piece|any|set)\)\s*$/i.test(n); }) : [];
    try { if (window.__setPieceNames) vocab = Array.from(new Set(vocab.concat(window.__setPieceNames()))); } catch(e){}
    try { if (window.EXTRA_ITEMS) vocab = Array.from(new Set(vocab.concat(Object.keys(window.EXTRA_ITEMS)))); } catch(e){}
    var logged = [], dupes = [], unrec = [], magicNew = [], extraCopies = [], cappedOut = [], errors = 0, cost = 0;
    var _aiErr = '';   // v407 — first AI-service error detail (so a key/credit/rate failure shows the REAL reason, not a false "empty")
    // v438 — USAGE-LIMIT / billing detection. When the Anthropic key hits its monthly spend cap it returns a
    // 400 "You have reached your specified API usage limits…" — which the recovery passes were SILENTLY
    // treating as empty, so a whole batch read "∅ no tooltip text" (looked like an accuracy bug; it was billing).
    // Now: detect it, set a clear banner, and ABORT the batch instead of hammering a capped API + faking empties.
    var _aiLimitHit = false;
    function _aiIsLimit(d){ return !!(d && d.error && (+d.status === 402 || /usage limit|credit balance|regain access|billing|insufficient|quota|reached your specified/i.test(String(d.detail || d.message || '')))); }
    function _aiLimitMsg(d){ var det = String((d && (d.detail || d.message)) || ''); var m = /regain access on ([0-9A-Za-z :\-]+?)(?:\.|"|$)/i.exec(det); return '⚠ AI usage limit reached — the Anthropic API key hit its monthly cap' + (m ? ' (regains access ' + m[1].trim() + ')' : '') + '. Raise the limit / add credit in the Anthropic console to read now. This is NOT your screenshots — they are fine.'; }
    function _aiReadJson(resp){ if (!resp || !resp.ok) return Promise.resolve(null); return resp.json().then(function(d){ if (_aiIsLimit(d)){ _aiLimitHit = true; if (!_aiErr) _aiErr = _aiLimitMsg(d); } return d; }).catch(function(){ return null; }); }
    function _sleep(ms){ return new Promise(function(r){ setTimeout(r, ms); }); }
    var _QTY_CAP = 3;   // v403 — mule AT MOST 3 of the same base; a 4th+ physical copy is thrown out
    // v310: track results PER screenshot FILE — so the report names the exact file each
    // item came from (Konyo: "identify specific screenshot files, not just blindly seeing
    // the picture"). Each entry: {file, nw:[new], own:[already-owned], unr:[read-not-tracked], err}.
    // `files` is a FileList (no .map) when it comes from the <input>; normalize to a real array so the
    // worker pool + perFile init work whether called with a FileList or an array (folder-scan path).
    files = Array.prototype.slice.call(files);
    // v342.27 — MANUAL intake now honours the seen-files ledger too (the folder watch already did).
    // Re-dropping the EXACT same file is FREE: it's skipped, never re-sent to the AI — so the same
    // file can never be re-read (no double-charge, and no chance a second read mis-assorts it).
    // The FOLDER path (opts.fromFolder) already filtered + marked its files seen in vaultOfferMenu,
    // so it must NOT be re-filtered here (that would skip everything it just offered).
    var _seenSkip = 0;
    if (!opts.fromFolder){
      var _seenL = (function(){ try { return seenLedger(); } catch(e){ return {}; } })();
      files = files.filter(function(f){
        if (!f || !f.name) return true;
        if (_seenL[f.name] || _seenL[f.name + '|' + f.lastModified]) { _seenSkip++; return false; }
        return true;
      });
      if (!files.length){
        report.hidden = false;
        report.innerHTML = '<div class="vir-card"><div class="vir-head"><span class="vir-title">📸 Nothing new to read</span>'
          + '<span class="vir-tot">' + _preReg + ' registered</span></div>'
          + '<div class="vir-reconcile"><span class="vir-rc"><b>' + _seenSkip + '</b> file' + (_seenSkip===1?'':'s') + ' already read — skipped (free, no AI call)</span>'
          + '<span class="vir-rc-note">these exact files were scanned before, so nothing was sent to the AI. Drop NEW screenshots, or use 🧽 Clear scan history to force a re-read.</span></div></div>';
        return;
      }
    }
    var perFile = files.map(function(f, _i){ return { file: (f && f.name) || ('screenshot ' + (_i+1)), nw: [], own: [], unr: [], mf: [], err: false }; });
    try { _vPruneShots(100); } catch(e){}   // v570 — keep the newest 100 full-res shots (was: wipe-all each scan → old cards lost their expandable screenshot)
    var endpoint = localStorage.getItem('d2r_intakeUrl')
      || (location.protocol === 'file:' ? 'https://bull-4-u.com/api/intake' : '/api/intake');
    var doneCount = 0;
    // v342.6 — process screenshots CONCURRENTLY via a small worker pool. Was strictly sequential, so
    // 62 shots × 2 calls each (locate + read) crawled — painfully so when the tab is backgrounded and
    // the browser throttles it. JS is single-threaded, so the shared accumulators (owned / magicFinds /
    // logged / …) have no real races; we just keep ~CONC reads in flight at once.
    async function processFile(i, _retry){
      _retry = _retry || 0;   // v407 — retry depth for transient AI-service failures (429 / 5xx)
      var fRec = perFile[i];
      // v438 — API cap already hit this batch → don't make a doomed call (and don't fake an empty); mark skipped.
      if (_aiLimitHit) { fRec.err = true; doneCount++; report.innerHTML = _scanUI(doneCount, files.length, logged.length); return; }
      var fname = fRec.file;
      try {
        // v342 — calibrate like runes/gems: LOCATE the hovered description tooltip, crop GENEROUSLY to
        // it (never clip), and ENLARGE so its text reads crisp — then read the ONE hovered item.
        var b64, _box = null, _imRef = null;
        // v569 — fail FAST and BOUNDED on a file deleted/moved after the batch was queued (see _vPreflight/_vTimed)
        await _vPreflight(files[i]);
        try {
          var _L = await _vTimed(_vLoadImg(files[i]), 30000, 'image decode');
          _imRef = _L.im;   // v346 — kept for the empty-read full-image retry below
          try { fRec.thumb = 'data:image/jpeg;base64,' + _vEnlarge(_L.im, null, 220, 0.5); } catch(e){}   // v359 — small thumbnail of the uploaded shot, linked to what it read
          try { _vPutShot(fname, 'data:image/jpeg;base64,' + _vEnlarge(_L.im, null, 1920, 0.82)); } catch(e){}   // v365 — full-res shot in IndexedDB for click-to-enlarge (1920px)
          // CHEAP locate input — a small 860px JPEG is plenty to find WHERE the dark tooltip box is
          // (Haiku reads it server-side); the real READ below uses the full-quality crop. Keeps credits sane.
          var _small = _vEnlarge(_L.im, null, 860, 0.72);
          try {
            var _lr = await _vFetch(endpoint, { method: 'POST', headers: { 'content-type': 'application/json' },
              body: JSON.stringify({ image: _small, media_type: 'image/jpeg', names: vocab, kind: 'locate', file: fname }) }, 45000);
            if (_lr.ok){ var _ld = await _lr.json(); if (_ld && _ld.found && _ld.box && _ld.box.length === 4) _box = _vPadBox(_ld.box.map(Number)); }
          } catch(e){}
          b64 = _vEnlarge(_L.im, _box);   // full-quality READ: crop if a tooltip was found, else whole image
          try { URL.revokeObjectURL(_L.u); } catch(e){}
          try { console.log('[vault-intake] ' + fname + ' → tooltip ' + (_box ? 'cropped ['+_box.map(function(v){return v.toFixed(2);}).join(', ')+']' : 'not found → full image')); } catch(e){}
        } catch(e){ b64 = await _vTimed(downscale(files[i]), 30000, 'image decode'); }
        var resp = await _vFetch(endpoint, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          // v343 — tell the backend this image was cropped to ONE located tooltip, so it enforces
          // single-item discipline (one hovered item = one registered thing; background grid = noise).
          body: JSON.stringify({ image: b64, media_type: 'image/jpeg', names: vocab, file: fname, cropped: !!_box }),
        }, 75000);
        if (!resp.ok) { errors++; fRec.err = true; if (!_aiErr) _aiErr = 'AI service unreachable · HTTP ' + resp.status; doneCount++; report.innerHTML = _scanUI(doneCount, files.length, logged.length); return; }
        var data = await resp.json();
        // v407 — the backend returns HTTP 200 with an {error,...} field when the Anthropic call itself failed
        // (bad/expired key, no credits, 429 rate-limit on a big burst, model error). Previously the vault path
        // ignored this and showed a FALSE "empty — no tooltip text" for every shot. Now: RETRY transient
        // failures (429 / 5xx / 529) with backoff, and on a hard failure surface the REAL reason in the report.
        if (data && data.error) {
          var _st = +(data.status || 0);
          if (_aiIsLimit(data)) { _aiLimitHit = true; errors++; fRec.err = true; if (!_aiErr) _aiErr = _aiLimitMsg(data); try { console.error('[vault-intake] AI USAGE LIMIT for ' + fname, data); } catch(e){} doneCount++; report.innerHTML = _scanUI(doneCount, files.length, logged.length); return; }
          var _transient = (_st === 429 || _st === 529 || _st >= 500 || _st === 0);
          if (_transient && _retry < 2) { _retry++; await _sleep(1500 * _retry); return await processFile(i, _retry); }
          errors++; fRec.err = true;
          if (!_aiErr) _aiErr = (data.error === 'upstream')
            ? ('AI service · HTTP ' + (_st || '?') + (data.detail ? ' · ' + String(data.detail).slice(0, 160) : ''))
            : (data.message ? ('AI service · ' + String(data.message).slice(0, 160)) : ('AI service · ' + data.error));
          try { console.error('[vault-intake] AI ERROR for ' + fname, data); } catch(e){}
          doneCount++; report.innerHTML = _scanUI(doneCount, files.length, logged.length); return;
        }
        // v346 — AUTO-RETRY EMPTIES on the FULL image. A cropped read that returns NOTHING (no items,
        // finds, OR unrecognized) almost always means the LOCATE box clipped/missed the tooltip — the
        // text simply wasn't in the crop. Re-read the whole uncropped image (cropped:false, so no
        // single-item cap) to recover the item instead of logging a false "empty". One extra call only
        // for shots that would otherwise be a total miss.
        var _isEmpty = function(d){ return !d || !((d.items&&d.items.length)||(d.finds&&d.finds.length)||(d.unrecognized&&d.unrecognized.length)); };
        if (_isEmpty(data) && !_aiLimitHit && _box && _imRef){
          try {
            var _full = _vEnlarge(_imRef, null);
            // v357 — the retry is still ONE hovered shot (the crop just clipped it), so send cropped:true
            // so the backend caps to the single best read. Was cropped:false (no cap) → the retry could
            // pull background-grid items too, re-inflating the count past the screenshot total.
            var _r2 = await _vFetch(endpoint, { method:'POST', headers:{'content-type':'application/json'},
              body: JSON.stringify({ image:_full, media_type:'image/jpeg', names:vocab, file:fname, cropped:true }) }, 75000);
            if (_r2.ok){ var _d2 = await _r2.json(); if (_aiIsLimit(_d2)) _aiLimitHit = true; else if (!_isEmpty(_d2)){ data = _d2;
              try { console.log('[vault-intake] ' + fname + ' → empty crop → full-image retry recovered', _d2.items || _d2.unrecognized); } catch(e){} } }
          } catch(e){}
        }
        // v413 — LAST-RESORT recovery for a STILL-empty shot: read the full image with cropped:FALSE (no
        // single-item cap), the widest net. Catches the "no tooltip text" miss where a tooltip IS clearly on
        // screen but the single-item passes kept reading nothing (Konyo's Grim Scythe 18.18.35). Better to
        // surface the item (dismiss any stray extra) than silently drop a real one. Only fires when the shot
        // would otherwise be a total empty — never inflates a shot that already read something.
        if (_isEmpty(data) && !_aiLimitHit && _imRef){
          try {
            var _full3 = _vEnlarge(_imRef, null);
            var _r3 = await _vFetch(endpoint, { method:'POST', headers:{'content-type':'application/json'},
              body: JSON.stringify({ image:_full3, media_type:'image/jpeg', names:vocab, file:fname, cropped:false }) }, 75000);
            if (_r3.ok){ var _d3 = await _r3.json(); if (_aiIsLimit(_d3)) _aiLimitHit = true; else if (!_isEmpty(_d3)){ data = _d3;
              try { console.log('[vault-intake] ' + fname + ' → still empty → wide-net (cropped:false) retry recovered', _d3.items || _d3.unrecognized); } catch(e){} } }
          } catch(e){}
        }
        // v415 — FINAL fallback for a still-empty shot: re-read the full image with a CONTRAST BOOST. Recovers
        // a faint / semi-transparent tooltip overlapping the UI (Konyo's Superior Grim Scythe) where the text is
        // legible to a human but too low-contrast for the model at normal exposure. One last call, empties only.
        if (_isEmpty(data) && !_aiLimitHit && _imRef){
          try {
            var _fullB = _vEnlarge(_imRef, null, 1568, 0.95, true);   // boost = true
            var _rB = await _vFetch(endpoint, { method:'POST', headers:{'content-type':'application/json'},
              body: JSON.stringify({ image:_fullB, media_type:'image/jpeg', names:vocab, file:fname, cropped:false }) }, 75000);
            if (_rB.ok){ var _dB = await _rB.json(); if (_aiIsLimit(_dB)) _aiLimitHit = true; else if (!_isEmpty(_dB)){ data = _dB;
              try { console.log('[vault-intake] ' + fname + ' → still empty → CONTRAST-BOOST retry recovered', _dB.items || _dB.unrecognized); } catch(e){} } }
          } catch(e){}
        }
        // v417 — ABSOLUTE last resort: TEXT-ISOLATION on the LOCATED tooltip crop (or whole image if locate
        // missed). Binarizes on HSV-value so faint glyphs separate HARD from a busy see-through background —
        // the one lever the boost tiers don't pull (they lift the background too). Two passes at different
        // floors, because the right threshold depends on how transparent the tooltip is; first non-empty wins.
        if (_isEmpty(data) && !_aiLimitHit && _imRef){
          // v627 — third, DEEPER floor (Konyo's Death Mask · Socketed(2): a translucent tooltip over the
          // red/blue stash grid beat floors 92+60 twice across two batches — the correctly-located crop
          // was simply illegible; a lower value-floor keeps the faintest glyph pixels).
          var _isoFloors = [92, 60, 38];
          for (var _fi = 0; _fi < _isoFloors.length && _isEmpty(data); _fi++){
            try {
              var _iso = _vTextIso(_imRef, _box || null, 1568, _isoFloors[_fi]);
              var _rI = await _vFetch(endpoint, { method:'POST', headers:{'content-type':'application/json'},
                body: JSON.stringify({ image:_iso, media_type:'image/jpeg', names:vocab, file:fname, cropped: !!_box }) }, 75000);
              if (_rI.ok){ var _dI = await _rI.json(); if (_aiIsLimit(_dI)) _aiLimitHit = true; else if (!_isEmpty(_dI)){ data = _dI;
                try { console.log('[vault-intake] ' + fname + ' → still empty → TEXT-ISOLATION (floor ' + _isoFloors[_fi] + ') recovered', _dI.items || _dI.unrecognized); } catch(e){} } }
            } catch(e){}
          }
        }
        // v421 — RAW-NAME escape hatch: a crisp, clearly-readable tooltip that the vocab-matching read still
        // returned empty on (Konyo's Ghoul Aegis — a Reign-of-the-Warlock UNIQUE on a tooltip-only crop). Ask
        // the backend for JUST the top coloured NAME line (no vocabulary, no single-item rule, mod names OK) so
        // any legible tooltip yields a name instead of "∅ no tooltip text". Resolves to a grail item if known,
        // else surfaces in the throw-out review (keepable) — never silently dropped.
        // v435 — REVERTED to the original CROPPED + ENLARGED raw-name read (the v432 full-frame experiment
        // hurt accuracy: full-screen text is too small, so 10-15 of 47 shots stopped recognizing — WORSE than
        // before). Konyo's switch-back: crop to the located tooltip box (or the whole crop if locate missed) and
        // upscale ≤3.2× so the NAME is large and legible — the same enlargement the other passes use.
        if (_isEmpty(data) && !_aiLimitHit && _imRef){
          try {
            var _rawImg = _vEnlarge(_imRef, _box || null);
            var _rN = await _vFetch(endpoint, { method:'POST', headers:{'content-type':'application/json'},
              body: JSON.stringify({ image:_rawImg, media_type:'image/jpeg', names:vocab, file:fname, kind:'rawname' }) }, 60000);
            if (_rN.ok){ var _dN = await _rN.json(); if (_aiIsLimit(_dN)) _aiLimitHit = true; else if (!_isEmpty(_dN)){ data = _dN;
              try { console.log('[vault-intake] ' + fname + ' → still empty → RAW-NAME recovered', _dN.items || _dN.unrecognized); } catch(e){} } }
          } catch(e){}
        }
        // v435 — the ONE tiny tweak (keeps the 95-99% accuracy of the cropped read above, adds a pinpoint for
        // the rare miss): a DETACHED tooltip — the kind locate boxes wrong — is almost always pinned to the
        // TOP-LEFT corner (D2R draws a stash-item tooltip there; Konyo's Superior Grim Scythe). So if everything
        // above is STILL empty, crop JUST that corner region and upscale it hard (≤3.2×) → the floating NAME is
        // large + legible, WITHOUT shrinking the whole screen (the full-frame v432 experiment that hurt accuracy).
        if (_isEmpty(data) && !_aiLimitHit && _imRef){
          // v623 (Konyo's 37-batch calibration: 7 misses, 2 verified by eye as CLEAR tooltips the chain
          // never saw) — the detached-tooltip rescue generalizes from one corner to the THREE bands D2R
          // actually pins tooltips to: top-left (stash items), LEFT-CENTER tall (his Bone Visage — the
          // old 0.42 bottom cut it), and the RIGHT/inventory panel (his Death Mask · Socketed (2), which
          // the left-only crop could never see). First non-empty wins; each is upscaled like the others.
          var _bands = [ [0, 0, 0.5, 0.42], [0, 0.08, 0.55, 0.62], [0.45, 0.05, 1, 0.65] ];
          for (var _bi = 0; _bi < _bands.length && _isEmpty(data); _bi++){
            try {
              var _tl = _vEnlarge(_imRef, _bands[_bi]);
              var _rT = await _vFetch(endpoint, { method:'POST', headers:{'content-type':'application/json'},
                body: JSON.stringify({ image:_tl, media_type:'image/jpeg', names:vocab, file:fname, kind:'rawname' }) }, 60000);
              if (_rT.ok){ var _dT = await _rT.json(); if (_aiIsLimit(_dT)) _aiLimitHit = true; else if (!_isEmpty(_dT)){ data = _dT;
                try { console.log('[vault-intake] ' + fname + ' → still empty → BAND ' + _bi + ' raw-name recovered', _dT.items || _dT.unrecognized); } catch(e){} } }
            } catch(e){}
          }
        }
        // v601 — SOCKET-COUNT VERIFY (Konyo's Superior Long Sword — third recurrence of this miss class,
        // after the Superior Champion Axe and Grim Scythe): a read claiming an UNSOCKETED base
        // ("<Base> (Larzuk base)" / "Larzuk <Slot> Base") gets ONE pinpoint follow-up on the same image —
        // "does the tooltip say Socketed (N)?" (kind:'socketcheck'). N ≥ 1 → the main read missed the
        // line; relabel to "<Base> (Nos)" before registration (eth/superior flags follow the label).
        // Fires only when the shot produced exactly ONE Larzuk claim (the one-tooltip-per-shot flow) so a
        // rare multi-tooltip shot can't cross-wire. The main read pipeline stays untouched (LOCKED).
        try {
          var _lz = (data.items || []).filter(function(x){ return /\(Larzuk base\)\s*$/i.test(x) || /^Larzuk .+ Base$/i.test(x); });
          if (_lz.length === 1 && !_aiLimitHit){
            // v601.3 — verify on the FULL FRAME, never the crop: the debug trace proved the locate box
            // CLIPS the tooltip's bottom edge on tall tooltips — exactly where the "Socketed (N)" line
            // sits — which is the root cause of the whole recurring miss class (the main read gets the
            // name from the top of the crop, the sockets line is simply not in the image it saw).
            var _vImg = _imRef ? _vEnlarge(_imRef, null) : b64;
            if (_vImg){
              var _vr = await _vFetch(endpoint, { method:'POST', headers:{'content-type':'application/json'},
                body: JSON.stringify({ image:_vImg, media_type:'image/jpeg', file:fname, kind:'socketcheck' }) }, 45000);
              if (_vr.ok){ var _vd = await _vr.json();
                var _vn = _vd && isFinite(+_vd.sockets) ? +_vd.sockets : 0;
                if (_vn >= 1 && _vn <= 6){
                  var _oldL = _lz[0];
                  var _newL = /\(Larzuk base\)\s*$/i.test(_oldL)
                    ? _oldL.replace(/\s*\(Larzuk base\)\s*$/i, ' ('+_vn+'os)')
                    : _oldL.replace(/^Larzuk (.+) Base$/i, 'Socketed $1 ('+_vn+'os)');
                  data.items = data.items.map(function(x){ return x === _oldL ? _newL : x; });
                  ['ethereal','superior'].forEach(function(k){ if (Array.isArray(data[k])) data[k] = data[k].map(function(x){ return x === _oldL ? _newL : x; }); });
                  try { console.warn('[vault-intake] ' + fname + ' → SOCKET VERIFY corrected "' + _oldL + '" → "' + _newL + '" (main read missed the Socketed line)'); } catch(e){}
                }
              }
            }
          }
        } catch(e){}
        // intake log — raw AI read per screenshot (open DevTools console to tune accuracy)
        try { console.log('[vault-intake] ' + fname + ' →', { items: data.items || [], unrecognized: data.unrecognized || [] }); } catch(e){}
        (data.items || []).forEach(function(n){
          if (typeof _ensureSocketBaseEntry === 'function') _ensureSocketBaseEntry(n);   // v379 — per-base socketed identity (art + exact max sockets)
          // v394 — LOW set pieces (Sigon's/Sander's/etc.): mark the SET's grail aggregate ✓ for the codex/
          // tracker, then THROW OUT the physical piece — don't keep or mule it. Konyo: reverse low-set muling.
          try {
            var _lsm = suggestMule(n);
            if (_lsm && _lsm.id === '__throwout'){
              try { var _spX = window.findSetPiece && window.findSetPiece(n);
                if (_spX && window.__setStemOf && typeof ITEMS!=='undefined'){ var _stX = window.__setStemOf((_spX.set && _spX.set.name) || '');
                  var _agX = ITEMS.find(function(i4){ return /\((any piece|set)\)\s*$/i.test(i4.n) && _stX.indexOf(window.__setStemOf(i4.n)) === 0; });
                  if (_agX) owned.add(_agX.n); } } catch(e){}
              if (!owned.has(n)){ if (unrec.indexOf(n) < 0) unrec.push(n); fRec.unr.push(n); try { unknownReads.add(n); } catch(e){} }
              return;   // low set — thrown out, not kept/muled
            }
          } catch(e){}
          if (!owned.has(n)) {
            owned.add(n);
            // v227: an exact piece ✓s its set's grail aggregate row too (calc-only)
            try {
              var spg = window.findSetPiece && window.findSetPiece(n);
              if (spg && window.__setStemOf && typeof ITEMS!=='undefined'){
                var pstem = window.__setStemOf((spg.set && spg.set.name) || '');
                var agg = ITEMS.find(function(it2){ return /\((any piece|set)\)\s*$/i.test(it2.n) && pstem.indexOf(window.__setStemOf(it2.n)) === 0; });
                if (agg) owned.add(agg.n);
              }
            } catch(e){}
            var sg = suggestMule(n);
            if (sg && muleById(sg.id) && !assign[n]) assign[n] = sg.id;
            else if (sg && sg.id==='__keep' && !assign[n]) assign[n] = '__keep';   // v409 — never-mule keeper (kept in inventory, shown in advisory, not muled)
            // v597 — a NEWLY-registered read is a FRESH physical item: any Forge chain-step memory for this
            // label belongs to a previous copy (Konyo's post-reset Bone Visage greeted him at "step 2/2" —
            // the OLD helm's Larzuk click had survived the vault reset). Reset it so the chain starts at 1.
            try { var _fst=JSON.parse(window.LSR.getItem('d2r_forgeStep')||'{}');
              if (_fst['chain|'+n]!=null){ delete _fst['chain|'+n]; window.LSR.setItem('d2r_forgeStep', JSON.stringify(_fst)); } } catch(e){}
            logged.push(n); fRec.nw.push(n);
          } else {
            // v342.28 — a re-read of a MULTI-KEEP staple that's still UNDER its target is a WANTED
            // extra copy (a spare you're collecting), not a discarded dupe. Bump the count; over
            // target it falls through to the normal already-owned path.
            var _tgt = multiTarget(n);
            var _cur = (copies[n] && copies[n] > 0) ? copies[n] : 1;
            // v375 — a generic SOCKETED / LARZUK BASE (cat 'Socketed bases') is a QUANTITY item: you
            // own MANY, and each screenshot is a SEPARATE physical base. Two white Threshers read the
            // SAME generic label ("Larzuk 2H Weapon Base") yet are different items (different files,
            // different durability) — so count each distinct read as an extra copy instead of
            // collapsing it to a phantom "duplicate shot". A grail UNIQUE stays presence-only (you
            // don't own two Tyrael's) → still collapses. The SEEN ledger already skips re-reading the
            // SAME file, so two reads here = two genuinely distinct screenshots (Konyo's two-Thresher test).
            var _qtyBase = (function(){ try { return !!(window.EXTRA_ITEMS && window.EXTRA_ITEMS[n] && window.EXTRA_ITEMS[n].cat === 'Socketed bases'); } catch(e){ return false; } })();
            if (_tgt > 1 && _cur < _tgt) {
              copies[n] = _cur + 1;
              extraCopies.push(n); (fRec.xc || (fRec.xc = [])).push(n);
            } else if (_qtyBase && _cur < _QTY_CAP) {
              // v403 — distinct physical base under the mule cap (3): keep as a separate copy
              copies[n] = _cur + 1;
              extraCopies.push(n); (fRec.xc || (fRec.xc = [])).push(n);
            } else if (_qtyBase) {
              // v403 — already muling the cap (3 of this base); a 4th+ physical copy is a THROW-OUT
              // (Konyo: "3 is the max CAP — if we have 4, 3 muled and 1 thrown out").
              cappedOut.push(n); (fRec.cap || (fRec.cap = [])).push(n);
            } else {
              // v310: the AI DID recognize it, but it's already ✓ owned (or at target) — count it so the
              // report shows "3 new + 6 already owned" instead of silently looking like 3/9.
              // v347 — for a NORMAL grail item (target 1) a re-read is a DUPLICATE you own a 2nd of:
              // bump the count so the Registered panel badges it ×N (UX: "you have spares"). A multi-keep
              // AT/over target is a true discard — leave its count alone (don't exceed the target).
              // v366 — but ONLY when there was genuine PRIOR history (_preReg>0). In a FRESH batch (after a
              // reset, vault empty at start) the same item in two screenshots is the SAME item photographed
              // twice — a DUPLICATE SHOT, not a 2nd copy. Bumping it to ×2 there is a phantom over-count
              // (Konyo: "when we reset how can it tell me owned for Chance Guards?"). Collapse to one instead.
              if (_tgt <= 1 && _preReg > 0) copies[n] = _cur + 1;
              if (dupes.indexOf(n) < 0) dupes.push(n);
              fRec.own.push(n);
            }
          }
        });
        (data.unrecognized || []).forEach(function(n){
          // v598 — FULLY-AUTOMATED low-base registration (Konyo: "this needs to be automated completely..
          // no clicks"). A "<Base> (Nos low base)" read carries EVERYTHING registration needs: the base
          // identity (quality prefix kept — Superior/Eth ride into the label), the EXACT socket count, and
          // _isRunewordBase + the vault verdict as the keep gates (same sources of truth as the Forge).
          // A runeword-capable keeper registers + mules automatically, exactly like a data.items read
          // ("Gothic Shield (3os low base)" → owned "Gothic Shield (3os)" → Sanctuary make-now). Only
          // genuine junk (can't host a word / verdict says vendor) still lands in the throw-out review.
          try {
            var _arl = window._autoRegisterLowBase ? window._autoRegisterLowBase(n) : null;
            if (_arl){
              if (_arl.mode === 'new'){ logged.push(_arl.label); fRec.nw.push(_arl.label); }
              else { if (extraCopies.indexOf(_arl.label) < 0) extraCopies.push(_arl.label); (fRec.xc || (fRec.xc = [])).push(_arl.label); }
              return;
            }
          } catch(e){}
          // v393 — a READ RUNEWORD (Enigma, Spirit, Call to Arms…) is a FORGED keeper, NOT a misread throw-out.
          // Recognize it: register (owned), mark it forged in the Chronicle (rwMade), and route it to a mule by
          // slot. Konyo: "runewords need their own grail and should be muled — this isn't an error."
          try {
            var _rwk = (typeof _rwResolve === 'function') ? _rwResolve(n) : ((typeof findRuneword === 'function') ? findRuneword(n) : null);
            if (_rwk){
              // v539 — a read that resolves to a runeword is recognized so it's NEVER thrown out, but it is NOT
              // auto-registered to owned (the RUNEWORDS locker) OR the Chronicle. OCR'd runeword NAMES are too
              // ambiguous — UI text, a base's "can-make" list, a Forge-tab screenshot — and kept injecting phantom
              // runewords into the RUNEWORDS locker + false "created" ticks (Konyo: "I didn't upload these
              // runewords"). Forged runewords are managed ONLY via the Chronicle ✓ (which has undo). Just skip it.
              return;   // recognized → never throw-out; not registered anywhere
            }
          } catch(e){}
          // v400 — a SECOND distinct-FILE read of the same base is a 2nd PHYSICAL item, not a duplicate shot:
          // the filename seen-ledger already guarantees the same file is never read twice, so a repeat name
          // from a different screenshot = another copy you own. Count it (×N) instead of collapsing it in the
          // Set. Konyo: "same item TYPE but a different one in my account — register the second too." Applies
          // to socketed bases / known base TYPES (a pure misread string still just collapses).
          var _cln = (typeof _throwClean==='function') ? _throwClean(n) : n;
          var _baseLike = /\(\d+\s*os/i.test(n) || ((typeof _baseCats==='function') && Object.keys(_baseCats(_cln)).length > 0);
          if (_baseLike && typeof unknownReads !== 'undefined' && unknownReads.has(n) && !owned.has(n)){
            copies[n] = ((copies[n] && copies[n] > 0) ? copies[n] : 1) + 1;
            if (extraCopies.indexOf(n) < 0) extraCopies.push(n); (fRec.xc || (fRec.xc = [])).push(n);
            return;   // 2nd copy counted (×N); already shown in the throw-out list
          }
          if (unrec.indexOf(n) < 0) unrec.push(n); fRec.unr.push(n);
          // v342.4 — persist unmatched reads so they're reviewable (not evaporated). Skip ones already
          // tracked as grail or a Magic & Rare keeper.
          try { if (!owned.has(n) && !(magicFinds && magicFinds[n])) unknownReads.add(n); } catch(e){} });
        // v342.3 — magic/rare/crafted keepers → the Magic & Rare bucket (separate from grail `owned`)
        (data.finds || []).forEach(function(f){
          var nm = f && f.name; if (!nm) return;
          var _mods = Array.isArray(f.mods) ? f.mods : [];   // v356 — verbatim stat lines off the tooltip
          // v396 — small-charm FILTER: keep only valuable rolls (MF/res/life/FHR/combos); throw out junk charms.
          try {
            var _scb = String((f.base || '') + ' ' + nm).toLowerCase();
            if (/small\s*charm/.test(_scb) && typeof _smallCharmKeep === 'function'){
              var _sk = _smallCharmKeep(_mods);
              if (_sk && !_sk.keep){ if (unrec.indexOf(nm) < 0) unrec.push(nm); fRec.unr.push(nm); try { unknownReads.add(nm); } catch(e){} return; }   // junk → throw-out
              if (_sk && _sk.keep && !assign[nm]) assign[nm] = 'uni-small';   // valuable → mule to UNI-SMALL
            } else if (typeof _jewelryKeep === 'function'){
              // v416 — TOP-TIER gate for rolled-name rings · amulets · jewels · large/grand charms. A junk
              // rare ring (Blood Grip: +AR/+energy/sliver of res) gets THROWN OUT, not muled — only a roll
              // that rivals SoJ/Raven (dual leech · FCR · +skills · loaded res/stat cluster · skiller) is kept.
              var _jk = _jewelryKeep(_mods, f.base);
              if (_jk && !_jk.keep){ if (unrec.indexOf(nm) < 0) unrec.push(nm); fRec.unr.push(nm); try { unknownReads.add(nm); } catch(e){} return; }   // junk jewelry → throw-out
              if (_jk && _jk.keep && !assign[nm]) assign[nm] = 'magic-rare';   // top-tier → MAGIC & RARE locker
            }
          } catch(e){}
          if (!magicFinds[nm]){ magicFinds[nm] = { q: f.q || 'magic', base: f.base || '', mods: _mods }; magicNew.push(nm); }
          else if (typeof magicFinds[nm] === 'object'){
            if (!magicFinds[nm].base && f.base) magicFinds[nm].base = f.base;
            // fill mods if we didn't have them yet (a later/cleaner read of the same item)
            if (_mods.length && !(magicFinds[nm].mods && magicFinds[nm].mods.length)) magicFinds[nm].mods = _mods;
          }
          fRec.mf.push(nm);
        });
        // v395 — record which reads are ETHEREAL (Cannot be Repaired). Match against the canonical name the
        // runeword/grail lookups resolve to, so the ⊘ badge sticks to the registered item.
        (data.ethereal || []).forEach(function(en){
          if (!en) return;
          var _cn = en;
          try { if (typeof findRuneword==='function' && findRuneword(en)) _cn = findRuneword(en); } catch(e){}
          // v429 — TYPE GUARD: never tag an item ethereal if its kind CAN'T be ethereal (rings/amulets/charms/
          // jewels/runes/gems/javelins/throwing-weapons). A mis-read (or a misclassified find) can't earn a
          // false ⊘ badge. Unknown types (null) still pass — only a definite "false" is blocked.
          try { if (typeof _canBeEthereal==='function' && _canBeEthereal(_cn) === false) return; } catch(e){}
          try { etherealItems.add(_cn); } catch(e){}
        });
        // v412 — record SUPERIOR socketed bases (can't runeword). Registered under the exact socket-base label.
        (data.superior || []).forEach(function(sn){ if (sn) { try { superiorBases.add(sn); } catch(e){} } });
        if (data.usage) cost += (data.usage.in || 0) / 1e6 * 3.0 + (data.usage.out || 0) / 1e6 * 15.0;   // v398 — items read now Sonnet 4.6 ($3/M in · $15/M out)
      } catch(e){ errors++; fRec.err = true; }
      doneCount++;
      report.innerHTML = _scanUI(doneCount, files.length, logged.length);
    }
    // worker pool — up to CONC screenshots read concurrently (huge speedup vs one-at-a-time)
    var CONC = Math.min(5, files.length), _next = 0;
    async function _worker(){ while (_next < files.length){ if (_aiLimitHit) break; var _my = _next++; await processFile(_my); } }   // v438 — stop pulling new shots once the API cap is hit
    var _pool = []; for (var _w = 0; _w < CONC; _w++) _pool.push(_worker());
    await Promise.all(_pool);
    // v342.27 / v413.1 — remember files we read so re-dropping them is free. CRITICAL: mark a file SEEN only
    // if it actually READ SOMETHING (a grail item, magic/rare find, or throw-out). A file that errored OR came
    // back TRULY EMPTY ("∅ no tooltip text") must stay re-scannable — otherwise it's silently skipped forever
    // and a re-shoot / the wide-net retry never gets to recover it (Konyo's Grim Scythe 18.18.35). This runs
    // for BOTH paths (the folder scan pre-marks files seen at discovery, so empties must be UN-marked here).
    // v567 — but ONLY re-scannable by a MANUAL 🔄 Scan, never by the 12s auto-poll: the v413.1 hard-delete +
    // the v396.3 auto-watch made every no-match screenshot an INFINITE re-read loop (Konyo's 3 stash shots
    // were re-billed to the AI every 12 seconds for 10+ minutes, flooding the journal with blank sessions).
    // A no-match file now gets a soft 'retry' mark: the quiet auto-scan treats it as seen; the manual Scan
    // button treats it as fresh — the recovery intent survives, the money-burning loop cannot.
    try {
      var _sNow = seenLedger();
      files.forEach(function(f, i){
        var fr = perFile[i]; if (!f || !f.name || !fr) return;
        var _readSomething = !fr.err && ((fr.nw && fr.nw.length) || (fr.own && fr.own.length) || (fr.unr && fr.unr.length) || (fr.mf && fr.mf.length));
        if (_readSomething){ _sNow[f.name] = 1; _sNow[f.name + '|' + f.lastModified] = 1; }
        else { _sNow[f.name] = 'retry'; delete _sNow[f.name + '|' + f.lastModified]; }   // err / no-match → manual-rescan only
      });
      window.LSR.setItem(SEEN_KEY, JSON.stringify(_sNow));
    } catch(e){}
    journalAdd(logged, perFile);
    try { var _promoted=(typeof window._promoteUnknownBases==='function')?window._promoteUnknownBases():[]; if(_promoted.length && typeof toast==='function') toast('🧰 '+_promoted.length+' read'+(_promoted.length>1?'s':'')+' promoted to forge bases: '+_promoted.join(', ')); } catch(e){}   // v631
    persistOwned(); saveA(); renderVault(); refreshOpenCard(); renderJournal();
    try { if (typeof renderAll === 'function') renderAll(); } catch(e){}
    // v342.7 — fixed-format, scrollable, ORGANIZED report card with a grand TOTAL (Konyo: "fixed format
    // on the bottom … scrollbar … total of registered items also not just each section").
    // v349 — rarity colour + #arttip hover (image+description) on every name in the report body.
    var _colorNames = function(arr){ return arr.map(function(n){ return (typeof _vColorName==='function') ? _vColorName(n) : ('<span'+(typeof _qStyle==='function'?_qStyle(n,'unique'):'')+'>'+esc(n)+'</span>'); }).join(' · '); };
    var _poolM = ownedPool();
    var _grailReg = Array.from(owned).filter(function(n){ return !isAggregate(n) && (isSharedStash(n) || _poolM.indexOf(n)>=0); }).length;
    var _magicReg = Object.keys(magicFinds||{}).length;
    var _throwReg = (typeof unknownReads!=='undefined' && unknownReads) ? unknownReads.size : 0;
    var _totalReg = _grailReg + _magicReg + _throwReg;
    var body = '';
    body += '<div class="vir-line">'
      + (logged.length
         ? '<span class="vir-k vir-k-new">✓ ' + logged.length + ' NEW</span> logged + assigned: ' + _colorNames(logged)
         : (dupes.length ? '<span class="vir-k vir-k-own">no NEW</span> everything read was already ✓ owned'
            : '<span class="vir-k vir-dim">none</span> no readable tracked items in ' + files.length + ' screenshot' + (files.length===1?'':'s')))
      + '</div>';
    if (extraCopies.length) { var _ecUniq = extraCopies.filter(function(n, i){ return extraCopies.indexOf(n) === i; });   // v401 — list each item ONCE with its final ×count (not once per extra read)
      body += '<div class="vir-line"><span class="vir-k" style="color:var(--gold-bright,#f0c060)">📦 extra copies · ' + extraCopies.length + '</span> ' + _ecUniq.map(function(n){ return _colorNames([n]) + ' <span style="color:#b5a48a;font-size:11px">(now ×' + copyCount(n) + (multiTarget(n) > 1 ? (' / ' + multiTarget(n)) : '') + ')</span>'; }).join(' · ') + ' <em>— extra copies, kept (not discarded)</em></div>'; }
    if (dupes.length) body += '<div class="vir-line"><span class="vir-k vir-k-own">already owned · ' + dupes.length + '</span> ' + _colorNames(dupes) + '</div>';
    if (magicNew.length) body += '<div class="vir-line"><span class="vir-k vir-k-magic">🔮 magic &amp; rare · ' + magicNew.length + '</span> ' + magicNew.map(function(n){ var q=_mfQual(n); var c=q==='rare'?'#ffd54a':(q==='crafted'?'var(--q-orange,#ffa800)':'#7aa2ff'); return '<span style="color:'+c+'">'+esc(n)+'</span>'; }).join(' · ') + '</div>';
    if (unrec.length) body += '<div class="vir-line vir-dim"><span class="vir-k vir-k-unmatched">🗑 throw-out · ' + unrec.length + '</span> ' + unrec.map(function(n){ return (typeof _vColorName==='function')?_vColorName(n):esc(n); }).join(' · ') + ' <em>— not grail; review &amp; keep/dismiss in 📋 Registered</em></div>';
    if (cappedOut.length) { var _capUniq = cappedOut.filter(function(n,i){ return cappedOut.indexOf(n)===i; });   // v403 — over the 3-copy mule cap → throw out the extras
      body += '<div class="vir-line vir-dim"><span class="vir-k vir-k-unmatched" style="border-color:rgba(240,192,96,.5);color:#f0c060">🗑 over-cap · ' + cappedOut.length + '</span> ' + _capUniq.map(function(n){ return _colorNames([n]); }).join(' · ') + ' <em>— already muling ' + _QTY_CAP + ' of these; throw out the extra' + (cappedOut.length===1?'':'s') + '</em></div>'; }
    if (!logged.length && !dupes.length && !unrec.length && !magicNew.length && !errors) body += '<div class="vir-line vir-dim">💡 the AI reads item NAMES, not icons — open a tooltip (hover) or hold Alt over loot, then screenshot.</div>';
    // v366 — the per-screenshot breakdown lived BOTH here and in the "Recently registered" history below,
    // which read as two near-identical panels. Removed the duplicate copy from this transient scan card;
    // the history owns the one canonical breakdown (📂 per-screenshot breakdown, with the same thumbnails).
    if (files.length > 1 || perFile.some(function(f){ return f.nw.length || f.own.length || f.unr.length || f.mf.length || f.err; })){
      body += '<div class="vir-line vir-dim" style="font-size:11px">📂 per-screenshot breakdown (which shot → which items) is in <strong>🕘 Recently registered</strong> just below ↓</div>';
    }
    if (errors) body += '<div class="vir-line" style="color:var(--hell,#ff4040)">' + errors + ' screenshot' + (errors===1?'':'s') + ' failed — retry or check the connection.</div>';
    if (_aiErr) body += '<div class="vir-line" style="color:var(--hell,#ff4040)"><strong>⚠ ' + esc(_aiErr) + '</strong> — this is an AI-service failure, NOT your screenshots. Likely the API key, credits, or a rate-limit on a big batch. Retry a smaller batch; if it persists the key/credits need attention.</div>';
    // v344 — surface the shots that need a human look at the TOP of the card (not buried in the expand):
    // EMPTY reads (no tooltip text found → maybe a real item the AI couldn't read) and THROW-OUT-ONLY
    // shots (the only thing read didn't match grail → could be a misread valuable). Filenames listed so
    // Konyo can jump straight to them. Shots that DID register a real item are not flagged.
    var _shortNL = function(s){ return String(s).replace(/^Screenshot\s+\d{4}-\d{2}-\d{2}\s+at\s+/i,'').replace(/\.(png|jpe?g|webp)$/i,''); };
    var _emptyShots = perFile.filter(function(f){ return !f.err && !f.nw.length && !f.mf.length && !f.own.length && !f.unr.length && !(f.xc && f.xc.length); });
    var _throwShots = perFile.filter(function(f){ return f.unr.length && !f.nw.length && !f.mf.length && !f.own.length; });
    var _needLook = '';
    var _needN = _emptyShots.length + _throwShots.length;
    if (_needN) {
      var _nlParts = [];
      if (_emptyShots.length) _nlParts.push('<b>' + _emptyShots.length + '</b> empty — no tooltip text read');
      if (_throwShots.length) _nlParts.push('<b>' + _throwShots.length + '</b> 🗑 throw-out only — read didn’t match grail (possible misread item)');
      // v366 — each flagged shot is CLICKABLE → opens that exact screenshot full-res (IndexedDB), so
      // Konyo can jump straight to the one of the 11 that needs a look instead of hunting the folder.
      var _nlNames = _emptyShots.concat(_throwShots).map(function(f){
        var _fb = f.thumb ? ' data-fb="'+esc(f.thumb)+'"' : '';
        return '<span class="vir-nl-fn vir-nl-clk" role="button" tabindex="0" data-shot="'+esc(f.file)+'"'+_fb+' title="click to open this screenshot full-size — '+esc(f.file)+'" onclick="window._shotLightbox&&window._shotLightbox(this.dataset.shot,this.dataset.fb||\'\')">🔍 ' + esc(_shortNL(f.file)) + '</span>';
      });
      _needLook = '<div class="vir-needlook" title="these screenshots either read no item text or read something that did not match a grail item — confirm none is a real item you want. Re-screenshot with a clean hover, or reclassify in 📋 Registered.">'
        + '<div class="vir-nl-top"><span class="vir-nl-h">⚠ ' + _needN + ' screenshot' + (_needN === 1 ? '' : 's') + ' need a look</span><span class="vir-nl-d">' + _nlParts.join(' · ') + '</span></div>'
        + '<div class="vir-nl-files">' + _nlNames.slice(0, 14).join('') + (_nlNames.length > 14 ? '<span class="vir-nl-fn vir-nl-more">+' + (_nlNames.length - 14) + ' more</span>' : '') + '</div></div>';
    }
    // v342.10 — reconcile the SCREENSHOT count so it's clear 62 shots ≠ 62 items (dupes collapse,
    // bases/junk are unmatched). Header leads with shots → registered; a reconcile row sums the outcome.
    // v441 — this card is the LAST-SCAN DELTA only (what THIS batch added). The canonical TOTAL + history live
    // in the joined "Recently registered" panel right below (CSS welds them into one). Konyo: stop showing "39
    // registered" twice — show the additive "+N new" on top, the running total below.
    var _newThis = Math.max(0, _totalReg - _preReg);
    var html = '<div class="vir-card vir-card-scan">'
      + '<div class="vir-head"><span class="vir-title">📸 Last scan · ' + files.length + ' screenshot' + (files.length===1?'':'s') + '</span>'
      + '<span class="vir-tot vir-delta" title="items this scan ADDED to your vault — folded into the running total below">+' + _newThis + ' new</span>'
      + '<span class="vir-sub">this scan: ' + logged.length + ' 🏦 muled · ' + magicNew.length + ' 🔮 magic · ' + (unrec.length+cappedOut.length) + ' 🗑 throw-out' + (cost?' · ≈$'+cost.toFixed(4):'') + '</span></div>'
      + (_preReg > 0
         ? '<div class="vir-accum" title="this batch ADDED to what was already registered — the vault remembers every prior scan and dedups against it from the first screenshot"><span class="va-pre"><b>' + _preReg + '</b> already in vault</span><span class="va-arrow">→</span><span class="va-new">+ <b>' + Math.max(0, _totalReg - _preReg) + '</b> new this scan</span><span class="va-arrow">→</span><span class="va-tot"><b>' + _totalReg + '</b> total registered</span></div>'
         : '')
      + (_aiErr ? '<div class="vir-needlook" style="border-color:rgba(255,64,64,.6);background:rgba(255,64,64,.08)"><div class="vir-nl-top"><span class="vir-nl-h" style="color:var(--hell,#ff4040)">⚠ AI service error — nothing registered</span><span class="vir-nl-d">' + esc(_aiErr) + ' · NOT your screenshots — likely API key / credits / rate-limit. Retry a smaller batch.</span></div></div>' : '')
      + _needLook
      + '<details class="vir-scandet"><summary class="vir-scansum">▸ scan details — new · copies · duplicates · throw-out · skipped</summary>'
      + '<div class="vir-reconcile"><span class="vir-rc"><b>' + logged.length + '</b> new</span>' + (extraCopies.length ? '<span class="vir-rc" style="color:var(--gold-bright,#f0c060)">+ <b>' + extraCopies.length + '</b> 📦 extra copies</span>' : '') + '<span class="vir-rc" title="' + (_preReg > 0 ? 'these items were already ✓ in your vault BEFORE this scan' : 'the vault was EMPTY at the start of this scan, so these are DUPLICATE SHOTS — the same item appeared in an earlier screenshot of this same batch (first = new, this = the repeat). Collapsed to one, never double-counted — NOT based on any prior history.') + '">+ <b>' + dupes.length + '</b> ' + (_preReg > 0 ? 'already-owned' : 'duplicate shot' + (dupes.length === 1 ? '' : 's')) + '</span><span class="vir-rc">+ <b>' + magicNew.length + '</b> 🔮 magic</span><span class="vir-rc">+ <b>' + (unrec.length + cappedOut.length) + '</b> 🗑 throw-out</span>' + (cappedOut.length ? '<span class="vir-rc" style="color:#b5a48a" title="extra copies past the 3-per-base mule cap">(incl <b>' + cappedOut.length + '</b> over-cap)</span>' : '') + (_seenSkip > 0 ? '<span class="vir-rc" style="color:#8a9aa8">· <b>' + _seenSkip + '</b> already-read file' + (_seenSkip===1?'':'s') + ' skipped (free)</span>' : '')
      + '<span class="vir-rc-note">' + (function(){ var _it = logged.length + magicNew.length + unrec.length + cappedOut.length;
          var parts = [files.length + ' shot' + (files.length===1?'':'s') + ' → ' + _it + ' item' + (_it===1?'':'s') + ' this scan'];
          if (extraCopies.length) parts.push(extraCopies.length + ' extra cop' + (extraCopies.length===1?'y':'ies'));
          if (cappedOut.length) parts.push(cappedOut.length + ' over the ' + _QTY_CAP + '-copy cap → thrown out');
          if (dupes.length) parts.push(dupes.length + ' duplicate shot' + (dupes.length===1?'':'s') + (_preReg>0?' (already owned)':' (same item — collapsed, not lost)'));
          if (_emptyShots.length) parts.push(_emptyShots.length + ' empty — no tooltip text, RE-SHOOT');
          if (_seenSkip) parts.push(_seenSkip + ' already-read file' + (_seenSkip===1?'':'s') + ' skipped');
          return parts.join(' · ') + ' — one shot can hold several items; duplicates never double-count.';
        })() + '</span></div></details>'
      // v443 — NO duplicate item list here: the Last-scan card is a pure SUMMARY (delta + need-a-look + scan
      // details). The ONE item list (color chips + per-screenshot breakdown) lives in the welded history zone
      // right below — Konyo: "why two sections showing the same items?". `body` (errors) folds in only if present.
      + (((errors || _aiErr) ) ? '<div class="vir-scan-errs" style="padding:8px 14px;border-top:1px solid rgba(255,64,64,.18)">' + (errors ? '<div class="vir-line" style="color:var(--hell,#ff4040)">' + errors + ' screenshot' + (errors===1?'':'s') + ' failed — retry or check the connection.</div>' : '') + '</div>' : '')
      + '</div>';
    report.innerHTML = html;
    } finally { window._vIntakeBusy = false; }   // v405 — ALWAYS clear (early return / throw included) so the folder auto-watch never wedges
  };

  // ── v212: 📂 folder watch — connect the D2R screenshots dir ONCE (File System
  // Access API, Chrome/Edge); the handle persists in IndexedDB, a seen-ledger in
  // localStorage keeps every scan incremental. New images run the SAME intake.
  var FOLDER_DB='d2r_vault_fs', FOLDER_KEY='shotdir', SEEN_KEY='d2r_intakeSeen';
  function idb(){ return new Promise(function(res, rej){
    var r=indexedDB.open(FOLDER_DB,1);
    r.onupgradeneeded=function(){ r.result.createObjectStore('kv'); };
    r.onsuccess=function(){ res(r.result); }; r.onerror=function(){ rej(r.error); };
  }); }
  function idbSet(k,v){ return idb().then(function(db){ return new Promise(function(res,rej){
    var t=db.transaction('kv','readwrite'); t.objectStore('kv').put(v,k);
    t.oncomplete=res; t.onerror=function(){ rej(t.error); };
  }); }); }
  function idbGet(k){ return idb().then(function(db){ return new Promise(function(res,rej){
    var t=db.transaction('kv','readonly'); var q=t.objectStore('kv').get(k);
    q.onsuccess=function(){ res(q.result); }; q.onerror=function(){ rej(q.error); };
  }); }); }
  // v365 — full-res screenshot store (IndexedDB, big quota) so click-to-enlarge shows the REAL 1920×1080
  // shot, not the tiny 220px grid thumb. Keyed 'shot:<filename>'. Cleared each scan → only the latest
  // batch is kept full-res (bounded). The small thumb stays in the journal for the grid icon.
  function _vPutShot(f, dataUrl){ return idbSet('shot:' + f, dataUrl).catch(function(){}); }
  function _vClearShots(){ return idb().then(function(db){ return new Promise(function(res){
    var t = db.transaction('kv', 'readwrite'); var st = t.objectStore('kv'); var cur = st.openCursor();
    cur.onsuccess = function(){ var c = cur.result; if (c){ if (String(c.key).indexOf('shot:') === 0) st.delete(c.key); c.continue(); } };
    t.oncomplete = function(){ res(); }; t.onerror = function(){ res(); };
  }); }).catch(function(){}); }
  // v570 — PRUNE instead of wipe-each-scan: wiping killed click-to-enlarge for every card from an earlier
  // session ("no shot" + thumb-only lightbox). Screenshot filenames carry their timestamp, so a descending
  // name sort = newest first; keep the newest `keepN` full-res shots, delete the rest. IndexedDB quota is
  // huge — 100 × ~300KB ≈ 30MB is nothing, and old cards keep their expandable HD screenshot.
  function _vPruneShots(keepN){ return idb().then(function(db){ return new Promise(function(res){
    var t = db.transaction('kv', 'readwrite'); var st = t.objectStore('kv'); var keys = [];
    var cur = st.openCursor();
    cur.onsuccess = function(){ var c = cur.result; if (c){ if (String(c.key).indexOf('shot:') === 0) keys.push(String(c.key)); c.continue(); }
      else { keys.sort().reverse().slice(keepN || 100).forEach(function(k){ st.delete(k); }); } };
    t.oncomplete = function(){ res(); }; t.onerror = function(){ res(); };
  }); }).catch(function(){}); }
  try { window._vPruneShots = _vPruneShots; } catch(e){}   // v570 — exposed for tests
  window._vGetShot = function(f){ return idbGet('shot:' + f).then(function(v){ return v || null; }).catch(function(){ return null; }); };
  // v571 — load the ORIGINAL screenshot straight from the linked folder by filename (object URL, native
  // resolution, zero storage cost). Konyo: "no shot needs to be PHOTOS of the item screenshot like the file
  // itself, rendering HD 1920×1080". Works whenever the folder is linked + the file still exists on disk —
  // review cards stay pictured even after the journal thumb was pruned or the session rolled off.
  window._vShotFromFolder = async function(fname){
    try {
      if (!fname) return null;
      var h = liveHandle; if (!h) { try { h = await idbGet(FOLDER_KEY); } catch(e){} }
      if (!h) return null;
      if ((await h.queryPermission({ mode: 'read' })) !== 'granted') return null;
      var fh = await h.getFileHandle(String(fname));
      var f = await fh.getFile();
      return URL.createObjectURL(f);
    } catch(e){ return null; }
  };
  // v609.1 — WHY did hydration fail? Chrome downgrades the persisted folder handle to permission
  // 'prompt' after a browser restart until a user GESTURE re-grants. Distinguish that from "no folder
  // linked" / "file deleted" so the review cards can offer a one-tap re-authorize instead of silently
  // degrading a TAGGED screenshot to a dead "no shot" (Konyo: "it should be tagged to folder like we coded").
  window._vFolderPerm = async function(){
    try { var h = liveHandle; if (!h){ try { h = await idbGet(FOLDER_KEY); } catch(e){} }
      if (!h) return 'none';
      return await h.queryPermission({ mode:'read' });
    } catch(e){ return 'none'; }
  };
  window._vFolderReauth = async function(){
    try { var h = liveHandle; if (!h){ try { h = await idbGet(FOLDER_KEY); } catch(e){} }
      if (!h) return false;
      var p = await h.queryPermission({ mode:'read' });
      if (p !== 'granted') p = await h.requestPermission({ mode:'read' });
      if (p === 'granted'){ liveHandle = h; _setFolderConnectedUI(true); return true; }
      return false;
    } catch(e){ return false; }
  };
  function seenLedger(){ try { return JSON.parse(window.LSR.getItem(SEEN_KEY)||'{}'); } catch(e){ return {}; } }
  // v224: ONE scan menu, rendered FULL-WIDTH in #vault-intake-report (the tiny
  // toolbar #vault-status span was invisible to Konyo — REG-class lesson:
  // injecting interactive UI into a cramped inline span = users never see it).
  // Every manual scan shows it. EVERY file is registered by name the moment the
  // menu appears (never re-read automatically); the buttons pick what to feed
  // the AI: the new ones, or a deliberate 🕐 Latest 20/40 session PAST the ledger.
  var _pendingAll = null, _pendingFresh = null;
  function vaultOfferMenu(all, fresh, seen){
    window.LSR.setItem(SEEN_KEY, JSON.stringify(seen));
    all.sort(function(a,b){ return a.lastModified-b.lastModified; });
    fresh.sort(function(a,b){ return a.lastModified-b.lastModified; });
    _pendingAll = all; _pendingFresh = fresh;
    var rep = document.getElementById('vault-intake-report');
    if (!rep){ if (fresh.length) window.vaultIntake(fresh, {fromFolder:true}); return; }
    rep.hidden = false;
    var html = '📂 folder scanned: <strong style="color:var(--best,#66ff88)">' + fresh.length + ' new</strong> · ' + all.length + ' screenshots total — read which?<br>';
    if (fresh.length) html += '<button class="vault-btn" onclick="window.vaultReadBatch(\'new\')" style="border-color:rgba(102,255,136,.5);color:var(--best,#66ff88)">✨ New ' + fresh.length + '</button> ';
    [20, 40].forEach(function(k){ if (all.length >= k) html += '<button class="vault-btn" onclick="window.vaultReadBatch('+k+')">🕐 Latest '+k+'</button> '; });
    if (all.length && all.length < 20) html += '<button class="vault-btn" onclick="window.vaultReadBatch('+all.length+')">🕐 All '+all.length+'</button> ';
    html += '<button class="vault-btn" onclick="window.vaultReadBatch(0)">Skip — just register</button>';
    rep.innerHTML = html;
  }
  window.vaultReadBatch = function(k){
    var all = _pendingAll || [], fresh = _pendingFresh || [];
    _pendingAll = _pendingFresh = null;
    var rep = document.getElementById('vault-intake-report');
    var pick = (k === 'new') ? fresh : (k ? all.slice(-k) : []);
    if (!pick.length){
      if (rep){ rep.innerHTML = ''; rep.hidden = true; }
      status(k ? '📂 nothing to read' : '📂 registered — only NEW screenshots count from now on');
      return;
    }
    status('📂 reading ' + pick.length + ' screenshot' + (pick.length===1?'':'s') + ' — already-owned items are skipped automatically…');
    window.vaultIntake(pick, {fromFolder:true});
  };
  var liveHandle = null; // session fallback when IndexedDB can't persist the handle
  window.vaultConnectFolder = async function(){
    try {
      var handle = await window.showDirectoryPicker({ id:'d2r-shots', mode:'read' });
      liveHandle = handle;
      try { await idbSet(FOLDER_KEY, handle); } catch(e){ /* session-only is fine */ }
      // v235: folder is remembered now — swap the Connect button for the animated
      // "watcher" (eye) so it's clear the folder is linked + being watched, and show Scan.
      _setFolderConnectedUI(true);
      status('📂 folder connected — scanning… new captures will auto-register from now on');
      window.vaultScanFolder();
      _startAutoWatch();   // v396.3 — auto-read new screenshots going forward (poll + on-focus)
    } catch(e){ if (e && e.name!=='AbortError') status('folder connect failed: '+e.name); }
  };
  var _vScanBusy = false;   // v567 — mutex: focus + visibilitychange + the 12s poll can fire within the same
  // moment; two overlapping scans both read the ledger BEFORE either writes it → the SAME batch went to the
  // AI twice (Konyo's journal: session pairs 1 second apart with contradictory reads of the same files).
  window.vaultScanFolder = async function(quiet){
    if (_vScanBusy){ if(!quiet) status('📂 a scan is already running…'); return; }
    _vScanBusy = true;
    try {
      var handle = liveHandle;
      if (!handle) { try { handle = await idbGet(FOLDER_KEY); } catch(e){} }
      if (!handle) { if(!quiet) status('no folder connected yet — click 📂 first'); return; }
      var perm = await handle.queryPermission({ mode:'read' });
      if (perm !== 'granted'){
        if (quiet) { status('📂 click 🔄 Scan folder to re-authorize access'); return; }
        perm = await handle.requestPermission({ mode:'read' });
        if (perm !== 'granted') { status('folder access declined'); return; }
      }
      var seen = seenLedger(), fresh = [], all = [], retriable = 0;
      var firstConnect = Object.keys(seen).length === 0;
      for await (var entry of handle.values()){
        if (entry.kind !== 'file' || !/\.(png|jpe?g|webp)$/i.test(entry.name)) continue;
        var f; try { f = await entry.getFile(); } catch(e){ continue; }   // v569 — deleted mid-enumeration → skip, don't abort the scan
        all.push(f);
        // v222: dedupe by FILE NAME — a name ever registered is NEVER read
        // again, even if the file is touched/re-saved (old name|mtime keys honored)
        // v567: a 'retry' soft mark (no-match read) counts as SEEN for the quiet auto-scan but as FRESH for
        // a manual 🔄 Scan — recoverable by hand, never auto-re-billed in a loop.
        var _mk = seen[f.name];
        if (!_mk && !seen[f.name + '|' + f.lastModified]) { seen[f.name] = 1; fresh.push(f); }
        else if (_mk === 'retry'){ retriable++; if (!quiet){ seen[f.name] = 1; fresh.push(f); } }
      }
      if (quiet){
        if (!fresh.length){ if (retriable) status('📂 '+retriable+' screenshot'+(retriable===1?'':'s')+' read nothing last time — hit 🔄 Scan folder to retry them'); return; }
        if (fresh.length <= 12){
          window.LSR.setItem(SEEN_KEY, JSON.stringify(seen));
          fresh.sort(function(a,b){ return a.lastModified-b.lastModified; });
          status('📂 '+fresh.length+' new screenshot'+(fresh.length===1?'':'s')+' — reading…');
          window.vaultIntake(fresh, {fromFolder:true});
        } else status('📂 '+fresh.length+' new screenshots waiting — hit 🔄 Scan folder to pick a batch');
        return;
      }
      // v584.1 — MANUAL scan with a small fresh batch reads IMMEDIATELY, exactly like the auto-watch
      // (Konyo's restart trap: the re-authorize click routed here, the offer menu pre-marked his new
      // shots seen, no batch was picked → "linked folder doesn't work"). The pick-a-batch menu is only
      // for BIG backlogs (>12) where the token guard genuinely matters.
      if (fresh.length > 0 && fresh.length <= 12){
        window.LSR.setItem(SEEN_KEY, JSON.stringify(seen));
        fresh.sort(function(a,b){ return a.lastModified-b.lastModified; });
        status('📂 '+fresh.length+' new screenshot'+(fresh.length===1?'':'s')+' — reading…');
        window.vaultIntake(fresh, {fromFolder:true});
        return;
      }
      vaultOfferMenu(all, fresh, seen);
    } catch(e){ if(!quiet) status('scan failed: '+(e && e.name || e)); }
    finally { _vScanBusy = false; }
  };
  // v221: Safari/Firefox have no showDirectoryPicker — fall back to the classic
  // webkitdirectory picker. No persistent handle, so each scan re-picks the folder;
  // the SAME seen-ledger keeps it incremental and the SAME first-connect guard
  // protects the token budget. NEVER hide the feature silently again (REG-011).
  window.vaultScanFolderLegacy = function(fileList){
    try {
      var seen = seenLedger(), fresh = [], all = [];
      var firstConnect = Object.keys(seen).length === 0;
      Array.prototype.forEach.call(fileList, function(f){
        if (!/\.(png|jpe?g|webp)$/i.test(f.name)) return;
        var rel = f.webkitRelativePath || f.name;
        if (rel.split('/').length > 2) return; // top-level only, like handle.values()
        all.push(f);
        var _mk = seen[f.name];
        if (!_mk && !seen[f.name + '|' + f.lastModified]) { seen[f.name] = 1; fresh.push(f); }
        else if (_mk === 'retry'){ seen[f.name] = 1; fresh.push(f); }   // v567 — legacy picker is manual → retry-able
      });
      vaultOfferMenu(all, fresh, seen);
    } catch(e){ status('scan failed: '+(e && e.message || e)); }
  };
  // v235: toggle the folder UI between "connect me" and the live animated watcher.
  function _setFolderConnectedUI(connected){
    try {
      var cb=document.getElementById('vault-folder-btn'),
          sb=document.getElementById('vault-scan-btn'),
          wch=document.getElementById('vault-watcher');
      var csb=document.getElementById('vault-clear-scan-btn');
      if (cb)  cb.style.display  = connected ? 'none' : '';
      if (sb)  sb.style.display  = connected ? '' : 'none';
      if (csb) csb.style.display = connected ? '' : 'none';
      if (wch) wch.style.display = connected ? 'inline-flex' : 'none';
    } catch(e){}
  }
  window._setFolderConnectedUI = _setFolderConnectedUI;
  // v569 — fully unlink the watched folder (used by the 🧹 full reset — Konyo: a reset should NOT stay
  // "linked to folder"): forget the persisted handle, drop the session handle, stop the poll, reset the UI.
  function idbDel(k){ return idb().then(function(db){ return new Promise(function(res,rej){
    var tx = db.transaction('kv','readwrite'); tx.objectStore('kv').delete(k);
    tx.oncomplete = function(){ res(); }; tx.onerror = function(){ rej(tx.error); };
  }); }); }
  window._vUnlinkFolder = async function(){
    liveHandle = null;
    try { await idbDel(FOLDER_KEY); } catch(e){}
    try { if (_pollTimer){ clearInterval(_pollTimer); _pollTimer = null; } _autoWatchOn = false; } catch(e){}
    try { document.removeEventListener('visibilitychange', _autoScanTick); window.removeEventListener('focus', _autoScanTick); } catch(e){}
    try { _setFolderConnectedUI(false); } catch(e){}
  };
  // v396.3 — AUTO-WATCH: the File System Access API has no file-change events, so we (a) re-scan whenever the
  // tab regains focus / becomes visible (you alt-tab back from fullscreen D2R after a screenshot → it auto-
  // reads it), and (b) poll the folder every ~12s while the tab is visible. Both use the QUIET scan, which
  // dedups via the seen-ledger and only feeds genuinely NEW screenshots to the AI. Skips while a read is in
  // flight (_vIntakeBusy) and when the tab is hidden (no wasted polling). Konyo: "it should auto-register."
  var _autoWatchOn = false, _pollTimer = null;
  function _autoScanTick(){
    try {
      if (document.visibilityState !== 'visible') return;
      if (window._vIntakeBusy) return;
      if (typeof window.vaultScanFolder === 'function') window.vaultScanFolder(true);
    } catch(e){}
  }
  function _startAutoWatch(){
    if (_autoWatchOn) return; _autoWatchOn = true;
    try { document.addEventListener('visibilitychange', _autoScanTick); } catch(e){}
    try { window.addEventListener('focus', _autoScanTick); } catch(e){}
    try { if (_pollTimer) clearInterval(_pollTimer); _pollTimer = setInterval(_autoScanTick, 12000); } catch(e){}
  }
  window._startFolderAutoWatch = _startAutoWatch;
  function initFolderWatch(){
    var cb=document.getElementById('vault-folder-btn'), sb=document.getElementById('vault-scan-btn');
    var di=document.getElementById('vault-dir-input');
    if ('showDirectoryPicker' in window){
      // v235: a remembered folder → swap Connect for the animated 👁 watcher +
      // show 🔄 Scan (folder stays linked across sessions; permission re-auths on
      // the first Scan click). No folder yet → show only 📂 Connect. Kills the
      // "connect again?" confusion and makes the linked state feel alive.
      var wch=document.getElementById('vault-watcher');
      if (wch) wch.onclick=function(){ window.vaultConnectFolder(); };
      idbGet(FOLDER_KEY).then(function(h){
        if (h){ _setFolderConnectedUI(true); window.vaultScanFolder(true); _startAutoWatch(); }
        else  { _setFolderConnectedUI(false); }
      }).catch(function(){ _setFolderConnectedUI(false); });
      return;
    }
    if (di && 'webkitdirectory' in di){
      if (sb){
        sb.style.display='';
        sb.textContent='📂 Scan screenshot folder';
        sb.title='pick your screenshots folder — only NEW images since the last scan are read (this browser re-asks each scan; Chrome/Edge remember the folder)';
        sb.onclick=function(){ di.click(); };
        // v229: Safari can't remember folder permission (no such API) — tell the
        // user the hands-free mode exists instead of leaving it undiscoverable
        var hint=document.createElement('span');
        hint.className='vault-status';
        hint.style.cssText='font-size:11px;color:var(--text-dim,#756657)';
        hint.innerHTML='⚡ want it hands-free? open this site in <strong>Chrome/Edge</strong> — connect the folder ONCE and the vault auto-reads new screenshots every visit';
        sb.parentNode.insertBefore(hint, sb.nextSibling);
      }
      di.addEventListener('change', function(){ window.vaultScanFolderLegacy(di.files); di.value=''; });
    }
  }
  // v215: the example = Konyo's OWN stash screenshot (Spellsteel tooltip visible) —
  // the exact input format the live endpoint reads correctly
  var VAULT_SHOT_EXAMPLE = 'art/perf/b64_0df29eb141.jpg';
  function initShotExample(){
    try {
      var img = document.getElementById('vault-shot-example');
      if (img) img.src = VAULT_SHOT_EXAMPLE;
    } catch(e){}
  }
  if (document.readyState==='loading') document.addEventListener('DOMContentLoaded', function(){ renderVault(); renderJournal(); initShotExample(); initFolderWatch(); });
  else { renderVault(); renderJournal(); initShotExample(); initFolderWatch(); }
})();
