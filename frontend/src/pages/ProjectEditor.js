import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { Button } from '../components/ui/button';
import { toast } from 'sonner';
import api from '../utils/api';
import LivePreview from '../components/LivePreview';
import { Save, Download, Trash2, FolderTree, Code2, Home, Rocket, Eye, EyeOff, Github } from 'lucide-react';

const ProjectEditor = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showPreview, setShowPreview] = useState(true);

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const loadProject = async () => {
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
      toast.error('Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleDeploy = async () => {
    setDeploying(true);
    try {
      const response = await api.post(`/deployments/deploy`, {
        project_id: projectId,
        tier: 'free'
      });
      if (response.data.status === 'deployed') {
        toast.success(`Deployed to ${response.data.urls.app}`);
        window.open(response.data.urls.app, '_blank');
      } else {
        toast.error('Deployment failed');
      }
    } catch (error) {
      toast.error(error.response?.data?.message || 'Deployment failed');
    } finally {
      setDeploying(false);
    }
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
          <div>
            <h1 className="text-xl font-heading font-bold text-white">{project.name}</h1>
            <p className="text-sm text-slate-400">{project.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setShowPreview(!showPreview)} className="text-white border-slate-600" data-testid="toggle-preview">
            {showPreview ? <EyeOff className="h-4 w-4 mr-2" /> : <Eye className="h-4 w-4 mr-2" />}
            {showPreview ? 'Hide' : 'Show'} Preview
          </Button>
          <div className="h-6 w-px bg-slate-700" />
          <Button variant="outline" size="sm" onClick={handleSave} disabled={saving} className="text-white border-slate-600" data-testid="save-button">
            <Save className="h-4 w-4 mr-2" />{saving ? 'Saving...' : 'Save'}
          </Button>
          <Button variant="outline" size="sm" onClick={handleDeploy} disabled={deploying} className="text-white border-slate-600 bg-[#ff4500] hover:bg-[#ff5722]" data-testid="deploy-button">
            <Rocket className="h-4 w-4 mr-2" />{deploying ? 'Deploying...' : 'Deploy'}
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
            <div className="w-1/2">
              <LivePreview files={project.files} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectEditor;