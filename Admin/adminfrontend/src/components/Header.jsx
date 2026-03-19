import React from 'react';
import { useLocation } from 'react-router-dom';
import NotificationCenter from './NotificationCenter';
import { Shield, ChevronRight } from 'lucide-react';

const Header = () => {
  const location = useLocation();
  
  const getPageTitle = () => {
    const path = location.pathname;
    if (path === '/') return 'Dashboard Overview';
    if (path.startsWith('/users')) return 'User Management';
    if (path === '/jobs') return 'Job Placements';
    if (path === '/logs') return 'System Audit Logs';
    if (path === '/chatbot') return 'Genesis Admin Assistant';
    if (path === '/profile') return 'Admin Profile Settings';
    return 'Admin Portal';
  };

  const breadcrumbs = location.pathname.split('/').filter(x => x);

  return (
    <header style={styles.header}>
      <div style={styles.left}>
        <div style={styles.breadcrumb}>
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Admin</span>
          <ChevronRight size={14} color="var(--text-secondary)" />
          <span style={{ color: 'var(--text-primary)', fontWeight: 600, fontSize: '0.85rem' }}>{getPageTitle()}</span>
        </div>
        <h1 style={styles.title}>{getPageTitle()}</h1>
      </div>

      <div style={styles.right}>
        <div style={styles.searchBar}>
             {/* Global search could go here if needed */}
        </div>
        <div style={styles.actions}>
          <NotificationCenter />
          <div style={styles.divider} />
          <div style={styles.userBadge}>
            <div style={styles.statusIndicator} />
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--success)' }}>SYSTEM ONLINE</span>
          </div>
        </div>
      </div>
    </header>
  );
};

const styles = {
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '2rem',
    padding: '0.5rem 0',
    borderBottom: '1px solid rgba(255,255,255,0.05)'
  },
  left: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.25rem'
  },
  breadcrumb: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '0.25rem'
  },
  title: {
    fontSize: '1.75rem',
    fontWeight: 800,
    margin: 0,
    background: 'linear-gradient(to right, #fff, #94a3b8)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent'
  },
  right: {
    display: 'flex',
    alignItems: 'center',
    gap: '1.5rem'
  },
  actions: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem'
  },
  divider: {
    width: '1px',
    height: '24px',
    background: 'var(--glass-border)'
  },
  userBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '6px 12px',
    background: 'rgba(16,185,129,0.1)',
    borderRadius: '20px',
    border: '1px solid rgba(16,185,129,0.2)'
  },
  statusIndicator: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    background: 'var(--success)',
    boxShadow: '0 0 8px var(--success)'
  }
};

export default Header;
