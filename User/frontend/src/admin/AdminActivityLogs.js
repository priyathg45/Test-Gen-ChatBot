import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { CHAT_API_URL } from '../config';
import './AdminLayout.css';

const AdminActivityLogs = () => {
  const { token } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterUserId, setFilterUserId] = useState('');
  const [filterAction, setFilterAction] = useState('');

  const loadLogs = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (filterUserId) params.set('user_id', filterUserId);
    if (filterAction) params.set('action', filterAction);
    fetch(`${CHAT_API_URL}/admin/activity-logs?${params.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) setLogs(data.logs || []);
        else setError(data.error || 'Failed to load logs');
      })
      .catch((err) => setError(err.message || 'Request failed'))
      .finally(() => setLoading(false));
  };

  // Initial load only; "Apply" button triggers loadLogs() with current filters
  useEffect(() => {
    loadLogs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (error) return <div className="alert alert-danger">{error}</div>;

  return (
    <>
      <h1 className="admin-page-title">Activity Logs</h1>
      <div className="admin-card">
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Filter by user ID"
            value={filterUserId}
            onChange={(e) => setFilterUserId(e.target.value)}
            className="form-control"
            style={{ maxWidth: 200 }}
          />
          <select
            value={filterAction}
            onChange={(e) => setFilterAction(e.target.value)}
            className="form-control"
            style={{ maxWidth: 180 }}
          >
            <option value="">All actions</option>
            <option value="login">Login</option>
            <option value="logout">Logout</option>
            <option value="chat">Chat</option>
            <option value="register">Register</option>
            <option value="admin_view_users">Admin: View users</option>
            <option value="admin_view_user">Admin: View user</option>
            <option value="admin_view_history">Admin: View history</option>
            <option value="admin_view_logs">Admin: View logs</option>
            <option value="admin_update_user">Admin: Update user</option>
          </select>
          <button type="button" className="btn btn-primary" onClick={loadLogs}>
            Apply
          </button>
        </div>
        {loading ? (
          <p>Loading logs...</p>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>User ID</th>
                <th>Action</th>
                <th>Resource</th>
                <th>Details</th>
                <th>IP</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{log.timestamp ? new Date(log.timestamp).toLocaleString() : '–'}</td>
                  <td><code style={{ fontSize: '0.85rem' }}>{log.user_id || '–'}</code></td>
                  <td>{log.action}</td>
                  <td>{log.resource || '–'}</td>
                  <td>{log.details && Object.keys(log.details).length ? JSON.stringify(log.details) : '–'}</td>
                  <td>{log.ip || '–'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {!loading && logs.length === 0 && <p className="text-muted mb-0">No logs found.</p>}
      </div>
    </>
  );
};

export default AdminActivityLogs;
