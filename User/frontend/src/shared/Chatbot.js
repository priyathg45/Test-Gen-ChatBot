import React, { useState, useRef, useEffect } from 'react';
import './Chatbot.css';
import { CHAT_API_URL } from '../config';
import { useAuth } from '../context/AuthContext';
import ReactMarkdown from 'react-markdown';

const generateSessionId = () =>
  `chat_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;

const ACCEPT_FILES = '.pdf,.png,.jpg,.jpeg,.gif,.webp';
const MAX_FILE_SIZE_MB = 10;

const Chatbot = () => {
  const { token } = useAuth();
  const [open, setOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      from: 'bot',
      text: 'Hi, I’m the AAW assistant. Ask me about aluminium products, production, or this portal. You can also attach a PDF or image and I’ll read its content.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [stagedFile, setStagedFile] = useState(null);
  const sessionIdRef = useRef(generateSessionId());
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchSessionData = async () => {
    try {
      let currentSessionId = sessionIdRef.current;
      
      if (token) {
        const sessRes = await fetch(`${CHAT_API_URL}/sessions`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const sessData = await sessRes.json();
        if (sessData.success && sessData.sessions) {
          setSessions(sessData.sessions);
          if (sessData.sessions.length > 0) {
            currentSessionId = sessData.sessions[0].session_id;
            sessionIdRef.current = currentSessionId;
            
            const histRes = await fetch(`${CHAT_API_URL}/history?session_id=${encodeURIComponent(currentSessionId)}`, {
              headers: { Authorization: `Bearer ${token}` }
            });
            const histData = await histRes.json();
            if (histData.success && histData.history && histData.history.length > 0) {
              const loadedMsgs = histData.history.map((m, i) => ({
                id: Date.now() + i,
                from: m.role === 'assistant' ? 'bot' : 'user',
                text: m.content
              }));
              setMessages(loadedMsgs);
            }
          }
        }
      }

      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const attRes = await fetch(
        `${CHAT_API_URL}/sessions/${encodeURIComponent(currentSessionId)}/attachments`,
        { headers }
      );
      const attData = await attRes.json();
      if (attData.success && Array.isArray(attData.attachments)) {
        setAttachments(attData.attachments);
      }
    } catch (_) {
      // ignore
    }
  };

  const loadSession = async (sid) => {
    sessionIdRef.current = sid;
    setShowHistory(false);
    setLoading(true);
    setMessages([{ id: 1, from: 'bot', text: 'Loading...' }]);
    setAttachments([]);
    setStagedFile(null);
    try {
      const histRes = await fetch(`${CHAT_API_URL}/history?session_id=${encodeURIComponent(sid)}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      const histData = await histRes.json();
      if (histData.success && histData.history) {
        setMessages(histData.history.map((m, i) => ({
          id: Date.now() + i,
          from: m.role === 'assistant' ? 'bot' : 'user',
          text: m.content
        })));
      } else {
        setMessages([]);
      }
      
      const attRes = await fetch(
        `${CHAT_API_URL}/sessions/${encodeURIComponent(sid)}/attachments`,
        { headers: token ? { Authorization: `Bearer ${token}` } : {} }
      );
      const attData = await attRes.json();
      if (attData.success && Array.isArray(attData.attachments)) {
        setAttachments(attData.attachments);
      }
    } catch (_) {
    } finally {
      setLoading(false);
      setTimeout(scrollToBottom, 100);
    }
  };

  const startNewChat = () => {
    sessionIdRef.current = generateSessionId();
    setMessages([
      {
        id: 1,
        from: 'bot',
        text: 'Hi, I’m the AAW assistant. Ask me about aluminium products, production, or this portal. You can also attach a PDF or image and I’ll read its content.',
      },
    ]);
    setAttachments([]);
    setStagedFile(null);
    setShowHistory(false);
  };

  useEffect(() => {
    if (open) fetchSessionData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, token]);

  const onFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const sizeMB = file.size / (1024 * 1024);
      if (sizeMB > MAX_FILE_SIZE_MB) {
        appendMessage(`File is too large (${sizeMB.toFixed(1)} MB). Max ${MAX_FILE_SIZE_MB} MB.`, 'bot');
        return;
      }
      setStagedFile(file);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const appendMessage = (text, from) => {
    if (!text) return;
    setMessages((prev) => [
      ...prev,
      { id: Date.now() + Math.random(), from, text },
    ]);
  };

  const sendMessage = async () => {
    let trimmed = input.trim();
    if ((!trimmed && !stagedFile) || loading || uploading) return;

    let attachedFilename = "";

    if (stagedFile) {
      setUploading(true);
      attachedFilename = stagedFile.name;
      const formData = new FormData();
      formData.append('file', stagedFile);
      formData.append('session_id', sessionIdRef.current);

      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      try {
        const res = await fetch(`${CHAT_API_URL}/upload`, {
          method: 'POST',
          headers,
          body: formData,
        });
        const data = await res.json();
        if (data.success && data.attachment) {
          setAttachments((prev) => [...prev, data.attachment]);
        }
      } catch (err) {
        appendMessage('Upload failed.', 'bot');
        setUploading(false);
        setStagedFile(null);
        return;
      }
      setStagedFile(null);
      setUploading(false);
    }

    let actualMessage = trimmed;
    let displayMessage = trimmed;
    if (attachedFilename) {
      const attachText = `[Attached: ${attachedFilename}]`;
      actualMessage = trimmed ? `${attachText}\n${trimmed}` : attachText;
      displayMessage = trimmed ? `📎 ${attachedFilename}\n${trimmed}` : `📎 ${attachedFilename}`;
    }

    appendMessage(displayMessage, 'user');
    setInput('');
    setLoading(true);

    try {
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res = await fetch(`${CHAT_API_URL}/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: actualMessage,
          session_id: sessionIdRef.current,
        }),
      });

      let data = {};
      try {
        data = await res.json();
      } catch (_) {
        data = {};
      }

      if (!res.ok) {
        appendMessage(
          data.error || 'Something went wrong. Please try again.',
          'bot',
        );
        return;
      }

      if (data.success !== false && data.message) {
        appendMessage(data.message, 'bot');
      } else {
        appendMessage(
          data.error || 'Could not get a response. Please try again.',
          'bot',
        );
      }
    } catch (err) {
      const msg =
        err.message === 'Failed to fetch'
          ? 'Cannot reach the chat server. Make sure the backend is running at ' +
            CHAT_API_URL
          : err.message || 'Network error. Please try again.';
      appendMessage(msg, 'bot');
    } finally {
      setLoading(false);
      setTimeout(scrollToBottom, 100);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      <div className={`chatbot-window ${open ? 'open' : ''} ${isExpanded ? 'expanded' : ''}`}>
        <div className="chatbot-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              type="button"
              onClick={() => {
                if (showHistory) setShowHistory(false);
                else {
                  setShowHistory(true);
                  fetchSessionData();
                }
              }}
              aria-label="Toggle History"
              title="Chat History"
            >
              <i className={`fa ${showHistory ? 'fa-arrow-left' : 'fa-list'}`} style={{ fontSize: '14px' }} />
            </button>
            <h4>AAW Assistant</h4>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              onClick={startNewChat}
              aria-label="Start new chat"
              title="New Chat"
            >
              <i className="fa fa-plus" style={{ fontSize: '14px' }} />
            </button>
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              aria-label={isExpanded ? 'Compress chat' : 'Expand chat'}
              title={isExpanded ? 'Compress display' : 'Expand to full screen'}
            >
              <i className={`fa fa-${isExpanded ? 'compress' : 'expand'}`} style={{ fontSize: '14px' }} />
            </button>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close chat">
              &times;
            </button>
          </div>
        </div>
        {showHistory ? (
          <div className="chatbot-history-view">
            {sessions.map(s => (
              <div key={s.session_id} className="history-item" onClick={() => loadSession(s.session_id)}>
                <div className="history-title">{s.title || 'Conversation'}</div>
                <div className="history-date">
                  {new Date(s.last_message_at || s.started_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                </div>
              </div>
            ))}
            {sessions.length === 0 && (
              <div style={{ padding: '20px', textAlign: 'center', color: '#888' }}>
                No previous chats found.
              </div>
            )}
          </div>
        ) : (
          <>
            <div className="chatbot-messages">
              {messages.map((m) => (
                <div key={m.id} className={`chatbot-message ${m.from}`}>
                  {m.from === 'bot' ? <ReactMarkdown>{m.text}</ReactMarkdown> : m.text}
                </div>
              ))}
              {loading && (
                <div className="chatbot-message bot chatbot-typing">
                  Thinking…
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            {stagedFile && (
              <div className="staged-file-area">
                <span>📎 {stagedFile.name} ({(stagedFile.size / 1024 / 1024).toFixed(2)} MB)</span>
                <span className="staged-file-remove" onClick={() => setStagedFile(null)} aria-label="Remove" title="Remove file">
                  &times;
                </span>
              </div>
            )}
            <div className="chatbot-input">
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPT_FILES}
                onChange={onFileChange}
                style={{ display: 'none' }}
                disabled={uploading}
              />
              <button
                type="button"
                className="chatbot-btn-attach"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                title="Attach PDF or image (max 10 MB)"
                aria-label="Attach document"
              >
                <i className="fa fa-paperclip" />
              </button>
              <input
                type="text"
                placeholder="Type your message..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
              />
              <button
                type="button"
                onClick={sendMessage}
                disabled={loading}
              >
                {uploading ? 'Wait' : 'Send'}
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
          setOpen((prev) => !prev);
          if (open && isExpanded) setIsExpanded(false); // Reset expand on close
        }}
      >
        <i className="fa fa-comments" />
      </button>
    </>
  );
};

export default Chatbot;

