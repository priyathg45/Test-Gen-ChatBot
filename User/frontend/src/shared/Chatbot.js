import React, { useState, useRef, useEffect, useCallback } from 'react';
import './Chatbot.css';
import { CHAT_API_URL } from '../config';
import { useAuth } from '../context/AuthContext';
import ReactMarkdown from 'react-markdown';
import JobFormCard from './JobFormCard';

const generateSessionId = () =>
  `chat_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;

/** Derive a short human-readable REF ID from a session_id */
const toRefId = (sessionId) => {
  const clean = (sessionId || '').replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
  return 'REF-' + clean.slice(-8).padStart(8, '0');
};

/** Detect job-creation intent in user text */
const isJobIntent = (text) => {
  const t = (text || '').toLowerCase();
  return (
    /\b(place|create|make|add|open|generate|new)\s+(a\s+)?(job|work order|order)\b/.test(t) ||
    /\bjob\s+(form|request|creation|order)\b/.test(t) ||
    t === 'job' || t === 'create job'
  );
};

const ACCEPT_FILES = '.pdf,.png,.jpg,.jpeg,.gif,.webp';
const MAX_FILE_SIZE_MB = 10;
const WELCOME_TEXT =
  "Hi, I'm the AAW assistant. Ask me about aluminium products, production, or this portal.\n\n" +
  "**You can also:**\n" +
  "- 📎 Attach one or more PDFs/images — I'll read their content\n" +
  "- 💼 Say **\"create a job\"** and I'll show a job form you can auto-fill from your PDFs";

const Chatbot = () => {
  const { token } = useAuth();
  const [open, setOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState([{ id: 1, from: 'bot', text: WELCOME_TEXT }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  // Multi-file staging — array of File objects
  const [stagedFiles, setStagedFiles] = useState([]);
  const [showRefPopup, setShowRefPopup] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const [historySearch, setHistorySearch] = useState('');

  const sessionIdRef = useRef(generateSessionId());
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const refPopupRef = useRef(null);

  const currentRefId = toRefId(sessionIdRef.current);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

  const appendMessage = useCallback((text, from, extra = {}) => {
    if (!text && !extra.type) return;
    setMessages((prev) => [...prev, { id: Date.now() + Math.random(), from, text, ...extra }]);
  }, []);

  const fetchSessionData = useCallback(async () => {
    try {
      let currentSessionId = sessionIdRef.current;
      if (token) {
        const sessRes = await fetch(`${CHAT_API_URL}/sessions`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const sessData = await sessRes.json();
        if (sessData.success && sessData.sessions) {
          setSessions(sessData.sessions);
          if (sessData.sessions.length > 0) {
            currentSessionId = sessData.sessions[0].session_id;
            sessionIdRef.current = currentSessionId;
            const histRes = await fetch(
              `${CHAT_API_URL}/history?session_id=${encodeURIComponent(currentSessionId)}`,
              { headers: { Authorization: `Bearer ${token}` } }
            );
            const histData = await histRes.json();
            if (histData.success && histData.history && histData.history.length > 0) {
              setMessages(histData.history.map((m, i) => ({
                id: Date.now() + i,
                from: m.role === 'assistant' ? 'bot' : 'user',
                text: m.content,
              })));
            }
          }
        }
      }
    } catch (_) { /* ignore */ }
  }, [token]);

  const loadSession = async (sid) => {
    sessionIdRef.current = sid;
    setShowHistory(false);
    setLoading(true);
    setMessages([{ id: 1, from: 'bot', text: 'Loading...' }]);
    setStagedFiles([]);
    try {
      const histRes = await fetch(
        `${CHAT_API_URL}/history?session_id=${encodeURIComponent(sid)}`,
        { headers: token ? { Authorization: `Bearer ${token}` } : {} }
      );
      const histData = await histRes.json();
      if (histData.success && histData.history) {
        setMessages(histData.history.map((m, i) => ({
          id: Date.now() + i,
          from: m.role === 'assistant' ? 'bot' : 'user',
          text: m.content,
        })));
      } else {
        setMessages([]);
      }
    } catch (_) {
    } finally {
      setLoading(false);
      setTimeout(scrollToBottom, 100);
    }
  };

  const startNewChat = () => {
    sessionIdRef.current = generateSessionId();
    setMessages([{ id: 1, from: 'bot', text: WELCOME_TEXT }]);
    setStagedFiles([]);
    setShowHistory(false);
    setShowRefPopup(false);
  };

  const deleteSession = async (sid, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this conversation?')) return;
    try {
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res = await fetch(`${CHAT_API_URL}/sessions/${encodeURIComponent(sid)}`, {
        method: 'DELETE', headers,
      });
      const data = await res.json();
      if (data.success) {
        setSessions(prev => prev.filter(s => s.session_id !== sid));
        if (sessionIdRef.current === sid) startNewChat();
      }
    } catch (_) {
      alert('Could not delete conversation. Please try again.');
    }
  };

  const copyRefId = async () => {
    try {
      await navigator.clipboard.writeText(currentRefId);
    } catch (_) {
      const el = document.createElement('textarea');
      el.value = currentRefId;
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
    }
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  // Close ref popup when clicking outside
  useEffect(() => {
    const handler = (e) => {
      if (refPopupRef.current && !refPopupRef.current.contains(e.target)) setShowRefPopup(false);
    };
    if (showRefPopup) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showRefPopup]);

  useEffect(() => {
    if (open) fetchSessionData();
  }, [open, token, fetchSessionData]);

  // ── Multi-file staging ──────────────────────────────────────────────────
  const onFileChange = (e) => {
    const files = Array.from(e.target.files || []);
    const valid = [];
    for (const file of files) {
      const sizeMB = file.size / (1024 * 1024);
      if (sizeMB > MAX_FILE_SIZE_MB) {
        appendMessage(`"${file.name}" is too large (${sizeMB.toFixed(1)} MB). Max ${MAX_FILE_SIZE_MB} MB.`, 'bot');
      } else {
        valid.push(file);
      }
    }
    if (valid.length > 0) setStagedFiles(prev => [...prev, ...valid]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeStagedFile = (idx) => setStagedFiles(prev => prev.filter((_, i) => i !== idx));

  // ── Send ────────────────────────────────────────────────────────────────
  const sendMessage = async () => {
    const trimmed = input.trim();
    if ((!trimmed && stagedFiles.length === 0) || loading || uploading) return;

    // Detect job intent BEFORE sending — show inline job form
    if (isJobIntent(trimmed) && stagedFiles.length === 0) {
      appendMessage(trimmed, 'user');
      setInput('');
      appendMessage('', 'bot', { type: 'job_form', sessionId: sessionIdRef.current });
      return;
    }

    let uploadedNames = [];

    // Upload all staged files using /upload-multiple
    if (stagedFiles.length > 0) {
      setUploading(true);
      const formData = new FormData();
      stagedFiles.forEach(f => formData.append('files', f));
      formData.append('session_id', sessionIdRef.current);
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;
      try {
        const res = await fetch(`${CHAT_API_URL}/upload-multiple`, {
          method: 'POST', headers, body: formData,
        });
        const data = await res.json();
        if (data.uploaded && data.uploaded.length > 0) {
          uploadedNames = data.uploaded.map(u => u.filename);
        }
        if (data.errors && data.errors.length > 0) {
          appendMessage(`⚠️ Some files failed: ${data.errors.join(', ')}`, 'bot');
        }
      } catch {
        appendMessage('Upload failed. Please try again.', 'bot');
        setUploading(false);
        return;
      } finally {
        setStagedFiles([]);
        setUploading(false);
      }
    }

    const attachLabel = uploadedNames.length > 0
      ? `[Attached: ${uploadedNames.join(', ')}]`
      : '';
    const actualMessage = [attachLabel, trimmed].filter(Boolean).join('\n');
    const displayMessage = uploadedNames.length > 0
      ? `📎 ${uploadedNames.join(', ')}${trimmed ? '\n' + trimmed : ''}`
      : trimmed;

    appendMessage(displayMessage, 'user');
    setInput('');
    setLoading(true);

    try {
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res = await fetch(`${CHAT_API_URL}/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ message: actualMessage, session_id: sessionIdRef.current }),
      });

      let data = {};
      try { data = await res.json(); } catch (_) { data = {}; }

      if (!res.ok) {
        appendMessage(data.error || 'Something went wrong. Please try again.', 'bot');
        return;
      }

      // Check if the bot reply itself triggers a job form
      if (data.action === 'show_job_form') {
        appendMessage(data.message || '', 'bot');
        appendMessage('', 'bot', { type: 'job_form', sessionId: sessionIdRef.current });
      } else if (data.success !== false && data.message) {
        appendMessage(data.message, 'bot');
      } else {
        appendMessage(data.error || 'Could not get a response. Please try again.', 'bot');
      }
    } catch (err) {
      const msg =
        err.message === 'Failed to fetch'
          ? 'Cannot reach the chat server. Make sure the backend is running at ' + CHAT_API_URL
          : err.message || 'Network error. Please try again.';
      appendMessage(msg, 'bot');
    } finally {
      setLoading(false);
      setTimeout(scrollToBottom, 100);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') { e.preventDefault(); sendMessage(); }
  };

  const filteredSessions = sessions.filter(s => {
    if (!historySearch.trim()) return true;
    const q = historySearch.trim().toLowerCase();
    const title = (s.title || 'Conversation').toLowerCase();
    const ref = toRefId(s.session_id).toLowerCase();
    return title.includes(q) || ref.includes(q) || (s.session_id || '').toLowerCase().includes(q);
  });

  // ── Render ──────────────────────────────────────────────────────────────
  const renderMessage = (m) => {
    if (m.from === 'bot') {
      return (
        <div key={m.id} className="chatbot-message bot">
          <div className="bot-avatar"><i className="fa fa-robot" /></div>
          <div className="bot-bubble">
            {m.type === 'job_form'
              ? <JobFormCard sessionId={m.sessionId || sessionIdRef.current} />
              : <ReactMarkdown>{m.text}</ReactMarkdown>
            }
          </div>
        </div>
      );
    }
    return (
      <div key={m.id} className="chatbot-message user">
        {m.text}
      </div>
    );
  };

  return (
    <>
      <div className={`chatbot-window ${open ? 'open' : ''} ${isExpanded ? 'expanded' : ''}`}>
        {/* Header */}
        <div className="chatbot-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              type="button"
              onClick={() => {
                if (showHistory) setShowHistory(false);
                else { setShowHistory(true); fetchSessionData(); }
              }}
              aria-label="Toggle History"
              title="Chat History"
            >
              <i className={`fa ${showHistory ? 'fa-arrow-left' : 'fa-list'}`} style={{ fontSize: '14px' }} />
            </button>
            <h4>AAW Assistant</h4>
          </div>
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            {/* REF.ID Button */}
            <div className="ref-id-wrapper" ref={refPopupRef}>
              <button
                type="button"
                className="ref-id-btn"
                onClick={() => setShowRefPopup(p => !p)}
                title="View Reference ID"
              >
                <i className="fa fa-tag" style={{ fontSize: '11px', marginRight: '3px' }} />
                REF.ID
              </button>
              {showRefPopup && (
                <div className="ref-id-popup">
                  <div className="ref-id-popup-label">Chat Reference ID</div>
                  <div className="ref-id-popup-value">{currentRefId}</div>
                  <button className="ref-id-copy-btn" onClick={copyRefId} type="button">
                    {copySuccess ? <><i className="fa fa-check" /> Copied!</> : <><i className="fa fa-copy" /> Copy</>}
                  </button>
                  <div className="ref-id-hint">Use this ID to find this conversation in history.</div>
                </div>
              )}
            </div>
            <button type="button" onClick={startNewChat} aria-label="New chat" title="New Chat">
              <i className="fa fa-plus" style={{ fontSize: '14px' }} />
            </button>
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              aria-label={isExpanded ? 'Compress' : 'Expand'}
              title={isExpanded ? 'Compress' : 'Expand'}
            >
              <i className={`fa fa-${isExpanded ? 'compress' : 'expand'}`} style={{ fontSize: '14px' }} />
            </button>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close chat">&times;</button>
          </div>
        </div>

        {showHistory ? (
          <div className="chatbot-history-view">
            <div className="history-search-wrap">
              <i className="fa fa-search history-search-icon" />
              <input
                className="history-search"
                type="text"
                placeholder="Search by title or REF.ID…"
                value={historySearch}
                onChange={e => setHistorySearch(e.target.value)}
              />
              {historySearch && (
                <button className="history-search-clear" onClick={() => setHistorySearch('')}>&times;</button>
              )}
            </div>
            {filteredSessions.map(s => (
              <div key={s.session_id} className="history-item" onClick={() => loadSession(s.session_id)}>
                <div className="history-item-main">
                  <div className="history-title">{s.title || 'Conversation'}</div>
                  <div className="history-ref">{toRefId(s.session_id)}</div>
                  <div className="history-date">
                    {new Date(s.last_message_at || s.started_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                  </div>
                </div>
                <button
                  className="history-delete-btn"
                  onClick={(e) => deleteSession(s.session_id, e)}
                  title="Delete"
                >
                  <i className="fa fa-trash" />
                </button>
              </div>
            ))}
            {filteredSessions.length === 0 && (
              <div className="history-empty">
                {historySearch ? `No results for "${historySearch}".` : 'No previous chats found.'}
              </div>
            )}
          </div>
        ) : (
          <>
            {/* Messages */}
            <div className="chatbot-messages">
              {messages.map(renderMessage)}
              {loading && (
                <div className="chatbot-message bot chatbot-typing">
                  <div className="bot-avatar"><i className="fa fa-robot" /></div>
                  <div className="bot-bubble">
                    <div className="typing-dot" /><div className="typing-dot" /><div className="typing-dot" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Staged files chips */}
            {stagedFiles.length > 0 && (
              <div className="staged-files-area">
                {stagedFiles.map((f, i) => (
                  <div key={i} className="staged-file-chip">
                    <i className="fa fa-file-pdf-o" />
                    <span className="staged-chip-name">{f.name}</span>
                    <span className="staged-chip-size">({(f.size / 1024 / 1024).toFixed(1)} MB)</span>
                    <button
                      className="staged-chip-remove"
                      onClick={() => removeStagedFile(i)}
                      title="Remove"
                    >&times;</button>
                  </div>
                ))}
              </div>
            )}

            {/* Input area */}
            <div className="chatbot-input">
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPT_FILES}
                multiple
                onChange={onFileChange}
                style={{ display: 'none' }}
                disabled={uploading}
              />
              <button
                type="button"
                className="chatbot-btn-attach"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                title="Attach PDF or image (multiple allowed, max 10 MB each)"
              >
                <i className="fa fa-paperclip" />
              </button>
              <input
                type="text"
                placeholder={stagedFiles.length > 0 ? `${stagedFiles.length} file(s) ready — type a message or send…` : 'Type your message…'}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
              />
              <button type="button" onClick={sendMessage} disabled={loading}>
                {uploading ? 'Wait…' : 'Send'}
              </button>
            </div>
          </>
        )}
      </div>

      <button
        type="button"
        className="chatbot-toggle"
        aria-label="Open chat"
        title="Chat with AAW assistant"
        onClick={() => {
          setOpen(prev => !prev);
          if (open && isExpanded) setIsExpanded(false);
        }}
      >
        <i className="fa fa-comments" />
      </button>
    </>
  );
};

export default Chatbot;
