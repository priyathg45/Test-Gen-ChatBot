import React, { useState, useRef, useEffect } from 'react';
import './Chatbot.css';
import { CHAT_API_URL } from '../config';
import { useAuth } from '../context/AuthContext';

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
        if (sessData.success && sessData.sessions && sessData.sessions.length > 0) {
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

  useEffect(() => {
    if (open) fetchSessionData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, token]);

  const uploadDocument = async (file) => {
    if (!file || uploading) return;
    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > MAX_FILE_SIZE_MB) {
      appendMessage(
        `File is too large (${sizeMB.toFixed(1)} MB). Max ${MAX_FILE_SIZE_MB} MB.`,
        'bot'
      );
      return;
    }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('session_id', sessionIdRef.current);

      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${CHAT_API_URL}/upload`, {
        method: 'POST',
        headers,
        body: formData,
      });
      const data = await res.json();
      if (data.success && data.attachment) {
        setAttachments((prev) => [...prev, data.attachment]);
        appendMessage(
          `I've received "${data.attachment.filename}". You can ask me to summarize it or ask questions about its content.`,
          'bot'
        );
      } else {
        appendMessage(
          data.error || 'Upload failed. Please try again.',
          'bot'
        );
      }
    } catch (err) {
      const msg =
        err.message === 'Failed to fetch'
          ? 'Cannot reach the server. Make sure the backend is running.'
          : err.message || 'Upload failed.';
      appendMessage(msg, 'bot');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setTimeout(scrollToBottom, 100);
    }
  };

  const onFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) uploadDocument(file);
  };

  const appendMessage = (text, from) => {
    if (!text) return;
    setMessages((prev) => [
      ...prev,
      { id: Date.now() + Math.random(), from, text },
    ]);
  };

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    appendMessage(trimmed, 'user');
    setInput('');
    setLoading(true);

    try {
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const res = await fetch(`${CHAT_API_URL}/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: trimmed,
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
          <h4>AAW Assistant</h4>
          <div style={{ display: 'flex', gap: '8px' }}>
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
        <div className="chatbot-messages">
          {messages.map((m) => (
            <div key={m.id} className={`chatbot-message ${m.from}`}>
              {m.text}
            </div>
          ))}
          {loading && (
            <div className="chatbot-message bot chatbot-typing">
              Thinking…
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        {attachments.length > 0 && (
          <div className="chatbot-attachments">
            <span className="chatbot-attachments-label">Attached:</span>
            {attachments.map((att) => (
              <span key={att.id} className="chatbot-attachment-tag" title={att.filename}>
                {att.filename}
              </span>
            ))}
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
            Send
          </button>
        </div>
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

