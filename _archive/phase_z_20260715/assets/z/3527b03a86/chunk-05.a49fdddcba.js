
  // v535 — DYNAMIC endgame loot filter. Rebuilds LIVE from your Chronicle so it always matches the runewords you
  // still need: unmade runeword -> its socket-correct meta base(s) (window._forgeMetaBase) -> base item code. No
  // "cube up a white base" premise (v534: white bases can't be tier-upgraded) — it shows the RIGHT-TIER base to
  // FIND on the ground, then Larzuk it. Reuses the vetted lf-data-endgame template (uniques/sets/runes/gems/
  // charms/rare-circlet+ring+amulet shows + a trash-hide) and only swaps the base-show rules' codes.
  // v588 — PREMIUM TRADE BASES (Konyo): bases the trade market ALWAYS asks for — each worth ≥ an Ist
  // on its own as a clean white/eth/socketed drop (Archon Plate/Staff, Bone Visage, the 4os-Flail-for-
  // HotO class). These must NEVER sync off the loot filter, regardless of the Chronicle or bases you
  // already own — only ordinary bases keep the v535/v536.2 auto-shrink. Edit this list to taste.
  // v589 (Konyo) — ENDGAME-ONLY trim: Crystal Sword out (Phase Blade owns that niche), armors down to
  // Archon Plate + Mage Plate (Dusk Shroud / Wyrmhide / Sacred Armor out). Flail stays — THE HotO base.
  window._premiumTradeBases = [
    'Archon Plate', 'Mage Plate',                                                    // the two trade armors
    'Archon Staff',                                                                  // 6os caster staff
    'Bone Visage',                                                                   // rare helm (Dream/Delirium class)
    'Monarch', 'Sacred Targe', 'Sacred Rondache', 'Troll Nest',                      // Spirit / pala-res / Phoenix shields
    'Flail', 'Phase Blade', 'Berserker Axe', 'Colossus Blade',                       // HotO / Grief / BotD weapons
    'Thresher', 'Giant Thresher', 'Cryptic Axe',                                     // eth merc polearms (Insight/Infinity)
    'Matriarchal Bow', 'Grand Matron Bow'                                            // Faith / Brand bows
  ];
  window._endgameFilterBases = function(opts){
    // v662 — opts.fresh: build for a FRESH grail (the cousin's reality). The normal build shrinks to
    // KONYO's Chronicle — and the shared-chronicle seed floors his 88 words on ANY browser, so a cousin
    // generating his own copy gets the same shrunk filter, with every sub-endgame socketed base folded
    // into the Hide-ETH-Sockets rule. fresh ignores rwMade + the owned-base sync so ALL words light
    // their bases (socketed/eth), exactly what a from-zero player hunts.
    var fresh = !!(opts && opts.fresh);
    var out = { codes: [], names: [], gambleOnlyCodes: [] };
    try {
      var CODE = JSON.parse(document.getElementById('lf-base-codes').textContent);
      var made = {}; try { if (!fresh) made = JSON.parse(window.LSR.getItem('d2r_rwMade')||'{}'); } catch(e){}
      var tips = (typeof RUNEWORD_TIP!=='undefined') ? RUNEWORD_TIP : (window.RUNEWORD_TIP||{});
      // v667 — chronicle stage, shared with the build's wide/doctrine split: early = <50% forged (or a fresh/cousin build)
      var _totalW = Object.keys(tips).length, _madeW = Object.keys(tips).filter(function(n){ return made[n]; }).length;
      var _early = fresh || (_totalW > 0 && (_madeW/_totalW) < 0.5);
      var meta = window._forgeMetaBase;
      // v536.2 — SYNC with the Forge: skip a word you ALREADY own a socket-correct base for (it's in the Forge's
      // make-now / pipeline, or a "have base, need runes" one-step). No point farming the ideal base for a word
      // you can already forge on a base you hold (e.g. Eternity/Honor on Konyo's Thresher+Cryptic Axe → don't
      // keep flagging Scourge/Ettin Axe on the ground). Only words with NO owned base still show their bases.
      var ownedBaseWord = {};
      // v587 — CAPACITY: an over-subscribed task (t.baseOver — its base copy is already claimed by a
      // higher-priority word) does NOT own a base → keep farming bases for that word.
      try { var sc = (!fresh && typeof window.forgeScan==='function') ? window.forgeScan() : null;
        if (sc){ [].concat(sc.now||[], sc.pipeline||[]).forEach(function(t){ if(t && t.base && !t.baseOver) ownedBaseWord[t.rw]=1; });
                 (sc.onestep||[]).forEach(function(t){ if(t && t.base && t.sub!=='base' && !t.baseOver) ownedBaseWord[t.rw]=1; }); } } catch(e){}
      var codeSet = {}, nameSet = {}, supOkSet = {}, larzukExact = {};   // v666 — bases where a live word's count == the trusted Larzuk max
      Object.keys(tips).forEach(function(rw){
        if (made[rw]) return;                                  // already forged -> skip
        if (typeof window._rwLadderBlocked==='function' && window._rwLadderBlocked(rw)) return;  // v553 — don't farm bases for ladder-only words you can't make off-ladder
        if (ownedBaseWord[rw]) return;                         // you own a socket-correct base for it -> not a base to farm
        var names = (typeof meta==='function') ? ((meta(rw)||{}).names||[]) : [];
        var _need = ((tips[rw]||{}).rec||[]).length;
        names.forEach(function(nm){
          if (!nm) return;
          if (/^\s*(Circlet|Coronet|Tiara|Diadem)\s*$/i.test(nm)) return;   // circlets can't host runewords
          var c = CODE[nm];
          if (c){ codeSet[c]=1; nameSet[nm]=1;
            // v575.2 — is a SUPERIOR drop of this base useful? Only if some unmade word needs exactly its
            // MAX sockets (superior = Larzuk-max only; the cube gamble is plain-normal only). Unknown max →
            // fail-open (superior allowed).
            var _mx = null; try { _mx = window._socketMaxTrusted(nm) || null; } catch(e){}   // v684 — trusted maxes only (understated weapon maxes wrongly denied superior/Larzuk-exact shows)
            if (!(_mx >= 1 && _mx <= 6) || _need === _mx) supOkSet[c] = 1;
            if (_mx >= 1 && _mx <= 6 && _need === _mx) larzukExact[c] = 1;   // v666 — Larzuk gives its max: ONE quest turns a PLAIN white into this word's base
          }
        });
      });
      // v588 — the premium trade floor joins LAST, unconditionally: no made[]/ownedBaseWord/ladder gate
      // touches it. supOk too — a SUPERIOR premium base is a better trade, never a gamble-only hide.
      // v592 — plainCodes: ONLY these light up as PLAIN (unsocketed, non-eth) whites. Everything else in
      // codes shows eth/socketed only — Konyo farms sockets instead of burning Larzuk quests.
      var plainSet = {};
      // v667 (Konyo: 'premium plains I don't think I really need… only in the beginning of the
      // chronicle — I'm not larzuking a base just for the fuck of it') — the premium PLAIN floor is
      // STAGE-GATED: below 50% forged it lights plain whites (early trade capital, the cousin's shell);
      // at 50%+ plains shrink to Larzuk-exact only. Premium SOCKETED/ETH copies keep riding the
      // universe — a grey 4os Archon Plate is still a pickup.
      // v667.2 (Konyo: 'not every single item though') — the premium floor is EARLY-ONLY in FULL:
      // below 50% forged it rides codes+socketed+plains as trade capital; from 50% on, premium bases
      // obey the exact same engine gates as every other base (hostability × socket feasibility ×
      // unmade words). No blanket floors: Flail/Bone Visage/eth-merc-polearms drop once their words
      // are forged; Archon Plate keeps riding only because Bramble still lives in it.
      if (_early) (window._premiumTradeBases || []).forEach(function(nm){
        var pc = CODE[nm]; if (!pc) return;
        codeSet[pc] = 1; nameSet[nm] = 1; supOkSet[pc] = 1; plainSet[pc] = 1;
      });
      out.codes = Object.keys(codeSet).sort();
      out.names = Object.keys(nameSet).sort();
      // v662.1 — ENGINE-TRUE SOCKETED UNIVERSE (Konyo: 'not just cousins build.. it should be
      // calibrated as a whole for the engine… I've been missing lots and lots of socketed gear').
      // The curated meta homes above are the FARM-PRIORITY intel (SI base hunt, plain/premium rules),
      // but the mod can't filter by socket COUNT — so hiding a socketed drop is only honest when NO
      // unmade word could ever live in that base TYPE. The socketed/eth show set is therefore the
      // _baseRunewords inverse: every base type class-legal for ANY unmade, non-ladder-blocked word.
      // A socketed Mage Plate shows while any armor word lives; forge the last armor word and the
      // whole armor class drops out on the next copy — the exact 'gradually removes the useless ones'
      // contract, computed from the engine instead of a hand-curated list.
      var sockSet = {};
      try {
        if (typeof window._baseRunewords === 'function'){
          Object.keys(CODE).forEach(function(nm){
            if (/^\s*(Circlet|Coronet|Tiara|Diadem)\s*$/i.test(nm)) return;   // circlets can't host runewords
            var c = CODE[nm]; if (!c) return;
            var isCurated = !!codeSet[c];
            if (isCurated) sockSet[c] = 1;                                    // curated/premium homes always ride socketed
            var hosts = window._baseRunewords(nm) || [];
            var liveNeeds = [];
            for (var hi = 0; hi < hosts.length; hi++){
              var hw = hosts[hi] && (hosts[hi].n || hosts[hi]); if (!hw) continue;
              if (made[hw]) continue;
              if (typeof window._rwLadderBlocked === 'function' && window._rwLadderBlocked(hw)) continue;
              liveNeeds.push(((tips[hw] || {}).rec || []).length);
            }
            if (!liveNeeds.length) return;                                    // no unmade word can live here → socketed copy is honestly useless
            // v665.3 (Konyo's Chaos run: plain-looking 'Scale Mail'/'Superior Elegant Blade' labels) —
            // SOCKET FEASIBILITY: a base whose TRUSTED max sockets sits below every live word's count
            // can never host any of them (a 2os-max Scale Mail is no Myth/Wealth base; a 3os-max
            // Elegant Blade is no Unbending Will). Trusted-max doctrine (v575.2): only exclude on a
            // KNOWN max — unknown maxes fail open, never wrongly hiding a real base.
            var _smx = null; try { _smx = window._socketMaxTrusted(nm) || null; } catch(e){}   // v684 — trusted maxes only: BASE_DB weapon maxes are understated and this gate HIDES bases (Wand max "1" hid real 2os White wands)
            // v667.1 — Larzuk-exact plains stay CURATED: only right-tier homes + premium bases earn a
            // plain-white show (a plain Ring Mail technically hosts Myth, but plain-spam is the exact
            // thing v592 killed). Non-curated bases remain socketed/eth-only forever.
            // v670 (Konyo's cow run: 'maybe only the mage plate') — PREMIUM names keep their Larzuk-exact
            // eligibility at EVERY stage: v667.2 gated premium out of codeSet late, which silently dropped
            // plain Mage Plate (max 3 = his 3os words). Quality doctrine: premium ∪ curated may earn a
            // Larzuk-exact plain; only premium's UNCONDITIONAL ride is early-gated.
            var _isPrem = false; try { _isPrem = (window._premiumTradeBases || []).indexOf(nm) >= 0; } catch(e){}
            if ((isCurated || _isPrem) && _smx >= 1 && _smx <= 6 && liveNeeds.indexOf(_smx) >= 0) larzukExact[c] = 1;
            if (!isCurated){
              if (_smx >= 1 && _smx <= 6 && !liveNeeds.some(function(n){ return n <= _smx; })) return;
              sockSet[c] = 1;
            }
            if (!(_smx >= 1 && _smx <= 6) || liveNeeds.indexOf(_smx) >= 0) supOkSet[c] = 1;
          });
        }
      } catch(e){}
      // v666/v667.1 (Konyo: 'or a MAX larzuk socket.. OR farming it socketed') — a plain white shows
      // when ONE Larzuk quest lands exactly on a live word's count. Merged HERE, after the full
      // universe pass, so premium/non-curated Larzuk-exacts (Mage Plate) make it in too.
      Object.keys(larzukExact).forEach(function(lc){ plainSet[lc] = 1; });
      out.plainCodes = Object.keys(plainSet).sort();
      out.sockCodes = Object.keys(sockSet).sort();
      if (!out.sockCodes.length) out.sockCodes = out.codes.slice();            // engine not ready → never narrower than the curated set
      out.gambleOnlyCodes = out.sockCodes.filter(function(c){ return !supOkSet[c]; });   // superior drops useless here
    } catch(e){}
    return out;
  };
  window.buildEndgameFilter = function(opts){
    var tplEl = document.getElementById('lf-data-endgame');
    var tpl = JSON.parse(tplEl.textContent);
    var eb = window._endgameFilterBases(opts);
    // v553 — ALWAYS sync the two base-show rules to the live set (was guarded by `if (eb.codes.length)`, which left
    // the template's ~50 hardcoded codes in place when nothing needs farming — contradicting the "0 bases" label).
    // Empty = show no bases, consistent with the count + the "shrinks to match your Chronicle" promise.
    // v592 (Konyo) — SOCKETED-ONLY for common bases: Larzuk quests are a pain — he'd rather FARM the
    // socketed drop. So the PLAIN-WHITE show rule ("Show Base Items") lights up ONLY the premium trade
    // floor (Bone Visage class — rare/valuable enough to burn a Larzuk or trade as-is); every other
    // wanted base appears eth/socketed ONLY (rule 3). No more plain War Spikes begging for a quest.
    tpl.rules.forEach(function(r){
      if (r.name==='3. Show ETH and Socket bases'){ r.equipmentItemCode = (eb.sockCodes||eb.codes).slice(); }   // v662.1 — the engine-true socketed universe
      if (r.name==='Show Base Items'){ r.equipmentItemCode = (eb.plainCodes||[]).slice(); }
    });
    // v562 — PLUG THE BLUE-MAGIC LEAK (Konyo's cow-run screenshots: magic Gothic Shield + magic Coronet showing).
    // The template's hide lists are STATIC complements of the OLD ~50-base draft: 70 codes (the wanted bases,
    // all 4 circlets, and stale drafts like Monarch/Colossus Blade) sat in NO rule at all, and this filter mod
    // defaults an unmatched item to SHOW — so every magic/rare/white copy of them leaked through. Fix, working
    // under both first-match and last-match rule semantics:
    //   (a) hide lists rebuilt LIVE = every base code (map ∪ template, keeps `pad`) minus quest items minus
    //       circlets minus the CURRENT wanted set — stale drafts get hidden again at every rarity;
    //   (b) the eth/socket show rule is pinned to normal+superior, so a socketed MAGIC wanted base can't ride it;
    //   (c) tail hide rules catch what the shows deliberately skip: magic/rare/cracked copies of wanted bases,
    //       and every non-rare circlet (rare circlets still show via "Show Rare Rings and Amulets", uniques via
    //       rule 2 — neither rarity is listed in the tails, so those keep working under either semantics).
    try {
      var CODE2 = JSON.parse(document.getElementById('lf-base-codes').textContent);
      var NEVER_HIDE = {hdm:1,hfh:1,hst:1,leg:1,msf:1,qf1:1,qf2:1,g33:1,d33:1};   // quest items — not real drops
      var CIRC = ['ci0','ci1','ci2','ci3'];
      var hideSet = {};
      tpl.rules.forEach(function(r){ if (r.ruleType==='hide') (r.equipmentItemCode||[]).forEach(function(c){ hideSet[c]=1; }); });
      Object.keys(CODE2).forEach(function(nm){ hideSet[CODE2[nm]]=1; });
      CIRC.forEach(function(c){ delete hideSet[c]; });
      Object.keys(NEVER_HIDE).forEach(function(c){ delete hideSet[c]; });
      (eb.sockCodes||eb.codes).forEach(function(c){ delete hideSet[c]; });   // v662.1 — nothing in the socketed universe may sit in a hide list
      var hideCodes = Object.keys(hideSet).sort();
      // v592 — a non-premium wanted base must be hidden as a PLAIN drop (it's only wanted eth/socketed):
      // its code joins the flat-item hide (rule 1, filterEtherealSocketed:false) but stays OUT of the
      // eth/socketed hide, so rule 3 keeps showing the drops actually worth picking up. Premium plains
      // keep showing via "Show Base Items". Works under first- and last-match semantics alike (the plain
      // drop matches ONLY a hide either way; the eth/socketed drop matches only the show).
      var _plainIs = {}; (eb.plainCodes||[]).forEach(function(c){ _plainIs[c]=1; });
      var plainHide = hideCodes.concat((eb.sockCodes||eb.codes).filter(function(c){ return !_plainIs[c]; })).sort();
      tpl.rules.forEach(function(r){
        if (r.name==='1. Hide Trash Gear'){ r.equipmentItemCode = plainHide.slice(); }
        if (r.name==='Hide ETH Sockets'){ r.equipmentItemCode = hideCodes.slice(); }
        if (r.name==='3. Show ETH and Socket bases'){ r.equipmentRarity = ['normal','hiQuality']; }
      });
      var TRASH_R = ['magic','rare','lowQuality'], Q3 = ['normal','exceptional','elite'];
      // v599 (Konyo's Torrid Diadem of Amicae) — a MAGIC DIADEM is a chase item (+3 class-skill / MF
      // rolls live on the elite circlet, alvl 85+), so BLUE Diadems (ci3) are exempt from the circlet
      // hide: the non-magic rarities keep the full 4-code hide, and a separate magic-rarity rule hides
      // only Circlet/Coronet/Tiara (the v562 blue-Coronet trash call stands). A blue Diadem matches NO
      // rule → the mod's default-show surfaces it.
      var CIRC_R = ['normal','lowQuality','hiQuality'], CIRC_MAGIC = ['ci0','ci1','ci2'];
      // v575.2 — SUPERIOR drops of GAMBLE-ONLY bases are useless (superior = Larzuk-max only; the word
      // needs LESS than max, reachable only by the plain-normal cube gamble) → hide their hiQuality drops.
      // Socketed/eth superiors keep riding rule 3 (a pre-socketed superior at the right count is usable).
      if ((eb.gambleOnlyCodes||[]).length){
        tpl.rules.push({ name:'Hide Superior Gamble-Only Bases', enabled:true, ruleType:'hide', filterEtherealSocketed:false, equipmentRarity:['hiQuality'], equipmentQuality:Q3.slice(), equipmentItemCode: eb.gambleOnlyCodes.slice() });
      }
      tpl.rules.push(
        { name:'Hide Magic Wanted Bases',     enabled:true, ruleType:'hide', filterEtherealSocketed:false, equipmentRarity:TRASH_R.slice(), equipmentQuality:Q3.slice(), equipmentItemCode: (eb.sockCodes||eb.codes).slice() },
        { name:'Hide Magic Wanted Bases ETH', enabled:true, ruleType:'hide', filterEtherealSocketed:true,  equipmentRarity:TRASH_R.slice(), equipmentQuality:Q3.slice(), equipmentItemCode: (eb.sockCodes||eb.codes).slice() },   // magic can never host a runeword — socketed magic of a wanted base is still trash
        { name:'Hide Non-Rare Circlets',      enabled:true, ruleType:'hide', filterEtherealSocketed:false, equipmentRarity:CIRC_R.slice(),  equipmentQuality:Q3.slice(), equipmentItemCode: CIRC.slice() },
        { name:'Hide Non-Rare Circlets ETH',  enabled:true, ruleType:'hide', filterEtherealSocketed:true,  equipmentRarity:CIRC_R.slice(),  equipmentQuality:Q3.slice(), equipmentItemCode: CIRC.slice() },
        { name:'Hide Magic Circlets Not Diadem',     enabled:true, ruleType:'hide', filterEtherealSocketed:false, equipmentRarity:['magic'], equipmentQuality:Q3.slice(), equipmentItemCode: CIRC_MAGIC.slice() },
        { name:'Hide Magic Circlets Not Diadem ETH', enabled:true, ruleType:'hide', filterEtherealSocketed:true,  equipmentRarity:['magic'], equipmentQuality:Q3.slice(), equipmentItemCode: CIRC_MAGIC.slice() }
      );
    } catch(e){}
    // v590 (Konyo) — CHRONICLE-NUMBERED NAME: the exported profile is "KonyoEndgame<N>" where N = runewords
    // forged (53/100 → KonyoEndgame53). Seeing the number in-game tells you at a glance whether the filter
    // you're running is in sync with your Chronicle — re-import when it lags.
    // v662 — PROGRESS-STAGED filter (Konyo: 'at first obviously give all socketed and all options…
    // and gradually as we tally off and progress through the forge and chronicle percentage wise it
    // automatically removes the useless ones'). Below 50% forged the player is LEVELING: a 2os Skull
    // Cap IS his Lore — so EVERY eth/socketed hide rule is stripped (sockets = show, period; unmatched
    // items default-show in the mod) while plain white/magic/rare trash hides stay. From 50% on, the
    // full endgame doctrine returns: curated homes + socketed-trash hides — and the base-show rules
    // keep shrinking with every forged word, exactly like Konyo's own filter always has. fresh:true
    // (the cousin export from Konyo's device) forces the wide stage regardless of the local chronicle.
    var _lfMadeN = (opts && opts.fresh) ? 0 : window._chronicleMadeCount();
    var _lfTotal = 0; try { _lfTotal = Object.keys((typeof RUNEWORD_TIP!=='undefined')?RUNEWORD_TIP:(window.RUNEWORD_TIP||{})).length; } catch(e){}
    var _lfWide = (opts && opts.fresh) || (_lfTotal > 0 && (_lfMadeN/_lfTotal) < 0.5);
    if (_lfWide) tpl.rules = tpl.rules.filter(function(r){ return !(r.ruleType==='hide' && r.filterEtherealSocketed===true); });
    tpl.name = (opts && opts.fresh) ? 'CousinFull' : ((window._isCousinShell ? 'Cousin' : 'KonyoEndgame') + window._chronicleMadeCount());   // v662/v663 — ASCII names; on the WINDOWS shell the number is the COUSIN's own progress
    return { text: JSON.stringify(tpl), baseCount: eb.codes.length, name: tpl.name };
  };
  // v590 — the one Chronicle-progress counter every filter surface shares (same math as the Forge meter).
  window._chronicleMadeCount = function(){
    try {
      var md = JSON.parse(window.LSR.getItem('d2r_rwMade')||'{}');
      var tips = (typeof RUNEWORD_TIP!=='undefined') ? RUNEWORD_TIP : (window.RUNEWORD_TIP||{});
      return Object.keys(tips).filter(function(n){ return md[n]; }).length;
    } catch(e){ return 0; }
  };
  // v591.1 — BOOT-RACE GUARD: this page is ONE huge file — the runeword engine (RUNEWORD_TIP mid-file,
  // forgeScan/_forgeMetaBase at the very end) comes alive SECONDS after this early block on a slow load.
  // Copying during that window exported a degenerate filter (premium floor only, "KonyoEndgame0") that
  // LOOKED valid. Every filter surface now checks readiness: Copy refuses with a "still loading" status,
  // the badge shows "loading…" and retries itself until the engine lands.
  window._lfEngineReady = function(){
    try {
      var tips = (typeof RUNEWORD_TIP!=='undefined') ? RUNEWORD_TIP : (window.RUNEWORD_TIP||{});
      return typeof window.forgeScan==='function' && typeof window._forgeMetaBase==='function' && Object.keys(tips).length>0;
    } catch(e){ return false; }
  };
  // Keep the "N bases" label + the numbered profile name in sync with the live Chronicle on tab open.
  window.refreshLootFilterCount = function(){
    try {
      var el = document.getElementById('lf-endgame-count');
      var nm = document.querySelector('.lf-b-name');
      if (!window._lfEngineReady()){
        if (el) el.textContent = 'loading…';
        window._lfCountTries = (window._lfCountTries||0) + 1;
        if (window._lfCountTries < 150) setTimeout(window.refreshLootFilterCount, 800);   // keep retrying (~2 min) until the engine lands
        return;
      }
      window._lfCountTries = 0;
      var _ebb = window._endgameFilterBases();
      // v664.1 — BOTH truths on the badge: the curated hunt set (what SI/base-hunt shows) AND the
      // engine-true socketed universe the filter actually ships (army audit: '27 bases' vs 204 lit).
      if (el) el.textContent = _ebb.names.length + ' hunt · ' + (_ebb.sockCodes || _ebb.codes).length + ' sock';
      // v665.2 (identity swarm) — the card label must follow the shell: it displayed 'KonyoEndgame0'
      // on WINDOWS while the export was correctly named 'Cousin0'.
      var _lfBrand = (window._isCousinShell ? 'Cousin' : 'KonyoEndgame');
      if (nm) nm.textContent = _lfBrand + window._chronicleMadeCount();
      try { var _cb = document.querySelector('.lf-copy-btn[onclick*="copyLootFilter(\'endgame\')"]'); if (_cb) _cb.textContent = '\ud83d\udccb Copy live ' + _lfBrand + ' filter'; } catch(e){}
    } catch(e){}
  };
  window.copyLootFilter = function(which){
    var st = document.getElementById('lf-endgame-status');
    // v591.1 \u2014 refuse to copy a half-booted filter (see _lfEngineReady): better a 3-second wait than a
    // silently-degenerate "KonyoEndgame0" profile imported into the game.
    if (!window._lfEngineReady()){
      if (st){ st.textContent='\u23f3 the page is still loading the runeword engine \u2014 try Copy again in a few seconds'; st.className='lf-status lf-no'; }
      return;
    }
    var nm = '';
    var ok = function(txt){ if(st){ st.textContent='\u2713 copied '+(nm?nm+' ':'')+'('+txt.length+' chars) \u2014 paste into the Loot Filter'; st.className='lf-status lf-ok'; } };
    var no = function(){ if(st){ st.textContent='clipboard blocked \u2014 long-press/select is off; try again'; st.className='lf-status lf-no'; } };
    var txt;
    try { var _bf = window.buildEndgameFilter(which==='cousin' ? {fresh:true} : undefined); txt = _bf.text; nm = _bf.name || ''; }
    catch(e){ var el=document.getElementById('lf-data-endgame'); txt = el?el.textContent.trim():''; }
    if(!txt){ if(st) st.textContent='data missing'; return; }
    try {
      if (navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(txt).then(function(){ok(txt);}, no); }
      else {
        var ta=document.createElement('textarea'); ta.value=txt; ta.style.position='fixed'; ta.style.opacity='0'; document.body.appendChild(ta); ta.select();
        try{ document.execCommand('copy'); ok(txt); }catch(e){ no(); } document.body.removeChild(ta);
      }
    } catch(e){ no(); }
  };

  // v543 — SMART CHRONICLE INSIGHTS. All read your live Chronicle (d2r_rwMade) + owned bases + rune stash, the
  // same way the loot filter does, recomputed on demand. No AI / no server — pure derivation from your progress.
  window._smartUnmadeNeedingBase = function(){
    var out=[];
    try{
      var made={}; try{made=JSON.parse(window.LSR.getItem('d2r_rwMade')||'{}');}catch(e){}
      var tips=(typeof RUNEWORD_TIP!=='undefined')?RUNEWORD_TIP:(window.RUNEWORD_TIP||{});
      var ownedBaseWord={};
      try{var sc=(typeof window.forgeScan==='function')?window.forgeScan():null; if(sc){[].concat(sc.now||[],sc.pipeline||[]).forEach(function(t){if(t&&t.base&&!t.baseOver)ownedBaseWord[t.rw]=1;});(sc.onestep||[]).forEach(function(t){if(t&&t.base&&t.sub!=='base'&&!t.baseOver)ownedBaseWord[t.rw]=1;});}}catch(e){}
      out=Object.keys(tips).filter(function(rw){return !made[rw] && !ownedBaseWord[rw] && !(window._rwLadderBlocked&&window._rwLadderBlocked(rw));});  // v553 — skip ladder-only words off-ladder
    }catch(e){}
    return out;
  };
  window._smartFarmPriority = function(){
    var unmade=window._smartUnmadeNeedingBase(); var meta=window._forgeMetaBase; var byBase={};
    unmade.forEach(function(rw){ var names=(typeof meta==='function')?((meta(rw)||{}).names||[]):[];
      names.forEach(function(nm){ if(!nm)return; if(/^\s*(Circlet|Coronet|Tiara|Diadem)\s*$/i.test(nm))return; (byBase[nm]=byBase[nm]||[]).push(rw); }); });
    return Object.keys(byBase).map(function(b){return {base:b, count:byBase[b].length, runewords:byBase[b]};}).sort(function(a,b){return b.count-a.count || a.base.localeCompare(b.base);});
  };
  window._smartRuneGating = function(){
    var made={}; try{made=JSON.parse(window.LSR.getItem('d2r_rwMade')||'{}');}catch(e){}
    var stash={}; try{stash=JSON.parse(window.LSR.getItem('d2r_runeStash')||'{}');}catch(e){}
    var tips=(typeof RUNEWORD_TIP!=='undefined')?RUNEWORD_TIP:(window.RUNEWORD_TIP||{});
    var demand={}, byRune={};
    Object.keys(tips).forEach(function(rw){ if(made[rw])return; if(window._rwLadderBlocked&&window._rwLadderBlocked(rw))return; var rec=(tips[rw]||{}).rec||[]; rec.forEach(function(r){ demand[r]=(demand[r]||0)+1; byRune[r]=byRune[r]||{}; byRune[r][rw]=1; }); });  // v553 — don't report short on runes only ladder words need
    return Object.keys(demand).map(function(r){var owned=stash[r]||0; return {rune:r, demand:demand[r], owned:owned, short:demand[r]-owned, words:Object.keys(byRune[r])};}).filter(function(x){return x.short>0;}).sort(function(a,b){return b.short-a.short || b.demand-a.demand;});
  };
  window._smartProgress = function(){
    var made={}; try{made=JSON.parse(window.LSR.getItem('d2r_rwMade')||'{}');}catch(e){}
    var tips=(typeof RUNEWORD_TIP!=='undefined')?RUNEWORD_TIP:(window.RUNEWORD_TIP||{});
    var total=Object.keys(tips).length; var madeN=Object.keys(tips).filter(function(n){return made[n];}).length;
    var s=(typeof window.forgeScan==='function')?window.forgeScan():{now:[],pipeline:[],onestep:[],crafts:[],farm:[],counts:{}};
    // v617 (lockdown) — ONE canonical accounting, shared with the Forge (s.counts): the audit found
    // THREE different numbers shipping under the same '⚒ Make now' label. Deferred tasks (ready, just
    // sharing a base/rune) are SHOWN, not dropped; baseOver one-steps count as base-blocked (their only
    // copy is claimed — the Farm panel below simultaneously lists their base to find); cube-reachable
    // words split out of 'need runes' (the runes exist, they just need cubing).
    var now=(s.now||[]).filter(function(t){return !t.deferred;});
    var deferredN=(s.counts&&s.counts.deferred)||0;
    var baseOnly=(s.onestep||[]).filter(function(t){return t.sub==='base'||t.baseOver;}).length;
    var runeOnly=(s.onestep||[]).filter(function(t){return t.sub==='runes'&&!t.baseOver;}).length;
    var cubeOnly=(s.onestep||[]).filter(function(t){return t.sub==='cube'&&!t.baseOver;}).length;
    var farmN=(s.farm||[]).length;
    var ladderN=0; try{ Object.keys(tips).forEach(function(n){ if(!made[n]&&window._rwLadderBlocked&&window._rwLadderBlocked(n))ladderN++; }); }catch(e){}
    var best=now.slice().sort(function(a,b){return (b.val||0)-(a.val||0);})[0];
    var fp=window._smartFarmPriority(); var nx=fp[0];
    // v617 — 'unlocks' honesty: of the words the top base serves, how many are READY the moment you
    // find it (runes in hand → onestep sub:'base') vs still rune-short (farm bucket → it only advances)?
    var nxReady=0, nxAdvance=0;
    if(nx){ try{ var _ready={}; (s.onestep||[]).forEach(function(t){ if(t.sub==='base')_ready[t.rw]=1; });
      nx.runewords.forEach(function(rw){ if(_ready[rw])nxReady++; else nxAdvance++; }); }catch(e){} }
    return {total:total, made:madeN, remaining:total-madeN, makeNow:now.length, deferred:deferredN,
      pipeline:(s.pipeline||[]).length, oneStep:(s.onestep||[]).length, farm:farmN, ladderExcluded:ladderN,
      // v656 — BASE-HUNT intel (Konyo: 'more depth for accuracy and elite bases'): the exact bases
      // worth picking up right now, elite-first, same live set the in-game loot filter shows.
      baseHunt:(function(){ try { var eb=window._endgameFilterBases(); var nm=(eb.names||[]).slice();
        nm.sort(function(a,b){ var ta=(window._baseTier&&window._baseTier(a)==='elite')?0:1, tb=(window._baseTier&&window._baseTier(b)==='elite')?0:1; return ta-tb || a.localeCompare(b); });
        // v658 — cow split (game-file qlvl): how many of the hunt bases Hell Cows can actually drop.
        var _cowY=0,_cowN=[]; nm.forEach(function(x){ var c=(typeof window._cowInfo==='function')?window._cowInfo(x):null; if(!c)return; if(c.cows)_cowY++; else _cowN.push(x+' '+c.q); });
        return { n: nm.length, top: nm.slice(0,4), elites: nm.filter(function(x){ return window._baseTier&&window._baseTier(x)==='elite'; }).length, cowY:_cowY, cowBlocked:_cowN };
      } catch(e){ return null; } })(),
      blockedByBase:baseOnly, blockedByRunes:runeOnly, cubeReachable:cubeOnly,
      bestNow:best?best.rw:null, nextUnlockBase:nx?nx.base:null, nextUnlockCount:nx?nx.count:0,
      nextUnlockReady:nxReady, nextUnlockAdvance:nxAdvance};
  };
  // v546 — how many of a rune you could END with by cascading your whole stash up the cube-up chain (reuses the
  // Runes-tab cubeUpPotential engine). Lets the Rune radar say "you can cube up to N Sur from what you hold".
  window._runeCubeUpTo = function(rune){
    try { if (typeof RUNES==='undefined' || typeof window.cubeUpPotential!=='function') return 0;
      var idx=RUNES.findIndex(function(r){return r.n===rune;}); return idx<0?0:(window.cubeUpPotential(idx)||0);
    } catch(e){ return 0; }
  };
  // v546 — jump to the Runes-tab cube-up planner, pre-selected to this rune (same Tools tab → just expand + scroll).
  window.smartJumpRuneCubeUp = function(rune){
    try {
      var idx=(typeof RUNES!=='undefined')?RUNES.findIndex(function(r){return r.n===rune;}):-1;
      var card=document.getElementById('rune-stash-card');
      if (card && card.classList.contains('collapsed') && typeof window.toggleCardCollapse==='function') window.toggleCardCollapse('rune-stash-card');
      setTimeout(function(){
        var sel=document.getElementById('rune-cubeup-target');
        if (sel && idx>=0){ sel.value=String(idx); if (typeof window.renderRuneStash==='function') window.renderRuneStash(); }
        var p=document.querySelector('#rune-stash-card .cubeup-panel'); if (p) p.scrollIntoView({block:'center',behavior:'smooth'});
      }, 130);
    } catch(e){}
  };
  // v546 — accurate, tier-based "where to farm" (NOT fabricated boss/area precision). Elite bases only roll in
  // high-level areas → point at today's lvl-85 Terror Zones; exceptional → NM/Hell mid or any 85; normal → broad.
  window._baseFarmWhere = function(base){
    var tier=(typeof window._baseTier==='function')?window._baseTier(base):'';
    if (tier==='elite') return {tag:'◆ elite', where:'drops only in <b>lvl-85</b> areas — run today’s Terror Zones (they scale to 85) or a permanent 85 (The Pit, Ancient Tunnels, Maggot Lair)'};
    if (tier==='exceptional') return {tag:'exc', where:'Nightmare/Hell mid areas, or any <b>lvl-85</b> zone'};
    return {tag:'', where:'drops broadly across Hell — or gamble it from a vendor'};
  };
  // v617 (lockdown+flagship, Konyo: "Smart Insights doesn't route anywhere… flagship it") — every
  // number ROUTES to the thing it describes, counts are the Forge's own (s.counts — the audit found
  // 3 formulas under one label), deferred/farm/ladder are named instead of vanishing, and the panel
  // wears the platform's engraved-plate language. Routing reuses forgeSetFilter + the v557 glide.
  window.smartGoForge = function(filter, word){
    try {
      if (window.switchTab) window.switchTab('forge');
      setTimeout(function(){
        try { if (filter && window.forgeSetFilter) window.forgeSetFilter(filter); } catch(e){}
        setTimeout(function(){
          var t=null;
          if (word){ t=Array.from(document.querySelectorAll('#forge-body .f-card')).find(function(c){ return (c.textContent||'').indexOf(word)>=0; }); }
          if (!t) t=document.querySelector('#forge-body .forge-sec');
          if (t) t.scrollIntoView({block:'center',behavior:'smooth'});
        }, 160);
      }, 60);
    } catch(e){}
  };
  window.renderSmartInsights = function(){
    var box=document.getElementById('smart-insights-body'); if(!box) return;
    try{
      var p=window._smartProgress(), fp=window._smartFarmPriority(), rg=window._smartRuneGating();
      var esc=function(s){ return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); };
      var pct=p.total?Math.round(p.made/p.total*100):0, H='';
      var row=function(icon,label,val,extra,route,title){
        return '<div class="si-row si-go" role="button" tabindex="0" title="'+esc(title||'open this in the Forge')+'" onclick="'+route+'"><span>'+icon+' '+label+'</span><span class="si-rhs">'+(extra||'')+'<b class="si-coin">'+val+'</b></span></div>';
      };
      H+='<div class="si-panel"><div class="si-h">📊 Progress</div>'
        +'<div class="si-bar"><div class="si-fill" style="width:'+pct+'%"></div><span class="si-barlbl">'+p.made+' / '+p.total+' · '+pct+'%</span></div>'
        +(p.ladderExcluded?'<div class="si-dim" style="margin:2px 0 4px">('+p.ladderExcluded+' ladder-only word'+(p.ladderExcluded>1?'s':'')+' excluded from the tasks below — they live on the 🪜 <b style="cursor:pointer" onclick="window.profileSwitch&&window.profileSwitch(\'ladder\')">LADDER account</b> — switch via the header pill)</div>':'')
        +row('⚒','Make now',p.makeNow,(p.deferred?' <span class="si-dim">(+'+p.deferred+' next up — share a base/rune)</span>':''),"window.smartGoForge('now')",'open the Forge → ⚒ Make now')
        +row('🔧','Pipeline',p.pipeline,'',"window.smartGoForge('pipeline')",'open the Forge → 🔧 Pipeline (Larzuk-socket, then forge)')
        +row('🟡','One step',p.oneStep,' <span class="si-dim">('+p.blockedByBase+' need a base · '+p.blockedByRunes+' need runes'+(p.cubeReachable?' · '+p.cubeReachable+' cube-up-able':'')+')</span>',"window.smartGoForge('onestep')",'open the Forge → 🟡 One step away')
        +(p.farm?row('🌾','Furthest out',p.farm,' <span class="si-dim">(need both base and runes)</span>',"window.smartGoForge('onestep')",'open the Forge — the 🌾 Furthest out list rides the One-step view'):'')
        +(p.baseHunt&&p.baseHunt.n?row('🏹','Base hunt',p.baseHunt.n,' <span class="si-dim">('+p.baseHunt.elites+' elite · top: '+p.baseHunt.top.map(function(x){return '<b data-arttip="'+x.replace(/"/g,'&quot;')+'">'+x+'</b>';}).join(' · ')+' — all lit in your in-game filter · 🐄 <b>Hell Cows</b> (alvl 81) = density king, drops <b>'+(p.baseHunt.cowY||0)+' of '+p.baseHunt.n+'</b>'+((p.baseHunt.cowBlocked&&p.baseHunt.cowBlocked.length)?' — but NEVER the qlvl-82+ elites ('+p.baseHunt.cowBlocked.slice(0,3).join(' · ')+(p.baseHunt.cowBlocked.length>3?' +'+(p.baseHunt.cowBlocked.length-3)+' more':'')+'): those = Pit / AT / lvl-85 TZs':'')+')</span>',"window.switchTab('tools')",'the exact grey/eth socketed bases worth grabbing — synced to the KonyoEndgame loot filter'):'')
        +(p.bestNow?'<div class="si-tip si-go" role="button" tabindex="0" onclick="window.smartGoForge(\'now\',\''+esc(p.bestNow)+'\')" title="jump to this exact task card">⭐ Best you can make now: <b data-arttip="'+esc(p.bestNow)+'">'+esc(p.bestNow)+'</b> →</div>':'')
        +(p.nextUnlockBase?'<div class="si-tip si-go" role="button" tabindex="0" onclick="window.openDrop&&window.openDrop(\''+esc(p.nextUnlockBase)+'\')" title="open this base\'s card">💡 Highest-leverage base to find: <b data-arttip="'+esc(p.nextUnlockBase)+'">'+esc(p.nextUnlockBase)+'</b>'
          +(p.nextUnlockReady||p.nextUnlockAdvance?' → <b>'+p.nextUnlockReady+'</b> ready on find'+(p.nextUnlockAdvance?' · advances '+p.nextUnlockAdvance+' more':''):' → unlocks '+p.nextUnlockCount)+' →</div>':'')
        +'</div>';
      H+='<div class="si-panel"><div class="si-h">🎯 Farm priority — bases by leverage</div>';
      if(!fp.length){ H+='<div class="si-dim">Nothing to farm — you own a base for every remaining runeword. 🎉</div>'; }
      else { fp.slice(0,12).forEach(function(x){ var fw=(typeof window._baseFarmWhere==='function')?window._baseFarmWhere(x.base):{tag:'',where:''};
        H+='<div class="si-fp"><span class="si-fpn si-go" role="button" tabindex="0" data-arttip="'+esc(x.base)+'" onclick="window.openDrop&&window.openDrop(\''+esc(x.base)+'\')" title="open '+esc(x.base)+'\'s base card">'+esc(x.base)+(fw.tag?' <span class="si-tier">'+esc(fw.tag)+'</span>':'')+' →</span><span class="si-fpc">'+x.count+' word'+(x.count>1?'s':'')+'</span><div class="si-fpw">'+x.runewords.slice(0,5).map(function(rw){ return '<span data-arttip="'+esc(rw)+'">'+esc(rw)+'</span>'; }).join(' · ')+(x.runewords.length>5?' …':'')+'</div>'+(fw.where?'<div class="si-fpwhere">📍 '+fw.where+'</div>':'')+'</div>'; });
        if(fp.length>12)H+='<div class="si-dim">+ '+(fp.length-12)+' more single-word bases</div>';
        H+='<div class="si-tip si-go" role="button" tabindex="0" onclick="window.switchTab&&window.switchTab(\'tz\')">🔥 Jump to <b>Terror Zones</b> for today\'s lvl-85 rotation →</div>'; }
      H+='</div>';
      H+='<div class="si-panel" style="border:none"><div class="si-h">🔑 Rune radar — what you\'re short on</div>';
      if(!rg.length){ H+='<div class="si-dim">You have every rune your remaining runewords need — just farm the bases. 🎉</div>'; }
      else { rg.slice(0,14).forEach(function(x){ var cu=(typeof window._runeCubeUpTo==='function')?window._runeCubeUpTo(x.rune):0; var cuNote=''; if(cu>x.owned){ var covers=cu>=x.demand; cuNote='<button class="si-cube'+(covers?' si-cube-full':'')+'" title="cascade your lower runes up the cube chain toward '+esc(x.rune)+'" onclick="window.smartJumpRuneCubeUp&&window.smartJumpRuneCubeUp(\''+esc(x.rune)+'\')">🧊 cube up to '+cu+(covers?' — covers it!':'')+'</button>'; } H+='<div class="si-rg"><span class="si-rgn" data-arttip="'+esc(x.rune)+'">'+esc(x.rune)+'</span><span class="si-rgs">short <b>'+x.short+'</b></span><span class="si-dim">need '+x.demand+' · have '+x.owned+'</span>'+cuNote+'</div>'; }); }
      H+='</div>';
      box.innerHTML=H;
    }catch(e){ box.innerHTML='<div class="si-dim">insights unavailable</div>'; }
  };
  // v544 — QUICK UPLOAD shortcut: one always-visible bar at the top of Tools → tap a stash → expands its card
  // (so the read result is visible) and opens the file picker straight into that section's AI intake. Same
  // intake each section already has; this just routes another easy entry point (Konyo's ask).
  window.quickIntake = function(which){
    var map={ vault:{file:'vault-intake-file', card:'mule-vault-card', render:'renderVault'},
              rune:{file:'rune-intake-file', card:'rune-stash-card', render:'renderRuneStash'},
              gem:{file:'gem-intake-file', card:'gem-stash-card', render:'renderGemStash'},
              material:{file:'material-intake-file', card:'material-stash-card', render:null} };
    var m=map[which]; if(!m) return;
    try{ var card=document.getElementById(m.card); if(card&&card.classList.contains('collapsed')){ if(window.toggleCardCollapse)window.toggleCardCollapse(m.card); if(m.render&&typeof window[m.render]==='function')window[m.render](); } }catch(e){}
    try{ var f=document.getElementById(m.file); if(f){ f.click(); } }catch(e){}
  };
  