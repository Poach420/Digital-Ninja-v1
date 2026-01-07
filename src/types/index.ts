export interface FileNode {
  name: string;
  type: 'file' | 'folder';
  path: string;
  children?: FileNode[];
  content?: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  framework: 'react' | 'next' | 'vue' | 'angular';
  template: string;
  createdAt: Date;
  updatedAt: Date;
  files: FileNode[];
}

export interface AIMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

export interface CodeGenerationRequest {
  prompt: string;
  context?: string;
  language: string;
  framework?: string;
}

export interface CodeGenerationResponse {
  code: string;
  explanation?: string;
  suggestions?: string[];
}

export interface Template {
  id: string;
  name: string;
  description: string;
  framework: string;
  tags: string[];
  thumbnail?: string;
  files: FileNode[];
}
