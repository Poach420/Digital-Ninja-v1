"use client";

import React, { useState } from 'react';

interface ProjectExplorerProps {
  onFileSelect: (file: string) => void;
}

interface FileNode {
  name: string;
  type: 'file' | 'folder';
  children?: FileNode[];
}

const demoStructure: FileNode[] = [
  {
    name: 'src',
    type: 'folder',
    children: [
      {
        name: 'components',
        type: 'folder',
        children: [
          { name: 'Button.tsx', type: 'file' },
          { name: 'Header.tsx', type: 'file' },
        ],
      },
      {
        name: 'pages',
        type: 'folder',
        children: [
          { name: 'index.tsx', type: 'file' },
          { name: 'about.tsx', type: 'file' },
        ],
      },
      { name: 'App.tsx', type: 'file' },
    ],
  },
  { name: 'package.json', type: 'file' },
  { name: 'tsconfig.json', type: 'file' },
];

const FileTreeNode: React.FC<{
  node: FileNode;
  level: number;
  onFileSelect: (file: string) => void;
}> = ({ node, level, onFileSelect }) => {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div>
      <div
        className={`flex items-center gap-2 px-2 py-1 cursor-pointer hover:bg-gray-700 rounded`}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={() => {
          if (node.type === 'folder') {
            setIsOpen(!isOpen);
          } else {
            onFileSelect(node.name);
          }
        }}
      >
        {node.type === 'folder' ? (
          <span className="text-yellow-400">{isOpen ? '📂' : '📁'}</span>
        ) : (
          <span className="text-blue-400">📄</span>
        )}
        <span className="text-sm text-gray-200">{node.name}</span>
      </div>
      {node.type === 'folder' && isOpen && node.children && (
        <div>
          {node.children.map((child, idx) => (
            <FileTreeNode
              key={idx}
              node={child}
              level={level + 1}
              onFileSelect={onFileSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const ProjectExplorer: React.FC<ProjectExplorerProps> = ({ onFileSelect }) => {
  return (
    <div className="h-full flex flex-col">
      <div className="p-3 border-b border-gray-700">
        <h2 className="text-sm font-semibold text-gray-300 uppercase">Project Explorer</h2>
      </div>
      <div className="flex-1 overflow-auto p-2">
        {demoStructure.map((node, idx) => (
          <FileTreeNode key={idx} node={node} level={0} onFileSelect={onFileSelect} />
        ))}
      </div>
      <div className="p-2 border-t border-gray-700">
        <button className="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition-colors">
          + New File
        </button>
      </div>
    </div>
  );
};
