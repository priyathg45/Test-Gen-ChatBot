import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Lock, User } from 'lucide-react';
import { AuthContext } from '../AuthContext';

const Login = () => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div className="glass glass-card" style={styles.card}>
        <div style={styles.header}>
          <div style={styles.iconWrapper}>
            <Shield size={40} color="var(--accent)" />
          </div>
          <h1>Admin Access</h1>
          <p>Login to manage the Genesis ChatBot system</p>
        </div>

        {error && (
          <div style={styles.errorBanner}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.inputGroup}>
            <User size={20} color="var(--text-secondary)" style={styles.inputIcon} />
            <input 
              type="text" 
              className="input" 
              placeholder="Username" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={styles.inputWithIcon}
              required
            />
          </div>

          <div style={styles.inputGroup}>
            <Lock size={20} color="var(--text-secondary)" style={styles.inputIcon} />
            <input 
              type="password" 
              className="input" 
              placeholder="Password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.inputWithIcon}
              required
            />
          </div>

          <button 
            type="submit" 
            className="btn btn-primary" 
            style={styles.submitBtn}
            disabled={isLoading}
          >
            {isLoading ? 'Authenticating...' : 'Secure Login'}
          </button>
        </form>
      </div>
    </div>
  );
};

const styles = {
  container: {
    height: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '1rem'
  },
  card: {
    width: '100%',
    maxWidth: '420px',
    padding: '3rem 2.5rem',
  },
  header: {
    textAlign: 'center',
    marginBottom: '2.5rem'
  },
  iconWrapper: {
    width: '80px',
    height: '80px',
    borderRadius: '20px',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 1.5rem auto'
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1.25rem'
  },
  inputGroup: {
    position: 'relative'
  },
  inputIcon: {
    position: 'absolute',
    left: '1rem',
    top: '50%',
    transform: 'translateY(-50%)',
    zIndex: 1
  },
  inputWithIcon: {
    paddingLeft: '3rem'
  },
  submitBtn: {
    width: '100%',
    marginTop: '1rem',
    padding: '1rem'
  },
  errorBanner: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid var(--danger)',
    color: '#fca5a5',
    padding: '1rem',
    borderRadius: '8px',
    marginBottom: '1.5rem',
    textAlign: 'center',
    fontSize: '0.9rem'
  }
};

export default Login;
