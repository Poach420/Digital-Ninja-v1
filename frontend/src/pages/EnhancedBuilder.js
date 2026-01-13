import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import {
    Rocket, MessageCircle, History, Paintbrush, Upload, Save,
    Code2, Eye, Sparkles, Clock, CheckCircle2, AlertCircle, Loader2
} from 'lucide-react';
import { toast } from 'sonner';
import api, { BACKEND_URL } from '../utils/api';
import LivePreview from '../components/LivePreview';
import VisualEditor from '../components/VisualEditor';
import DashboardLayout from '../components/DashboardLayout';
import DeploymentConsole from '../components/DeploymentConsole';

/**
 * Enhanced Builder - All Replit/Emergent-level features
 * - Autonomous Agent (200+ min builds)
 * - Visual Editor (click-to-edit)
 * - Version Control (snapshots)
 * - Discussion Mode (plan without building)
 * - One-Click Deployment
 * - Auto Database Setup
 */
const EnhancedBuilder = () => {
    const navigate = useNavigate();
    const { projectId } = useParams();

    const [mode, setMode] = useState('build'); // build, discuss, edit, deploy
    const [prompt, setPrompt] = useState('');
    const [building, setBuilding] = useState(false);
    const [progress, setProgress] = useState([]);
    const [project, setProject] = useState(null);
    const [snapshots, setSnapshots] = useState([]);
    const [discussionHistory, setDiscussionHistory] = useState([]);
    const [activeTab, setActiveTab] = useState('preview');
    const [showDeploymentConsole, setShowDeploymentConsole] = useState(false);

    useEffect(() => {
        if (projectId) {
            loadProject();
            loadSnapshots();
        }
    }, [projectId]);

    const loadProject = async () => {
        try {
            const response = await api.get(`/projects/${projectId}`);
            setProject(response.data);
        } catch (error) {
            toast.error('Failed to load project');
        }
    };

    const loadSnapshots = async () => {
        try {
            const response = await api.get(`/projects/${projectId}/snapshots`);
            setSnapshots(response.data.snapshots || []);
        } catch (error) {
            console.error('Failed to load snapshots');
        }
    };

    const startAutonomousBuild = async () => {
        if (!prompt.trim()) {
            toast.error('Please describe what you want to build');
            return;
        }

        setBuilding(true);
        setProgress([]);

        try {
            const response = await fetch(`${BACKEND_URL}/api/projects/autonomous/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({
                    prompt,
                    tech_stack: {
                        frontend: 'React',
                        backend: 'FastAPI',
                        database: 'MongoDB'
                    }
                })
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));

                            setProgress(prev => [...prev, {
                                type: data.type,
                                message: data.message,
                                timestamp: data.timestamp || new Date().toISOString()
                            }]);

                            if (data.type === 'complete') {
                                setProject(data);
                                toast.success('Autonomous build complete!');

                                // Auto-create snapshot
                                await createSnapshot('Initial autonomous build');
                            } else if (data.type === 'error') {
                                toast.error(data.message);
                            }
                        } catch (e) {
                            // Skip invalid JSON
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Build error:', error);
            toast.error('Build failed: ' + error.message);
        } finally {
            setBuilding(false);
        }
    };

    const discussWithAI = async () => {
        if (!prompt.trim()) return;

        const userMessage = { role: 'user', content: prompt };
        setDiscussionHistory(prev => [...prev, userMessage]);
        setPrompt('');

        try {
            const response = await api.post('/discuss', {
                message: userMessage.content,
                project_id: projectId,
                history: discussionHistory
            });

            const aiMessage = { role: 'assistant', content: response.data.response };
            setDiscussionHistory(prev => [...prev, aiMessage]);
        } catch (error) {
            toast.error('Discussion failed');
        }
    };

    const createSnapshot = async (message) => {
        if (!projectId) return;

        try {
            const response = await api.post(`/projects/${projectId}/snapshots`, {
                message: message || 'Manual snapshot'
            });

            if (response.data.success) {
                toast.success('Snapshot created');
                loadSnapshots();
            }
        } catch (error) {
            toast.error('Failed to create snapshot');
        }
    };

    const restoreSnapshot = async (snapshotId) => {
        try {
            const response = await api.post(
                `/projects/${projectId}/snapshots/${snapshotId}/restore`
            );

            if (response.data.success) {
                toast.success('Project restored');
                loadProject();
            }
        } catch (error) {
            toast.error('Failed to restore snapshot');
        }
    };

    const openDeploymentConsole = () => {
        if (!projectId) {
            toast.error('Generate or select a project before deploying');
            return;
        }
        setShowDeploymentConsole(true);
    };

    const handleDeploymentComplete = (deploymentResult) => {
        toast.success(deploymentResult?.url ? `Deployed to ${deploymentResult.url}` : 'Deployment completed');
        setProject((prev) => (prev ? { ...prev, deployment: deploymentResult } : prev));
    };

    return (
        <DashboardLayout>
            <div className="min-h-screen bg-slate-900 text-white">
                <div className="max-w-[1800px] mx-auto p-6 space-y-6">

                    {/* Header */}
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold flex items-center gap-3">
                                <Sparkles className="h-8 w-8 text-orange-500" />
                                Digital Ninja - Replit-Level Builder
                            </h1>
                            <p className="text-slate-400 mt-1">
                                Autonomous agent • Self-testing • Visual editor • Snapshots
                            </p>
                        </div>

                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                onClick={() => navigate('/projects')}
                                className="border-slate-600 text-white"
                            >
                                My Projects
                            </Button>
                            {projectId && (
                                <>
                                    <Button
                                        variant="outline"
                                        onClick={() => createSnapshot()}
                                        className="border-slate-600 text-white"
                                    >
                                        <Save className="h-4 w-4 mr-2" />
                                        Save Snapshot
                                    </Button>
                                    <Button
                                        onClick={openDeploymentConsole}
                                        className="bg-green-600 hover:bg-green-700"
                                    >
                                        <Upload className="h-4 w-4 mr-2" />
                                        Deploy Now
                                    </Button>
                                </>
                            )}
                        </div>
                    </div>

                    {/* Mode Selector */}
                    <Card className="bg-slate-800 border-slate-700 p-4">
                        <div className="grid grid-cols-4 gap-3">
                            <Button
                                variant={mode === 'build' ? 'default' : 'outline'}
                                onClick={() => setMode('build')}
                                className={mode === 'build' ? 'bg-orange-500' : 'border-slate-600'}
                            >
                                <Rocket className="h-4 w-4 mr-2" />
                                Autonomous Build
                            </Button>
                            <Button
                                variant={mode === 'discuss' ? 'default' : 'outline'}
                                onClick={() => setMode('discuss')}
                                className={mode === 'discuss' ? 'bg-blue-500' : 'border-slate-600'}
                            >
                                <MessageCircle className="h-4 w-4 mr-2" />
                                Discussion Mode
                            </Button>
                            <Button
                                variant={mode === 'edit' ? 'default' : 'outline'}
                                onClick={() => setMode('edit')}
                                className={mode === 'edit' ? 'bg-purple-500' : 'border-slate-600'}
                                disabled={!project}
                            >
                                <Paintbrush className="h-4 w-4 mr-2" />
                                Visual Editor
                            </Button>
                            <Button
                                variant={mode === 'history' ? 'default' : 'outline'}
                                onClick={() => setMode('history')}
                                className={mode === 'history' ? 'bg-green-500' : 'border-slate-600'}
                                disabled={!projectId}
                            >
                                <History className="h-4 w-4 mr-2" />
                                Version History
                            </Button>
                        </div>
                    </Card>

                    {/* Main Content Area */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-300px)]">

                        {/* Left Panel - Input/Control */}
                        <Card className="bg-slate-800 border-slate-700 p-6 flex flex-col">
                            {mode === 'build' && (
                                <div className="flex flex-col h-full">
                                    <h2 className="text-xl font-semibold mb-4">Autonomous Agent</h2>
                                    <p className="text-slate-400 text-sm mb-4">
                                        Describe your app and the AI will build it with self-testing and auto-fixing.
                                        Runs for up to 200 minutes autonomously.
                                    </p>

                                    <textarea
                                        value={prompt}
                                        onChange={(e) => setPrompt(e.target.value)}
                                        placeholder="Example: Build a real-time chat app with user authentication, message history, and online status indicators. Make it look professional with dark mode."
                                        className="flex-1 bg-slate-900 text-white p-4 rounded-lg border border-slate-700 resize-none focus:outline-none focus:ring-2 focus:ring-orange-500"
                                        disabled={building}
                                    />

                                    <Button
                                        onClick={startAutonomousBuild}
                                        disabled={building}
                                        className="mt-4 bg-orange-500 hover:bg-orange-600 h-12 text-lg"
                                    >
                                        {building ? (
                                            <>
                                                <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                                                Building...
                                            </>
                                        ) : (
                                            <>
                                                <Rocket className="h-5 w-5 mr-2" />
                                                Start Autonomous Build
                                            </>
                                        )}
                                    </Button>

                                    {/* Progress Log */}
                                    {progress.length > 0 && (
                                        <div className="mt-4 bg-slate-900 rounded-lg p-4 flex-1 overflow-y-auto max-h-64">
                                            <h3 className="text-sm font-semibold mb-2 text-slate-300">Build Progress</h3>
                                            <div className="space-y-2">
                                                {progress.map((log, idx) => (
                                                    <div key={idx} className="text-sm flex items-start gap-2">
                                                        {log.type === 'success' && <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />}
                                                        {log.type === 'error' && <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />}
                                                        {log.type === 'info' && <Clock className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />}
                                                        <span className="text-slate-300">{log.message}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}

                            {mode === 'discuss' && (
                                <div className="flex flex-col h-full">
                                    <h2 className="text-xl font-semibold mb-4">Discussion Mode</h2>
                                    <p className="text-slate-400 text-sm mb-4">
                                        Plan and brainstorm without making changes. Free credit-efficient planning.
                                    </p>

                                    {/* Discussion History */}
                                    <div className="flex-1 bg-slate-900 rounded-lg p-4 overflow-y-auto mb-4">
                                        {discussionHistory.length === 0 ? (
                                            <div className="text-slate-500 text-center py-8">
                                                Start a discussion about your project
                                            </div>
                                        ) : (
                                            <div className="space-y-4">
                                                {discussionHistory.map((msg, idx) => (
                                                    <div key={idx} className={`${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                                                        <div className={`inline-block max-w-[80%] p-3 rounded-lg ${msg.role === 'user'
                                                            ? 'bg-orange-500 text-white'
                                                            : 'bg-slate-700 text-slate-100'
                                                            }`}>
                                                            {msg.content}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    <div className="flex gap-2">
                                        <input
                                            type="text"
                                            value={prompt}
                                            onChange={(e) => setPrompt(e.target.value)}
                                            onKeyPress={(e) => e.key === 'Enter' && discussWithAI()}
                                            placeholder="Ask about features, architecture, trade-offs..."
                                            className="flex-1 bg-slate-900 text-white px-4 py-3 rounded-lg border border-slate-700"
                                        />
                                        <Button onClick={discussWithAI} className="bg-blue-500 hover:bg-blue-600">
                                            <MessageCircle className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                            )}

                            {mode === 'history' && (
                                <div className="flex flex-col h-full">
                                    <h2 className="text-xl font-semibold mb-4">Version History</h2>
                                    <p className="text-slate-400 text-sm mb-4">
                                        Snapshots are created automatically. Restore to any previous version.
                                    </p>

                                    <div className="flex-1 overflow-y-auto space-y-2">
                                        {snapshots.length === 0 ? (
                                            <div className="text-slate-500 text-center py-8">
                                                No snapshots yet
                                            </div>
                                        ) : (
                                            snapshots.map((snapshot) => (
                                                <Card key={snapshot.snapshot_id} className="bg-slate-700 border-slate-600 p-4">
                                                    <div className="flex items-start justify-between">
                                                        <div className="flex-1">
                                                            <div className="font-medium">{snapshot.message}</div>
                                                            <div className="text-sm text-slate-400 mt-1">
                                                                {new Date(snapshot.created_at).toLocaleString()}
                                                            </div>
                                                            <div className="text-xs text-slate-500 mt-1">
                                                                {snapshot.file_count} files • {snapshot.auto_created ? 'Auto' : 'Manual'}
                                                            </div>
                                                        </div>
                                                        <Button
                                                            size="sm"
                                                            onClick={() => restoreSnapshot(snapshot.snapshot_id)}
                                                            variant="outline"
                                                            className="border-slate-500"
                                                        >
                                                            Restore
                                                        </Button>
                                                    </div>
                                                </Card>
                                            ))
                                        )}
                                    </div>
                                </div>
                            )}
                        </Card>

                        {/* Right Panel - Preview/Editor */}
                        <Card className="bg-slate-800 border-slate-700 overflow-hidden">
                            {!project ? (
                                <div className="h-full flex items-center justify-center text-slate-500">
                                    <div className="text-center">
                                        <Sparkles className="h-16 w-16 mx-auto mb-4 text-slate-600" />
                                        <p>Start building or select a project</p>
                                    </div>
                                </div>
                            ) : mode === 'edit' ? (
                                <VisualEditor
                                    files={project.files || []}
                                    onFilesUpdate={(updatedFiles) => {
                                        setProject({ ...project, files: updatedFiles });
                                    }}
                                />
                            ) : (
                                <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
                                    <TabsList className="bg-slate-700 border-b border-slate-600 w-full justify-start rounded-none">
                                        <TabsTrigger value="preview" className="flex items-center gap-2">
                                            <Eye className="h-4 w-4" />
                                            Preview
                                        </TabsTrigger>
                                        <TabsTrigger value="code" className="flex items-center gap-2">
                                            <Code2 className="h-4 w-4" />
                                            Code
                                        </TabsTrigger>
                                    </TabsList>

                                    <TabsContent value="preview" className="flex-1 m-0 data-[state=active]:flex">
                                        <LivePreview files={project.files || []} />
                                    </TabsContent>

                                    <TabsContent value="code" className="flex-1 m-0 p-4 overflow-y-auto">
                                        <div className="space-y-4">
                                            {(project.files || []).map((file, idx) => (
                                                <div key={idx} className="bg-slate-900 rounded-lg p-4">
                                                    <div className="text-sm font-mono text-orange-400 mb-2">{file.path}</div>
                                                    <pre className="text-xs text-slate-300 overflow-x-auto">
                                                        <code>{file.content}</code>
                                                    </pre>
                                                </div>
                                            ))}
                                        </div>
                                    </TabsContent>
                                </Tabs>
                            )}
                        </Card>
                    </div>
                </div>
                <DeploymentConsole
                    open={showDeploymentConsole}
                    onOpenChange={setShowDeploymentConsole}
                    projectId={projectId}
                    projectName={project?.name}
                    onComplete={handleDeploymentComplete}
                />
            </div>
        </DashboardLayout>
    );
};

export default EnhancedBuilder;
