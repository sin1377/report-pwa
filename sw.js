var CACHE_NAME = 'report-archive-v2';
var urlsToCache = [
  '/report-pwa/',
  '/report-pwa/index.html',
  '/report-pwa/manifest.json',
  '/report-pwa/icon-48.png',
  '/report-pwa/icon-192.png',
  '/report-pwa/icon-512.png'
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(urlsToCache);
    })
  );
});

self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request).then(function(response) {
      // Cache hit - return response
      if (response) {
        return response;
      }
      // Clone the request
      var fetchRequest = event.request.clone();
      return fetch(fetchRequest).then(function(response) {
        // Check if valid response
        if(!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }
        // Clone the response
        var responseToCache = response.clone();
        caches.open(CACHE_NAME).then(function(cache) {
          cache.put(event.request, responseToCache);
        });
        return response;
      }).catch(function() {
        // Offline fallback - return cached index page for navigation requests
        if (event.request.mode === 'navigate') {
          return caches.match('/report-pwa/');
        }
        return new Response('Offline', {status: 503});
      });
    })
  );
});

self.addEventListener('activate', function(event) {
  var cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
