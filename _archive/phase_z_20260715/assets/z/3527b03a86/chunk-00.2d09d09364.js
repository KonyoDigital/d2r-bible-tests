
// ══════════════════════════════════════════════════════════════════════════════
// v635 — LADDER PROFILE STORAGE ROUTER (Konyo: "a smooth polished toggle that ascends perfectly
// from non-ladder to ladder — make sure nothing bleeds"). Two accounts, one engine:
//   · main   → the original unprefixed d2r_* keys, byte-for-byte untouched (zero migration)
//   · ladder → the same keys under the 'L·' prefix — a genuinely fresh second account
// D2R_PROFILE is read ONCE per page load; switching profiles is ALWAYS a full reload
// (window.profileSwitch) so no half-pointed in-memory state can ever mix the two.
// Only ACCOUNT state forks (vault, tallies, chronicle, forge progress, intake ledgers);
// site prefs, caches and reference data stay shared. Defined in the first script block so
// every later block routes through it.
// ══════════════════════════════════════════════════════════════════════════════
// v663 — MASTER MACHINE SWITCH (Konyo: "a master switch between the two — WINDOWS/MAC").
// MAC = Konyo's world, byte-identical to everything before (bare keys + the L· ladder fork).
// WINDOWS = the cousin's OWN isolated world: EVERY d2r_* key routes to the 'W·' prefix — chronicle
// included (unlike ladder's shared grail, the cousin shares NOTHING), and every owner seed floor
// (_RWC_SEED · _GRAIL_SEED · rwVerify fails) is suppressed so he genuinely starts from zero.
// Same doctrine as v635: the machine is read ONCE per load; switching is ALWAYS a full reload.
window.D2R_MACHINE = (function(){ try { return window.localStorage.getItem('d2r_activeMachine')==='windows' ? 'windows' : 'mac'; } catch(e){ return 'mac'; } })();
window._isCousinShell = (window.D2R_MACHINE==='windows');
// v665.1 — WINDOWS has its own Main/Ladder pair (Konyo: "the windows need to also have the toggle").
// Each machine remembers its own active account via its own pointer key.
window._PROFILE_PTR = (window.D2R_MACHINE==='windows') ? 'd2r_activeProfileWin' : 'd2r_activeProfile';
window.D2R_PROFILE = (function(){ try { return window.localStorage.getItem(window._PROFILE_PTR)==='ladder' ? 'ladder' : 'main'; } catch(e){ return 'main'; } })();
window._LP_FORKED = new Set(["d2r_owned", "d2r_copies", "d2r_unknownReads", "d2r_magicFinds", "d2r_ethereal", "d2r_superiorBases", "d2r_multiKeep", "d2r_wishlist", "d2r_runeStash", "d2r_gemStash", "d2r_craftStash", "d2r_craftBaseStash", "d2r_materialStash", "d2r_statues", "d2r_setPieces", "d2r_rwBaseUsed", "d2r_rwVerify", "d2r_muleAssign", "d2r_muleRoster", "d2r_forgeStep", "d2r_forgeSkip", "d2r_forgeDone", "d2r_intakeLog", "d2r_intakeSeen", "d2r_grailImportReport", "d2r_createNow", "d2r_createNowDate", "d2r_createNowAi", "d2r_createNowAiV", "d2r_createNowAiDate", "d2r_lastTopScan", "d2r_aicDraft", "d2r_mf", "d2r_players", "d2r_foundLog", "d2r_stashMeta", "d2r_chroniclePin", "d2r_sessionLog"]);  

// v665 — the WINDOWS fork set (Konyo: "make it the same and identical… structured the same").
// v663 forked EVERY d2r_* key, which also forked UI PREFERENCES (active tab, dock, boss sorts,
// grail-wall state…) — so the cousin shell rendered structurally different. Doctrine restored to
// v635's: only ACCOUNT STATE forks; prefs/caches stay shared so both machines LOOK identical.
// WINDOWS forks the ladder set PLUS the chronicle family (unlike ladder, the cousin shares no grail).
window._WP_FORKED = new Set(Array.from(window._LP_FORKED).concat(['d2r_rwMade','d2r_rwUnmade','d2r_rwProfile','d2r_grailUnfound','d2r_ladderMode','d2r_unknownReads']));
window.LSR = (function(){
  var RAW = window.localStorage;
  function key(k){
    // v665.1 — the full 2×2: MAC main = bare · MAC ladder = L· · WINDOWS main = W· · WINDOWS ladder = WL·.
    // On WINDOWS the chronicle family (in _WP_FORKED but NOT _LP_FORKED) falls through to W· on BOTH
    // cousin profiles — the cousin's main and ladder share the COUSIN's grail, the exact v638 doctrine
    // Konyo's own two accounts follow. UI prefs match no fork set → bare = identical structure everywhere.
    if (window.D2R_MACHINE==='windows'){
      if (window.D2R_PROFILE==='ladder' && window._LP_FORKED.has(k)) return 'WL·'+k;
      if (window._WP_FORKED.has(k)) return 'W·'+k;
      return k;
    }
    return (window.D2R_PROFILE==='ladder' && window._LP_FORKED.has(k)) ? 'L·'+k : k;
  }
  return {
    getItem:    function(k){ return RAW.getItem(key(k)); },
    setItem:    function(k,v){ return RAW.setItem(key(k), v); },
    removeItem: function(k){ return RAW.removeItem(key(k)); },
    raw: RAW, key: key
  };
})();
// v680 — TOOLS is home (Konyo: 'hard refresh should put me by default at tools'): a BARE tab hash
// (the last-visited tab riding the URL) is normalized at PARSE time, before the v39 routers
// register. True deep-links keep working: a hash WITH a subpath (#bosses/baal, #item/…) is intent,
// not residue, and routes normally.
try { var _h680 = window.location.hash || ''; if (_h680 && _h680 !== '#tools' && _h680.indexOf('/') < 0) window.history.replaceState(null, '', '#tools'); } catch(e){ try { window.location.hash = 'tools'; } catch(e2){} }
window._grailStamp = function(){ try { var d=new Date(); return d.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})+' \u00b7 '+d.toTimeString().slice(0,5); } catch(e){ return ''+Date.now(); } };
window.profileSwitch = function(p){
  p = (p==='ladder') ? 'ladder' : 'main';
  if (p === window.D2R_PROFILE) return;   // v636 — clicking the already-active account is a no-op, not a reload
  try { window.localStorage.setItem(window._PROFILE_PTR, p); } catch(e){}   // v665.1 — each machine keeps its own pointer
  location.reload();
};
window.machineSwitch = function(m){
  m = (m==='windows') ? 'windows' : 'mac';
  if (m === window.D2R_MACHINE) return;
  try { window.localStorage.setItem('d2r_activeMachine', m); } catch(e){}
  location.reload();
};
// v636 — PROFILE-SCOPED WIPE (the closure swarm's #1 critical: the footer reset ran raw
// localStorage.clear(), nuking BOTH accounts + the profile pointer from either side).
// Wipes ONLY the active account: ladder = its 'L·' keys; main = the bare keys (never 'L·',
// never d2r_activeProfile). The other account stays byte-identical.
window.LSR.wipeProfile = function(){
  try {
    var RAW = window.localStorage, kill = [];
    for (var i = 0; i < RAW.length; i++){
      var k = RAW.key(i); if (k == null || k === 'd2r_activeProfile') continue;
      if (k === 'd2r_activeMachine' || k === 'd2r_activeProfileWin') continue;   // v663/v665.1 — the pointers survive every wipe
      if (window.D2R_MACHINE === 'windows'){
        if (window.D2R_PROFILE === 'ladder'){ if (k.indexOf('WL·') === 0) kill.push(k); }          // cousin-ladder wipe = WL· only
        else { if (k.indexOf('W·') === 0 && k.indexOf('WL·') !== 0) kill.push(k); }                // cousin-main wipe = W· only, never WL·
      }
      else if (window.D2R_PROFILE === 'ladder'){ if (k.indexOf('L·') === 0 && k.indexOf('WL·') !== 0) kill.push(k); }
      else { if (k.indexOf('L·') !== 0 && k.indexOf('W·') !== 0 && k.indexOf('WL·') !== 0) kill.push(k); }   // MAC main wipe never reaches the cousin's worlds
    }
    kill.forEach(function(k){ RAW.removeItem(k); });
    return kill.length;
  } catch(e){ return 0; }
};
// First ladder boot: pre-seed the intake SEEN ledger from main — every screenshot already scanned
// belongs to the non-ladder account; without this, the first ladder folder-scan would re-intake
// the entire history as ladder loot (the ultimate bleed).
// v650 — the LADDER account's rwVerify may still hold the v635-window copy of the NON-ladder
// fail seed (Mania/Hysteria/Hustle 'did-not-form'). Konyo's ladder Hysteria screenshot DISPROVES
// it there: ladder chars form these words. Wipe exactly that legacy seed from L· once.
try {
  var _lv = window.localStorage.getItem('L·d2r_rwVerify');
  if (_lv){ var _pv = JSON.parse(_lv)||{};
    var _keys = Object.keys(_pv);
    if (_keys.length && _keys.every(function(k){ return ['Mania','Hysteria','Hustle'].indexOf(k)>=0 && _pv[k]==='fail'; }))
      window.localStorage.setItem('L·d2r_rwVerify','{}');
  }
} catch(e){}
// v638 — one-time reconcile: v635-v637 briefly forked the chronicle; any forge recorded under the
// orphaned L·d2r_rwMade merges INTO the shared ledger (union-only — nothing is ever un-made), then
// the L· chronicle copies are removed.
try {
  var _oL = window.localStorage.getItem('L·d2r_rwMade');
  if (_oL){
    var _lm = JSON.parse(_oL)||{}, _bm = JSON.parse(window.localStorage.getItem('d2r_rwMade')||'{}')||{};
    Object.keys(_lm).forEach(function(k){ if(!_bm[k]) _bm[k]=_lm[k]; });
    window.localStorage.setItem('d2r_rwMade', JSON.stringify(_bm));
    window.localStorage.removeItem('L·d2r_rwMade');
    window.localStorage.removeItem('L·d2r_rwUnmade');
    window.localStorage.removeItem('L·d2r_rwProfile');
  }
} catch(e){}
try {
  if (window.D2R_PROFILE==='ladder'){
    // v684 — machine-aware: WINDOWS-ladder seeds WL· from the COUSIN's own W· ledger (it was hardcoded
    // to the MAC keys, so the first cousin-ladder folder scan would re-intake the entire screenshot
    // history — and worse, the cousin re-created MAC's L· key, a cross-machine write).
    var _seenKey = window._isCousinShell ? 'WL·d2r_intakeSeen' : 'L·d2r_intakeSeen';
    var _seenSrc = window._isCousinShell ? 'W·d2r_intakeSeen'  : 'd2r_intakeSeen';   // v636 — RAW read of the owning MAIN's key (a routed read resolves to the very key the guard proved empty)
    if (!window.localStorage.getItem(_seenKey)){
      var _mSeen = window.localStorage.getItem(_seenSrc);
      if (_mSeen) window.localStorage.setItem(_seenKey, _mSeen);
    }
  }
} catch(e){}
