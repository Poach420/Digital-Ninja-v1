import React, { useEffect, useState } from 'react';
import api, { BACKEND_URL } from '../utils/api';
import { isDevAuthEnabled } from '../utils/devAuth';

const Dot = ({ ok }) => (
  <span 
    style={{ 
      display: 'inline-block', 
      width: 8, 
      height: 8, 
      borderRadius: 999, 
      background: ok ? '#22c55e' : '#ef4444', 
      marginRight: 8 
    }} 
    aria-hidden="true" 
  />
);

const Row = ({ label, ok, extra }) => (
  <div className="flex items-center text-sm text-slate-300">
    <Dot ok={ok} />
    <span className="mr-2">{label}</span>
    {extra ? <span className="text-slate-500">({extra})</span> : null}
  </div>
);

const SystemStatus = () => {
  const [pngLogo, setPngLogo] = useState(false);
  const [backendOk, setBackendOk] = useState(false);
  const [authOk, setAuthOk] = useState(false);
  const [projectsOk, setProjectsOk] = useState(false);
  const [chatOk, setChatOk] = useState(false);
  const [devMode, setDevMode] = useState(false);
  const [notes, setNotes] = useState([]);

  useEffect(() => {
    // PNG logo detection
    const img = new Image();
    img.onload = () => setPngLogo(true);
    img.onerror = () => setPngLogo(false);
    img.src = '/digital-ninja-logo.png';
    
    // Dev mode
    setDevMode(isDevAuthEnabled());
    
    // Auth token present
    const token = localStorage.getItem('token');
    setAuthOk(Boolean(token));
    
    // Backend health
    fetch(`${BACKEND_URL}/api/health`, { credentials: 'include' })
      .then((r) => {
        if (r.ok) {
          setBackendOk(true);
          return r.json();
        }
        setBackendOk(false);
        return null;
      })
      .then((json) => {
        if (json?.status !== 'ok') {
          setNotes((n) => [...n, 'Health check returned non-ok status']);
        }
      })
      .catch(() => setBackendOk(false));
    
    // Projects API
    api.get('/projects')
      .then(() => setProjectsOk(true))
      .catch(() => setProjectsOk(false));
    
    // Chat endpoint basic reachability
    fetch(`${BACKEND_URL}/api/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message: 'proof' }),
      credentials: 'include',
    })
      .then((r) => setChatOk(r.ok))
      .catch(() => setChatOk(false));
  }, []);

  return (
    <div className="mt-2 rounded-md border border-slate-700 bg-slate-800/70 p-3">
      <div className="text-xs uppercase tracking-wide text-slate-400 mb-2">System Status (proof)</div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-y-2 gap-x-6">
        <Row 
          label="Logo PNG detected" 
          ok={pngLogo} 
          extra={pngLogo ? 'PNG in use' : 'Fallback SVG in use'} 
        />
        <Row 
          label="Backend health" 
          ok={backendOk} 
          extra={BACKEND_URL} 
        />
        <Row 
          label="Auth token present" 
          ok={authOk} 
        />
        <Row 
          label="Projects API reachable" 
          ok={projectsOk} 
        />
        <Row 
          label="Chat endpoint reachable" 
          ok={chatOk} 
          extra={chatOk ? 'OK' : devMode ? 'Dev fallback available' : 'Unreachable'} 
        />
        <Row 
          label="Dev mode (fallbacks enabled)" 
          ok={devMode} 
        />
      </div>
      {notes.length > 0 ? (
        <div className="mt-2 text-xs text-amber-400">
          {notes.map((n, i) => (
            <div key={i}>• {n}</div>
          ))}
        </div>
      ) : null}
    </div>
  );
};

export default SystemStatus;