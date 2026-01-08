import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Eye, Hammer, ClipboardList, ExternalLink, Code2, Download, Github } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import ProjectSelect from '../components/ProjectSelect';
import ProjectChat from '../components/ProjectChat';
import LivePreview from '../components/LivePreview';
import Editor from '@monaco-editor/react';
import GitHubPushDialog from '../components/GitHubPushDialog';

const AiBuilder = () => {
  const navigate = useNavigate();
  const [projectId, setProjectId] = useState('');
  const [project, setProject] = useState(null);
  const [loadingProject, setLoadingProject] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const pid = params.get('projectId');
    if (pid) setProjectId(pid);
  }, []);

  useEffect(() => {
    if (projectId) {
      loadProject(projectId);
    } else {
      setProject(null);
      setSelectedFile(null);
    }
  }, [projectId]);

  const loadProject = async (id) => {
    setLoadingProject(true);
    try {
      const res = await api.get(`/projects/${id}`);
      setProject(res.data);
      if (res.data.files.length > 0) setSelectedFile(res.data.files[0]);
    } catch (e) {
      toast.error('Failed to load project');
      setProject(null);
      setSelectedFile(null);
    } finally {
      setLoadingProject(false);
    }
  };

  const handleOpenEditor = () => {
    if (!projectId) {
      toast.error('Select a project first');
      return;
    }
    navigate(`/editor/${projectId}`);
  };

  const handleFileUpdatesApplied = (updates) => {
    if (!project) return;
    const updatedFiles = [...project.files];
    updates.forEach(u => {
      const idx = updatedFiles.findIndex(f => f.path === u.path);
      if (idx >= 0) {
        updatedFiles[idx] = { ...updatedFiles[idx], content: u.content };
      } else {
        updatedFiles.push({ path: u.path, content: u.content, language: u.path.split('.').pop() });
      }
    });
    setProject(prev => ({ ...prev, files: updatedFiles }));
  };

  const exportProject = async () => {
    if (!projectId) return toast.error('Select a project first');
    try {
      const response = await api.post(`/projects/${projectId}/export`);
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${response.data.name}-export.json`;
      a.click();
      toast.success('Project exported');
    } catch (error) {
      toast.error('Export failed');
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white p-4" data-testid="ai-builder">
      <div className="max-w-7xl mx-auto space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <ProjectSelect
            value={projectId}
            onChange={setProjectId}
            onNewProject={() => navigate('/builder')}
          />
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={handleOpenEditor} className="text-white border-slate-600">
              <ExternalLink className="h-4 w-4 mr-2" />
              Open Editor
            </Button>
          </div>
        </div>

        <Card className="bg-slate-800/50 border-slate-700 p-4">
          <Tabs defaultValue="preview" className="w-full">
            <TabsList className="grid grid-cols-4 w-full bg-slate-800 border border-slate-700">
              <TabsTrigger value="preview" className="data-[state=active]:bg-slate-700">
                <Eye className="h-4 w-4 mr-2" />
                Preview
              </TabsTrigger>
              <TabsTrigger value="plan" className="data-[state=active]:bg-slate-700">
                <ClipboardList className="h-4 w-4 mr-2" />
                Chat / Plan
              </TabsTrigger>
              <TabsTrigger value="build" className="data-[state=active]:bg-slate-700">
                <Hammer className="h-4 w-4 mr-2" />
                Chat / Build
              </TabsTrigger>
              <TabsTrigger value="code" className="data-[state=active]:bg-slate-700">
                <Code2 className="h-4 w-4 mr-2" />
                Code
              </TabsTrigger>
            </TabsList>

            <TabsContent value="preview" className="mt-4">
              {!projectId ? (
                <div className="text-slate-300 text-center py-16">Select a project to preview</div>
              ) : loadingProject ? (
                <div className="text-slate-300 text-center py-16">Loading project...</div>
              ) : !project ? (
                <div className="text-slate-300 text-center py-16">Project not found</div>
              ) : (
                <div className="h-[70vh] bg-white rounded">
                  <LivePreview files={project.files} />
                </div>
              )}
            </TabsContent>

            <TabsContent value="plan" className="mt-4">
              {!projectId ? (
                <div className="text-slate-300 text-center py-16">Select a project to start planning</div>
              ) : (
                <div className="h-[70vh]">
                  <ProjectChat
                    projectId={projectId}
                    mode="plan"
                  />
                </div>
              )}
            </TabsContent>

            <TabsContent value="build" className="mt-4">
              {!projectId ? (
                <div className="text-slate-300 text-center py-16">Select a project to start building</div>
              ) : (
                <div className="h-[70vh]">
                  <ProjectChat
                    projectId={projectId}
                    mode="build"
                    onFileUpdates={handleFileUpdatesApplied}
                  />
                </div>
              )}
            </TabsContent>

            <TabsContent value="code" className="mt-4">
              {!projectId ? (
                <div className="text-slate-300 text-center py-16">Select a project to view code</div>
              ) : loadingProject ? (
                <div className="text-slate-300 text-center py-16">Loading project...</div>
              ) : !project ? (
                <div className="text-slate-300 text-center py-16">Project not found</div>
              ) : (
                <div className="grid grid-cols-[260px_1fr] gap-4 h-[70vh]">
                  <div className="bg-slate-800 border border-slate-700 rounded p-2 overflow-y-auto">
                    {project.files.map((f, idx) => (
                      <button
                        key={idx}
                        className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${selectedFile?.path === f.path ? 'bg-[#ff4500] text-white' : 'text-slate-300 hover:bg-slate-700'}`}
                        onClick={() => setSelectedFile(f)}
                      >
                        <Code2 className="h-3 w-3 inline mr-2" />
                        {f.path}
                      </button>
                    ))}
                    <div className="mt-4 space-x-2">
                      <Button variant="outline" size="sm" onClick={exportProject} className="text-white border-slate-600">
                        <Download className="h-4 w-4 mr-2" />
                        Export
                      </Button>
                      <GitHubPushDialog
                        trigger={<Button variant="outline" size="sm" className="text-white border-slate-600"><Github className="h-4 w-4 mr-2" />Push</Button>}
                        defaultOwner="Poach420"
                        defaultRepo="Digital-Ninja-v1"
                        defaultBranch="main"
                      />
                    </div>
                  </div>
                  <div className="bg-slate-800 border border-slate-700 rounded overflow-hidden">
                    {selectedFile ? (
                      <Editor
                        height="100%"
                        language={(selectedFile.path.split('.').pop() || 'txt') === 'js' ? 'javascript' : selectedFile.path.split('.').pop()}
                        value={selectedFile.content}
                        options={{ readOnly: true, minimap: { enabled: false }, fontSize: 14, lineNumbers: 'on', automaticLayout: true }}
                        theme="vs-dark"
                      />
                    ) : (
                      <div className="h-full flex items-center justify-center text-slate-400">Select a file to view</div>
                    )}
                  </div>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </Card>
      </div>
    </div>
  );
};

export default AiBuilder;