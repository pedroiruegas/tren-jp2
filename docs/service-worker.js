/**
 * TrenJP2 Service Worker
 * 
 * Estrategia de cache:
 * - App shell (HTML, CSS, JS, iconos): cache-first (cargan instantáneo, funcionan offline)
 * - API requests (fetch al backend): network-first (siempre intenta datos frescos,
 *   pero si no hay internet usa la última respuesta cacheada)
 */

const CACHE_VERSION = 'tren-jp2-v3';
const CACHE_API = 'tren-jp2-api-v3';

// Recursos que se precachean al instalar
const APP_SHELL = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  './apple-touch-icon.png',
  './favicon-32.png',
];

// === INSTALACIÓN ===
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => {
      return cache.addAll(APP_SHELL);
    }).then(() => self.skipWaiting())
  );
});

// === ACTIVACIÓN: limpiar caches viejos ===
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== CACHE_VERSION && key !== CACHE_API)
          .map((key) => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

// === FETCH: estrategia según tipo de petición ===
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Solo cachear GET requests
  if (event.request.method !== 'GET') {
    return;
  }
  
  // Peticiones a la API de Render: network-first
  if (url.hostname.includes('onrender.com')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Si la respuesta es válida, guardarla en cache
          if (response.ok) {
            const responseClone = response.clone();
            caches.open(CACHE_API).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // Si no hay red, intentar servir desde cache
          return caches.match(event.request).then((cached) => {
            if (cached) {
              return cached;
            }
            // Si no hay nada cacheado, devolver respuesta de error custom
            return new Response(
              JSON.stringify({
                offline: true,
                mensaje: 'Sin conexión',
                hay_tren: false,
                total_reportes_recientes: 0,
                ultimo_reporte: null
              }),
              {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
              }
            );
          });
        })
    );
    return;
  }
  
  // App shell y assets: cache-first
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        // Actualizar en background si hay red
        fetch(event.request).then((response) => {
          if (response.ok) {
            caches.open(CACHE_VERSION).then((cache) => {
              cache.put(event.request, response);
            });
          }
        }).catch(() => { /* sin red, ignorar */ });
        return cached;
      }
      
      // Si no está cacheado, ir a red
      return fetch(event.request).then((response) => {
        if (response.ok) {
          const responseClone = response.clone();
          caches.open(CACHE_VERSION).then((cache) => {
            cache.put(event.request, responseClone);
          });
        }
        return response;
      });
    })
  );
});
