/* D2R Bible Phase-Z SW — auto from deploy */
const ZSET = '3527b03a86';
const CACHE = 'd2r-z-' + ZSET;
self.addEventListener('install', (e) => { self.skipWaiting(); });
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k.startsWith('d2r-z-') && k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});
self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/api/')) return;
  const isHtml = url.pathname === '/d2r/' || url.pathname === '/d2r/index.html';
  if (isHtml) {
    e.respondWith(fetch(req).catch(() => caches.match(req)));
    return;
  }
  const cacheable = url.pathname.startsWith('/d2r/assets/z/') || url.pathname.startsWith('/d2r/art/');
  if (!cacheable) return;
  e.respondWith(
    caches.open(CACHE).then(async (cache) => {
      const hit = await cache.match(req);
      if (hit) return hit;
      try {
        const res = await fetch(req);
        if (res && res.ok) cache.put(req, res.clone());
        return res;
      } catch (err) {
        return hit || Response.error();
      }
    })
  );
});
