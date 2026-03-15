import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Terminal, AlertCircle, CheckCircle, Info } from 'lucide-react';

const SystemLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await axios.get('/api/logs');
        setLogs(res.data.logs);
      } catch (err) {
        console.error("Failed to load logs", err);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  const getLogIcon = (level) => {
    switch(level) {
      case 'ERROR': return <AlertCircle size={16} color="var(--danger)" />;
      case 'WARNING': return <AlertCircle size={16} color="#F59E0B" />;
      case 'INFO': return <Info size={16} color="var(--accent)" />;
      default: return <CheckCircle size={16} color="var(--success)" />;
    }
  };

  const getLogColor = (level) => {
    switch(level) {
      case 'ERROR': return 'var(--danger)';
      case 'WARNING': return '#F59E0B';
      default: return 'var(--text-primary)';
    }
  };

  return (
    <div>
      <div style={styles.header}>
        <h1>System Logs</h1>
        <p>Real-time monitoring of backend operations</p>
      </div>

      <div className="glass glass-card" style={styles.terminalContainer}>
        <div style={styles.terminalHeader}>
          <div style={styles.windowControls}>
            <div style={{...styles.dot, backgroundColor: '#EF4444'}}></div>
            <div style={{...styles.dot, backgroundColor: '#F59E0B'}}></div>
            <div style={{...styles.dot, backgroundColor: '#10B981'}}></div>
          </div>
          <div style={{display: 'flex', alignItems: 'center', gap: '8px', color: '#94A3B8'}}>
            <Terminal size={16} /> adminbackend/app.log
          </div>
        </div>

        <div style={styles.terminalBody}>
          {loading ? (
            <div style={{color: '#94A3B8'}}>Waiting for log stream...</div>
          ) : (
            logs.map((log, idx) => (
              <div key={idx} style={styles.logRow}>
                <span style={styles.logTime}>[{log.timestamp}]</span>
                <span style={styles.logIcon}>{getLogIcon(log.level)}</span>
                <span style={{...styles.logLevel, color: getLogColor(log.level)}}>
                  {log.level}
                </span>
                <span style={{color: getLogColor(log.level)}}>{log.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

const styles = {
  header: {
    marginBottom: '2rem'
  },
  terminalContainer: {
    padding: 0,
    overflow: 'hidden',
    backgroundColor: '#0F172A',
    borderColor: '#334155'
  },
  terminalHeader: {
    backgroundColor: '#1E293B',
    padding: '0.75rem 1rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottom: '1px solid #334155'
  },
  windowControls: {
    display: 'flex',
    gap: '6px'
  },
  dot: {
    width: '12px',
    height: '12px',
    borderRadius: '50%'
  },
  terminalBody: {
    padding: '1.5rem',
    fontFamily: '"Fira Code", monospace',
    fontSize: '0.85rem',
    height: '60vh',
    overflowY: 'auto'
  },
  logRow: {
    display: 'flex',
    alignItems: 'flex-start',
    marginBottom: '0.5rem',
    gap: '0.75rem',
    lineHeight: 1.5
  },
  logTime: {
    color: '#64748B',
    whiteSpace: 'nowrap'
  },
  logIcon: {
    marginTop: '2px'
  },
  logLevel: {
    fontWeight: '600',
    width: '70px',
    flexShrink: 0
  }
};

export default SystemLogs;
