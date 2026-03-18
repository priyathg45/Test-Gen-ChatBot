import React, { useEffect, useState, useContext } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Eye, Trash2, Search, UserCheck, UserX } from 'lucide-react';
import { AuthContext } from '../AuthContext';

const StatusBadge = ({ isActive }) => (
  <span style={{
    padding: '3px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: 700,
    background: isActive ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
    color: isActive ? '#10b981' : '#ef4444',
  }}>
    {isActive ? 'Active' : 'Inactive'}
  </span>
);

const UsersList = () => {
  const { token } = useContext(AuthContext);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [toggling, setToggling] = useState(null);
  const navigate = useNavigate();

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  useEffect(() => { fetchUsers(); }, []);

  const fetchUsers = async () => {
    try {
      const res = await axios.get('/api/users/', { headers });
      setUsers(res.data.users);
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to permanently delete this user?')) return;
    try {
      await axios.delete(`/api/users/${id}`, { headers });
      setUsers(users.filter(u => u._id !== id));
    } catch {
      alert('Failed to delete user');
    }
  };

  const handleToggleActive = async (user, e) => {
    e.stopPropagation();
    const isActive = user.is_active !== false;
    const endpoint = isActive ? 'deactivate' : 'activate';
    setToggling(user._id);
    try {
      await axios.put(`/api/users/${user._id}/${endpoint}`, {}, { headers });
      setUsers(prev => prev.map(u => u._id === user._id ? { ...u, is_active: !isActive } : u));
    } catch {
      alert(`Failed to ${endpoint} user`);
    } finally {
      setToggling(null);
    }
  };

  const filteredUsers = users.filter(user =>
    user.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div>
      <div style={styles.header}>
        <div style={{ visibility: 'hidden', pointerEvents: 'none' }}>
          <h1>User Management</h1>
        </div>
        <div style={styles.searchBox}>
          <Search size={20} color="var(--text-secondary)" style={styles.searchIcon} />
          <input type="text" className="input" placeholder="Search users..."
            value={searchTerm} onChange={e => setSearchTerm(e.target.value)}
            style={styles.searchInput} />
        </div>
      </div>

      {/* Summary badges */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="glass glass-card" style={styles.miniStat}>
          <span style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent)' }}>{users.length}</span>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Total</span>
        </div>
        <div className="glass glass-card" style={styles.miniStat}>
          <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#10b981' }}>{users.filter(u => u.is_active !== false).length}</span>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Active</span>
        </div>
        <div className="glass glass-card" style={styles.miniStat}>
          <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#ef4444' }}>{users.filter(u => u.is_active === false).length}</span>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Inactive</span>
        </div>
      </div>

      <div className="glass glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={styles.loading}>Loading users...</div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                {['Username', 'Email', 'Status', 'Joined', 'Actions'].map(h => (
                  <th key={h} style={styles.th}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredUsers.length === 0 ? (
                <tr><td colSpan="5" style={styles.emptyState}>No users found.</td></tr>
              ) : filteredUsers.map(user => (
                <tr key={user._id} style={styles.tr} onClick={() => navigate(`/users/${user._id}`)}>
                  <td style={styles.td}>
                    <div style={styles.userCell}>
                      <div style={{
                        ...styles.avatarMini,
                        background: user.is_active !== false ? 'rgba(59,130,246,0.2)' : 'rgba(100,116,139,0.2)',
                        color: user.is_active !== false ? 'var(--accent)' : '#64748b',
                      }}>
                        {user.username?.charAt(0).toUpperCase() || 'U'}
                      </div>
                      {user.username}
                    </div>
                  </td>
                  <td style={styles.td}>{user.email || 'N/A'}</td>
                  <td style={styles.td}><StatusBadge isActive={user.is_active !== false} /></td>
                  <td style={styles.td}>
                    {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'}
                  </td>
                  <td style={styles.td}>
                    <div style={styles.actions}>
                      <button style={styles.actionBtn} title="View Profile"
                        onClick={e => { e.stopPropagation(); navigate(`/users/${user._id}`); }}>
                        <Eye size={17} />
                      </button>
                      <button
                        style={{ ...styles.actionBtn, color: user.is_active !== false ? '#f59e0b' : '#10b981' }}
                        title={user.is_active !== false ? 'Deactivate user' : 'Activate user'}
                        disabled={toggling === user._id}
                        onClick={e => handleToggleActive(user, e)}>
                        {user.is_active !== false ? <UserX size={17} /> : <UserCheck size={17} />}
                      </button>
                      <button style={{ ...styles.actionBtn, color: 'var(--danger)' }} title="Delete User"
                        onClick={e => handleDelete(user._id, e)}>
                        <Trash2 size={17} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

const styles = {
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' },
  searchBox: { position: 'relative', width: '300px' },
  searchIcon: { position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' },
  searchInput: { paddingLeft: '2.5rem' },
  miniStat: { padding: '0.75rem 1.25rem', display: 'flex', flexDirection: 'column', gap: '2px', minWidth: '90px' },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { textAlign: 'left', padding: '1rem 1.5rem', color: 'var(--text-secondary)', fontWeight: 500, borderBottom: '1px solid var(--glass-border)', fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em' },
  td: { padding: '1rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)' },
  tr: { cursor: 'pointer', transition: 'background-color 0.2s' },
  userCell: { display: 'flex', alignItems: 'center', gap: '1rem', fontWeight: 500 },
  avatarMini: { width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.9rem', fontWeight: 'bold' },
  actions: { display: 'flex', gap: '0.5rem' },
  actionBtn: { background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '0.25rem', transition: 'color 0.2s' },
  loading: { padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' },
  emptyState: { padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' },
};

export default UsersList;
