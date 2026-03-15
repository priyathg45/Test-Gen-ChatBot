import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Mail, Calendar, Clock, MessageCircle } from 'lucide-react';

const UserProfile = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [userRes, chatRes] = await Promise.all([
          axios.get(`/api/users/${id}`),
          axios.get(`/api/chat/history/${id}`) // Trying ID first
        ]);
        
        setUser(userRes.data.user);
        
        // If history is empty, the user might be using username as session id
        if (chatRes.data.history.length === 0 && userRes.data.user.username) {
           const fallbackRes = await axios.get(`/api/chat/history/${userRes.data.user.username}`);
           setChatHistory(fallbackRes.data.history);
        } else {
           setChatHistory(chatRes.data.history);
        }
      } catch (err) {
        console.error("Error fetching user data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  if (loading) return <div style={styles.loading}>Loading profile...</div>;
  if (!user) return <div style={styles.loading}>User not found.</div>;

  return (
    <div>
      <div style={styles.header}>
        <button className="btn" style={styles.backBtn} onClick={() => navigate('/users')}>
          <ArrowLeft size={18} /> Back to Users
        </button>
      </div>

      <div style={styles.grid}>
        {/* Profile Card */}
        <div className="glass glass-card" style={styles.profileCard}>
          <div style={styles.avatarLarge}>
             {user.username?.charAt(0).toUpperCase() || 'U'}
          </div>
          <h2 style={{margin: '1rem 0 0.5rem 0'}}>{user.username}</h2>
          
          <div style={styles.infoList}>
            <div style={styles.infoItem}>
              <Mail size={16} color="var(--text-secondary)" />
              <span>{user.email || 'No email provided'}</span>
            </div>
            <div style={styles.infoItem}>
              <Calendar size={16} color="var(--text-secondary)" />
              <span>Joined: {new Date(user.created_at).toLocaleDateString()}</span>
            </div>
            <div style={styles.infoItem}>
              <MessageCircle size={16} color="var(--text-secondary)" />
              <span>Total Interactions: {chatHistory.length}</span>
            </div>
          </div>
        </div>

        {/* Chat History Panel */}
        <div className="glass glass-card" style={styles.historyPanel}>
          <h3 style={{marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
            <Clock size={20} color="var(--accent)" /> Chat History Logs
          </h3>
          
          <div style={styles.chatScroll}>
            {chatHistory.length === 0 ? (
              <p style={{color: 'var(--text-secondary)', textAlign: 'center', marginTop: '3rem'}}>
                No chat history found for this user.
              </p>
            ) : (
              chatHistory.map((chat, idx) => (
                <div key={idx} style={styles.chatMessage}>
                  <div style={styles.messageHeader}>
                     <span style={styles.roleLabel(chat.role || 'user')}>
                        {chat.role === 'assistant' ? 'Bot' : 'User'}
                     </span>
                     <span style={styles.timeStamp}>
                        {chat.timestamp ? new Date(chat.timestamp).toLocaleString() : ''}
                     </span>
                  </div>
                  <div style={styles.messageContent}>
                    {chat.content}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const styles = {
  header: {
    marginBottom: '2rem'
  },
  backBtn: {
    backgroundColor: 'transparent',
    border: '1px solid var(--glass-border)',
    color: 'var(--text-primary)',
    padding: '0.5rem 1rem'
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: '1fr 2fr',
    gap: '2rem',
    height: 'calc(100vh - 140px)'
  },
  profileCard: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    height: 'fit-content'
  },
  avatarLarge: {
    width: '100px',
    height: '100px',
    borderRadius: '50%',
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    color: 'var(--accent)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '3rem',
    fontWeight: 'bold',
    marginBottom: '1rem'
  },
  infoList: {
    width: '100%',
    marginTop: '2rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
    textAlign: 'left'
  },
  infoItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    color: 'var(--text-secondary)',
    fontSize: '0.95rem'
  },
  historyPanel: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%'
  },
  chatScroll: {
    flex: 1,
    overflowY: 'auto',
    paddingRight: '1rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem'
  },
  chatMessage: {
    padding: '1rem',
    borderRadius: '8px',
    backgroundColor: 'rgba(15, 23, 42, 0.4)',
    border: '1px solid rgba(255, 255, 255, 0.05)'
  },
  messageHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: '0.75rem',
    fontSize: '0.85rem'
  },
  roleLabel: (role) => ({
    fontWeight: '600',
    color: role === 'assistant' ? 'var(--success)' : 'var(--accent)',
    textTransform: 'uppercase',
    letterSpacing: '0.05em'
  }),
  timeStamp: {
    color: 'var(--text-secondary)'
  },
  messageContent: {
    lineHeight: 1.5,
    color: '#E2E8F0',
    whiteSpace: 'pre-wrap'
  },
  loading: {
    color: 'var(--text-secondary)',
    fontSize: '1.2rem',
    textAlign: 'center',
    marginTop: '4rem'
  }
};

export default UserProfile;
