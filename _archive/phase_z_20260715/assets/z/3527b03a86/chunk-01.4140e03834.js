
(function(){
  function loadFonts(){
    if (document.getElementById('gfont-css')) return;
    var l = document.createElement('link');
    l.id = 'gfont-css'; l.rel = 'stylesheet';
    l.href = 'https://fonts.googleapis.com/css2?family=Cinzel:wght@500;600;700&family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Inter:wght@400;500;600;700&display=swap';
    document.head.appendChild(l);
  }
  if (document.readyState === 'complete') loadFonts();
  else window.addEventListener('load', loadFonts);
})();
