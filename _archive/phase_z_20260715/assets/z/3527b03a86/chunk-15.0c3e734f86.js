
(function(){
  window.D2R_BUILD = { id:'v688', name:'Task Force', date:'2026-07-14', note:'Mission brief · ops queue · battlefield' };
  function badge(){
    if (document.getElementById('v687-build-badge')) return;
    var el = document.createElement('div');
    el.id = 'v687-build-badge';
    el.title = 'D2R Bible build';
    el.textContent = 'v688 · Task Force · 2026-07-14';
    document.body.appendChild(el);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', badge);
  else badge();
})();
