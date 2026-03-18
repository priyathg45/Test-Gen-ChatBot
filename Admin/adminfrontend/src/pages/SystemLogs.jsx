import React, { useEffect, useState, useContext } from 'react';
import axios from 'axios';
import { Terminal, AlertCircle, CheckCircle, Info, RefreshCw, Filter, Trash2 } from 'lucide-react';
import { AuthContext } from '../AuthContext';

const SystemLogs = () => {
  const { admin, loading: authLoading } = useContext(AuthContext);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [source, setSource] = useState('admin');
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchLogs = async (currentFilter = filter, currentSource = source) => {
    if (authLoading) return;
    try {
      setLoading(true);
      const res = await axios.get(`/api/logs/?level=${currentFilter}&source=${currentSource}&limit=100`);
      setLogs(res.data.logs || []);
    } catch (err) {
      console.error("DEBUG: SystemLogs Failed to load logs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs(filter, source);
    
    let interval;
    if (autoRefresh) {
      interval = setInterval(() => fetchLogs(filter, source), 10000); // Pulse every 10s
    }
    return () => clearInterval(interval);
  }, [admin, authLoading, filter, source, autoRefresh]);

  const getLogIcon = (level, logSource) => {
    if (logSource === 'user') return <Terminal size={14} color="#a855f7" />;
    switch(level) {
      case 'ERROR': return <AlertCircle size={14} color="#ef4444" />;
      case 'WARNING': return <AlertCircle size={14} color="#f59e0b" />;
      case 'INFO': return <Info size={14} color="#3b82f6" />;
      case 'SUCCESS': return <CheckCircle size={14} color="#10b981" />;
      default: return <Terminal size={14} color="#94a3b8" />;
    }
  };

  const getLogColor = (level) => {
    switch(level) {
      case 'ERROR': return '#ef4444';
      case 'WARNING': return '#f59e0b';
      case 'INFO': return '#3b82f6';
      case 'SUCCESS': return '#10b981';
      default: return '#94a3b8';
    }
  };

  return (
    <div className="logs-container">
      <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.25rem' }}>System Audit Logs</h1>
          <p style={{ color: 'var(--text-secondary)' }}>
            Real-time activity monitoring for <b>{source === 'admin' ? 'Admin Panel' : 'User Chatbot'}</b>.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <div className="glass" style={{ display: 'flex', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
            <button 
              onClick={() => setSource('admin')} 
              style={{ 
                padding: '6px 16px', borderRadius: '7px', border: 'none', cursor: 'pointer',
                background: source === 'admin' ? 'var(--primary-color)' : 'transparent',
                color: source === 'admin' ? '#fff' : 'var(--text-secondary)',
                fontWeight: 600, transition: 'all 0.2s'
              }}
            >
              Admin Side
            </button>
            <button 
              onClick={() => setSource('user')} 
              style={{ 
                padding: '6px 16px', borderRadius: '7px', border: 'none', cursor: 'pointer',
                background: source === 'user' ? '#a855f7' : 'transparent',
                color: source === 'user' ? '#fff' : 'var(--text-secondary)',
                fontWeight: 600, transition: 'all 0.2s'
              }}
            >
              User Side
            </button>
          </div>
          <button onClick={() => fetchLogs(filter, source)} className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '0.5rem 1rem', borderRadius: '8px' }}>
            <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      <div className="glass glass-card" style={{ padding: '0', overflow: 'hidden', backgroundColor: '#0f172a', border: '1px solid #334155' }}>
        {/* Terminal Header / Toolbar */}
        <div style={{ backgroundColor: '#1e293b', padding: '0.75rem 1.25rem', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {['ALL', 'INFO', 'WARNING', 'ERROR'].map(lvl => (
              <button 
                key={lvl}
                onClick={() => setFilter(lvl)}
                style={{
                  fontSize: '0.7rem', fontWeight: 700, padding: '4px 10px', borderRadius: '4px',
                  background: filter === lvl ? '#334155' : 'transparent',
                  color: filter === lvl ? '#fff' : '#94a3b8', border: '1px solid #334155', cursor: 'pointer'
                }}
              >
                {lvl}
              </button>
            ))}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.75rem', color: '#94a3b8' }}>
             <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                <input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} style={{ accentColor: '#3b82f6' }} />
                Auto-refresh
             </label>
             <span style={{ opacity: 0.5 }}>|</span>
             <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}><Terminal size={14} /> app.log</div>
          </div>
        </div>

        {/* Terminal Body */}
        <div className="terminal-body" style={{ 
          padding: '1.25rem', height: '65vh', overflowY: 'auto', 
          fontFamily: '"JetBrains Mono", "Fira Code", monospace', fontSize: '0.82rem', 
          lineHeight: 1.6, scrollBehavior: 'smooth' 
        }}>
          {loading && logs.length === 0 ? (
            <div style={{ color: '#64748b', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <RefreshCw size={14} className="spin" /> Initializing log stream...
            </div>
          ) : logs.length === 0 ? (
            <div style={{ color: '#64748b', textAlign: 'center', paddingTop: '4rem' }}>
              No {source} logs found for the selected filter.
            </div>
          ) : (
            logs.map((log, idx) => (
              <div key={log.id || idx} className="log-line" style={{ display: 'flex', gap: '1rem', marginBottom: '4px', padding: '4px 8px', borderRadius: '6px', borderLeft: `3px solid ${log.source === 'user' ? '#a855f7' : getLogColor(log.level)}` }}>
                <span style={{ color: '#64748b', minWidth: '140px', userSelect: 'none', fontSize: '0.75rem' }}>
                  {log.timestamp ? new Date(log.timestamp).toLocaleString('en-GB', { hour12: false, month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }).replace(',', '') : '---'}
                </span>
                <span style={{ color: log.source === 'user' ? '#a855f7' : getLogColor(log.level), fontWeight: 700, minWidth: '70px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {getLogIcon(log.level, log.source)}
                  {log.level.padEnd(7)}
                </span>
                <span style={{ color: '#94a3b8', fontStyle: 'italic', minWidth: '140px', fontSize: '0.75rem', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  [{log.user || 'system'}]
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ color: log.level === 'ERROR' ? '#ef4444' : log.level === 'WARNING' ? '#fbbf24' : '#e2e8f0' }}>
                    {log.message}
                  </div>
                  {log.details && Object.keys(log.details).length > 0 && (
                    <div style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '2px', background: '#020617', padding: '2px 6px', borderRadius: '4px', display: 'inline-block' }}>
                      {JSON.stringify(log.details)}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <style>{`
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .log-line:hover { background: rgba(255,255,255,0.03); }
        .terminal-body::-webkit-scrollbar { width: 8px; }
        .terminal-body::-webkit-scrollbar-track { background: transparent; }
        .terminal-body::-webkit-scrollbar-thumb { background: #334155; borderRadius: 4px; }
        .logs-container { animation: fadeIn 0.4s ease-out; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
      `}</style>
    </div>
  );
};

export default SystemLogs;
