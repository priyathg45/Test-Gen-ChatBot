import React, { useState, useRef, useEffect, useContext } from 'react';
import axios from 'axios';
import { Send, Bot, User, Cpu, Paperclip, X, Zap } from 'lucide-react';
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

const WELCOME = `## 👋 Hello, Admin!

I'm your **Genesis Intelligence Assistant** — powered by Llama via Ollama.

I have **live access** to your system data and can:
- 📊 Answer questions about users, jobs and chat sessions
- 👥 Manage users (activate, deactivate, delete)
- 💼 Manage jobs (accept, reject)
- 📎 Read uploaded PDFs and answer questions about them

**Try a quick action below, or type anything!**`;

const AdminChatbot = () => {
  const { token } = useContext(AuthContext);
  const [messages, setMessages] = useState([{ role: 'assistant', content: WELCOME }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [stagedFiles, setStagedFiles] = useState([]);
  const [fileContext, setFileContext] = useState('');
  const [uploading, setUploading] = useState(false);
  const scrollRef = useRef(null);
  const fileInputRef = useRef(null);

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const appendMsg = (role, content) =>
    setMessages(prev => [...prev, { role, content }]);

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
      appendMsg('assistant', `✅ Read **${newNames.join(', ')}**. You can now ask questions about ${newNames.length > 1 ? 'these files' : 'this file'}.`);
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
    if (!userMsg || isLoading) return;
    setInput('');
    appendMsg('user', userMsg);
    setIsLoading(true);
    try {
      const res = await axios.post('/api/admin-bot/ask', {
        message: userMsg,
        file_context: fileContext,
      }, { headers });
      appendMsg('assistant', res.data.response || 'No response received.');
    } catch {
      appendMsg('assistant', '❌ Could not reach the server. Make sure the admin backend is running.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <div style={{ height: 'calc(100vh - 4rem)', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{
          width: 52, height: 52, borderRadius: 16,
          background: 'rgba(59,130,246,0.15)', border: '1px solid rgba(59,130,246,0.3)',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <Cpu size={26} color="var(--accent)" />
        </div>
        <div>
          <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Genesis Intelligence</h1>
          <p style={{ margin: 0 }}>Llama-powered admin assistant with full system access</p>
        </div>
      </div>

      {/* Quick chips */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '1rem' }}>
        {QUICK_CHIPS.map(chip => (
          <button key={chip.label} onClick={() => handleSend(chip.msg)} disabled={isLoading}
            style={{
              padding: '6px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: 600,
              background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.35)',
              color: 'var(--accent)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px',
              opacity: isLoading ? 0.5 : 1, transition: 'opacity 0.15s',
            }}>
            {chip.label}
          </button>
        ))}
      </div>

      {/* Chat window */}
      <div className="glass glass-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '1.5rem' }}>
        {/* Messages */}
        <div ref={scrollRef} style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem', marginBottom: '1rem', paddingRight: '4px' }}>
          {messages.map((msg, idx) => (
            <div key={idx} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
              <div style={{
                maxWidth: '78%', display: 'flex', gap: '0.75rem', alignItems: 'flex-start',
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              }}>
                {/* Avatar */}
                <div style={{
                  width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
                  background: msg.role === 'user' ? 'var(--accent)' : 'rgba(59,130,246,0.2)',
                  color: msg.role === 'user' ? '#fff' : 'var(--accent)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                </div>
                {/* Bubble */}
                <div style={{
                  padding: '0.9rem 1.1rem', borderRadius: msg.role === 'user' ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
                  background: msg.role === 'user' ? 'var(--accent)' : 'rgba(15,23,42,0.6)',
                  border: msg.role === 'user' ? 'none' : '1px solid var(--glass-border)',
                  color: 'var(--text-primary)', lineHeight: 1.6, fontSize: '0.9rem',
                }}>
                  {msg.role === 'assistant'
                    ? <ReactMarkdown>{msg.content}</ReactMarkdown>
                    : msg.content}
                </div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
              <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'rgba(59,130,246,0.2)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Bot size={16} />
              </div>
              <div style={{ padding: '0.9rem 1.1rem', borderRadius: '4px 16px 16px 16px', background: 'rgba(15,23,42,0.6)', border: '1px solid var(--glass-border)' }}>
                <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                  {[0,1,2].map(i => (
                    <div key={i} style={{
                      width: 8, height: 8, borderRadius: '50%', background: 'var(--accent)',
                      animation: `bounce 1.2s ${i * 0.2}s infinite ease-in-out`,
                    }} />
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Staged file chips */}
        {stagedFiles.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '8px' }}>
            {stagedFiles.map(name => (
              <div key={name} style={{
                display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px', fontWeight: 600,
                background: 'rgba(59,130,246,0.15)', border: '1px solid rgba(59,130,246,0.35)',
                color: 'var(--accent)', padding: '4px 10px 4px 8px', borderRadius: '20px',
              }}>
                <Paperclip size={11} /> <span>{name}</span>
                <button onClick={() => removeFile(name)} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '14px', lineHeight: 1, padding: 0 }}>
                  <X size={13} />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Input area */}
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', paddingTop: '0.75rem', borderTop: '1px solid var(--glass-border)' }}>
          <input ref={fileInputRef} type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.txt,.csv" style={{ display: 'none' }} onChange={handleFileSelect} />
          <button
            type="button" onClick={() => fileInputRef.current?.click()} disabled={uploading}
            style={{
              width: 40, height: 40, borderRadius: '10px', border: '1px solid var(--glass-border)',
              background: 'transparent', color: uploading ? 'var(--text-secondary)' : 'var(--accent)',
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            }} title="Attach PDF or image">
            {uploading ? <Zap size={18} className="spin" /> : <Paperclip size={18} />}
          </button>
          <input
            className="input" style={{ flex: 1 }}
            value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
            placeholder={stagedFiles.length > 0 ? `Ask about ${stagedFiles.join(', ')}…` : 'Ask anything about the system…'}
            disabled={isLoading}
          />
          <button
            type="button" onClick={() => handleSend()} disabled={isLoading || !input.trim()}
            className="btn btn-primary" style={{ padding: '0.6rem 1.1rem', flexShrink: 0 }}>
            <Send size={18} />
          </button>
        </div>
      </div>

      <style>{`
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

export default AdminChatbot;
