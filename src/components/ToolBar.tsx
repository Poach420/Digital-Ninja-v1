"use client";

import React from 'react';

interface ToolBarProps {
  projectName: string;
}

export const ToolBar: React.FC<ToolBarProps> = ({ projectName }) => {
  return (
    <div className="bg-gray-800 border-b border-gray-700 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600">
          Digital Ninja
        </h1>
        <span className="text-gray-400">|</span>
        <span className="text-gray-300">{projectName}</span>
      </div>
      
      <div className="flex items-center gap-2">
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition-colors">
          Save
        </button>
        <button className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm font-medium transition-colors">
          Deploy
        </button>
        <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-md text-sm font-medium transition-colors">
          Export
        </button>
      </div>
    </div>
  );
};
