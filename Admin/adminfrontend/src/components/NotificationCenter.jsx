import React, { useState, useEffect, useRef } from 'react';
import { Bell, Info, AlertCircle, CheckCircle, X, ExternalLink } from 'lucide-react';

const NotificationCenter = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([
    {
      id: 1,
      type: 'info',
      title: 'System Update',
      message: 'Genesis AI has been updated to v2.4.0 with improved response times.',
      time: '2 hours ago',
      read: false
    },
    {
      id: 2,
      type: 'warning',
      title: 'High Traffic Alert',
      message: 'Detected unusual traffic spike from US East region. Monitoring system health.',
      time: '5 hours ago',
      read: true
    },
    {
      id: 3,
      type: 'success',
      title: 'Backup Successful',
      message: 'Weekly database backup completed successfully. All data is synchronized.',
      time: '1 day ago',
      read: true
    },
    {
        id: 4,
        type: 'info',
        title: 'New Feature',
        message: 'Reference IDs can now be copied directly from the session list.',
        time: 'Just now',
        read: false
    }
  ]);

  const popoverRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const unreadCount = notifications.filter(n => !n.read).length;

  const markAllAsRead = () => {
    setNotifications(notifications.map(n => ({ ...n, read: true })));
  };

  const getIcon = (type) => {
    switch (type) {
      case 'info': return <Info size={18} color="#3b82f6" />;
      case 'warning': return <AlertCircle size={18} color="#f59e0b" />;
      case 'success': return <CheckCircle size={18} color="#10b981" />;
      default: return <Bell size={18} />;
    }
  };

  return (
    <div style={{ position: 'relative' }} ref={popoverRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        style={{
          background: 'none', border: 'none', cursor: 'pointer', position: 'relative',
          padding: '8px', borderRadius: '50%', transition: 'background 0.2s',
          display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-primary)'
        }}
        onMouseOver={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
        onMouseOut={e => e.currentTarget.style.background = 'none'}
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span style={{
            position: 'absolute', top: '4px', right: '4px', background: 'var(--danger)',
            color: 'white', fontSize: '10px', fontWeight: 700, borderRadius: '50%',
            width: '16px', height: '16px', display: 'flex', alignItems: 'center',
            justifyContent: 'center', border: '2px solid var(--bg-secondary)'
          }}>
            {unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="glass" style={{
          position: 'absolute', top: '100%', right: 0, marginTop: '12px',
          width: '320px', maxHeight: '450px', display: 'flex', flexDirection: 'column',
          zIndex: 1000, overflow: 'hidden', animation: 'slideDown 0.3s ease-out'
        }}>
          <div style={{
            padding: '1rem', borderBottom: '1px solid var(--glass-border)',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <h3 style={{ margin: 0, fontSize: '1rem' }}>Notification Center</h3>
            <button 
              onClick={markAllAsRead}
              style={{ background: 'none', border: 'none', color: 'var(--accent)', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer' }}
            >
              Mark all read
            </button>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
            {notifications.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                No notifications yet.
              </div>
            ) : (
              notifications.map(n => (
                <div 
                  key={n.id} 
                  style={{
                    padding: '1rem', borderRadius: '12px', marginBottom: '4px',
                    background: n.read ? 'transparent' : 'rgba(59,130,246,0.05)',
                    transition: 'background 0.2s', cursor: 'pointer', position: 'relative'
                  }}
                  onMouseOver={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                  onMouseOut={e => e.currentTarget.style.background = n.read ? 'transparent' : 'rgba(59,130,246,0.05)'}
                >
                  {!n.read && (
                    <div style={{ position: 'absolute', left: '8px', top: '16px', width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent)' }} />
                  )}
                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <div style={{ marginTop: '2px' }}>{getIcon(n.type)}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{n.title}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: 1.4 }}>{n.message}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '8px', opacity: 0.6 }}>{n.time}</div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          <div style={{
            padding: '0.75rem', borderTop: '1px solid var(--glass-border)',
            textAlign: 'center', background: 'rgba(255,255,255,0.02)'
          }}>
            <button style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', fontSize: '0.8rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', margin: '0 auto' }}>
              View all notifications <ExternalLink size={12} />
            </button>
          </div>
        </div>
      )}
      <style>{`
        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
};

export default NotificationCenter;
