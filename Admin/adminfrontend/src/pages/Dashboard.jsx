import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Users, Activity, MessageSquare } from 'lucide-react';

const StatCard = ({ title, value, icon, color }) => (
  <div className="glass glass-card" style={styles.statCard}>
    <div style={{ ...styles.iconBox, backgroundColor: `${color}15`, color }}>
      {icon}
    </div>
    <div>
      <h3 style={styles.statValue}>{value}</h3>
      <p style={styles.statTitle}>{title}</p>
    </div>
  </div>
);

const Dashboard = () => {
  const [stats, setStats] = useState({ users: 0, activeChats: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // Fetch total users for dashboard
        const res = await axios.get('/api/users');
        setStats({
          users: res.data.users.length || 0,
          activeChats: 24 // Mock active chats for dashboard feel
        });
      } catch (err) {
        console.error("Failed to load users:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  return (
    <div>
      <div style={styles.header}>
        <h1>Dashboard Overview</h1>
        <p>Monitor your chat system operations and user metrics.</p>
      </div>

      <div style={styles.statsGrid}>
        <StatCard 
          title="Total Registered Users" 
          value={loading ? "..." : stats.users} 
          icon={<Users size={24} />} 
          color="var(--accent)"
        />
        <StatCard 
          title="Active Sessions" 
          value={loading ? "..." : stats.activeChats} 
          icon={<Activity size={24} />} 
          color="var(--success)"
        />
        <StatCard 
          title="Total Queries Today" 
          value="1,452" 
          icon={<MessageSquare size={24} />} 
          color="#8B5CF6"
        />
      </div>

      <div className="glass glass-card" style={styles.recentSection}>
        <h2>System Status</h2>
        <div style={styles.statusBanner}>
          <div style={styles.statusDot}></div>
          <span>All systems operational</span>
          <span style={styles.statusTime}>Updated just now</span>
        </div>
      </div>
    </div>
  );
};

const styles = {
  header: {
    marginBottom: '2rem'
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '1.5rem',
    marginBottom: '2.5rem'
  },
  statCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '1.25rem',
    padding: '1.5rem'
  },
  iconBox: {
    width: '56px',
    height: '56px',
    borderRadius: '14px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  statValue: {
    fontSize: '2rem',
    margin: 0,
    lineHeight: 1.2
  },
  statTitle: {
    margin: 0,
    fontSize: '0.9rem'
  },
  recentSection: {
    marginTop: '2rem'
  },
  statusBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    padding: '1rem',
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    border: '1px solid rgba(16, 185, 129, 0.2)',
    borderRadius: '8px',
    color: 'var(--success)'
  },
  statusDot: {
    width: '10px',
    height: '10px',
    backgroundColor: 'var(--success)',
    borderRadius: '50%',
    boxShadow: '0 0 10px var(--success)'
  },
  statusTime: {
    marginLeft: 'auto',
    fontSize: '0.85rem',
    color: 'var(--text-secondary)'
  }
};

export default Dashboard;
