import React from 'react';
import { Link } from 'react-router-dom';
import './AdminLayout.css';

const AdminDashboard = () => (
  <>
    <h1 className="admin-page-title">Dashboard</h1>
    <div className="admin-card">
      <p>Welcome to the admin panel. Use the sidebar to manage users and monitor activity.</p>
      <ul style={{ marginTop: '1rem', paddingLeft: '1.25rem' }}>
        <li><Link to="/admin/users">Users</Link> – View and manage user accounts, profiles, and chat history.</li>
        <li><Link to="/admin/activity-logs">Activity Logs</Link> – Monitor login, chat, and admin actions.</li>
      </ul>
    </div>
  </>
);

export default AdminDashboard;
