# Digital Ninja App Builder

A powerful SaaS platform for building web applications with drag-and-drop functionality, AI assistance, team collaboration, and billing integration.

## Features

### Core Features
- ✅ **Authentication**: Email/Password + Google OAuth (Emergent Auth)
- ✅ **AI Assistant**: Sidebar chat with streaming responses (OpenAI GPT-4o-mini)
- ✅ **Page Builder**: Advanced drag-and-drop interface with components library
- ✅ **Team Management**: Role-based access control (Owner, Admin, Editor, Viewer)
- ✅ **Billing**: ZAR payment support with Peach Payments integration
- ✅ **Admin Dashboard**: System diagnostics and user management
- ✅ **Security**: JWT rotation, CORS whitelist, IP allowlist

### Billing Plans
- **Free**: 3 pages, Basic support, 1 team member
- **Pro**: R299/month - 50 pages, Priority support, 5 team members
- **Business**: R999/month - Unlimited pages, 24/7 support, Unlimited team members

## Tech Stack

### Backend
- FastAPI (Python)
- MongoDB (Motor async driver)
- JWT Authentication
- Emergent Integrations (OpenAI)
- PassLib (Password hashing)
- Pyppeteer (PDF generation)

### Frontend
- React 19
- React Router v7
- Tailwind CSS
- Shadcn/UI Components
- Lucide Icons
- Axios
- Sonner (Toasts)

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB
- Yarn

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Required API Keys:
- **Emergent LLM Key**: Get from Emergent dashboard (for AI chat)
- **Gmail App Password**: Generate from Google Account Security (for SMTP)
- **Peach Payments**: Test credentials from Peach Payments (for billing)
- **Google OAuth**: Not required - handled by Emergent Auth

6. Start the backend:
```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
yarn install
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your backend URL
```

4. Start the frontend:
```bash
yarn start
```

5. Access the application:
```
http://localhost:3000
```

## Environment Variables

### Backend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `MONGO_URL` | MongoDB connection string | Yes |
| `DB_NAME` | Database name | Yes |
| `JWT_SECRET` | Secret for JWT signing | Yes |
| `EMERGENT_LLM_KEY` | AI chat API key | Yes |
| `SMTP_USER` | Gmail email address | Optional |
| `SMTP_PASSWORD` | Gmail app password | Optional |
| `PEACH_PAYMENTS_API_KEY` | Payment gateway key | Optional |

### Frontend (.env)

| Variable | Description | Required |
|----------|-------------|----------|
| `REACT_APP_BACKEND_URL` | Backend API URL | Yes |

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login with email/password
- `GET /api/auth/me` - Get current user
- `GET /api/auth/google` - Initiate Google OAuth
- `POST /api/auth/google/callback` - OAuth callback handler
- `POST /api/auth/logout` - Logout

### AI Chat
- `POST /api/chat/message` - Send message (streaming)
- `GET /api/chat/history` - Get chat history

### Pages
- `GET /api/pages` - List all pages
- `POST /api/pages` - Create new page
- `GET /api/pages/{page_id}` - Get page by ID
- `PUT /api/pages/{page_id}` - Update page
- `DELETE /api/pages/{page_id}` - Delete page

### Teams
- `GET /api/teams/current` - Get current team
- `GET /api/teams/members` - List team members
- `POST /api/teams/invite` - Invite member

### Billing
- `GET /api/billing/plans` - List all plans
- `POST /api/billing/subscribe` - Subscribe to plan

### Admin
- `GET /api/admin/users` - List all users (admin only)
- `GET /api/admin/diagnostics` - System diagnostics (admin only)

## Security Features

1. **JWT Authentication**: Secure token-based auth with 72-hour expiration
2. **Password Hashing**: BCrypt with salt rounds
3. **CORS Configuration**: Whitelist origins
4. **HTTP-only Cookies**: Secure session storage
5. **Role-based Access Control**: Owner, Admin, Editor, Viewer
6. **IP Allowlist**: Optional IP restriction

## Integrations

### Emergent Auth (Google OAuth)
- No configuration needed
- Automatic user creation
- Profile picture sync
- Email verification

### Emergent LLM (AI Chat)
- OpenAI GPT-4o-mini
- Streaming responses
- Session management
- Context-aware conversations

### Peach Payments (ZAR Billing)
- Test mode enabled
- ZAR currency
- Subscription management
- Invoice generation

## Testing

Run the application and test:

1. **Authentication**:
   - Register new account
   - Login with credentials
   - Google OAuth flow

2. **AI Chat**:
   - Open AI assistant sidebar
   - Send messages
   - View streaming responses

3. **Page Builder**:
   - Create new page
   - Add components (headings, text, buttons, images)
   - Save page
   - Edit existing pages

4. **Team Management**:
   - Invite team members
   - View member list
   - Check role badges

5. **Billing**:
   - View plans
   - Subscribe to plan
   - Check current plan status

6. **Admin Features** (Owner/Admin only):
   - View all users
   - Check system diagnostics
   - Monitor service health

## Diagnostics Page

Access `/admin/diagnostics` to check:
- ✅ OAuth Status (Google Auth integration)
- ✅ SMTP Status (Email service)
- ✅ PDF Status (Export service)
- ✅ Billing Status (Payment gateway)
- ✅ AI Status (Chat assistant)

## Project Structure

```
/app/
├── backend/
│   ├── server.py          # FastAPI application
│   ├── requirements.txt   # Python dependencies
│   ├── .env              # Environment variables
│   └── .env.example      # Environment template
│
├── frontend/
│   ├── src/
│   │   ├── components/   # Reusable components
│   │   │   ├── ui/       # Shadcn components
│   │   │   ├── DashboardLayout.js
│   │   │   ├── AIChat.js
│   │   │   └── ProtectedRoute.js
│   │   ├── pages/        # Page components
│   │   │   ├── Login.js
│   │   │   ├── Register.js
│   │   │   ├── Dashboard.js
│   │   │   ├── PageBuilder.js
│   │   │   ├── TeamManagement.js
│   │   │   ├── Billing.js
│   │   │   ├── Settings.js
│   │   │   ├── AdminDashboard.js
│   │   │   ├── Diagnostics.js
│   │   │   └── AuthCallback.js
│   │   ├── utils/
│   │   │   └── api.js    # API client
│   │   ├── App.js
│   │   ├── App.css
│   │   └── index.js
│   ├── package.json
│   ├── tailwind.config.js
│   ├── .env
│   └── .env.example
│
├── design_guidelines.json  # Design system
└── README.md              # This file
```

## Deployment

### Using Emergent Platform

1. Connect GitHub repository
2. Configure environment variables in dashboard
3. Deploy using native deployment
4. GitHub export available via dashboard

### Manual Deployment

#### Backend (Production)
```bash
uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
```

#### Frontend (Production)
```bash
yarn build
# Serve build folder with nginx/apache
```

## Export & Ownership

### GitHub Export
1. Click "Save to GitHub" in Emergent dashboard
2. Select branch or create new
3. Push changes
4. Clone repository locally:
```bash
git clone https://github.com/your-username/digital-ninja-app.git
```

### VS Code Access
- Click VS Code icon in Emergent interface
- View complete project structure
- Edit files directly
- Navigate all folders

## Troubleshooting

### Backend Issues

**MongoDB Connection Failed**
```bash
# Check MongoDB is running
sudo systemctl status mongod

# Check connection string in .env
MONGO_URL=mongodb://localhost:27017
```

**Import Errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend Issues

**Module Not Found**
```bash
# Clear cache and reinstall
rm -rf node_modules yarn.lock
yarn install
```

**API Connection Failed**
- Check `REACT_APP_BACKEND_URL` in `.env`
- Verify backend is running
- Check CORS configuration

### AI Chat Not Working
- Verify `EMERGENT_LLM_KEY` is set
- Check backend logs for errors
- Test API endpoint directly:
```bash
curl -X POST http://localhost:8001/api/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message":"Hello"}'
```

## Credits

- Built on [Emergent Platform](https://emergent.sh)
- Design: Space Grotesk + Inter fonts
- UI Components: [Shadcn/UI](https://ui.shadcn.com)
- Icons: [Lucide](https://lucide.dev)

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- Check diagnostics page: `/admin/diagnostics`
- Review backend logs
- Contact support: support@emergent.sh

---

Built with ⚡ by Digital Ninja App Builder