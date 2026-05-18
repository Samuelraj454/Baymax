// Dynamically resolve backend endpoint: local vs. cloud fallback
const defaultBackend = import.meta.env.VITE_API_URL || 'https://baymax-3.onrender.com';
let activeUrl = localStorage.getItem('__active_api_url') || defaultBackend;

// If we are browsing on a remote host (like Render), try to detect a running local backend
if (!['localhost', '127.0.0.1'].includes(window.location.hostname)) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 1200);

  fetch('http://localhost:8000/health', { signal: controller.signal })
    .then(res => res.json())
    .then(data => {
      clearTimeout(timeoutId);
      if (data && data.status === 'online') {
        console.log('Local backend detected! Routing queries to http://localhost:8000');
        localStorage.setItem('__active_api_url', 'http://localhost:8000');
        if (activeUrl !== 'http://localhost:8000') {
          window.location.reload();
        }
      } else {
        localStorage.setItem('__active_api_url', defaultBackend);
      }
    })
    .catch(() => {
      clearTimeout(timeoutId);
      console.log('Local backend not active. Using cloud backend:', defaultBackend);
      if (activeUrl !== defaultBackend) {
        localStorage.setItem('__active_api_url', defaultBackend);
        window.location.reload();
      }
    });
} else {
  // If browsing locally, always lock to local backend
  activeUrl = 'http://localhost:8000';
}

export const API_BASE_URL = activeUrl;
