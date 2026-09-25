// J.A.R.V.I.S. Service Worker v3
// 策略：HTML 走「网络优先」（永远最新），静态资源走「缓存优先」（秒开）
var CACHE_NAME = 'jarvis-v3';
var STATIC_ASSETS = [
  '/report-pwa/manifest.json',
  '/report-pwa/icon-48.png',
  '/report-pwa/icon-192.png',
  '/report-pwa/icon-512.png'
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(STATIC_ASSETS);
    }).then(function() {
      // 新版本 SW 立即接管，不再等所有标签页关闭
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            // 清掉所有旧缓存（包括顽固的 v2）
            return caches.delete(cacheName);
          }
        })
      );
    }).then(function() {
      // 立即控制所有已打开的客户端
      return self.clients.claim();
    })
  );
});

self.addEventListener('message', function(event) {
  if (event.data && event.data.action === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

self.addEventListener('fetch', function(event) {
  var request = event.request;

  // 页面导航请求：网络优先，失败才用缓存（离线兜底）
  if (request.mode === 'navigate' || (request.method === 'GET' && request.headers.get('accept') && request.headers.get('accept').indexOf('text/html') !== -1)) {
    event.respondWith(
      fetch(request).then(function(response) {
        var responseToCache = response.clone();
        caches.open(CACHE_NAME).then(function(cache) {
          cache.put(request, responseToCache);
        });
        return response;
      }).catch(function() {
        return caches.match(request).then(function(cached) {
          if (cached) return cached;
          return caches.match('/report-pwa/');
        });
      })
    );
    return;
  }

  // 静态资源：缓存优先
  event.respondWith(
    caches.match(request).then(function(cached) {
      if (cached) return cached;
      return fetch(request).then(function(response) {
        if (response && response.status === 200) {
          var responseToCache = response.clone();
          caches.open(CACHE_NAME).then(function(cache) {
            cache.put(request, responseToCache);
          });
        }
        return response;
      });
    })
  );
});
