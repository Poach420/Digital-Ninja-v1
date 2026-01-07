import { useState, useEffect } from 'react';
import DashboardLayout from '../components/DashboardLayout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import api from '../utils/api';
import { Check, CreditCard, Zap } from 'lucide-react';

const Billing = () => {
  const [plans, setPlans] = useState([]);
  const [currentPlan, setCurrentPlan] = useState('free');
  const [loading, setLoading] = useState('');

  useEffect(() => {
    loadPlans();
    loadCurrentPlan();
  }, []);

  const loadPlans = async () => {
    try {
      const response = await api.get('/billing/plans');
      setPlans(response.data);
    } catch (error) {
      toast.error('Failed to load plans');
    }
  };

  const loadCurrentPlan = async () => {
    try {
      const response = await api.get('/teams/current');
      setCurrentPlan(response.data.plan);
    } catch (error) {
      console.error('Failed to load current plan');
    }
  };

  const handleSubscribe = async (planId) => {
    setLoading(planId);
    try {
      await api.post('/billing/subscribe', null, { params: { plan_id: planId } });
      toast.success(`Subscribed to ${planId} plan!`);
      setCurrentPlan(planId);
    } catch (error) {
      toast.error('Subscription failed');
    } finally {
      setLoading('');
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8" data-testid="billing-page">
        <div>
          <h1 className="text-3xl font-heading font-bold tracking-tight text-primary">Billing & Plans</h1>
          <p className="text-muted-foreground mt-2">Choose the plan that's right for you</p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {plans.map((plan) => (
            <Card
              key={plan.plan_id}
              className={`relative ${
                currentPlan === plan.plan_id ? 'border-accent shadow-lg' : ''
              }`}
              data-testid={`plan-card-${plan.plan_id}`}
            >
              {currentPlan === plan.plan_id && (
                <Badge className="absolute -top-3 left-1/2 -translate-x-1/2" data-testid="current-plan-badge">
                  Current Plan
                </Badge>
              )}
              <CardHeader>
                <CardTitle className="font-heading text-2xl">{plan.name}</CardTitle>
                <CardDescription>
                  <div className="mt-4">
                    <span className="text-4xl font-bold text-primary">R{plan.price_zar}</span>
                    <span className="text-muted-foreground">/month</span>
                  </div>
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <ul className="space-y-3">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <Check className="h-5 w-5 text-accent flex-shrink-0 mt-0.5" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button
                  className="w-full"
                  variant={currentPlan === plan.plan_id ? 'outline' : 'default'}
                  onClick={() => handleSubscribe(plan.plan_id)}
                  disabled={currentPlan === plan.plan_id || loading === plan.plan_id}
                  data-testid={`subscribe-${plan.plan_id}-button`}
                >
                  {loading === plan.plan_id ? 'Processing...' : currentPlan === plan.plan_id ? 'Current Plan' : 'Subscribe'}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="font-heading">Payment Method</CardTitle>
            <CardDescription>Manage your payment information</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between p-4 border border-border rounded-lg">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded bg-accent/10 flex items-center justify-center">
                  <CreditCard className="h-5 w-5 text-accent" />
                </div>
                <div>
                  <p className="font-medium">Payment via Peach Payments</p>
                  <p className="text-sm text-muted-foreground">ZAR currency support</p>
                </div>
              </div>
              <Badge variant="outline">Test Mode</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default Billing;