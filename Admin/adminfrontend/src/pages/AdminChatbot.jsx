import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Bot, User, Cpu } from 'lucide-react';

const AdminChatbot = () => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello Admin. I am your operational assistant. I can help you query user data, check system health, and provide quick logs.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await axios.post('/api/admin-bot/ask', { message: userMsg.content });
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: Could not process request.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={styles.botIconMain}>
            <Cpu size={24} color="var(--accent)" />
          </div>
          <div>
            <h1 style={{margin: 0, fontSize: '1.5rem'}}>Genesis Ops Assistant</h1>
            <p style={{margin: 0, color: 'var(--text-secondary)'}}>Ask me anything about the system state or users.</p>
          </div>
        </div>
      </div>

      <div className="glass glass-card" style={styles.chatWindow}>
        <div style={styles.messagesContainer} ref={scrollRef}>
          {messages.map((msg, idx) => (
            <div key={idx} style={msg.role === 'user' ? styles.userRow : styles.botRow}>
              <div style={msg.role === 'user' ? styles.userBubble : styles.botBubble}>
                <div style={msg.role === 'user' ? styles.userAvatar : styles.botAvatar}>
                  {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                </div>
                <div style={styles.msgContent}>{msg.content}</div>
              </div>
            </div>
          ))}
          {isLoading && (
            <div style={styles.botRow}>
              <div style={styles.botBubble}>
                <div style={styles.botAvatar}><Bot size={16} /></div>
                <div style={styles.msgContent}>
                   <div style={styles.loadingDots}>Processing...</div>
                </div>
              </div>
            </div>
          )}
        </div>

        <form onSubmit={handleSend} style={styles.inputForm}>
          <input
            type="text"
            className="input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="E.g. What is the system status?"
            style={styles.inputField}
            disabled={isLoading}
          />
          <button type="submit" className="btn btn-primary" disabled={isLoading || !input.trim()}>
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  );
};

const styles = {
  container: {
    height: 'calc(100vh - 4rem)',
    display: 'flex',
    flexDirection: 'column'
  },
  header: {
    marginBottom: '2rem'
  },
  botIconMain: {
    width: '48px',
    height: '48px',
    borderRadius: '16px',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: '1px solid rgba(59, 130, 246, 0.2)'
  },
  chatWindow: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    padding: '1.5rem',
    overflow: 'hidden'
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
    paddingRight: '1rem',
    marginBottom: '1rem'
  },
  userRow: {
    display: 'flex',
    justifyContent: 'flex-end'
  },
  botRow: {
    display: 'flex',
    justifyContent: 'flex-start'
  },
  userBubble: {
    maxWidth: '75%',
    backgroundColor: 'var(--accent)',
    color: 'white',
    padding: '1rem',
    borderRadius: '16px',
    borderBottomRightRadius: '4px',
    display: 'flex',
    gap: '1rem',
    alignItems: 'flex-start'
  },
  botBubble: {
    maxWidth: '75%',
    backgroundColor: 'rgba(15, 23, 42, 0.6)',
    border: '1px solid var(--glass-border)',
    color: 'var(--text-primary)',
    padding: '1rem',
    borderRadius: '16px',
    borderBottomLeftRadius: '4px',
    display: 'flex',
    gap: '1rem',
    alignItems: 'flex-start'
  },
  userAvatar: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    width: '32px', height: '32px', borderRadius: '50%',
    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
  },
  botAvatar: {
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    color: 'var(--accent)',
    width: '32px', height: '32px', borderRadius: '50%',
    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
  },
  msgContent: {
    lineHeight: 1.5,
    marginTop: '5px'
  },
  inputForm: {
    display: 'flex',
    gap: '1rem',
    paddingTop: '1rem',
    borderTop: '1px solid var(--glass-border)'
  },
  inputField: {
    flex: 1
  },
  loadingDots: {
    color: 'var(--text-secondary)',
    fontStyle: 'italic'
  }
};

export default AdminChatbot;
