import React, { useContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, AuthContext } from './AuthContext';

// Layout & Pages (to be implemented)
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import UsersList from './pages/UsersList';
import UserProfile from './pages/UserProfile';
import SystemLogs from './pages/SystemLogs';
import AdminChatbot from './pages/AdminChatbot';

// Protected Route Wrapper
const ProtectedRoute = ({ children }) => {
  const { admin, loading } = useContext(AuthContext);
  if (loading) return <div>Loading...</div>;
  if (!admin) return <Navigate to="/login" replace />;
  
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        {children}
      </main>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/users" element={
            <ProtectedRoute>
              <UsersList />
            </ProtectedRoute>
          } />
          
          <Route path="/users/:id" element={
            <ProtectedRoute>
              <UserProfile />
            </ProtectedRoute>
          } />
          
          <Route path="/logs" element={
            <ProtectedRoute>
              <SystemLogs />
            </ProtectedRoute>
          } />

          <Route path="/chatbot" element={
            <ProtectedRoute>
              <AdminChatbot />
            </ProtectedRoute>
          } />
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
