import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute, AdminRoute } from './components/ProtectedRoute';
import NavBar from './components/NavBar';

// Temporary placeholders until pages are built in plan 2.5, 2.6, 2.7
const LoginPage = () => <div className="page-enter" style={{ padding: '2rem', textAlign: 'center' }}>Login Page (Coming soon)</div>;
const RegisterPage = () => <div className="page-enter" style={{ padding: '2rem', textAlign: 'center' }}>Register Page (Coming soon)</div>;
const SearchPage = () => <div className="page-enter" style={{ padding: '2rem', textAlign: 'center' }}>Search Page (Coming soon)</div>;
const AdminPage = () => <div className="page-enter" style={{ padding: '2rem', textAlign: 'center' }}>Admin Page (Coming soon)</div>;

function App() {
  return (
    <AuthProvider>
      <div className="bg-orbs"></div>
      <BrowserRouter>
        <NavBar />
        <Routes>
          <Route path="/" element={<Navigate to="/search" replace />} />
          
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          <Route element={<ProtectedRoute />}>
            <Route path="/search" element={<SearchPage />} />
          </Route>
          
          <Route element={<AdminRoute />}>
            <Route path="/admin" element={<AdminPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
