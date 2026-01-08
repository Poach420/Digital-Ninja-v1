import { useEffect, useRef, useState } from 'react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { toast } from 'sonner';
import api from '../utils/api';
import { isDevAuthEnabled } from '../utils/devAuth';

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

  const applyLocalBuild = (message) => {
    const cache = JSON.parse(localStorage.getItem('dev_projects') || '{}');
    const proj = cache[projectId];
    if (!proj || !Array.isArray(proj.files)) return [];

    const appFile = proj.files.find(f => /App\.(js|jsx)$/.test(f.path)) || { path: 'src/App.js', content: "export default function App(){return <div style={{padding:24}}>Hello</div>;}" };
    let content = appFile.content;
    const m = message.toLowerCase();

    const tabShell = `
export default function App(){
  const [tab,setTab]=React.useState('home');
  const Link = ({id,children}) => <button onClick={()=>setTab(id)} style={{padding:8,marginRight:8,borderRadius:8,border:'1px solid #334155',background:tab===id?'#0f172a':'#111827',color:'#d7e7ff'}}>{children}</button>;
  return (
    <div style={{minHeight:'100vh',background:'#0b0f16',color:'#d7e7ff',fontFamily:'system-ui',padding:24}}>
      <nav style={{marginBottom:16}}>
        <Link id="home">Home</Link>
        <Link id="about">About</Link>
        <Link id="products">Products</Link>
        <Link id="faq">FAQ</Link>
        <Link id="contact">Contact</Link>
      </nav>
      {tab==='home' && (<div><h1>Home</h1><p>Welcome to Digital Ninja.</p></div>)}
      {tab==='about' && (<div><h1>About</h1><p>About our project.</p></div>)}
      {tab==='products' && (<div><h1>Products</h1><ul><li>Product A</li><li>Product B</li></ul></div>)}
      {tab==='faq' && (<div><h1>FAQ</h1><p>Q: What is this? A: An AI-built demo.</p></div>)}
      {tab==='contact' && (<div><h1>Contact</h1><p>Email: hello@example.com</p></div>)}
    </div>
  );
}
`.trim();

    if (/(tab|navbar|about|contact|faq|products)/.test(m) && !/useState\(['"]home['"]\)/.test(content)) {
      content = tabShell;
    }
    const themeHex = (m.match(/#(?:[0-9a-f]{3}|[0-9a-f]{6})/i) || [])[0];
    if (themeHex) {
      content = content.replace(/#20d6ff/g, themeHex).replace(/#46ff9b/g, themeHex);
    }

    const update = { path: appFile.path, content };
    // Put back into local cache
    const idx = proj.files.findIndex(f => f.path === appFile.path);
    if (idx >= 0) {
      proj.files[idx] = { ...proj.files[idx], content };
    } else {
      proj.files.push({ path: appFile.path, content, language: 'js' });
    }
    cache[projectId] = proj;
    localStorage.setItem('dev_projects', JSON.stringify(cache));
    return [update];
  };

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
      if (isDevAuthEnabled()) {
        if (mode === 'plan') {
          const assist = `Plan summary:\n- Add tabs (Home, About, Products, FAQ, Contact)\n- Polish UI components and navigation\n- Adjust theme color and spacing\nReply with a specific change and I'll apply it.`;
          setMessages((prev) => [...prev, { role: 'assistant', content: assist }]);
        } else {
          const updates = applyLocalBuild(userMessage);
          const reply = updates.length
            ? 'Applied your change locally. Preview should update.'
            : 'No changes were necessary. Try asking to add tabs or set a theme color (e.g., #ff4500).';
          setMessages((prev) => [...prev, { role: 'assistant', content: reply }]);
          if (updates.length && onFileUpdates) onFileUpdates(updates);
          toast.success('Local update applied');
        }
      } else {
        toast.error(e.response?.data?.detail || 'Chat failed');
        setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' }]);
      }
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