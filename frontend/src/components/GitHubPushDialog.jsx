import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { toast } from 'sonner';
import api from '../utils/api';

const GitHubPushDialog = ({ trigger, defaultOwner = 'Poach420', defaultRepo = 'Digital-Ninja-v1', defaultBranch = 'main' }) => {
  const [open, setOpen] = useState(false);
  const [owner, setOwner] = useState(defaultOwner);
  const [repo, setRepo] = useState(defaultRepo);
  const [branch, setBranch] = useState(defaultBranch);
  const [token, setToken] = useState('');
  const [message, setMessage] = useState('Push from Digital Ninja App Builder');
  const [pushing, setPushing] = useState(false);

  const onPush = async () => {
    if (!token.trim()) {
      toast.error('Please paste a GitHub Personal Access Token (repo scope).');
      return;
    }
    if (!owner.trim() || !repo.trim()) {
      toast.error('Owner and repository are required.');
      return;
    }
    setPushing(true);
    try {
      const res = await api.post('/github/push', {
        token: token.trim(),
        owner: owner.trim(),
        repo: repo.trim(),
        branch: branch.trim(),
        commit_message: message.trim(),
        // Include typical workspace paths; backend will walk & filter
        include_paths: [
          'frontend',
          'backend',
          'docker-compose.yml',
          'package.json',
          'pnpm-workspace.yaml',
          'README.md',
          'README_FINAL.md',
          'render.yaml',
          'vercel.json',
          '.gitignore'
        ]
      });
      toast.success(`Pushed ${res.data.files_pushed} file(s) to ${owner}/${repo}@${branch}`);
      setOpen(false);
    } catch (e) {
      const err = e.response?.data?.detail || e.message || 'GitHub push failed';
      toast.error(err);
    } finally {
      setPushing(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger || <Button>Push to GitHub</Button>}</DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Push to GitHub</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label>Repository Owner</Label>
            <Input value={owner} onChange={e => setOwner(e.target.value)} placeholder="github username or org" />
          </div>
          <div>
            <Label>Repository Name</Label>
            <Input value={repo} onChange={e => setRepo(e.target.value)} placeholder="repo name" />
          </div>
          <div>
            <Label>Branch</Label>
            <Input value={branch} onChange={e => setBranch(e.target.value)} placeholder="main" />
          </div>
          <div>
            <Label>Commit Message</Label>
            <Input value={message} onChange={e => setMessage(e.target.value)} />
          </div>
          <div>
            <Label>GitHub Personal Access Token (repo scope)</Label>
            <Input value={token} onChange={e => setToken(e.target.value)} placeholder="ghp_..." type="password" />
            <p className="text-xs text-muted-foreground mt-1">Your token is used only to contact GitHub from your server and is not stored.</p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={pushing}>Cancel</Button>
          <Button onClick={onPush} disabled={pushing}>{pushing ? 'Pushing...' : 'Push'}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default GitHubPushDialog;