import axios from 'axios';

const api = axios.create({
  baseURL: '',  // Uses Vite proxy in dev, same-origin in prod
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auto-recover stale participant ID after DB reset
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 404 && error.response?.data?.detail === 'participant_not_found') {
      localStorage.removeItem('participantId');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export default api;
