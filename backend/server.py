from dotenv import load_dotenv
import os

# Load the .env file explicitly
load_dotenv()

# Debug: Print the value of OPENAI_API_KEY
print('DEBUG: OPENAI_API_KEY =', os.getenv('OPENAI_API_KEY'))

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
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

    # Update the project's files list
    files = project.get('files', [])
    files.append({
        "path": file_update.path,
        "content": file_update.content
    })

    project_dict = project.model_dump()
    project_dict['files'] = files
    project_dict['updated_at'] = datetime.now(timezone.utc).isoformat()

    await db.projects.update_one(
        {"project_id": project_id, "user_id": current_user.user_id},
        {"$set": project_dict}
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


# ==================== SETUP ====================

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.get("/")
async def root():
    return {"message": "AI Application Builder API", "version": "1.0.0"}