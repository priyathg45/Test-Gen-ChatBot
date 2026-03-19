import React, { useState } from 'react';
import { CHAT_API_URL } from '../config';
import { useAuth } from '../context/AuthContext';
import './JobFormCard.css';

const EMPTY = {
  title: '', client_name: '', client_contact: '', site_address: '',
  start_date: '', end_date: '', window_door_type: '', quantity: '',
  description: '', notes: '', status: 'pending',
};

const STATUS_OPTIONS = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled'];

const JobFormCard = ({ sessionId, onJobCreated }) => {
  const { token } = useAuth();
  const [fields, setFields] = useState(EMPTY);
  const [generating, setGenerating] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [genError, setGenError] = useState('');
  const [submitMsg, setSubmitMsg] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFields(f => ({ ...f, [name]: value }));
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setGenError('');
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res = await fetch(`${CHAT_API_URL}/jobs/extract-from-pdf`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ session_id: sessionId }),
      });
      const data = await res.json();
      if (data.success && data.fields) {
        setFields(f => ({ ...f, ...Object.fromEntries(Object.entries(data.fields).filter(([, v]) => v)) }));
      } else {
        setGenError(data.error || 'Could not extract fields from PDF.');
      }
    } catch (e) {
      setGenError('Failed to reach the server.');
    } finally {
      setGenerating(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!fields.title.trim()) { setGenError('Job title is required.'); return; }
    setSubmitting(true);
    setGenError('');
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res = await fetch(`${CHAT_API_URL}/jobs`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ ...fields, session_id: sessionId }),
      });
      const data = await res.json();
      if (data.success) {
        setSubmitMsg(`✅ Job "${data.job.title}" created! View it in the Jobs page.`);
        if (onJobCreated) onJobCreated(data.job);
      } else {
        setGenError(data.error || 'Failed to create job.');
      }
    } catch (e) {
      setGenError('Network error. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (submitMsg) {
    return (
      <div className="jfc-success">
        <i className="fa fa-check-circle" />
        <p>{submitMsg}</p>
        <a href="/jobs" className="jfc-view-btn">View Jobs →</a>
      </div>
    );
  }

  return (
    <div className="jfc-card">
      <div className="jfc-header">
        <i className="fa fa-briefcase" />
        <span>Create Job</span>
        <button
          type="button"
          className="jfc-gen-btn"
          onClick={handleGenerate}
          disabled={generating}
          title="Auto-fill from attached PDF"
        >
          {generating ? <><i className="fa fa-spinner fa-spin" /> Generating…</> : <><i className="fa fa-magic" /> Generate from PDF</>}
        </button>
      </div>
      {genError && <div className="jfc-error">{genError}</div>}
      <form className="jfc-form" onSubmit={handleSubmit}>
        <div className="jfc-row">
          <div className="jfc-field jfc-full">
            <label>Job Title *</label>
            <input name="title" value={fields.title} onChange={handleChange} placeholder="e.g. Window Installation — Smith Residence" required />
          </div>
        </div>
        <div className="jfc-row">
          <div className="jfc-field">
            <label>Client Name</label>
            <input name="client_name" value={fields.client_name} onChange={handleChange} placeholder="Full name" />
          </div>
          <div className="jfc-field">
            <label>Client Contact</label>
            <input name="client_contact" value={fields.client_contact} onChange={handleChange} placeholder="Email or phone" />
          </div>
        </div>
        <div className="jfc-row">
          <div className="jfc-field jfc-full">
            <label>Site Address</label>
            <input name="site_address" value={fields.site_address} onChange={handleChange} placeholder="Full site address" />
          </div>
        </div>
        <div className="jfc-row">
          <div className="jfc-field">
            <label>Start Date</label>
            <input type="date" name="start_date" value={fields.start_date} onChange={handleChange} />
          </div>
          <div className="jfc-field">
            <label>End Date</label>
            <input type="date" name="end_date" value={fields.end_date} onChange={handleChange} />
          </div>
        </div>
        <div className="jfc-row">
          <div className="jfc-field">
            <label>Window / Door Type</label>
            <input name="window_door_type" value={fields.window_door_type} onChange={handleChange} placeholder="e.g. Casement Window" />
          </div>
          <div className="jfc-field">
            <label>Quantity</label>
            <input name="quantity" value={fields.quantity} onChange={handleChange} placeholder="Number / description" />
          </div>
        </div>
        <div className="jfc-row">
          <div className="jfc-field jfc-full">
            <label>Description</label>
            <textarea name="description" value={fields.description} onChange={handleChange} rows={2} placeholder="Brief job description..." />
          </div>
        </div>
        <div className="jfc-row">
          <div className="jfc-field jfc-full">
            <label>Notes</label>
            <textarea name="notes" value={fields.notes} onChange={handleChange} rows={2} placeholder="Special requirements, notes..." />
          </div>
        </div>
        <div className="jfc-row">
          <div className="jfc-field">
            <label>Status</label>
            <select name="status" value={fields.status} onChange={handleChange}>
              {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
            </select>
          </div>
        </div>
        <div className="jfc-actions">
          <button type="submit" className="jfc-submit-btn" disabled={submitting}>
            {submitting ? <><i className="fa fa-spinner fa-spin" /> Placing Job…</> : <><i className="fa fa-paper-plane" /> Place Job</>}
          </button>
        </div>
      </form>
    </div>
  );
};

export default JobFormCard;
