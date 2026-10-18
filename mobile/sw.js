// mobile/sw.js
// Service Worker untuk Precision Palm Mobile Edge PWA
// Offline-First Caching Strategy (Termasuk Pustaka EXIF & Aset Kamera)

const CACHE_NAME = 'precision-palm-mobile-v2.1';
const STATIC_ASSETS = [
  '/mobile/',
  '/mobile/index.html',
  '/mobile/manifest.json',
  '/mobile/js/mobile_camera.js',
  '/mobile/js/mobile_db.js',
  '/mobile/js/mobile_gps.js',
  '/static/img/sawit_drone.jpg',
  'https://cdn.tailwindcss.com',
  'https://cdn.jsdelivr.net/npm/piexifjs@1.0.6/piexif.min.js',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap'
];

// Install Event: Pre-cache seluruh aset utama agar halaman & injeksi EXIF bekerja tanpa sinyal
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[PWA SW] Pre-caching core offline assets v2.0');
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('[PWA SW] Pre-cache notice:', err);
      });
    })
  );
  self.skipWaiting();
});

// Activate Event: Bersihkan cache versi lama
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch Event: Network-First untuk API (/api/), Stale-While-Revalidate untuk Aset Statis
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Jika request menuju endpoint API di app.py
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(
          JSON.stringify({
            success: false,
            offline: true,
            message: 'Mode Offline: Data diamankan di dalam buffer lokal IndexedDB perangkat.'
          }),
          { headers: { 'Content-Type': 'application/json' } }
        );
      })
    );
    return;
  }

  // Untuk halaman /mobile/ dan pustaka statis: utamakan Cache agar instan saat tanpa sinyal
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200 && event.request.method === 'GET') {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return networkResponse;
        })
        .catch(() => cachedResponse);

      return cachedResponse || fetchPromise;
    })
  );
});