# Digital Ninja App Builder - Deployment Guide

## Deployment Architecture
- **Backend**: Render (FastAPI)
- **Frontend**: Vercel (React)
- **Database**: MongoDB Atlas

---

## Prerequisites

1. **Accounts Required**:
   - GitHub account (for repo export)
   - Render account (render.com)
   - Vercel account (vercel.com)
   - MongoDB Atlas account (mongodb.com/atlas)

2. **Credentials to Prepare**:
   - Gmail App Password (for SMTP)
   - Peach Payments Test API Key
   - JWT Secret (generate secure random string)

---

## Step 1: MongoDB Atlas Setup

### 1.1 Create Cluster
```
1. Login to MongoDB Atlas
2. Create new cluster (Free tier M0 is sufficient for testing)
3. Choose region closest to your Render deployment
4. Wait for cluster to be created
```

### 1.2 Configure Network Access
```
1. Go to Network Access
2. Add IP Address: 0.0.0.0/0 (Allow all - for initial setup)
3. Or add specific Render IP ranges for production
```

### 1.3 Create Database User
```
1. Go to Database Access
2. Add New Database User
3. Set username: digitalninja_user
4. Set strong password
5. Grant role: Atlas admin (or readWriteAnyDatabase)
6. Save credentials
```

### 1.4 Get Connection String
```
1. Click "Connect" on your cluster
2. Choose "Connect your application"
3. Copy connection string:
   mongodb+srv://digitalninja_user:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
4. Replace <password> with your database password
5. Add database name: /digital_ninja_db before the ?
```

---

## Step 2: GitHub Repository Export

### 2.1 Export from Emergent
```
1. In Emergent dashboard, click "Save to GitHub"
2. Select or create repository: digital-ninja-app-builder
3. Push all files (frontend, backend, services, docs)
4. Wait for export to complete
5. Get repository URL: https://github.com/YOUR_USERNAME/digital-ninja-app-builder
```

### 2.2 Verify Repository Contents
```
digital-ninja-app-builder/
├── backend/
│   ├── server.py
│   ├── routes_extensions.py
│   ├── services/
│   │   ├── email_service.py
│   │   └── pdf_service.py
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── .env.example
│   └── Dockerfile
├── README.md
├── DEPLOYMENT.md
└── design_guidelines.json
```

---

## Step 3: Backend Deployment on Render

### 3.1 Create New Web Service
```
1. Login to Render
2. Click "New +" → "Web Service"
3. Connect GitHub repository
4. Select digital-ninja-app-builder
5. Configure:
   - Name: digitalninja-backend
   - Environment: Python 3
   - Region: Choose closest to MongoDB Atlas
   - Branch: main
   - Root Directory: backend
   - Build Command: pip install -r requirements.txt
   - Start Command: uvicorn server:app --host 0.0.0.0 --port $PORT
```

### 3.2 Configure Environment Variables
```
In Render dashboard, add these environment variables:

MONGO_URL=mongodb+srv://digitalninja_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/digital_ninja_db?retryWrites=true&w=majority
DB_NAME=digital_ninja_db
CORS_ORIGINS=*
JWT_SECRET=your-super-secret-jwt-key-change-in-production-RANDOM-STRING
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=72
EMERGENT_LLM_KEY=sk-emergent-76924Ca13Fe786dC7E
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_FROM=Digital Ninja <noreply@digitalninja.app>
PEACH_PAYMENTS_MERCHANT_ID=your_merchant_id
PEACH_PAYMENTS_API_KEY=your_api_key
PEACH_PAYMENTS_MODE=test
ALLOWED_IPS=*
FRONTEND_URL=https://your-app.vercel.app
PORT=10000
```

### 3.3 Deploy
```
1. Click "Create Web Service"
2. Wait for deployment (5-10 minutes)
3. Get backend URL: https://digitalninja-backend.onrender.com
4. Test health: curl https://digitalninja-backend.onrender.com/api/admin/diagnostics
```

---

## Step 4: Frontend Deployment on Vercel

### 4.1 Import Project
```
1. Login to Vercel
2. Click "Add New..." → "Project"
3. Import from GitHub: digital-ninja-app-builder
4. Configure:
   - Framework Preset: Create React App
   - Root Directory: frontend
   - Build Command: yarn build
   - Output Directory: build
```

### 4.2 Configure Environment Variables
```
In Vercel project settings → Environment Variables:

REACT_APP_BACKEND_URL=https://digitalninja-backend.onrender.com
WDS_SOCKET_PORT=443
REACT_APP_ENABLE_VISUAL_EDITS=false
ENABLE_HEALTH_CHECK=false
```

### 4.3 Deploy
```
1. Click "Deploy"
2. Wait for build (2-5 minutes)
3. Get frontend URL: https://digitalninja.vercel.app
4. Set custom domain (optional)
```

### 4.4 Update Backend FRONTEND_URL
```
1. Go back to Render dashboard
2. Update FRONTEND_URL environment variable:
   FRONTEND_URL=https://digitalninja.vercel.app
3. Trigger manual deploy
```

---

## Step 5: Post-Deployment Configuration

### 5.1 Update OAuth Redirect
```
Since we're using Emergent Auth, no OAuth client configuration needed.
OAuth redirects will automatically work with your new domain.
```

### 5.2 Test All Services

#### Test Authentication
```bash
# Register new user
curl -X POST https://digitalninja-backend.onrender.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"password123"}'

# Login
curl -X POST https://digitalninja-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

#### Test Diagnostics
```bash
# Get your JWT token from login response, then:
curl https://digitalninja-backend.onrender.com/api/admin/diagnostics \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 5.3 Verify Diagnostics Page
```
1. Open https://digitalninja.vercel.app
2. Register/Login
3. Navigate to Admin → Diagnostics
4. Verify all checks show green:
   ✅ OAuth: Operational
   ✅ SMTP: Configured
   ✅ PDF: Operational
   ✅ Billing: Configured
   ✅ AI: Operational
```

---

## Step 6: Configure SMTP (Production Emails)

### 6.1 Gmail Setup
```
1. Go to Google Account → Security
2. Enable 2-Step Verification
3. Go to App Passwords
4. Generate password for "Mail"
5. Copy 16-character password
6. Update SMTP_PASSWORD in Render environment variables
7. Trigger manual deploy
```

### 6.2 Test Email Sending
```bash
curl -X POST https://digitalninja-backend.onrender.com/api/email/send-password-reset \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"email":"your-test-email@gmail.com"}'
```

---

## Step 7: Configure Peach Payments (ZAR Billing)

### 7.1 Get Test Credentials
```
1. Sign up at https://www.peachpayments.com
2. Request test account credentials
3. Get Test Merchant ID
4. Get Test API Key
```

### 7.2 Update Environment Variables
```
In Render dashboard:
PEACH_PAYMENTS_MERCHANT_ID=test_merchant_xxxxx
PEACH_PAYMENTS_API_KEY=test_api_key_xxxxx
PEACH_PAYMENTS_MODE=test

Trigger manual deploy
```

---

## Step 8: Performance Optimization

### 8.1 Render Instance Scaling
```
Free tier: 512 MB RAM, shared CPU
Starter: $7/month - 512 MB RAM, shared CPU
Standard: $25/month - 2 GB RAM, 1 CPU (recommended)
```

### 8.2 MongoDB Atlas Scaling
```
M0: Free tier (sufficient for testing)
M10: $57/month (production recommended)
```

### 8.3 Vercel Scaling
```
Hobby: Free (sufficient for most cases)
Pro: $20/month (better performance, analytics)
```

---

## Step 9: Monitoring & Logs

### 9.1 Render Logs
```
1. Go to Render dashboard
2. Click on digitalninja-backend service
3. View "Logs" tab for real-time logs
4. Set up log drains for long-term storage
```

### 9.2 Vercel Analytics
```
1. Go to Vercel dashboard
2. Click on digitalninja project
3. Enable Analytics
4. Monitor Core Web Vitals
```

### 9.3 MongoDB Atlas Monitoring
```
1. Go to Atlas dashboard
2. Click "Metrics" tab
3. Monitor connections, operations, memory
4. Set up alerts for high usage
```

---

## Step 10: Backup & Security

### 10.1 MongoDB Backups
```
1. Atlas provides automatic backups (M10+)
2. For M0, use mongodump manually:
   mongodump --uri="YOUR_MONGODB_URI" --out=/backup
```

### 10.2 Security Hardening
```
1. Change JWT_SECRET to strong random string
2. Restrict CORS_ORIGINS to your domain
3. Enable IP allowlist in MongoDB Atlas
4. Enable HTTPS only (automatic on Render/Vercel)
5. Rotate API keys regularly
```

### 10.3 Environment Secrets
```
Never commit:
- .env files
- API keys
- Passwords
- JWT secrets

Always use:
- Environment variables
- Secrets management
- .env.example templates
```

---

## Troubleshooting

### Backend Won't Start
```
1. Check Render logs for errors
2. Verify all environment variables are set
3. Test MongoDB connection string locally
4. Check requirements.txt has all dependencies
```

### Frontend Can't Connect to Backend
```
1. Verify REACT_APP_BACKEND_URL is correct
2. Check CORS configuration in backend
3. Ensure /api prefix on all backend routes
4. Test backend directly with curl
```

### MongoDB Connection Errors
```
1. Check connection string format
2. Verify IP allowlist includes 0.0.0.0/0
3. Confirm database user has correct permissions
4. Test connection with MongoDB Compass
```

### SMTP Not Working
```
1. Verify Gmail app password is correct
2. Check SMTP_HOST and SMTP_PORT
3. Ensure 2-Step Verification is enabled
4. Test with different email provider
```

---

## Cost Estimation

### Free Tier (Testing)
```
- Render: Free (with sleep on inactivity)
- Vercel: Free (Hobby plan)
- MongoDB Atlas: Free (M0 cluster)
- Total: $0/month
```

### Production (Recommended)
```
- Render Standard: $25/month
- Vercel Pro: $20/month
- MongoDB Atlas M10: $57/month
- Total: $102/month
```

---

## Support & Resources

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **MongoDB Atlas Docs**: https://docs.atlas.mongodb.com
- **GitHub Repo**: https://github.com/YOUR_USERNAME/digital-ninja-app-builder

---

## Quick Reference Commands

```bash
# Test backend health
curl https://digitalninja-backend.onrender.com/api/admin/diagnostics

# Rebuild frontend
cd frontend && yarn build

# Check MongoDB connection
mongosh "YOUR_MONGODB_URI"

# View Render logs
render logs digitalninja-backend

# Deploy to Vercel
vercel --prod
```

---

**Deployment Checklist:**
- [ ] MongoDB Atlas cluster created and configured
- [ ] GitHub repository exported
- [ ] Backend deployed on Render with all env vars
- [ ] Frontend deployed on Vercel
- [ ] FRONTEND_URL updated in backend
- [ ] SMTP configured with Gmail
- [ ] Peach Payments credentials added
- [ ] Diagnostics page shows all green
- [ ] OAuth login tested
- [ ] Email sending tested
- [ ] PDF generation tested
- [ ] Billing flow tested

**Status**: Ready for production deployment 🚀
