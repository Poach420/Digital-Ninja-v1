import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import api from '../utils/api';

const AuthCallback = () => {
  const navigate = useNavigate();
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    // Prevent double execution
    if (processing) return;
    
    const processAuth = async () => {
      setProcessing(true);
      
      try {
        // Get session_id from URL hash
        const hash = window.location.hash;
        const params = new URLSearchParams(hash.substring(1));
        const sessionId = params.get('session_id');

        if (!sessionId) {
          console.error('No session_id in URL');
          toast.error('Authentication failed - no session ID');
          setTimeout(() => navigate('/login', { replace: true }), 1500);
          return;
        }

        console.log('Processing session_id:', sessionId.substring(0, 10) + '...');

        // Call backend to process session
        const response = await api.post('/auth/google/session', {
          session_id: sessionId
        });

        // Store tokens and user data
        localStorage.setItem('token', response.data.access_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        
        console.log('Auth successful, redirecting to projects...');
        toast.success('Welcome!');
        
        // Small delay to ensure toast shows
        setTimeout(() => {
          navigate('/projects', { replace: true });
        }, 500);
        
      } catch (error) {
        console.error('Auth callback error:', error);
        const errorMsg = error.response?.data?.detail || 'Authentication failed';
        toast.error(errorMsg);
        
        setTimeout(() => {
          navigate('/login', { replace: true });
        }, 2000);
      }
    };

    processAuth();
  }, []); // Empty dependency array - run once

  return (
    <div className="flex items-center justify-center min-h-screen bg-[#1c1c1e]">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-[#ff4500]"></div>
        <p className="text-white mt-4 text-lg">Completing sign in...</p>
        <p className="text-gray-400 mt-2 text-sm">Please wait while we verify your session</p>
      </div>
    </div>
  );
};

export default AuthCallback;