import { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import api from '../utils/api';
import { CheckCircle, XCircle, AlertCircle, RefreshCw } from 'lucide-react';

const Diagnostics = () => {
  const [checks, setChecks] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDiagnostics();
  }, []);

  const loadDiagnostics = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/diagnostics');
      setChecks(response.data);
    } catch (error) {
      console.error('Failed to load diagnostics');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
      case 'configured':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'unhealthy':
      case 'not_configured':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'healthy':
      case 'configured':
        return <Badge className="bg-green-500">Operational</Badge>;
      case 'unhealthy':
      case 'not_configured':
        return <Badge variant="destructive">Needs Attention</Badge>;
      default:
        return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  const allHealthy = checks.every(c => c.status === 'healthy' || c.status === 'configured');

  return (
    <DashboardLayout>
      <div className="space-y-6" data-testid="diagnostics-page">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-heading font-bold tracking-tight text-primary">System Diagnostics</h1>
            <p className="text-muted-foreground mt-2">Monitor system health and integrations</p>
          </div>
          <Button onClick={loadDiagnostics} disabled={loading} data-testid="refresh-diagnostics">
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {allHealthy ? (
          <Alert className="border-green-500 bg-green-50" data-testid="all-systems-operational">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <AlertTitle>All Systems Operational</AlertTitle>
            <AlertDescription>
              All integrations and services are functioning correctly.
            </AlertDescription>
          </Alert>
        ) : (
          <Alert variant="destructive" data-testid="systems-need-attention">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Action Required</AlertTitle>
            <AlertDescription>
              Some services need configuration or are experiencing issues.
            </AlertDescription>
          </Alert>
        )}

        <div className="grid gap-4">
          {checks.map((check) => (
            <Card key={check.check_type} data-testid={`diagnostic-${check.check_type}`}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(check.status)}
                    <div>
                      <CardTitle className="font-heading text-lg capitalize">
                        {check.check_type.replace('_', ' ')}
                      </CardTitle>
                      <CardDescription>{check.details}</CardDescription>
                    </div>
                  </div>
                  {getStatusBadge(check.status)}
                </div>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-muted-foreground">
                  Last checked: {new Date(check.last_check).toLocaleString()}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Diagnostics;