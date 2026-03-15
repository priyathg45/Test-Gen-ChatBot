import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { CHAT_API_URL } from '../config';
import './AdminLayout.css';

const AdminUserDetail = () => {
  const { userId } = useParams();
  const { token } = useAuth();
  const [user, setUser] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedSession, setSelectedSession] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const fetchUser = async () => {
      try {
        const res = await fetch(`${CHAT_API_URL}/admin/users/${userId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (!cancelled && data.success) setUser(data.user);
        else if (!data.success) setError(data.error || 'User not found');
      } catch (err) {
        if (!cancelled) setError(err.message || 'Request failed');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchUser();
    return () => { cancelled = true; };
  }, [userId, token]);

  useEffect(() => {
    if (!userId) return;
    let cancelled = false;
    const fetchSessions = async () => {
      try {
        const res = await fetch(`${CHAT_API_URL}/admin/users/${userId}/sessions`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (!cancelled && data.success) setSessions(data.sessions || []);
      } catch (_) {}
    };
    fetchSessions();
    return () => { cancelled = true; };
  }, [userId, token]);

  useEffect(() => {
    if (!userId || !selectedSession) {
      setHistory([]);
      return;
    }
    let cancelled = false;
    const fetchHistory = async () => {
      try {
        const res = await fetch(
          `${CHAT_API_URL}/admin/users/${userId}/sessions/${encodeURIComponent(selectedSession)}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        const data = await res.json();
        if (!cancelled && data.success) setHistory(data.history || []);
      } catch (_) {}
    };
    fetchHistory();
    return () => { cancelled = true; };
  }, [userId, selectedSession, token]);

  if (error) return <div className="alert alert-danger">{error}</div>;
  if (loading || !user) return <p>Loading...</p>;

  return (
    <>
      <h1 className="admin-page-title">
        <Link to="/admin/users" className="text-secondary" style={{ fontSize: '1rem', marginRight: '0.5rem' }}>← Users</Link>
        User: {user.email}
      </h1>
      <div className="admin-card">
        <h3>Profile</h3>
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>Full Name:</strong> {user.full_name || '–'}</p>
        <p><strong>Role:</strong> <span className={`admin-badge role-${user.role}`}>{user.role}</span></p>
        <p><strong>Created:</strong> {user.created_at ? new Date(user.created_at).toLocaleString() : '–'}</p>
      </div>
      <div className="admin-card">
        <h3>Chat Sessions</h3>
        <p>Select a session to view chat history.</p>
        {sessions.length === 0 ? (
          <p className="text-muted">No chat sessions for this user.</p>
        ) : (
          <ul className="list-group list-group-flush" style={{ listStyle: 'none', paddingLeft: 0 }}>
            {sessions.map((s) => (
              <li key={s.session_id} style={{ borderBottom: '1px solid #eee', padding: '0.5rem 0' }}>
                <button
                  type="button"
                  className="btn btn-sm btn-outline-primary me-2"
                  onClick={() => setSelectedSession(selectedSession === s.session_id ? null : s.session_id)}
                >
                  {selectedSession === s.session_id ? 'Hide' : 'View'} history
                </button>
                <span className="text-muted">{s.session_id}</span>
                <span className="ms-2">({s.message_count} messages)</span>
                {s.last_message_at && (
                  <span className="ms-2 text-muted">{new Date(s.last_message_at).toLocaleString()}</span>
                )}
              </li>
            ))}
          </ul>
        )}
        {selectedSession && history.length > 0 && (
          <div className="mt-4">
            <h4>Conversation</h4>
            <div style={{ maxHeight: 400, overflow: 'auto', border: '1px solid #eee', borderRadius: 4, padding: '0.75rem' }}>
              {history.map((msg, i) => (
                <div key={i} style={{ marginBottom: '0.75rem' }}>
                  <strong>{msg.role === 'user' ? 'User' : 'Assistant'}:</strong>
                  <div style={{ whiteSpace: 'pre-wrap', marginLeft: '0.5rem' }}>{msg.content}</div>
                  {msg.timestamp && (
                    <small className="text-muted">{new Date(msg.timestamp).toLocaleString()}</small>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default AdminUserDetail;
