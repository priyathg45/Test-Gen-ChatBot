import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Eye, Trash2, Search } from 'lucide-react';

const UsersList = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const res = await axios.get('/api/users');
      setUsers(res.data.users);
    } catch (error) {
      console.error("Error fetching users:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this user?")) return;
    
    try {
      await axios.delete(`/api/users/${id}`);
      setUsers(users.filter(u => u._id !== id));
    } catch (err) {
      alert("Failed to delete user");
    }
  };

  const filteredUsers = users.filter(user => 
    user.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div>
      <div style={styles.header}>
        <div>
          <h1>User Management</h1>
          <p>View, manage and monitor user accounts</p>
        </div>
        
        <div style={styles.searchBox}>
          <Search size={20} color="var(--text-secondary)" style={styles.searchIcon} />
          <input 
            type="text" 
            className="input" 
            placeholder="Search users..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={styles.searchInput}
          />
        </div>
      </div>

      <div className="glass glass-card" style={styles.tableContainer}>
        {loading ? (
          <div style={styles.loading}>Loading users...</div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Username</th>
                <th style={styles.th}>Email</th>
                <th style={styles.th}>Joined</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan="4" style={styles.emptyState}>No users found.</td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr 
                    key={user._id} 
                    style={styles.tr}
                    onClick={() => navigate(`/users/${user._id}`)}
                  >
                    <td style={styles.td}>
                      <div style={styles.userCell}>
                        <div style={styles.avatarMini}>
                          {user.username?.charAt(0).toUpperCase() || 'U'}
                        </div>
                        {user.username}
                      </div>
                    </td>
                    <td style={styles.td}>{user.email || 'N/A'}</td>
                    <td style={styles.td}>
                      {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'}
                    </td>
                    <td style={styles.td}>
                      <div style={styles.actions}>
                        <button 
                          style={styles.actionBtn} 
                          title="View Profile & Chats"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/users/${user._id}`);
                          }}
                        >
                          <Eye size={18} />
                        </button>
                        <button 
                          style={{...styles.actionBtn, color: 'var(--danger)'}} 
                          title="Delete User"
                          onClick={(e) => handleDelete(user._id, e)}
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

const styles = {
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '2rem'
  },
  searchBox: {
    position: 'relative',
    width: '300px'
  },
  searchIcon: {
    position: 'absolute',
    left: '12px',
    top: '50%',
    transform: 'translateY(-50%)'
  },
  searchInput: {
    paddingLeft: '2.5rem'
  },
  tableContainer: {
    padding: '0',
    overflow: 'hidden'
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse'
  },
  th: {
    textAlign: 'left',
    padding: '1.25rem 1.5rem',
    color: 'var(--text-secondary)',
    fontWeight: '500',
    borderBottom: '1px solid var(--glass-border)',
    fontSize: '0.9rem',
    textTransform: 'uppercase',
    letterSpacing: '0.05em'
  },
  td: {
    padding: '1.25rem 1.5rem',
    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
  },
  tr: {
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  userCell: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    fontWeight: '500'
  },
  avatarMini: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    color: 'var(--accent)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.9rem',
    fontWeight: 'bold'
  },
  actions: {
    display: 'flex',
    gap: '0.75rem'
  },
  actionBtn: {
    background: 'none',
    border: 'none',
    color: 'var(--text-secondary)',
    cursor: 'pointer',
    padding: '0.25rem',
    transition: 'color 0.2s'
  },
  loading: {
    padding: '3rem',
    textAlign: 'center',
    color: 'var(--text-secondary)'
  },
  emptyState: {
    padding: '3rem',
    textAlign: 'center',
    color: 'var(--text-secondary)'
  }
};

export default UsersList;
