import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
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

const InfoRow = ({ label, value }) => (
  <div className="vj-info-row">
    <span className="vj-label">{label}</span>
    <span className="vj-value">{value || <em className="vj-empty">—</em>}</span>
  </div>
);

export default function ViewJobPage() {
  const { jobId } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchJob = async () => {
      try {
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const res = await fetch(`${CHAT_API_URL}/jobs/${jobId}`, { headers });
        const data = await res.json();
        if (data.success) setJob(data.job);
        else setError(data.error || 'Job not found.');
      } catch {
        setError('Cannot reach the server.');
      } finally {
        setLoading(false);
      }
    };
    fetchJob();
  }, [jobId, token]);

  if (loading) return (
    <div className="vj-page">
      <div className="vj-loading"><i className="fa fa-spinner fa-spin" /> Loading job…</div>
    </div>
  );

  if (error || !job) return (
    <div className="vj-page">
      <div className="jobs-error">{error || 'Job not found.'}</div>
      <Link to="/jobs" className="vj-back-btn"><i className="fa fa-arrow-left" /> Back to Jobs</Link>
    </div>
  );

  const statusColor = STATUS_COLORS[job.status] || '#999';
  const createdAt = job.created_at ? new Date(job.created_at).toLocaleString() : '—';
  const updatedAt = job.updated_at ? new Date(job.updated_at).toLocaleString() : '—';

  return (
    <div className="vj-page">
      {/* Breadcrumb */}
      <div className="vj-breadcrumb">
        <Link to="/jobs"><i className="fa fa-briefcase" /> Jobs</Link>
        <span>/</span>
        <span>{job.title || 'Job Details'}</span>
      </div>

      {/* Header card */}
      <div className="vj-hero">
        <div className="vj-hero-left">
          <div className="vj-icon"><i className="fa fa-briefcase" /></div>
          <div>
            <h1 className="vj-title">{job.title || 'Untitled Job'}</h1>
            <p className="vj-subtitle">Job ID: <code>{job.job_id}</code></p>
          </div>
        </div>
        <div className="vj-hero-right">
          <span className="vj-status-badge" style={{ background: statusColor }}>
            {(job.status || 'pending').replace('_', ' ')}
          </span>
          <button className="vj-edit-btn" onClick={() => navigate('/jobs')}>
            <i className="fa fa-pencil" /> Edit
          </button>
        </div>
      </div>

      {/* Details grid */}
      <div className="vj-grid">
        {/* Client Info */}
        <div className="vj-card">
          <div className="vj-card-header"><i className="fa fa-user" /> Client Information</div>
          <InfoRow label="Client Name" value={job.client_name} />
          <InfoRow label="Contact" value={job.client_contact} />
          <InfoRow label="Site Address" value={job.site_address} />
        </div>

        {/* Job Details */}
        <div className="vj-card">
          <div className="vj-card-header"><i className="fa fa-cog" /> Job Details</div>
          <InfoRow label="Window / Door Type" value={job.window_door_type} />
          <InfoRow label="Quantity" value={job.quantity} />
          <InfoRow label="Start Date" value={job.start_date} />
          <InfoRow label="End Date" value={job.end_date} />
        </div>

        {/* Description */}
        {job.description && (
          <div className="vj-card vj-card-wide">
            <div className="vj-card-header"><i className="fa fa-file-text" /> Description</div>
            <p className="vj-body-text">{job.description}</p>
          </div>
        )}

        {/* Notes */}
        {job.notes && (
          <div className="vj-card vj-card-wide">
            <div className="vj-card-header"><i className="fa fa-sticky-note" /> Notes</div>
            <p className="vj-body-text">{job.notes}</p>
          </div>
        )}

        {/* Metadata */}
        <div className="vj-card vj-card-wide">
          <div className="vj-card-header"><i className="fa fa-info-circle" /> Record Info</div>
          <InfoRow label="Created" value={createdAt} />
          <InfoRow label="Last Updated" value={updatedAt} />
          {job.session_id && <InfoRow label="Chat Session" value={job.session_id} />}
        </div>
      </div>

      <div className="vj-footer-actions">
        <Link to="/jobs" className="vj-back-btn"><i className="fa fa-arrow-left" /> Back to Jobs</Link>
      </div>
    </div>
  );
}
