import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { 
  Home, 
  Users, 
  MessageSquare, 
  FileText, 
  LogOut,
  Shield,
  Briefcase
} from 'lucide-react';
import { useContext } from 'react';
import { AuthContext } from '../AuthContext';

const Sidebar = () => {
  const { logout, admin } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { icon: <Home size={20} />, label: 'Dashboard', path: '/' },
    { icon: <Users size={20} />, label: 'User Management', path: '/users' },
    { icon: <Briefcase size={20} />, label: 'Jobs', path: '/jobs' },
    { icon: <FileText size={20} />, label: 'System Logs', path: '/logs' },
    { icon: <MessageSquare size={20} />, label: 'Admin Assistant', path: '/chatbot' },
  ];

  return (
    <aside style={styles.sidebar} className="glass">
      <div style={styles.header}>
        <Shield size={32} color="var(--accent)" />
        <h2 style={{ fontSize: '1.25rem', margin: 0 }}>Admin Portal</h2>
      </div>
      
      <div 
        style={{...styles.userProfile, cursor: 'pointer'}} 
        className="sidebar-profile"
        onClick={() => navigate('/profile')}
      >
        <div style={styles.avatar}>
          {admin?.username?.charAt(0).toUpperCase() || 'A'}
        </div>
        <div>
          <div style={{ fontWeight: '600' }}>{admin?.username || 'Admin'}</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            {admin?.role === 'superadmin' ? 'Super Administrator' : 'Administrator'}
          </div>
        </div>
      </div>

      <nav style={styles.nav}>
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            style={({ isActive }) => ({
              ...styles.navItem,
              ...(isActive ? styles.navItemActive : {})
            })}
          >
            {item.icon}
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div style={styles.footer}>
        <button className="btn" style={styles.logoutBtn} onClick={handleLogout}>
          <LogOut size={20} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
};

const styles = {
  sidebar: {
    width: '260px',
    height: '100vh',
    position: 'fixed',
    left: 0,
    top: 0,
    display: 'flex',
    flexDirection: 'column',
    borderRight: '1px solid var(--glass-border)',
    borderTopRightRadius: 0,
    borderBottomRightRadius: 0,
    zIndex: 100
  },
  header: {
    padding: '2rem 1.5rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    borderBottom: '1px solid var(--glass-border)'
  },
  userProfile: {
    padding: '1.5rem',
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    borderBottom: '1px solid var(--glass-border)'
  },
  avatar: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    backgroundColor: 'var(--accent)',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    fontSize: '1.2rem'
  },
  nav: {
    padding: '1.5rem 1rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    flex: 1
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    padding: '0.75rem 1rem',
    borderRadius: '8px',
    color: 'var(--text-secondary)',
    textDecoration: 'none',
    transition: 'all 0.2s ease',
  },
  navItemActive: {
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    color: 'var(--accent)',
    fontWeight: '500'
  },
  footer: {
    padding: '1.5rem',
    borderTop: '1px solid var(--glass-border)'
  },
  logoutBtn: {
    width: '100%',
    backgroundColor: 'transparent',
    border: '1px solid var(--danger)',
    color: 'var(--danger)',
  }
};

export default Sidebar;
