import React, { useEffect, useState, useContext, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  ArrowLeft, Mail, Calendar, MessageCircle, Clock, 
  Briefcase, UserCheck, UserX, Trash2, ChevronRight, 
  MessageSquare, Trash, Search, Paperclip, Download, Eye
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { AuthContext } from '../AuthContext';

const StatusBadge = ({ isActive }) => (
  <span style={{
    padding: '3px 10px', borderRadius: '12px', fontSize: '11px', fontWeight: 700,
    background: isActive ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
    color: isActive ? '#10b981' : '#ef4444',
  }}>
    {isActive ? 'Active' : 'Inactive'}
  </span>
);

const UserProfile = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { token } = useContext(AuthContext);

  const toRefId = (sessionId) => {
    const clean = (sessionId || '').replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
    return 'REF-' + clean.slice(-8).padStart(8, '0');
  };
  
  const [user, setUser] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [sessionMessages, setSessionMessages] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('profile'); // 'profile', 'chat', 'jobs'
  const [msgLoading, setMsgLoading] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [sessionSearch, setSessionSearch] = useState('');
  const [attachments, setAttachments] = useState([]);
  const [attLoading, setAttLoading] = useState(false);

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [uRes, sRes, jRes] = await Promise.all([
        axios.get(`/api/users/${id}`, { headers }),
        axios.get(`/api/chat/user/${id}/sessions`, { headers }),
        axios.get(`/api/jobs/`, { headers })
      ]);
      
      setUser(uRes.data.user);
      setSessions(sRes.data.sessions || []);
      // Filter jobs for this user
      const userJobs = (jRes.data.jobs || []).filter(j => j.user_id === id);
      setJobs(userJobs);
    } catch (err) {
      console.error("Error fetching user profile data", err);
    } finally {
      setLoading(false);
    }
  }, [id, token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const loadSessionContent = async (sessionId) => {
    setActiveSession(sessionId);
    setMsgLoading(true);
    setAttLoading(true);
    try {
      const [msgRes, attRes] = await Promise.all([
        axios.get(`/api/chat/session/${sessionId}/messages`, { headers }),
        axios.get(`/api/chat/session/${sessionId}/attachments`, { headers })
      ]);
      setSessionMessages(msgRes.data.messages || []);
      setAttachments(attRes.data.attachments || []);
    } catch (err) {
      console.error("Error loading session content", err);
    } finally {
      setMsgLoading(false);
      setAttLoading(false);
    }
  };

  const handleDownload = async (att) => {
    try {
      const response = await axios.get(`/api/chat/attachment/${att._id}/download`, {
        headers,
        responseType: 'blob'
      });
      
      // Check if response is actually a JSON error hidden in a blob
      if (response.data.type === 'application/json') {
        const text = await response.data.text();
        const error = JSON.parse(text);
        alert(`Download failed: ${error.error || 'Unknown error'}`);
        return;
      }

      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', att.filename || 'download');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download error:", err);
      alert("Failed to download file. Please check server logs.");
    }
  };

  const handleToggleActive = async () => {
    if (!user) return;
    const endpoint = user.is_active !== false ? 'deactivate' : 'activate';
    setToggling(true);
    try {
      await axios.put(`/api/users/${id}/${endpoint}`, {}, { headers });
      setUser(prev => ({ ...prev, is_active: !prev.is_active }));
    } catch {
      alert(`Failed to ${endpoint} user`);
    } finally {
      setToggling(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to permanently delete this user? This cannot be undone.')) return;
    try {
      await axios.delete(`/api/users/${id}`, { headers });
      navigate('/users');
    } catch {
      alert('Failed to delete user');
    }
  };

  if (loading) return <div style={styles.loading}>Loading user profile...</div>;
  if (!user) return <div style={styles.loading}>User not found.</div>;

  return (
    <div style={{ paddingBottom: '2rem' }}>
      {/* Header */}
      <div style={styles.header}>
        <button onClick={() => navigate('/users')} style={styles.backBtn}>
          <ArrowLeft size={18} /> Back to Users
        </button>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button 
            onClick={handleToggleActive} disabled={toggling}
            className={`btn ${user.is_active !== false ? 'btn-danger' : 'btn-primary'}`}
            style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            {user.is_active !== false ? <UserX size={16} /> : <UserCheck size={16} />}
            {user.is_active !== false ? 'Deactivate' : 'Activate'}
          </button>
          <button 
            onClick={handleDelete}
            className="btn" style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444', border: '1px solid #ef4444', padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Trash2 size={16} /> Delete User
          </button>
        </div>
      </div>

      <div style={styles.mainGrid}>
        {/* Sidebar info */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="glass glass-card" style={styles.profileCard}>
            <div style={styles.avatarLarge}>
               {user.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <h2 style={{margin: '1rem 0 0.25rem 0'}}>{user.username}</h2>
            <StatusBadge isActive={user.is_active !== false} />
            
            <div style={styles.infoList}>
              <div style={styles.infoItem}>
                <Mail size={16} color="var(--accent)" />
                <div style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{user.email || 'N/A'}</div>
              </div>
              <div style={styles.infoItem}>
                <Calendar size={16} color="var(--accent)" />
                <span>Joined {new Date(user.created_at).toLocaleDateString()}</span>
              </div>
              <div style={styles.infoItem}>
                <MessageSquare size={16} color="var(--accent)" />
                <span>{sessions.length} Chat Sessions</span>
              </div>
              <div style={styles.infoItem}>
                <Briefcase size={16} color="var(--accent)" />
                <span>{jobs.length} Jobs Placed</span>
              </div>
            </div>
          </div>

          <div className="glass glass-card" style={{ padding: '0.5rem' }}>
            {['profile', 'chat', 'jobs'].map(tab => (
              <button 
                key={tab} onClick={() => setActiveTab(tab)}
                style={{
                  ...styles.tabBtn,
                  background: activeTab === tab ? 'rgba(59,130,246,0.15)' : 'transparent',
                  color: activeTab === tab ? 'var(--accent)' : 'var(--text-secondary)',
                  fontWeight: activeTab === tab ? 700 : 500,
                }}
              >
                {tab === 'profile' && <UserCheck size={18} />}
                {tab === 'chat' && <MessageCircle size={18} />}
                {tab === 'jobs' && <Briefcase size={18} />}
                {tab.charAt(0).toUpperCase() + tab.slice(1)} Details
              </button>
            ))}
          </div>
        </div>

        {/* Dynamic Content area */}
        <div className="glass glass-card" style={{ minHeight: '500px', display: 'flex', flexDirection: 'column' }}>
          {activeTab === 'profile' && (
            <div style={{ padding: '0.5rem' }}>
              <h3 style={styles.tabHeader}>User Profile Details</h3>
              <div style={styles.detailGrid}>
                {Object.entries({
                   "Username": user.username,
                   "Email": user.email,
                   "User ID": user._id,
                   "Role": user.role || 'user',
                   "Account Status": user.is_active !== false ? 'Active' : 'Inactive',
                   "Member Since": user.created_at ? new Date(user.created_at).toLocaleString() : 'N/A',
                   "Last Update": user.updated_at ? new Date(user.updated_at).toLocaleString() : 'N/A'
                }).map(([k,v]) => (
                  <div key={k} style={styles.detailItem}>
                    <span style={styles.detailLabel}>{k}</span>
                    <span style={styles.detailValue}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'chat' && (
            <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: '1px', background: 'var(--glass-border)', flex: 1, borderRadius: '8px', overflow: 'hidden' }}>
              {/* Sessions Sidebar */}
              <div style={{ background: 'rgba(15,23,42,0.3)', overflowY: 'auto', maxHeight: '700px', display: 'flex', flexDirection: 'column' }}>
                <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderBottom: '1px solid var(--glass-border)' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.75rem', textTransform: 'uppercase' }}>
                    Sessions ({sessions.length})
                  </div>
                  <div style={{ position: 'relative' }}>
                    <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', opacity: 0.5 }} />
                    <input 
                      type="text" placeholder="Search sessions..." 
                      value={sessionSearch} onChange={e => setSessionSearch(e.target.value)}
                      style={{ 
                        width: '100%', padding: '6px 10px 6px 30px', background: 'rgba(0,0,0,0.2)', 
                        border: '1px solid var(--glass-border)', borderRadius: '6px', fontSize: '0.8rem', color: '#fff' 
                      }} 
                    />
                  </div>
                </div>
                <div style={{ flex: 1, overflowY: 'auto' }}>
                  {sessions.filter(s => 
                    s.title?.toLowerCase().includes(sessionSearch.toLowerCase()) || 
                    s.session_id?.toLowerCase().includes(sessionSearch.toLowerCase())
                  ).length === 0 ? (
                    <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>No sessions found.</div>
                  ) : sessions.filter(s => 
                    s.title?.toLowerCase().includes(sessionSearch.toLowerCase()) || 
                    s.session_id?.toLowerCase().includes(sessionSearch.toLowerCase())
                  ).map(s => (
                    <div 
                      key={s._id} onClick={() => loadSessionContent(s._id)}
                      style={{
                        ...styles.sessionItem,
                        background: activeSession === s._id ? 'rgba(59,130,246,0.1)' : 'transparent',
                        borderLeft: activeSession === s._id ? '3px solid var(--accent)' : '3px solid transparent',
                      }}
                    >
                      <div style={{ fontWeight: 600, fontSize: '0.85rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.title || 'Untitled Session'}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--accent)', marginTop: '4px', fontWeight: 700 }}>{toRefId(s.session_id)}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginTop: '2px' }}>{new Date(s.started_at).toLocaleString()}</div>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Messages Panel */}
              <div style={{ background: 'rgba(15,23,42,0.45)', display: 'flex', flexDirection: 'column', maxHeight: '700px' }}>
                 {!activeSession ? (
                   <div style={styles.emptyContent}>
                     <MessageSquare size={48} color="var(--glass-border)" style={{ marginBottom: '1rem' }} />
                     <p>Select a chat session to view history</p>
                   </div>
                 ) : msgLoading ? (
                   <div style={styles.emptyContent}>Loading messages...</div>
                 ) : (
                   <>
                    {/* Session Header */}
                    <div style={{ padding: '0.75rem 1.5rem', background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                       <div>
                          <div style={{ fontSize: '0.65rem', color: 'var(--accent)', fontWeight: 800, textTransform: 'uppercase' }}>Reference ID</div>
                          <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {toRefId(activeSession)}
                            <span style={{ fontSize: '0.7rem', opacity: 0.5, fontWeight: 400 }}>(Full ID: {activeSession})</span>
                          </div>
                       </div>
                       {attachments.length > 0 && (
                         <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                           <Paperclip size={14} /> {attachments.length} attached
                         </div>
                       )}
                    </div>

                    <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                       {/* Attachments Section at top */}
                       {attachments.length > 0 && (
                         <div style={{ marginBottom: '1rem' }}>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.5rem', fontWeight: 600 }}>SESSION ATTACHMENTS</div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem' }}>
                              {attachments.map(att => (
                                <div key={att._id} style={styles.attachmentChip}>
                                  <Paperclip size={14} />
                                  <span style={{ fontSize: '0.8rem', maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{att.filename}</span>
                                  <div style={{ display: 'flex', gap: '4px', marginLeft: '8px' }}>
                                    <button onClick={() => handleDownload(att)} style={styles.attBtn} title="Download"><Download size={14} /></button>
                                  </div>
                                </div>
                              ))}
                            </div>
                         </div>
                       )}

                       {sessionMessages.length === 0 ? (
                         <p style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No messages in this session.</p>
                       ) : sessionMessages.map((m, idx) => (
                         <div key={idx} style={{ 
                           alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                           maxWidth: '90%',
                           display: 'flex', flexDirection: 'column',
                           alignItems: m.role === 'user' ? 'flex-end' : 'flex-start'
                         }}>
                            <div className="markdown-container" style={{
                              padding: '1rem 1.25rem',
                              borderRadius: m.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                              background: m.role === 'user' ? 'var(--accent)' : 'rgba(255,255,255,0.07)',
                              color: m.role === 'user' ? '#fff' : '#E2E8F0',
                              fontSize: '0.92rem',
                              border: m.role === 'user' ? 'none' : '1px solid rgba(255,255,255,0.1)',
                              lineHeight: 1.6,
                              boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                            }}>
                               <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                 {m.content}
                               </ReactMarkdown>
                            </div>
                            <span style={{ fontSize: '0.68rem', color: 'var(--text-secondary)', marginTop: '6px', fontWeight: 500 }}>
                              {m.role === 'assistant' ? 'GENESIS AI' : user.username.toUpperCase()} • {new Date(m.timestamp).toLocaleString()}
                            </span>
                         </div>
                       ))}
                    </div>
                   </>
                 )}
              </div>
            </div>
          )}

          {activeTab === 'jobs' && (
            <div style={{ padding: '0.5rem' }}>
              <h3 style={styles.tabHeader}>User Job Placements</h3>
              {jobs.length === 0 ? (
                <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  <Briefcase size={40} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                  <p>No jobs placed by this user yet.</p>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {jobs.map(job => (
                    <div key={job.job_id} className="glass" style={styles.jobRow} onClick={() => navigate('/jobs')}>
                       <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 700, fontSize: '1rem' }}>{job.title}</div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>ID: {job.job_id} • Client: {job.client_name}</div>
                       </div>
                       <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                         <span style={{ 
                            fontSize: '11px', fontWeight: 800, textTransform: 'uppercase',
                            color: job.status === 'pending' ? '#f59e0b' : job.status === 'accepted' ? '#3b82f6' : '#10b981'
                         }}>{job.status}</span>
                         <ChevronRight size={18} color="var(--text-secondary)" />
                       </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const styles = {
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' },
  backBtn: { background: 'none', border: '1px solid var(--glass-border)', color: 'var(--text-primary)', padding: '0.5rem 1rem', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.9rem' },
  mainGrid: { display: 'grid', gridTemplateColumns: '300px 1fr', gap: '1.5rem' },
  profileCard: { display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2rem 1.5rem' },
  avatarLarge: { width: 80, height: 80, borderRadius: '24px', background: 'rgba(59,130,246,0.15)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2.5rem', fontWeight: 800, border: '1px solid rgba(59,130,246,0.3)' },
  infoList: { width: '100%', marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.8rem' },
  infoItem: { display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.85rem', color: 'var(--text-secondary)' },
  tabBtn: { width: '100%', padding: '0.85rem 1rem', border: 'none', borderRadius: '8px', cursor: 'pointer', textAlign: 'left', display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '4px', transition: 'all 0.2s' },
  tabHeader: { padding: '1rem', borderBottom: '1px solid var(--glass-border)', margin: 0, fontSize: '1.1rem' },
  detailGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', padding: '1.5rem' },
  detailItem: { display: 'flex', flexDirection: 'column', gap: '4px' },
  detailLabel: { fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: 600, letterSpacing: '0.05em' },
  detailValue: { fontSize: '0.95rem', fontWeight: 500 },
  sessionItem: { padding: '1rem', cursor: 'pointer', borderBottom: '1px solid rgba(255,255,255,0.03)', transition: 'background 0.2s' },
  emptyContent: { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', fontSize: '0.9rem' },
  jobRow: { padding: '1.25rem', display: 'flex', alignItems: 'center', border: '1px solid var(--glass-border)', cursor: 'pointer', transition: 'transform 0.2s' },
  loading: { padding: '5rem', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '1.1rem' },
  attachmentChip: { display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', borderRadius: '20px', color: 'var(--text-primary)' },
  attBtn: { background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', padding: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '4px', transition: 'background 0.2s', ':hover': { background: 'rgba(59,130,246,0.1)' } }
};

export default UserProfile;
