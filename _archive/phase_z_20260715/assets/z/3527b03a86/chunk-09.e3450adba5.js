
(function(){
  'use strict';
  var box = null;
  function ensure(){
    if (box) return box;
    box = document.createElement('div');
    box.id = 'gild-lightbox';
    box.setAttribute('aria-hidden','true');
    box.setAttribute('role','dialog');
    box.innerHTML = '<button class="glb-close" aria-label="close (Esc)">\u2715 close</button>'
      + '<figure class="glb-frame"><img class="glb-img" alt=""><figcaption class="glb-cap"></figcaption></figure>'
      + '<div class="glb-hint">click anywhere or press Esc to close</div>';
    box.addEventListener('click', closeBox);
    document.body.appendChild(box);
    return box;
  }
  function openBox(src, cap, alt){
    var b = ensure();
    var img = b.querySelector('.glb-img');
    img.src = src; img.alt = alt || cap || 'screenshot';
    b.querySelector('.glb-cap').textContent = cap || '';
    b.classList.add('show'); b.setAttribute('aria-hidden','false');
    document.documentElement.classList.add('glb-lock');
  }
  function closeBox(){
    if (!box) return;
    box.classList.remove('show'); box.setAttribute('aria-hidden','true');
    document.documentElement.classList.remove('glb-lock');
  }
  // CAPTURE phase: the gallery slots live inside .btg-card[onclick] (routes to the
  // bind card) — capture beats the inline onclick so a screenshot click means
  // "view HD", never "route" (same capture technique as the keyword router).
  document.addEventListener('click', function(e){
    var t = e.target;
    if (!t || !t.closest) return;
    var img = t.closest('.su-banner-slot.filled img') || ((t.tagName === 'IMG' && t.closest('.su-banner-slot.filled')) ? t : null);
    if (!img) return;
    e.preventDefault(); e.stopPropagation();
    var fig = img.closest('.su-banner-slot');
    var cap = fig ? ((fig.querySelector('figcaption') || {}).textContent || '').trim() : '';
    openBox(img.src, cap, img.alt);
  }, true);
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape') closeBox(); });
  window._gildLightboxOpen = openBox;
  window._gildLightboxClose = closeBox;
})();
