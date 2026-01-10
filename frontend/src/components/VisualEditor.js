import { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Paintbrush, Type, Layout, Palette, Save, X } from 'lucide-react';
import { toast } from 'sonner';

/**
 * Visual Editor - Click to edit any element
 * Inspired by Replit's visual editor and Base44's instant styling
 */
const VisualEditor = ({ files, onFilesUpdate }) => {
    const [editMode, setEditMode] = useState(false);
    const [selectedElement, setSelectedElement] = useState(null);
    const [styles, setStyles] = useState({
        color: '#000000',
        backgroundColor: '#ffffff',
        fontSize: '16px',
        fontFamily: 'Arial',
        padding: '10px',
        margin: '0px',
        borderRadius: '0px'
    });
    const iframeRef = useRef(null);

    useEffect(() => {
        if (editMode && iframeRef.current) {
            setupEditableIframe();
        }
    }, [editMode, files]);

    const setupEditableIframe = () => {
        const iframe = iframeRef.current;
        if (!iframe || !iframe.contentWindow) return;

        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;

        // Inject click handlers into iframe
        const script = iframeDoc.createElement('script');
        script.textContent = `
      document.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        // Highlight selected element
        document.querySelectorAll('.editor-selected').forEach(el => {
          el.classList.remove('editor-selected');
        });
        e.target.classList.add('editor-selected');
        
        // Send element data to parent
        const computedStyle = window.getComputedStyle(e.target);
        window.parent.postMessage({
          type: 'element-selected',
          tagName: e.target.tagName,
          className: e.target.className,
          id: e.target.id,
          styles: {
            color: computedStyle.color,
            backgroundColor: computedStyle.backgroundColor,
            fontSize: computedStyle.fontSize,
            fontFamily: computedStyle.fontFamily,
            padding: computedStyle.padding,
            margin: computedStyle.margin,
            borderRadius: computedStyle.borderRadius
          }
        }, '*');
      });
    `;
        iframeDoc.body.appendChild(script);

        // Add visual editing styles
        const style = iframeDoc.createElement('style');
        style.textContent = `
      .editor-selected {
        outline: 3px solid #ff4500 !important;
        outline-offset: 2px;
        cursor: pointer !important;
      }
      * {
        cursor: pointer !important;
      }
    `;
        iframeDoc.head.appendChild(style);
    };

    useEffect(() => {
        const handleMessage = (event) => {
            if (event.data.type === 'element-selected') {
                setSelectedElement(event.data);
                setStyles({
                    color: event.data.styles.color || '#000000',
                    backgroundColor: event.data.styles.backgroundColor || '#ffffff',
                    fontSize: event.data.styles.fontSize || '16px',
                    fontFamily: event.data.styles.fontFamily || 'Arial',
                    padding: event.data.styles.padding || '10px',
                    margin: event.data.styles.margin || '0px',
                    borderRadius: event.data.styles.borderRadius || '0px'
                });
            }
        };

        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, []);

    const applyStyles = () => {
        if (!selectedElement) {
            toast.error('No element selected');
            return;
        }

        const iframe = iframeRef.current;
        if (!iframe) return;

        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        const element = iframeDoc.querySelector('.editor-selected');

        if (element) {
            element.style.color = styles.color;
            element.style.backgroundColor = styles.backgroundColor;
            element.style.fontSize = styles.fontSize;
            element.style.fontFamily = styles.fontFamily;
            element.style.padding = styles.padding;
            element.style.margin = styles.margin;
            element.style.borderRadius = styles.borderRadius;

            toast.success('Styles applied! Click Save to persist changes.');
        }
    };

    const saveChanges = async () => {
        // Extract styles from iframe and update CSS files
        const iframe = iframeRef.current;
        if (!iframe) return;

        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        const styleElement = iframeDoc.querySelector('style');

        if (styleElement) {
            const cssContent = styleElement.textContent;

            // Find or create CSS file
            const cssFile = files.find(f => f.path.includes('.css') || f.path.includes('App.css'));

            if (cssFile) {
                const updatedFiles = files.map(f => {
                    if (f.path === cssFile.path) {
                        return {
                            ...f,
                            content: cssContent
                        };
                    }
                    return f;
                });

                onFilesUpdate(updatedFiles);
                toast.success('Changes saved!');
            }
        }
    };

    const generatePreviewHtml = () => {
        const appFile = files.find(f => f.path.includes('App.js'));
        if (!appFile) return '';

        const cssFiles = files.filter(f => f.path.endsWith('.css'));
        const cssContent = cssFiles.map(f => f.content).join('\n');

        return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <style>
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
    #root { min-height: 100vh; }
    ${cssContent}
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel">
    const { useState, useEffect, useRef } = React;
    ${appFile.content.replace(/import\s+.*?from\s+['"].*?['"];?\s*/g, '').replace(/export\s+default\s+/g, '').replace(/export\s+/g, '')}
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
  </script>
</body>
</html>
    `;
    };

    return (
        <div className="h-full flex">
            {/* Preview Area */}
            <div className="flex-1 relative">
                <div className="absolute top-4 left-4 z-10 flex gap-2">
                    <Button
                        onClick={() => setEditMode(!editMode)}
                        variant={editMode ? "default" : "outline"}
                        className={editMode ? "bg-orange-500 hover:bg-orange-600" : ""}
                    >
                        <Paintbrush className="h-4 w-4 mr-2" />
                        {editMode ? 'Edit Mode ON' : 'Edit Mode OFF'}
                    </Button>
                    {editMode && (
                        <Button onClick={saveChanges} variant="outline">
                            <Save className="h-4 w-4 mr-2" />
                            Save Changes
                        </Button>
                    )}
                </div>

                <iframe
                    ref={iframeRef}
                    srcDoc={generatePreviewHtml()}
                    className="w-full h-full border-0"
                    sandbox="allow-scripts allow-same-origin"
                    title="Visual Editor Preview"
                />
            </div>

            {/* Style Panel */}
            {editMode && selectedElement && (
                <Card className="w-80 bg-slate-800 border-slate-700 p-4 space-y-4 overflow-y-auto">
                    <div className="flex items-center justify-between">
                        <h3 className="text-white font-semibold flex items-center gap-2">
                            <Palette className="h-5 w-5" />
                            Element Styles
                        </h3>
                        <Button variant="ghost" size="sm" onClick={() => setSelectedElement(null)}>
                            <X className="h-4 w-4" />
                        </Button>
                    </div>

                    <div className="space-y-3">
                        <div className="text-sm text-slate-400">
                            {selectedElement.tagName} {selectedElement.className && `.${selectedElement.className}`}
                        </div>

                        {/* Color */}
                        <div>
                            <label className="text-sm text-slate-300 block mb-1">Text Color</label>
                            <input
                                type="color"
                                value={styles.color}
                                onChange={(e) => setStyles({ ...styles, color: e.target.value })}
                                className="w-full h-10 rounded cursor-pointer"
                            />
                        </div>

                        {/* Background */}
                        <div>
                            <label className="text-sm text-slate-300 block mb-1">Background</label>
                            <input
                                type="color"
                                value={styles.backgroundColor}
                                onChange={(e) => setStyles({ ...styles, backgroundColor: e.target.value })}
                                className="w-full h-10 rounded cursor-pointer"
                            />
                        </div>

                        {/* Font Size */}
                        <div>
                            <label className="text-sm text-slate-300 block mb-1">Font Size</label>
                            <input
                                type="text"
                                value={styles.fontSize}
                                onChange={(e) => setStyles({ ...styles, fontSize: e.target.value })}
                                className="w-full px-3 py-2 bg-slate-700 text-white rounded"
                                placeholder="16px"
                            />
                        </div>

                        {/* Font Family */}
                        <div>
                            <label className="text-sm text-slate-300 block mb-1">Font Family</label>
                            <select
                                value={styles.fontFamily}
                                onChange={(e) => setStyles({ ...styles, fontFamily: e.target.value })}
                                className="w-full px-3 py-2 bg-slate-700 text-white rounded"
                            >
                                <option value="Arial">Arial</option>
                                <option value="Helvetica">Helvetica</option>
                                <option value="Times New Roman">Times New Roman</option>
                                <option value="Courier New">Courier New</option>
                                <option value="Georgia">Georgia</option>
                                <option value="Verdana">Verdana</option>
                            </select>
                        </div>

                        {/* Padding */}
                        <div>
                            <label className="text-sm text-slate-300 block mb-1">Padding</label>
                            <input
                                type="text"
                                value={styles.padding}
                                onChange={(e) => setStyles({ ...styles, padding: e.target.value })}
                                className="w-full px-3 py-2 bg-slate-700 text-white rounded"
                                placeholder="10px"
                            />
                        </div>

                        {/* Border Radius */}
                        <div>
                            <label className="text-sm text-slate-300 block mb-1">Border Radius</label>
                            <input
                                type="text"
                                value={styles.borderRadius}
                                onChange={(e) => setStyles({ ...styles, borderRadius: e.target.value })}
                                className="w-full px-3 py-2 bg-slate-700 text-white rounded"
                                placeholder="0px"
                            />
                        </div>

                        <Button onClick={applyStyles} className="w-full bg-orange-500 hover:bg-orange-600">
                            Apply Styles
                        </Button>
                    </div>
                </Card>
            )}
        </div>
    );
};

export default VisualEditor;
