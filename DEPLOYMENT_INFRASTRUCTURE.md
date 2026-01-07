# Digital Ninja AI Builder - Deployment Infrastructure Guide

## Overview
Complete multi-tenant deployment system for hosting generated applications on YOUR infrastructure.

---

## Architecture

### 1. Multi-Tier Hosting

**FREE TIER**
- Subdomain: `[project-id].digitalninja.co.za`
- Frontend: Your Vercel account
- Backend: Your Render account (free tier)
- Database: Shared MongoDB Atlas cluster
- SSL: Automatic via Let's Encrypt
- Limits: 3 active deployments per user

**PRO TIER (R299/month)**
- Custom subdomain choices
- Dedicated Render instance
- Dedicated MongoDB database
- Priority deployment queue
- Limits: 20 active deployments

**AGENCY TIER (R999/month)**
- Custom domains with SSL
- Premium Render instances
- Dedicated MongoDB cluster
- White-label deployments
- Unlimited deployments
- API access

###

 2. Infrastructure Setup

**Required Accounts (Owner/Admin)**
```
1. Vercel Account
   - Team ID: VERCEL_TEAM_ID
   - API Token: VERCEL_TOKEN
   - Used for: Frontend deployments

2. Render Account
   - API Key: RENDER_API_KEY
   - Used for: Backend deployments

3. MongoDB Atlas
   - Public Key: MONGODB_ATLAS_PUBLIC_KEY
   - Private Key: MONGODB_ATLAS_PRIVATE_KEY
   - Project ID: MONGODB_ATLAS_PROJECT_ID
   - Used for: Database provisioning

4. DNS Provider (Cloudflare recommended)
   - API Token: CLOUDFLARE_API_TOKEN
   - Zone ID: CLOUDFLARE_ZONE_ID
   - Used for: Subdomain management
```

**Environment Variables (.env)**
```env
# Deployment Infrastructure
VERCEL_TOKEN=your_vercel_api_token
VERCEL_TEAM_ID=your_team_id
RENDER_API_KEY=your_render_api_key
MONGODB_ATLAS_PUBLIC_KEY=your_atlas_public_key
MONGODB_ATLAS_PRIVATE_KEY=your_atlas_private_key
MONGODB_ATLAS_PROJECT_ID=your_project_id
CLOUDFLARE_API_TOKEN=your_cloudflare_token
CLOUDFLARE_ZONE_ID=your_zone_id
BASE_DOMAIN=digitalninja.co.za

# Deployment Limits
FREE_TIER_LIMIT=3
PRO_TIER_LIMIT=20
AGENCY_TIER_LIMIT=999
```

---

## 3. Deployment Flow

### User Deploys Project

**Step 1: User clicks "Deploy" in Monaco Editor**
```javascript
// Frontend action
POST /api/deployments/deploy
{
  "project_id": "proj_abc123",
  "tier": "free"
}
```

**Step 2: Backend processes deployment**
```python
# deployment_service.py handles:
1. Create MongoDB database
2. Deploy backend to Render with DB connection
3. Deploy frontend to Vercel with API URL
4. Configure DNS subdomain
5. Setup SSL certificate
6. Return deployment URLs
```

**Step 3: User receives live URLs**
```json
{
  "status": "deployed",
  "urls": {
    "app": "https://proj-abc123.digitalninja.co.za",
    "api": "https://proj-abc123-api.onrender.com"
  },
  "deployment_id": "deploy_xyz789"
}
```

---

## 4. DNS & SSL Configuration

### Cloudflare Setup

**Add Subdomain DNS Record**
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{
    "type": "CNAME",
    "name": "proj-abc123",
    "content": "cname.vercel-dns.com",
    "ttl": 1,
    "proxied": true
  }'
```

**SSL Certificate**
- Automatic via Cloudflare Proxy
- Or Let's Encrypt via Vercel
- Forced HTTPS redirect

---

## 5. Admin Dashboard Features

### Deployment Management

**View All Deployments**
```
GET /api/admin/deployments

Returns:
- Total active deployments
- Deployments by tier
- Resource usage per deployment
- Cost breakdown
```

**Monitor Resource Usage**
```
GET /api/admin/deployments/{deployment_id}/metrics

Returns:
- Frontend bandwidth (GB)
- Backend compute hours
- Database storage (MB)
- API requests count
```

**Set Deployment Limits**
```
PUT /api/admin/settings/limits
{
  "free_tier_max": 3,
  "pro_tier_max": 20,
  "max_bandwidth_gb": 100,
  "max_db_size_mb": 500
}
```

**Delete Deployments**
```
DELETE /api/admin/deployments/{deployment_id}

Actions:
- Remove Vercel deployment
- Delete Render service
- Drop MongoDB database
- Remove DNS records
```

---

## 6. Deployment Automation

### One-Click Deploy Button

**Frontend Component**
```javascript
// In ProjectEditor.js
const handleDeploy = async () => {
  setDeploying(true);
  
  try {
    const response = await api.post('/deployments/deploy', {
      project_id: projectId,
      tier: userTier
    });
    
    if (response.data.status === 'deployed') {
      toast.success(`Deployed to ${response.data.urls.app}`);
      setDeploymentUrl(response.data.urls.app);
    }
  } catch (error) {
    toast.error('Deployment failed');
  } finally {
    setDeploying(false);
  }
};

<Button onClick={handleDeploy} disabled={deploying}>
  {deploying ? 'Deploying...' : 'Deploy to Production'}
</Button>
```

### GitHub Actions Workflow (Included)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Digital Ninja

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy Frontend
        run: |
          vercel --token=${{ secrets.VERCEL_TOKEN }} --prod
      
      - name: Deploy Backend
        run: |
          render deploy --api-key=${{ secrets.RENDER_API_KEY }}
```

### Environment Variable Management

**Set Variables via UI**
```javascript
// Deployment settings page
POST /api/deployments/{deployment_id}/env
{
  "variables": {
    "STRIPE_KEY": "sk_live_...",
    "SMTP_HOST": "smtp.gmail.com",
    "API_KEY": "..."
  }
}
```

### Rollback Capabilities

```javascript
// Rollback to previous deployment
POST /api/deployments/{deployment_id}/rollback
{
  "target_version": "v1.2.0"
}

// Vercel automatic rollback
// Render service restart
// MongoDB snapshot restore
```

---

## 7. Cost Management

### Resource Tracking

**Monthly Costs (Your Infrastructure)**
```
Vercel:
- Hobby: Free (100 GB bandwidth)
- Pro: $20/month (1 TB bandwidth)

Render:
- Free: $0 (750 hours)
- Starter: $7/month per service
- Standard: $25/month per service

MongoDB Atlas:
- M0: Free (512 MB storage)
- M10: $57/month (10 GB storage)

Cloudflare:
- Free: Unlimited DNS + SSL
- Pro: $20/month (advanced features)
```

**Billing Users for Overages**
```python
# Calculate user costs
def calculate_deployment_cost(deployment):
    if deployment.tier == 'free':
        return 0
    elif deployment.tier == 'pro':
        base = 299  # ZAR
        overages = calculate_resource_overages(deployment)
        return base + overages
    elif deployment.tier == 'agency':
        return 999  # ZAR (unlimited)
```

---

## 8. Implementation Checklist

### Phase 1: Infrastructure Setup
- [ ] Create Vercel team account
- [ ] Create Render account
- [ ] Setup MongoDB Atlas project
- [ ] Configure Cloudflare DNS
- [ ] Generate all API tokens
- [ ] Add tokens to backend .env

### Phase 2: Backend Implementation
- [ ] Add deployment endpoints to builder_server.py
- [ ] Implement deployment_service.py
- [ ] Add MongoDB deployment tracking collection
- [ ] Create admin deployment management API
- [ ] Add resource usage monitoring

### Phase 3: Frontend Implementation
- [ ] Add "Deploy" button to ProjectEditor
- [ ] Create deployment status modal
- [ ] Add deployment history view
- [ ] Implement admin deployment dashboard
- [ ] Add environment variable UI

### Phase 4: DNS & SSL
- [ ] Setup Cloudflare API integration
- [ ] Implement subdomain creation
- [ ] Configure SSL certificates
- [ ] Add custom domain support (Agency tier)

### Phase 5: Monitoring & Limits
- [ ] Track resource usage per deployment
- [ ] Implement tier limits enforcement
- [ ] Add billing calculations
- [ ] Setup usage alerts
- [ ] Create cost reports

---

## 9. API Endpoints

### Deployment Endpoints

```
POST   /api/deployments/deploy          # Deploy project
GET    /api/deployments                 # List user deployments
GET    /api/deployments/{id}            # Get deployment details
DELETE /api/deployments/{id}            # Delete deployment
POST   /api/deployments/{id}/rollback   # Rollback deployment
PUT    /api/deployments/{id}/env        # Update env variables
GET    /api/deployments/{id}/logs       # View deployment logs
GET    /api/deployments/{id}/metrics    # Resource usage metrics
```

### Admin Endpoints

```
GET    /api/admin/deployments           # All deployments
GET    /api/admin/deployments/stats     # Deployment statistics
PUT    /api/admin/deployments/limits    # Set global limits
GET    /api/admin/costs                 # Cost breakdown
POST   /api/admin/deployments/{id}/suspend  # Suspend deployment
```

---

## 10. Security Considerations

### API Key Security
```python
# Encrypt API keys in database
from cryptography.fernet import Fernet

key = os.getenv("ENCRYPTION_KEY")
cipher = Fernet(key)

encrypted_token = cipher.encrypt(vercel_token.encode())
```

### Rate Limiting
```python
# Limit deployment frequency
@rate_limit("10 per hour")
async def deploy_project():
    pass
```

### Access Control
```python
# Only project owner can deploy
async def deploy_project(project_id, current_user):
    project = await db.projects.find_one({"project_id": project_id})
    if project["user_id"] != current_user.user_id:
        raise HTTPException(403, "Not authorized")
```

---

## 11. Deployment Success Metrics

**Target Metrics**
- Deployment success rate: > 95%
- Average deployment time: < 5 minutes
- Uptime: > 99.9%
- SSL certificate issuance: < 30 seconds

**Monitoring Dashboard**
```
Admin Panel → Deployments → Metrics:
- Total deployments: 1,234
- Active deployments: 456
- Failed deployments: 12 (1%)
- Average deploy time: 3.5 min
- Total bandwidth: 45 GB
```

---

## 12. Getting Started

### Quick Start Commands

```bash
# 1. Setup your infrastructure accounts
# Visit: vercel.com, render.com, mongodb.com/atlas, cloudflare.com

# 2. Get API tokens from each platform

# 3. Update backend/.env
nano backend/.env
# Add all deployment tokens

# 4. Restart backend
sudo supervisorctl restart backend

# 5. Test deployment
curl -X POST http://localhost:8001/api/deployments/deploy \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj_test", "tier": "free"}'

# 6. Verify deployment
curl https://proj-test.digitalninja.co.za
```

---

## Summary

This deployment infrastructure provides:
✅ Multi-tenant hosting on YOUR accounts
✅ Automatic deployments to Vercel + Render
✅ MongoDB database provisioning
✅ Custom subdomain generation
✅ SSL certificate automation
✅ Admin controls and monitoring
✅ Resource usage tracking
✅ Tier-based limits
✅ One-click deploy from editor
✅ Rollback capabilities
✅ GitHub Actions integration

**Total Implementation Time:** 2-3 days
**Monthly Cost (Your infrastructure):** ~$100-200 for 50 deployments
**User Pricing:** R299 (Pro) / R999 (Agency) covers costs + profit

Ready to deploy! 🚀
