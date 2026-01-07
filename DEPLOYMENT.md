# Deployment Guide - AI Application Builder

Complete guide to deploy your AI Application Builder to production infrastructure.

## 📋 Overview

This guide covers deploying:
- **Frontend** → Vercel (React application)
- **Backend** → Render (FastAPI server)
- **Database** → MongoDB Atlas (managed MongoDB)
- **Authentication** → Google OAuth configuration

## 🎯 Prerequisites

- GitHub account (for code hosting)
- Vercel account (free tier available)
- Render account (free tier available)
- MongoDB Atlas account (free tier available)
- OpenAI API account with API key
- Google Cloud Console project (for OAuth)

---

## 📦 Part 1: MongoDB Atlas Setup

### 1.1 Create MongoDB Cluster

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up or log in
3. Click **"Build a Database"**
4. Choose **"M0 Free"** tier
5. Select your cloud provider and region
6. Click **"Create Cluster"**

### 1.2 Configure Network Access

1. Go to **Network Access** in left sidebar
2. Click **"Add IP Address"**
3. Click **"Allow Access from Anywhere"** (for production, restrict to your server IPs)
4. Click **"Confirm"**

### 1.3 Create Database User

1. Go to **Database Access** in left sidebar
2. Click **"Add New Database User"**
3. Choose **"Password"** authentication
4. Set username and password (save these!)
5. Set user privileges to **"Read and write to any database"**
6. Click **"Add User"**

### 1.4 Get Connection String

1. Go to **Database** in left sidebar
2. Click **"Connect"** on your cluster
3. Choose **"Connect your application"**
4. Copy the connection string (looks like: `mongodb+srv://username:<password>@cluster0.xxxxx.mongodb.net/`)
5. Replace `<password>` with your actual password
6. Add database name at the end: `mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/ai_app_builder`

**Save this connection string** - you'll need it for Render deployment.

---

## 🚀 Part 2: Backend Deployment (Render)

### 2.1 Prepare Repository

Ensure your GitHub repository has:
- `/backend/builder_server.py`
- `/backend/requirements.txt`
- `/backend/.env.example`

### 2.2 Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:

**Settings:**
- **Name:** `ai-builder-backend`
- **Region:** Choose closest to your users
- **Branch:** `main`
- **Root Directory:** `backend`
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn builder_server:app --host 0.0.0.0 --port $PORT`
- **Instance Type:** Free (or paid for production)

### 2.3 Configure Environment Variables

In Render, go to **Environment** tab and add:

```env
MONGO_URL=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/ai_app_builder
DB_NAME=ai_app_builder
JWT_SECRET=generate-a-random-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=72
OPENAI_API_KEY=sk-your-openai-api-key
CORS_ORIGINS=*
FRONTEND_URL=https://your-app.vercel.app
```

**Important:**
- Replace MongoDB connection string with your Atlas URL
- Generate a strong JWT secret (use `openssl rand -base64 32`)
- Add your OpenAI API key
- Update `FRONTEND_URL` after deploying frontend (next step)

### 2.4 Deploy

1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes)
3. Copy your backend URL: `https://ai-builder-backend.onrender.com`

---

## 🌐 Part 3: Frontend Deployment (Vercel)

### 3.1 Deploy to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New"** → **"Project"**
3. Import your GitHub repository
4. Configure:

**Settings:**
- **Framework Preset:** Create React App
- **Root Directory:** `frontend`
- **Build Command:** `yarn build`
- **Output Directory:** `build`
- **Install Command:** `yarn install`

### 3.2 Environment Variables

Add in Vercel project settings:

```env
REACT_APP_BACKEND_URL=https://ai-builder-backend.onrender.com
WDS_SOCKET_PORT=443
```

Replace with your actual Render backend URL.

### 3.3 Deploy

1. Click **"Deploy"**
2. Wait for deployment (2-5 minutes)
3. Copy your frontend URL: `https://your-app.vercel.app`

### 3.4 Update Backend CORS

Go back to Render and update `FRONTEND_URL`:
```env
FRONTEND_URL=https://your-app.vercel.app
```

Redeploy backend for changes to take effect.

---

## 🔐 Part 4: Google OAuth Configuration

### 4.1 Emergent Auth (Managed OAuth)

This application uses **Emergent Auth** for OAuth handling. The flow is:

1. User clicks "Sign in with Google"
2. Redirects to: `https://auth.emergentagent.com/?redirect=https://your-app.vercel.app/auth/callback`
3. Emergent Auth handles Google OAuth
4. Redirects back with `session_id` in URL hash
5. Backend processes session and creates user

**No Google Cloud Console configuration needed** - Emergent Auth handles everything!

### 4.2 Testing OAuth

1. Deploy both frontend and backend
2. Go to your Vercel URL
3. Click "Sign in with Google"
4. Complete Google authentication
5. Verify redirect to dashboard

---

## ✅ Part 5: Verification & Testing

### 5.1 Test Email/Password Authentication

```bash
curl -X POST https://ai-builder-backend.onrender.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User"}'
```

### 5.2 Test Google OAuth

1. Go to `https://your-app.vercel.app/login`
2. Click "Sign in with Google"
3. Complete authentication
4. Verify dashboard access

### 5.3 Test AI Code Generation

1. Login to application
2. Click "New Project"
3. Enter: "Build a calculator app"
4. Verify code generation works
5. Check live preview renders

---

## 🔧 Environment Variables Reference

### Backend (Render)

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGO_URL` | MongoDB Atlas connection string | Yes |
| `DB_NAME` | Database name | Yes |
| `OPENAI_API_KEY` | OpenAI API key for code generation | Yes |
| `JWT_SECRET` | Secret for JWT token signing | Yes |
| `FRONTEND_URL` | Your Vercel frontend URL | Yes |
| `CORS_ORIGINS` | Allowed CORS origins | Yes |

### Frontend (Vercel)

| Variable | Description | Required |
|----------|-------------|----------|
| `REACT_APP_BACKEND_URL` | Your Render backend URL | Yes |
| `WDS_SOCKET_PORT` | WebSocket port for Vercel | No |

---

## 🐛 Troubleshooting

### Backend Issues

**CORS errors:**
- Verify `FRONTEND_URL` matches your Vercel URL exactly
- Check `CORS_ORIGINS` is set to `*` or includes frontend URL

**Database connection fails:**
- Verify MongoDB Atlas network access allows all IPs (0.0.0.0/0)
- Check connection string has correct password
- Ensure database user has correct permissions

**OpenAI errors:**
- Verify API key is valid
- Check OpenAI account has credits
- Monitor API usage in OpenAI dashboard

### Frontend Issues

**API calls fail:**
- Check `REACT_APP_BACKEND_URL` is correct
- Verify backend is running (check Render logs)
- Test backend health: `curl https://your-backend.onrender.com/api/health`

**Google OAuth fails:**
- Check browser console for errors
- Verify `/auth/callback` route exists
- Ensure no ad blockers blocking redirects

---

## 📊 Monitoring

### Render (Backend)
- Check **Logs** tab for errors
- Monitor **Metrics** for performance  
- Set up **Health Checks**: `/api/health`

### Vercel (Frontend)
- Check **Deployments** for build status
- Review **Analytics** for traffic
- Monitor **Functions** logs

### MongoDB Atlas
- Check **Metrics** for database performance
- Set up **Alerts** for high usage
- Monitor **Storage** and connection counts

---

## 💰 Cost Estimates

### Free Tier (Getting Started)
- Render Free: 750 hours/month (sleeps after 15min inactivity)
- Vercel Hobby: 100GB bandwidth/month
- MongoDB Atlas M0: 512MB storage
- OpenAI: Pay per token (~$0.01-0.10 per generation)

**Total: ~$5-20/month** (mostly OpenAI usage)

### Production Scale
- Render Starter: $7/month (no sleep)
- Vercel Pro: $20/month
- MongoDB Atlas M10: ~$60/month
- OpenAI: $50-200/month (depends on usage)

**Total: ~$137-287/month**

---

## 🔒 Security Checklist

- ✅ Never commit `.env` files
- ✅ Use strong JWT secrets (32+ characters)
- ✅ Rotate API keys regularly
- ✅ Enable MongoDB authentication
- ✅ Use HTTPS everywhere
- ✅ Set up rate limiting (optional)
- ✅ Monitor for suspicious activity
- ✅ Regular security updates

---

## 🚀 Next Steps

1. **Custom Domain**: Add your domain in Vercel
2. **Analytics**: Set up Vercel Analytics
3. **Monitoring**: Add Sentry for error tracking
4. **Backups**: Configure MongoDB automated backups
5. **CDN**: Use Vercel Edge Network for global delivery
6. **Caching**: Add Redis for performance (optional)

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Emergent Auth Documentation](https://emergent.sh/docs/auth)

---

**Deployment Complete! 🎉**

Your AI Application Builder is now live and ready for production use!