/* ═══════════════════════════════════════════════════════════════════════════
   v44 — Session Cockpit · Progress schema v2 · Intake review · Pillar nav
   · Dock Chronicle pin · Stash staleness · Offline SW registration
   Loads AFTER the bible monolith. Additive only; never deletes base behavior.
   ═══════════════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var BUILD = {
    id: 'v44',
    name: 'Session Cockpit',
    date: '2026-07-14',
    rev: '1',
  };
  window.D2R_BUILD = BUILD;

  var STALE_WARN_H = 12;   // hours → yellow
  var STALE_BAD_H = 36;    // hours → red
  var META_KEY = 'd2r_stashMeta';
  var PIN_KEY = 'd2r_chroniclePin';
  var SCHEMA_KEYS = {
    grail: ['d2r_owned', 'd2r_copies', 'd2r_wishlist', 'd2r_setPieces', 'd2r_ethereal', 'd2r_superiorBases', 'd2r_multiKeep', 'd2r_unknownReads', 'd2r_magicFinds', 'd2r_foundLog', 'd2r_grailUnfound', 'd2r_grailImportReport'],
    stashes: ['d2r_runeStash', 'd2r_gemStash', 'd2r_materialStash', 'd2r_craftStash', 'd2r_craftBaseStash', 'd2r_statues', 'd2r_muleAssign', 'd2r_muleRoster', 'd2r_vault_fs'],
    chronicle: ['d2r_rwMade', 'd2r_rwUnmade', 'd2r_rwVerify', 'd2r_rwProfile', 'd2r_rwBaseUsed', 'd2r_ladderMode', 'd2r_ladderPreview'],
    forge: ['d2r_forgeStep', 'd2r_forgeSkip', 'd2r_forgeDone', 'd2r_createNow', 'd2r_createNowDate', 'd2r_createNowAi', 'd2r_createNowAiV', 'd2r_createNowAiDate'],
    intake: ['d2r_intakeLog', 'd2r_intakeSeen', 'd2r_intakeUrl', 'd2r_lastTopScan', 'd2r_aicDraft', META_KEY, PIN_KEY],
    settings: ['d2r_mf', 'd2r_players', 'd2r_activeTab', 'd2r_dockCollapsed', 'd2r_bossFilters', 'd2r_bossSorts', 'd2r_pinnedBoss', 'd2r_grailWallOpen', 'd2r_shortcuts_seen', 'd2r_v42_recent', 'd2r_v42_tz_visible'],
  };

  function lsGet(k, fallback) {
    try {
      var raw = (window.LS && window.LS.getItem) ? window.LS.getItem(k) : localStorage.getItem(k);
      return raw == null ? fallback : raw;
    } catch (e) { return fallback; }
  }
  function lsSet(k, v) {
    try {
      if (window.LS && window.LS.setItem) window.LS.setItem(k, v);
      else localStorage.setItem(k, v);
    } catch (e) {}
  }
  function lsJson(k, fallback) {
    try {
      var r = lsGet(k, null);
      if (r == null || r === '') return fallback;
      return JSON.parse(r);
    } catch (e) { return fallback; }
  }
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
  function $(id) { return document.getElementById(id); }

  // ── Build badge ──────────────────────────────────────────────────────────
  function mountBuildBadge() {
    if ($('v44-build-badge')) return;
    var el = document.createElement('div');
    el.id = 'v44-build-badge';
    el.title = 'Konyo D2R Bible build id';
    el.textContent = BUILD.id + ' · ' + BUILD.date + ' · r' + BUILD.rev;
    document.body.appendChild(el);
  }

  // ── Progress schema v2 (wrap export snapshot) ────────────────────────────
  function groupSchema(flat) {
    var schema = { version: 2, groups: {} };
    var used = {};
    Object.keys(SCHEMA_KEYS).forEach(function (g) {
      schema.groups[g] = {};
      SCHEMA_KEYS[g].forEach(function (k) {
        if (flat && flat[k] != null) {
          schema.groups[g][k] = true;
          used[k] = true;
        }
      });
    });
    schema.groups.other = {};
    if (flat) {
      Object.keys(flat).forEach(function (k) {
        if (!used[k] && k.indexOf('d2r_') === 0) schema.groups.other[k] = true;
      });
    }
    return schema;
  }

  function enhanceProgressSnapshot() {
    if (typeof window._progressSnapshot !== 'function') return;
    var orig = window._progressSnapshot;
    // Also patch the inner function if it's only local — exportProgress calls _progressSnapshot from closure.
    // On window we re-bind after defining.
    window._progressSnapshot = function () {
      var flat = (typeof window._collectProgress === 'function')
        ? window._collectProgress()
        : {};
      // Prefer live collect; fall back to parsing original
      if (!flat || !Object.keys(flat).length) {
        try {
          var o = JSON.parse(orig());
          flat = (o && o.data) || {};
        } catch (e) { flat = {}; }
      }
      var meta = {
        schemaVersion: 2,
        build: BUILD.id,
        buildDate: BUILD.date,
        profile: window.D2R_PROFILE || 'main',
        machine: window.D2R_MACHINE || 'mac',
        stashMeta: lsJson(META_KEY, {}),
        chroniclePin: lsGet(PIN_KEY, '') || null,
      };
      return JSON.stringify({
        app: 'd2r-bible',
        kind: 'grail-progress',
        version: 2,
        exported: new Date().toISOString(),
        meta: meta,
        schema: groupSchema(flat),
        data: flat,
      }, null, 2);
    };

    // Re-wire public export helpers if they closed over the old snapshot fn —
    // they call _progressSnapshot by name in the same scope, but window.* bindings
    // used from HTML onclick go through window.exportProgress which we re-wrap:
    ['exportProgress', 'copyProgress', 'downloadProgress'].forEach(function (name) {
      var fn = window[name];
      if (typeof fn !== 'function') return;
      // leave as-is if they already call window._progressSnapshot via free name in outer scope
    });
  }

  // Patch _collectProgress onto window if missing (it's in the same script scope as export)
  function exposeCollect() {
    // bible already has function _collectProgress in global script scope (non-module) → window
    // Ensure version note on backup status after export
    var origExport = window.exportProgress;
    if (typeof origExport === 'function') {
      window.exportProgress = function () {
        // Force snapshot through our v2 builder by writing textarea ourselves
        var ta = $('backup-textarea');
        var snap = window._progressSnapshot();
        if (ta) ta.value = snap;
        var ownedN = 0, wishN = 0;
        try {
          var o = JSON.parse(snap);
          var d = o.data || {};
          if (d.d2r_owned) ownedN = Object.keys(JSON.parse(d.d2r_owned)).length;
          if (d.d2r_wishlist) {
            var w = JSON.parse(d.d2r_wishlist);
            wishN = Array.isArray(w) ? w.length : Object.keys(w).length;
          }
        } catch (e) {}
        var el = $('backup-status');
        if (el) {
          el.textContent = 'Snapshot v2 built — schema groups + ' + Object.keys((function () {
            try { return JSON.parse(snap).data || {}; } catch (e) { return {}; }
          })()).length + ' keys · build ' + BUILD.id + '. Safe on any machine.';
          el.className = 'backup-status ok';
        }
      };
    }
    var origCopy = window.copyProgress;
    if (typeof origCopy === 'function') {
      window.copyProgress = function () {
        var snap = window._progressSnapshot();
        var ta = $('backup-textarea');
        if (ta) ta.value = snap;
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(snap).then(function () {
            var el = $('backup-status');
            if (el) { el.textContent = 'Copied v2 snapshot ✓'; el.className = 'backup-status ok'; }
          }, function () { if (ta) ta.select(); });
        } else if (ta) ta.select();
      };
    }
    var origDl = window.downloadProgress;
    if (typeof origDl === 'function') {
      window.downloadProgress = function () {
        var snap = window._progressSnapshot();
        var ta = $('backup-textarea');
        if (ta) ta.value = snap;
        try {
          var blob = new Blob([snap], { type: 'application/json' });
          var url = URL.createObjectURL(blob);
          var a = document.createElement('a');
          a.href = url;
          a.download = 'd2r-bible-progress-v2-' + new Date().toISOString().slice(0, 10) + '.json';
          document.body.appendChild(a); a.click(); a.remove();
          setTimeout(function () { URL.revokeObjectURL(url); }, 1500);
          var el = $('backup-status');
          if (el) { el.textContent = 'Downloaded v2 snapshot ✓'; el.className = 'backup-status ok'; }
        } catch (e) {}
      };
    }
  }

  // ── Stash meta / staleness ───────────────────────────────────────────────
  function readMeta() { return lsJson(META_KEY, {}) || {}; }
  function touchStash(kind) {
    var m = readMeta();
    m[kind] = new Date().toISOString();
    lsSet(META_KEY, JSON.stringify(m));
    refreshStalenessUI();
  }
  function ageHours(iso) {
    if (!iso) return Infinity;
    var t = Date.parse(iso);
    if (!isFinite(t)) return Infinity;
    return (Date.now() - t) / 3600000;
  }
  function ageLabel(iso) {
    var h = ageHours(iso);
    if (!isFinite(h) || h === Infinity) return 'never scanned';
    if (h < 1) return Math.round(h * 60) + 'm ago';
    if (h < 48) return Math.round(h) + 'h ago';
    return Math.round(h / 24) + 'd ago';
  }
  function ageClass(iso) {
    var h = ageHours(iso);
    if (!isFinite(h) || h >= STALE_BAD_H) return 'bad';
    if (h >= STALE_WARN_H) return 'warn';
    return 'ok';
  }

  function refreshStalenessUI() {
    var m = readMeta();
    var kinds = [
      { k: 'runes', label: 'Runes', tab: 'tools' },
      { k: 'gems', label: 'Gems', tab: 'tools' },
      { k: 'materials', label: 'Mats', tab: 'tools' },
      { k: 'vault', label: 'Vault', tab: 'tools' },
    ];
    // Global strip
    var strip = $('v44-global-stale');
    if (!strip) {
      strip = document.createElement('div');
      strip.id = 'v44-global-stale';
      strip.setAttribute('role', 'status');
      document.body.insertBefore(strip, document.body.firstChild);
    }
    var worst = 'ok';
    var bits = [];
    kinds.forEach(function (x) {
      var c = ageClass(m[x.k]);
      if (c === 'bad') worst = 'bad';
      else if (c === 'warn' && worst === 'ok') worst = 'warn';
      if (c !== 'ok') bits.push(x.label + ' ' + ageLabel(m[x.k]));
    });
    if (bits.length) {
      strip.className = 'show';
      strip.innerHTML = '<strong>Stash freshness</strong> · ' + esc(bits.join(' · ')) +
        ' <button type="button" class="v44-btn ghost" style="padding:3px 8px;font-size:11px" onclick="window.switchTab&&window.switchTab(\'tools\')">Update in Tools →</button>';
    } else {
      strip.className = '';
      strip.innerHTML = '';
    }
    // Session chips
    var host = $('v44-session-stale');
    if (host) {
      host.innerHTML = kinds.map(function (x) {
        var c = ageClass(m[x.k]);
        return '<button type="button" class="v44-stale-chip ' + c + '" data-tab="' + x.tab + '" title="last intake: ' + esc(m[x.k] || 'never') + '">' +
          esc(x.label) + ' · ' + esc(ageLabel(m[x.k])) + '</button>';
      }).join('');
      host.querySelectorAll('button').forEach(function (btn) {
        btn.addEventListener('click', function () {
          if (window.switchTab) window.switchTab(btn.getAttribute('data-tab'));
        });
      });
    }
  }

  // ── Chronicle pin ────────────────────────────────────────────────────────
  function getChronicleTarget() {
    var pin = lsGet(PIN_KEY, '');
    if (pin) return { name: pin, source: 'pin' };
    // Infer next forge-able / one-step from forgeScan
    try {
      if (typeof window.forgeScan === 'function') {
        var s = window.forgeScan();
        if (s && s.now && s.now.length) {
          var live = s.now.filter(function (t) { return !t.deferred; });
          if (live[0]) return { name: live[0].rw, source: 'make-now', detail: 'ready to forge' };
        }
        if (s && s.onestep && s.onestep[0]) {
          return { name: s.onestep[0].rw, source: 'one-step', detail: s.onestep[0].sub || 'one step away' };
        }
        if (s && s.pipeline && s.pipeline[0]) {
          return { name: s.pipeline[0].rw, source: 'pipeline', detail: 'pipeline' };
        }
      }
    } catch (e) {}
    return { name: null, source: 'none', detail: 'set a Chronicle target' };
  }

  function setChroniclePin(name) {
    if (name) lsSet(PIN_KEY, String(name));
    else {
      try {
        if (window.LS && window.LS.removeItem) window.LS.removeItem(PIN_KEY);
        else localStorage.removeItem(PIN_KEY);
      } catch (e) {}
    }
    refreshDockPin();
    if ($('tab-session') && $('tab-session').classList.contains('active')) renderSession();
  }

  function refreshDockPin() {
    var dock = $('control-dock');
    if (!dock) return;
    var btn = $('v44-dock-chronicle');
    if (!btn) {
      btn = document.createElement('button');
      btn.type = 'button';
      btn.id = 'v44-dock-chronicle';
      btn.title = 'Chronicle target — click to open Forge / Session';
      var inner = dock.querySelector('.dock-inner');
      if (inner) {
        // insert after handle / before sliders
        var sliders = $('dock-sliders');
        if (sliders) inner.insertBefore(btn, sliders);
        else inner.appendChild(btn);
      }
      btn.addEventListener('click', function () {
        if (window.switchTab) window.switchTab('session');
      });
    }
    var t = getChronicleTarget();
    var label = t.name || '— pick target —';
    var meta = t.detail || t.source || '';
    btn.innerHTML = '<span class="v44-dc-label">Chronicle</span>' +
      '<span class="v44-dc-target" data-arttip="' + esc(label) + '">' + esc(label) + '</span>' +
      (meta ? '<span class="v44-dc-meta">' + esc(meta) + '</span>' : '');
  }

  // ── Pillar navigation ────────────────────────────────────────────────────
  var PILLARS = [
    { id: 'session', label: 'Session', tabs: ['session'] },
    { id: 'hunt', label: 'Hunt', tabs: ['bosses', 'calc', 'tz', 'tztracker'] },
    { id: 'stash', label: 'Stash', tabs: ['tools', 'runes', 'forge'] },
    { id: 'grail', label: 'Grail', tabs: ['main', 'funi', 'fsets'] },
    { id: 'codex', label: 'Codex', tabs: ['rotw', 'ancients', 'endgame', 'binds', 'ref'], collapsible: true },
  ];

  function restructureTabs() {
    var root = document.querySelector('.tabs');
    if (!root || root.classList.contains('v44-pillars')) return;
    root.classList.add('v44-pillars');

    // Ensure session tab button exists
    if (!root.querySelector('.tab[data-tab="session"]')) {
      var sb = document.createElement('button');
      sb.className = 'tab';
      sb.setAttribute('data-tab', 'session');
      sb.dataset.tab = 'session';
      sb.textContent = '⚡ session';
      sb.title = 'Today\'s session cockpit — Forge · TZ · Chronicle · intake health';
      var first = root.querySelector('.tab');
      if (first && first.parentNode) first.parentNode.insertBefore(sb, first);
      else root.insertBefore(sb, root.firstChild);
    }

    // Collect all tab buttons
    var byName = {};
    root.querySelectorAll('.tab[data-tab]').forEach(function (btn) {
      byName[btn.getAttribute('data-tab')] = btn;
      // Re-bind to navClean (same as base bible) so pillar move never orphans clicks
      btn.onclick = function () {
        var n = btn.getAttribute('data-tab') || btn.dataset.tab;
        if (typeof window.navClean === 'function') window.navClean(n);
        else if (typeof window.switchTab === 'function') window.switchTab(n);
      };
    });

    // Build pillar rows
    var frag = document.createDocumentFragment();
    var codexCollapsed = lsGet('d2r_v44_codexCollapsed', '1') !== '0';

    PILLARS.forEach(function (p) {
      var row = document.createElement('div');
      row.className = 'v44-pillar-row';
      row.setAttribute('data-pillar', p.id);
      var lab = document.createElement('span');
      lab.className = 'v44-pillar-label';
      lab.textContent = p.label;
      row.appendChild(lab);
      var hold = document.createElement('div');
      hold.className = 'v44-pillar-tabs';
      p.tabs.forEach(function (tn) {
        var btn = byName[tn];
        if (btn) {
          if (p.collapsible) btn.classList.add('v44-codex-tab');
          hold.appendChild(btn);
        }
      });
      if (p.collapsible) {
        var more = document.createElement('button');
        more.type = 'button';
        more.className = 'v44-more-btn';
        more.setAttribute('aria-expanded', codexCollapsed ? 'false' : 'true');
        more.textContent = codexCollapsed ? 'Codex ▾' : 'Codex ▴';
        more.addEventListener('click', function (e) {
          e.stopPropagation();
          codexCollapsed = !codexCollapsed;
          lsSet('d2r_v44_codexCollapsed', codexCollapsed ? '1' : '0');
          root.classList.toggle('v44-codex-collapsed', codexCollapsed);
          more.setAttribute('aria-expanded', codexCollapsed ? 'false' : 'true');
          more.textContent = codexCollapsed ? 'Codex ▾' : 'Codex ▴';
        });
        hold.appendChild(more);
      }
      row.appendChild(hold);
      frag.appendChild(row);
    });

    // Clear old structure and append pillars (orphan leftover wrappers)
    while (root.firstChild) root.removeChild(root.firstChild);
    root.appendChild(frag);
    if (codexCollapsed) root.classList.add('v44-codex-collapsed');
  }

  // ── Session tab content ──────────────────────────────────────────────────
  function ensureSessionTab() {
    if ($('tab-session')) return;
    var container = document.querySelector('.container');
    if (!container) return;
    var div = document.createElement('div');
    div.className = 'tab-content';
    div.id = 'tab-session';
    div.innerHTML =
      '<div class="v44-session-hero">' +
        '<div><h1>⚡ Today\'s Session</h1>' +
        '<p class="v44-sub">What to farm, cube, and forge <b>right now</b> for Chronicle. Live from your tallies · MF · TZ.</p></div>' +
        '<div class="v44-session-kpis" id="v44-kpis"></div>' +
      '</div>' +
      '<div class="v44-staleness" id="v44-session-stale"></div>' +
      '<div class="v44-grid">' +
        '<section class="v44-card" id="v44-card-tz"><h2>🔥 Terror Zone <button type="button" class="v44-go" data-go="tztracker">tracker</button></h2><div class="v44-body" id="v44-tz-body"></div></section>' +
        '<section class="v44-card" id="v44-card-forge"><h2>🔨 Forge top 3 <button type="button" class="v44-go" data-go="forge">full forge</button></h2><div class="v44-body" id="v44-forge-body"></div></section>' +
        '<section class="v44-card" id="v44-card-chronicle"><h2>📜 Chronicle target <button type="button" class="v44-go" data-go="forge">open</button></h2><div class="v44-body" id="v44-chronicle-body"></div></section>' +
        '<section class="v44-card" id="v44-card-grail"><h2>⭐ Wishlist hunt <button type="button" class="v44-go" data-go="calc">calculator</button></h2><div class="v44-body" id="v44-grail-body"></div></section>' +
      '</div>' +
      '<div class="v44-actions">' +
        '<button type="button" class="v44-btn primary" data-go="tools">📸 Update intakes</button>' +
        '<button type="button" class="v44-btn" data-go="forge">🔨 Open Forge</button>' +
        '<button type="button" class="v44-btn" data-go="tztracker">📡 TZ Tracker</button>' +
        '<button type="button" class="v44-btn" id="v44-print-plan">🖨 Tonight\'s plan</button>' +
        '<button type="button" class="v44-btn ghost" data-go="main">📚 Full main bible</button>' +
      '</div>';
    // Insert as first tab-content
    var first = container.querySelector('.tab-content');
    if (first) container.insertBefore(div, first);
    else container.appendChild(div);

    div.querySelectorAll('[data-go]').forEach(function (el) {
      el.addEventListener('click', function () {
        var t = el.getAttribute('data-go');
        if (t && window.switchTab) window.switchTab(t);
      });
    });
    var pr = $('v44-print-plan');
    if (pr) pr.addEventListener('click', function () {
      if (window.switchTab) window.switchTab('session');
      setTimeout(function () { window.print(); }, 200);
    });
  }

  function chronicleProgress() {
    try {
      var total = (typeof RUNEWORD_TIP !== 'undefined') ? Object.keys(RUNEWORD_TIP).length : 0;
      var made = 0;
      var raw = lsGet('d2r_rwMade', '{}');
      var obj = JSON.parse(raw || '{}');
      if (obj && typeof obj === 'object') made = Object.keys(obj).length;
      return { made: made, total: total || 100, pct: total ? Math.round(made / total * 100) : 0 };
    } catch (e) { return { made: 0, total: 100, pct: 0 }; }
  }

  function grailProgress() {
    try {
      var raw = lsGet('d2r_owned', '{}');
      var o = JSON.parse(raw || '{}');
      var n = o && typeof o === 'object' ? Object.keys(o).length : 0;
      // prefer live circle text if present
      var t = $('gp-circle-text');
      var pct = t ? t.textContent : '';
      return { owned: n, pct: pct };
    } catch (e) { return { owned: 0, pct: '0%' }; }
  }

  function renderTzCard() {
    var body = $('v44-tz-body');
    if (!body) return;
    body.innerHTML = '<p class="v44-empty">Loading live TZ…</p>';
    fetch('/api/tz', { cache: 'no-store', credentials: 'same-origin' })
      .then(function (r) { if (!r.ok) throw new Error('http ' + r.status); return r.json(); })
      .then(function (data) {
        var cur = data.current || data.tz || data.active || null;
        var next = data.next || null;
        var label = '';
        if (typeof cur === 'string') label = cur;
        else if (cur && cur.zone) label = cur.zone;
        else if (cur && cur.name) label = cur.name;
        else if (data.terrorZone) label = data.terrorZone;
        else if (data.zones && data.zones[0]) label = data.zones[0].name || data.zones[0];
        var html = '';
        if (label) {
          html += '<div class="v44-row"><span class="v44-tag farm">now</span><div class="v44-body"><b>' + esc(label) + '</b>';
          if (cur && cur.act) html += ' <span style="color:var(--v44-muted)">· Act ' + esc(cur.act) + '</span>';
          html += '</div>' +
            '<button type="button" class="v44-link" onclick="window.switchTab&&window.switchTab(\'tz\')">zones</button></div>';
        } else {
          html += '<p class="v44-empty">TZ feed online but zone label unknown — open the tracker.</p>';
        }
        if (next) {
          var nl = typeof next === 'string' ? next : (next.zone || next.name || '');
          if (nl) html += '<div class="v44-row"><span class="v44-tag">next</span><div class="v44-body">' + esc(nl) + '</div></div>';
        }
        // history hint
        if (data.updated || data.fetchedAt) {
          html += '<p class="v44-empty" style="margin-top:8px">Updated ' + esc(data.updated || data.fetchedAt) + '</p>';
        }
        body.innerHTML = html;
      })
      .catch(function () {
        body.innerHTML = '<p class="v44-empty">Could not reach <code>/api/tz</code> (offline or gate). Open <b>TZ tracker</b> when online.</p>';
      });
  }

  function renderForgeCard() {
    var body = $('v44-forge-body');
    if (!body) return;
    var rows = [];
    try {
      if (typeof window.forgeScan === 'function') {
        var s = window.forgeScan();
        var live = (s.now || []).filter(function (t) { return !t.deferred; });
        live.slice(0, 2).forEach(function (t) {
          rows.push({ tag: 'now', tagClass: 'now', text: 'Forge <b>' + esc(t.rw) + '</b> — runes + base ready', rw: t.rw });
        });
        (s.onestep || []).slice(0, 2).forEach(function (t) {
          var miss = (t.missing && t.missing.length) ? t.missing.join(', ') : (t.sub || 'one step');
          rows.push({ tag: 'step', tagClass: 'step', text: '<b>' + esc(t.rw) + '</b> — ' + esc(miss), rw: t.rw });
        });
        (s.pipeline || []).slice(0, 1).forEach(function (t) {
          rows.push({ tag: 'pipe', tagClass: 'pipe', text: 'Socket/pipeline <b>' + esc(t.rw) + '</b>', rw: t.rw });
        });
      }
    } catch (e) {}
    if (!rows.length) {
      body.innerHTML = '<p class="v44-empty">No forge tasks yet — scan runes/gems in Tools, then re-open Session.</p>';
      return;
    }
    body.innerHTML = rows.slice(0, 3).map(function (r) {
      return '<div class="v44-row"><span class="v44-tag ' + r.tagClass + '">' + r.tag + '</span>' +
        '<div class="v44-body">' + r.text + '</div>' +
        '<button type="button" class="v44-link" data-pin="' + esc(r.rw) + '">pin</button></div>';
    }).join('');
    body.querySelectorAll('[data-pin]').forEach(function (b) {
      b.addEventListener('click', function () { setChroniclePin(b.getAttribute('data-pin')); });
    });
  }

  function renderChronicleCard() {
    var body = $('v44-chronicle-body');
    if (!body) return;
    var t = getChronicleTarget();
    var prog = chronicleProgress();
    var html = '';
    html += '<div class="v44-row"><span class="v44-tag">progress</span><div class="v44-body"><b>' + prog.made + '</b> / ' + prog.total + ' runewords · ' + prog.pct + '%</div></div>';
    if (t.name) {
      html += '<div class="v44-row"><span class="v44-tag now">target</span><div class="v44-body"><b>' + esc(t.name) + '</b>';
      if (t.detail) html += ' <span style="color:var(--v44-muted)">· ' + esc(t.detail) + '</span>';
      html += '</div></div>';
    } else {
      html += '<p class="v44-empty">No target yet. Pin one from Forge top 3, or open Forge and mark your next word.</p>';
    }
    html += '<div class="v44-actions" style="margin-top:6px">' +
      '<button type="button" class="v44-btn" id="v44-clear-pin">Clear pin</button>' +
      '<button type="button" class="v44-btn primary" data-go="forge">Work this in Forge</button></div>';
    // manual pin input
    html += '<div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap">' +
      '<input id="v44-pin-input" type="text" placeholder="Pin runeword name…" style="flex:1;min-width:140px;background:var(--surface-3);border:1px solid var(--v44-border);color:var(--v44-text);border-radius:6px;padding:6px 8px;font:inherit">' +
      '<button type="button" class="v44-btn" id="v44-set-pin">Set pin</button></div>';
    body.innerHTML = html;
    var clear = $('v44-clear-pin');
    if (clear) clear.addEventListener('click', function () { setChroniclePin(''); });
    var setb = $('v44-set-pin');
    if (setb) setb.addEventListener('click', function () {
      var v = ($('v44-pin-input') || {}).value;
      if (v && v.trim()) setChroniclePin(v.trim());
    });
    body.querySelectorAll('[data-go]').forEach(function (el) {
      el.addEventListener('click', function () {
        if (window.switchTab) window.switchTab(el.getAttribute('data-go'));
      });
    });
  }

  function renderGrailCard() {
    var body = $('v44-grail-body');
    if (!body) return;
    var picks = [];
    try {
      // hero-picks DOM (main tab) if populated
      var hp = $('hero-picks');
      if (hp) {
        hp.querySelectorAll('[data-name], .hero-pick, .hp-item, [onclick*="openDrop"]').forEach(function (el) {
          var n = el.getAttribute('data-name') || el.getAttribute('data-item') || (el.textContent || '').trim();
          if (n && n.length < 48) picks.push(n.split('\n')[0].trim());
        });
      }
    } catch (e) {}
    try {
      var wish = lsJson('d2r_wishlist', null);
      if (Array.isArray(wish)) picks = picks.concat(wish);
      else if (wish && typeof wish === 'object') picks = picks.concat(Object.keys(wish));
    } catch (e) {}
    // unique
    var seen = {};
    picks = picks.filter(function (p) {
      p = String(p).replace(/\s+/g, ' ').trim();
      if (!p || seen[p]) return false;
      seen[p] = true;
      return true;
    }).slice(0, 5);

    var g = grailProgress();
    var html = '<div class="v44-row"><span class="v44-tag">grail</span><div class="v44-body"><b>' + g.owned + '</b> owned' +
      (g.pct ? ' · ' + esc(g.pct) : '') + '</div></div>';
    if (picks.length) {
      html += picks.map(function (n) {
        return '<div class="v44-row"><span class="v44-tag farm">want</span><div class="v44-body">' + esc(n) + '</div>' +
          '<button type="button" class="v44-link" data-drop="' + esc(n) + '">open</button></div>';
      }).join('');
    } else {
      html += '<p class="v44-empty">Star items in the calculator to prioritize them here.</p>';
    }
    body.innerHTML = html;
    body.querySelectorAll('[data-drop]').forEach(function (b) {
      b.addEventListener('click', function () {
        var n = b.getAttribute('data-drop');
        if (window.openDrop) window.openDrop(n);
        else if (window.switchTab) window.switchTab('calc');
      });
    });
  }

  function renderKpis() {
    var host = $('v44-kpis');
    if (!host) return;
    var c = chronicleProgress();
    var g = grailProgress();
    var mf = lsGet('d2r_mf', '—');
    var p = lsGet('d2r_players', '—');
    host.innerHTML =
      '<div class="v44-kpi"><b>' + c.pct + '%</b><span>Chronicle</span></div>' +
      '<div class="v44-kpi"><b>' + esc(String(g.pct || g.owned)) + '</b><span>Grail</span></div>' +
      '<div class="v44-kpi"><b>' + esc(String(mf)) + '</b><span>MF</span></div>' +
      '<div class="v44-kpi"><b>/p' + esc(String(p)) + '</b><span>Players</span></div>';
  }

  function renderSession() {
    ensureSessionTab();
    renderKpis();
    refreshStalenessUI();
    renderTzCard();
    renderForgeCard();
    renderChronicleCard();
    renderGrailCard();
    refreshDockPin();
  }
  window.V44 = window.V44 || {};
  window.V44.renderSession = renderSession;
  window.V44.setChroniclePin = setChroniclePin;
  window.V44.touchStash = touchStash;
  window.V44.BUILD = BUILD;

  // ── Hook switchTab ───────────────────────────────────────────────────────
  function hookSwitchTab() {
    if (typeof window.switchTab !== 'function') return;
    if (window.switchTab.__v44) return;
    var orig = window.switchTab;
    var wrapped = function (name) {
      orig(name);
      if (name === 'session') {
        try { renderSession(); } catch (e) {}
      }
      // keep dock pin fresh when visiting forge
      if (name === 'forge' || name === 'tools') {
        try { refreshDockPin(); refreshStalenessUI(); } catch (e) {}
      }
    };
    wrapped.__v44 = true;
    window.switchTab = wrapped;
  }

  // ── Intake review (post-commit undo/edit) ────────────────────────────────
  function diffMaps(before, after) {
    var keys = {};
    Object.keys(before || {}).forEach(function (k) { keys[k] = 1; });
    Object.keys(after || {}).forEach(function (k) { keys[k] = 1; });
    var rows = [];
    Object.keys(keys).sort().forEach(function (k) {
      var a = parseInt((before || {})[k], 10) || 0;
      var b = parseInt((after || {})[k], 10) || 0;
      if (a === b) return;
      rows.push({ k: k, before: a, after: b, delta: b - a });
    });
    return rows;
  }

  function showIntakeReview(kind, before, after, applyFn, revertFn) {
    var rows = diffMaps(before, after);
    if (!rows.length) return; // nothing changed

    var modal = $('v44-intake-modal');
    if (!modal) {
      modal = document.createElement('div');
      modal.id = 'v44-intake-modal';
      modal.innerHTML = '<div class="v44-modal" role="dialog" aria-modal="true" aria-labelledby="v44-intake-title">' +
        '<h3 id="v44-intake-title">Review intake</h3>' +
        '<p class="v44-modal-sub" id="v44-intake-sub"></p>' +
        '<div id="v44-intake-table-wrap"></div>' +
        '<div class="v44-modal-actions">' +
        '<button type="button" class="v44-btn ghost" id="v44-intake-undo">↩ Undo (restore before)</button>' +
        '<button type="button" class="v44-btn" id="v44-intake-edit">Apply edits</button>' +
        '<button type="button" class="v44-btn primary" id="v44-intake-keep">✓ Keep changes</button>' +
        '</div></div>';
      document.body.appendChild(modal);
      modal.addEventListener('click', function (e) {
        if (e.target === modal) modal.classList.remove('open');
      });
    }
    $('v44-intake-title').textContent = 'Review ' + kind + ' intake';
    $('v44-intake-sub').textContent = rows.length + ' change' + (rows.length === 1 ? '' : 's') +
      ' applied by vision. Confirm, edit counts, or undo before you trust Forge.';
    var wrap = $('v44-intake-table-wrap');
    wrap.innerHTML = '<table class="v44-diff-table"><thead><tr><th>Item</th><th>Before</th><th>Δ</th><th>After (edit)</th></tr></thead><tbody>' +
      rows.map(function (r, i) {
        var cls = r.delta > 0 ? 'up' : 'down';
        return '<tr data-i="' + i + '"><td>' + esc(r.k) + '</td><td class="same">' + r.before + '</td>' +
          '<td class="' + cls + '">' + (r.delta > 0 ? '+' : '') + r.delta + '</td>' +
          '<td><input type="number" min="0" step="1" data-key="' + esc(r.k) + '" value="' + r.after + '"></td></tr>';
      }).join('') + '</tbody></table>';

    modal.classList.add('open');
    var stateAfter = JSON.parse(JSON.stringify(after));

    function close() { modal.classList.remove('open'); }

    $('v44-intake-keep').onclick = function () {
      touchStash(kind === 'runes' ? 'runes' : kind === 'gems' ? 'gems' : kind === 'materials' ? 'materials' : 'vault');
      close();
      try { renderSession(); } catch (e) {}
    };
    $('v44-intake-undo').onclick = function () {
      if (typeof revertFn === 'function') revertFn(before);
      touchStash(kind === 'runes' ? 'runes' : kind === 'gems' ? 'gems' : kind === 'materials' ? 'materials' : 'vault');
      close();
      try { renderSession(); } catch (e) {}
    };
    $('v44-intake-edit').onclick = function () {
      var next = JSON.parse(JSON.stringify(before));
      wrap.querySelectorAll('input[data-key]').forEach(function (inp) {
        var k = inp.getAttribute('data-key');
        var v = parseInt(inp.value, 10);
        if (isFinite(v) && v > 0) next[k] = v;
        else delete next[k];
      });
      if (typeof applyFn === 'function') applyFn(next);
      touchStash(kind === 'runes' ? 'runes' : kind === 'gems' ? 'gems' : kind === 'materials' ? 'materials' : 'vault');
      close();
      try { renderSession(); } catch (e) {}
    };
  }

  function snapshotStash(key) {
    try {
      return JSON.parse(lsGet(key, '{}') || '{}') || {};
    } catch (e) { return {}; }
  }

  function wrapIntake(name, kind, storageKey, reloadFn) {
    var orig = window[name];
    if (typeof orig !== 'function') return;
    window[name] = async function () {
      var before = snapshotStash(storageKey);
      // also snapshot window.runeStash if present
      if (kind === 'runes' && window.runeStash && typeof window.runeStash === 'object') {
        before = JSON.parse(JSON.stringify(window.runeStash));
      }
      var args = arguments;
      var result = await orig.apply(this, args);
      var after = snapshotStash(storageKey);
      if (kind === 'runes' && window.runeStash && typeof window.runeStash === 'object') {
        after = JSON.parse(JSON.stringify(window.runeStash));
      }
      // Always stamp freshness when intake function finishes
      touchStash(kind === 'runes' ? 'runes' : kind === 'gems' ? 'gems' : kind === 'materials' ? 'materials' : 'vault');
      showIntakeReview(kind, before, after, function (next) {
        try {
          if (kind === 'runes' && window.runeStash) {
            // mutate in place so closure stays in sync
            Object.keys(window.runeStash).forEach(function (k) { delete window.runeStash[k]; });
            Object.keys(next).forEach(function (k) { window.runeStash[k] = next[k]; });
          }
          lsSet(storageKey, JSON.stringify(next));
          // trigger bible re-render helpers if present
          if (typeof window.renderRuneStash === 'function') window.renderRuneStash();
          if (typeof window.renderGemStash === 'function') window.renderGemStash();
          if (typeof window.renderMaterialStash === 'function') window.renderMaterialStash();
          if (typeof window.renderForge === 'function') window.renderForge();
          if (typeof window.persist === 'function') window.persist();
          // many builds use a global persist via assignment — force LS write is enough + reload soft
        } catch (e) {}
        if (typeof reloadFn === 'function') reloadFn();
      }, function (prev) {
        try {
          if (kind === 'runes' && window.runeStash) {
            Object.keys(window.runeStash).forEach(function (k) { delete window.runeStash[k]; });
            Object.keys(prev).forEach(function (k) { window.runeStash[k] = prev[k]; });
          }
          lsSet(storageKey, JSON.stringify(prev));
          if (typeof window.renderRuneStash === 'function') window.renderRuneStash();
          if (typeof window.renderGemStash === 'function') window.renderGemStash();
          if (typeof window.renderMaterialStash === 'function') window.renderMaterialStash();
          if (typeof window.renderForge === 'function') window.renderForge();
        } catch (e) {}
      });
      return result;
    };
  }

  function wrapIntakes() {
    wrapIntake('runeIntake', 'runes', 'd2r_runeStash');
    // gem intake may be named gemIntake
    if (typeof window.gemIntake === 'function') wrapIntake('gemIntake', 'gems', 'd2r_gemStash');
    // materialIntake
    if (typeof window.materialIntake === 'function') wrapIntake('materialIntake', 'materials', 'd2r_materialStash');
    // vault / grail photo intakes — stamp vault freshness if present
    ['vaultIntake', 'grailIntake', 'itemIntake'].forEach(function (n) {
      if (typeof window[n] === 'function') {
        var o = window[n];
        window[n] = async function () {
          var r = await o.apply(this, arguments);
          touchStash('vault');
          return r;
        };
      }
    });
  }

  // ── Default to Session when no hash / first run ──────────────────────────
  function maybeOpenSession() {
    var hash = (location.hash || '').replace(/^#/, '').trim();
    if (hash && hash !== 'session' && hash.indexOf('session/') !== 0) return;
    // Opt out: localStorage d2r_v44_defaultSession = '0'
    var prefer = lsGet('d2r_v44_defaultSession', '1');
    if (prefer === '0') return;
    var saved = lsGet('d2r_activeTab', '');
    // Respect a deliberate deep-link to another tab from last session
    if (!hash && saved && saved !== 'main' && saved !== 'session') return;
    setTimeout(function () {
      ensureSessionTab();
      restructureTabs();
      hookSwitchTab();
      if (window.switchTab) window.switchTab('session');
      else if (window.navClean) window.navClean('session');
    }, 180);
  }

  // ── Service worker ───────────────────────────────────────────────────────
  function registerSW() {
    if (!('serviceWorker' in navigator)) return;
    // only on http(s) same origin
    try {
      var path = '/d2r/v44/sw.js';
      navigator.serviceWorker.register(path, { scope: '/d2r/' }).catch(function () {});
    } catch (e) {}
  }

  // ── Cmd/Ctrl+K already exists; add "S" → session? avoid steal. Use Shift+S via ?
  function hotkeys() {
    document.addEventListener('keydown', function (e) {
      if (e.target && /^(INPUT|TEXTAREA|SELECT)$/i.test(e.target.tagName)) return;
      // Alt+S → session
      if (e.altKey && !e.metaKey && !e.ctrlKey && e.key.toLowerCase() === 's') {
        e.preventDefault();
        if (window.switchTab) window.switchTab('session');
      }
    });
  }

  // ── Init ─────────────────────────────────────────────────────────────────
  function init() {
    mountBuildBadge();
    ensureSessionTab();
    restructureTabs();
    enhanceProgressSnapshot();
    exposeCollect();
    hookSwitchTab();
    wrapIntakes();
    refreshDockPin();
    refreshStalenessUI();
    hotkeys();
    registerSW();
    maybeOpenSession();

    // periodic dock refresh (TZ/forge can change mid-session)
    setInterval(function () {
      try { refreshDockPin(); } catch (e) {}
    }, 60000);

    // If forge renders later, re-bind pin
    var tries = 0;
    var t = setInterval(function () {
      tries++;
      if (typeof window.forgeScan === 'function' || tries > 40) {
        clearInterval(t);
        refreshDockPin();
        wrapIntakes(); // late-bound intakes
      }
    }, 250);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    // bible is huge; scripts at end may still be defining switchTab — delay slightly
    setTimeout(init, 0);
    setTimeout(function () {
      hookSwitchTab();
      wrapIntakes();
      restructureTabs();
      refreshDockPin();
    }, 800);
  }
})();
