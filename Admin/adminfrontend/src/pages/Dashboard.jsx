import React, { useEffect, useState, useContext } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Users, Activity, MessageSquare, Briefcase, CheckCircle, Clock } from 'lucide-react';
import { AuthContext } from '../AuthContext';

const StatCard = ({ title, value, icon, color, sub }) => (
  <div className="glass glass-card stat-card" style={{ 
    display: 'flex', alignItems: 'center', gap: '1.25rem', padding: '1.5rem',
    transition: 'transform 0.2s ease, box-shadow 0.2s ease',
    cursor: 'default'
  }}>
    <div style={{ 
      width: 56, height: 56, borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center', 
      backgroundColor: `${color}15`, color, border: `1px solid ${color}30`
    }}>
      {icon}
    </div>
    <div style={{ flex: 1 }}>
      <h3 style={{ fontSize: '1.85rem', fontWeight: 800, margin: 0, lineHeight: 1.1, color: 'var(--text-primary)' }}>{value}</h3>
      <p style={{ margin: '4px 0 0', fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 500 }}>{title}</p>
      {sub && <p style={{ margin: '6px 0 0', fontSize: '0.78rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px' }}>{sub}</p>}
    </div>
  </div>
);

const Dashboard = () => {
  const { admin } = useContext(AuthContext);
  const token = admin?.token;
  const navigate = useNavigate();
  const [stats, setStats] = useState({ users: 0, active: 0, inactive: 0, jobs: 0, pending: 0, completed: 0, sessions: 0 });
  const [recentUsers, setRecentUsers] = useState([]);
  const [recentJobs, setRecentJobs] = useState([]);
  const [health, setHealth] = useState({ status: 'loading', mongodb: '...', ollama: '...' });
  const [loading, setLoading] = useState(true);

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [uRes, jRes, hRes] = await Promise.all([
          axios.get('/api/users/stats', { headers }),
          axios.get('/api/jobs/stats', { headers }),
          axios.get('/api/health', { headers }),
        ]);

        const u = uRes.data;
        const j = jRes.data;
        const h = hRes.data;

        setStats({
          users: u.total || 0,
          active: u.active || 0,
          inactive: u.inactive || 0,
          jobs: j.total || 0,
          pending: j.stats?.pending || 0,
          completed: j.stats?.completed || 0,
          sessions: u.total_sessions || 0, // Assuming backend might provide this, or we fallback
        });
        
        // Let's also check if total_sessions comes from jobs for some reason or just hardcode for now
        // if users/stats doesn't have it, maybe we don't have it yet.
        
        setHealth({
          status: h.overall || 'unknown',
          mongodb: h.mongodb || 'error',
          ollama: h.ollama || 'offline'
        });

        setRecentUsers(u.recent || []);
        
        const jListRes = await axios.get('/api/jobs/', { headers });
        setRecentJobs((jListRes.data.jobs || []).slice(0, 5));
      } catch (err) {
        console.error('Dashboard stats error:', err);
        setHealth({ status: 'error', mongodb: 'error', ollama: 'error' });
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, [token]);

  const STATUS_COLOR = {
    pending: '#f59e0b', accepted: '#3b82f6', confirmed: '#3b82f6',
    in_progress: '#8b5cf6', completed: '#10b981', rejected: '#ef4444',
  };

  const getHealthBadge = (val) => {
    if (val === 'connected' || val === 'online' || val === 'healthy') 
      return { bg: 'rgba(16,185,129,0.1)', color: '#10b981', label: val.toUpperCase() };
    if (val === 'offline' || val === 'degraded' || val === 'error')
      return { bg: 'rgba(239,68,68,0.1)', color: '#ef4444', label: val.toUpperCase() };
    return { bg: 'rgba(245,158,11,0.1)', color: '#f59e0b', label: val.toUpperCase() };
  };

  return (
    <div className="dashboard-container">
      <div style={{ marginBottom: '2.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 style={{ fontSize: '2.25rem', fontWeight: 800, letterSpacing: '-0.025em', marginBottom: '0.5rem' }}>Dashboard Overview</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem' }}>Real-time metrics and system health monitoring.</p>
        </div>
        <div style={{ textAlign: 'right', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
        <StatCard title="Total Users" value={loading ? '...' : stats.users} icon={<Users size={24} />} color="#3b82f6" sub={<span><span style={{ color: '#10b981' }}>●</span> {stats.active} active</span>} />
        <StatCard title="Active Jobs" value={loading ? '...' : stats.jobs} icon={<Briefcase size={24} />} color="#f59e0b" sub={<span>{stats.pending} awaiting approval</span>} />
        <StatCard title="Completed" value={loading ? '...' : stats.completed} icon={<CheckCircle size={24} />} color="#10b981" />
        <StatCard title="Pending" value={loading ? '...' : stats.pending} icon={<Clock size={24} />} color="#8b5cf6" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem', marginBottom: '2.5rem' }}>
        {/* Recent Users */}
        <div className="glass glass-card" style={{ padding: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.75rem' }}>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700 }}>Recent Users</h2>
            <button onClick={() => navigate('/users')} className="btn-text" style={{ color: 'var(--accent)', cursor: 'pointer', fontSize: '0.9rem', fontWeight: 600, border: 'none', background: 'none' }}>View all →</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {recentUsers.length === 0 ? <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem' }}>No users found.</p> : recentUsers.map(u => (
              <div key={u._id} onClick={() => navigate(`/users/${u._id}`)} className="list-item"
                style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.85rem', borderRadius: '12px', cursor: 'pointer', transition: 'background 0.2s' }}>
                <div style={{ width: 40, height: 40, borderRadius: '12px', background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '1rem' }}>
                  {u.username?.charAt(0).toUpperCase()}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{u.username}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{u.email}</div>
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                  {u.created_at ? new Date(u.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) : ''}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Jobs */}
        <div className="glass glass-card" style={{ padding: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.75rem' }}>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700 }}>Recent Jobs</h2>
            <button onClick={() => navigate('/jobs')} className="btn-text" style={{ color: 'var(--accent)', cursor: 'pointer', fontSize: '0.9rem', fontWeight: 600, border: 'none', background: 'none' }}>View all →</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {recentJobs.length === 0 ? <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem' }}>No jobs yet.</p> : recentJobs.map(j => (
              <div key={j.job_id} className="list-item"
                style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.85rem', borderRadius: '12px', border: '1px solid transparent' }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: STATUS_COLOR[j.status] || '#64748b', boxShadow: `0 0 8px ${STATUS_COLOR[j.status] || '#64748b'}80` }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{j.title || 'Untitled'}</div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{j.user_info?.username || 'Unknown'} · {j.client_name || ''}</div>
                </div>
                <span style={{ 
                  fontSize: '0.7rem', fontWeight: 800, color: STATUS_COLOR[j.status] || '#64748b', 
                  textTransform: 'uppercase', padding: '4px 8px', borderRadius: '6px', 
                  background: `${STATUS_COLOR[j.status] || '#64748b'}15`, letterSpacing: '0.05em'
                }}>{j.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* System status details */}
      <div className="glass glass-card" style={{ padding: '2rem' }}>
        <h2 style={{ margin: '0 0 1.5rem', fontSize: '1.25rem', fontWeight: 700 }}>Infrastructure Health</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
          {[
            { name: 'Core API', status: health.status === 'healthy' ? 'online' : health.status, icon: <Activity size={18} /> },
            { name: 'Database', status: health.mongodb, icon: <Activity size={18} /> },
            { name: 'Intelligence', status: health.ollama, icon: <Activity size={18} /> }
          ].map(svc => {
            const badge = getHealthBadge(svc.status);
            return (
              <div key={svc.name} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
                <div style={{ color: badge.color }}>{svc.icon}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{svc.name}</div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '2px' }}>{svc.name === 'Intelligence' ? 'Ollama Engine' : 'System Service'}</div>
                </div>
                <div style={{ padding: '4px 8px', borderRadius: '6px', background: badge.bg, color: badge.color, fontSize: '0.65rem', fontWeight: 900 }}>
                  {badge.label}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <style>{`
        .stat-card:hover { transform: translateY(-4px); box-shadow: 0 12px 24px -10px rgba(0,0,0,0.3); border-color: var(--accent); }
        .list-item:hover { background: rgba(59,130,246,0.08); }
        .dashboard-container { animation: fadeIn 0.5s ease-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
};

export default Dashboard;
