import { useEffect, useState } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Button } from './ui/button';
import { toast } from 'sonner';
import api from '../utils/api';

const ProjectSelect = ({ value, onChange, onNewProject }) => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const res = await api.get('/projects');
        if (mounted) setProjects(res.data || []);
      } catch (e) {
        toast.error('Failed to load projects');
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => { mounted = false; };
  }, []);

  return (
    <div className="flex items-center gap-2">
      <Select value={value || ''} onValueChange={(v) => onChange(v)} disabled={loading}>
        <SelectTrigger className="min-w-[240px]">
          <SelectValue placeholder={loading ? 'Loading projects...' : 'Select a project'} />
        </SelectTrigger>
        <SelectContent>
          {projects.map((p) => (
            <SelectItem key={p.project_id} value={p.project_id}>
              {p.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button variant="outline" onClick={onNewProject}>New Project</Button>
    </div>
  );
};

export default ProjectSelect;