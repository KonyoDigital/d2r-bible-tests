/* D2R Bible Phase-Z SW — cache hashed assets only; HTML always network-first */
const ZSET = '3527b03a86';
const CACHE = 'd2r-z-' + ZSET;
const ASSET_PREFIX = '/d2r/assets/z/' + ZSET + '/';
const ART_PREFIX = '/d2r/art/';

self.addEventListener('install', (e) => {
  self.skipWaiting();
});
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
  // never cache APIs
  if (url.pathname.startsWith('/api/')) return;
  // HTML shell: network-first (v657 anti-ghost)
  if (
    url.pathname === '/d2r/' ||
    url.pathname === '/d2r/index.html' ||
    url.pathname.endsWith('/bible.html')
  ) {
    e.respondWith(
      fetch(req)
        .then((res) => res)
        .catch(() => caches.match(req))
    );
    return;
  }
  // hashed assets + art: cache-first
  if (url.pathname.startsWith(ASSET_PREFIX) || url.pathname.startsWith(ART_PREFIX) || url.pathname.startsWith('/d2r/art/perf/')) {
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
  }
});
