const APP_CACHE = 'quotation-ai-app-v2';
const RUNTIME_CACHE = 'quotation-ai-runtime-v2';
const APP_SHELL = [
  '/',
  '/index.html',
  '/manifest.json',
  '/favicon.ico',
  '/logo192.png',
  '/logo512.png',
  '/hero.png',
  '/kohler_cover.jpg',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(APP_CACHE).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  const keepCaches = [APP_CACHE, RUNTIME_CACHE];

  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.map((key) => (keepCaches.includes(key) ? Promise.resolve() : caches.delete(key))))
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') {
    return;
  }

  const url = new URL(request.url);
  const isSameOrigin = url.origin === self.location.origin;
  const isStaticAsset =
    isSameOrigin &&
    ['style', 'script', 'image', 'font', 'document'].includes(request.destination);

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const cloned = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => cache.put('/index.html', cloned));
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          return cached || caches.match('/index.html');
        })
    );
    return;
  }

  if (isStaticAsset) {
    event.respondWith(
      caches.match(request).then((cached) => {
        const networkFetch = fetch(request)
          .then((response) => {
            if (response && response.status === 200) {
              const cloned = response.clone();
              caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, cloned));
            }
            return response;
          })
          .catch(() => cached);

        return cached || networkFetch;
      })
    );
  }
});
