/* Service worker do painel: permite instalar no celular. Não guarda dados da API
   em cache (sempre vem do servidor); só os ícones, para abrir mais rápido. */
const CACHE = "bussola-v1";
const ESTATICOS = ["/img/app/icone-192.png", "/img/app/icone-512.png"];

self.addEventListener("install", (ev) => {
  ev.waitUntil(caches.open(CACHE).then((c) => c.addAll(ESTATICOS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (ev) => {
  ev.waitUntil(caches.keys().then((chaves) => Promise.all(chaves.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (ev) => {
  const url = new URL(ev.request.url);
  if (ev.request.method !== "GET" || url.origin !== location.origin || url.pathname.startsWith("/api/")) return;
  if (ESTATICOS.includes(url.pathname)) {
    ev.respondWith(caches.match(ev.request).then((r) => r || fetch(ev.request)));
  }
});
