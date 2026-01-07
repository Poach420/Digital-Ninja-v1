import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import api from '../utils/api';
import { Layout, Users, FileText, Plus, TrendingUp } from 'lucide-react';

const Dashboard = () => {
  const [pages, setPages] = useState([]);
  const [team, setTeam] = useState(null);
  const [members, setMembers] = useState([]);
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [pagesRes, teamRes, membersRes] = await Promise.all([
        api.get('/pages'),
        api.get('/teams/current'),
        api.get('/teams/members'),
      ]);
      setPages(pagesRes.data);
      setTeam(teamRes.data);
      setMembers(membersRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8" data-testid="dashboard-page">
        <div>
          <h1 className="text-3xl font-heading font-bold tracking-tight text-primary">Welcome back, {user.name}!</h1>
          <p className="text-muted-foreground mt-2">Here's what's happening with your projects</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card className="border-l-4 border-l-accent">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Pages</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{pages.length}</div>
              <p className="text-xs text-muted-foreground mt-1">Pages created</p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-accent">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Team Members</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{members.length}</div>
              <p className="text-xs text-muted-foreground mt-1">Active members</p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-accent">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Current Plan</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold capitalize">{team?.plan || 'Free'}</div>
              <p className="text-xs text-muted-foreground mt-1">Subscription</p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-accent">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Published</CardTitle>
              <Layout className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{pages.filter(p => p.published).length}</div>
              <p className="text-xs text-muted-foreground mt-1">Live pages</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="font-heading">Recent Pages</CardTitle>
              <CardDescription>Your latest page creations</CardDescription>
            </CardHeader>
            <CardContent>
              {pages.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-muted-foreground mb-4">No pages yet. Create your first one!</p>
                  <Link to="/builder">
                    <Button data-testid="create-first-page">
                      <Plus className="mr-2 h-4 w-4" />
                      Create Page
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="space-y-3">
                  {pages.slice(0, 5).map((page) => (
                    <Link
                      key={page.page_id}
                      to={`/builder/${page.page_id}`}
                      className="flex items-center justify-between p-3 rounded-lg hover:bg-secondary transition-colors"
                      data-testid={`page-item-${page.page_id}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded bg-accent/10 flex items-center justify-center">
                          <Layout className="h-5 w-5 text-accent" />
                        </div>
                        <div>
                          <p className="font-medium">{page.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {page.published ? 'Published' : 'Draft'}
                          </p>
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(page.updated_at).toLocaleDateString()}
                      </div>
                    </Link>
                  ))}
                  {pages.length > 5 && (
                    <Link to="/builder" className="block text-center text-sm text-accent hover:text-accent/80 pt-2">
                      View all pages
                    </Link>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="font-heading">Quick Actions</CardTitle>
              <CardDescription>Get started with these actions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Link to="/builder">
                <Button className="w-full justify-start" variant="outline" data-testid="quick-action-new-page">
                  <Plus className="mr-2 h-4 w-4" />
                  Create New Page
                </Button>
              </Link>
              <Link to="/team">
                <Button className="w-full justify-start" variant="outline" data-testid="quick-action-invite">
                  <Users className="mr-2 h-4 w-4" />
                  Invite Team Member
                </Button>
              </Link>
              <Link to="/billing">
                <Button className="w-full justify-start" variant="outline" data-testid="quick-action-upgrade">
                  <TrendingUp className="mr-2 h-4 w-4" />
                  Upgrade Plan
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Dashboard;