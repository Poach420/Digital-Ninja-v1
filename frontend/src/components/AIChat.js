import { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { X, Send, Sparkles } from 'lucide-react';
import { BACKEND_URL } from '../utils/api';
import { isDevAuthEnabled } from '../utils/devAuth';

const AIChat = ({ onClose }) => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I\'m your Digital Ninja AI assistant. How can I help you build your app today?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const devStream = (text) => {
    const words = (`Dev reply: ${text}`).split(' ');
    let idx = 0;
    setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);
    const interval = setInterval(() => {
      idx += 1;
      setMessages((prev) => {
        const newMessages = [...prev];
        const assembled = words.slice(0, idx).join(' ');
        newMessages[newMessages.length - 1] = { role: 'assistant', content: assembled };
        return newMessages;
      });
      if (idx >= words.length) clearInterval(interval);
    }, 40);
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message: userMessage }),
      });

      // If backend not reachable or unauthorized, use dev fallback
      if (!response.ok && isDevAuthEnabled()) {
        devStream(userMessage);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';

      setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;
            if (data.trim()) {
              assistantMessage += (assistantMessage ? ' ' : '') + data.trim();
              setMessages((prev) => {
                const newMessages = [...prev];
                newMessages[newMessages.length - 1] = {
                  role: 'assistant',
                  content: assistantMessage,
                };
                return newMessages;
              });
            }
          }
        }
      }
    } catch (error) {
      if (isDevAuthEnabled()) {
        devStream(userMessage);
      } else {
        console.error('Chat error:', error);
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' },
        ]);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed right-0 top-0 h-screen w-96 bg-white border-l border-border shadow-xl z-[100] flex flex-col">
      <Card className="flex flex-col h-full border-0 rounded-none">
        <CardHeader className="border-b border-border flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-accent/10 flex items-center justify-center">
                <Sparkles className="h-4 w-4 text-accent" />
              </div>
              <CardTitle className="text-lg font-heading">AI Assistant</CardTitle>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose} data-testid="close-ai-chat">
              <X className="h-5 w-5" />
            </Button>
          </div>
        </CardHeader>

        <ScrollArea className="flex-1 p-4" ref={scrollRef}>
          <div className="space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                data-testid={`chat-message-${msg.role}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    msg.role === 'user'
                      ? 'bg-accent text-white'
                      : 'bg-secondary text-foreground'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-secondary rounded-lg px-4 py-2">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        <CardContent className="p-4 border-t border-border flex-shrink-0">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex gap-2"
          >
            <Input
              placeholder="Ask me anything..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
              data-testid="ai-chat-input"
            />
            <Button type="submit" size="icon" disabled={loading || !input.trim()} data-testid="ai-chat-send">
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default AIChat;