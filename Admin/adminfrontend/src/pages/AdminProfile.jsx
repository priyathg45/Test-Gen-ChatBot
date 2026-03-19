import React, { useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { 
  User, 
  Mail, 
  Phone, 
  Shield, 
  Edit2, 
  Save, 
  X, 
  CheckCircle,
  Briefcase,
  Calendar,
  Info
} from 'lucide-react';
import { AuthContext } from '../AuthContext';

const AdminProfile = () => {
  const { admin } = useContext(AuthContext);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    bio: ''
  });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const res = await axios.get('/api/auth/me');
      setProfile(res.data);
      setFormData({
        full_name: res.data.full_name || '',
        email: res.data.email || '',
        phone: res.data.phone || '',
        bio: res.data.bio || ''
      });
    } catch (err) {
      console.error('Error fetching admin profile:', err);
      setMessage({ type: 'error', text: 'Failed to load profile details.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      await axios.put('/api/auth/profile', formData);
      setMessage({ type: 'success', text: 'Profile updated successfully!' });
      setEditing(false);
      fetchProfile();
      setTimeout(() => setMessage({ type: '', text: '' }), 3000);
    } catch (err) {
      console.error('Error updating profile:', err);
      setMessage({ type: 'error', text: err.response?.data?.error || 'Failed to update profile.' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="loading-container">Loading Profile...</div>;

  return (
    <div className="profile-container" style={styles.container}>
      {message.text && (
        <div style={{
          ...styles.alert,
          backgroundColor: message.type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          color: message.type === 'success' ? '#10b981' : '#ef4444',
          border: `1px solid ${message.type === 'success' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
        }}>
          {message.type === 'success' ? <CheckCircle size={18} /> : <Info size={18} />}
          {message.text}
        </div>
      )}

      <div className="glass glass-card" style={styles.profileCard}>
        <div style={styles.headerSection}>
          <div style={styles.avatarLarge}>
            {profile?.username?.charAt(0).toUpperCase() || 'A'}
          </div>
          <div style={styles.headerInfo}>
            <h2 style={styles.username}>{profile?.username || 'Admin'}</h2>
            <div style={styles.badge}>
              <Shield size={14} />
              <span>{profile?.role === 'superadmin' ? 'Super Administrator' : 'Administrator'}</span>
            </div>
          </div>
          {!editing && (
            <button 
              className="btn btn-primary" 
              style={styles.editBtn}
              onClick={() => setEditing(true)}
            >
              <Edit2 size={18} />
              Edit Profile
            </button>
          )}
        </div>

        <div style={styles.detailsGrid}>
          {editing ? (
            <form onSubmit={handleUpdate} style={styles.editForm}>
              <div style={styles.inputGroup}>
                <label style={styles.label}>Full Name</label>
                <div style={styles.inputWrapper}>
                  <User size={18} style={styles.inputIcon} />
                  <input 
                    type="text" 
                    value={formData.full_name}
                    onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                    placeholder="Enter full name"
                    style={styles.input}
                  />
                </div>
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Email Address</label>
                <div style={styles.inputWrapper}>
                  <Mail size={18} style={styles.inputIcon} />
                  <input 
                    type="email" 
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    placeholder="admin@example.com"
                    style={styles.input}
                  />
                </div>
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Phone Number</label>
                <div style={styles.inputWrapper}>
                  <Phone size={18} style={styles.inputIcon} />
                  <input 
                    type="text" 
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    placeholder="+1 234 567 890"
                    style={styles.input}
                  />
                </div>
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Bio / Personal Note</label>
                <textarea 
                  value={formData.bio}
                  onChange={(e) => setFormData({...formData, bio: e.target.value})}
                  placeholder="Tell us a bit about yourself..."
                  style={{...styles.input, height: '100px', paddingLeft: '1rem'}}
                />
              </div>

              <div style={styles.formActions}>
                <button 
                  type="button" 
                  className="btn" 
                  style={styles.cancelBtn}
                  onClick={() => setEditing(false)}
                  disabled={saving}
                >
                  <X size={18} />
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="btn btn-primary" 
                  style={styles.saveBtn}
                  disabled={saving}
                >
                  {saving ? 'Saving...' : <><Save size={18} /> Save Changes</>}
                </button>
              </div>
            </form>
          ) : (
            <>
              <div style={styles.infoBlock}>
                <div style={styles.infoLabel}><User size={16} /> Full Name</div>
                <div style={styles.infoValue}>{profile?.full_name || 'Not provided'}</div>
              </div>
              <div style={styles.infoBlock}>
                <div style={styles.infoLabel}><Mail size={16} /> Email</div>
                <div style={styles.infoValue}>{profile?.email || 'Not provided'}</div>
              </div>
              <div style={styles.infoBlock}>
                <div style={styles.infoLabel}><Phone size={16} /> Phone</div>
                <div style={styles.infoValue}>{profile?.phone || 'Not provided'}</div>
              </div>
              <div style={styles.infoBlock}>
                <div style={styles.infoLabel}><Shield size={16} /> Role</div>
                <div style={styles.infoValue}>{profile?.role || 'Administrator'}</div>
              </div>
              {profile?.bio && (
                <div style={{ ...styles.infoBlock, gridColumn: '1 / -1' }}>
                  <div style={styles.infoLabel}><Info size={16} /> About</div>
                  <div style={styles.infoValue}>{profile.bio}</div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      <div style={styles.otherStats}>
        <div className="glass glass-card" style={styles.miniCard}>
          <Briefcase size={24} color="#3b82f6" />
          <div>
            <div style={styles.miniLabel}>Assigned Responsibilities</div>
            <div style={styles.miniValue}>System Maintenance, User Audit</div>
          </div>
        </div>
        <div className="glass glass-card" style={styles.miniCard}>
          <Calendar size={24} color="#10b981" />
          <div>
            <div style={styles.miniLabel}>Last Login</div>
            <div style={styles.miniValue}>{new Date().toLocaleDateString()}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    maxWidth: '900px',
    margin: '0 auto',
    animation: 'fadeIn 0.5s ease-out'
  },
  alert: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '1rem',
    borderRadius: '12px',
    marginBottom: '2rem',
    fontSize: '0.9rem',
    fontWeight: 500
  },
  profileCard: {
    padding: '2.5rem',
    marginBottom: '2rem'
  },
  headerSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '2rem',
    marginBottom: '3rem',
    borderBottom: '1px solid var(--glass-border)',
    paddingBottom: '2.5rem'
  },
  avatarLarge: {
    width: '100px',
    height: '100px',
    borderRadius: '24px',
    background: 'linear-gradient(135deg, var(--accent) 0%, #2563eb 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontSize: '3rem',
    fontWeight: 800,
    boxShadow: '0 10px 25px -5px rgba(59, 130, 246, 0.4)'
  },
  headerInfo: {
    flex: 1
  },
  username: {
    fontSize: '2rem',
    fontWeight: 800,
    margin: '0 0 0.5rem 0',
    color: 'var(--text-primary)'
  },
  badge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.4rem 0.8rem',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    color: 'var(--accent)',
    borderRadius: '8px',
    fontSize: '0.85rem',
    fontWeight: 600
  },
  editBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem'
  },
  detailsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '2rem'
  },
  infoBlock: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem'
  },
  infoLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    fontSize: '0.85rem',
    color: 'var(--text-secondary)',
    fontWeight: 600
  },
  infoValue: {
    fontSize: '1.1rem',
    fontWeight: 500,
    color: 'var(--text-primary)',
    padding: '0.75rem 1rem',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)'
  },
  editForm: {
    gridColumn: '1 / -1',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '1.5rem'
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem'
  },
  label: {
    fontSize: '0.85rem',
    fontWeight: 600,
    color: 'var(--text-secondary)',
    marginLeft: '4px'
  },
  inputWrapper: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center'
  },
  inputIcon: {
    position: 'absolute',
    left: '12px',
    color: 'var(--text-secondary)'
  },
  input: {
    width: '100%',
    padding: '0.8rem 1rem 0.8rem 2.5rem',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    border: '1px solid var(--glass-border)',
    borderRadius: '10px',
    color: 'var(--text-primary)',
    fontSize: '1rem',
    transition: 'border-color 0.2s',
    outline: 'none'
  },
  formActions: {
    gridColumn: '1 / -1',
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '1rem',
    marginTop: '1rem'
  },
  cancelBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    backgroundColor: 'transparent',
    border: '1px solid var(--glass-border)',
    color: 'var(--text-secondary)'
  },
  saveBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem'
  },
  otherStats: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
    gap: '1.5rem',
    marginTop: '1rem'
  },
  miniCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '1.25rem',
    padding: '1.5rem'
  },
  miniLabel: {
    fontSize: '0.8rem',
    color: 'var(--text-secondary)',
    fontWeight: 500
  },
  miniValue: {
    fontSize: '1rem',
    fontWeight: 700,
    color: 'var(--text-primary)',
    marginTop: '2px'
  }
};

export default AdminProfile;
