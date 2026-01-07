# AI Application Builder

An AI-powered platform that generates complete, functional applications from natural language prompts. Similar to Bolt.new or Lovable.dev, but self-hostable.

## 🎯 Features

- 🤖 **AI Code Generation** - Generate working React apps from natural language (powered by OpenAI GPT-4o)
- 💻 **In-Browser IDE** - Monaco code editor with syntax highlighting
- 👁️ **Live Preview** - Real-time preview of generated applications in iframe
- 🔐 **Authentication** - Email/password + Google OAuth (via Emergent Auth)
- 📦 **Project Management** - Save, edit, and manage generated applications
- 🎨 **Professional UI** - Modern, responsive interface with Tailwind CSS + shadcn/ui

## 🚀 Live Demo

Try it at: `https://ai-app-forge-8.preview.emergentagent.com`

## 📸 Screenshots

### AI Code Generation
Generate complete apps from prompts like "Build a calculator" or "Build a todo list":
- Calculator with full arithmetic operations
- Todo list with localStorage persistence
- Blog with posts and comments system

### Live Preview
Watch your generated app render in real-time as the AI creates it.

## 🛠️ Tech Stack

**Frontend:**
- React 18
- React Router v6
- Monaco Editor (VS Code editor)
- Tailwind CSS + shadcn/ui components
- Axios for API calls

**Backend:**
- FastAPI (Python 3.9+)
- MongoDB (Motor async driver)
- OpenAI API (GPT-4o model)
- JWT authentication
- Passlib + bcrypt for passwords

## 📋 Prerequisites

- Node.js 16+ and yarn
- Python 3.9+
- MongoDB (local or Atlas)
- OpenAI API key

## 🔧 Installation

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd ai-app-builder
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your credentials
```

### 3. Frontend Setup
```bash
cd frontend
yarn install

cp .env.example .env
# Update REACT_APP_BACKEND_URL if needed
```

### 4. Start Services

**MongoDB:**
```bash
mongod  # Or use MongoDB Atlas
```

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn builder_server:app --host 0.0.0.0 --port 8001 --reload
```

**Frontend:**
```bash
cd frontend
yarn start
```

Access at `http://localhost:3000`

## 📝 Usage

1. **Register/Login** - Create account or use Google OAuth
2. **Create Project** - Click "New Project" and enter prompt:
   - "Build a calculator app"
   - "Build a todo list with persistence"
   - "Build a blog with comments"
3. **View Code** - Generated code appears in Monaco editor
4. **Live Preview** - App renders in real-time
5. **Edit & Save** - Modify code and save changes

## 🗂️ Project Structure

```
├── backend/
│   ├── builder_server.py        # Main FastAPI server
│   ├── ai_builder_service.py    # OpenAI GPT-4o integration
│   ├── deployment_service.py    # Deployment logic
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.js         # Email/password login
│   │   │   ├── Register.js      # User registration
│   │   │   ├── AuthCallback.js  # OAuth callback handler
│   │   │   ├── Projects.js      # Project dashboard
│   │   │   ├── Builder.js       # Prompt input page
│   │   │   └── ProjectEditor.js # Monaco + Live Preview
│   │   └── components/
│   │       ├── LivePreview.js   # Iframe preview component
│   │       └── ProtectedRoute.js
│   └── package.json
└── DEPLOYMENT.md                # Deployment guide
```

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login with email/password
- `GET /api/auth/google` - Get Google OAuth URL
- `POST /api/auth/google/session` - Process OAuth session
- `GET /api/auth/me` - Get current user

### Projects
- `POST /api/projects/generate` - Generate project from prompt
- `GET /api/projects` - List user's projects
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}/files` - Update files
- `DELETE /api/projects/{id}` - Delete project

## 🌍 Environment Variables

### Backend (.env)
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=ai_app_builder
OPENAI_API_KEY=sk-...
JWT_SECRET=your-secret-key
FRONTEND_URL=http://localhost:3000
```

### Frontend (.env)
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 🚢 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment guide covering:
- Vercel (Frontend)
- Render (Backend)
- MongoDB Atlas (Database)
- Environment configuration
- Google OAuth setup

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- Built on [Emergent.sh](https://emergent.sh) platform
- Powered by OpenAI GPT-4o
- UI components from [shadcn/ui](https://ui.shadcn.com)
- Monaco Editor from Microsoft

## 📧 Support

For issues, questions, or contributions, please open an issue on GitHub.
