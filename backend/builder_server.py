

from dotenv import load_dotenv, find_dotenv
import sys
load_dotenv(find_dotenv(), override=True)

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
import uuid
import logging

# MongoDB robust connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME')
if not mongo_url or not db_name:
    logging.error('MONGO_URL or DB_NAME not set in environment. Please check your .env file.')
    print('MONGO_URL:', mongo_url)
    print('DB_NAME:', db_name)
    sys.exit(1)
try:
    print(f'Attempting MongoDB connection to: {mongo_url}, DB: {db_name}')
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
except Exception as e:
    logging.error(f'Failed to connect to MongoDB: {e}')
    print(f'Failed to connect to MongoDB: {e}')
    sys.exit(1)


# Add MongoDB connection test to FastAPI startup event (must be after app is defined)

# ...existing code...

app = FastAPI(title="AI Application Builder")
api_router = APIRouter(prefix="/api")

@app.on_event("startup")
async def test_mongo_connection():
    try:
        await db.command("ping")
        print("MongoDB connection successful.")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        raise

app = FastAPI(title="AI Application Builder")
api_router = APIRouter(prefix="/api")

# --- Strict CORS config ---
from starlette.middleware.cors import CORSMiddleware
frontend_origin = os.environ.get('CORS_ORIGINS', 'http://localhost:3000')
if isinstance(frontend_origin, str) and frontend_origin.startswith('['):
    import ast
    frontend_origin = ast.literal_eval(frontend_origin)
elif isinstance(frontend_origin, str):
    frontend_origin = [o.strip() for o in frontend_origin.split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELS ====================

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    created_at: datetime
    picture: Optional[str] = ""

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

# ==================== AUTH HELPERS ====================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret-key")
JWT_ALGORITHM = "HS256"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=72)
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
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user_doc.get('password_hash'):
        raise HTTPException(status_code=401, detail="This account uses Google sign-in. Please sign in with Google.")
    if not verify_password(credentials.password, user_doc.get('password_hash')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    user = User(**{k: v for k, v in user_doc.items() if k != 'password_hash'})
    access_token = create_access_token(data={"user_id": user.user_id})
    return TokenResponse(access_token=access_token, user=user)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ==================== GOOGLE OAUTH ENDPOINTS ====================

@api_router.get("/auth/google")
async def google_auth(request: Request):
    """Initiate Google OAuth flow"""
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    google_oauth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile&"
        f"access_type=offline"
    )
    return {"auth_url": google_oauth_url}


# POST handler (for API clients)
@api_router.post("/auth/google/session")
async def process_google_session_post(request: Request):
    """Process Google OAuth code from frontend and exchange for tokens (POST)."""
    import httpx
    data = await request.json()
    code = data.get("code")
    return await process_google_oauth_code(code)

# GET handler (for browser redirect)
@api_router.get("/auth/google/session")
async def process_google_session_get(request: Request):
    """Process Google OAuth code from Google redirect (GET)."""
    code = request.query_params.get("code")
    from fastapi.responses import RedirectResponse, HTMLResponse
    if not code:
        return HTMLResponse("<h2>Google OAuth Error: Missing code in query params.</h2>", status_code=400)
    try:
        result = await process_google_oauth_code(code)
        jwt_token = result["access_token"]
        redirect_url = f"http://localhost:3000/login?token={jwt_token}"
        return RedirectResponse(url=redirect_url)
    except Exception as e:
        return HTMLResponse(f"<h2>Google OAuth Error: {str(e)}</h2>", status_code=400)

# Shared logic for both GET and POST
async def process_google_oauth_code(code: str):
    import httpx
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(token_url, data=token_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")
        tokens = token_resp.json()
        id_token = tokens.get("id_token")
        access_token = tokens.get("access_token")
        if not id_token:
            raise HTTPException(status_code=400, detail="No id_token in Google response")
        from jose import jwt as jose_jwt
        user_info = jose_jwt.get_unverified_claims(id_token)
        email = user_info.get("email")
        name = user_info.get("name", "Google User")
        picture = user_info.get("picture", "")
        if not email:
            raise HTTPException(status_code=400, detail="No email in Google id_token")
        user_doc = await db.users.find_one({"email": email}, {"_id": 0})
        if not user_doc:
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            user_doc = {
                "user_id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.users.insert_one(user_doc)
        else:
            user_id = user_doc["user_id"]
        session_token = uuid.uuid4().hex
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await db.user_sessions.insert_one({
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        user = User(**user_doc)
        jwt_token = create_access_token(data={"user_id": user.user_id})
        return {"access_token": jwt_token, "user": user_doc}

# ==================== PROJECT ENDPOINTS ====================

@api_router.get("/projects", response_model=List[Project])
async def get_projects(current_user: User = Depends(get_current_user)):
    projects = await db.projects.find({"user_id": current_user.user_id}, {"_id": 0}).to_list(100)
    for proj in projects:
        if isinstance(proj.get('created_at'), str):
            proj['created_at'] = datetime.fromisoformat(proj['created_at'])
        if isinstance(proj.get('updated_at'), str):
            proj['updated_at'] = datetime.fromisoformat(proj['updated_at'])
    return projects

@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str, current_user: User = Depends(get_current_user)):
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": current_user.user_id},
        {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if isinstance(project.get('created_at'), str):
        project['created_at'] = datetime.fromisoformat(project['created_at'])
    if isinstance(project.get('updated_at'), str):
        project['updated_at'] = datetime.fromisoformat(project['updated_at'])
    return Project(**project)

@api_router.post("/projects/generate", response_model=Project)
async def generate_project(project_data: ProjectCreate, current_user: User = Depends(get_current_user)):
    from ai_builder_service import AIBuilderService
    try:
        ai_builder = AIBuilderService()
        app_struct = await ai_builder.generate_app_structure(project_data.prompt, project_data.tech_stack)
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        project_doc = {
            "project_id": project_id,
            "user_id": current_user.user_id,
            "name": app_struct.get("app_name", "AI Project"),
            "description": app_struct.get("description", project_data.prompt),
            "prompt": project_data.prompt,
            "tech_stack": project_data.tech_stack,
            "files": app_struct.get("files", []),
            "status": "active",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        await db.projects.insert_one(project_doc)
        project_doc['created_at'] = now
        project_doc['updated_at'] = now
        return Project(**project_doc)
    except Exception as e:
        logging.error(f"AI builder error: {e}")
        raise HTTPException(status_code=500, detail=f"AI builder error: {e}")

# --- Add /api/chat endpoint if missing ---
from fastapi import Body
class ChatRequest(BaseModel):
    prompt: str
    tech_stack: Optional[Dict[str, str]] = None

@api_router.post("/chat")
async def chat_endpoint(data: ChatRequest = Body(...), current_user: User = Depends(get_current_user)):
    from ai_builder_service import AIBuilderService
    try:
        ai_builder = AIBuilderService()
        result = await ai_builder.generate_app_structure(data.prompt, data.tech_stack or {})
        return {"result": result}
    except Exception as e:
        logging.error(f"AI chat error: {e}")
        raise HTTPException(status_code=500, detail=f"AI chat error: {e}")

@api_router.put("/projects/{project_id}/files")
async def update_file(
    project_id: str,
    file_update: FileUpdate,
    current_user: User = Depends(get_current_user)
):
    result = await db.projects.update_one(
        {"project_id": project_id, "user_id": current_user.user_id},
        {"$set": {"files.$[elem].content": file_update.content, "updated_at": datetime.now(timezone.utc).isoformat()}},
        array_filters=[{"elem.path": file_update.path}]
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="File or project not found")
    return {"message": "File updated"}


# ==================== HEALTH CHECK & SETUP ====================
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "Digital Ninja App Builder", "version": "1.0.0"}

@app.get("/")
async def root():
    return {"message": "Digital Ninja App Builder API", "version": "1.0.0", "docs": "/docs"}

app.include_router(api_router)

import logging
logging.info("Setting up CORS for http://localhost:3000")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("builder_server:app", host="0.0.0.0", port=8000, reload=True)
