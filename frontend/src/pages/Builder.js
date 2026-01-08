import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import api from '../utils/api';
import { Sparkles, Loader2 } from 'lucide-react';
import GenerationLogger from '../components/GenerationLogger';
import BrandLogo from '../components/BrandLogo';
import { isDevAuthEnabled } from '../utils/devAuth';
import { BACKEND_URL } from '../utils/api';

const Builder = () => {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState('');
  const [mode, setMode] = useState('build');
  const [chatHistory, setChatHistory] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [chatting, setChatting] = useState(false);
  const [showLogger, setShowLogger] = useState(false);
  const [currentProjectId, setCurrentProjectId] = useState(null);

  const handleBuild = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a project description');
      return;
    }

    setGenerating(true);
    setShowLogger(true);
    try {
      const response = await api.post('/projects/generate', {
        prompt: prompt.trim(),
        tech_stack: {
          frontend: 'React',
          backend: 'FastAPI',
          database: 'MongoDB'
        }
      });

      setCurrentProjectId(response.data.project_id);
      toast.success(`Project "${response.data.name}" generated successfully!`);
      // Logger will handle navigation after completion
    } catch (error) {
      console.error('Generation error:', error);
      if (isDevAuthEnabled()) {
        const localId = `dev_${Date.now().toString(36)}`;
        const wantsCalculator = /\b(calc|calculator|arithmetic|add|subtract|multiply|divide)\b/i.test(prompt.trim());
        const calculatorApp = `
export default function App(){
  const [a, setA] = React.useState('');
  const [b, setB] = React.useState('');
  const [op, setOp] = React.useState('+');

  const calc = (x, y, o) => {
    const A = parseFloat(x), B = parseFloat(y);
    if (Number.isNaN(A) || Number.isNaN(B)) return '';
    switch (o) { case '+': return A+B; case '-': return A-B; case '*': return A*B; case '/': return B!==0?A/B:'∞'; default: return ''; }
  };

  const result = calc(a, b, op);

  return (
    <div style={{minHeight:'100vh', background:'#0b0f16', color:'#d7e7ff', fontFamily:'system-ui', padding:24}}>
      <header style={{display:'flex', alignItems:'center', gap:12, marginBottom:16}}>
        <div style={{width:12, height:12, borderRadius:999, background:'#20d6ff'}}></div>
        <h1 style={{margin:0, background:'linear-gradient(90deg,#20d6ff,#46ff9b)', WebkitBackgroundClip:'text', color:'transparent'}}>Digital Ninja Calculator</h1>
      </header>
      <div style={{display:'grid', gap:12, maxWidth:480, background:'rgba(255,255,255,0.06)', border:'1px solid rgba(255,255,255,0.12)', borderRadius:12, padding:16}}>
        <input placeholder="First number" value={a} onChange={e=>setA(e.target.value)} style={{padding:10, borderRadius:8, border:'1px solid #334155', background:'#0f172a', color:'#d7e7ff'}} />
        <select value={op} onChange={e=>setOp(e.target.value)} style={{padding:10, borderRadius:8, border:'1px solid #334155', background:'#0f172a', color:'#d7e7ff'}}>
          <option value="+">Add (+)</option>
          <option value="-">Subtract (-)</option>
          <option value="*">Multiply (*)</option>
          <option value="/">Divide (/)</option>
        </select>
        <input placeholder="Second number" value={b} onChange={e=>setB(e.target.value)} style={{padding:10, borderRadius:8, border:'1px solid #334155', background:'#0f172a', color:'#d7e7ff'}} />
        <div style={{padding:12, background:'#0f172a', border:'1px solid #334155', borderRadius:8}}>
          <strong style={{color:'#20d6ff'}}>Result:</strong> <span style={{marginLeft:8}}>{String(result)}</span>
        </div>
      </div>
    </div>
  );
}
        `.trim();

        const defaultApp = `
export default function App(){
  return (
    <div style={{minHeight:'100vh', background:'#0b0f16', color:'#d7e7ff', fontFamily:'system-ui', padding:24}}>
      <header style={{display:'flex', alignItems:'center', gap:12, marginBottom:16}}>
        <div style={{width:12, height:12, borderRadius:999, background:'#20d6ff'}}></div>
        <h1 style={{margin:0, background:'linear-gradient(90deg,#20d6ff,#46ff9b)', WebkitBackgroundClip:'text', color:'transparent'}}>Demo App</h1>
      </header>
      <p>Generated locally: ${prompt.trim().replace(/"/g, '\\"')}</p>
    </div>
  );
}
        `.trim();

        const demoProject = {
          project_id: localId,
          user_id: 'dev_user',
          name: prompt.trim().slice(0, 40) || 'Demo App',
          description: prompt.trim(),
          prompt: prompt.trim(),
          tech_stack: { frontend: 'React', backend: 'FastAPI', database: 'MongoDB' },
          files: [
            { path: 'src/App.js', content: wantsCalculator ? calculatorApp : defaultApp, language: 'js' },
            { path: 'src/index.css', content: 'body{font-family:sans-serif;margin:0;background:#0b0f16}', language: 'css' },
          ],
          status: 'active',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        const cache = JSON.parse(localStorage.getItem('dev_projects') || '{}');
        cache[localId] = demoProject;
        localStorage.setItem('dev_projects', JSON.stringify(cache));
        setCurrentProjectId(localId);
        toast.success(wantsCalculator ? 'Local calculator created' : 'Local demo project created');
        // Keep logger visible; onComplete will navigate to the editor
        return;
      }
      toast.error(error.response?.data?.detail || 'Failed to generate project');
      setShowLogger(false);
      setGenerating(false);
    }
  };

  const handleGenerationComplete = () => {
    setGenerating(false);
    setShowLogger(false);
    if (currentProjectId) {
      navigate(`/editor/${currentProjectId}`);
    }
  };

  const handleChat = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a message');
      return;
    }

    const userMessage = prompt.trim();
    // Use unique key to avoid duplicate key warnings
    setChatHistory(prev => [...prev, { role: 'user', content: userMessage, _k: Date.now() + Math.random() }]);
    setPrompt('');
    setChatting(true);

    try {
      // Stream from backend if available
      const token = localStorage.getItem('token');
      const res = await fetch(`${BACKEND_URL}/api/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ message: userMessage })
      });

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';

      // Push empty assistant message first (for streaming)
      setChatHistory(prev => [...prev, { role: 'assistant', content: '', _k: Date.now() + Math.random() }]);

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim();
              if (data === '[DONE]') break;
              if (data) {
                assistantMessage += (assistantMessage ? ' ' : '') + data;
                setChatHistory(prev => {
                  const arr = [...prev];
                  arr[arr.length - 1] = { role: 'assistant', content: assistantMessage, _k: arr[arr.length - 1]._k };
                  return arr;
                });
              }
            }
          }
        }
      } else {
        // Non-streaming fallback
        const json = await res.json().catch(() => null);
        const content = (json && json.message) ? `Echo: ${json.message}` : 'Response received.';
        setChatHistory(prev => [...prev, { role: 'assistant', content, _k: Date.now() + Math.random() }]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      if (isDevAuthEnabled()) {
        setChatHistory(prev => [...prev, { role: 'assistant', content: 'Dev reply: your request was processed locally.', _k: Date.now() + Math.random() }]);
      } else {
        toast.error('Failed to get response');
        setChatHistory(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.', _k: Date.now() + Math.random() }]);
      }
    } finally {
      setChatting(false);
    }
  };

  const handleSubmit = () => {
    if (mode === 'build') {
      handleBuild();
    } else {
      handleChat();
    }
  };

  return (
    <div className="min-h-screen bg-[#1c1c1e] p-6" data-testid="builder-page">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <BrandLogo className="w-16 h-16 rounded-lg shadow-lg" />
            <div className="w-14 h-14 bg-gradient-to-br from-[#9b00e8] to-[#ff4500] rounded-2xl flex items-center justify-center shadow-lg shadow-[#9b00e8]/50 animate-pulse-slow">
              <Sparkles className="w-8 h-8 text-white" strokeWidth={2.5} />
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-[#9b00e8] via-[#ff4500] to-[#9b00e8] bg-clip-text text-transparent animate-gradient">
              Digital Ninja App Builder
            </h1>
          </div>
          <p className="text-xl text-gray-300 font-medium">
            Describe your app idea. Get production-ready code instantly.
          </p>
          <p className="text-sm text-gray-400 mt-2 flex items-center justify-center gap-2">
            <span className="inline-flex items-center gap-1">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              Powered by GPT-4
            </span>
            <span className="text-gray-600">•</span>
            <span>Deploy to Vercel & Render</span>
            <span className="text-gray-600">•</span>
            <span>Export to GitHub</span>
          </p>
        </div>

        {/* Mode Selector */}
        <div className="flex justify-center gap-4 mb-6">
          <Button
            onClick={() => setMode('build')}
            className={`h-12 px-8 font-semibold transition-all ${
              mode === 'build'
                ? 'bg-gradient-to-r from-[#9b00e8] to-[#ff4500] text-white shadow-lg shadow-[#9b00e8]/50'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <Sparkles className="w-5 h-5 mr-2" />
            Build Mode
          </Button>
          <Button
            onClick={() => setMode('chat')}
            className={`h-12 px-8 font-semibold transition-all ${
              mode === 'chat'
                ? 'bg-gradient-to-r from-[#9b00e8] to-[#ff4500] text-white shadow-lg shadow-[#9b00e8]/50'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.293 1.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L7.586 10 5.293 7.707a1 1 0 010-1.414zM11 12a1 1 0 100 2h3a1 1 0 100-2h-3z" />
            </svg>
            Chat Mode
          </Button>
        </div>

        <Card className="bg-gray-900/50 backdrop-blur-lg border-gray-800 p-6 shadow-2xl">
          {mode === 'build' ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">
                  What do you want to build?
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSubmit())}
                  placeholder="Example: Build a calculator with basic arithmetic operations, a clean UI, and keyboard support"
                  className="w-full h-32 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-[#ff4500] focus:ring-2 focus:ring-[#ff4500]/50 resize-none"
                  disabled={generating}
                />
                <p className="text-xs text-gray-500 mt-2">
                  💡 Be specific about features and functionality you want
                </p>
              </div>

              <Button
                onClick={handleBuild}
                disabled={generating || !prompt.trim()}
                className="w-full h-14 bg-gradient-to-r from-[#9b00e8] to-[#ff4500] hover:from-[#8800d4] hover:to-[#e63e00] text-white font-semibold text-lg shadow-lg shadow-[#9b00e8]/30 disabled:opacity-50 rounded-xl transition-all"
              >
                {generating ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Generating with GPT-4...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5 mr-2" />
                    Build App Now
                  </>
                )}
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="h-96 overflow-y-auto space-y-3 mb-4 p-4 bg-gray-800/50 rounded-lg">
                {chatHistory.length === 0 ? (
                  <div className="text-center text-gray-500 mt-20">
                    <p className="text-lg">Start a conversation with GPT-4</p>
                    <p className="text-sm mt-2">Ask about debugging, improvements, or technical questions</p>
                  </div>
                ) : (
                  chatHistory.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`p-4 rounded-xl animate-fade-in ${
                        msg.role === 'user'
                          ? 'bg-gradient-to-r from-[#9b00e8] to-[#ff4500] text-white ml-12'
                          : 'bg-gray-700/80 text-gray-100 mr-12 border border-gray-600'
                      }`}
                    >
                      <p className="text-xs font-semibold mb-2 opacity-80">
                        {msg.role === 'user' ? '👤 You' : '🤖 GPT-4'}
                      </p>
                      <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    </div>
                  ))
                )}
              </div>

              <div className="flex gap-2">
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSubmit())}
                  placeholder="Ask GPT-4 anything about your app..."
                  className="flex-1 h-20 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-[#ff4500] focus:ring-2 focus:ring-[#ff4500]/50 resize-none"
                  disabled={chatting}
                />
                <Button
                  onClick={handleChat}
                  disabled={chatting || !prompt.trim()}
                  className="h-20 px-6 bg-gradient-to-r from-[#9b00e8] to-[#ff4500] hover:from-[#8800d4] hover:to-[#e63e00] text-white font-semibold disabled:opacity-50 rounded-xl shadow-lg transition-all"
                >
                  {chatting ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    'Send'
                  )}
                </Button>
              </div>
            </div>
          )}
        </Card>

        {mode === 'build' && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold text-white mb-4">Try these examples:</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[
                "Build a calculator with basic arithmetic operations",
                "Create a todo list with add, edit, and delete features",
                "Build a weather app with city search",
                "Create a markdown editor with live preview"
              ].map((example, idx) => (
                <button
                  key={idx}
                  onClick={() => setPrompt(example)}
                  className="text-left p-4 bg-gray-800/50 hover:bg-gray-800 border border-gray-700 hover:border-[#ff4500]/50 rounded-lg transition-all text-sm text-gray-300 hover:text-white"
                  disabled={generating}
                >
                  💡 {example}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Generation Logger Modal */}
      {showLogger && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="max-w-2xl w-full">
            <div className="bg-gray-900 rounded-lg p-6 border border-gray-800">
              <h2 className="text-2xl font-bold text-white mb-4">Building Your App...</h2>
              <GenerationLogger
                projectId={currentProjectId}
                onComplete={handleGenerationComplete}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Builder;