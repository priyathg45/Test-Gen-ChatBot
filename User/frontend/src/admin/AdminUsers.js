import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { CHAT_API_URL } from '../config';
import './AdminLayout.css';

const AdminUsers = () => {
  const { token } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    const fetchUsers = async () => {
      try {
        const res = await fetch(`${CHAT_API_URL}/admin/users`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (!cancelled && data.success) {
          setUsers(data.users || []);
        } else if (!data.success) {
          setError(data.error || 'Failed to load users');
        }
      } catch (err) {
        if (!cancelled) setError(err.message || 'Request failed');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchUsers();
    return () => { cancelled = true; };
  }, [token]);

  if (loading) return <p>Loading users...</p>;
  if (error) return <div className="alert alert-danger">{error}</div>;

  return (
    <>
      <h1 className="admin-page-title">Users</h1>
      <div className="admin-card">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Full Name</th>
              <th>Role</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.email}</td>
                <td>{u.full_name || '–'}</td>
                <td>
                  <span className={`admin-badge role-${u.role}`}>{u.role}</span>
                </td>
                <td>{u.created_at ? new Date(u.created_at).toLocaleDateString() : '–'}</td>
                <td>
                  <Link to={`/admin/users/${u.id}`} className="btn btn-sm btn-primary">
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {users.length === 0 && <p className="text-muted mb-0">No users found.</p>}
      </div>
    </>
  );
};

export default AdminUsers;
