from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv
from pathlib import Path
import os
import uuid
import logging

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from ai_builder_service import ai_builder

# MongoDB
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if user has a password_hash (users who signed up with Google OAuth don't have one)
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
    # Get the frontend origin from the request
    frontend_url = os.environ.get('FRONTEND_URL', request.headers.get('origin', 'http://localhost:3000'))
    redirect_url = f"{frontend_url}/auth/callback"
    
    # Redirect to Emergent auth with the callback URL
    auth_url = f"https://auth.emergentagent.com/?redirect={redirect_url}"
    return {"auth_url": auth_url}

@api_router.post("/auth/google/session")
async def process_google_session(request: Request):
    """Process Google OAuth session_id from Emergent Auth
    
    NOTE: Emergent Auth provides the session_id directly in the URL after OAuth.
    We use the session_id as the session_token since it's already validated by Emergent.
    """
    # Get session_id from request body (sent by frontend)
    data = await request.json()
    session_id = data.get("session_id")
    
    logger.info(f"Processing Google OAuth session: {session_id[:10] if session_id else 'None'}...")
    
    if not session_id:
        logger.error("Missing session_id in request")
        raise HTTPException(status_code=400, detail="Missing session_id")
    
    # For Emergent Auth, the session_id IS the session token
    # We need to create a user record based on the fact that Emergent has validated this session
    # Since we don't have user details yet, we'll create a placeholder and update it later
    
    # Check if a session already exists for this token
    existing_session = await db.user_sessions.find_one({"session_token": session_id}, {"_id": 0})
    
    if existing_session:
        logger.info(f"Found existing session for user: {existing_session['user_id']}")
        user_id = existing_session["user_id"]
        user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    else:
        logger.info("Creating new user for OAuth session")
        # Create new user with OAuth - we don't have email yet, so use session_id as identifier
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": f"oauth_{session_id[:10]}@temp.com",  # Temp email, will be updated
            "name": "Digital Ninja User",
            "picture": "",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
        
        # Store session with 7-day expiry
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await db.user_sessions.insert_one({
            "user_id": user_id,
            "session_token": session_id,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    user = User(**user_doc)
    
    # Create JWT token
    access_token = create_access_token(data={"user_id": user.user_id})
    
    return {
        "access_token": access_token,
        "session_token": session_id,
        "user": user,
        "token_type": "bearer"
    }


# ==================== AI BUILDER ENDPOINTS ====================

@api_router.post("/projects/generate", response_model=Project)
async def generate_project(project_data: ProjectCreate, current_user: User = Depends(get_current_user)):
    """Generate a complete application from natural language prompt"""
    
    logger.info(f"Generating project for user {current_user.user_id}: {project_data.prompt}")
    
    # Generate app structure using AI
    app_structure = await ai_builder.generate_app_structure(
        project_data.prompt,
        project_data.tech_stack
    )
    
    # Create project
    project_id = f"proj_{uuid.uuid4().hex[:12]}"
    project = Project(
        project_id=project_id,
        user_id=current_user.user_id,
        name=app_structure['app_name'],
        description=app_structure['description'],
        prompt=project_data.prompt,
        tech_stack=project_data.tech_stack,
        files=app_structure['files'],
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Save to database
    project_dict = project.model_dump()
    project_dict['created_at'] = project_dict['created_at'].isoformat()
    project_dict['updated_at'] = project_dict['updated_at'].isoformat()
    
    await db.projects.insert_one(project_dict)
    
    logger.info(f"Project {project_id} created with {len(app_structure['files'])} files")
    
    return project

@api_router.get("/projects", response_model=List[Project])
async def get_projects(current_user: User = Depends(get_current_user)):
    """Get all projects for current user"""
    projects = await db.projects.find({"user_id": current_user.user_id}, {"_id": 0}).to_list(100)
    
    for proj in projects:
        if isinstance(proj.get('created_at'), str):
            proj['created_at'] = datetime.fromisoformat(proj['created_at'])
        if isinstance(proj.get('updated_at'), str):
            proj['updated_at'] = datetime.fromisoformat(proj['updated_at'])
    
    return projects

@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Get specific project with all files"""
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

@api_router.put("/projects/{project_id}/files")
async def update_file(
    project_id: str,
    file_update: FileUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a specific file in project"""
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update file content
    files = project['files']
    file_found = False
    
    for f in files:
        if f['path'] == file_update.path:
            f['content'] = file_update.content
            file_found = True
            break
    
    if not file_found:
        # Add new file
        files.append({
            "path": file_update.path,
            "content": file_update.content,
            "language": file_update.path.split('.')[-1]
        })
    
    # Update project
    await db.projects.update_one(
        {"project_id": project_id},
        {"$set": {
            "files": files,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "File updated successfully", "path": file_update.path}

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Delete a project"""
    result = await db.projects.delete_one(
        {"project_id": project_id, "user_id": current_user.user_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Project deleted successfully"}

@api_router.post("/projects/{project_id}/export")
async def export_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Generate export package for project"""
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Return project data for GitHub export
    return {
        "project_id": project_id,
        "name": project['name'],
        "files": project['files'],
        "export_ready": True,
        "instructions": "Use GitHub export button to create repository"
    }

# ==================== DEPLOYMENT ENDPOINTS ====================

from deployment_service import deployment_service

@api_router.post("/deployments/deploy")
async def deploy_project(
    deployment_request: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Deploy project to production infrastructure"""
    project_id = deployment_request.get("project_id")
    tier = deployment_request.get("tier", "free")
    
    # Get project
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Deploy
    logger.info(f"Deploying project {project_id} for user {current_user.user_id}")
    result = await deployment_service.deploy_full_stack(
        project_id,
        project['files'],
        tier
    )
    
    # Save deployment record
    deployment_dict = {
        **result,
        "user_id": current_user.user_id,
        "project_name": project['name']
    }
    await db.deployments.insert_one(deployment_dict)
    
    return result


@api_router.post("/projects/{project_id}/export/github")
async def export_to_github(
    project_id: str,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Export project to GitHub - clean, deployment-ready code"""
    
    # Get project
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": current_user.user_id},
        {"_id": 0}
    )
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Clean files - remove .emergent dependencies
    cleaned_files = []
    for file in project['files']:
        content = file['content']
        
        # Remove emergent-specific imports/code
        if 'emergent' not in file['path'].lower():
            # Clean imports
            if file['path'].endswith('.js') or file['path'].endswith('.jsx'):
                # Remove any emergent imports
                lines = content.split('\n')
                cleaned_lines = [l for l in lines if 'emergent' not in l.lower()]
                content = '\n'.join(cleaned_lines)
            
            cleaned_files.append({
                "path": file['path'],
                "content": content,
                "language": file.get('language', 'text')
            })
    
    # Return cleaned project structure
    return {
        "project_name": project['name'],
        "files": cleaned_files
    }


# ==================== CHAT ENDPOINT ====================

class ChatMessage(BaseModel):
    message: str
    history: List[Dict[str, str]] = []

@api_router.post("/chat")
async def chat_with_gpt(request: ChatMessage, current_user: User = Depends(get_current_user)):
    """Chat with GPT-4 for debugging and improvements"""
    import httpx
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    try:
        # Build messages for GPT-4
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant specialized in app development, debugging, and code improvements. Provide clear, actionable advice."}
        ]
        
        # Add history
        for msg in request.history[-10:]:  # Last 10 messages for context
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current message
        messages.append({"role": "user", "content": request.message})
        
        # Call OpenAI API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
        return {"response": data["choices"][0]["message"]["content"]}
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat response")

@api_router.get("/deployments")
async def get_deployments(current_user: User = Depends(get_current_user)):
    """Get all deployments for current user"""
    deployments = await db.deployments.find(
        {"user_id": current_user.user_id},
        {"_id": 0}
    ).to_list(100)
    return deployments

@api_router.delete("/deployments/{deployment_id}")
async def delete_deployment(deployment_id: str, current_user: User = Depends(get_current_user)):
    """Delete a deployment"""
    deployment = await db.deployments.find_one(
        {"deployment_id": deployment_id, "user_id": current_user.user_id}
    )
    
    if not deployment:


# ==================== HEALTH CHECK ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "ok",
        "service": "Digital Ninja App Builder",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Digital Ninja App Builder API",
        "version": "1.0.0",
        "docs": "/docs"
    }

        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Delete from infrastructure
    if deployment.get("frontend"):
        await deployment_service.delete_deployment(
            deployment["frontend"].get("deployment_id"),
            "vercel"
        )
    
    if deployment.get("backend"):
        await deployment_service.delete_deployment(
            deployment["backend"].get("service_id"),
            "render"
        )
    
    # Delete from database
    await db.deployments.delete_one({"deployment_id": deployment_id})
    
    return {"message": "Deployment deleted"}

# ==================== ADMIN DEPLOYMENT ENDPOINTS ====================

@api_router.get("/admin/deployments")
async def admin_get_all_deployments(current_user: User = Depends(get_current_user)):
    """Get all deployments (admin only)"""
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    deployments = await db.deployments.find({}, {"_id": 0}).to_list(1000)
    return deployments

@api_router.get("/admin/deployments/stats")
async def admin_deployment_stats(current_user: User = Depends(get_current_user)):
    """Get deployment statistics"""
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total = await db.deployments.count_documents({})
    active = await db.deployments.count_documents({"status": "deployed"})
    failed = await db.deployments.count_documents({"status": {"$in": ["failed", "backend_failed", "frontend_failed"]}})
    
    return {
        "total_deployments": total,
        "active_deployments": active,
        "failed_deployments": failed,
        "success_rate": round((active / total * 100) if total > 0 else 0, 1)
    }

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
