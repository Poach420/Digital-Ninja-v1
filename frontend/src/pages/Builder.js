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
    setChatHistory(prev => [...prev, { role: 'user', content: userMessage }]);
    setPrompt('');
    setChatting(true);

    try {
      const response = await api.post('/chat', {
        message: userMessage,
        history: chatHistory
      });

      setChatHistory(prev => [...prev, { role: 'assistant', content: response.data.response }]);
    } catch (error) {
      console.error('Chat error:', error);
      toast.error('Failed to get response');
      setChatHistory(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
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
            <div className="w-12 h-12 bg-[#ff4500] rounded-lg flex items-center justify-center">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-5xl font-bold text-white">Digital Ninja App Builder</h1>
          </div>
          <p className="text-xl text-gray-300">
            Describe your app idea. Get production-ready code instantly.
          </p>
          <p className="text-sm text-gray-400 mt-2">
            Powered by GPT-4 • Deploy to Vercel & Render • Export to GitHub
          </p>
        </div>

        {/* Mode Selector */}
        <div className="flex justify-center gap-4 mb-6">
          <Button
            onClick={() => setMode('build')}
            className={`h-12 px-8 font-semibold ${
              mode === 'build'
                ? 'bg-[#ff4500] text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            <Sparkles className="w-5 h-5 mr-2" />
            Build Mode
          </Button>
          <Button
            onClick={() => setMode('chat')}
            className={`h-12 px-8 font-semibold ${
              mode === 'chat'
                ? 'bg-[#ff4500] text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
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
                className="w-full h-14 bg-[#ff4500] hover:bg-[#ff5722] text-white font-semibold text-lg shadow-lg shadow-[#ff4500]/30 disabled:opacity-50"
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
                      className={`p-4 rounded-lg ${
                        msg.role === 'user'
                          ? 'bg-[#ff4500] text-white ml-12'
                          : 'bg-gray-700 text-gray-100 mr-12'
                      }`}
                    >
                      <p className="text-sm font-semibold mb-1">
                        {msg.role === 'user' ? 'You' : 'GPT-4'}
                      </p>
                      <p className="whitespace-pre-wrap">{msg.content}</p>
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
                  className="h-20 px-6 bg-[#ff4500] hover:bg-[#ff5722] text-white font-semibold disabled:opacity-50"
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
    </div>
  );
};

export default Builder;
