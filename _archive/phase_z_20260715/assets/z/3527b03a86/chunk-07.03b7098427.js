
(function() {
  'use strict';
  // --- v42: Build command list from the bible's live data sources ---
  // --- v42 polish: common D2R runewords (now a shared top-level global, see RUNEWORDS) ---
  const V42_RUNEWORDS = (typeof RUNEWORDS !== 'undefined') ? RUNEWORDS : [];

  // === v61 sticky global search — reuses v42BuildCommands() index + its actions ===
  (function(){
    function gsInit(){
      var inp = document.getElementById('gsearch-input');
      var box = document.getElementById('gsearch-results');
      if (!inp || !box) return;
      var ranked = [], active = -1, index = null;
      function getIndex(){ if (!index){ try { index = (typeof v42BuildCommands === 'function') ? v42BuildCommands() : []; } catch(e){ index = []; } } return index; }
      function esc(t){ return String(t==null?'':t).replace(/[&<>"]/g, function(m){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]; }); }
      // v133 - token AND-match for natural multi-word/intent queries ("recipe for
      // renewing my sunder charm"): drop stopwords, loose-stem each token, require
      // ALL to appear in label/keywords. Single-token + exact/prefix paths unchanged
      // so existing precise matches still outrank fuzzy intent hits.
      var GS_STOP={the:1,for:1,my:1,a:1,an:1,of:1,to:1,how:1,do:1,i:1,is:1,it:1,and:1,with:1,can:1,me:1,you:1,what:1,whats:1,'on':1,in:1};
      function score(c, q){
        var l=(c.label||'').toLowerCase(), k=(c.keywords||'').toLowerCase(), hay=l+' '+k;
        if (l===q) return 100;
        if (l.indexOf(q)===0) return 80;
        if (l.indexOf(q)>0) return 60;
        if (k.indexOf(q)>=0) return 40;
        var toks=q.split(/\s+/).filter(function(t){ return t && !GS_STOP[t]; });
        if (toks.length>=2){
          var inLabel=0;
          for (var i=0;i<toks.length;i++){
            var t=toks[i], pre=t.slice(0, Math.max(4, t.length-3));
            if (hay.indexOf(t)<0 && hay.indexOf(pre)<0) return -1;
            if (l.indexOf(t)>=0 || l.indexOf(pre)>=0) inLabel++;
          }
          return 30 + inLabel*4;
        }
        return -1;
      }
      function close(){ box.hidden=true; box.innerHTML=''; ranked=[]; active=-1; }
      function paint(){ var els=box.querySelectorAll('.gsearch-item'); for (var i=0;i<els.length;i++){ if (i===active) els[i].classList.add('gsearch-active'); else els[i].classList.remove('gsearch-active'); } var a=box.querySelector('.gsearch-active'); if (a) a.scrollIntoView({block:'nearest'}); }
      function render(q){
        q=(q||'').trim().toLowerCase();
        if (!q){ close(); return; }
        var all=getIndex(), scored=[];
        for (var i=0;i<all.length;i++){ var sc=score(all[i],q); if (sc>=0) scored.push({c:all[i],s:sc}); }
        scored.sort(function(a,b){ return b.s-a.s || (a.c.label||'').length-(b.c.label||'').length; });
        ranked=scored.slice(0,10);
        if (!ranked.length){ box.innerHTML='<div class="gsearch-empty">No boss, zone, act, or item matches "'+esc(q)+'"</div>'; box.hidden=false; active=-1; return; }
        var html='';
        for (var j=0;j<ranked.length;j++){ var c=ranked[j].c;
          // v146 — prefer the verified in-game art logo over the generic tier emoji.
          // artUrl() returns null for art-less labels (tabs/bosses/MF), so those keep
          // their emoji; any label matching a D2IO_ART key shows its synced logo.
          var _ic = (c.icon||'\u2022');
          var _artName = (typeof window.artUrl==='function' && window.artUrl(c.label)) ? c.label
            : ((typeof window._setRepArtName==='function') ? window._setRepArtName(c.label) : null);
          var icHtml = (_artName && typeof window.artOr==='function')
            ? window.artOr(_artName, '<span class="gsearch-ic-emoji">'+_ic+'</span>', 'sm')
            : _ic;
          html += '<div class="gsearch-item" data-gi="'+j+'"><span class="gsearch-ic">'+icHtml+'</span><span class="gsearch-lab"'+(typeof _qStyle==='function'?_qStyle(c.label):'')+'>'+esc(c.label)+(c.sub?' <span class="gsearch-sub">'+esc(c.sub)+'</span>':'')+'</span><span class="gsearch-cat">'+esc(c.cat||'')+'</span></div>';
        }
        box.innerHTML=html; active=0; box.hidden=false; paint();
      }
      function run(i){ if (ranked[i]){ try { ranked[i].c.action(); } catch(e){} inp.value=''; close(); inp.blur(); } }
      inp.addEventListener('input', function(e){ render(e.target.value); });
      inp.addEventListener('keydown', function(e){
        var n=ranked.length;
        if (e.key==='ArrowDown'){ e.preventDefault(); active=Math.min(active+1, n-1); paint(); }
        else if (e.key==='ArrowUp'){ e.preventDefault(); active=Math.max(active-1, 0); paint(); }
        else if (e.key==='Enter'){ e.preventDefault(); run(active>=0?active:0); }
        else if (e.key==='Escape'){ if (box.hidden){ inp.value=''; } else { close(); } inp.blur(); }
      });
      box.addEventListener('mousedown', function(e){ var it=e.target.closest('.gsearch-item'); if (it){ e.preventDefault(); run(parseInt(it.getAttribute('data-gi'),10)); } });
      document.addEventListener('click', function(e){ if (!e.target.closest('.gsearch-wrap')) close(); });
    }
    if (document.readyState==='loading') document.addEventListener('DOMContentLoaded', gsInit); else gsInit();
  })();
  function v42BuildCommands() {
    const cmds = [];

    // Tabs — derived LIVE from the DOM tab bar (skipping the 'main' home) so a newly
    // added tab is auto-searchable; no hardcoded list to drift out of sync. The v83
    // sync-audit enforces "every nav tab is globally searchable". Per-id extra
    // keywords aid discoverability for the content-dense tabs.
    const TAB_KW = {
      ancients: 'uber tristram diablo clone summoner cow level colossal ancients pandemonium nights of terror torch annihilus',
      endgame: 'road hellfire torch colossal ancients herald sunder pinnacle relics',
      tools: 'rune stash cube planner material uber planner item set tracker gadgets',
    };
    [...document.querySelectorAll('.tabs .tab[data-tab]')]
      .filter(btn => btn.dataset.tab !== 'main')
      .forEach((btn, i) => {
        const id = btn.dataset.tab;
        const parts = (btn.textContent || '').trim().split(/\s+/);
        // v551 — the HD-art tab rewrite (applyTabIcons) strips the emoji from textContent and stashes the real
        // label/emoji in dataset. Prefer those so the palette label stays "Switch to Reference" (not "Switch to Ref").
        const icon = btn.dataset.emoji || parts[0] || '•';
        const rawLabel = btn.dataset.label || (parts.slice(1).join(' ') || id);
        const label = rawLabel.replace(/\b\w/g, c => c.toUpperCase());
        cmds.push({
          icon,
          label: `Switch to ${label}`,
          cat: 'tab',
          hint: ({bosses:'1',calc:'2',tz:'3',runes:'4',rotw:'5',ancients:'6',endgame:'7',binds:'8',ref:'9',tools:'0'})[id] || '',
          keywords: `tab ${label.toLowerCase()} ${id} ${TAB_KW[id] || ''}`,
          action: () => { if (typeof window.switchTab === 'function') window.switchTab(id); }
        });
      });

    // Bosses (11)
    const BOSSES_DATA = (typeof BOSSES !== 'undefined') ? BOSSES : [];
    BOSSES_DATA.forEach(b => cmds.push({
      icon: b.emoji || '👹',
      label: `${b.name}`,
      sub: b.subtitle || '',
      cat: 'boss',
      hint: b.tierTag || '',
      keywords: `boss ${b.name.toLowerCase()} ${b.id} ${(b.subtitle||'').toLowerCase()} ${(b.tierTag||'').toLowerCase()}`,
      action: () => {
        if (typeof window.openBossDetail === 'function') window.openBossDetail(b.id);
      }
    }));

    // Items (unique names from ITEMS - dedup; we want one entry per item name regardless of which boss list it's in)
    const seenItems = new Set();
    const ITEMS_DATA = (typeof ITEMS !== 'undefined') ? ITEMS : [];
    ITEMS_DATA.forEach(it => {
      const name = it.n || it.name;
      if (!name || seenItems.has(name)) return;
      seenItems.add(name);
      const icon = it.tier === 'grail' ? '⭐' :
                   it.tier === 'uber' ? '💎' :
                   it.tier === 'high' ? '✨' :
                   it.tier === 'set' ? '🟢' : '•';
      cmds.push({
        icon,
        label: name,
        sub: it.tier ? `tier: ${it.tier}` : '',
        cat: 'item',
        hint: it.tc ? `TC${it.tc}` : '',
        keywords: `item ${name.toLowerCase()} ${(it.tier||'')}`,
        action: () => {
          // v42 UX (CC find): navigateToItem is the canonical path that updates
          // module-scoped selectedItem (not window.selectedItem — those are different)
          // AND syncs the active-item-bar via setActiveItem.
          try {
            if (typeof window.navigateToItem === 'function') {
              window.navigateToItem(name);
            } else {
              // Fallback for very-early-call edge cases
              if (typeof setActiveItem === 'function') setActiveItem(name);
              if (typeof window.switchTab === 'function') window.switchTab('calc');
              if (typeof renderDetail === 'function') renderDetail();
            }
          } catch(e) { console.warn('v42 palette item select error:', e); }
        }
      });
    });

    // Runewords (v42 polish — not in ITEMS data)
    V42_RUNEWORDS.forEach(rw => cmds.push({
      icon: '🔮',
      label: rw.n + ((typeof _rwIsLadderOnly==='function' && _rwIsLadderOnly(rw.n)) ? ' 🪜' : ''),
      sub: `${rw.runes} · ${rw.base}` + ((typeof _rwIsLadderOnly==='function' && _rwIsLadderOnly(rw.n)) ? ' · ladder-only' : ''),
      cat: 'runeword',
      hint: (typeof _rwIsLadderOnly==='function' && _rwIsLadderOnly(rw.n)) ? '🪜 RW' : 'RW',
      keywords: `runeword rw ${rw.n.toLowerCase()} ${rw.runes.toLowerCase()} ${rw.base.toLowerCase()} ${(rw.notes||'').toLowerCase()}`,
      action: () => {
        // v140 — route to the verified runeword ID card (same openDrop format as
        // every other entity). Falls back to the legacy toast for any runeword that
        // isn't in the RUNEWORD_TIP registry (e.g. the Death's Web pseudo-entry).
        if (typeof window.openDrop === 'function' && typeof window.findRuneword === 'function' && window.findRuneword(rw.n)) {
          window.openDrop(rw.n);
          return;
        }
        // Switch to runes tab — most relevant context for runewords
        if (typeof window.switchTab === 'function') window.switchTab('runes');
        // Briefly highlight a notice or scroll — for now just switch tabs
        setTimeout(() => {
          // Show a tiny inline note about which runeword
          try {
            const existing = document.getElementById('v42-rw-toast');
            if (existing) existing.remove();
            const t = document.createElement('div');
            t.id = 'v42-rw-toast';
            t.style.cssText = 'position:fixed;bottom:24px;right:24px;background:#1a1208;border:1px solid var(--gold-bright,#f0c060);color:#f0c060;padding:12px 18px;border-radius:6px;font-family:var(--mono,monospace);font-size:12px;box-shadow:0 6px 20px rgba(0,0,0,.7);z-index:9998;max-width:340px;line-height:1.5';
            t.innerHTML = `<div style="font-weight:700;margin-bottom:4px">${rw.n}</div><div style="opacity:.85">${rw.runes}</div><div style="opacity:.75;margin-top:4px">${rw.base}</div><div style="opacity:.65;margin-top:4px;font-style:italic">${rw.notes||''}</div>`;
            document.body.appendChild(t);
            setTimeout(() => t.remove(), 6000);
          } catch(e) {}
        }, 150);
      }
    }));

    // MF Presets (6)
    [
      {v:250, label:'MF 250%'},
      {v:400, label:'MF 400%'},
      {v:553, label:'MF 553% (Shako)'},
      {v:699, label:'MF 699% (MF swap)'},
      {v:800, label:'MF 800%'},
      {v:1000, label:'MF 1000%'},
    ].forEach(p => cmds.push({
      icon: '🎯',
      label: `Set ${p.label}`,
      cat: 'mf',
      hint: `${p.v}`,
      keywords: `mf magic find ${p.v} preset`,
      action: () => { if (typeof setMFPreset === 'function') setMFPreset(p.v); }
    }));

    // Charm affixes (v449) — the magic-charm reference cards (FHR / resist / MF / life /
    // FRW small charms + class skillers) live in EXTRA_ITEMS and route via openDrop, but
    // EXTRA_ITEMS was never folded into this index, so "FHR charm" / "faster hit recovery"
    // found nothing. Index the charm cards here, keyed by what they ROLL: fold each card's
    // affixes + common shorthand (fhr/mf/frw/res/skiller) into keywords so a roll-name query
    // surfaces the right card. score() matches label+keywords. (openDrop already handles them.)
    try {
      const EI = (typeof window.EXTRA_ITEMS !== 'undefined' && window.EXTRA_ITEMS)
        ? window.EXTRA_ITEMS : (typeof EXTRA_ITEMS !== 'undefined' ? EXTRA_ITEMS : {});
      const AFFIX_KW = {
        'faster hit recovery': ' fhr faster hit recovery breakpoint',
        'faster run': ' frw faster run walk run/walk',
        'better chance of getting magic items': ' mf magic find better chance',
        'all resistances': ' res resist resistance all-res all res',
        'resist': ' res resist resistance',
        'to life': ' life vita hp',
        'to mana': ' mana',
        'attack rating': ' ar attack rating',
        'skill': ' skiller skill tab +1 skills',
        'maximum damage': ' max damage'
      };
      Object.keys(EI).forEach(nm => {
        const e = EI[nm]; if (!e) return;
        if (!/charm/.test(String(e.base || '').toLowerCase())) return;
        if (seenItems.has(nm)) return; seenItems.add(nm);
        const stats = Array.isArray(e.stats) ? e.stats.join(' ') : '';
        const hay = (nm + ' ' + stats + ' ' + (e.desc || e.note || '')).toLowerCase();
        let extra = '';
        Object.keys(AFFIX_KW).forEach(p => { if (hay.indexOf(p) >= 0) extra += AFFIX_KW[p]; });
        cmds.push({
          icon: '🔹',
          label: nm,
          sub: e.val ? String(e.val) : 'magic charm',
          cat: 'charm',
          keywords: 'charm small grand large charm affix roll keeper ' + hay + extra,
          action: () => { if (typeof window.openDrop === 'function') window.openDrop(nm); }
        });
      });
      // FCR clarifier — charms genuinely cannot roll Faster Cast Rate (a common mis-search);
      // point it at where FCR actually lives so the query isn't a dead end.
      cmds.push({
        icon: 'ℹ️',
        label: 'Faster Cast Rate (FCR) — not a charm affix',
        sub: "charms can't roll FCR — it's on amulets / rings / jewels",
        cat: 'charm',
        keywords: 'fcr faster cast rate charm small charm grand charm not available where amulet ring jewel',
        action: () => { if (typeof window.openDrop === 'function') window.openDrop('Godly Caster Amulet (rare)'); }
      });
    } catch(e){}

    // Actions
    cmds.push({
      icon: '⌨️',
      label: 'Show keyboard shortcuts',
      cat: 'action',
      hint: '?',
      keywords: 'help keyboard shortcuts kbd',
      action: () => { if (typeof toggleKbdHelp === 'function') toggleKbdHelp(); }
    });
    cmds.push({
      icon: '🔄',
      label: 'Refresh routine status',
      cat: 'action',
      keywords: 'refresh routine status reload',
      action: () => {
        const btn = document.getElementById('routine-refresh-btn');
        if (btn) btn.click();
        else if (typeof window.fetchRoutineStatus === 'function') window.fetchRoutineStatus();
      }
    });
    cmds.push({
      icon: '🔥',
      label: 'Toggle TZ rotation countdown',
      cat: 'action',
      keywords: 'tz terror zone countdown timer toggle',
      action: () => { if (typeof window._v42_toggleTZCountdown === 'function') window._v42_toggleTZCountdown(); }
    });
    cmds.push({
      icon: '🌟',
      label: 'Toggle routine bar visibility',
      cat: 'action',
      keywords: 'routine bar toggle hide show',
      action: () => {
        const bar = document.getElementById('routine-status-bar');
        if (bar) {
          const hidden = bar.style.display === 'none';
          bar.style.display = hidden ? 'block' : 'none';
          try { localStorage.setItem('routineBarVisible', hidden ? '1' : '0'); } catch(e){}
        }
      }
    });

    // v288: the 4 crafts → their ID cards, + the Crafted Items Workshop tool opener.
    const CRAFT_DATA = (typeof CRAFTS !== 'undefined') ? CRAFTS : [];
    CRAFT_DATA.forEach((c) => cmds.push({
      icon: '🔨',
      label: c.key + ' Craft',
      sub: c.gem + ' · ' + c.tell,
      cat: 'craft',
      hint: '9 slots',
      keywords: 'craft crafted item ' + c.key.toLowerCase() + ' ' + c.gem.toLowerCase() + ' ' + c.gemType.toLowerCase() + ' perfect gem rune jewel rare ' + c.best.join(' ').toLowerCase() + ' caster blood safety hit power fcr leech damage reduced frost nova',
      action: () => { if (window.openDrop) window.openDrop(c.key); }
    }));
    cmds.push({
      icon: '🔨',
      label: 'Crafted Items Workshop',
      sub: 'Tools · what\'s needed to craft + cubeable now',
      cat: 'tool',
      keywords: 'craft crafted items workshop tool planner recipe caster blood safety hit power perfect gem rune cubeable what do i need',
      action: () => { if (window.openCraftWorkshop) window.openCraftWorkshop(); }
    });

    // v298: reference items (owned + carded, outside the 312-item grail)
    Object.keys(typeof EXTRA_ITEMS !== 'undefined' ? EXTRA_ITEMS : {}).forEach((n) => {
      const rar = EXTRA_ITEMS[n].rarity || 'rare';
      cmds.push({
        icon: rar === 'unique' ? '⚔️' : rar === 'rare' ? '🟡' : rar === 'magic' ? '🔵' : '🟠',
        label: n,
        sub: rar.charAt(0).toUpperCase() + rar.slice(1) + ' · reference card',
        cat: 'item',
        keywords: rar + ' item reference ' + n.toLowerCase() + ' ' + (EXTRA_ITEMS[n].base || '').toLowerCase(),
        action: () => { if (window.openDrop) window.openDrop(n); }
      });
    });

    // --- v427 search index: ALL 498 game-data BASE ITEMS (BASE_CLASS) — every white base is now searchable
    // + clickable, routing to its base card (class · max sockets · runewords it enables). Skips names already
    // indexed above (grail uniques/sets, off-grail) so there's no duplicate row. (Konyo: "search all 1200+
    // items by name… I don't see them all rendering.") ---
    try {
      const _seenLabels = new Set(cmds.map((c) => c.label));
      const BC = (typeof BASE_CLASS !== 'undefined') ? BASE_CLASS : {};
      Object.keys(BC).forEach((bn) => {
        if (_seenLabels.has(bn)) return;   // already an item/unique/set row — don't double-list
        const cls = (BC[bn] || [])[0] || 'base';
        const mx = (typeof _socketMaxFor === 'function') ? _socketMaxFor(bn) : null;
        cmds.push({
          icon: '🔩',
          label: bn,
          sub: cls.replace(/\b\w/g, (c) => c.toUpperCase()) + ' base' + (mx != null ? ' · max ' + mx + 'os' : ''),
          cat: 'base',
          keywords: 'base item white grey socket runeword craft ' + bn.toLowerCase() + ' ' + (BC[bn] || []).join(' ').toLowerCase(),
          action: () => { if (window.openDrop) window.openDrop(bn); }
        });
      });
    } catch (e) {}

    // --- v61 search index: Terror Zones + Super-Uniques (acts/zones/gold-names jumpable) ---
    const TZ_DATA = (typeof TZ_ZONES !== 'undefined') ? TZ_ZONES : [];
    TZ_DATA.forEach((z, zi) => cmds.push({
      icon: z.emoji || '🔥',
      label: z.name,
      sub: z.act || '',
      cat: 'zone',
      hint: z.tier ? z.tier + '-tier' : '',
      keywords: 'zone area terror tz ' + (z.name||'').toLowerCase() + ' ' + (z.act||'').toLowerCase() + ' ' + (z.unique||'').toLowerCase() + ' ' + ((z.tags||[]).join(' ')),
      action: () => { if (window.switchTab) window.switchTab('tz'); setTimeout(() => { if (window.jumpToTzZone) window.jumpToTzZone(zi); }, 90); }
    }));
    // v66: permanent lvl-85 alert zones (The Pit) — searchable AS a zone, routing to the TZ
    // cross-link card. Closes the gap where a TZ-alerted zone could only be found as a boss.
    const CL_DATA = (typeof TZ_CROSSLINKS !== 'undefined') ? TZ_CROSSLINKS : [];
    CL_DATA.forEach((cl) => {
      const b = (typeof BOSSES !== 'undefined') ? BOSSES.find((x) => x.id === cl.bossId) : null;
      if (!b) return;
      cmds.push({
        icon: b.emoji || '🔥',
        label: b.name,
        sub: (b.subtitle || '') + ' · terror zone',
        cat: 'zone',
        hint: b.tierTag || '',
        keywords: 'zone area terror tz ' + (b.name||'').toLowerCase() + ' ' + (b.id||'').toLowerCase() + ' ' + (b.loc||'').toLowerCase() + ' ' + (cl.act||'').toLowerCase(),
        action: () => { if (window.switchTab) window.switchTab('tz'); setTimeout(() => {
          const card = document.querySelector('.tz-crosslink-card[data-crosslink-boss-id="' + b.id + '"]');
          if (card) card.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 110); }
      });
    });
    const SU_DATA = (typeof SUPER_UNIQUES !== 'undefined') ? SUPER_UNIQUES : [];
    SU_DATA.forEach((su, si) => cmds.push({
      icon: su.emoji || '⚡',
      label: su.name,
      sub: su.act || '',
      cat: 'super-unique',
      hint: su.mlvl ? 'mlvl ' + su.mlvl : '',
      keywords: 'super unique superunique gold name boss ' + (su.name||'').toLowerCase() + ' ' + (su.act||'').toLowerCase() + ' ' + (su.role||'').toLowerCase() + ' ' + (su.tzMatch||'').toLowerCase(),
      action: () => { if (window.switchTab) window.switchTab('tz'); setTimeout(() => {
        const d = document.getElementById('su-detail-' + si);
        if (d && d.hasAttribute('hidden') && window.toggleSuperUnique) window.toggleSuperUnique(si);
        const card = document.querySelector('.su-card[data-su-idx="' + si + '"]');
        if (card) card.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 110); }
    }));
    // Herald of Terror dedicated ID card (RotW tab)
    cmds.push({
      icon: '👹',
      label: 'Herald of Terror',
      sub: 'Hell TZ Sunder hunter',
      cat: 'rotw',
      hint: 'sunder charms',
      keywords: 'herald terror sunder charm immunity break latent renewed worldstone shard rotw bone break black cleft crack heavens cold rupture flame rift rotting fissure',
      action: () => { if (window.openHeraldCard) window.openHeraldCard(); }
    });

    // RotW & event materials — every SPECIAL_DROPS item becomes searchable and
    // routes to its EXISTING material ID card via openDrop (sunders, essences,
    // worldstone shards, colossal statues/jewels, pandemonium keys, uber organs/
    // charms). No new data — pure search-wiring so each is findable like an item.
    const SD = (typeof SPECIAL_DROPS !== 'undefined') ? SPECIAL_DROPS : {};
    const SD_META = {
      sunder:          {icon:'💠', sub:'Sunder Charm · breaks an immunity',      kw:'sunder charm immunity break latent renewed herald grand charm'},
      essence:         {icon:'🩸', sub:'Essence · cube → Token of Absolution',    kw:'essence token absolution respec reset hell act boss'},
      token:           {icon:'🎟️', sub:'Token of Absolution · cube 4 essences → respec', kw:'token absolution respec reset skills stats essence craft full'},
      worldstoneShard: {icon:'💠', sub:'Worldstone Shard · upgrades a Sunder',    kw:'worldstone shard renewed sunder upgrade tz hell western eastern southern northern deep'},
      colossalStatue:  {icon:'👑', sub:'Colossal Statue · summon ingredient',     kw:'colossal ancient statue summit pinnacle terror cube talic korlic madawc'},
      colossalJewel:   {icon:'💎', sub:'Colossal Jewel · endgame BiS',            kw:'colossal ancient jewel facet pinnacle reward bis'},
      key:             {icon:'🗝️', sub:'Pandemonium Key · opens an uber portal',  kw:'key pandemonium uber terror hate destruction red portal'},
      organ:           {icon:'🫀', sub:'Uber Organ · cube → Hellfire Torch',      kw:'organ uber horn brain eye torch'},
      uberCharm:       {icon:'🔥', sub:'Uber Charm · event grail',                kw:'torch annihilus uber charm grail'},
    };
    const seenMat = new Set();
    Object.keys(SD).forEach(catKey => {
      const cat = SD[catKey]; if (!cat) return;
      const meta = SD_META[catKey] || {icon: cat.icon || '•', sub: cat.label || '', kw: ''};
      (cat.items || []).forEach(it => {
        const nm = it.n; if (!nm || seenMat.has(nm)) return; seenMat.add(nm);
        cmds.push({
          icon: meta.icon,
          label: nm,
          sub: meta.sub,
          cat: 'material',
          hint: it.rate || '',
          keywords: 'material ' + nm.toLowerCase() + ' ' + (cat.label || '').toLowerCase() + ' ' + meta.kw,
          action: () => { if (window.openDrop) window.openDrop(nm); }
        });
      });
    });
    // Herald ladder — the 5 Hell-TZ superunique tiers, each searchable and routed
    // to its own tier ID card via openDrop (the Sunder-source roster).
    const HT = (typeof HERALD_TIERS !== 'undefined') ? HERALD_TIERS : [];
    HT.forEach(t => {
      // The apex (Herald of Terror) already has its own richer search command above
      // (→ the dedicated RotW #herald-card) — don't add a second, leaner duplicate.
      if (t.apex) return;
      cmds.push({
        icon: '👹', label: t.n,
        sub: `Herald tier ${t.tier}${t.apex ? ' · apex' : ''} · Sunder source`,
        cat: 'herald', hint: t.drops,
        keywords: 'herald tier sunder superunique terror zone ' + t.n.toLowerCase() + ' ' + t.tier,
        action: () => { if (window.openDrop) window.openDrop(t.n); }
      });
    });
    // Uber Boss ID cards (9) — each searchable and routed to its own expandable
    // stat card in the Ancients tab via jumpToUberBoss.
    const UB = (typeof UBER_BOSSES !== 'undefined') ? UBER_BOSSES : [];
    UB.forEach((b) => {
      cmds.push({
        icon: b.emoji, label: b.name,
        sub: b.group + ' · ' + b.role,
        cat: 'uber boss', hint: b.immune ? 'immune: ' + b.immune : '',
        keywords: 'uber boss pandemonium tristram ancient pinnacle ' + b.name.toLowerCase() + ' ' + b.group.toLowerCase() + ' ' + b.role.toLowerCase(),
        action: () => { if (window.jumpToUberBoss) window.jumpToUberBoss(b.id); }
      });
    });
    // The 6 named Colossal Ancient Jewels — each its own searchable calculator
    // ID card (openDrop → colossalJewelDetailHtml). Distinct from the aggregate
    // "Colossal Ancient Jewels" material entry above.
    const CJ = (typeof COLOSSAL_JEWELS !== 'undefined') ? COLOSSAL_JEWELS : [];
    CJ.forEach((j) => {
      cmds.push({
        icon: j.emoji, label: j.n,
        sub: 'Colossal Jewel · ' + j.elem + ' · from Colossal ' + j.ancient,
        cat: 'colossal jewel', hint: j.dmg,
        keywords: 'colossal ancient jewel facet endgame bis pinnacle ' + j.n.toLowerCase() + ' ' + j.elem.toLowerCase() + ' ' + j.ancient.toLowerCase(),
        action: () => { if (window.openDrop) window.openDrop(j.n); }
      });
    });
    // The 5 named Colossal Statues — each its own searchable card (openDrop →
    // colossalStatueDetailHtml). Distinct from the aggregate statue material entry.
    const CS = (typeof COLOSSAL_STATUES !== 'undefined') ? COLOSSAL_STATUES : [];
    CS.forEach((s) => {
      cmds.push({
        icon: '👑', label: s.n,
        sub: 'Colossal Statue · from terrorized Hell ' + s.boss,
        cat: 'colossal statue', hint: '~1:8 to 1:15',
        keywords: 'colossal ancient statue summit pinnacle terror cube ' + s.n.toLowerCase() + ' ' + s.boss.toLowerCase() + ' ' + s.ancient.toLowerCase(),
        action: () => { if (window.openDrop) window.openDrop(s.n); }
      });
    });
    // The 33 runes — each its own searchable ID card (openDrop → runeDetailHtml,
    // exact rune-first branch). Audit fix (v191): runes had first-class clickable
    // cards but were absent from the search index — "Vex"/"Ber" returned no match.
    const RN = (typeof RUNES !== 'undefined') ? RUNES : [];
    RN.forEach((r) => {
      cmds.push({
        icon: '🪨', label: r.n + ' Rune',
        sub: 'Rune #' + r.num + ' · clvl ' + r.clvl + ' · ' + r.tier + ' tier',
        cat: 'rune', hint: 'wpn: ' + r.w,
        keywords: 'rune runes socket cube up ' + r.n.toLowerCase() + ' ' + r.tier + ' ' + (r.rw || '').toLowerCase(),
        action: () => { if (window.openDrop) window.openDrop(r.n); }
      });
    });
    // The 35 gem variants (7 types × 5 grades) — each its own searchable ID card
    // (openDrop → gem card via findGem exact match). Same audit fix as runes.
    const GT = (typeof GEM_TYPES !== 'undefined') ? GEM_TYPES : [];
    GT.forEach((g) => {
      (g.q || []).forEach((v) => {
        cmds.push({
          icon: '💎', label: v.name,
          sub: 'Gem · ' + g.type + ' · ' + g.role,
          cat: 'gem', hint: 'wpn: ' + v.w,
          keywords: 'gem gems socket cube ' + v.name.toLowerCase() + ' ' + g.type.toLowerCase() + ' ' + v.q.toLowerCase(),
          action: () => { if (window.openDrop) window.openDrop(v.name); }
        });
      });
    });
    // The 8 Rainbow Facets — each its own searchable ID card (openDrop →
    // rainbowFacetDetailHtml). Descriptive only: no roll %s, no drop odds.
    const RF = (typeof RAINBOW_FACETS !== 'undefined') ? RAINBOW_FACETS : [];
    RF.forEach((f) => {
      cmds.push({
        icon: f.emoji, label: f.n,
        sub: 'Rainbow Facet · ' + f.elem + ' · on ' + f.trig,
        cat: 'rainbow facet', hint: f.elem + ' skill damage / -enemy resist',
        keywords: 'rainbow facet jewel of fervor unique jewel skill damage enemy resistance ' + f.n.toLowerCase() + ' ' + f.elem.toLowerCase() + ' ' + f.trig.toLowerCase(),
        action: () => { if (window.openDrop) window.openDrop(f.n); }
      });
    });
    // v133 - "how do I renew my Sunder Charm?" -> the Sunder Renewal recipe tool.
    cmds.push({
      icon:'💠', label:'Renew a Sunder Charm - recipe', sub:'Latent + Perfect Gem + Rune + Worldstone Shard -> Renewed',
      cat:'recipe', hint:'tools',
      keywords:'recipe renew renewed sunder charm upgrade cube craft how to make what is the latent perfect gem rune worldstone shard immunity cold rupture flame rift crack of the heavens rotting fissure bone break black cleft',
      action: () => { if (window.openSunderRecipes) window.openSunderRecipes(); }
    });
    (typeof SUNDER_RECIPES !== 'undefined' ? SUNDER_RECIPES : []).forEach(function(s){
      cmds.push({
        icon:'💠', label:'Renew '+s.n+' - recipe', sub:s.gem+' + '+s.rune+' Rune + '+s.shards.length+' shard'+(s.shards.length>1?'s':''),
        cat:'recipe', hint:'tools',
        keywords:'recipe renew renewed upgrade cube craft '+s.n.toLowerCase()+' '+s.breaks.toLowerCase()+' sunder charm '+s.rune.toLowerCase()+' '+s.gem.toLowerCase(),
        action: () => { if (window.openSunderRecipes) window.openSunderRecipes(s.n); }
      });
    });
    return cmds;
  }

  // --- v42: Fuzzy matching (subsequence + prefix bonus) ---
  function v42FuzzyScore(query, target) {
    // Word-boundary aware fuzzy score.
    //   1000  exact prefix of label
    //    800  word-boundary match (after space, paren, dash, slash)
    //    500  anywhere-in-string match
    //    100  subsequence-only match
    //     -1  no match
    // Tie-break: shorter target wins (more specific result).
    if (!query) return 0;
    query = query.toLowerCase().trim();
    target = target.toLowerCase();
    if (!query) return 0;
    if (target.startsWith(query)) return 1000 - target.length;
    const wbRe = new RegExp('(^|[\\s\\(\\)/\\-_])' + query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    if (wbRe.test(target)) return 800 - target.length;
    const idx = target.indexOf(query);
    if (idx >= 0) return 500 - idx - (target.length / 100);
    // Subsequence
    let qi = 0;
    for (let i = 0; i < target.length && qi < query.length; i++) {
      if (target[i] === query[qi]) qi++;
    }
    if (qi === query.length) return 100 - (target.length - query.length);
    return -1;
  }

  function v42HighlightMatch(label, query) {
    if (!query) return label;
    const q = query.toLowerCase().trim();
    const lc = label.toLowerCase();
    const idx = lc.indexOf(q);
    if (idx >= 0) {
      return label.slice(0, idx) + '<mark>' + label.slice(idx, idx + q.length) + '</mark>' + label.slice(idx + q.length);
    }
    return label;
  }

  // --- v42: Custom MF parsing ("mf 750") ---
  function v42TryParseCustomMF(query) {
    const m = query.match(/^mf\s+(\d{1,4})$/i);
    if (m) {
      const v = parseInt(m[1], 10);
      if (v >= 0 && v <= 9999) return v;
    }
    return null;
  }
  // v42 polish: relative slider bump — "mf+50", "mf +50", "mf-100" all parse
  function v42TryParseMFBump(query) {
    const m = query.match(/^mf\s*([+-])\s*(\d{1,4})$/i);
    if (!m) return null;
    const sign = m[1] === '-' ? -1 : 1;
    const mag = parseInt(m[2], 10);
    if (mag <= 0 || mag > 9999) return null;
    return sign * mag;
  }

  // --- v42: State ---
  let v42Commands = null;  // lazy-built
  let v42Filtered = [];
  let v42ActiveIdx = 0;

  function v42EnsureCommands() {
    if (!v42Commands) v42Commands = v42BuildCommands();
    return v42Commands;
  }

  function v42Render() {
    const list = document.getElementById('v42-palette-list');
    if (!list) return;
    if (v42Filtered.length === 0) {
      list.innerHTML = '<div class="v42-pal-empty">no results · try a different query</div>';
      return;
    }
    let html = '';
    let lastCat = null;
    const catLabels = { recent:'Recently viewed', tab:'Tabs', boss:'Bosses', item:'Items', base:'Base items', runeword:'Runewords', mf:'MF Presets', action:'Actions' };
    const query = document.getElementById('v42-palette-input').value || '';
    v42Filtered.slice(0, 100).forEach((c, i) => {
      const effectiveCat = c._recent ? 'recent' : c.cat;
      if (effectiveCat !== lastCat) {
        html += `<div class="v42-pal-section-header">${catLabels[effectiveCat] || effectiveCat}</div>`;
        lastCat = effectiveCat;
      }
      const labelHl = v42HighlightMatch(c.label, query);
      const sub = c.sub ? `<div style="font-size:11px;opacity:.65;margin-top:2px">${c.sub}</div>` : '';
      const hint = c.hint ? `<span class="v42-pal-category">${c.hint}</span>` : '';
      html += `
        <div class="v42-pal-item ${i === v42ActiveIdx ? 'v42-pal-active' : ''}" data-v42-idx="${i}">
          <div class="v42-pal-icon">${c.icon}</div>
          <div class="v42-pal-label">${labelHl}${sub}</div>
          ${hint}
        </div>`;
    });
    list.innerHTML = html;
    // Scroll active into view
    const activeEl = list.querySelector('.v42-pal-active');
    if (activeEl) activeEl.scrollIntoView({ block: 'nearest' });
  }

  function v42Filter() {
    const input = document.getElementById('v42-palette-input');
    if (!input) return;
    const q = input.value.trim();
    const cmds = v42EnsureCommands();

    // Special: "mf <num>" -> inject custom MF command at top
    const customMF = v42TryParseCustomMF(q);
    let custom = [];
    if (customMF !== null) {
      custom.push({
        icon: '🎯',
        label: `Set MF to ${customMF}%`,
        cat: 'mf',
        hint: 'custom',
        action: () => {
          const slider = document.getElementById('mf');
          if (slider) {
            slider.value = customMF;
            slider.dispatchEvent(new Event('input', { bubbles: true }));
          }
        }
      });
    }
    // v42 polish: "mf+50" / "mf-100" -> relative bump, clamps to slider min/max, shows preview
    const mfBump = v42TryParseMFBump(q);
    if (mfBump !== null) {
      const slider = document.getElementById('mf');
      if (slider) {
        const cur = parseInt(slider.value, 10) || 0;
        const min = parseInt(slider.min, 10) || 0;
        const max = parseInt(slider.max, 10) || 1000;
        const target = Math.max(min, Math.min(max, cur + mfBump));
        const sign = mfBump >= 0 ? '+' : '';
        const clampNote = (target !== cur + mfBump) ? ' (clamped)' : '';
        custom.push({
          icon: mfBump >= 0 ? '⬆' : '⬇',
          label: `MF ${cur}% ${sign}${mfBump} → ${target}%${clampNote}`,
          cat: 'mf',
          hint: 'bump',
          action: () => {
            slider.value = target;
            slider.dispatchEvent(new Event('input', { bubbles: true }));
          }
        });
      }
    }
    // v42 polish: "star <query>" or "unstar <query>" -> add wishlist toggle commands
    const starMatch = q.match(/^(un)?star\s+(.+)$/i);
    if (starMatch) {
      const unstarMode = !!starMatch[1];
      const subQuery = starMatch[2].toLowerCase().trim();
      // ITEMS + wishlist are module-scoped in main bible script — access via eval (same global script scope)
      let items = [], wishlistSet = null;
      try {
        items = eval('typeof ITEMS !== "undefined" ? ITEMS : []') || [];
        wishlistSet = eval('typeof wishlist !== "undefined" ? wishlist : null');
      } catch(e) {}
      const seen = new Set();
      const matches = [];
      for (const it of items) {
        const name = it.n || it.name;
        if (!name || seen.has(name)) continue;
        if (!name.toLowerCase().includes(subQuery)) continue;
        const isStarred = (wishlistSet instanceof Set) ? wishlistSet.has(name) : false;
        // unstar mode: only show currently-starred items
        if (unstarMode && !isStarred) continue;
        // star mode: show all matching items (already-starred ones will toggle off)
        seen.add(name);
        matches.push({
          icon: isStarred ? '★' : '☆',
          label: `${isStarred ? 'Unstar' : 'Star'}: ${name}`,
          cat: 'action',
          hint: isStarred ? 'starred' : '',
          action: () => {
            if (typeof window.toggleStarred === 'function') window.toggleStarred(name);
          }
        });
        if (matches.length >= 12) break;
      }
      custom = [...custom, ...matches];
    }

    if (!q && custom.length === 0) {
      // v42 polish: show recently-viewed first, then defaults
      const recent = v42GetRecent();
      const recentCmds = [];
      recent.forEach(r => {
        const match = cmds.find(c => c.label === r.label && c.cat === r.cat);
        if (match) recentCmds.push({ ...match, _recent: true });
      });
      const usedLabels = new Set(recent.map(r => r.label));
      const others = cmds.filter(c => !usedLabels.has(c.label)).slice(0, 30 - recentCmds.length);
      v42Filtered = [...recentCmds, ...others];
    } else {
      // v42: score label and keywords SEPARATELY — label match always beats keywords-only
      const scored = cmds
        .map(c => {
          const labelScore = v42FuzzyScore(q, c.label);
          const keyScore = c.keywords ? v42FuzzyScore(q, c.keywords) * 0.4 : -1;
          let s = Math.max(labelScore, keyScore);
          // Runeword boost — when label score is positive (real match), give priority for commonly-searched RWs
          if (labelScore > 0 && c.cat === 'runeword') s += 25;
          return { c, score: s };
        })
        .filter(x => x.score > 0)
        .sort((a, b) => b.score - a.score)
        .map(x => x.c);
      v42Filtered = [...custom, ...scored];
    }
    v42ActiveIdx = 0;
    v42Render();
  }

  function v42Open() {
    v42EnsureCommands();
    const overlay = document.getElementById('v42-palette-overlay');
    const input = document.getElementById('v42-palette-input');
    if (!overlay || !input) return;
    overlay.classList.add('show');
    input.value = '';
    v42Filter();
    setTimeout(() => input.focus(), 30);
  }
  function v42Close() {
    const overlay = document.getElementById('v42-palette-overlay');
    if (overlay) overlay.classList.remove('show');
  }
  // v42 polish: recently-viewed tracking
  const V42_RECENT_KEY = 'd2r_v42_recent';
  const V42_RECENT_MAX = 8;
  function v42PushRecent(cmd) {
    if (!cmd || !['boss','item','runeword'].includes(cmd.cat)) return;
    try {
      const stored = JSON.parse(localStorage.getItem(V42_RECENT_KEY) || '[]');
      // Dedup by label
      const filtered = stored.filter(r => r.label !== cmd.label);
      filtered.unshift({ label: cmd.label, cat: cmd.cat, ts: Date.now() });
      const trimmed = filtered.slice(0, V42_RECENT_MAX);
      localStorage.setItem(V42_RECENT_KEY, JSON.stringify(trimmed));
    } catch(e) {}
  }
  function v42GetRecent() {
    try {
      const stored = JSON.parse(localStorage.getItem(V42_RECENT_KEY) || '[]');
      return stored;
    } catch(e) { return []; }
  }

  function v42Execute(idx) {
    const c = v42Filtered[idx];
    if (!c || typeof c.action !== 'function') return;
    v42PushRecent(c);
    v42Close();
    setTimeout(() => { try { c.action(); } catch(e) { console.warn('v42 palette action error:', e); } }, 80);
  }

  // Expose for external triggers
  window._v42_openPalette = v42Open;
  window._v42_pushRecent = v42PushRecent;  // v42 polish: exposed so setActiveItem/openBossDetail hooks can record
  window._v42_closePalette = v42Close;

  // --- v42: Event wiring ---
  document.addEventListener('DOMContentLoaded', () => {
    // Cmd+K / Ctrl+K toggles palette (works inside inputs too — that's the point)
    document.addEventListener('keydown', e => {
      const isCmdK = (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k';
      if (isCmdK) {
        e.preventDefault();
        const overlay = document.getElementById('v42-palette-overlay');
        if (overlay && overlay.classList.contains('show')) v42Close();
        else v42Open();
        return;
      }
      // Inside the palette: handle navigation
      const overlay = document.getElementById('v42-palette-overlay');
      if (!overlay || !overlay.classList.contains('show')) return;
      if (e.key === 'Escape') { e.preventDefault(); v42Close(); return; }
      if (e.key === 'ArrowDown') { e.preventDefault(); v42ActiveIdx = Math.min(v42ActiveIdx + 1, v42Filtered.length - 1); v42Render(); return; }
      if (e.key === 'ArrowUp')   { e.preventDefault(); v42ActiveIdx = Math.max(v42ActiveIdx - 1, 0); v42Render(); return; }
      if (e.key === 'Enter') { e.preventDefault(); v42Execute(v42ActiveIdx); return; }
    });

    const input = document.getElementById('v42-palette-input');
    if (input) input.addEventListener('input', v42Filter);

    // Click on list item executes
    const list = document.getElementById('v42-palette-list');
    if (list) list.addEventListener('click', e => {
      const item = e.target.closest('.v42-pal-item');
      if (!item) return;
      const idx = parseInt(item.dataset.v42Idx, 10);
      if (!isNaN(idx)) v42Execute(idx);
    });

    // Click overlay (outside palette) closes
    const overlay = document.getElementById('v42-palette-overlay');
    if (overlay) overlay.addEventListener('click', e => {
      if (e.target === overlay) v42Close();
    });
  });
})();
