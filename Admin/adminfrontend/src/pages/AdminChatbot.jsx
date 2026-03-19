import React, { useState, useRef, useEffect, useContext, useCallback, useMemo } from 'react';
import axios from 'axios';
import { Send, Bot, User, Cpu, Paperclip, X, Zap, History, Plus, Trash2, Search, Tag, Copy, Check, ArrowLeft } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { AuthContext } from '../AuthContext';

const QUICK_CHIPS = [
  { label: '📊 System Summary',      msg: 'Give me a full system summary with all stats' },
  { label: '👥 List All Users',       msg: 'List all registered users with their status' },
  { label: '💼 Pending Jobs',         msg: 'Show all pending jobs that need approval' },
  { label: '✅ Recent Completions',   msg: 'Show recently completed jobs' },
  { label: '📉 Inactive Users',       msg: 'List all inactive/deactivated users' },
  { label: '📈 Today\'s Activity',    msg: 'Summarize today\'s user activity' },
];

const WELCOME = `## 👋 Welcome to Genesis Admin Intelligence

I'm your official system co-pilot. I have **live access** to the Genesis IT Lab database and can help you manage the platform efficiently.

**What I can do:**
- 📊 **Query System Stats:** Ask about users, jobs, or chat sessions.
- 👥 **User Management:** Deactivate, activate, or delete users via chat.
- 💼 **Job Control:** Monitor and update job statuses (accept/reject).
- 📎 **Contextual Analysis:** Upload PDFs or text files for instant summaries.

*Note: If Ollama is offline, I'll switch to **Lite Mode** to ensure you still have access to key system data.*

**Try a quick command below to get started!**`;

const generateSessionId = () => `admin_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 9)}`;
const toRefId = (sid) => {
  const clean = (sid || '').replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
  return 'REF-' + clean.slice(-8).padStart(8, '0');
};

const AdminChatbot = () => {
  const { admin } = useContext(AuthContext);
  const token = admin?.token;
  const [messages, setMessages] = useState([{ role: 'assistant', content: WELCOME }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [stagedFiles, setStagedFiles] = useState([]);
  const [fileContext, setFileContext] = useState('');
  const [uploading, setUploading] = useState(false);
  
  // History & Session State
  const [sessionId, setSessionId] = useState(() => {
    return localStorage.getItem('genesis_admin_session_id') || generateSessionId();
  });
  const [sessions, setSessions] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [historySearch, setHistorySearch] = useState('');
  const [copySuccess, setCopySuccess] = useState(false);

  const scrollRef = useRef(null);
  const fileInputRef = useRef(null);

  // Calculate headers for fetch/axios
  const headers = useMemo(() => token ? { Authorization: `Bearer ${token}` } : {}, [token]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const appendMsg = (role, content) =>
    setMessages(prev => [...prev, { role, content }]);

  const fetchSessions = useCallback(async () => {
    try {
      const res = await axios.get('/api/admin-bot/sessions', { headers });
      if (res.data.success) setSessions(res.data.sessions);
    } catch (err) {
      console.error("Failed to fetch sessions", err);
    }
  }, [headers]);

  const loadSession = useCallback(async (sid) => {
    if (!sid) return;
    setSessionId(sid);
    localStorage.setItem('genesis_admin_session_id', sid);
    setShowHistory(false);
    setIsLoading(true);
    setMessages([]); // Clear while loading for a cleaner look
    try {
      const res = await axios.get(`/api/admin-bot/history?session_id=${sid}`, { headers });
      if (res.data.success) {
        setMessages(res.data.history.length > 0 ? res.data.history : [{ role: 'assistant', content: WELCOME }]);
      }
    } catch (err) {
      appendMsg('assistant', "❌ Failed to load history.");
    } finally {
      setIsLoading(false);
    }
  }, [headers]);

  const startNewChat = () => {
    const newId = generateSessionId();
    setSessionId(newId);
    localStorage.setItem('genesis_admin_session_id', newId);
    setMessages([{ role: 'assistant', content: WELCOME }]);
    setFileContext('');
    setStagedFiles([]);
    setShowHistory(false);
  };

  const deleteSession = async (sid, e) => {
    e.stopPropagation();
    if (!window.confirm("Delete this conversation?")) return;
    try {
      await axios.delete(`/api/admin-bot/sessions/${sid}`, { headers });
      setSessions(prev => prev.filter(s => s.session_id !== sid));
      if (sessionId === sid) {
        localStorage.removeItem('genesis_admin_session_id');
        startNewChat();
      }
    } catch (err) {
      alert("Failed to delete.");
    }
  };

  const copyRefId = () => {
    navigator.clipboard.writeText(toRefId(sessionId));
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  useEffect(() => {
    fetchSessions();
    // On mount, if we have a session ID that isn't brand new (or even if it is), 
    // try to load its history to see if it exists in DB.
    const storedId = localStorage.getItem('genesis_admin_session_id');
    if (storedId) {
      loadSession(storedId);
    }
  }, [fetchSessions, loadSession]);

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    setUploading(true);
    const newCtxParts = [];
    const newNames = [];
    for (const file of files) {
      try {
        const fd = new FormData();
        fd.append('file', file);
        const res = await axios.post('/api/admin-bot/upload', fd, {
          headers: { ...headers, 'Content-Type': 'multipart/form-data' }
        });
        if (res.data.success) {
          newCtxParts.push(`[File: ${res.data.filename}]\n${res.data.text}`);
          newNames.push(res.data.filename);
        }
      } catch {
        appendMsg('assistant', `⚠️ Could not read "${file.name}".`);
      }
    }
    if (newCtxParts.length) {
      setFileContext(prev => prev + '\n\n' + newCtxParts.join('\n\n'));
      setStagedFiles(prev => [...prev, ...newNames]);
      // Removed the auto-assistant message to keep chat clean until "Send"
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeFile = (name) => {
    setStagedFiles(prev => prev.filter(f => f !== name));
    // Also remove that file's context block
    setFileContext(prev =>
      prev.split('\n\n').filter(block => !block.startsWith(`[File: ${name}]`)).join('\n\n')
    );
  };

  const handleSend = async (msgOverride) => {
    const userMsg = (msgOverride || input).trim();
    const hasFiles = stagedFiles.length > 0;
    
    if ((!userMsg && !hasFiles) || isLoading) return;

    const currentFiles = [...stagedFiles];
    setInput('');
    setStagedFiles([]);

    // Add message with attachments to UI
    setMessages(prev => [...prev, { 
      role: 'user', 
      content: userMsg, 
      attachments: currentFiles 
    }]);

    setIsLoading(true);
    try {
      const response = await fetch('/api/admin-bot/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': headers.Authorization,
        },
        body: JSON.stringify({
          message: userMsg || (currentFiles.length > 0 ? "Please analyze the attached files." : ""),
          file_context: fileContext,
          session_id: sessionId,
          attachments: currentFiles,
        }),
      });

      if (!response.ok) throw new Error('Server error');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let streamText = "";

      // Add a placeholder message for the assistant
      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        const chunk = decoder.decode(value, { stream: !done });
        streamText += chunk;

        // Update the last message in real-time
        setMessages(prev => {
          const newMsgs = [...prev];
          if (newMsgs.length > 0) {
            newMsgs[newMsgs.length - 1].content = streamText;
          }
          return newMsgs;
        });
      }
      
      fetchSessions(); // Sync history titles/previews
    } catch (err) {
      console.error("Stream error:", err);
      appendMsg('assistant', '❌ Connection failed or timed out. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <div style={{ 
      height: 'calc(100vh - 4rem)', display: 'flex', flexDirection: 'column',
      background: 'radial-gradient(circle at top right, rgba(59,130,246,0.05), transparent), radial-gradient(circle at bottom left, rgba(139,92,246,0.03), transparent)'
    }}>
      {/* Header */}
      <div style={{ padding: '0 0.5rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{
          width: 52, height: 52, borderRadius: 18,
          background: 'linear-gradient(135deg, rgba(59,130,246,0.2), rgba(37,99,235,0.1))', 
          border: '1px solid rgba(59,130,246,0.3)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 8px 16px -4px rgba(59,130,246,0.2)'
        }}>
          <Cpu size={26} color="var(--accent)" />
        </div>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.025em' }}>Genesis Admin Intelligence</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Advanced System Co-pilot & Assistant</p>
            <span 
              onClick={copyRefId}
              style={{ 
                fontSize: '10px', padding: '3px 10px', background: 'rgba(59,130,246,0.12)', 
                border: '1px solid rgba(59,130,246,0.25)', borderRadius: '14px', 
                color: 'var(--accent)', fontWeight: 700, cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: '4px',
                transition: 'all 0.2s', boxShadow: copySuccess ? '0 0 10px rgba(59,130,246,0.3)' : 'none'
              }}
            >
              <Tag size={10} />
              {toRefId(sessionId)}
              {copySuccess && <span style={{ marginLeft: '4px', color: '#10B981' }}>COPIED!</span>}
            </span>
          </div>
        </div>
        
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '10px' }}>
          <button onClick={() => setShowHistory(!showHistory)} 
            style={{ 
              width: 44, height: 44, borderRadius: '12px', border: '1px solid var(--glass-border)', 
              background: showHistory ? 'var(--accent)' : 'rgba(255,255,255,0.03)', 
              color: showHistory ? '#fff' : 'var(--text-primary)', 
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'all 0.2s'
            }}>
            <History size={20} />
          </button>
          <button onClick={startNewChat} 
            style={{ 
              width: 44, height: 44, borderRadius: '12px', border: '1px solid var(--glass-border)', 
              background: 'rgba(255,255,255,0.03)', color: 'var(--text-primary)', 
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'all 0.2s'
            }}>
            <Plus size={20} />
          </button>
        </div>
      </div>

      {/* Main Container */}
      <div style={{ flex: 1, display: 'flex', gap: '1.5rem', overflow: 'hidden', position: 'relative' }}>
        
        {/* Chat Window */}
        <div className="glass" style={{ 
          flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', 
          borderRadius: '24px', border: '1px solid var(--glass-border)',
          background: 'rgba(15, 23, 42, 0.4)', backdropFilter: 'blur(20px)',
          boxShadow: '0 20px 50px -12px rgba(0,0,0,0.5)'
        }}>
          {/* Messages */}
          <div ref={scrollRef} style={{ 
            flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', 
            gap: '1.5rem', padding: '2rem', scrollBehavior: 'smooth' 
          }}>
            {messages.length === 1 && messages[0].content === WELCOME ? (
              <div style={{ 
                flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', 
                justifyContent: 'center', textAlign: 'center', padding: '2rem' 
              }}>
                <div style={{ 
                  width: 80, height: 80, borderRadius: '24px', background: 'rgba(59,130,246,0.1)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.5rem',
                  border: '1px solid rgba(59,130,246,0.2)'
                }}>
                  <Zap size={40} color="var(--accent)" />
                </div>
                <h2 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.5rem', background: 'linear-gradient(to bottom right, #fff, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                  How can I help you today?
                </h2>
                <p style={{ color: 'var(--text-secondary)', maxWidth: '450px', lineHeight: 1.6, marginBottom: '2.5rem' }}>
                  Analyze PDFs, manage users, or query system statistics in real-time with Genesis Intelligence.
                </p>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px', width: '100%', maxWidth: '600px' }}>
                  {QUICK_CHIPS.slice(0, 4).map(chip => (
                    <button key={chip.label} onClick={() => handleSend(chip.msg)}
                      style={{
                        padding: '16px', borderRadius: '16px', fontSize: '14px', fontWeight: 600,
                        background: 'rgba(255,255,255,0.03)', border: '1px solid var(--glass-border)',
                        color: 'var(--text-primary)', cursor: 'pointer', textAlign: 'left',
                        transition: 'all 0.2s', display: 'flex', alignItems: 'center', justifyContent: 'space-between'
                      }}
                      onMouseEnter={e => { e.currentTarget.style.background = 'rgba(59,130,246,0.1)'; e.currentTarget.style.borderColor = 'rgba(59,130,246,0.3)'; }}
                      onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.03)'; e.currentTarget.style.borderColor = 'var(--glass-border)'; }}
                    >
                      {chip.label} <Zap size={14} style={{ opacity: 0.5 }} />
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div key={idx} style={{ 
                  display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  animation: 'fadeInUp 0.4s ease-out forwards'
                }}>
                  <div style={{
                    maxWidth: '85%', display: 'flex', gap: '1rem', alignItems: 'flex-start',
                    flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                  }}>
                    <div style={{
                      width: 36, height: 36, borderRadius: '12px', flexShrink: 0,
                      background: msg.role === 'user' ? 'var(--accent)' : 'rgba(59,130,246,0.15)',
                      color: msg.role === 'user' ? '#fff' : 'var(--accent)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      boxShadow: msg.role === 'user' ? '0 4px 12px rgba(59,130,246,0.3)' : 'none',
                      marginTop: '4px'
                    }}>
                      {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                    </div>
                    <div style={{
                      padding: '1rem 1.25rem', borderRadius: msg.role === 'user' ? '20px 4px 20px 20px' : '4px 20px 20px 20px',
                      background: msg.role === 'user' ? 'linear-gradient(135deg, var(--accent), #2563eb)' : 'rgba(30, 41, 59, 0.7)',
                      border: msg.role === 'user' ? 'none' : '1px solid var(--glass-border)',
                      color: '#fff', lineHeight: 1.6, fontSize: '0.95rem',
                      boxShadow: '0 4px 15px rgba(0,0,0,0.1)'
                    }}>
                      {msg.attachments && msg.attachments.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: msg.content ? '12px' : 0 }}>
                          {msg.attachments.map(name => (
                            <div key={name} style={{
                              display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 14px',
                              background: 'rgba(255,255,255,0.1)', borderRadius: '10px', fontSize: '0.85rem',
                              border: '1px solid rgba(255,255,255,0.15)', color: '#fff', backdropFilter: 'blur(5px)'
                            }}>
                              <Paperclip size={14} /> <span>{name}</span>
                            </div>
                          ))}
                        </div>
                      )}
                      <div className="markdown-content">
                        {msg.role === 'assistant' ? <ReactMarkdown>{msg.content}</ReactMarkdown> : msg.content}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start', animation: 'fadeIn 0.3s ease-in' }}>
                <div style={{ width: 36, height: 36, borderRadius: '12px', background: 'rgba(59,130,246,0.15)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Bot size={18} />
                </div>
                <div style={{ padding: '1rem 1.25rem', borderRadius: '4px 20px 20px 20px', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid var(--glass-border)' }}>
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                    {[0,1,2].map(i => (
                      <div key={i} style={{
                        width: 8, height: 8, borderRadius: '50%', background: 'var(--accent)',
                        animation: `pulse 1.5s ${i * 0.2}s infinite ease-in-out`,
                        boxShadow: '0 0 10px var(--accent)'
                      }} />
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Staged files */}
          {stagedFiles.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', padding: '0 2rem 1rem' }}>
              {stagedFiles.map(name => (
                <div key={name} style={{
                  display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: 600,
                  background: 'rgba(59,130,246,0.15)', border: '1px solid rgba(59,130,246,0.3)',
                  color: 'var(--accent)', padding: '6px 14px', borderRadius: '12px',
                  animation: 'scaleIn 0.2s ease-out'
                }}>
                  <Paperclip size={13} /> <span>{name}</span>
                  <button onClick={() => removeFile(name)} style={{ background: 'none', border: 'none', color: 'rgba(239,68,68,0.7)', cursor: 'pointer', padding: 0, marginLeft: '4px' }}>
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Input area */}
          <div style={{ padding: '1.5rem 2rem 2rem', background: 'rgba(15,23,42,0.6)', borderTop: '1px solid var(--glass-border)' }}>
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', background: 'rgba(255,255,255,0.03)', padding: '6px', borderRadius: '18px', border: '1px solid var(--glass-border)' }}>
              <input ref={fileInputRef} type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.txt,.csv" style={{ display: 'none' }} onChange={handleFileSelect} />
              <button
                type="button" onClick={() => fileInputRef.current?.click()} disabled={uploading}
                style={{
                  width: 44, height: 44, borderRadius: '14px', border: 'none',
                  background: uploading ? 'rgba(255,255,255,0.05)' : 'rgba(59,130,246,0.1)', 
                  color: uploading ? 'var(--text-secondary)' : 'var(--accent)',
                  cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                  transition: 'all 0.2s'
                }}>
                {uploading ? <Zap size={20} className="spin" /> : <Paperclip size={20} />}
              </button>
              <textarea
                style={{ 
                  flex: 1, background: 'none', border: 'none', outline: 'none', 
                  color: '#fff', fontSize: '1rem', padding: '12px 8px', resize: 'none',
                  height: '44px', maxHeight: '120px', fontFamily: 'inherit'
                }}
                value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
                placeholder={stagedFiles.length > 0 ? `Ask about ${stagedFiles.join(', ')}…` : 'Ask anything about the system…'}
                disabled={isLoading} rows={1}
              />
              <button
                type="button" onClick={() => handleSend()} disabled={isLoading || (!input.trim() && stagedFiles.length === 0)}
                style={{ 
                  width: 44, height: 44, borderRadius: '14px', border: 'none',
                  background: (isLoading || (!input.trim() && stagedFiles.length === 0)) ? 'rgba(255,255,255,0.05)' : 'var(--accent)',
                  color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', 
                  flexShrink: 0, transition: 'all 0.2s', boxShadow: '0 4px 12px rgba(59,130,246,0.2)'
                }}>
                <Send size={20} />
              </button>
            </div>
          </div>
        </div>

        {/* History Sidebar */}
        <div style={{ 
          width: showHistory ? '350px' : '0', 
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)', 
          overflow: 'hidden', display: 'flex', flexDirection: 'column',
          background: 'rgba(15, 23, 42, 0.4)', borderRadius: '24px',
          border: showHistory ? '1px solid var(--glass-border)' : 'none',
          backdropFilter: 'blur(20px)', opacity: showHistory ? 1 : 0
        }}>
          <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--glass-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '10px' }}>
              <History size={18} color="var(--accent)" /> Chat History
            </h3>
          </div>
          
          <div style={{ padding: '1.25rem' }}>
            <div style={{ position: 'relative' }}>
              <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)', opacity: 0.6 }} />
              <input 
                className="input" 
                style={{ 
                  paddingLeft: '38px', fontSize: '14px', borderRadius: '14px',
                  background: 'rgba(255,255,255,0.03)', border: '1px solid var(--glass-border)'
                }} 
                placeholder="Search sessions..." 
                value={historySearch}
                onChange={e => setHistorySearch(e.target.value)}
              />
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '0 1rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {sessions.filter(s => 
              s.title.toLowerCase().includes(historySearch.toLowerCase()) || 
              toRefId(s.session_id).toLowerCase().includes(historySearch.toLowerCase())
            ).map(s => (
              <div 
                key={s.session_id} 
                onClick={() => loadSession(s.session_id)}
                className={`history-item ${sessionId === s.session_id ? 'active' : ''}`}
                style={{ 
                  padding: '14px', borderRadius: '16px', cursor: 'pointer',
                  background: sessionId === s.session_id ? 'rgba(59,130,246,0.15)' : 'rgba(255,255,255,0.02)',
                  border: sessionId === s.session_id ? '1px solid var(--accent)' : '1px solid rgba(255,255,255,0.05)',
                  transition: 'all 0.2s', position: 'relative'
                }}
              >
                <div style={{ fontSize: '13.5px', fontWeight: 600, color: sessionId === s.session_id ? 'var(--accent)' : '#fff', marginBottom: '4px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {s.title}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', opacity: 0.7, marginBottom: '8px', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 1, WebkitBoxOrient: 'vertical' }}>
                  {s.preview || "No messages yet"}
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', opacity: 0.5 }}>
                  <span style={{ fontWeight: 700 }}>{toRefId(s.session_id)}</span>
                  <span>{new Date(s.last_message_at).toLocaleDateString()}</span>
                </div>
                <button 
                  onClick={(e) => deleteSession(s.session_id, e)}
                  style={{ position: 'absolute', top: '12px', right: '12px', background: 'none', border: 'none', color: 'rgba(239,68,68,0.5)', cursor: 'pointer', opacity: 0 }}
                  className="delete-btn"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 0.3; transform: scale(0.8); } 50% { opacity: 1; transform: scale(1); } }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes fadeInUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes scaleIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
        
        .history-item:hover { background: rgba(255,255,255,0.06) !important; transform: translateY(-2px); }
        .history-item:hover .delete-btn { opacity: 1 !important; }
        
        .markdown-content p { margin: 0 0 0.75rem 0; }
        .markdown-content p:last-child { margin-bottom: 0; }
        .markdown-content ul, .markdown-content ol { margin-top: 0.5rem; padding-left: 1.25rem; }
        .markdown-content li { margin-bottom: 0.25rem; }
        
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.2); borderRadius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(148, 163, 184, 0.4); }
      `}</style>
    </div>
  );
};

export default AdminChatbot;
