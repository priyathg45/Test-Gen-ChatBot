/**
 * API client: builds URL, logs in dev, handles errors so auth shows clear messages.
 */
import { CHAT_API_URL } from '../config';

const getBase = () => (CHAT_API_URL || '').replace(/\/$/, '');
const buildUrl = (path) => `${getBase()}${path.startsWith('/') ? path : '/' + path}`;

const isDev = process.env.NODE_ENV !== 'production';

export async function apiFetch(path, options = {}) {
  const url = buildUrl(path);
  if (isDev) {
    console.log(`[API] ${options.method || 'GET'} ${url}`);
  }
  let res;
  const headers = { ...options.headers };
  if (options.body != null && typeof options.body === 'string' && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  try {
    res = await fetch(url, { ...options, headers });
  } catch (err) {
    if (isDev) console.error('[API] Network error:', err);
    const base = getBase() || 'http://localhost:5000';
    throw new Error(
      `Cannot reach the backend at ${base}. Start it in a separate terminal: cd backend, then .\\venv\\Scripts\\activate, then python -m src.api.app. Wait until you see "Running on http://0.0.0.0:5000". Then open ${base}/health in your browser to confirm.`
    );
  }
  if (isDev) {
    console.log(`[API] ${res.status} ${path}`);
  }
  let data = null;
  const contentType = res.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    try {
      data = await res.json();
    } catch (_) {
      throw new Error('Invalid response from server.');
    }
  }
  if (!res.ok) {
    const msg = data?.error || data?.message || `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return data;
}

export async function apiPost(path, body, token = null) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  return apiFetch(path, { method: 'POST', body: JSON.stringify(body), headers });
}

export async function apiGet(path, token = null) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  return apiFetch(path, { method: 'GET', headers });
}

export async function apiPut(path, body, token = null) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  return apiFetch(path, { method: 'PUT', body: JSON.stringify(body), headers });
}
