import { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { RefreshCw, AlertCircle } from 'lucide-react';

const LivePreview = ({ files }) => {
  const [previewHtml, setPreviewHtml] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const iframeRef = useRef(null);

  useEffect(() => {
    generatePreview();
  }, [files]);

  const generatePreview = () => {
    setLoading(true);
    setError(null);

    try {
      // Find React files
      const appJs = files.find(f => f.path.includes('App.js'));
      const appCss = files.find(f => f.path.includes('App.css'));
      const indexCss = files.find(f => f.path.includes('index.css'));

      if (!appJs) {
        setError('No App.js file found');
        setLoading(false);
        return;
      }

      // Build HTML with inline React code
      const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Live Preview</title>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <style>
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
        'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
        sans-serif;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }
    #root {
      min-height: 100vh;
    }
    ${indexCss ? indexCss.content : ''}
    ${appCss ? appCss.content : ''}
  </style>
  <script>
    // Catch errors
    window.addEventListener('error', (e) => {
      document.body.innerHTML = \`
        <div style="padding: 20px; color: #e74c3c; font-family: monospace;">
          <h3>Error in Preview:</h3>
          <pre>\${e.message}</pre>
          <pre>\${e.error?.stack || ''}</pre>
        </div>
      \`;
    });

    console.log = function(...args) {
      window.parent.postMessage({ type: 'console.log', args }, '*');
    };
    
    console.error = function(...args) {
      window.parent.postMessage({ type: 'console.error', args }, '*');
    };
  </script>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    ${appJs.content}
    
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>
      `;

      setPreviewHtml(html);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    generatePreview();
    if (iframeRef.current) {
      iframeRef.current.src = iframeRef.current.src;
    }
  };

  // Listen for console messages from iframe
  useEffect(() => {
    const handleMessage = (event) => {
      if (event.data.type === 'console.error') {
        setError(event.data.args.join(' '));
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  return (
    <div className="h-full flex flex-col bg-white">
      <div className="bg-slate-800 px-6 py-3 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-500"></div>
          <span className="text-sm text-slate-300">Live Preview</span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleRefresh}
          disabled={loading}
          className="text-slate-300"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {error ? (
        <div className="flex-1 flex items-center justify-center bg-red-50 p-6">
          <div className="text-center max-w-md">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-red-900 mb-2">Preview Error</h3>
            <pre className="text-sm text-red-700 bg-red-100 p-3 rounded overflow-auto text-left">
              {error}
            </pre>
            <Button onClick={handleRefresh} className="mt-4" variant="outline">
              Try Again
            </Button>
          </div>
        </div>
      ) : (
        <iframe
          ref={iframeRef}
          srcDoc={previewHtml}
          className="flex-1 w-full border-0"
          sandbox="allow-scripts allow-same-origin"
          title="Live Preview"
        />
      )}
    </div>
  );
};

export default LivePreview;
