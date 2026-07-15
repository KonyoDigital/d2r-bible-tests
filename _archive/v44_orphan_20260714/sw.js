/* v44 service worker — offline shell + last-known bible + long-cache art */
const CACHE = 'd2r-bible-v44-1';
const SHELL = [
  '/d2r/',
  '/d2r/index.html',
  '/d2r/v44/v44-upgrade.css',
  '/d2r/v44/v44-upgrade.js',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL).catch(() => {})).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  // Never cache AI/API calls
  if (url.pathname.startsWith('/api/')) return;

  // Art: cache-first (immutable-ish)
  if (url.pathname.indexOf('/d2r/art/') === 0) {
    event.respondWith(
      caches.open(CACHE).then(async (cache) => {
        const hit = await cache.match(req);
        if (hit) return hit;
        try {
          const res = await fetch(req);
          if (res && res.ok) cache.put(req, res.clone());
          return res;
        } catch (e) {
          return hit || Response.error();
        }
      })
    );
    return;
  }

  // HTML + v44 assets: network-first, fall back to cache (offline farm laptop)
  if (
    url.pathname === '/d2r/' ||
    url.pathname === '/d2r/index.html' ||
    url.pathname.indexOf('/d2r/v44/') === 0
  ) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res && res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => caches.match(req).then((h) => h || caches.match('/d2r/')))
    );
  }
});
