import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import AuthCallback from './pages/AuthCallback';
import ImprovedBuilder from './pages/ImprovedBuilder';
import EnhancedBuilder from './pages/EnhancedBuilder';
import Projects from './pages/Projects';
import ProjectEditor from './pages/ProjectEditor';
import ProtectedRoute from './components/ProtectedRoute';
import { Toaster } from './components/ui/sonner';
import './App.css';
import AiBuilder from './pages/AiBuilder';

function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/" element={<Navigate to="/enhanced-builder" replace />} />
          <Route path="/projects" element={<ProtectedRoute><Projects /></ProtectedRoute>} />
          <Route path="/builder" element={<ProtectedRoute><ImprovedBuilder /></ProtectedRoute>} />
          <Route path="/enhanced-builder" element={<ProtectedRoute><EnhancedBuilder /></ProtectedRoute>} />
          <Route path="/enhanced-builder/:projectId" element={<ProtectedRoute><EnhancedBuilder /></ProtectedRoute>} />
          <Route path="/ai-builder" element={<ProtectedRoute><AiBuilder /></ProtectedRoute>} />
          <Route path="/editor/:projectId" element={<ProtectedRoute><ProjectEditor /></ProtectedRoute>} />
        </Routes>
        <Toaster />
      </div>
    </BrowserRouter>
  );
}

export default App;