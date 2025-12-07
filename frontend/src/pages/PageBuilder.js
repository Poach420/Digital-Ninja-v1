import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import DashboardLayout from '../components/DashboardLayout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import api from '../utils/api';
import { Save, Eye, Plus, Type, Image, SquareIcon, Layout } from 'lucide-react';

const PageBuilder = () => {
  const { pageId } = useParams();
  const navigate = useNavigate();
  const [pageName, setPageName] = useState('Untitled Page');
  const [components, setComponents] = useState([]);
  const [selectedComponent, setSelectedComponent] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (pageId) {
      loadPage();
    }
  }, [pageId]);

  const loadPage = async () => {
    try {
      const response = await api.get(`/pages/${pageId}`);
      setPageName(response.data.name);
      setComponents(response.data.content_json.components || []);
    } catch (error) {
      toast.error('Failed to load page');
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const data = {
        name: pageName,
        content_json: { components },
      };

      if (pageId) {
        await api.put(`/pages/${pageId}`, data);
        toast.success('Page updated successfully');
      } else {
        const response = await api.post('/pages', data);
        toast.success('Page created successfully');
        navigate(`/builder/${response.data.page_id}`);
      }
    } catch (error) {
      toast.error('Failed to save page');
    } finally {
      setLoading(false);
    }
  };

  const addComponent = (type) => {
    const newComponent = {
      id: Date.now().toString(),
      type,
      content: type === 'text' ? 'Edit this text' : type === 'heading' ? 'Heading Text' : '',
      styles: {},
    };
    setComponents([...components, newComponent]);
  };

  const updateComponent = (id, updates) => {
    setComponents(components.map(c => c.id === id ? { ...c, ...updates } : c));
  };

  const deleteComponent = (id) => {
    setComponents(components.filter(c => c.id !== id));
    setSelectedComponent(null);
  };

  return (
    <DashboardLayout>
      <div className="h-[calc(100vh-8rem)]" data-testid="page-builder">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1">
            <Input
              value={pageName}
              onChange={(e) => setPageName(e.target.value)}
              className="max-w-md font-heading text-lg"
              data-testid="page-name-input"
            />
          </div>
          <div className="flex gap-2">
            <Button variant="outline" data-testid="preview-button">
              <Eye className="mr-2 h-4 w-4" />
              Preview
            </Button>
            <Button onClick={handleSave} disabled={loading} data-testid="save-page-button">
              <Save className="mr-2 h-4 w-4" />
              {loading ? 'Saving...' : 'Save'}
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-[280px_1fr_300px] gap-4 h-full">
          {/* Components Panel */}
          <Card className="overflow-y-auto">
            <CardContent className="p-4">
              <h3 className="font-heading font-semibold mb-4">Components</h3>
              <div className="space-y-2">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => addComponent('heading')}
                  data-testid="add-heading-component"
                >
                  <Type className="mr-2 h-4 w-4" />
                  Heading
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => addComponent('text')}
                  data-testid="add-text-component"
                >
                  <Type className="mr-2 h-4 w-4" />
                  Text
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => addComponent('image')}
                  data-testid="add-image-component"
                >
                  <Image className="mr-2 h-4 w-4" />
                  Image
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => addComponent('button')}
                  data-testid="add-button-component"
                >
                  <SquareIcon className="mr-2 h-4 w-4" />
                  Button
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => addComponent('section')}
                  data-testid="add-section-component"
                >
                  <Layout className="mr-2 h-4 w-4" />
                  Section
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Canvas */}
          <Card className="overflow-y-auto bg-slate-50">
            <CardContent className="p-8">
              {components.length === 0 ? (
                <div className="flex items-center justify-center h-64 border-2 border-dashed border-border rounded-lg">
                  <div className="text-center">
                    <Plus className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                    <p className="text-muted-foreground">Add components to start building</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4 min-h-[400px] bg-white p-8 rounded-lg shadow-sm">
                  {components.map((component) => (
                    <div
                      key={component.id}
                      className={`p-4 border-2 rounded cursor-pointer transition-colors ${
                        selectedComponent?.id === component.id
                          ? 'border-accent bg-accent/5'
                          : 'border-transparent hover:border-border'
                      }`}
                      onClick={() => setSelectedComponent(component)}
                      data-testid={`canvas-component-${component.type}`}
                    >
                      {component.type === 'heading' && (
                        <h2 className="text-2xl font-heading font-bold">{component.content}</h2>
                      )}
                      {component.type === 'text' && <p>{component.content}</p>}
                      {component.type === 'button' && (
                        <button className="px-4 py-2 bg-accent text-white rounded">{component.content || 'Button'}</button>
                      )}
                      {component.type === 'image' && (
                        <div className="bg-secondary h-48 flex items-center justify-center rounded">
                          <Image className="h-12 w-12 text-muted-foreground" />
                        </div>
                      )}
                      {component.type === 'section' && (
                        <div className="border-2 border-dashed border-border p-8 rounded">
                          <p className="text-center text-muted-foreground">Section Container</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Properties Panel */}
          <Card className="overflow-y-auto">
            <CardContent className="p-4">
              <h3 className="font-heading font-semibold mb-4">Properties</h3>
              {selectedComponent ? (
                <div className="space-y-4">
                  <div>
                    <Label>Content</Label>
                    <Input
                      value={selectedComponent.content}
                      onChange={(e) => updateComponent(selectedComponent.id, { content: e.target.value })}
                      data-testid="component-content-input"
                    />
                  </div>
                  <Button
                    variant="destructive"
                    className="w-full"
                    onClick={() => deleteComponent(selectedComponent.id)}
                    data-testid="delete-component-button"
                  >
                    Delete Component
                  </Button>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Select a component to edit its properties</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default PageBuilder;