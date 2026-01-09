import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import api, { BACKEND_URL } from '../utils/api';
import { Sparkles, Loader2, Code, Eye, FileCode, CheckCircle, AlertCircle } from 'lucide-react';
import BrandLogo from '../components/BrandLogo';

const ImprovedBuilder = () => {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState('');
  const [chatMessage, setChatMessage] = useState(''); // Separate chat input
  const [generating, setGenerating] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [generatedFiles, setGeneratedFiles] = useState([]);
  const [progressLog, setProgressLog] = useState([]);
  const [currentProjectId, setCurrentProjectId] = useState(null);
  const [previewHtml, setPreviewHtml] = useState('');
  const [aiSummary, setAiSummary] = useState(''); // AI conclusion after build
  const [chatMode, setChatMode] = useState(false); // Toggle between build/chat
  const iframeRef = useRef(null);

  // Add progress log entry
  const addLog = (message, type = 'info') => {
    setProgressLog(prev => [...prev, {
      message,
      type, // 'info', 'success', 'error', 'file'
      timestamp: new Date().toLocaleTimeString()
    }]);
  };

  // Simulate file-by-file generation progress
  const simulateProgress = (files) => {
    addLog('🚀 Starting AI-powered generation with GPT-4o...', 'info');
    addLog('📊 Analyzing your requirements...', 'info');
    
    setTimeout(() => {
      addLog('🏗️ Building project structure...', 'info');
    }, 500);

    setTimeout(() => {
      addLog('⚛️ Setting up React components...', 'info');
    }, 1000);

    // Show each file being created
    files.forEach((file, index) => {
      setTimeout(() => {
        addLog(`✅ Created: ${file.path} (${file.content?.length || 0} chars)`, 'file');
      }, 1500 + (index * 300));
    });

    setTimeout(() => {
      addLog('🎨 Applying styles and themes...', 'info');
    }, 1500 + (files.length * 300) + 500);

    setTimeout(() => {
      addLog('✨ Finalizing build...', 'success');
    }, 1500 + (files.length * 300) + 1000);

    setTimeout(() => {
      addLog('🎉 Project generated successfully!', 'success');
    }, 1500 + (files.length * 300) + 1500);
  };

  // Chat with AI about the project (no rebuild)
  const handleChat = async () => {
    if (!chatMessage.trim()) return;
    
    setGenerating(true);
    addLog(`💬 You: ${chatMessage}`, 'info');
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: chatMessage,
          context: currentProjectId ? {
            project_id: currentProjectId,
            files: generatedFiles.map(f => ({ path: f.path, size: f.content.length }))
          } : null
        })
      });
      
      const data = await response.json();
      if (data.response) {
        // Display AI response
        const aiResponse = data.response;
        addLog(`🤖 AI: ${aiResponse}`, 'success');
        
        // Update summary with chat response
        setAiSummary(prev => prev + `\n\n**Q:** ${chatMessage}\n**A:** ${aiResponse}`);
      }
      
      setChatMessage('');
    } catch (error) {
      console.error('Chat error:', error);
      addLog(`❌ Chat error: ${error.message}`, 'error');
      toast.error('Failed to chat with AI');
    } finally {
      setGenerating(false);
    }
  };

  const handleBuild = async () => {
    if (!prompt.trim()) {
      toast.error('Please enter a project description');
      return;
    }

    setGenerating(true);
    setProgressLog([]);
    setGeneratedFiles([]);
    setShowPreview(false);

    try {
      // Use REAL streaming endpoint
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/projects/generate/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          prompt: prompt.trim(),
          tech_stack: {
            frontend: 'React',
            backend: 'FastAPI',
            database: 'MongoDB'
          }
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let allFiles = [];
      let projectId = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'status') {
                addLog(data.message, 'info');
              } else if (data.type === 'file') {
                const file = data.file;
                allFiles.push(file);
                addLog(`✅ Created: ${file.path} (${file.content?.length || 0} chars)`, 'file');
              } else if (data.type === 'complete') {
                projectId = data.project_id;
                setGeneratedFiles(data.files);
                allFiles = data.files;
                addLog('🎉 Project generated successfully!', 'success');
                
                // Generate AI summary
                const pageCount = data.files.filter(f => f.path.includes('pages/') || f.path.includes('Pages/')).length;
                const componentCount = data.files.filter(f => f.path.includes('components/') || f.path.includes('Components/')).length;
                const hasCSS = data.files.some(f => f.path.includes('.css'));
                
                const summary = `🎉 **Build Complete!**\n\n` +
                  `I've created a professional ${pageCount}-page application with:\n` +
                  `• ${data.files.length} total files (${componentCount} reusable components)\n` +
                  `• ${pageCount} unique pages with real content\n` +
                  `• ${hasCSS ? 'Modern CSS styling with animations' : 'Basic styling'}\n` +
                  `• Responsive design for mobile/desktop\n\n` +
                  `**Files created:**\n` +
                  data.files.slice(0, 8).map(f => `• ${f.path}`).join('\n') +
                  (data.files.length > 8 ? `\n• ...and ${data.files.length - 8} more files` : '') +
                  `\n\n**Next steps:**\n` +
                  `• Preview on the right shows simplified version\n` +
                  `• Use "Continue working" below to add features/fix issues\n` +
                  `• Click "My Projects" to access full editor and deployment`;
                
                setAiSummary(summary);
              } else if (data.type === 'error') {
                addLog(`❌ Error: ${data.message}`, 'error');
              }
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }

      // Generate preview
      if (allFiles.length > 0) {
        setCurrentProjectId(projectId);
        const appFile = allFiles.find(f => f.path.includes('App.js') || f.path.includes('App.jsx'));
        
        // Check if this is a multi-page app with React Router
        const hasRouter = appFile?.content.includes('react-router') || appFile?.content.includes('BrowserRouter');
        
        if (hasRouter) {
          // Multi-page apps can't preview properly in iframe
          console.log('Multi-page app detected (uses React Router) - showing info instead');
          const pageCount = allFiles.filter(f => f.path.includes('pages/') || f.path.includes('Pages/')).length;
          setPreviewHtml(generateInfoHtml(allFiles, pageCount));
        } else if (appFile) {
          console.log('Single-page app detected - generating preview:', appFile.path);
          const previewCode = generatePreviewHtml(appFile.content, allFiles);
          console.log('Preview HTML length:', previewCode.length);
          setPreviewHtml(previewCode);
        } else {
          console.warn('No App.js found, using first file');
          const firstFile = allFiles[0];
          if (firstFile) {
            const previewCode = generatePreviewHtml(firstFile.content, allFiles);
            setPreviewHtml(previewCode);
          }
        }
        setShowPreview(true);
      }

      setGenerating(false);
      toast.success(`Project generated with ${allFiles.length} files!`);
      
    } catch (error) {
      console.error('Generation error:', error);
      addLog(`❌ Error: ${error.message || 'Failed to generate project'}`, 'error');
      toast.error(error.message || 'Failed to generate project');
      setGenerating(false);
    }
  };

  const generateInfoHtml = (files, pageCount) => {
    // For multi-page apps with Router, show info instead of broken preview
    const pages = files.filter(f => f.path.includes('pages/') || f.path.includes('Pages/'));
    const components = files.filter(f => f.path.includes('components/') || f.path.includes('Components/'));
    
    return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      margin: 0;
      padding: 40px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .container {
      background: rgba(255,255,255,0.95);
      color: #1a202c;
      padding: 40px;
      border-radius: 16px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      max-width: 600px;
      width: 100%;
    }
    h1 { margin: 0 0 10px; color: #667eea; font-size: 28px; }
    .success { color: #10b981; font-size: 48px; margin-bottom: 20px; }
    .info { background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .file-list { list-style: none; padding: 0; margin: 15px 0; }
    .file-list li { padding: 8px 0; border-bottom: 1px solid #e5e7eb; display: flex; align-items: center; }
    .file-list li:before { content: '📄'; margin-right: 8px; }
    .note { background: #fef3c7; color: #92400e; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #f59e0b; }
    .download-btn { 
      display: inline-block;
      background: #667eea;
      color: white;
      padding: 12px 24px;
      border-radius: 8px;
      text-decoration: none;
      margin-top: 20px;
      font-weight: 600;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="success">✅</div>
    <h1>Multi-Page App Generated!</h1>
    <p>Your ${pageCount}-page application with ${files.length} files is ready.</p>
    
    <div class="info">
      <strong>📦 What was created:</strong>
      <ul class="file-list">
        ${pages.slice(0, 6).map(f => `<li>${f.path.split('/').pop()}</li>`).join('')}
        ${pages.length > 6 ? `<li>...and ${pages.length - 6} more pages</li>` : ''}
      </ul>
      
      <strong>🧩 Components:</strong>
      <ul class="file-list">
        ${components.slice(0, 4).map(f => `<li>${f.path.split('/').pop()}</li>`).join('')}
        ${components.length > 4 ? `<li>...and ${components.length - 4} more</li>` : ''}
      </ul>
    </div>
    
    <div class="note">
      <strong>⚠️ Why no live preview?</strong><br>
      Multi-page apps with React Router require a proper development server to work correctly. 
      The navigation, routing, and page transitions need a full build environment.
    </div>
    
    <p><strong>Next steps:</strong></p>
    <ol>
      <li>Click <strong>"My Projects"</strong> to access the full editor</li>
      <li>Download the files and run <code>npm install && npm start</code></li>
      <li>Or deploy directly to Vercel/Netlify</li>
    </ol>
  </div>
</body>
</html>
    `.trim();
  };

  const generatePreviewHtml = (appCode, files) => {
    // Find CSS file
    const cssFile = files.find(f => f.path.includes('.css'));
    const cssContent = cssFile?.content || '';

    // For preview, create a super simple single-page version
    // Strip ALL imports and just render basic content
    let cleanCode = appCode
      .split('\n')
      .filter(line => !line.trim().startsWith('import '))
      .filter(line => !line.trim().startsWith('export '))
      .join('\n');

    // Simple fallback if code is empty
    if (cleanCode.trim().length < 50) {
      cleanCode = `function PreviewComponent() {
        return (
          <div style={{padding: '40px', fontFamily: 'system-ui'}}>
            <h1>✨ Generated Successfully!</h1>
            <p>Your multi-page app with ${files.length} files is ready.</p>
            <p>Click "Open in Editor" to see all files and full functionality.</p>
          </div>
        );
      }`;
    } else {
      // Replace the function declaration
      cleanCode = cleanCode.replace(/function\s+\w+\s*\(/, 'function PreviewComponent(');
      cleanCode = cleanCode.replace(/const\s+\w+\s*=\s*\(/, 'const PreviewComponent = (');
    }

    return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <style>
    body { margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; }
    * { box-sizing: border-box; }
    ${cssContent}
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    const { useState, useEffect } = React;
    
    ${cleanCode}
    
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<PreviewComponent />);
  </script>
</body>
</html>
    `.trim();
  };

  const downloadProject = async () => {
    if (!generatedFiles.length) return;
    
    try {
      // Dynamically import JSZip
      const JSZip = (await import('jszip')).default;
      const zip = new JSZip();
      
      // Add all files to ZIP maintaining directory structure
      generatedFiles.forEach(file => {
        zip.file(file.path, file.content || '');
      });
      
      // Generate ZIP file
      const content = await zip.generateAsync({ type: 'blob' });
      
      // Download
      const url = URL.createObjectURL(content);
      const a = document.createElement('a');
      a.href = url;
      a.download = `digital-ninja-project-${Date.now()}.zip`;
      a.click();
      URL.revokeObjectURL(url);
      
      toast.success(`Downloaded ${generatedFiles.length} files as ZIP!`);
    } catch (error) {
      console.error('ZIP download error:', error);
      // Fallback to individual file download
      generatedFiles.forEach(file => {
        const blob = new Blob([file.content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = file.path.split('/').pop();
        a.click();
        URL.revokeObjectURL(url);
      });
      toast.success(`Downloaded ${generatedFiles.length} files individually`);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      {/* FULL SCREEN Logo Background */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <img 
          src="/digital-ninja-logo.png" 
          alt=""
          className="w-full h-full object-cover opacity-15"
          style={{ filter: 'brightness(0.8)' }}
        />
        <div className="absolute inset-0 bg-gradient-to-br from-[#1c1c1e]/90 via-[#2d1b4e]/85 to-[#1c1c1e]/90"></div>
      </div>

      {/* Content */}
      <div className="relative z-10 min-h-screen">
        <div className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-between mb-4">
              <button
                onClick={() => {
                  setGeneratedFiles([]);
                  setProgressLog([]);
                  setPrompt('');
                  setChatMessage('');
                  setCurrentProjectId(null);
                  setShowPreview(false);
                  setGenerating(false);
                  setAiSummary('');
                  setChatMode(false);
                }}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-all"
              >
                🏠 New Project
              </button>
              <button
                onClick={() => navigate('/projects')}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-all"
              >
                📁 My Projects
              </button>
            </div>
            <p className="text-2xl text-gray-300 font-medium mb-2">
              Can you imagine it?
            </p>
            <p className="text-4xl font-bold bg-gradient-to-r from-[#9b00e8] via-[#ff4500] to-[#9b00e8] bg-clip-text text-transparent">
              Build it here.
            </p>
            <p className="text-sm text-gray-400 mt-2">
              GPT-4o • Real-time Generation • Live Preview • Multi-Page Apps
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Input & Progress */}
            <div className="space-y-4">
              <div className="bg-gray-900/60 backdrop-blur-lg border border-gray-800 rounded-xl p-6 shadow-2xl">
                <label className="block text-lg font-semibold text-gray-200 mb-4">
                  What do you want to build?
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Example: Build a professional restaurant website with menu pages, about section, image gallery, customer reviews, and contact form"
                  className="w-full h-40 px-4 py-3 bg-gray-800/80 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-[#00ff41] focus:ring-2 focus:ring-[#00ff41]/50 resize-none"
                  disabled={generating}
                />
                
                <button
                  onClick={handleBuild}
                  disabled={generating || !prompt.trim()}
                  className="w-full mt-4 h-14 bg-gradient-to-r from-[#00ff41] to-[#00d4ff] hover:from-[#00cc35] hover:to-[#00b8e6] text-black font-bold text-lg rounded-xl shadow-lg shadow-[#00ff41]/30 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
                >
                  {generating ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      Build with AI
                    </>
                  )}
                </button>

                {generatedFiles.length > 0 && !generating && (
                  <>
                    <div className="mt-4 grid grid-cols-3 gap-2">
                      <button
                        onClick={() => setShowPreview(!showPreview)}
                        className="h-12 bg-gray-800 hover:bg-gray-700 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-all"
                      >
                        {showPreview ? <Code className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        {showPreview ? 'Code' : 'Preview'}
                      </button>
                      <button
                        onClick={downloadProject}
                        className="h-12 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-all"
                        title="Download as ZIP"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        Download
                      </button>
                      <button
                        onClick={() => currentProjectId && navigate(`/editor/${currentProjectId}`)}
                        className="h-12 bg-[#9b00e8] hover:bg-[#8800d4] text-white font-semibold rounded-lg flex items-center justify-center gap-2 transition-all"
                      >
                        <FileCode className="w-4 h-4" />
                        Editor
                      </button>
                    </div>
                    
                    {/* AI Summary */}
                    {aiSummary && (
                      <div className="mt-4 p-6 bg-gradient-to-br from-[#1e3a8a]/40 to-[#312e81]/40 rounded-lg border border-[#00ff41]/30">
                        <h3 className="text-lg font-bold text-[#00ff41] mb-3 flex items-center gap-2">
                          <Sparkles className="w-5 h-5" />
                          AI Summary
                        </h3>
                        <div className="text-gray-200 whitespace-pre-line text-sm leading-relaxed">
                          {aiSummary}
                        </div>
                      </div>
                    )}
                    
                    {/* Continue Working Chat */}
                    <div className="mt-4 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                      <div className="flex items-center justify-between mb-3">
                        <label className="text-sm font-medium text-gray-300">
                          💬 Continue working on this project:
                        </label>
                        <div className="flex gap-2">
                          <button
                            onClick={() => setChatMode(false)}
                            className={`px-3 py-1 text-xs rounded transition-all ${!chatMode ? 'bg-[#9b00e8] text-white' : 'bg-gray-700 text-gray-400'}`}
                          >
                            🔨 Rebuild
                          </button>
                          <button
                            onClick={() => setChatMode(true)}
                            className={`px-3 py-1 text-xs rounded transition-all ${chatMode ? 'bg-[#00ff41] text-black' : 'bg-gray-700 text-gray-400'}`}
                          >
                            💭 Brainstorm
                          </button>
                        </div>
                      </div>
                      
                      <div className="flex gap-2">
                        <textarea
                          value={chatMode ? chatMessage : prompt}
                          onChange={(e) => chatMode ? setChatMessage(e.target.value) : setPrompt(e.target.value)}
                          placeholder={chatMode 
                            ? "Ask questions: 'What features should I add?' 'How can I improve this?' 'What's missing?'"
                            : "Request changes: 'Add a contact page' 'Change colors to blue' 'Fix the preview'"}
                          className="flex-1 h-20 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-[#9b00e8] focus:ring-2 focus:ring-[#9b00e8]/50 resize-none text-sm"
                          disabled={generating}
                        />
                        <button
                          onClick={() => chatMode ? handleChat() : handleBuild()}
                          disabled={generating || (chatMode ? !chatMessage.trim() : !prompt.trim())}
                          className={`h-20 px-6 ${chatMode 
                            ? 'bg-gradient-to-r from-[#00ff41] to-[#00d4ff]' 
                            : 'bg-gradient-to-r from-[#9b00e8] to-[#ff4500]'} hover:opacity-90 text-${chatMode ? 'black' : 'white'} font-semibold rounded-lg disabled:opacity-50 transition-all`}
                        >
                          {generating ? <Loader2 className="w-5 h-5 animate-spin" /> : (chatMode ? '💭 Chat' : '🔨 Rebuild')}
                        </button>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">
                        {chatMode 
                          ? "💡 Brainstorm mode: Ask questions and get suggestions without rebuilding" 
                          : "🔨 Rebuild mode: Will regenerate all files based on your request"}
                      </p>
                    </div>
                  </>
                )}
              </div>

              {/* Progress Log */}
              {progressLog.length > 0 && (
                <div className="bg-gray-900/60 backdrop-blur-lg border border-gray-800 rounded-xl p-6 shadow-2xl">
                  <h3 className="text-lg font-semibold text-gray-200 mb-4 flex items-center gap-2">
                    <FileCode className="w-5 h-5 text-[#00ff41]" />
                    Build Progress
                  </h3>
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {progressLog.map((log, idx) => (
                      <div
                        key={idx}
                        className={`flex items-start gap-3 p-3 rounded-lg text-sm ${
                          log.type === 'error' ? 'bg-red-900/20 text-red-300' :
                          log.type === 'success' ? 'bg-green-900/20 text-green-300' :
                          log.type === 'file' ? 'bg-blue-900/20 text-blue-300' :
                          'bg-gray-800/50 text-gray-300'
                        }`}
                      >
                        {log.type === 'success' ? <CheckCircle className="w-4 h-4 mt-0.5" /> :
                         log.type === 'error' ? <AlertCircle className="w-4 h-4 mt-0.5" /> :
                         log.type === 'file' ? <FileCode className="w-4 h-4 mt-0.5" /> :
                         <div className="w-2 h-2 mt-1.5 rounded-full bg-[#00ff41] animate-pulse"></div>
                        }
                        <div className="flex-1">
                          <p>{log.message}</p>
                          <p className="text-xs text-gray-500 mt-1">{log.timestamp}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right: Preview/Code */}
            <div className="bg-gray-900/60 backdrop-blur-lg border border-gray-800 rounded-xl p-6 shadow-2xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-200 flex items-center gap-2">
                  {showPreview ? (
                    <>
                      <Eye className="w-5 h-5 text-[#00d4ff]" />
                      Live Preview
                    </>
                  ) : (
                    <>
                      <Code className="w-5 h-5 text-[#9b00e8]" />
                      Generated Code
                    </>
                  )}
                </h3>
                {generatedFiles.length > 0 && (
                  <span className="text-sm text-gray-400">
                    {generatedFiles.length} files
                  </span>
                )}
              </div>

              {!generatedFiles.length ? (
                <div className="h-[600px] flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <Sparkles className="w-16 h-16 mx-auto mb-4 opacity-30" />
                    <p className="text-lg">Your app will appear here</p>
                    <p className="text-sm mt-2">Enter a description and click "Build with AI"</p>
                  </div>
                </div>
              ) : showPreview ? (
                <div className="h-[600px] bg-white rounded-lg overflow-hidden shadow-inner">
                  <iframe
                    ref={iframeRef}
                    srcDoc={previewHtml}
                    className="w-full h-full border-0"
                    title="App Preview"
                    sandbox="allow-scripts allow-same-origin"
                  />
                </div>
              ) : (
                <div className="h-[600px] overflow-y-auto">
                  <div className="space-y-4">
                    {generatedFiles.map((file, idx) => (
                      <div key={idx} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-mono text-[#00ff41]">{file.path}</span>
                          <span className="text-xs text-gray-500">{file.content?.length || 0} chars</span>
                        </div>
                        <pre className="text-xs text-gray-300 overflow-x-auto bg-gray-900 p-3 rounded">
                          <code>{file.content?.slice(0, 500)}{file.content?.length > 500 ? '...' : ''}</code>
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Examples */}
          <div className="mt-8 bg-gray-900/40 backdrop-blur-lg border border-gray-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-gray-200 mb-4">Try these examples:</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {[
                "Build a professional restaurant website with menu, gallery, and reservations",
                "Create an e-commerce store for gym supplements with product catalog and cart",
                "Build a natural medicine website with articles, testimonials, and contact form",
                "Create a portfolio website for a photographer with image galleries",
                "Build a SaaS landing page with pricing tiers and feature comparison",
                "Create a blog platform with article listings and reading experience"
              ].map((example, idx) => (
                <button
                  key={idx}
                  onClick={() => setPrompt(example)}
                  className="text-left p-4 bg-gray-800/50 hover:bg-gray-800 border border-gray-700 hover:border-[#00ff41]/50 rounded-lg transition-all text-sm text-gray-300 hover:text-white"
                  disabled={generating}
                >
                  💡 {example}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImprovedBuilder;
