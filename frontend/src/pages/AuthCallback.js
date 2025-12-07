import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import api from '../utils/api';

const AuthCallback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const processAuth = async () => {
      try {
        // Get session_id from URL hash
        const hash = window.location.hash;
        const params = new URLSearchParams(hash.substring(1));
        const sessionId = params.get('session_id');

        if (!sessionId) {
          toast.error('Authentication failed - no session ID');
          navigate('/login');
          return;
        }

        // Call backend to process session
        const response = await api.post('/auth/google/session', {
          session_id: sessionId
        });

        // Store tokens and user data
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        
        // Set flag to skip delay in ProtectedRoute
        sessionStorage.setItem('just_authenticated', 'true');

        toast.success('Welcome!');
        
        // Redirect to projects dashboard
        navigate('/projects', { replace: true });
      } catch (error) {
        console.error('Auth callback error:', error);
        toast.error('Authentication failed');
        navigate('/login');
      }
    };

    processAuth();
  }, [navigate]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-900">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
        <p className="text-white mt-4">Completing sign in...</p>
      </div>
    </div>
  );
};

export default AuthCallback;