import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import api from '../utils/api';
import LivePreview from '../components/LivePreview';
import { Save, Download, Trash2, FolderTree, Code2, Home, Rocket, Eye, EyeOff, Github, MessageSquare, Hammer } from 'lucide-react';
import { isDevAuthEnabled } from '../utils/devAuth';
import AIChat from '../components/AIChat';
import BrandLogo from '../components/BrandLogo';
import DeploymentConsole from '../components/DeploymentConsole';

const ProjectEditor = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showPreview, setShowPreview] = useState(true);
  const [showChat, setShowChat] = useState(false);
  const [deployConsoleOpen, setDeployConsoleOpen] = useState(false);

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const loadProject = async () => {
    // Offline dev: load local project without calling backend
    if (isDevAuthEnabled() && (projectId.startsWith('dev_') || projectId === 'demo_project')) {
      const cache = JSON.parse(localStorage.getItem('dev_projects') || '{}');
      const localProj = cache[projectId];
      if (localProj) {
        setProject(localProj);
        if (localProj.files.length > 0) selectFile(localProj.files[0]);
        setLoading(false);
        return;
      }
      if (projectId === 'demo_project') {
        const demo = {
          project_id: 'demo_project',
          user_id: 'dev_user',
          name: 'Demo App',
          description: 'Sample project for preview',
          prompt: 'Demo app preview',
          tech_stack: { frontend: 'React', backend: 'FastAPI', database: 'MongoDB' },
          files: [
            { path: 'src/App.js', content: 'export default function App(){return <div style={{padding:20}}><h1>Demo App</h1><p>Hello from Digital Ninja.</p></div>}', language: 'js' },
            { path: 'src/index.css', content: 'body{font-family:sans-serif;background:#0b0f16}', language: 'css' },
          ],
          status: 'active',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        setProject(demo);
        selectFile(demo.files[0]);
        setLoading(false);
        return;
      }
    }

    try {
      const response = await api.get(`/projects/${projectId}`);
      setProject(response.data);
      if (response.data.files.length > 0) {
        selectFile(response.data.files[0]);
      }
    } catch (error) {
      toast.error('Failed to load project');
      navigate('/projects');
    } finally {
      setLoading(false);
    }
  };

  const selectFile = (file) => {
    setSelectedFile(file);
    setFileContent(file.content);
  };

  const handleSave = async () => {
    if (!selectedFile) return;
    setSaving(true);
    try {
      await api.put(`/projects/${projectId}/files`, {
        path: selectedFile.path,
        content: fileContent
      });
      setProject(prev => ({
        ...prev,
        files: prev.files.map(f =>
          f.path === selectedFile.path ? { ...f, content: fileContent } : f
        )
      }));
      toast.success('File saved');
    } catch (error) {
      if (isDevAuthEnabled()) {
        // Save to local cache
        const cache = JSON.parse(localStorage.getItem('dev_projects') || '{}');
        const current = cache[projectId] || project;
        const updatedFiles = (current.files || []).map(f =>
          f.path === selectedFile.path ? { ...f, content: fileContent } : f
        );
        cache[projectId] = { ...(current || {}), files: updatedFiles, updated_at: new Date().toISOString() };
        localStorage.setItem('dev_projects', JSON.stringify(cache));
        setProject(prev => ({ ...prev, files: updatedFiles }));
        toast.success('Saved locally');
      } else {
        toast.error('Save failed');
      }
    } finally {
      setSaving(false);
    }
  };

  const handleDeploymentComplete = (deploymentResult) => {
    toast.success(deploymentResult?.url ? `Deployed to ${deploymentResult.url}` : 'Deployment completed');
    setProject((prev) => (
      prev
        ? {
          ...prev,
          deployment: deploymentResult,
          deployed_at: new Date().toISOString(),
        }
        : prev
    ));
  };

  const handleExport = async () => {
    try {
      const response = await api.post(`/projects/${projectId}/export`);
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${project.name}-export.json`;
      a.click();
      toast.success('Project exported');
    } catch (error) {
      toast.error('Export failed');
    }
  };

  const handleGitHubExport = async () => {
    try {
      toast.loading('Preparing clean export...');
      const response = await api.post(`/projects/${projectId}/export/github`);

      // Create a download of the clean project structure
      const exportData = {
        name: response.data.project_name,
        description: response.data.description,
        files: response.data.files,
        deployment_ready: true,
        instructions: "All files are clean and deployment-ready. No Emergent dependencies included."
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${response.data.project_name}-github-ready.json`;
      a.click();

      toast.success('✅ Clean code exported! Ready for GitHub push');
      toast.info('📦 Files include: vercel.json, .env.example, .gitignore');
    } catch (error) {
      toast.error('GitHub export failed');
    }
  };


  const handleDelete = async () => {
    if (!confirm('Delete this project?')) return;
    try {
      await api.delete(`/projects/${projectId}`);
      toast.success('Project deleted');
      navigate('/projects');
    } catch (error) {
      toast.error('Delete failed');
    }
  };

  const getLanguage = (filename) => {
    const ext = filename.split('.').pop();
    const map = { js: 'javascript', jsx: 'javascript', ts: 'typescript', tsx: 'typescript', py: 'python', json: 'json', html: 'html', css: 'css', md: 'markdown' };
    return map[ext] || 'plaintext';
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen bg-slate-900 text-white">Loading...</div>;
  }

  if (!project) return null;

  return (
    <div className="h-screen flex flex-col bg-slate-900" data-testid="project-editor">
      <div className="bg-slate-800 border-b border-slate-700 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/projects')} className="text-slate-300">
            <Home className="h-4 w-4 mr-2" />Projects
          </Button>
          <div className="h-6 w-px bg-slate-700" />
          <BrandLogo className="h-6 w-6 rounded-md" />
          <div>
            <h1 className="text-xl font-heading font-bold text-white">{project.name}</h1>
            <p className="text-sm text-slate-400">{project.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setShowChat(!showChat)} className="text-white border-slate-600" data-testid="toggle-chat">
            <MessageSquare className="h-4 w-4 mr-2" />
            {showChat ? 'Close Chat' : 'AI Assistant'}
          </Button>
          <Button variant="outline" size="sm" onClick={() => navigate(`/ai-builder?projectId=${projectId}`)} className="text-white border-slate-600" data-testid="continue-build">
            <Hammer className="h-4 w-4 mr-2" />
            Continue Build
          </Button>
          <div className="h-6 w-px bg-slate-700" />
          <Button variant="outline" size="sm" onClick={() => setShowPreview(!showPreview)} className="text-white border-slate-600" data-testid="toggle-preview">
            {showPreview ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
            {showPreview ? 'Hide' : 'Show'} Preview
          </Button>
          <div className="h-6 w-px bg-slate-700" />
          <Button variant="outline" size="sm" onClick={handleSave} disabled={saving} className="text-white border-slate-600" data-testid="save-button">
            <Save className="h-4 w-4 mr-2" />{saving ? 'Saving...' : 'Save'}
          </Button>
          <Button variant="outline" size="sm" onClick={() => setDeployConsoleOpen(true)} className="text-white border-slate-600 bg-[#ff4500] hover:bg-[#ff5722]" data-testid="deploy-button">
            <Rocket className="h-4 w-4 mr-2" />Deploy
          </Button>
          <Button variant="outline" size="sm" onClick={handleGitHubExport} className="text-white border-slate-600 bg-[#ff4500] hover:bg-[#ff5722]" data-testid="github-export-button">
            <Github className="h-4 w-4 mr-2" />Export to GitHub
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport} className="text-white border-slate-600" data-testid="export-button">
            <Download className="h-4 w-4 mr-2" />Download
          </Button>
          <Button variant="outline" size="sm" onClick={handleDelete} className="text-red-400 border-slate-600" data-testid="delete-button">
            <Trash2 className="h-4 w-4 mr-2" />Delete
          </Button>
        </div>
      </div>
      <div className="flex-1 flex overflow-hidden">
        <div className="w-64 bg-slate-800 border-r border-slate-700 overflow-y-auto">
          <div className="p-4 border-b border-slate-700">
            <div className="flex items-center gap-2 text-white font-medium"><FolderTree className="h-4 w-4" /><span>Files</span></div>
          </div>
          <div className="p-2">
            {project.files.map((file, idx) => (
              <button key={idx} onClick={() => selectFile(file)} className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${selectedFile?.path === file.path ? 'bg-[#ff4500] text-white' : 'text-slate-300 hover:bg-slate-700'}`} data-testid={`file-${idx}`}>
                <Code2 className="h-3 w-3 inline mr-2" />{file.path}
              </button>
            ))}
          </div>
        </div>
        <div className={`flex-1 flex ${showPreview ? 'flex-row' : 'flex-col'}`}>
          <div className={`flex flex-col ${showPreview ? 'w-1/2 border-r border-slate-700' : 'flex-1'}`}>
            {selectedFile ? (
              <>
                <div className="bg-slate-800 px-6 py-3 border-b border-slate-700">
                  <p className="text-sm text-slate-300 font-mono">{selectedFile.path}</p>
                </div>
                <div className="flex-1">
                  <Editor height="100%" language={getLanguage(selectedFile.path)} value={fileContent} onChange={(value) => setFileContent(value || '')} theme="vs-dark" options={{ minimap: { enabled: false }, fontSize: 14, lineNumbers: 'on', scrollBeyondLastLine: false, automaticLayout: true }} />
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-slate-400">Select a file to edit</div>
            )}
          </div>
          {showPreview && (
            <div className="w-1/2 relative">
              <LivePreview files={project.files} />
              {showChat && <AIChat onClose={() => setShowChat(false)} />}
            </div>
          )}
        </div>
      </div>
      <DeploymentConsole
        open={deployConsoleOpen}
        onOpenChange={setDeployConsoleOpen}
        projectId={projectId}
        projectName={project?.name}
        onComplete={handleDeploymentComplete}
      />
    </div>
  );
};

export default ProjectEditor;