import { useEffect, useRef, useState } from 'react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { toast } from 'sonner';
import api from '../utils/api';

const ProjectChat = ({ projectId, mode = 'plan', onFileUpdates }) => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: mode === 'plan'
      ? 'Hi! Let’s plan improvements for this project. What would you like to achieve?'
      : 'Hi! Describe the change you want. I’ll suggest concrete edits.' }
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const send = async () => {
    if (!input.trim() || sending) return;
    if (!projectId) {
      toast.error('Please select a project first.');
      return;
    }
    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setSending(true);

    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      const endpoint = mode === 'plan'
        ? `/projects/${projectId}/chat/plan`
        : `/projects/${projectId}/chat/build`;

      const res = await api.post(endpoint, { message: userMessage, history });
      const data = res.data;
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }]);

      if (mode === 'build' && Array.isArray(data.file_updates) && data.file_updates.length > 0) {
        toast.info(`Applying ${data.file_updates.length} file update(s)...`);
        for (const f of data.file_updates) {
          await api.put(`/projects/${projectId}/files`, { path: f.path, content: f.content });
        }
        if (onFileUpdates) onFileUpdates(data.file_updates);
        toast.success('Updates applied');
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Chat failed');
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' }]);
    } finally {
      setSending(false);
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <div className="flex-1 border-b border-border">
        <ScrollArea className="h-full p-4" ref={scrollRef}>
          <div className="space-y-3">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`${m.role === 'user' ? 'bg-accent text-white' : 'bg-secondary text-foreground'} rounded-lg px-3 py-2 max-w-[80%]`}>
                  <p className="text-sm whitespace-pre-wrap">{m.content}</p>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>
      <div className="p-3 flex gap-2">
        <Input
          placeholder={mode === 'plan' ? 'Describe goals, features, or constraints...' : 'Describe the change to build...'}
          value={input}
          onChange={e => setInput(e.target.value)}
          disabled={sending}
        />
        <Button onClick={send} disabled={sending || !input.trim()}>
          {sending ? 'Sending...' : 'Send'}
        </Button>
      </div>
    </Card>
  );
};

export default ProjectChat;