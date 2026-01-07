"use client";

import React, { useState } from 'react';
import { ProjectExplorer } from '@/components/ProjectExplorer';
import { CodeEditor } from '@/components/CodeEditor';
import { PreviewPanel } from '@/components/PreviewPanel';
import { AIAssistant } from '@/components/AIAssistant';
import { ToolBar } from '@/components/ToolBar';

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [code, setCode] = useState<string>('');
  const [projectName, setProjectName] = useState<string>('My App');

  return (
    <main className="flex min-h-screen flex-col bg-gray-900">
      <ToolBar projectName={projectName} />
      
      <div className="flex flex-1 overflow-hidden">
        {/* Project Explorer Sidebar */}
        <div className="w-64 bg-gray-800 border-r border-gray-700">
          <ProjectExplorer 
            onFileSelect={(file) => {
              setSelectedFile(file);
            }}
          />
        </div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Code Editor */}
          <div className="flex-1 overflow-hidden">
            <CodeEditor 
              code={code}
              onChange={setCode}
              selectedFile={selectedFile}
            />
          </div>
        </div>

        {/* Right Sidebar - Preview & AI */}
        <div className="w-96 bg-gray-800 border-l border-gray-700 flex flex-col">
          <div className="flex-1 border-b border-gray-700 overflow-auto">
            <PreviewPanel code={code} />
          </div>
          <div className="h-80 overflow-auto">
            <AIAssistant 
              onCodeGenerate={(generatedCode) => {
                setCode(generatedCode);
              }}
            />
          </div>
        </div>
      </div>
    </main>
  );
}
