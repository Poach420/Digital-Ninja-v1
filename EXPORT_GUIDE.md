# Digital Ninja App Builder - Export & Deployment Guide

## 🚀 Quick Export

Your generated applications are **completely self-contained** and free of any proprietary dependencies. Each exported project includes:

- ✅ Production-ready React frontend with Tailwind CSS
- ✅ FastAPI backend with complete CRUD operations
- ✅ MongoDB schemas and connection setup
- ✅ Vercel deployment configuration
- ✅ Render deployment configuration
- ✅ Environment variable templates
- ✅ Complete documentation

## 📦 Export Methods

### Method 1: One-Click GitHub Export (Recommended)

1. Open your project in the editor
2. Click the "Export to GitHub" button (purple button with GitHub icon)
3. Download the generated `project-name-github-ready.json` file
4. Create a new GitHub repository
5. Extract files from the JSON and commit to your repo

### Method 2: Manual Download

1. Click "Download" button in the project editor
2. Extract the ZIP file
3. Follow the README.md instructions included

## 🌐 Deployment to Vercel (Frontend)

### Prerequisites
- GitHub account
- Vercel account (free tier available)

### Steps

1. **Push to GitHub**
   ```bash
   cd your-project
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/your-repo.git
   git push -u origin main
   ```

2. **Deploy to Vercel**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your GitHub repository
   - Configure:
     - **Framework Preset**: Create React App
     - **Root Directory**: Leave empty (or `frontend` if using monorepo)
     - **Build Command**: `npm install && npm run build`
     - **Output Directory**: `build`
   
3. **Environment Variables**
   Add in Vercel dashboard:
   ```env
   REACT_APP_API_URL=https://your-backend.onrender.com
   ```

4. **Deploy**
   - Click "Deploy"
   - Your frontend will be live at `https://your-app.vercel.app`

## 🖥️ Deployment to Render (Backend)

### Prerequisites
- GitHub account
- Render account (free tier available)
- MongoDB Atlas account (or local MongoDB)

### Steps

1. **MongoDB Atlas Setup** (if not using local)
   - Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
   - Create free cluster (M0)
   - Create database user
   - Get connection string: `mongodb+srv://username:password@cluster.mongodb.net/dbname`

2. **Deploy to Render**
   - Go to [dashboard.render.com](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: your-app-backend
     - **Root Directory**: `backend` (if monorepo)
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn builder_server:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables**
   Add in Render dashboard:
   ```env
   MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/dbname
   DB_NAME=your_database
   OPENAI_API_KEY=sk-your-key-here
   JWT_SECRET=your-random-secret-key
   FRONTEND_URL=https://your-app.vercel.app
   CORS_ORIGINS=https://your-app.vercel.app
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Backend will be live at `https://your-app-backend.onrender.com`

5. **Update Frontend**
   - Go back to Vercel
   - Update `REACT_APP_API_URL` to your Render URL
   - Redeploy frontend

## 🔒 Security Best Practices

### Never Commit Secrets
Add to `.gitignore`:
```
.env
.env.local
*.env
backend/.env
frontend/.env
```

### Generate Strong Secrets
```bash
# For JWT_SECRET
openssl rand -base64 32
```

### Environment Variables
Always use environment variables for:
- API keys
- Database credentials
- JWT secrets
- Service URLs

## 📋 Generated File Structure

```
your-project/
├── frontend/
│   ├── src/
│   │   ├── App.js          # Main React component
│   │   ├── App.css         # Tailwind styles
│   │   └── index.js        # Entry point
│   ├── public/
│   ├── package.json        # Dependencies
│   └── .env.example        # Environment template
├── backend/
│   ├── main.py             # FastAPI application
│   ├── models.py           # MongoDB models
│   ├── routes.py           # API endpoints
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment template
├── vercel.json             # Vercel config
├── render.yaml             # Render config
├── .gitignore              # Git ignore rules
└── README.md               # Setup instructions
```

## 🎯 Features Included

### Frontend (React + Tailwind CSS)
- ✅ Responsive design
- ✅ Modern UI components
- ✅ State management
- ✅ API integration
- ✅ Error handling
- ✅ Loading states

### Backend (FastAPI)
- ✅ RESTful API endpoints
- ✅ CRUD operations
- ✅ MongoDB integration
- ✅ JWT authentication (if requested)
- ✅ CORS configuration
- ✅ Error handling
- ✅ Data validation

### Deployment Configs
- ✅ vercel.json for frontend deployment
- ✅ render.yaml for backend deployment
- ✅ .env.example files
- ✅ .gitignore for security
- ✅ README.md with setup instructions

## 🔄 Version Control

### Creating Versions
1. In the project editor, click "Save Version"
2. Add a description (e.g., "Added user authentication")
3. Version is saved with timestamp

### Rollback
1. Click "Version History"
2. Select version to restore
3. Click "Rollback to This Version"
4. Project files are restored instantly

## 👥 Team Collaboration

### Inviting Team Members
1. Open project settings
2. Click "Team" tab
3. Enter team member email
4. Select role:
   - **Admin**: Full access including deletion
   - **Editor**: Can edit code and files
   - **Viewer**: Read-only access

### Managing Permissions
- Project owner has full control
- Admins can invite/remove members
- Editors can modify code
- Viewers can view and export

## 🐛 Troubleshooting

### Frontend Issues

**Build fails on Vercel:**
- Check `package.json` dependencies
- Verify Node.js version compatibility
- Check build logs for errors

**API calls fail:**
- Verify `REACT_APP_API_URL` is set correctly
- Check CORS settings in backend
- Verify backend is running

### Backend Issues

**Import errors:**
- Run `pip install -r requirements.txt`
- Check Python version (3.9+)

**Database connection fails:**
- Verify MongoDB connection string
- Check network access in MongoDB Atlas
- Ensure database user has correct permissions

**Port conflicts:**
- Backend uses port from `$PORT` environment variable
- Locally, it defaults to 8001

## 📞 Support

### Getting Help
- Check README.md in your exported project
- Review deployment logs on Vercel/Render
- MongoDB Atlas has detailed documentation

### Common Solutions
- Clear browser cache if frontend doesn't update
- Redeploy backend after environment variable changes
- Check security groups and firewall rules

## 🎉 Success Checklist

Before going live:
- [ ] All environment variables set
- [ ] Frontend deployed to Vercel
- [ ] Backend deployed to Render
- [ ] MongoDB Atlas configured
- [ ] CORS settings correct
- [ ] API endpoints tested
- [ ] SSL certificates active (automatic)
- [ ] Custom domain configured (optional)

## 🚀 You're Ready!

Your Digital Ninja generated application is now:
- ✅ Deployed and accessible worldwide
- ✅ Scalable and production-ready
- ✅ Secure with HTTPS
- ✅ No vendor lock-in
- ✅ Fully customizable
- ✅ Team collaboration enabled

**Happy Building!** 🎨
