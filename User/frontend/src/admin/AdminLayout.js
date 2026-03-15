import React from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './AdminLayout.css';

const AdminLayout = () => {
  const { user, logout } = useAuth();

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <div className="admin-sidebar-header">
          <h2>Admin</h2>
          <span className="admin-role-badge">Admin</span>
        </div>
        <nav className="admin-nav">
          <NavLink end to="/admin" className={({ isActive }) => (isActive ? 'admin-nav-item active' : 'admin-nav-item')}>
            Dashboard
          </NavLink>
          <NavLink to="/admin/users" className={({ isActive }) => (isActive ? 'admin-nav-item active' : 'admin-nav-item')}>
            Users
          </NavLink>
          <NavLink to="/admin/activity-logs" className={({ isActive }) => (isActive ? 'admin-nav-item active' : 'admin-nav-item')}>
            Activity Logs
          </NavLink>
        </nav>
        <div className="admin-sidebar-footer">
          <div className="admin-user-email">{user?.email}</div>
          <NavLink to="/" className="admin-nav-item">Back to Site</NavLink>
          <button type="button" className="btn btn-sm btn-outline-secondary" onClick={logout}>
            Logout
          </button>
        </div>
      </aside>
      <main className="admin-main">
        <Outlet />
      </main>
    </div>
  );
};

export default AdminLayout;
