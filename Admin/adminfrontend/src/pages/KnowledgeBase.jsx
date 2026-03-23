import React, { useState, useEffect, useRef, useContext, useMemo } from 'react';
import axios from 'axios';
import { 
  FileText, 
  Upload, 
  Trash2, 
  Search, 
  ChevronRight, 
  FileCheck, 
  AlertCircle,
  Loader2,
  Database,
  RefreshCw,
  Plus
} from 'lucide-react';
import { AuthContext } from '../AuthContext';

const KnowledgeBase = () => {
  const { admin } = useContext(AuthContext);
  const token = admin?.token;
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const headers = useMemo(() => token ? { Authorization: `Bearer ${token}` } : {}, [token]);

  const fetchChunks = async () => {
    setLoading(true);
    try {
      const res = await axios.get('/api/knowledge/chunks', { headers });
      if (res.data.success) {
        setChunks(res.data.chunks);
      }
    } catch (err) {
      setError("Failed to fetch knowledge base chunks.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChunks();
  }, [headers]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post('/api/knowledge/upload', formData, {
        headers: { ...headers, 'Content-Type': 'multipart/form-data' }
      });
      if (res.data.success) {
        fetchChunks();
      }
    } catch (err) {
      setError(err.response?.data?.error || "Failed to upload file.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const deleteChunk = async (id) => {
    if (!window.confirm("Delete this chunk?")) return;
    try {
      await axios.delete(`/api/knowledge/chunks/${id}`, { headers });
      setChunks(chunks.filter(c => c._id !== id));
    } catch (err) {
      alert("Failed to delete chunk.");
    }
  };

  const deleteDocument = async (docId) => {
    if (!window.confirm("Delete all chunks for this document?")) return;
    try {
      await axios.delete(`/api/knowledge/documents/${docId}`, { headers });
      setChunks(chunks.filter(c => c.document_id !== docId));
    } catch (err) {
      alert("Failed to delete document.");
    }
  };

  // Group chunks by filename
  const groupedDocs = useMemo(() => {
    const groups = {};
    chunks.forEach(chunk => {
      if (!groups[chunk.document_id]) {
        groups[chunk.document_id] = {
          filename: chunk.filename,
          document_id: chunk.document_id,
          created_at: chunk.created_at,
          chunks: []
        };
      }
      groups[chunk.document_id].chunks.push(chunk);
    });
    return Object.values(groups).filter(doc => 
      doc.filename.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [chunks, searchTerm]);

  return (
    <div style={{ padding: '2rem', minHeight: '100vh', background: 'var(--bg-main)' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Database color="var(--accent)" size={32} /> Global Knowledge Base
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>Manage documents and fragments used by the chatbot across all user sessions.</p>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button 
            onClick={fetchChunks}
            className="btn"
            style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)' }}
          >
            <RefreshCw size={18} className={loading ? 'spin' : ''} /> Refresh
          </button>
          <button 
            onClick={() => fileInputRef.current.click()}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            disabled={uploading}
          >
            {uploading ? <Loader2 size={18} className="spin" /> : <Plus size={18} />}
            Upload Document (PDF)
          </button>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
            accept=".pdf,.txt" 
            style={{ display: 'none' }} 
          />
        </div>
      </div>

      {error && (
        <div style={{ 
          padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', 
          borderRadius: '12px', color: '#ef4444', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '12px' 
        }}>
          <AlertCircle size={20} /> {error}
        </div>
      )}

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="glass" style={{ padding: '1.5rem', borderRadius: '20px', border: '1px solid var(--glass-border)' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>Total Documents</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700 }}>{groupedDocs.length}</div>
        </div>
        <div className="glass" style={{ padding: '1.5rem', borderRadius: '20px', border: '1px solid var(--glass-border)' }}>
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>Total Fragments</div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700 }}>{chunks.length}</div>
        </div>
      </div>

      {/* Search & List */}
      <div className="glass" style={{ borderRadius: '24px', border: '1px solid var(--glass-border)', overflow: 'hidden' }}>
        <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.02)' }}>
          <div style={{ position: 'relative', maxWidth: '400px' }}>
            <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
            <input 
              type="text" 
              placeholder="Search documents..." 
              className="input"
              style={{ paddingLeft: '40px', background: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', background: 'rgba(255,255,255,0.01)' }}>
                <th style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Document Name</th>
                <th style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Fragments</th>
                <th style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Uploaded Date</th>
                <th style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)', fontWeight: 600, textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="4" style={{ padding: '3rem', textAlign: 'center' }}>
                    <Loader2 size={32} className="spin" color="var(--accent)" />
                    <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>Loading catalog...</p>
                  </td>
                </tr>
              ) : groupedDocs.length === 0 ? (
                <tr>
                  <td colSpan="4" style={{ padding: '3rem', textAlign: 'center' }}>
                    <FileText size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                    <p style={{ color: 'var(--text-secondary)' }}>No documents found in knowledge base.</p>
                  </td>
                </tr>
              ) : (
                groupedDocs.map((doc) => (
                  <tr key={doc.document_id} style={{ borderBottom: '1px solid var(--glass-border)', transition: 'background 0.2s' }} className="table-row">
                    <td style={{ padding: '1.25rem 1.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{ 
                          width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(59,130,246,0.1)', 
                          display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)' 
                        }}>
                          <FileText size={20} />
                        </div>
                        <span style={{ fontWeight: 500 }}>{doc.filename}</span>
                      </div>
                    </td>
                    <td style={{ padding: '1.25rem 1.5rem' }}>
                      <span style={{ 
                        padding: '4px 10px', background: 'rgba(139,92,246,0.1)', color: '#a78bfa', 
                        borderRadius: '20px', fontSize: '0.85rem', fontWeight: 600 
                      }}>
                        {doc.chunks.length} chunks
                      </span>
                    </td>
                    <td style={{ padding: '1.25rem 1.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                      {new Date(doc.created_at).toLocaleDateString()} {new Date(doc.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right' }}>
                      <button 
                        onClick={() => deleteDocument(doc.document_id)}
                        style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', opacity: 0.7 }}
                        className="hover-scale"
                      >
                        <Trash2 size={18} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <style>{`
        .table-row:hover { background: rgba(255,255,255,0.02); }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .hover-scale:hover { transform: scale(1.1); opacity: 1 !important; }
      `}</style>
    </div>
  );
};

export default KnowledgeBase;
