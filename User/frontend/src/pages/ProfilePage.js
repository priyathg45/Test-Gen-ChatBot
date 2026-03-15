import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiPut } from '../api/client';
import './AuthPages.css';

const ProfilePage = () => {
  const { user, token, refreshUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');

  React.useEffect(() => {
    setFullName(user?.full_name || '');
  }, [user?.full_name]);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      const data = await apiPut('/me', { full_name: fullName }, token);
      if (data.success) {
        setMessage('Profile updated.');
        refreshUser();
      } else {
        setMessage(data.error || 'Update failed');
      }
    } catch (err) {
      setMessage(err.message || 'Update failed');
    } finally {
      setSaving(false);
    }
  };

  if (!user) return null;

  return (
    <div className="auth-page">
      <div className="container py-5">
        <div className="auth-card profile-card">
          <h1 className="auth-title">My Profile</h1>
          {message && (
            <div className={message.startsWith('Profile') ? 'alert alert-success' : 'alert alert-danger'}>
              {message}
            </div>
          )}
          <form onSubmit={handleSave}>
            <div className="form-group">
              <label>Email</label>
              <input type="text" className="form-control" value={user.email} readOnly disabled />
            </div>
            <div className="form-group">
              <label htmlFor="profile-fullname">Full Name</label>
              <input
                id="profile-fullname"
                type="text"
                className="form-control"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Your name"
              />
            </div>
            <div className="form-group">
              <label>Role</label>
              <input type="text" className="form-control" value={user.role} readOnly disabled />
            </div>
            <button type="submit" className="btn btn-primary btn-auth" disabled={saving}>
              {saving ? 'Saving...' : 'Save Profile'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
