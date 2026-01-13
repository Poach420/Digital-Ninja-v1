import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Textarea } from '../components/ui/textarea';
import { Switch } from '../components/ui/switch';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';
import { Separator } from '../components/ui/separator';
import { ToggleGroup, ToggleGroupItem } from '../components/ui/toggle-group';
import { toast } from 'sonner';
import api from '../utils/api';
import { Sparkles, Loader2, Zap, History, ExternalLink } from 'lucide-react';
import GenerationLogger from '../components/GenerationLogger';
import BrandLogo from '../components/BrandLogo';
import { isDevAuthEnabled } from '../utils/devAuth';
import { BACKEND_URL } from '../utils/api';

const APP_TYPES = [
  {
    value: 'saas-dashboard',
    label: 'SaaS Dashboard',
    description: 'Multi-tenant analytics dashboards with metrics, teams, billing, and alerts.',
  },
  {
    value: 'marketing-site',
    label: 'Marketing Site',
    description: 'High-conversion marketing site with hero, product sections, testimonials, and CTAs.',
  },
  {
    value: 'ecommerce',
    label: 'E-commerce',
    description: 'Storefront with catalog, product detail pages, carts, and checkout integrations.',
  },
  {
    value: 'internal-tools',
    label: 'Internal Tools',
    description: 'Operations console with CRUD workflows, permissions, and data grids.',
  },
  {
    value: 'community-platform',
    label: 'Community Platform',
    description: 'Membership portal with profiles, discussions, events, and notifications.',
  },
];

const INTEGRATIONS = [
  {
    id: 'auth',
    label: 'Auth & Roles',
    prompt: 'Implement secure authentication with email magic links, optional OAuth, and role-based access control for admins and contributors.',
  },
  {
    id: 'payments',
    label: 'Payments',
    prompt: 'Add Stripe billing with subscription plans, usage-based metering, invoices, and upgrade flows surfaced in the dashboard.',
  },
  {
    id: 'analytics',
    label: 'Analytics',
    prompt: 'Instrument product analytics with charts, KPIs, and trend analysis backed by a mocked data layer.',
  },
  {
    id: 'ai-assistant',
    label: 'AI Assistant',
    prompt: 'Embed an AI assistant sidebar that can answer domain questions and execute quick automations tied to the project context.',
  },
  {
    id: 'notifications',
    label: 'Notifications',
    prompt: 'Include real-time notifications and email digests that summarize key changes and alerts for the team.',
  },
  {
    id: 'deployment',
    label: 'Deployment',
    prompt: 'Provision deployment configs for Vercel and Render, including health checks, observability hooks, and environment management.',
  },
];

const CHAT_MODES = [
  {
    value: 'plan',
    label: 'Plan',
    description: 'Break down next steps and feature recommendations.',
  },
  {
    value: 'build',
    label: 'Apply',
    description: 'Apply code updates directly to the active project.',
  },
  {
    value: 'general',
    label: 'General',
    description: 'Open Q&A not tied to a specific project.',
  },
];

const Builder = () => {
  const navigate = useNavigate();
  const [activePromptTab, setActivePromptTab] = useState('app');
  const [promptDrafts, setPromptDrafts] = useState({ app: '', design: '' });
  const [appType, setAppType] = useState(APP_TYPES[0].value);
  const [fastMode, setFastMode] = useState(false);
  const [selectedIntegrations, setSelectedIntegrations] = useState([]);
  const [chatSessions, setChatSessions] = useState({});
  const [generating, setGenerating] = useState(false);
  const [chatting, setChatting] = useState(false);
  const [showLogger, setShowLogger] = useState(false);
  const [currentProjectId, setCurrentProjectId] = useState(null);
  const [activeProject, setActiveProject] = useState(null);
  const [recentProjects, setRecentProjects] = useState([]);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loadingProjectDetails, setLoadingProjectDetails] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatMode, setChatMode] = useState('plan');

  const appTypeMap = useMemo(() => Object.fromEntries(APP_TYPES.map((type) => [type.value, type])), []);
  const integrationMap = useMemo(() => Object.fromEntries(INTEGRATIONS.map((item) => [item.id, item])), []);
  const effectiveChatMode = (!activeProject && chatMode !== 'general') ? 'general' : chatMode;
  const activeChatKey = effectiveChatMode === 'general' ? 'general' : (activeProject?.project_id || 'general');
  const chatHistory = chatSessions[activeChatKey] || [];
  const activeModeMeta = useMemo(() => CHAT_MODES.find(mode => mode.value === effectiveChatMode) || CHAT_MODES[0], [effectiveChatMode]);
  const chatPlaceholder = useMemo(() => {
    if (effectiveChatMode === 'general') {
      return 'Ask the copilot anything about building apps, debugging, or using Digital Ninja.';
    }
    if (effectiveChatMode === 'plan') {
      return 'Request a roadmap, feature breakdown, or improvement ideas for the active project.';
    }
    return 'Describe the change you want applied to the codebase (e.g., add pricing page, theme update, API integration).';
  }, [effectiveChatMode, activeProject]);
  const lastUpdatedLabel = useMemo(() => {
    if (!activeProject) return '';
    const timestamp = activeProject.updated_at || activeProject.created_at;
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return Number.isNaN(date.getTime()) ? '' : date.toLocaleString();
  }, [activeProject]);

  useEffect(() => {
    let isMounted = true;

    const loadRecentProjects = async () => {
      try {
        const response = await api.get('/projects');
        if (!isMounted) return;
        const sorted = [...response.data].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        setRecentProjects(sorted.slice(0, 6));
      } catch (error) {
        console.error('Failed to load recent projects:', error);
        if (isDevAuthEnabled()) {
          const cache = JSON.parse(localStorage.getItem('dev_projects') || '{}');
          const demoProjects = Object.values(cache);
          setRecentProjects(demoProjects.slice(0, 3));
        } else {
          toast.error('Unable to load recent projects');
        }
      } finally {
        if (isMounted) {
          setLoadingProjects(false);
        }
      }
    };

    loadRecentProjects();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!activeProject && chatMode !== 'general') {
      setChatMode('general');
    }
  }, [activeProject, chatMode]);

  const handlePromptChange = (tabKey, value) => {
    setPromptDrafts((prev) => ({ ...prev, [tabKey]: value }));
  };

  const toggleIntegration = (id) => {
    setSelectedIntegrations((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]));
  };

  const handleProjectSelect = async (projectId) => {
    setLoadingProjectDetails(true);
    try {
      const response = await api.get(`/projects/${projectId}`);
      setActiveProject(response.data);
      setCurrentProjectId(projectId);
      setChatSessions(prev => ({
        ...prev,
        [projectId]: prev[projectId] || []
      }));
      setChatMode('plan');
      toast.success(`Loaded ${response.data.name}`);
    } catch (error) {
      console.error('Failed to load project details:', error);
      if (isDevAuthEnabled()) {
        const cache = JSON.parse(localStorage.getItem('dev_projects') || '{}');
        if (cache[projectId]) {
          setActiveProject(cache[projectId]);
          setCurrentProjectId(projectId);
          setChatSessions(prev => ({
            ...prev,
            [projectId]: prev[projectId] || []
          }));
          setChatMode('plan');
          toast.success(`Loaded ${cache[projectId].name}`);
          setLoadingProjectDetails(false);
          return;
        }
      }
      toast.error('Unable to open project context');
    } finally {
      setLoadingProjectDetails(false);
    }
  };

  const handleBuild = async () => {
    const appBrief = promptDrafts.app.trim();
    const designBrief = promptDrafts.design.trim();

    if (!appBrief) {
      toast.error('Add an app brief before generating.');
      return;
    }

    setGenerating(true);
    setShowLogger(true);
    try {
      const appTypeInfo = appTypeMap[appType];
      const integrationSection = selectedIntegrations.length
        ? selectedIntegrations
          .map((id) => `- ${integrationMap[id]?.prompt}`)
          .filter(Boolean)
          .join('\n')
        : '';

      const compositePrompt = [
        `You are Digital Ninja's autonomous app builder. Build a production-ready ${appTypeInfo?.label || 'application'}.`,
        appTypeInfo?.description ? `### Project Type Focus\n${appTypeInfo.description}` : null,
        `### Product Requirements\n${appBrief}`,
        designBrief ? `### Visual & UX Direction\n${designBrief}` : null,
        integrationSection ? `### Integrations & Capabilities\n${integrationSection}` : null,
        `### Generation Mode\n${fastMode ? 'FAST_MODE: Deliver a lean multi-page MVP optimized for rapid iteration. Prefer fewer dependencies, lightweight styling, and essential flows.' : 'DEEP_MODE: Deliver a comprehensive multi-page experience with rich content, reusable components, documentation, tests, and deployment configuration.'}`,
      ]
        .filter(Boolean)
        .join('\n\n');

      const response = await api.post('/projects/generate', {
        prompt: compositePrompt,
        tech_stack: {
          frontend: 'React',
          backend: 'FastAPI',
          database: 'MongoDB'
        }
      });

      const projectPayload = response.data;
      setCurrentProjectId(projectPayload.project_id);
      setActiveProject(projectPayload);
      setChatSessions(prev => ({
        ...prev,
        [projectPayload.project_id]: prev[projectPayload.project_id] || []
      }));
      setRecentProjects(prev => {
        const filtered = prev.filter(proj => proj.project_id !== projectPayload.project_id);
        return [projectPayload, ...filtered].slice(0, 6);
      });
      setChatMode('plan');
      toast.success(`Project "${projectPayload.name}" generated successfully!`);
      // Logger will handle navigation after completion
    } catch (error) {
      console.error('Generation error:', error);
      if (isDevAuthEnabled()) {
        const localId = `dev_${Date.now().toString(36)}`;
        const wantsCalculator = /\b(calc|calculator|arithmetic|add|subtract|multiply|divide)\b/i.test(promptDrafts.app.trim());
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
        setActiveProject(demoProject);
        setChatSessions(prev => ({
          ...prev,
          [localId]: prev[localId] || []
        }));
        setRecentProjects(prev => [{ ...demoProject }, ...prev.filter(p => p.project_id !== localId)].slice(0, 6));
        setChatMode('plan');
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
    if (!chatInput.trim()) {
      toast.error('Please enter a message');
      return;
    }

    const userMessage = chatInput.trim();
    const targetProjectId = activeProject?.project_id;
    const effectiveMode = !targetProjectId ? 'general' : chatMode;
    const chatKey = effectiveMode === 'general' ? 'general' : targetProjectId;

    if (effectiveMode !== 'general' && !targetProjectId) {
      toast.error('Generate or select a project to link the copilot conversation.');
      return;
    }

    const priorHistory = (chatSessions[chatKey] || []).map(({ role, content }) => ({ role, content }));
    const userEntryKey = Date.now() + Math.random();
    setChatSessions(prev => {
      const history = prev[chatKey] || [];
      return { ...prev, [chatKey]: [...history, { role: 'user', content: userMessage, _k: userEntryKey }] };
    });
    setChatInput('');
    setChatting(true);

    const assistantKey = Date.now() + Math.random();
    setChatSessions(prev => {
      const history = prev[chatKey] || [];
      return { ...prev, [chatKey]: [...history, { role: 'assistant', content: '', _k: assistantKey }] };
    });

    try {
      if (effectiveMode === 'general') {
        const token = localStorage.getItem('token');
        const res = await fetch(`${BACKEND_URL}/api/chat/message`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {})
          },
          body: JSON.stringify({ message: userMessage, history: priorHistory })
        });

        const reader = res.body?.getReader();
        const decoder = new TextDecoder();
        let assistantMessage = '';

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
                  setChatSessions(prev => {
                    const history = prev[chatKey] || [];
                    return {
                      ...prev,
                      [chatKey]: history.map(entry => (entry._k === assistantKey ? { ...entry, content: assistantMessage } : entry))
                    };
                  });
                }
              }
            }
          }
        } else {
          const json = await res.json().catch(() => null);
          const content = (json && json.message) ? `Echo: ${json.message}` : 'Response received.';
          setChatSessions(prev => {
            const history = prev[chatKey] || [];
            return {
              ...prev,
              [chatKey]: history.map(entry => (entry._k === assistantKey ? { ...entry, content } : entry))
            };
          });
        }
      } else {
        const endpointSuffix = effectiveMode === 'plan' ? 'plan' : 'build';
        const { data } = await api.post(`/projects/${targetProjectId}/chat/${endpointSuffix}`, {
          message: userMessage,
          history: priorHistory
        });

        let reply = data.response || '';
        if (effectiveMode === 'build' && Array.isArray(data.file_updates) && data.file_updates.length) {
          const fileList = data.file_updates.map(update => `• ${update.path}`).join('\n');
          reply = `${reply}\n\nUpdated files:\n${fileList}`;
          setActiveProject(prev => {
            if (!prev || prev.project_id !== targetProjectId) return prev;
            const existingFiles = Array.isArray(prev.files) ? [...prev.files] : [];
            data.file_updates.forEach(update => {
              const idx = existingFiles.findIndex(f => f.path === update.path);
              if (idx >= 0) {
                existingFiles[idx] = { ...existingFiles[idx], content: update.content };
              } else {
                existingFiles.push({ path: update.path, content: update.content, language: 'js' });
              }
            });
            return { ...prev, files: existingFiles, updated_at: new Date().toISOString() };
          });
        }

        setChatSessions(prev => {
          const history = prev[chatKey] || [];
          return {
            ...prev,
            [chatKey]: history.map(entry => (entry._k === assistantKey ? { ...entry, content: reply } : entry))
          };
        });
      }
    } catch (error) {
      console.error('Chat error:', error);
      const fallbackMessage = isDevAuthEnabled()
        ? 'Dev reply: your request was processed locally.'
        : 'Sorry, I encountered an error. Please try again.';
      if (!isDevAuthEnabled()) {
        toast.error('Failed to get response');
      }
      setChatSessions(prev => {
        const history = prev[chatKey] || [];
        const hasPlaceholder = history.some(entry => entry._k === assistantKey);
        if (hasPlaceholder) {
          return {
            ...prev,
            [chatKey]: history.map(entry => (entry._k === assistantKey ? { ...entry, content: fallbackMessage } : entry))
          };
        }
        return {
          ...prev,
          [chatKey]: [...history, { role: 'assistant', content: fallbackMessage, _k: Date.now() + Math.random() }]
        };
      });
    } finally {
      setChatting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0d16] p-6" data-testid="builder-page">
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="flex flex-col items-center text-center gap-4">
          <div className="flex items-center gap-3">
            <BrandLogo className="w-16 h-16 rounded-lg shadow-lg" />
            <div className="w-14 h-14 bg-gradient-to-br from-[#9b00e8] to-[#ff4500] rounded-2xl flex items-center justify-center shadow-lg shadow-[#9b00e8]/50 animate-pulse-slow">
              <Sparkles className="w-8 h-8 text-white" strokeWidth={2.5} />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-[#9b00e8] via-[#ff4500] to-[#9b00e8] bg-clip-text text-transparent animate-gradient">
              Digital Ninja Builder
            </h1>
          </div>
          <p className="text-lg text-gray-300 font-medium max-w-3xl">
            Multi-tab prompting, instant deployment, and Replit-grade iteration in one workspace. Describe what you need—we handle the build.
          </p>
          <div className="flex items-center gap-3 text-sm text-gray-400">
            <span className="inline-flex items-center gap-1">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              Powered by GPT-4
            </span>
            <span className="text-gray-600">•</span>
            <span>Vercel | Render | GitHub Deployments</span>
            <span className="text-gray-600">•</span>
            <span>Project context stays live across chat + builds</span>
          </div>
        </div>

        <div className="grid gap-6 xl:grid-cols-[2fr_minmax(320px,1fr)]">
          <div className="space-y-6">
            <Card className="bg-[#15182a]/80 border-[#1f2339] shadow-2xl shadow-black/40 p-6">
              <div className="flex flex-col gap-6">
                <div className="flex flex-wrap items-center justify-between gap-6">
                  <div className="w-full sm:w-1/2">
                    <Label htmlFor="app-type" className="text-gray-300 mb-2 block">App type</Label>
                    <Select value={appType} onValueChange={setAppType}>
                      <SelectTrigger id="app-type" className="bg-[#0f121f] border-[#242a3f] text-gray-100">
                        <SelectValue placeholder="Choose a project type" />
                      </SelectTrigger>
                      <SelectContent className="bg-[#0f121f] border-[#242a3f] text-gray-100">
                        {APP_TYPES.map((type) => (
                          <SelectItem key={type.value} value={type.value} className="focus:bg-[#1a2035] focus:text-white">
                            <div>
                              <p className="font-semibold text-sm">{type.label}</p>
                              <p className="text-xs text-gray-400">{type.description}</p>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center gap-3 bg-[#0f121f] border border-[#242a3f] rounded-xl px-4 py-3">
                    <Switch id="fast-mode" checked={fastMode} onCheckedChange={setFastMode} />
                    <div className="text-left">
                      <Label htmlFor="fast-mode" className="text-gray-200 cursor-pointer">Fast mode</Label>
                      <p className="text-xs text-gray-500">
                        {fastMode ? 'Lean MVP generation for rapid iteration.' : 'Full build with docs, tests, and multi-page flows.'}
                      </p>
                    </div>
                    <Zap className={`w-5 h-5 ${fastMode ? 'text-[#ff7a45]' : 'text-gray-600'}`} />
                  </div>
                </div>

                <Tabs value={activePromptTab} onValueChange={setActivePromptTab} className="w-full">
                  <TabsList className="bg-[#0f121f] border border-[#242a3f] text-gray-400">
                    <TabsTrigger value="app" className="data-[state=active]:bg-[#1a2035] data-[state=active]:text-white">App Brief</TabsTrigger>
                    <TabsTrigger value="design" className="data-[state=active]:bg-[#1a2035] data-[state=active]:text-white">Design Brief</TabsTrigger>
                  </TabsList>
                  <TabsContent value="app" className="mt-4">
                    <Textarea
                      value={promptDrafts.app}
                      onChange={(e) => handlePromptChange('app', e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && e.ctrlKey) {
                          e.preventDefault();
                          handleBuild();
                        }
                      }}
                      placeholder="Outline user goals, workflows, and domain context. Example: Build a multi-tenant analytics dashboard for a robotics startup with device monitoring, alert routing, maintenance scheduling, and API integrations."
                      className="min-h-[200px] bg-[#0f121f] border-[#242a3f] text-gray-100 placeholder:text-gray-500 focus-visible:ring-[#ff4500]/60"
                      disabled={generating}
                    />
                    <p className="text-xs text-gray-500 mt-2">Press Ctrl+Enter to generate immediately.</p>
                  </TabsContent>
                  <TabsContent value="design" className="mt-4">
                    <Textarea
                      value={promptDrafts.design}
                      onChange={(e) => handlePromptChange('design', e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && e.ctrlKey) {
                          e.preventDefault();
                          handleBuild();
                        }
                      }}
                      placeholder="Describe brand tones, layout expectations, and UX patterns. Example: Neon cyberpunk theme, dark background, glowing gradients, responsive nav with glassmorphism, consistent iconography."
                      className="min-h-[160px] bg-[#0f121f] border-[#242a3f] text-gray-100 placeholder:text-gray-500 focus-visible:ring-[#ff4500]/60"
                      disabled={generating}
                    />
                  </TabsContent>
                </Tabs>

                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm text-gray-300">
                    <span>Integration shortcuts</span>
                    <span className="text-xs text-gray-500">Append capabilities without rewriting your prompt.</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {INTEGRATIONS.map((integration) => {
                      const active = selectedIntegrations.includes(integration.id);
                      return (
                        <Button
                          key={integration.id}
                          type="button"
                          variant={active ? 'default' : 'outline'}
                          onClick={() => toggleIntegration(integration.id)}
                          className={`${active ? 'bg-gradient-to-r from-[#9b00e8] to-[#ff4500] text-white border-none' : 'bg-[#0f121f] border-[#242a3f] text-gray-300 hover:bg-[#1a2035] hover:text-white'} rounded-full h-10 px-4 text-sm`}>
                          {integration.label}
                        </Button>
                      );
                    })}
                  </div>
                </div>

                <Button
                  onClick={handleBuild}
                  disabled={generating || !promptDrafts.app.trim()}
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
            </Card>

            <Card className="bg-[#121629] border-[#1f2339] p-6 text-sm text-gray-400">
              <h3 className="text-lg font-semibold text-white mb-3">Prompt crafting tips</h3>
              <ul className="list-disc ml-5 space-y-2">
                <li>Call out audiences, success metrics, and key data sources to anchor GPT output.</li>
                <li>List critical pages, onboarding states, and fallback flows—Digital Ninja will scaffold each route.</li>
                <li>Pair functional requests in the App tab with tone and layout guidance in the Design tab for richer UI.</li>
              </ul>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="bg-[#15182a]/90 border-[#1f2339] p-6 h-full">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold text-white">Project Copilot Chat</h3>
                  <p className="text-xs text-gray-500">
                    {activeProject ? `Linked to ${activeProject.name}` : 'Select or generate a project to unlock plan & build automation.'}
                  </p>
                </div>
                <Badge variant="outline" className="border-[#2a3150] text-gray-300">GPT-4</Badge>
              </div>

              <div className="mt-4 flex flex-col gap-3">
                <ToggleGroup
                  type="single"
                  value={chatMode}
                  onValueChange={(value) => value && setChatMode(value)}
                  className="justify-start flex-wrap gap-2"
                >
                  {CHAT_MODES.map((mode) => (
                    <ToggleGroupItem
                      key={mode.value}
                      value={mode.value}
                      disabled={!activeProject && mode.value !== 'general'}
                      className={`px-4 py-2 border border-[#242a3f] text-gray-300 data-[state=on]:bg-gradient-to-r data-[state=on]:from-[#9b00e8] data-[state=on]:to-[#ff4500] data-[state=on]:text-white data-[state=on]:border-transparent ${(!activeProject && mode.value !== 'general') ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      {mode.label}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
                <p className="text-xs text-gray-500">{activeModeMeta.description}</p>
              </div>

              {activeProject ? (
                <div className="mt-4 bg-[#0f121f] border border-[#242a3f] rounded-lg p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-xs text-gray-500">Active project</p>
                      <p className="text-sm font-semibold text-white">{activeProject.name}</p>
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => navigate(`/editor/${activeProject.project_id}`)}
                      className="border-[#2a3150] text-gray-200 hover:bg-[#1a2035]"
                    >
                      Open editor
                    </Button>
                  </div>
                  <p className="text-xs text-gray-500 mt-2 line-clamp-2">{activeProject.description || 'Generated by Digital Ninja.'}</p>
                  <div className="mt-2 flex items-center gap-3 text-[11px] text-gray-600">
                    <span>{activeProject.files?.length || 0} files</span>
                    <span>•</span>
                    <span>{lastUpdatedLabel ? `Updated ${lastUpdatedLabel}` : 'Fresh build'}</span>
                  </div>
                  {loadingProjectDetails && (
                    <div className="mt-2 flex items-center gap-2 text-xs text-[#ff7a45]">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Refreshing project context…</span>
                    </div>
                  )}
                </div>
              ) : (
                <div className="mt-4 bg-[#0f121f] border border-dashed border-[#242a3f] rounded-lg p-4 text-xs text-gray-500">
                  Generate a project or choose one from the recent builds list to enable contextual planning and live edits.
                </div>
              )}

              <Separator className="my-4 bg-[#1f2339]" />

              <ScrollArea className="h-72 rounded-lg border border-[#1f2339] bg-[#0f121f] p-4">
                {chatHistory.length === 0 ? (
                  <div className="text-center text-gray-500 mt-10">
                    <p className="text-base">{effectiveChatMode === 'general' ? 'Chat stays open between builds.' : 'Kick off your project plan or request a live code change.'}</p>
                    <p className="text-sm mt-2">{effectiveChatMode === 'general' ? 'Ask about tooling, deployment, or best practices.' : 'Describe the feature or adjustment you want and the copilot will respond in place.'}</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {chatHistory.map((msg) => (
                      <div
                        key={msg._k}
                        className={`p-4 rounded-xl ${msg.role === 'user' ? 'bg-gradient-to-r from-[#9b00e8] to-[#ff4500] text-white ml-8' : 'bg-[#181d33] border border-[#242a3f] text-gray-100 mr-8'}`}
                      >
                        <p className="text-xs font-semibold mb-1 opacity-80">
                          {msg.role === 'user' ? 'You' : 'Digital Ninja Copilot'}
                        </p>
                        <p className="whitespace-pre-wrap leading-relaxed text-sm">{msg.content}</p>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>

              <div className="mt-4 flex flex-col gap-3">
                <Textarea
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleChat();
                    }
                  }}
                  placeholder={chatPlaceholder}
                  className="bg-[#0f121f] border-[#242a3f] text-gray-100 placeholder:text-gray-500 min-h-[80px]"
                  disabled={chatting}
                />
                <div className="flex justify-between items-center text-xs text-gray-500">
                  <span>Press Enter to send • Shift+Enter for newline</span>
                  <Button
                    onClick={handleChat}
                    disabled={chatting || !chatInput.trim() || (effectiveChatMode !== 'general' && !activeProject)}
                    className="bg-gradient-to-r from-[#9b00e8] to-[#ff4500] hover:from-[#8800d4] hover:to-[#e63e00] text-white disabled:opacity-50 h-10 px-5"
                  >
                    {chatting ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Send'}
                  </Button>
                </div>
              </div>
            </Card>

            <Card className="bg-[#15182a]/60 border-[#1f2339] p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-white">Recent builds</h3>
                  <p className="text-xs text-gray-500">Reopen a project to iterate without restarting.</p>
                </div>
                <History className="w-5 h-5 text-gray-500" />
              </div>
              <div className="space-y-3">
                {loadingProjects ? (
                  <p className="text-sm text-gray-500">Loading project history...</p>
                ) : recentProjects.length === 0 ? (
                  <p className="text-sm text-gray-500">No recent builds yet. Generate your first project to populate this list.</p>
                ) : (
                  recentProjects.map((project) => {
                    const isActive = activeProject?.project_id === project.project_id;
                    return (
                      <button
                        key={project.project_id}
                        onClick={() => handleProjectSelect(project.project_id)}
                        disabled={loadingProjectDetails && activeProject?.project_id === project.project_id}
                        className={`w-full text-left bg-[#0f121f] border border-[#242a3f] transition-all rounded-lg px-4 py-3 text-gray-200 hover:border-[#ff4500] ${isActive ? 'border-[#ff4500] shadow-lg shadow-[#ff4500]/20' : ''} ${(loadingProjectDetails && activeProject?.project_id === project.project_id) ? 'opacity-60 cursor-progress' : ''}`}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-semibold text-sm text-white">{project.name}</p>
                            <p className="text-xs text-gray-500 line-clamp-2">{project.description || 'Generated by Digital Ninja'}</p>
                          </div>
                          <ExternalLink className="w-4 h-4 text-[#ff7a45]" />
                        </div>
                        <div className="mt-2 flex items-center gap-3 text-[11px] text-gray-500">
                          <span>{new Date(project.created_at).toLocaleDateString()}</span>
                          <span>•</span>
                          <span>{project.files?.length || 0} files</span>
                        </div>
                      </button>
                    );
                  })
                )}
              </div>
            </Card>
          </div>
        </div>
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