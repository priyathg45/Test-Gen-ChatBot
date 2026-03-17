import React, { useEffect, useState, useContext } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Users, Activity, MessageSquare, Briefcase, CheckCircle, Clock } from 'lucide-react';
import { AuthContext } from '../AuthContext';

const StatCard = ({ title, value, icon, color, sub }) => (
  <div className="glass glass-card" style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', padding: '1.5rem' }}>
    <div style={{ width: 56, height: 56, borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: `${color}18`, color }}>
      {icon}
    </div>
    <div>
      <h3 style={{ fontSize: '2rem', margin: 0, lineHeight: 1.1 }}>{value}</h3>
      <p style={{ margin: 0, fontSize: '0.88rem' }}>{title}</p>
      {sub && <p style={{ margin: '2px 0 0', fontSize: '0.78rem', color: '#64748b' }}>{sub}</p>}
    </div>
  </div>
);

const Dashboard = () => {
  const { token } = useContext(AuthContext);
  const navigate = useNavigate();
  const [stats, setStats] = useState({ users: 0, active: 0, inactive: 0, jobs: 0, pending: 0, completed: 0, sessions: 0 });
  const [recentUsers, setRecentUsers] = useState([]);
  const [recentJobs, setRecentJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [uRes, jRes] = await Promise.all([
          axios.get('/api/users/stats', { headers }),
          axios.get('/api/jobs/stats', { headers }),
        ]);
        const u = uRes.data;
        const j = jRes.data;
        setStats(prev => ({
          ...prev,
          users: u.total || 0,
          active: u.active || 0,
          inactive: u.inactive || 0,
          jobs: j.total || 0,
          pending: j.stats?.pending || 0,
          completed: j.stats?.completed || 0,
        }));
        setRecentUsers(u.recent || []);
        // Fetch recent jobs separately
        const jListRes = await axios.get('/api/jobs/', { headers });
        setRecentJobs((jListRes.data.jobs || []).slice(0, 5));
      } catch (err) {
        console.error('Dashboard stats error:', err);
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

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1>Dashboard Overview</h1>
        <p>Monitor your chat system operations and user metrics.</p>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: '1.25rem', marginBottom: '2.5rem' }}>
        <StatCard title="Total Users" value={loading ? '…' : stats.users} icon={<Users size={24} />} color="var(--accent)" sub={`${stats.active} active · ${stats.inactive} inactive`} />
        <StatCard title="Total Jobs" value={loading ? '…' : stats.jobs} icon={<Briefcase size={24} />} color="#f59e0b" sub={`${stats.pending} pending`} />
        <StatCard title="Completed Jobs" value={loading ? '…' : stats.completed} icon={<CheckCircle size={24} />} color="#10b981" />
        <StatCard title="Pending Approvals" value={loading ? '…' : stats.pending} icon={<Clock size={24} />} color="#8b5cf6" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Recent Users */}
        <div className="glass glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <h2 style={{ margin: 0 }}>Recent Users</h2>
            <button onClick={() => navigate('/users')} style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: '0.85rem' }}>View all →</button>
          </div>
          {recentUsers.length === 0 ? <p>No users found.</p> : recentUsers.map(u => (
            <div key={u._id} onClick={() => navigate(`/users/${u._id}`)}
              style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.6rem 0', borderBottom: '1px solid var(--glass-border)', cursor: 'pointer' }}>
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'rgba(59,130,246,0.2)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: '0.85rem', flexShrink: 0 }}>
                {u.username?.charAt(0).toUpperCase()}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{u.username}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{u.email}</div>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                {u.created_at ? new Date(u.created_at).toLocaleDateString() : ''}
              </div>
            </div>
          ))}
        </div>

        {/* Recent Jobs */}
        <div className="glass glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <h2 style={{ margin: 0 }}>Recent Jobs</h2>
            <button onClick={() => navigate('/jobs')} style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: '0.85rem' }}>View all →</button>
          </div>
          {recentJobs.length === 0 ? <p>No jobs yet.</p> : recentJobs.map(j => (
            <div key={j.job_id}
              style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.6rem 0', borderBottom: '1px solid var(--glass-border)' }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: STATUS_COLOR[j.status] || '#64748b', flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontSize: '0.88rem' }}>{j.title || 'Untitled'}</div>
                <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)' }}>{j.user_info?.username || ''} · {j.client_name || ''}</div>
              </div>
              <span style={{ fontSize: '11px', fontWeight: 700, color: STATUS_COLOR[j.status] || '#64748b', textTransform: 'capitalize' }}>{j.status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* System status */}
      <div className="glass glass-card" style={{ marginTop: '1.5rem' }}>
        <h2>System Status</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '8px', color: 'var(--success)' }}>
          <div style={{ width: 10, height: 10, background: 'var(--success)', borderRadius: '50%', boxShadow: '0 0 10px var(--success)' }} />
          <span>All systems operational</span>
          <span style={{ marginLeft: 'auto', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>MongoDB · Flask API · Ollama</span>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
