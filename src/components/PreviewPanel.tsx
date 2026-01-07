"use client";

import React from 'react';

interface PreviewPanelProps {
  code: string;
}

export const PreviewPanel: React.FC<PreviewPanelProps> = ({ code }) => {
  return (
    <div className="h-full flex flex-col">
      <div className="bg-gray-800 px-4 py-2 border-b border-gray-700">
        <h2 className="text-sm font-semibold text-gray-300">Live Preview</h2>
      </div>
      
      <div className="flex-1 bg-white p-4 overflow-auto">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <div className="text-gray-600">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <p className="text-sm font-medium">Preview Window</p>
            <p className="text-xs text-gray-500 mt-2">Your app will render here in real-time</p>
          </div>
        </div>
      </div>
      
      <div className="bg-gray-800 px-4 py-2 border-t border-gray-700 flex gap-2">
        <button className="flex-1 px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-xs font-medium transition-colors">
          Desktop
        </button>
        <button className="flex-1 px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-xs font-medium transition-colors">
          Tablet
        </button>
        <button className="flex-1 px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-xs font-medium transition-colors">
          Mobile
        </button>
      </div>
    </div>
  );
};
