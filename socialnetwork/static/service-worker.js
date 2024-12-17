const cacheName = 'app-cache-v1';
const assetsToCache = [
    '/',
    '/home.html',
    '/static/assets/css/main.css',
    '/static/app.js',
    '/static/images/icons/logo.png'
];

// Install event - caching assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(cacheName).then(cache => {
            console.log('Caching app assets');
            return cache.addAll(assetsToCache);
        })
    );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    const cacheWhitelist = [cacheName];
    event.waitUntil(
        caches.keys().then(keyList =>
            Promise.all(
                keyList.map(key => {
                    if (!cacheWhitelist.includes(key)) {
                        console.log('Deleting old cache: ', key);
                        return caches.delete(key);
                    }
                })
            )
        )
    );
});

// Push event - handle push notifications
self.addEventListener('push', event => {
    const data = event.data.json();  // Payload from FCM
    const title = data.notification.title;
    const options = {
        body: data.notification.body,
        icon: '/static/images/icons/logo.png',  // Your app's icon
        badge: '/static/images/icons/logo.png',  // Your app's badge icon
        data: { url: data.notification.click_action }  // Handle click action URL
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Notification click event - handle notification clicks
self.addEventListener('notificationclick', event => {
    event.notification.close();  // Close the notification
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
            // Open or focus the app window when notification is clicked
            for (const client of clientList) {
                if (client.url === event.notification.data.url && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(event.notification.data.url);
            }
        })
    );
});
