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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6" data-testid="builder-page">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="h-12 w-12 text-indigo-400" />
            <h1 className="text-5xl font-heading font-bold text-white">AI Application Builder</h1>
          </div>
          <p className="text-xl text-slate-300">Describe your app, and AI will generate the complete code</p>
        </div>

        <Card className="p-8 bg-slate-800/50 border-slate-700">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-3">What do you want to build?</label>
              <Input
                placeholder="e.g., A todo app with user authentication and real-time updates"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="text-lg h-14 bg-slate-900 border-slate-700 text-white placeholder:text-slate-500"
                disabled={generating}
                data-testid="prompt-input"
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Frontend</label>
                <Select value={frontend} onValueChange={setFrontend} disabled={generating}>
                  <SelectTrigger className="bg-slate-900 border-slate-700 text-white" data-testid="frontend-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="React">React</SelectItem>
                    <SelectItem value="Vue">Vue</SelectItem>
                    <SelectItem value="Next.js">Next.js</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Backend</label>
                <Select value={backend} onValueChange={setBackend} disabled={generating}>
                  <SelectTrigger className="bg-slate-900 border-slate-700 text-white" data-testid="backend-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="FastAPI">FastAPI</SelectItem>
                    <SelectItem value="Express">Express</SelectItem>
                    <SelectItem value="Django">Django</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Database</label>
                <Select value={database} onValueChange={setDatabase} disabled={generating}>
                  <SelectTrigger className="bg-slate-900 border-slate-700 text-white" data-testid="database-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MongoDB">MongoDB</SelectItem>
                    <SelectItem value="PostgreSQL">PostgreSQL</SelectItem>
                    <SelectItem value="MySQL">MySQL</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <Button
              onClick={handleGenerate}
              disabled={generating || !prompt.trim()}
              className="w-full h-14 text-lg bg-indigo-600 hover:bg-indigo-700"
              data-testid="generate-button"
            >
              {generating ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Generating Your App...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-5 w-5" />
                  Generate Application
                </>
              )}
            </Button>
          </div>
        </Card>

        <div className="mt-8 text-center text-slate-400 text-sm">
          <p>AI will generate a complete, production-ready application with all necessary files</p>
        </div>
      </div>
    </div>
  );
};

export default Builder;