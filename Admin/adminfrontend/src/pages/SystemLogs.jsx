import React, { useEffect, useState, useContext } from 'react';
import axios from 'axios';
import { 
  Terminal, AlertCircle, CheckCircle, Info, RefreshCw, 
  Filter, Trash2, Search, Calendar, Download, BarChart2,
  ChevronDown, X
} from 'lucide-react';
import { AuthContext } from '../AuthContext';

const SystemLogs = () => {
  const { admin, loading: authLoading } = useContext(AuthContext);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState({ INFO: 0, WARNING: 0, ERROR: 0 });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('ALL');
  const [source, setSource] = useState('admin');
  const [search, setSearch] = useState('');
  const [dateRange, setDateRange] = useState('all'); // all, today, week
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchLogs = async (currentFilter = filter, currentSource = source, currentSearch = search) => {
    if (authLoading) return;
    try {
      setLoading(true);
      let url = `/api/logs/?level=${currentFilter}&source=${currentSource}&limit=100`;
      if (currentSearch) url += `&search=${encodeURIComponent(currentSearch)}`;
      
      const res = await axios.get(url);
      setLogs(res.data.logs || []);
      fetchStats(currentSource);
    } catch (err) {
      console.error("DEBUG: SystemLogs Failed to load logs", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async (currentSource = source) => {
    try {
      const res = await axios.get(`/api/logs/stats?source=${currentSource}`);
      setStats(res.data);
    } catch (err) {
      console.error("Failed to fetch log stats", err);
    }
  };

  useEffect(() => {
    fetchLogs(filter, source, search);
    
    let interval;
    if (autoRefresh) {
      interval = setInterval(() => fetchLogs(filter, source, search), 10000);
    }
    return () => clearInterval(interval);
  }, [admin, authLoading, filter, source, search, autoRefresh]);

  const handleExport = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(logs, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href",     dataStr);
    downloadAnchorNode.setAttribute("download", `system_logs_${source}_${new Date().toISOString()}.json`);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  const handleClear = async () => {
    if (!window.confirm(`Are you sure you want to clear all ${source} logs? This action cannot be undone.`)) return;
    try {
      await axios.delete(`/api/logs/clear?source=${source}`);
      fetchLogs();
    } catch (err) {
      console.error("Failed to clear logs", err);
      alert("Failed to clear logs");
    }
  };

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
        <div style={{ visibility: 'hidden', pointerEvents: 'none' }}>
          <h1 style={{ margin: 0 }}>System Audit Logs</h1>
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
          <button onClick={() => fetchLogs(filter, source, search)} className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '0.5rem 1rem', borderRadius: '8px' }}>
            <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
          </button>
        </div>
      </div>
      
      {/* Activity Stats Board */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div className="glass card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem', borderLeft: '4px solid #3b82f6' }}>
          <div style={{ background: 'rgba(59, 130, 246, 0.1)', padding: '10px', borderRadius: '12px' }}><Info color="#3b82f6" /></div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600 }}>INFO LOGS</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{stats.INFO || 0}</div>
          </div>
        </div>
        <div className="glass card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem', borderLeft: '4px solid #f59e0b' }}>
          <div style={{ background: 'rgba(245, 158, 11, 0.1)', padding: '10px', borderRadius: '12px' }}><AlertCircle color="#f59e0b" /></div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600 }}>WARNINGS</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{stats.WARNING || 0}</div>
          </div>
        </div>
        <div className="glass card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem', borderLeft: '4px solid #ef4444' }}>
          <div style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '10px', borderRadius: '12px' }}><X color="#ef4444" /></div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600 }}>ERRORS</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{stats.ERROR || 0}</div>
          </div>
        </div>
        <div className="glass card" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem', borderLeft: '4px solid #a855f7' }}>
          <div style={{ background: 'rgba(168, 85, 247, 0.1)', padding: '10px', borderRadius: '12px' }}><BarChart2 color="#a855f7" /></div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600 }}>FETCHED</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{logs.length}</div>
          </div>
        </div>
      </div>

      <div className="glass glass-card" style={{ padding: '0', overflow: 'hidden', backgroundColor: '#0f172a', border: '1px solid #334155' }}>
        {/* Terminal Header / Toolbar */}
        <div style={{ backgroundColor: '#1e293b', padding: '0.75rem 1.25rem', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <div style={{ display: 'flex', background: '#0f172a', borderRadius: '6px', padding: '2px', border: '1px solid #334155', marginRight: '0.5rem' }}>
              {['ALL', 'INFO', 'WARNING', 'ERROR'].map(lvl => (
                <button 
                  key={lvl}
                  onClick={() => setFilter(lvl)}
                  style={{
                    fontSize: '0.65rem', fontWeight: 700, padding: '4px 10px', borderRadius: '4px',
                    background: filter === lvl ? '#334155' : 'transparent',
                    color: filter === lvl ? '#fff' : '#94a3b8', border: 'none', cursor: 'pointer', transition: 'all 0.2s'
                  }}
                >
                  {lvl}
                </button>
              ))}
            </div>
            
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <Search size={14} style={{ position: 'absolute', left: '10px', color: '#64748b' }} />
              <input 
                type="text" 
                placeholder="Search logs..." 
                value={search}
                onChange={e => setSearch(e.target.value)}
                style={{ 
                  background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', 
                  padding: '6px 12px 6px 32px', color: '#f1f5f9', fontSize: '0.75rem', width: '200px',
                  outline: 'none'
                }}
              />
              {search && <X size={14} onClick={() => setSearch('')} style={{ position: 'absolute', right: '10px', color: '#64748b', cursor: 'pointer' }} />}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.75rem', color: '#94a3b8' }}>
             <button 
                onClick={handleExport}
                title="Export to JSON" 
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center', transition: 'color 0.2s' }}
                onMouseOver={e => e.currentTarget.style.color = '#fff'}
                onMouseOut={e => e.currentTarget.style.color = '#94a3b8'}
             >
                <Download size={16} />
             </button>
             <button 
                onClick={handleClear}
                title="Clear Logs" 
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center', transition: 'color 0.2s' }}
                onMouseOver={e => e.currentTarget.style.color = '#ef4444'}
                onMouseOut={e => e.currentTarget.style.color = '#94a3b8'}
             >
                <Trash2 size={16} />
             </button>
             <span style={{ opacity: 0.3 }}>|</span>
             <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                <input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} style={{ accentColor: '#3b82f6' }} />
                Live
             </label>
             <span style={{ opacity: 0.3 }}>|</span>
             <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#64748b' }}><Terminal size={14} /> terminal.log</div>
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
