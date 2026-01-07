from dotenv import load_dotenv
import os

# Load the .env file explicitly
load_dotenv()

# Debug: Print the value of OPENAI_API_KEY
print('DEBUG: OPENAI_API_KEY =', os.getenv('OPENAI_API_KEY'))

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, RedirectResponse, HTMLResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from pathlib import Path
import uuid
import logging

from ai_builder_service import ai_builder

# Define project root and load .env again if needed
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB Configuration
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize FastAPI
app = FastAPI(title="AI Application Builder")
api_router = APIRouter(prefix="/api")

# Auth setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 72

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User


class ProjectCreate(BaseModel):
    prompt: str
    tech_stack: Dict[str, str] = {
        "frontend": "React",
        "backend": "FastAPI",
        "database": "MongoDB"
    }


class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    project_id: str
    user_id: str
    name: str
    description: str
    prompt: str
    tech_stack: Dict[str, str]
    files: List[Dict[str, str]]
    status: str = "active"
    created_at: datetime
    updated_at: datetime


class FileUpdate(BaseModel):
    path: str
    content: str

# NEW: Chat models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    response: str

class ChatBuildResponse(BaseModel):
    response: str
    file_updates: List[FileUpdate] = []

# ==================== AUTH HELPERS ====================

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


async def get_current_user(request: Request) -> User:
    auth_header = request.headers.get("Authorization")
    token = request.cookies.get("session_token")

    if not token and auth_header:
        token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else auth_header

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])

    return User(**{k: v for k, v in user_doc.items() if k != 'password_hash'})

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user = User(
        user_id=user_id,
        email=user_data.email,
        name=user_data.name,
        created_at=datetime.now(timezone.utc)
    )

    user_dict = user.model_dump()
    user_dict['password_hash'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()

    await db.users.insert_one(user_dict)

    access_token = create_access_token(data={"user_id": user.user_id})
    return TokenResponse(access_token=access_token, user=user)


@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc or not verify_password(credentials.password, user_doc.get('password_hash', '')):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])

    user = User(**{k: v for k, v in user_doc.items() if k != 'password_hash'})
    access_token = create_access_token(data={"user_id": user.user_id})

    return TokenResponse(access_token=access_token, user=user)


@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ==================== PROJECT ENDPOINTS (LIST/GENERATE) ====================

@api_router.get("/projects", response_model=List[Project])
async def get_projects(current_user: User = Depends(get_current_user)):
    projects = await db.projects.find({"user_id": current_user.user_id}, {"_id": 0}).to_list(100)
    for proj in projects:
        if isinstance(proj.get('created_at'), str):
            proj['created_at'] = datetime.fromisoformat(proj['created_at'])
        if isinstance(proj.get('updated_at'), str):
            proj['updated_at'] = datetime.fromisoformat(proj['updated_at'])
    return projects

@api_router.post("/projects/generate", response_model=Project)
async def generate_project(project_data: ProjectCreate, current_user: User = Depends(get_current_user)):
    # Fallback if ai_builder is available; else create a basic scaffold
    try:
        app_structure = await ai_builder.generate_app_structure(
            project_data.prompt,
            project_data.tech_stack
        )
        name = app_structure.get("app_name", project_data.prompt[:40] or "AI Project")
        description = app_structure.get("description", project_data.prompt)
        files = app_structure.get("files", [])
    except Exception:
        # Minimal safe scaffold
        name = project_data.prompt[:40] or "AI Project"
        description = project_data.prompt
        files = [
            {"path": "src/App.js", "content": "export default function App(){return <div>Hello</div>}", "language": "js"},
            {"path": "src/index.css", "content": "body{font-family:sans-serif}", "language": "css"}
        ]

    project_id = f"proj_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    project_doc = {
        "project_id": project_id,
        "user_id": current_user.user_id,
        "name": name,
        "description": description,
        "prompt": project_data.prompt,
        "tech_stack": project_data.tech_stack,
        "files": files,
        "status": "active",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    await db.projects.insert_one(project_doc)
    project_doc["created_at"] = now
    project_doc["updated_at"] = now
    return Project(**project_doc)

# ==================== PROJECT ENDPOINTS ====================

@api_router.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate, current_user: User = Depends(get_current_user)):
    project = Project(
        project_id=f"project_{uuid.uuid4().hex[:12]}",
        user_id=current_user.user_id,
        name=project_data.prompt,
        description="",
        prompt=project_data.prompt,
        tech_stack=project_data.tech_stack,
        files=[],
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    project_dict = project.model_dump()
    project_dict['created_at'] = project_dict['created_at'].isoformat()
    project_dict['updated_at'] = project_dict['updated_at'].isoformat()

    await db.projects.insert_one(project_dict)

    return project


@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str, current_user: User = Depends(get_current_user)):
    project = await db.projects.find_one({"project_id": project_id, "user_id": current_user.user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if isinstance(project.get('created_at'), str):
        project['created_at'] = datetime.fromisoformat(project['created_at'])

    if isinstance(project.get('updated_at'), str):
        project['updated_at'] = datetime.fromisoformat(project['updated_at'])

    return Project(**project)


@api_router.put("/projects/{project_id}/files")
async def update_file(
    project_id: str,
    file_update: FileUpdate,
    current_user: User = Depends(get_current_user)
):
    project = await db.projects.find_one({"project_id": project_id, "user_id": current_user.user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    files = project.get('files', [])
    updated = False
    for i, f in enumerate(files):
        if f.get("path") == file_update.path:
            files[i] = {**f, "content": file_update.content}
            updated = True
            break
    if not updated:
        files.append({
            "path": file_update.path,
            "content": file_update.content,
            "language": file_update.path.split('.')[-1] if '.' in file_update.path else "txt"
        })

    await db.projects.update_one(
        {"project_id": project_id, "user_id": current_user.user_id},
        {"$set": {"files": files, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "File updated successfully", "path": file_update.path}


# NEW: Project-scoped chat endpoints

@api_router.post("/projects/{project_id}/chat/plan", response_model=ChatResponse)
async def project_chat_plan(project_id: str, req: ChatRequest, current_user: User = Depends(get_current_user)):
    project = await db.projects.find_one({"project_id": project_id, "user_id": current_user.user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Simple, deterministic planning reply; replace with real LLM integration later.
    plan = (
        f"I see your project '{project.get('name')}'. "
        f"Your goal: {req.message}\n"
        "- Suggestion 1: Outline key pages (Home, About, Contact, FAQ, Products).\n"
        "- Suggestion 2: Define data models and API endpoints required.\n"
        "- Suggestion 3: Plan UI components and navigation.\n"
        "Reply with specifics and I can break it into tasks."
    )
    return ChatResponse(response=plan)


@api_router.post("/projects/{project_id}/chat/build", response_model=ChatBuildResponse)
async def project_chat_build(project_id: str, req: ChatRequest, current_user: User = Depends(get_current_user)):
    project = await db.projects.find_one({"project_id": project_id, "user_id": current_user.user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Stub build reply. In future, generate file_updates from AI.
    reply = (
        f"Applying build reasoning for '{project.get('name')}'. "
        f"Requested change: {req.message}\n"
        "I can generate specific file updates next. For now, no changes were applied."
    )
    return ChatBuildResponse(response=reply, file_updates=[])


# ==================== EXPORT ENDPOINTS ====================

@api_router.post("/projects/{project_id}/export")
async def export_project(project_id: str, current_user: User = Depends(get_current_user)):
    project = await db.projects.find_one({"project_id": project_id, "user_id": current_user.user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "project_id": project_id,
        "name": project.get("name"),
        "files": project.get("files", []),
        "export_ready": True,
        "instructions": "Import into your preferred host or push to GitHub."
    }

@api_router.post("/projects/{project_id}/export/github")
async def export_project_github(project_id: str, current_user: User = Depends(get_current_user)):
    project = await db.projects.find_one({"project_id": project_id, "user_id": current_user.user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "project_name": project.get("name", f"project_{project_id}"),
        "description": project.get("description", ""),
        "files": project.get("files", []),
        "deployment_ready": True
    }

# ==================== GOOGLE OAUTH (MINIMAL) ====================

@api_router.get("/auth/google")
async def google_auth():
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    if not GOOGLE_CLIENT_ID or not GOOGLE_REDIRECT_URI:
        # Return helpful message rather than failing
        return {"auth_url": None, "message": "Google OAuth not configured on server."}
    google_oauth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile&"
        f"access_type=offline"
    )
    return {"auth_url": google_oauth_url}

@api_router.get("/auth/google/session")
async def process_google_session_get(request: Request):
    code = request.query_params.get("code")
    if not code:
        return HTMLResponse("<h2>Google OAuth Error: Missing code in query params.</h2>", status_code=400)
    # If tokens are needed, implement exchange here (requires env secrets); for now redirect back
    redirect_frontend = os.getenv("FRONTEND_URL", "http://localhost:3000")
    return RedirectResponse(url=f"{redirect_frontend}/login?token=")

# ==================== GENERIC AI CHAT STREAM (for AIChat sidebar) ====================

class ChatMessageRequest(BaseModel):
    message: str

@api_router.post("/chat/message")
async def chat_message(req: ChatMessageRequest, current_user: User = Depends(get_current_user)):
    async def stream():
        text = f"Echo: {req.message}"
        for word in text.split():
            yield f"data: {word}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(stream(), media_type="text/event-stream")

# ==================== SETUP ====================

app.include_router(api_router)

# Explicit origins are required when allow_credentials is True
origins_env = os.environ.get('CORS_ORIGINS')
if origins_env:
    ALLOW_ORIGINS = [o.strip() for o in origins_env.split(',') if o.strip()]
else:
    ALLOW_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=ALLOW_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.get("/")
async def root():
    return {"message": "AI Application Builder API", "version": "1.0.0"}