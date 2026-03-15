/**
 * API base URL. Default: backend on port 5000 (direct connection; CORS is enabled on backend).
 * Set REACT_APP_CHAT_API_URL in .env to override. Use '' or '/api' to use the dev proxy instead.
 */
export const CHAT_API_URL =
  process.env.REACT_APP_CHAT_API_URL !== undefined && process.env.REACT_APP_CHAT_API_URL !== ''
    ? process.env.REACT_APP_CHAT_API_URL
    : 'http://localhost:5000';
