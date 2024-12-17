// Import and configure Firebase
importScripts('https://www.gstatic.com/firebasejs/9.6.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/9.6.1/firebase-messaging.js');

const firebaseConfig = {
    apiKey: "AIzaSyDApv6AJ5uG0IMyioE7bYJHRtUWHfvomTE",
    authDomain: "socialnetwork-6b6b4.firebaseapp.com",
    projectId: "socialnetwork-6b6b4",
    storageBucket: "socialnetwork-6b6b4.appspot.com",
    messagingSenderId: "1009355837533",
    appId: "1:1009355837533:web:b8544c848e99315bfafdb4",
    measurementId: "G-BZFPYS1RZF"
};

firebase.initializeApp(firebaseConfig);

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
    console.log('Received background message', payload);

    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: payload.notification.icon
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
});
