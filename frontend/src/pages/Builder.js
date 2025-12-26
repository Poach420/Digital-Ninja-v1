import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import api from '../utils/api';
import { Sparkles, Loader2 } from 'lucide-react';

const Builder = () => {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState('');
  const [frontend, setFrontend] = useState('React');
  const [backend, setBackend] = useState('FastAPI');
  const [database, setDatabase] = useState('MongoDB');
  const [generating, setGenerating] = useState(false);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a project description');
      return;
    }

    setGenerating(true);
    try {
      const response = await api.post('/projects/generate', {
        prompt: prompt.trim(),
        tech_stack: {
          frontend,
          backend,
          database
        }
      });

      toast.success(`Project "${response.data.name}" generated successfully!`);
      navigate(`/project/${response.data.project_id}`);
    } catch (error) {
      console.error('Generation error:', error);
      toast.error(error.response?.data?.detail || 'Failed to generate project');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-6" data-testid="builder-page">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="w-10 h-10 text-purple-400" />
            <h1 className="text-5xl font-bold text-white">Base44 AI Builder</h1>
          </div>
          <p className="text-xl text-gray-300">
            Describe your app in natural language. Get production-ready code instantly.
          </p>
          <p className="text-sm text-gray-400 mt-2">
            Powered by GPT-4 • Deploy to Vercel & Render • Export to GitHub
          </p>
        </div>

        <Card className="bg-slate-800/50 backdrop-blur-lg border-slate-700 p-8 shadow-2xl">
          <div className="space-y-6">
            {/* Main Prompt Input */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-3">
                What do you want to build?
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Example: Build a live chat app with real-time messaging, user authentication, and message history. Include typing indicators and online status."
                className="w-full h-32 px-4 py-3 bg-slate-900/80 border border-slate-600 rounded-lg text-white placeholder-gray-500 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 resize-none"
                disabled={generating}
              />
              <p className="text-xs text-gray-500 mt-2">
                💡 Be specific about features, UI elements, and functionality
              </p>
            </div>

            {/* Tech Stack Selection */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Frontend</label>
                <Select value={frontend} onValueChange={setFrontend} disabled={generating}>
                  <SelectTrigger className="bg-slate-900/80 border-slate-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="React">React 18</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Backend</label>
                <Select value={backend} onValueChange={setBackend} disabled={generating}>
                  <SelectTrigger className="bg-slate-900/80 border-slate-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="FastAPI">FastAPI</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Database</label>
                <Select value={database} onValueChange={setDatabase} disabled={generating}>
                  <SelectTrigger className="bg-slate-900/80 border-slate-600 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MongoDB">MongoDB</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Generate Button */}
            <Button
              onClick={handleGenerate}
              disabled={generating || !prompt.trim()}
              className="w-full h-14 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold text-lg shadow-lg shadow-purple-500/50 disabled:opacity-50"
            >
              {generating ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Generating with GPT-4...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5 mr-2" />
                  Generate App Instantly
                </>
              )}
            </Button>

            {/* Features Grid */}
            <div className="grid grid-cols-2 gap-4 pt-6 border-t border-slate-700">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-purple-400">✓</span>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-white">Production Ready</h4>
                  <p className="text-xs text-gray-400">Deployment configs included</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-purple-400">✓</span>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-white">Live Preview</h4>
                  <p className="text-xs text-gray-400">See your app instantly</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-purple-400">✓</span>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-white">GitHub Export</h4>
                  <p className="text-xs text-gray-400">One-click code export</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-purple-400">✓</span>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-white">GPT-4 Powered</h4>
                  <p className="text-xs text-gray-400">Advanced reasoning</p>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Quick Examples */}
        <div className="mt-8">
          <h3 className="text-lg font-semibold text-white mb-4">Try these examples:</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[
              "Build a task management app with drag-and-drop, categories, and due dates",
              "Create a weather dashboard with real-time data and 7-day forecast",
              "Build a markdown editor with live preview and file export",
              "Create an e-commerce product catalog with filters and shopping cart"
            ].map((example, idx) => (
              <button
                key={idx}
                onClick={() => setPrompt(example)}
                className="text-left p-4 bg-slate-800/30 hover:bg-slate-800/50 border border-slate-700 hover:border-purple-500/50 rounded-lg transition-all text-sm text-gray-300 hover:text-white"
                disabled={generating}
              >
                💡 {example}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Builder;