// 轻量 Service Worker：支持 PWA 安装与离线壳层，但不缓存任何 /api 请求。
const CACHE = 'scenic-ai-v1'

self.addEventListener('install', (event) => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))),
    ),
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  const req = event.request
  if (req.method !== 'GET') return
  const url = new URL(req.url)
  // 同源且非 API：静态资源走 stale-while-revalidate
  if (url.origin === self.location.origin && !url.pathname.startsWith('/api')) {
    if (req.mode === 'navigate') {
      // 导航请求：网络优先，失败回退缓存首页
      event.respondWith(
        fetch(req).catch(() => caches.match('/index.html').then((r) => r || fetch(req))),
      )
      return
    }
    event.respondWith(
      caches.open(CACHE).then(async (cache) => {
        const cached = await cache.match(req)
        const network = fetch(req)
          .then((res) => {
            if (res && res.status === 200) cache.put(req, res.clone())
            return res
          })
          .catch(() => cached)
        return cached || network
      }),
    )
    return
  }
  // 其余（含 /api 与跨域）直接走网络，不缓存
  return
})
