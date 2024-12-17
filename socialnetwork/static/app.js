// Service Worker Registration for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/service-worker.js')
            .then(reg => {
                console.log('Service Worker registered with scope: ', reg.scope);
                // Call subscribeUserToPush to subscribe users after service worker registration
                subscribeUserToPush();
            })
            .catch(err => {
                console.log('Service Worker registration failed: ', err);
            });
    });
}

// PWA Installation Handling
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();  // Prevent automatic prompt
    deferredPrompt = e;  // Store event for triggering later
    const installButton = document.getElementById('install-button');
    installButton.style.display = 'block';  // Display custom install button

    installButton.addEventListener('click', () => {
        deferredPrompt.prompt();  // Show install prompt
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('User accepted the install prompt');
            } else {
                console.log('User dismissed the install prompt');
            }
            deferredPrompt = null;
        });
    });
});

// Network Status Updates
function updateOnlineStatus() {
    const status = navigator.onLine ? 'Online' : 'Offline';
    document.getElementById('status').textContent = `Status: ${status}`;
}
window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);

// Push Notifications Subscription
function subscribeUserToPush() {
    navigator.serviceWorker.ready.then((reg) => {
        reg.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: 'BOaBQgBigg4La1jC_SqDz23cFnWLPV7kjTBTqEhHQU5dGxk9f2T9CiBwAUrCJ7U0chK1bEHjOk-qy8Y_c6nXtHY'  // Replace with Firebase's public VAPID key
        })
            .then(sub => {
                console.log('User is subscribed to push notifications:', sub);
                // You can send this subscription object to your server
            })
            .catch(err => {
                console.log('Failed to subscribe user to push notifications', err);
            });
    });
}

// Firebase Initialization and Push Handling
const firebaseConfig = {
    apiKey: "AIzaSyDApv6AJ5uG0IMyioE7bYJHRtUWHfvomTE",
    authDomain: "socialnetwork-6b6b4.firebaseapp.com",
    projectId: "socialnetwork-6b6b4",
    storageBucket: "socialnetwork-6b6b4.appspot.com",
    messagingSenderId: "1009355837533",
    appId: "1:1009355837533:web:b8544c848e99315bfafdb4",
};
firebase.initializeApp(firebaseConfig);

const messaging = firebase.messaging();
messaging.getToken({ vapidKey: 'BOaBQgBigg4La1jC_SqDz23cFnWLPV7kjTBTqEhHQU5dGxk9f2T9CiBwAUrCJ7U0chK1bEHjOk-qy8Y_c6nXtHY' }).then((currentToken) => {
    if (currentToken) {
        console.log('Firebase token received:', currentToken);
        // Send token to the server to save it for later use
    } else {
        console.log('No registration token available. Request permission to generate one.');
    }
}).catch((err) => {
    console.error('An error occurred while retrieving token. ', err);
});

// Handle Incoming Push Messages
messaging.onMessage((payload) => {
    console.log('Message received: ', payload);
    // Display notification or alert based on message data
});

// Fetch Data for UI Updates
async function fetchData() {
    const response = await fetch('/api/data');
    const data = await response.json();
    document.getElementById('data-display').innerText = JSON.stringify(data);
}
fetchData();
