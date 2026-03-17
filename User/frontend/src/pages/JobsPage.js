import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { CHAT_API_URL } from '../config';
import { useAuth } from '../context/AuthContext';
import './JobsPage.css';

const STATUS_COLORS = {
  pending: '#f59e0b',
  confirmed: '#3b82f6',
  in_progress: '#8b5cf6',
  completed: '#10b981',
  cancelled: '#ef4444',
};

const EMPTY_JOB = {
  title: '', client_name: '', client_contact: '', site_address: '',
  start_date: '', end_date: '', window_door_type: '', quantity: '',
  description: '', notes: '', status: 'pending',
};

const STATUS_OPTIONS = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled'];

export default function JobsPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editJob, setEditJob] = useState(null);        // job being edited
  const [editFields, setEditFields] = useState(EMPTY_JOB);
  const [saving, setSaving] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [searchQ, setSearchQ] = useState('');

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res = await fetch(`${CHAT_API_URL}/jobs`, { headers });
      const data = await res.json();
      if (data.success) setJobs(data.jobs || []);
      else setError(data.error || 'Failed to load jobs.');
    } catch {
      setError('Cannot reach the server.');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  const openEdit = (job) => {
    setEditJob(job);
    setEditFields({ ...EMPTY_JOB, ...job });
  };

  const closeEdit = () => { setEditJob(null); setEditFields(EMPTY_JOB); };

  const handleEditChange = (e) => {
    const { name, value } = e.target;
    setEditFields(f => ({ ...f, [name]: value }));
  };

  const handleEditSave = async (e) => {
    e.preventDefault();
    if (!editFields.title.trim()) return;
    setSaving(true);
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res = await fetch(`${CHAT_API_URL}/jobs/${editJob.job_id}`, {
        method: 'PUT', headers, body: JSON.stringify(editFields),
      });
      const data = await res.json();
      if (data.success) {
        setJobs(prev => prev.map(j => j.job_id === editJob.job_id ? data.job : j));
        closeEdit();
      }
    } catch { /* ignore */ }
    finally { setSaving(false); }
  };

  const handleDelete = async (jobId) => {
    setDeleteId(jobId);
    if (!window.confirm('Delete this job? This cannot be undone.')) { setDeleteId(null); return; }
    try {
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      await fetch(`${CHAT_API_URL}/jobs/${jobId}`, { method: 'DELETE', headers });
      setJobs(prev => prev.filter(j => j.job_id !== jobId));
    } catch { /* ignore */ }
    finally { setDeleteId(null); }
  };

  const filtered = jobs.filter(j => {
    if (!searchQ.trim()) return true;
    const q = searchQ.toLowerCase();
    return (
      (j.title || '').toLowerCase().includes(q) ||
      (j.client_name || '').toLowerCase().includes(q) ||
      (j.site_address || '').toLowerCase().includes(q) ||
      (j.status || '').toLowerCase().includes(q)
    );
  });

  return (
    <div className="jobs-page">
      <div className="jobs-header">
        <div>
          <h1><i className="fa fa-briefcase" /> Jobs</h1>
          <p>{jobs.length} job{jobs.length !== 1 ? 's' : ''} total</p>
        </div>
        <div className="jobs-header-actions">
          <input
            className="jobs-search"
            type="text"
            placeholder="Search jobs…"
            value={searchQ}
            onChange={e => setSearchQ(e.target.value)}
          />
        </div>
      </div>

      {error && <div className="jobs-error">{error}</div>}

      {loading ? (
        <div className="jobs-loading"><i className="fa fa-spinner fa-spin" /> Loading jobs…</div>
      ) : filtered.length === 0 ? (
        <div className="jobs-empty">
          <i className="fa fa-folder-open" />
          <p>{searchQ ? 'No jobs match your search.' : 'No jobs yet. Create one from the chatbot!'}</p>
        </div>
      ) : (
        <div className="jobs-table-wrap">
          <table className="jobs-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Title</th>
                <th>Client</th>
                <th>Site Address</th>
                <th>Type / Qty</th>
                <th>Dates</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((job, idx) => (
                <tr key={job.job_id}>
                  <td className="jobs-num">{idx + 1}</td>
                  <td className="jobs-title">{job.title || '—'}</td>
                  <td>{job.client_name || '—'}</td>
                  <td className="jobs-address">{job.site_address || '—'}</td>
                  <td>{[job.window_door_type, job.quantity].filter(Boolean).join(' / ') || '—'}</td>
                  <td className="jobs-dates">
                    {job.start_date && <span>{job.start_date}</span>}
                    {job.start_date && job.end_date && <span className="jobs-dates-sep">→</span>}
                    {job.end_date && <span>{job.end_date}</span>}
                    {!job.start_date && !job.end_date && '—'}
                  </td>
                  <td>
                    <span className="jobs-status-badge" style={{ background: STATUS_COLORS[job.status] || '#999' }}>
                      {(job.status || 'pending').replace('_', ' ')}
                    </span>
                  </td>
                  <td className="jobs-actions-cell">
                    <button
                      className="jobs-btn jobs-btn-view"
                      onClick={() => navigate(`/jobs/${job.job_id}`)}
                      title="View details"
                    >
                      <i className="fa fa-eye" />
                    </button>
                    <button
                      className="jobs-btn jobs-btn-edit"
                      onClick={() => openEdit(job)}
                      title="Edit"
                    >
                      <i className="fa fa-pencil" />
                    </button>
                    <button
                      className="jobs-btn jobs-btn-delete"
                      onClick={() => handleDelete(job.job_id)}
                      title="Delete"
                      disabled={deleteId === job.job_id}
                    >
                      <i className={`fa ${deleteId === job.job_id ? 'fa-spinner fa-spin' : 'fa-trash'}`} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Edit Modal */}
      {editJob && (
        <div className="jobs-modal-overlay" onClick={closeEdit}>
          <div className="jobs-modal" onClick={e => e.stopPropagation()}>
            <div className="jobs-modal-header">
              <h3><i className="fa fa-pencil" /> Edit Job</h3>
              <button className="jobs-modal-close" onClick={closeEdit}>&times;</button>
            </div>
            <form className="jm-form" onSubmit={handleEditSave}>
              <div className="jm-row">
                <div className="jm-field jm-full">
                  <label>Job Title *</label>
                  <input name="title" value={editFields.title} onChange={handleEditChange} required />
                </div>
              </div>
              <div className="jm-row">
                <div className="jm-field">
                  <label>Client Name</label>
                  <input name="client_name" value={editFields.client_name} onChange={handleEditChange} />
                </div>
                <div className="jm-field">
                  <label>Client Contact</label>
                  <input name="client_contact" value={editFields.client_contact} onChange={handleEditChange} />
                </div>
              </div>
              <div className="jm-row">
                <div className="jm-field jm-full">
                  <label>Site Address</label>
                  <input name="site_address" value={editFields.site_address} onChange={handleEditChange} />
                </div>
              </div>
              <div className="jm-row">
                <div className="jm-field">
                  <label>Start Date</label>
                  <input type="date" name="start_date" value={editFields.start_date} onChange={handleEditChange} />
                </div>
                <div className="jm-field">
                  <label>End Date</label>
                  <input type="date" name="end_date" value={editFields.end_date} onChange={handleEditChange} />
                </div>
              </div>
              <div className="jm-row">
                <div className="jm-field">
                  <label>Window / Door Type</label>
                  <input name="window_door_type" value={editFields.window_door_type} onChange={handleEditChange} />
                </div>
                <div className="jm-field">
                  <label>Quantity</label>
                  <input name="quantity" value={editFields.quantity} onChange={handleEditChange} />
                </div>
              </div>
              <div className="jm-row">
                <div className="jm-field jm-full">
                  <label>Description</label>
                  <textarea name="description" value={editFields.description} onChange={handleEditChange} rows={2} />
                </div>
              </div>
              <div className="jm-row">
                <div className="jm-field jm-full">
                  <label>Notes</label>
                  <textarea name="notes" value={editFields.notes} onChange={handleEditChange} rows={2} />
                </div>
              </div>
              <div className="jm-row">
                <div className="jm-field">
                  <label>Status</label>
                  <select name="status" value={editFields.status} onChange={handleEditChange}>
                    {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
                  </select>
                </div>
              </div>
              <div className="jm-actions">
                <button type="button" className="jm-btn-cancel" onClick={closeEdit}>Cancel</button>
                <button type="submit" className="jm-btn-save" disabled={saving}>
                  {saving ? <><i className="fa fa-spinner fa-spin" /> Saving…</> : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
