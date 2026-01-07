import { CodeGenerationRequest, CodeGenerationResponse } from '@/types';

/**
 * AI Code Generation Service
 * This is a mock implementation. In production, this would integrate with
 * OpenAI, Anthropic, or other AI providers.
 */

export class AICodeGenerator {
  /**
   * Generate code based on a prompt
   */
  async generateCode(request: CodeGenerationRequest): Promise<CodeGenerationResponse> {
    // Mock implementation - in production, this would call an AI API
    const { prompt, language, framework } = request;
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Generate sample code based on prompt keywords
    let code = '';
    let explanation = '';
    
    if (prompt.toLowerCase().includes('login')) {
      code = this.generateLoginForm(framework || 'react');
      explanation = 'Generated a modern login form with email and password fields, including form validation and styling.';
    } else if (prompt.toLowerCase().includes('dashboard')) {
      code = this.generateDashboard(framework || 'react');
      explanation = 'Generated a dashboard layout with sidebar navigation, header, and content area.';
    } else if (prompt.toLowerCase().includes('api')) {
      code = this.generateAPIRoute(framework || 'next');
      explanation = 'Generated a REST API route handler with error handling.';
    } else if (prompt.toLowerCase().includes('dark mode')) {
      code = this.generateDarkMode();
      explanation = 'Generated dark mode toggle functionality with CSS variables and local storage persistence.';
    } else {
      code = this.generateGenericComponent(prompt);
      explanation = `Generated a component based on your description: "${prompt}"`;
    }
    
    return {
      code,
      explanation,
      suggestions: [
        'Add error handling',
        'Implement loading states',
        'Add unit tests',
        'Optimize for performance',
      ],
    };
  }
  
  private generateLoginForm(framework: string): string {
    return `import React, { useState } from 'react';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // API call would go here
      console.log('Login:', { email, password });
    } catch (error) {
      console.error('Login failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center">Login</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div className="mb-6">
            <label className="block text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  );
}`;
  }
  
  private generateDashboard(framework: string): string {
    return `import React from 'react';

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="px-6 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
          <div className="flex items-center gap-4">
            <button className="text-gray-600 hover:text-gray-800">
              Notifications
            </button>
            <button className="text-gray-600 hover:text-gray-800">
              Profile
            </button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white shadow-sm min-h-screen">
          <nav className="p-4">
            <ul className="space-y-2">
              <li>
                <a href="#" className="block px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">
                  Overview
                </a>
              </li>
              <li>
                <a href="#" className="block px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">
                  Analytics
                </a>
              </li>
              <li>
                <a href="#" className="block px-4 py-2 text-gray-700 hover:bg-gray-100 rounded">
                  Settings
                </a>
              </li>
            </ul>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm">Total Users</h3>
              <p className="text-3xl font-bold text-gray-800">1,234</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm">Revenue</h3>
              <p className="text-3xl font-bold text-gray-800">$12,345</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-gray-500 text-sm">Active Projects</h3>
              <p className="text-3xl font-bold text-gray-800">42</p>
            </div>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-bold mb-4">Recent Activity</h2>
            <p className="text-gray-600">Activity feed would go here...</p>
          </div>
        </main>
      </div>
    </div>
  );
}`;
  }
  
  private generateAPIRoute(framework: string): string {
    return `// API Route: /api/users
import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    if (req.method === 'GET') {
      // Get all users
      const users = [
        { id: 1, name: 'John Doe', email: 'john@example.com' },
        { id: 2, name: 'Jane Smith', email: 'jane@example.com' },
      ];
      
      return res.status(200).json({ users });
    }
    
    if (req.method === 'POST') {
      // Create new user
      const { name, email } = req.body;
      
      // Validate input
      if (!name || !email) {
        return res.status(400).json({ error: 'Name and email are required' });
      }
      
      // Save user (database logic would go here)
      const newUser = { id: 3, name, email };
      
      return res.status(201).json({ user: newUser });
    }
    
    // Method not allowed
    res.setHeader('Allow', ['GET', 'POST']);
    return res.status(405).json({ error: \`Method \${req.method} not allowed\` });
    
  } catch (error) {
    console.error('API Error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}`;
  }
  
  private generateDarkMode(): string {
    return `import React, { useEffect, useState } from 'react';

export function DarkModeToggle() {
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    // Check local storage for saved preference
    const saved = localStorage.getItem('darkMode');
    if (saved) {
      setDarkMode(saved === 'true');
    }
  }, []);

  useEffect(() => {
    // Apply dark mode class to document
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    
    // Save preference
    localStorage.setItem('darkMode', darkMode.toString());
  }, [darkMode]);

  return (
    <button
      onClick={() => setDarkMode(!darkMode)}
      className="p-2 rounded-lg bg-gray-200 dark:bg-gray-700"
      aria-label="Toggle dark mode"
    >
      {darkMode ? '☀️' : '🌙'}
    </button>
  );
}

// Add to your CSS/Tailwind config:
// - Use 'dark:' prefix for dark mode styles
// - Example: className="bg-white dark:bg-gray-900"`;
  }
  
  private generateGenericComponent(prompt: string): string {
    return `import React from 'react';

// Component generated based on: "${prompt}"

export default function CustomComponent() {
  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">
        Component: ${prompt}
      </h2>
      <p className="text-gray-600">
        This is a generated component. Customize it to fit your needs!
      </p>
    </div>
  );
}`;
  }
}

// Export singleton instance
export const aiGenerator = new AICodeGenerator();
