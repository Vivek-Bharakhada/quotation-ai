export function registerServiceWorker() {
  if (process.env.NODE_ENV !== 'production' || !('serviceWorker' in navigator)) {
    return;
  }

  window.addEventListener('load', () => {
    const swUrl = `${process.env.PUBLIC_URL || ''}/service-worker.js`;

    navigator.serviceWorker
      .register(swUrl)
      .catch((error) => console.warn('Service worker registration failed', error));
  });
}
