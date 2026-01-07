"use client";

import React, { useState } from 'react';

interface AIAssistantProps {
  onCodeGenerate: (code: string) => void;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const AIAssistant: React.FC<AIAssistantProps> = ({ onCodeGenerate }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hi! I'm your AI coding assistant. I can help you:\n\n• Generate components and code\n• Debug and optimize code\n• Suggest best practices\n• Create full app structures\n\nWhat would you like to build?"
    }
  ]);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages([...messages, userMessage]);

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        role: 'assistant',
        content: `I'll help you with that! Here's a suggestion:\n\n\`\`\`tsx\nfunction Component() {\n  return <div>Generated code based on: ${input}</div>\n}\n\`\`\`\n\nWould you like me to add this to your editor?`
      };
      setMessages(prev => [...prev, aiResponse]);
    }, 500);

    setInput('');
  };

  const quickActions = [
    'Create a login form',
    'Build a dashboard',
    'Add dark mode',
    'Create API routes',
  ];

  return (
    <div className="h-full flex flex-col bg-gray-900">
      <div className="bg-gray-800 px-4 py-2 border-b border-gray-700">
        <h2 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
          <span className="text-purple-400">✨</span>
          AI Assistant
        </h2>
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg p-3 text-sm ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-200'
              }`}
            >
              <pre className="whitespace-pre-wrap font-sans">{msg.content}</pre>
            </div>
          </div>
        ))}
      </div>

      <div className="p-3 space-y-2 border-t border-gray-700">
        <div className="flex flex-wrap gap-2">
          {quickActions.map((action, idx) => (
            <button
              key={idx}
              onClick={() => setInput(action)}
              className="text-xs px-2 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded border border-gray-700 transition-colors"
            >
              {action}
            </button>
          ))}
        </div>
        
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask AI anything..."
            className="flex-1 px-3 py-2 bg-gray-800 text-gray-200 rounded border border-gray-700 focus:outline-none focus:border-blue-500 text-sm"
          />
          <button
            onClick={handleSend}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded text-sm font-medium transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};
