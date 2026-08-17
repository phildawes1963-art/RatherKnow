import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { API, readSessions } from './mirrorTheme';

const TOKEN_KEY = 'rk.token';
const AuthContext = createContext(null);

export const getToken = () => localStorage.getItem(TOKEN_KEY);

export function authHeaders(extra = {}) {
  const token = getToken();
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

export function formatApiErrorDetail(detail) {
  if (detail == null) return 'Something went wrong. Please try again.';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((e) => (e && typeof e.msg === 'string' ? e.msg : '')).filter(Boolean).join(' ');
  if (typeof detail.msg === 'string') return detail.msg;
  return String(detail);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // null = checking, false = anonymous, object = signed in

  const claimLocal = useCallback(async () => {
    const ids = Object.values(readSessions());
    if (ids.length === 0) return;
    await fetch(`${API}/api/auth/claim`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ session_ids: ids }),
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!getToken()) {
      setUser(false);
      return;
    }
    (async () => {
      try {
        const res = await fetch(`${API}/api/auth/me`, { headers: authHeaders() });
        if (!res.ok) throw new Error();
        const data = await res.json();
        setUser(data.user);
      } catch {
        localStorage.removeItem(TOKEN_KEY);
        setUser(false);
      }
    })();
  }, []);

  const authenticate = async (path, body) => {
    const res = await fetch(`${API}/api/auth/${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(formatApiErrorDetail(data.detail));
    localStorage.setItem(TOKEN_KEY, data.access_token);
    setUser(data.user);
    await claimLocal();
    return data.user;
  };

  const register = (body) => authenticate('register', body);
  const login = (body) => authenticate('login', body);

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(false);
  };

  return (
    <AuthContext.Provider value={{ user, register, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
