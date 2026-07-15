
(function() {
  'use strict';
  // v42: TZ countdown — D2R Terror Zones rotate every hour on the hour (UTC-aligned in-game).
  // We show MM:SS until next rotation (local clock approximation).
  const W = document.getElementById('v42-tz-countdown');
  if (!W) return;
  const TIME_EL = W.querySelector('.v42-tz-time');

  // User can toggle visibility — persist in localStorage
  const VIS_KEY = 'd2r_v42_tz_visible';
  function isVisible() {
    const v = localStorage.getItem(VIS_KEY);
    return v === null ? true : v === '1';  // default: visible
  }
  function setVisible(v) {
    try { localStorage.setItem(VIS_KEY, v ? '1' : '0'); } catch(e){}
    W.classList.toggle('show', !!v);
  }

  // Visibility is toggled from the ⌘K command palette (window._v42_toggleTZCountdown);
  // the badge itself is pointer-events:none so it never intercepts clicks on page content.

  function update() {
    const now = new Date();
    const m = now.getMinutes();
    const s = now.getSeconds();
    const remMin = 59 - m;
    const remSec = 60 - s;
    const totalSecRem = remMin * 60 + remSec;
    const mm = Math.floor(totalSecRem / 60);
    const ss = totalSecRem % 60;
    if (TIME_EL) TIME_EL.textContent = `${String(mm).padStart(2,'0')}:${String(ss).padStart(2,'0')}`;
    W.classList.toggle('imminent', totalSecRem <= 120);  // last 2min: pulse
  }

  // Wait for DOMReady to apply visibility
  function init() {
    setVisible(isVisible());
    update();
    setInterval(update, 1000);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose toggle for palette action
  window._v42_toggleTZCountdown = function() {
    setVisible(!isVisible());
  };
})();
