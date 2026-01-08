import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Eye, Hammer, ClipboardList, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import ProjectSelect from '../components/ProjectSelect';
import ProjectChat from '../components/ProjectChat';
import LivePreview from '../components/LivePreview';

const AiBuilder = () => {
  const navigate = useNavigate();
  const [projectId, setProjectId] = useState('');
  const [project, setProject] = useState(null);
  const [loadingProject, setLoadingProject] = useState(false);

  useEffect(() => {
    // Preselect project from query string (e.g., /ai-builder?projectId=xyz)
    const params = new URLSearchParams(window.location.search);
    const pid = params.get('projectId');
    if (pid) setProjectId(pid);
  }, []);

  useEffect(() => {
    if (projectId) {
      loadProject(projectId);
    } else {
      setProject(null);
    }
  }, [projectId]);

  const loadProject = async (id) => {
    setLoadingProject(true);
    try {
      const res = await api.get(`/projects/${id}`);
      setProject(res.data);
    } catch (e) {
      toast.error('Failed to load project');
      setProject(null);
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
            <TabsList className="grid grid-cols-3 w-full bg-slate-800 border border-slate-700">
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
          </Tabs>
        </Card>
      </div>
    </div>
  );
};

export default AiBuilder;