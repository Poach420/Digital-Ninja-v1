"use client";

import React, { useState } from 'react';

interface CodeEditorProps {
  code: string;
  onChange: (code: string) => void;
  selectedFile: string | null;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({ code, onChange, selectedFile }) => {
  const [localCode, setLocalCode] = useState(code);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newCode = e.target.value;
    setLocalCode(newCode);
    onChange(newCode);
  };

  return (
    <div className="h-full flex flex-col bg-gray-900">
      <div className="bg-gray-800 px-4 py-2 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">
            {selectedFile || 'No file selected'}
          </span>
        </div>
        <div className="flex gap-2">
          <button className="text-xs text-gray-400 hover:text-gray-200 px-2 py-1 rounded hover:bg-gray-700">
            Format
          </button>
          <button className="text-xs text-gray-400 hover:text-gray-200 px-2 py-1 rounded hover:bg-gray-700">
            AI Optimize
          </button>
        </div>
      </div>
      
      <div className="flex-1 relative">
        <textarea
          value={localCode}
          onChange={handleChange}
          className="w-full h-full bg-gray-900 text-gray-100 p-4 font-mono text-sm resize-none focus:outline-none"
          placeholder={`// Start coding your app here...\n// Use the AI Assistant to generate code quickly!\n\nfunction App() {\n  return (\n    <div>\n      <h1>Hello, Digital Ninja!</h1>\n    </div>\n  );\n}`}
          spellCheck={false}
        />
        <div className="absolute bottom-4 right-4 text-xs text-gray-500">
          Lines: {localCode.split('\n').length} | Characters: {localCode.length}
        </div>
      </div>
    </div>
  );
};
