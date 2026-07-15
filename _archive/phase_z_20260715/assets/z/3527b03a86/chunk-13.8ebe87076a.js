

(function(){
  function I(id,ico,name,note){ return '<div class="tlp-item" role="button" tabindex="0" onclick="window.toolsLegendJump(\''+id+'\')"><span class="tlp-ico">'+ico+'</span><span><b>'+name+'</b>'+(note?' <small>'+note+'</small>':'')+'</span></div>'; }
  function build(){
    if(document.getElementById('tools-legend-fab')) return;
    if(!document.getElementById('tab-tools')) return;
    var pop='<div class="tools-legend-pop" id="tools-legend-pop">'
      +'<span class="tlp-close" title="close" onclick="window.toolsLegendToggle()">✕</span>'
      +'<div class="tlp-h">🧭 Tools — map</div><div class="tlp-sub">Everything in this tab, grouped by what you\'re doing. Tap any row to jump to it.</div>'
      +'<div class="tlp-start" role="button" tabindex="0" onclick="window.toolsLegendJump(\'mule-vault-card\')">👉 <b>Start here — feed the engine.</b> 📸 Screenshot your loot into the <b>3 stashes</b>: Vault (items) · Runes · Gems. The Forge &amp; the AI tools read all three together.</div>'
      +'<div class="tlp-grp">📸 Feed the engine — the 3 stashes</div>'
      + I('mule-vault-card','🎒','The Vault — items','📸 photo → auto-files to mules')
      + I('rune-stash-card','ᛝ','Rune Stash','📸 photo → tally + cube-up')
      + I('gem-stash-card','💎','Gem Stash','📸 photo → tally + cube-up')
      + I('material-stash-card','🎲','Materials Stash','📸 uber / Sunder mats')
      +'<div class="tlp-grp">🤖 AI tools — flagship</div>'
      + I('ask-bible-card','🔮','Ask the AI — Diablo II Helper','Sonnet · reads your live stash')
      + I('ai-item-checker-card','🔬','AI Item Checker','magic/rare — keep or toss?')
      +'<div class="tlp-grp">🏆 The endgame — make it &amp; farm it</div>'
      + I('rw-chronicle-card','📜','Chronicle','the 100-runeword endgame goal · ✓ progress')
      + I('loot-filters-card','🎯','Loot Filters','copy → D2R · farm the bases you still need')
      +'<div class="tlp-grp">📊 Data &amp; reference</div>'
      + I('rw-bases-card','🔩','Best Runeword Bases','which base per word')
      + I('craft-workshop-card','🔨','Crafted Workshop','gem crafts by slot')
      + I('all-runewords-card','📖','All Runewords','the full DB')
      + I('horadric-recipe-card','🧊','Horadric Cube Recipes','filter · ✓ cubeable now')
      + I('item-values-card','💠','Trade Values','High → Trash')
      + I('hvf-card','⭐','High-Value Finds','off-grail best-of-best')
      + I('sunder-recipe-card','⚡','Sunder Renewal','recipe per charm')
      + I('item-rarity-card','🎨','Item Rarity &amp; Colours','what each colour means')
      + I('set-tracker-card','🎽','Item Set Tracker','set completion')
      +'</div>';
    var w=document.createElement('div');
    w.innerHTML='<button class="tools-legend-fab" id="tools-legend-fab" title="Tools map — what\'s here + where to start" onclick="window.toolsLegendToggle()">🧭</button>'+pop;
    while(w.firstChild) document.body.appendChild(w.firstChild);
  }
  window.toolsLegendToggle=function(){ var p=document.getElementById('tools-legend-pop'); if(p) p.classList.toggle('open'); };
  window.toolsLegendJump=function(id){
    var c=document.getElementById(id); if(!c) return;
    if(c.classList.contains('collapsed') && typeof window.toggleCardCollapse==='function') window.toggleCardCollapse(id);
    try{ c.scrollIntoView({behavior:'smooth',block:'start'}); }catch(e){ c.scrollIntoView(); }
    var p=document.getElementById('tools-legend-pop'); if(p) p.classList.remove('open');
  };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',build); else build();
})();
