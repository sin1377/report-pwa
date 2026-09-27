// J.A.R.V.I.S. Service Worker v4 — 多源容灾版
// 策略：
//   - index.html: 网络优先（8秒超时快速回退缓存，避免白屏等待）
//   - data.js:    永远网络优先、绝不缓存（保证数据实时性）
//   - 静态资源:   缓存优先（秒开）
var CACHE_NAME = 'jarvis-v4';
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
            return caches.delete(cacheName);
          }
        })
      );
    }).then(function() {
      return self.clients.claim();
    })
  );
});

self.addEventListener('message', function(event) {
  if (event.data && event.data.action === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// 带超时的 fetch
function fetchWithTimeout(request, ms) {
  return new Promise(function(resolve, reject) {
    var ctl = setTimeout(function(){ reject(new Error('timeout')); }, ms);
    fetch(request).then(function(r){ clearTimeout(ctl); resolve(r); },
                        function(e){ clearTimeout(ctl); reject(e); });
  });
}

self.addEventListener('fetch', function(event) {
  var request = event.request;
  var url = new URL(request.url);

  // data.js：数据文件，永远走网络（多源由页面层竞速），SW 不缓存不拦截
  if (url.pathname.indexOf('data.js') !== -1) {
    return; // 直接放行，不 respondWith
  }

  // 页面导航请求：网络优先 + 8秒超时回退
  if (request.mode === 'navigate' || (request.method === 'GET' && request.headers.get('accept') && request.headers.get('accept').indexOf('text/html') !== -1)) {
    event.respondWith(
      fetchWithTimeout(request, 8000).then(function(response) {
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
