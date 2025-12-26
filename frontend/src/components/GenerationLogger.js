import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/card';
import { CheckCircle2, Loader2, AlertCircle } from 'lucide-react';

export const GenerationLogger = ({ projectId, onComplete }) => {
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState('initializing');

  useEffect(() => {
    // Simulate real-time logging
    const logSteps = [
      { id: 1, message: 'Analyzing project requirements...', time: 1000 },
      { id: 2, message: 'Generating React components with Tailwind CSS...', time: 2000 },
      { id: 3, message: 'Creating FastAPI backend with CRUD endpoints...', time: 2500 },
      { id: 4, message: 'Setting up MongoDB schemas...', time: 1500 },
      { id: 5, message: 'Configuring Vercel deployment...', time: 1000 },
      { id: 6, message: 'Configuring Render deployment...', time: 1000 },
      { id: 7, message: 'Generating .env.example and documentation...', time: 1000 },
      { id: 8, message: 'Finalizing code structure...', time: 1500 }
    ];

    let currentIndex = 0;
    let timer;

    const addLog = () => {
      if (currentIndex < logSteps.length) {
        const step = logSteps[currentIndex];
        setLogs(prev => [...prev, { ...step, status: 'in-progress', timestamp: new Date() }]);
        
        timer = setTimeout(() => {
          setLogs(prev => 
            prev.map(log => 
              log.id === step.id ? { ...log, status: 'completed' } : log
            )
          );
          currentIndex++;
          addLog();
        }, step.time);
      } else {
        setStatus('completed');
        if (onComplete) {
          setTimeout(onComplete, 500);
        }
      }
    };

    addLog();

    return () => clearTimeout(timer);
  }, [projectId, onComplete]);

  return (
    <Card className="bg-gray-900/50 border-gray-800 p-6 max-h-96 overflow-y-auto">
      <div className="space-y-3">
        {logs.map(log => (
          <div key={log.id} className="flex items-start gap-3">
            {log.status === 'completed' ? (
              <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
            ) : (
              <Loader2 className="w-5 h-5 text-[#ff4500] animate-spin flex-shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <p className="text-white text-sm">{log.message}</p>
              <p className="text-gray-500 text-xs mt-1">
                {log.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        
        {status === 'completed' && (
          <div className="flex items-start gap-3 pt-3 border-t border-gray-800">
            <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-green-500 font-semibold">Generation Complete!</p>
              <p className="text-gray-400 text-sm">Your app is ready to edit and deploy</p>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default GenerationLogger;
