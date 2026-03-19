import React, { useEffect, useState, useContext, useCallback } from 'react';
import axios from 'axios';
import { Briefcase, Check, X, RefreshCw, Eye, ChevronDown } from 'lucide-react';
import { AuthContext } from '../AuthContext';

const STATUS_COLORS = {
  pending:     { bg: 'rgba(245,158,11,0.15)', color: '#f59e0b', label: 'Pending' },
  confirmed:   { bg: 'rgba(59,130,246,0.15)', color: '#3b82f6', label: 'Confirmed' },
  accepted:    { bg: 'rgba(59,130,246,0.15)', color: '#3b82f6', label: 'Accepted' },
  in_progress: { bg: 'rgba(139,92,246,0.15)', color: '#8b5cf6', label: 'In Progress' },
  completed:   { bg: 'rgba(16,185,129,0.15)', color: '#10b981', label: 'Completed' },
  rejected:    { bg: 'rgba(239,68,68,0.15)',  color: '#ef4444', label: 'Rejected' },
  cancelled:   { bg: 'rgba(100,116,139,0.15)',color: '#64748b', label: 'Cancelled' },
};

const StatusBadge = ({ status }) => {
  const s = STATUS_COLORS[status] || STATUS_COLORS.pending;
  return (
    <span style={{
      padding: '4px 10px', borderRadius: '20px', fontSize: '12px', fontWeight: 600,
      background: s.bg, color: s.color, textTransform: 'capitalize',
    }}>
      {s.label || status}
    </span>
  );
};

const AdminJobsPage = () => {
  const { token } = useContext(AuthContext);
  const [jobs, setJobs]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch]  = useState('');
  const [filter, setFilter]  = useState('all');
  const [updating, setUpdating] = useState(null);
  const [viewJob, setViewJob] = useState(null);

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get('/api/jobs/', { headers });
      setJobs(res.data.jobs || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  const updateStatus = async (jobId, status) => {
    setUpdating(jobId + status);
    try {
      const res = await axios.put(`/api/jobs/${jobId}/status`, { status }, { headers });
      setJobs(prev => prev.map(j => j.job_id === jobId ? res.data.job : j));
    } catch (e) {
      alert('Failed to update status');
    } finally {
      setUpdating(null);
    }
  };

  const filtered = jobs.filter(j => {
    const q = search.toLowerCase();
    const matchQ = !q || (j.title||'').toLowerCase().includes(q) ||
      (j.client_name||'').toLowerCase().includes(q) ||
      (j.user_info?.username||'').toLowerCase().includes(q);
    const matchF = filter === 'all' || j.status === filter;
    return matchQ && matchF;
  });

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Briefcase size={28} color="var(--accent)" /> Jobs Management
          </h1>
          <p>Review and approve jobs placed by users.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <input
            className="input" style={{ width: '220px' }}
            placeholder="Search jobs…"
            value={search} onChange={e => setSearch(e.target.value)}
          />
          <select
            className="input" style={{ width: '140px' }}
            value={filter} onChange={e => setFilter(e.target.value)}
          >
            <option value="all">All Statuses</option>
            {Object.keys(STATUS_COLORS).map(s => (
              <option key={s} value={s}>{STATUS_COLORS[s].label}</option>
            ))}
          </select>
          <button className="btn btn-primary" onClick={fetchJobs} style={{ padding: '0.6rem 1rem' }}>
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        {[
          { label: 'Total', val: jobs.length, color: 'var(--accent)' },
          { label: 'Pending', val: jobs.filter(j => j.status === 'pending').length, color: '#f59e0b' },
          { label: 'Accepted', val: jobs.filter(j => ['accepted','confirmed'].includes(j.status)).length, color: '#3b82f6' },
          { label: 'Completed', val: jobs.filter(j => j.status === 'completed').length, color: '#10b981' },
        ].map(stat => (
          <div key={stat.label} className="glass glass-card" style={{ padding: '1rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '4px', minWidth: '120px' }}>
            <span style={{ fontSize: '1.6rem', fontWeight: '800', color: stat.color }}>{stat.val}</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>{stat.label}</span>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className="glass glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading jobs…</div>
        ) : filtered.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-secondary)' }}>No jobs found.</div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--glass-border)' }}>
                {['User', 'Job Title', 'Client', 'Type / Qty', 'Status', 'Created', 'Actions'].map(h => (
                  <th key={h} style={{ padding: '1rem 1.25rem', textAlign: 'left', color: 'var(--text-secondary)', fontWeight: 500, textTransform: 'uppercase', fontSize: '0.78rem', letterSpacing: '0.05em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map(job => (
                <tr key={job.job_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '1rem 1.25rem' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{job.user_info?.username || '—'}</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>{job.user_info?.email || ''}</div>
                  </td>
                  <td style={{ padding: '1rem 1.25rem', fontWeight: 600, maxWidth: '160px' }}>{job.title || '—'}</td>
                  <td style={{ padding: '1rem 1.25rem', color: 'var(--text-secondary)' }}>{job.client_name || '—'}</td>
                  <td style={{ padding: '1rem 1.25rem', color: 'var(--text-secondary)', fontSize: '0.83rem' }}>
                    {[job.window_door_type, job.quantity].filter(Boolean).join(' / ') || '—'}
                  </td>
                  <td style={{ padding: '1rem 1.25rem' }}><StatusBadge status={job.status} /></td>
                  <td style={{ padding: '1rem 1.25rem', color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
                    {job.created_at ? new Date(job.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td style={{ padding: '1rem 1.25rem' }}>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      <ActionBtn
                        label="Accept" icon={<Check size={13} />} color="#10b981"
                        disabled={['accepted','completed'].includes(job.status) || updating === job.job_id + 'accepted'}
                        onClick={() => updateStatus(job.job_id, 'accepted')}
                      />
                      <ActionBtn
                        label="Reject" icon={<X size={13} />} color="#ef4444"
                        disabled={job.status === 'rejected' || updating === job.job_id + 'rejected'}
                        onClick={() => updateStatus(job.job_id, 'rejected')}
                      />
                      <ActionBtn
                        label="In Progress" icon={<RefreshCw size={13} />} color="#8b5cf6"
                        disabled={updating === job.job_id + 'in_progress'}
                        onClick={() => updateStatus(job.job_id, 'in_progress')}
                      />
                      <ActionBtn
                        label="View" icon={<Eye size={13} />} color="var(--accent)"
                        onClick={() => setViewJob(job)}
                      />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* View Modal */}
      {viewJob && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 9000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          onClick={() => setViewJob(null)}>
          <div className="glass glass-card" style={{ width: '520px', maxWidth: 'calc(100vw - 32px)', maxHeight: '90vh', overflowY: 'auto', padding: '2rem' }}
            onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0 }}>{viewJob.title}</h2>
              <button onClick={() => setViewJob(null)} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', fontSize: '1.5rem', cursor: 'pointer' }}>&times;</button>
            </div>
            <StatusBadge status={viewJob.status} />
            <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {[
                ['User', `${viewJob.user_info?.username || '—'} (${viewJob.user_info?.email || ''})`],
                ['Client', viewJob.client_name],
                ['Contact', viewJob.client_contact],
                ['Site Address', viewJob.site_address],
                ['Window / Door Type', viewJob.window_door_type],
                ['Quantity', viewJob.quantity],
                ['Start Date', viewJob.start_date],
                ['End Date', viewJob.end_date],
                ['Description', viewJob.description],
                ['Notes', viewJob.notes],
              ].map(([label, value]) => value && (
                <div key={label} style={{ display: 'flex', gap: '12px', padding: '8px 0', borderBottom: '1px solid var(--glass-border)' }}>
                  <span style={{ minWidth: '140px', color: 'var(--text-secondary)', fontWeight: 500, fontSize: '0.85rem' }}>{label}</span>
                  <span style={{ color: 'var(--text-primary)', fontSize: '0.9rem' }}>{value}</span>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '8px', marginTop: '1.5rem' }}>
              <ActionBtn label="Accept" icon={<Check size={14} />} color="#10b981" onClick={() => { updateStatus(viewJob.job_id, 'accepted'); setViewJob(null); }} />
              <ActionBtn label="Reject" icon={<X size={14} />} color="#ef4444" onClick={() => { updateStatus(viewJob.job_id, 'rejected'); setViewJob(null); }} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const ActionBtn = ({ label, icon, color, onClick, disabled }) => (
  <button
    onClick={onClick} disabled={disabled}
    style={{
      display: 'flex', alignItems: 'center', gap: '4px',
      padding: '5px 10px', borderRadius: '6px', border: `1px solid ${color}`,
      background: `${color}18`, color, fontSize: '12px', fontWeight: 600,
      cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.45 : 1,
      transition: 'opacity 0.15s',
    }}
  >
    {icon} {label}
  </button>
);

export default AdminJobsPage;
