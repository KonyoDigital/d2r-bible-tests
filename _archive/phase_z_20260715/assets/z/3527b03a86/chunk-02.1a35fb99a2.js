
(function(){
  var dockS = document.getElementById('dock-sliders');
  var dockP = document.getElementById('dock-presets');
  var header = document.querySelector('.header');
  if(!dockS || !dockP || !header) return;
  function divider(){ var d = document.createElement('span'); d.className = 'dock-div'; return d; }
  // Relocate the two slider-groups (MF + P#) and the eff-unique readout.
  var groups = header.querySelectorAll('.header-top .slider-group');
  if(groups[0]) dockS.appendChild(groups[0]);
  if(groups[0] && groups[1]) dockS.appendChild(divider());
  if(groups[1]) dockS.appendChild(groups[1]);
  var eff = header.querySelector('.eff-readout');
  if(eff){ dockS.appendChild(divider()); dockS.appendChild(eff); }
  // Relocate the MF quick-set preset bar (label + chips + exact input); the trailing
  // keyboard-hint caption span is dropped to keep the dock clean.
  var bar = header.querySelector('.mf-preset-bar');
  if(bar){
    Array.prototype.slice.call(bar.children).forEach(function(k){
      if(k.tagName === 'SPAN' && !k.classList.contains('mf-preset-label')) return;
      dockP.appendChild(k);
    });
    if(bar.parentNode) bar.parentNode.removeChild(bar);
  }
  // Relocate the masthead tagline to the bottom dock (top caption row); the element
  // keeps its class + verbatim text, so its smoke assertions still pass.
  var tagline = header.querySelector('.masthead .masthead-tagline');
  var dockT = document.getElementById('dock-tagline');
  if(tagline && dockT){ dockT.appendChild(tagline); }
})();
