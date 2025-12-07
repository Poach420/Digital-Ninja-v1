import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import api from '../utils/api';
import { Plus, Code2, Calendar, Sparkles, LogOut } from 'lucide-react';

const Projects = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await api.get('/projects');
      setProjects(response.data);
    } catch (error) {
      toast.error('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <div className=\"min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6\" data-testid=\"projects-page\">
      <div className=\"max-w-7xl mx-auto\">
        {/* Header */}
        <div className=\"flex items-center justify-between mb-8\">
          <div>
            <h1 className=\"text-4xl font-heading font-bold text-white mb-2\">Your Projects</h1>
            <p className=\"text-slate-400\">Welcome back, {user.name}</p>
          </div>
          <div className=\"flex gap-3\">
            <Button onClick={() => navigate('/builder')} className=\"bg-indigo-600 hover:bg-indigo-700\" data-testid=\"new-project-button\">
              <Plus className=\"mr-2 h-4 w-4\" />
              New Project
            </Button>
            <Button variant=\"outline\" onClick={handleLogout} className=\"text-white border-slate-600\" data-testid=\"logout-button\">
              <LogOut className=\"mr-2 h-4 w-4\" />
              Logout
            </Button>
          </div>
        </div>

        {/* Projects Grid */}
        {loading ? (
          <div className=\"text-center text-white py-12\">
            <p>Loading projects...</p>
          </div>
        ) : projects.length === 0 ? (
          <Card className=\"p-12 text-center bg-slate-800/50 border-slate-700\">
            <Sparkles className=\"h-16 w-16 text-indigo-400 mx-auto mb-4\" />
            <h2 className=\"text-2xl font-heading font-bold text-white mb-2\">No Projects Yet</h2>
            <p className=\"text-slate-400 mb-6\">Start building your first AI-generated application</p>
            <Button onClick={() => navigate('/builder')} className=\"bg-indigo-600 hover:bg-indigo-700\">
              <Plus className=\"mr-2 h-4 w-4\" />
              Create Your First Project
            </Button>
          </Card>
        ) : (
          <div className=\"grid gap-6 md:grid-cols-2 lg:grid-cols-3\">
            {projects.map((project) => (
              <Card
                key={project.project_id}
                className=\"bg-slate-800/50 border-slate-700 hover:border-indigo-500 transition-colors cursor-pointer\"
                onClick={() => navigate(`/project/${project.project_id}`)}
                data-testid={`project-${project.project_id}`}
              >
                <CardHeader>
                  <div className=\"flex items-start justify-between mb-2\">
                    <Code2 className=\"h-8 w-8 text-indigo-400\" />
                    <Badge variant=\"outline\" className=\"text-xs text-slate-300 border-slate-600\">
                      {project.tech_stack.frontend}
                    </Badge>
                  </div>
                  <CardTitle className=\"text-white font-heading\">{project.name}</CardTitle>
                  <CardDescription className=\"text-slate-400\">{project.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className=\"flex items-center justify-between text-sm\">
                    <div className=\"flex items-center gap-4 text-slate-400\">
                      <span className=\"flex items-center gap-1\">
                        <Calendar className=\"h-3 w-3\" />
                        {new Date(project.created_at).toLocaleDateString()}
                      </span>
                      <span>{project.files.length} files</span>
                    </div>
                  </div>
                  <div className=\"flex gap-2 mt-4\">
                    <Badge variant=\"secondary\" className=\"text-xs bg-slate-700 text-slate-300\">
                      {project.tech_stack.backend}
                    </Badge>
                    <Badge variant=\"secondary\" className=\"text-xs bg-slate-700 text-slate-300\">
                      {project.tech_stack.database}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Projects;
