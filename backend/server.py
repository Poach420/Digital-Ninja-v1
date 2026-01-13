from dotenv import load_dotenv, find_dotenv
import sys
load_dotenv(find_dotenv(), override=True)

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
import uuid
import logging
from pathlib import Path
import contextlib
import base64
import httpx
import re
import asyncio
import json
import json

# MongoDB robust connection
mongo_url = os.environ.get("MONGO_URL")
db_name = os.environ.get("DB_NAME")
if not mongo_url or not db_name:
    logging.warning("MONGO_URL or DB_NAME not set in environment. Using defaults.")
    mongo_url = mongo_url or "mongodb://localhost:27017"
    db_name = db_name or "digital_ninja_app"

try:
    print(f"Attempting MongoDB connection to: {mongo_url}, DB: {db_name}")
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {e}")
    print(f"MongoDB connection warning: {e}")

# Initialize services
from version_control_service import VersionControlService
from file_storage_service import FileStorageService
from discussion_service import DiscussionService

version_control = VersionControlService(db)
file_storage = FileStorageService()
discussion_service = DiscussionService()

# Add MongoDB connection test to FastAPI startup event
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

# --- Strict CORS config ---
from starlette.middleware.cors import CORSMiddleware
frontend_origin = os.environ.get("CORS_ORIGINS", "http://localhost:3000")
if isinstance(frontend_origin, str) and frontend_origin.startswith("["):
    import ast
    frontend_origin = ast.literal_eval(frontend_origin)
elif isinstance(frontend_origin, str):
    frontend_origin = [o.strip() for o in frontend_origin.split(",") if o.strip()]

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
    team_id: Optional[str] = None
    role: str = "member"
    plan: str = "free"
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

class SnapshotCreate(BaseModel):
    message: Optional[str] = None

class DeployRequest(BaseModel):
    platform: str = "vercel"  # vercel, render, docker
    env_vars: Optional[Dict[str, str]] = None

class DiscussionRequest(BaseModel):
    message: str
    project_id: Optional[str] = None
    history: Optional[List[Dict]] = []

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

class Team(BaseModel):
    model_config = ConfigDict(extra="ignore")
    team_id: str
    name: str
    owner_id: str
    plan: str = "free"
    created_at: datetime
    billing_status: str = "active"

class TeamMember(BaseModel):
    user_id: str
    email: EmailStr
    name: str
    role: str
    picture: Optional[str] = None

class TeamInvite(BaseModel):
    email: EmailStr
    role: str = "viewer"

class BillingPlan(BaseModel):
    plan_id: str
    name: str
    price_zar: float
    features: List[str]
    max_pages: int

class BillingUsage(BaseModel):
    projects: int = 0
    deployments: int = 0
    credits_used: int = 0

class PaymentMethod(BaseModel):
    provider: str
    status: str
    currency: str = "ZAR"
    last4: Optional[str] = None

class SecretItem(BaseModel):
    key: str
    value: str
    scope: str = "team"
    updated_at: datetime

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    picture: Optional[str] = None

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

# ==================== AUTH HELPERS ====================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret-key")
JWT_ALGORITHM = "HS256"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_PLAN = "free"
TEAM_OWNER_ROLE = "owner"
BILLING_ALLOWED_ROLES = {"owner", "admin"}
TEAM_ROLES_ALLOWED = {"owner", "admin", "editor", "viewer"}
BILLING_PLANS = [
    BillingPlan(
        plan_id="free",
        name="Free",
        price_zar=0.0,
        features=["3 pages", "Basic support", "1 team member"],
        max_pages=3,
    ),
    BillingPlan(
        plan_id="pro",
        name="Pro",
        price_zar=299.0,
        features=["50 pages", "Priority support", "5 team members", "Custom domain"],
        max_pages=50,
    ),
    BillingPlan(
        plan_id="business",
        name="Business",
        price_zar=999.0,
        features=["Unlimited pages", "24/7 support", "Unlimited team members", "White label"],
        max_pages=999999,
    ),
]
BILLING_PLAN_MAP = {plan.plan_id: plan for plan in BILLING_PLANS}

def parse_datetime_field(document: Dict[str, Any], field: str) -> None:
    value = document.get(field)
    if isinstance(value, str):
        document[field] = datetime.fromisoformat(value)

async def ensure_team_for_user(user_doc: Dict[str, Any]) -> Dict[str, Any]:
    if user_doc.get("team_id"):
        team_doc = await db.teams.find_one({"team_id": user_doc["team_id"]}, {"_id": 0})
        if team_doc:
            parse_datetime_field(team_doc, "created_at")
            plan_code = team_doc.get("plan", DEFAULT_PLAN)
            if user_doc.get("plan") != plan_code:
                await db.users.update_one({"user_id": user_doc["user_id"]}, {"$set": {"plan": plan_code}})
                user_doc["plan"] = plan_code
            return user_doc
    team_id = f"team_{uuid.uuid4().hex[:12]}"
    team_name = user_doc.get("name") or "Digital Ninja Team"
    created_at = datetime.now(timezone.utc)
    team_payload = {
        "team_id": team_id,
        "name": f"{team_name}'s Team" if not team_name.endswith(" Team") else team_name,
        "owner_id": user_doc["user_id"],
        "plan": DEFAULT_PLAN,
        "billing_status": "active",
        "created_at": created_at.isoformat(),
        "usage": {"projects": 0, "deployments": 0, "credits_used": 0},
    }
    await db.teams.insert_one(team_payload)
    await db.users.update_one(
        {"user_id": user_doc["user_id"]},
        {"$set": {"team_id": team_id, "role": TEAM_OWNER_ROLE, "plan": DEFAULT_PLAN}},
    )
    user_doc["team_id"] = team_id
    user_doc["role"] = TEAM_OWNER_ROLE
    user_doc["plan"] = DEFAULT_PLAN
    return user_doc

async def load_user_document(user_id: str) -> Optional[Dict[str, Any]]:
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user_doc:
        return None
    user_doc = dict(user_doc)
    parse_datetime_field(user_doc, "created_at")
    await ensure_team_for_user(user_doc)
    user_doc.pop("password_hash", None)
    return user_doc

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
    user_doc = await load_user_document(user_id)
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user_doc)

# ==================== AUTH ENDPOINTS ====================
@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    created_at = datetime.now(timezone.utc)
    team_id = f"team_{uuid.uuid4().hex[:12]}"
    team_payload = {
        "team_id": team_id,
        "name": f"{user_data.name}'s Team" if user_data.name else "Digital Ninja Team",
        "owner_id": user_id,
        "plan": DEFAULT_PLAN,
        "billing_status": "active",
        "created_at": created_at.isoformat(),
        "usage": {"projects": 0, "deployments": 0, "credits_used": 0},
    }
    user_payload = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "created_at": created_at.isoformat(),
        "team_id": team_id,
        "role": TEAM_OWNER_ROLE,
        "plan": DEFAULT_PLAN,
        "picture": "",
        "password_hash": hash_password(user_data.password),
    }
    await db.teams.insert_one(team_payload)
    await db.users.insert_one(user_payload)
    user_doc = await load_user_document(user_id)
    if not user_doc:
        raise HTTPException(status_code=500, detail="Failed to create user")
    access_token = create_access_token(data={"user_id": user_id})
    return TokenResponse(access_token=access_token, user=User(**user_doc))

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user_doc.get("password_hash"):
        raise HTTPException(status_code=401, detail="This account uses Google sign-in. Please sign in with Google.")
    if not verify_password(credentials.password, user_doc.get("password_hash")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user_doc = dict(user_doc)
    parse_datetime_field(user_doc, "created_at")
    await ensure_team_for_user(user_doc)
    user_doc.pop("password_hash", None)
    user = User(**user_doc)
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
            created_at = datetime.now(timezone.utc)
            team_id = f"team_{uuid.uuid4().hex[:12]}"
            team_payload = {
                "team_id": team_id,
                "name": f"{name}'s Team" if name else "Digital Ninja Team",
                "owner_id": user_id,
                "plan": DEFAULT_PLAN,
                "billing_status": "active",
                "created_at": created_at.isoformat(),
                "usage": {"projects": 0, "deployments": 0, "credits_used": 0},
            }
            user_doc = {
                "user_id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "created_at": created_at.isoformat(),
                "team_id": team_id,
                "role": TEAM_OWNER_ROLE,
                "plan": DEFAULT_PLAN,
            }
            await db.teams.insert_one(team_payload)
            await db.users.insert_one({**user_doc})
        else:
            user_doc = dict(user_doc)
            user_id = user_doc["user_id"]
        parse_datetime_field(user_doc, "created_at")
        await ensure_team_for_user(user_doc)
        user_doc.pop("password_hash", None)
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

# ==================== ACCOUNT & TEAM ENDPOINTS ====================
@api_router.get("/account/profile", response_model=User)
async def get_account_profile(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.put("/account/profile", response_model=User)
async def update_account_profile(update: ProfileUpdate, current_user: User = Depends(get_current_user)):
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await db.users.update_one({"user_id": current_user.user_id}, {"$set": update_data})
    refreshed = await load_user_document(current_user.user_id)
    if not refreshed:
        raise HTTPException(status_code=404, detail="User not found after update")
    return User(**refreshed)

@api_router.post("/account/password")
async def update_account_password(payload: PasswordUpdate, current_user: User = Depends(get_current_user)):
    user_doc = await db.users.find_one({"user_id": current_user.user_id}, {"_id": 0})
    if not user_doc or not user_doc.get("password_hash"):
        raise HTTPException(status_code=400, detail="Password-based login not configured for this account")
    if not verify_password(payload.current_password, user_doc["password_hash"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    new_hash = hash_password(payload.new_password)
    await db.users.update_one({"user_id": current_user.user_id}, {"$set": {"password_hash": new_hash}})
    return {"status": "success"}

@api_router.get("/teams/current", response_model=Team)
async def get_current_team(current_user: User = Depends(get_current_user)):
    if not current_user.team_id:
        raise HTTPException(status_code=404, detail="No team associated with user")
    team_doc = await db.teams.find_one({"team_id": current_user.team_id}, {"_id": 0})
    if not team_doc:
        raise HTTPException(status_code=404, detail="Team not found")
    parse_datetime_field(team_doc, "created_at")
    team_doc.setdefault("plan", current_user.plan)
    return Team(**team_doc)

@api_router.get("/teams/members", response_model=List[TeamMember])
async def get_team_members(current_user: User = Depends(get_current_user)):
    if not current_user.team_id:
        return []
    members = await db.users.find({"team_id": current_user.team_id}, {"_id": 0, "password_hash": 0}).to_list(200)
    results: List[TeamMember] = []
    for member in members:
        results.append(
            TeamMember(
                user_id=member["user_id"],
                email=member.get("email", ""),
                name=member.get("name", ""),
                role=member.get("role", "member"),
                picture=member.get("picture"),
            )
        )
    return results

@api_router.post("/teams/invite")
async def invite_team_member(invite: TeamInvite, current_user: User = Depends(get_current_user)):
    if current_user.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Only owners and admins can invite members")
    if invite.role not in TEAM_ROLES_ALLOWED:
        raise HTTPException(status_code=400, detail="Invalid role requested")
    token = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    invitation = {
        "team_id": current_user.team_id,
        "email": invite.email.lower(),
        "role": invite.role,
        "invited_by": current_user.user_id,
        "token": token,
        "status": "pending",
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=7)).isoformat(),
    }
    await db.team_invitations.insert_one(invitation)
    return {"status": "pending", "token": token, "message": f"Invitation sent to {invite.email}"}

# ==================== BILLING ENDPOINTS ====================
@api_router.get("/billing/plans", response_model=List[BillingPlan])
async def list_billing_plans() -> List[BillingPlan]:
    return BILLING_PLANS

@api_router.post("/billing/subscribe")
async def subscribe_to_plan(plan_id: str, current_user: User = Depends(get_current_user)):
    plan_id = plan_id.lower()
    if plan_id not in BILLING_PLAN_MAP:
        raise HTTPException(status_code=404, detail="Plan not found")
    if current_user.role not in BILLING_ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions to change billing plan")
    await db.teams.update_one({"team_id": current_user.team_id}, {"$set": {"plan": plan_id}})
    await db.users.update_many({"team_id": current_user.team_id}, {"$set": {"plan": plan_id}})
    event = {
        "team_id": current_user.team_id,
        "plan_id": plan_id,
        "changed_by": current_user.user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await db.billing_events.insert_one(event)
    return {"status": "success", "plan_id": plan_id}

@api_router.get("/billing/usage", response_model=BillingUsage)
async def get_billing_usage(current_user: User = Depends(get_current_user)) -> BillingUsage:
    team_doc = await db.teams.find_one({"team_id": current_user.team_id}, {"_id": 0, "usage": 1})
    usage = team_doc.get("usage", {}) if team_doc else {}
    return BillingUsage(**{
        "projects": usage.get("projects", 0),
        "deployments": usage.get("deployments", 0),
        "credits_used": usage.get("credits_used", 0),
    })

@api_router.get("/billing/payment-method", response_model=PaymentMethod)
async def get_payment_method(current_user: User = Depends(get_current_user)) -> PaymentMethod:
    profile = await db.billing_profiles.find_one({"team_id": current_user.team_id}, {"_id": 0})
    if not profile:
        return PaymentMethod(provider="Peach Payments", status="test_mode", currency="ZAR")
    return PaymentMethod(
        provider=profile.get("provider", "Peach Payments"),
        status=profile.get("status", "test_mode"),
        currency=profile.get("currency", "ZAR"),
        last4=profile.get("last4"),
    )

@api_router.post("/billing/payment-method")
async def update_payment_method(method: PaymentMethod, current_user: User = Depends(get_current_user)):
    if current_user.role not in BILLING_ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="Insufficient permissions to update billing")
    payload = method.model_dump()
    payload["team_id"] = current_user.team_id
    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.billing_profiles.update_one(
        {"team_id": current_user.team_id},
        {"$set": payload},
        upsert=True,
    )
    return {"status": "success"}

# ==================== PROJECT ENDPOINTS ====================
@api_router.get("/projects", response_model=List[Project])
async def get_projects(current_user: User = Depends(get_current_user)):
    projects = await db.projects.find({"user_id": current_user.user_id}, {"_id": 0}).to_list(100)
    for proj in projects:
        if isinstance(proj.get("created_at"), str):
            proj["created_at"] = datetime.fromisoformat(proj["created_at"])
        if isinstance(proj.get("updated_at"), str):
            proj["updated_at"] = datetime.fromisoformat(proj["updated_at"])
    return projects

@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str, current_user: User = Depends(get_current_user)):
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": current_user.user_id},
        {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if isinstance(project.get("created_at"), str):
        project["created_at"] = datetime.fromisoformat(project["created_at"])
    if isinstance(project.get("updated_at"), str):
        project["updated_at"] = datetime.fromisoformat(project["updated_at"])
    return Project(**project)

@api_router.post("/projects/generate", response_model=Project)
async def generate_project(project_data: ProjectCreate, current_user: User = Depends(get_current_user)):
    """Generate a project using AIBuilderService V2 (ENHANCED with real APIs); fallback to V1 or basic if unavailable."""
    try:
        # Try V2 first (with API integrations, backend generation, etc.)
        from ai_builder_service_v2 import AIBuilderServiceV2
        ai_builder = AIBuilderServiceV2()
        app_struct = await ai_builder.generate_app_structure(project_data.prompt, project_data.tech_stack)
        files = app_struct.get("files", [])
        logging.info("✅ Using AI Builder V2 (Enhanced)")
    except Exception as e1:
        logging.warning(f"AI Builder V2 unavailable: {e1}, trying V1...")
        try:
            from ai_builder_service import AIBuilderService
            ai_builder = AIBuilderService()
            app_struct = await ai_builder.generate_app_structure(project_data.prompt, project_data.tech_stack)
            files = app_struct.get("files", [])
            logging.info("✅ Using AI Builder V1 (Basic)")
        except Exception as e2:
            logging.warning(f"All AI builders unavailable, using fallback: {e2}")
            # Deterministic fallback
            wants_calc = re.search(r"\b(calc|calculator|arithmetic|add|subtract|multiply|divide)\b", project_data.prompt or "", re.I)
            app_js = (
                """export default function App(){ const [a,setA]=React.useState(''); const [b,setB]=React.useState(''); const [op,setOp]=React.useState('+'); const calc=(x,y,o)=>{const A=parseFloat(x),B=parseFloat(y); if(Number.isNaN(A)||Number.isNaN(B))return ''; switch(o){case '+':return A+B;case '-':return A-B;case '*':return A*B;case '/':return B!==0?A/B:'∞';default:return ''}}; const res=calc(a,b,op); return (<div style={{minHeight:'100vh',background:'#0b0f16',color:'#d7e7ff',fontFamily:'system-ui',padding:24}}> <header style={{display:'flex',alignItems:'center',gap:12,marginBottom:16}}> <div style={{width:12,height:12,borderRadius:999,background:'#20d6ff'}}></div> <h1 style={{margin:0,background:'linear-gradient(90deg,#20d6ff,#46ff9b)',WebkitBackgroundClip:'text',color:'transparent'}}>Digital Ninja Calculator</h1> </header> <div style={{display:'grid',gap:12,maxWidth:480,background:'rgba(255,255,255,0.06)',border:'1px solid rgba(255,255,255,0.12)',borderRadius:12,padding:16}}> <input placeholder="First number" value={a} onChange={e=>setA(e.target.value)} style={{padding:10,borderRadius:8,border:'1px solid #334155',background:'#0f172a',color:'#d7e7ff'}} /> <select value={op} onChange={e=>setOp(e.target.value)} style={{padding:10,borderRadius:8,border:'1px solid #334155',background:'#0f172a',color:'#d7e7ff'}}> <option value="+">Add (+)</option><option value="-">Subtract (-)</option><option value="*">Multiply (*)</option><option value="/">Divide (/)</option> </select> <input placeholder="Second number" value={b} onChange={e=>setB(e.target.value)} style={{padding:10,borderRadius:8,border:'1px solid #334155',background:'#0f172a',color:'#d7e7ff'}} /> <div style={{padding:12,background:'#0f172a',border:'1px solid #334155',borderRadius:8}}> <strong style={{color:'#20d6ff'}}>Result:</strong> <span style={{marginLeft:8}}>{String(res)}</span> </div> </div> </div>);} """
                if wants_calc else f"""export default function App(){{return <div style={{padding:24,fontFamily:'system-ui'}}><h1>Demo App</h1><p>Generated locally: {(project_data.prompt or '').replace('"','\\"')}</p></div>;}}"""
            )
            files = [
                {"path": "src/App.js", "content": app_js, "language": "js"},
                {"path": "src/index.css", "content": "body{font-family:sans-serif;margin:0;background:#0b0f16}", "language": "css"}
            ]
    except Exception as e:
        logging.warning(f"AI builder unavailable, falling back: {e}")
        # Deterministic fallback that renders well in our preview
        wants_calc = re.search(r"\b(calc|calculator|arithmetic|add|subtract|multiply|divide)\b", project_data.prompt or "", re.I)
        app_js = (
            """export default function App(){ const [a,setA]=React.useState(''); const [b,setB]=React.useState(''); const [op,setOp]=React.useState('+'); const calc=(x,y,o)=>{const A=parseFloat(x),B=parseFloat(y); if(Number.isNaN(A)||Number.isNaN(B))return ''; switch(o){case '+':return A+B;case '-':return A-B;case '*':return A*B;case '/':return B!==0?A/B:'∞';default:return ''}}; const res=calc(a,b,op); return (<div style={{minHeight:'100vh',background:'#0b0f16',color:'#d7e7ff',fontFamily:'system-ui',padding:24}}> <header style={{display:'flex',alignItems:'center',gap:12,marginBottom:16}}> <div style={{width:12,height:12,borderRadius:999,background:'#20d6ff'}}></div> <h1 style={{margin:0,background:'linear-gradient(90deg,#20d6ff,#46ff9b)',WebkitBackgroundClip:'text',color:'transparent'}}>Digital Ninja Calculator</h1> </header> <div style={{display:'grid',gap:12,maxWidth:480,background:'rgba(255,255,255,0.06)',border:'1px solid rgba(255,255,255,0.12)',borderRadius:12,padding:16}}> <input placeholder="First number" value={a} onChange={e=>setA(e.target.value)} style={{padding:10,borderRadius:8,border:'1px solid #334155',background:'#0f172a',color:'#d7e7ff'}} /> <select value={op} onChange={e=>setOp(e.target.value)} style={{padding:10,borderRadius:8,border:'1px solid #334155',background:'#0f172a',color:'#d7e7ff'}}> <option value="+">Add (+)</option><option value="-">Subtract (-)</option><option value="*">Multiply (*)</option><option value="/">Divide (/)</option> </select> <input placeholder="Second number" value={b} onChange={e=>setB(e.target.value)} style={{padding:10,borderRadius:8,border:'1px solid #334155',background:'#0f172a',color:'#d7e7ff'}} /> <div style={{padding:12,background:'#0f172a',border:'1px solid #334155',borderRadius:8}}> <strong style={{color:'#20d6ff'}}>Result:</strong> <span style={{marginLeft:8}}>{String(res)}</span> </div> </div> </div>);} """
            if wants_calc else f"""export default function App(){{return <div style={{padding:24,fontFamily:'system-ui'}}><h1>Demo App</h1><p>Generated locally: {(project_data.prompt or '').replace('"','\\"')}</p></div>;}}"""
        )
        files = [
            {"path": "src/App.js", "content": app_js, "language": "js"},
            {"path": "src/index.css", "content": "body{font-family:sans-serif;margin:0;background:#0b0f16}", "language": "css"}
        ]

    # Normalize paths: map frontend/src/* → src/* for our previewer
    normalized_files = []
    for f in files:
        p = f.get("path", "")
        p = p.replace("\\", "/")
        p = re.sub(r"^frontend/", "", p)
        p = re.sub(r"^client/", "", p)
        p = re.sub(r"^app/", "", p)
        normalized_files.append({"path": p, "content": f.get("content", ""), "language": f.get("language", "txt")})

    project_id = f"proj_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    project_doc = {
        "project_id": project_id,
        "user_id": current_user.user_id,
        "name": (project_data.prompt or "AI Project")[:40] or "AI Project",
        "description": project_data.prompt or "",
        "prompt": project_data.prompt or "",
        "tech_stack": project_data.tech_stack,
        "files": normalized_files,
        "status": "active",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }
    await db.projects.insert_one(project_doc)
    project_doc["created_at"] = now
    project_doc["updated_at"] = now
    return Project(**project_doc)

# ==================== STREAMING GENERATION ====================
@api_router.post("/projects/generate/stream")
async def generate_project_stream(project_data: ProjectCreate, current_user: User = Depends(get_current_user)):
    """Stream real-time generation progress using Server-Sent Events"""
    
    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'status', 'message': '🚀 Starting AI-powered generation...'})}\n\n"
            await asyncio.sleep(0.1)
            
            yield f"data: {json.dumps({'type': 'status', 'message': '📊 Analyzing requirements...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Start actual AI generation - Try V2 first (enhanced), fallback to V1
            try:
                from ai_builder_service_v2 import AIBuilderServiceV2
                ai_builder = AIBuilderServiceV2()
                yield f"data: {json.dumps({'type': 'status', 'message': '🤖 GPT-4o with API integrations...'})}\n\n"
            except:
                from ai_builder_service import AIBuilderService
                ai_builder = AIBuilderService()
                yield f"data: {json.dumps({'type': 'status', 'message': '🤖 GPT-4o is thinking...'})}\n\n"
            
            app_struct = await ai_builder.generate_app_structure(project_data.prompt, project_data.tech_stack)
            files = app_struct.get("files", [])
            
            yield f"data: {json.dumps({'type': 'status', 'message': f'✨ Generated {len(files)} files!'})}\n\n"
            
            # Send each file
            for idx, file in enumerate(files):
                await asyncio.sleep(0.05)
                yield f"data: {json.dumps({'type': 'file', 'file': file, 'index': idx, 'total': len(files)})}\n\n"
            
            # Save to database
            now = datetime.now(timezone.utc)
            project_id = str(uuid.uuid4())
            
            normalized_files = []
            for f in files:
                p = f.get("path", "")
                p = p.replace("\\", "/")
                p = re.sub(r"^frontend/", "", p)
                normalized_files.append({
                    "path": p,
                    "content": f.get("content", ""),
                    "language": f.get("language", "")
                })
            
            project_doc = {
                "project_id": project_id,
                "user_id": current_user.user_id,
                "name": (project_data.prompt or "AI Project")[:40],
                "description": project_data.prompt or "",
                "prompt": project_data.prompt or "",
                "tech_stack": project_data.tech_stack,
                "files": normalized_files,
                "status": "active",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            await db.projects.insert_one(project_doc)
            
            yield f"data: {json.dumps({'type': 'complete', 'project_id': project_id, 'files': normalized_files})}\n\n"
            
        except Exception as e:
            logging.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ==================== PROJECT CHAT (PLAN / BUILD) ====================
@api_router.post("/projects/{project_id}/chat/plan", response_model=ChatResponse)
async def project_chat_plan(project_id: str, req: ChatRequest, current_user: User = Depends(get_current_user)):
    project = await db.projects.find_one({"project_id": project_id, "user_id": current_user.user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    plan = (
        f"I see your project '{project.get('name')}'. Your goal: {req.message}\n"
        "- Suggestion 1: Add tabs for Home, About, Contact, FAQ.\n"
        "- Suggestion 2: Extract UI into small components to keep App.js clean.\n"
        "- Suggestion 3: Define next actions (e.g., add FAQ content, switch theme colors, add navbar).\n"
        "Reply with a specific change and I will apply it."
    )
    return ChatResponse(response=plan)

def _apply_simple_build(message: str, app_js: str) -> str:
    """Very simple transform: add tabs/nav and common sections or theme changes."""
    m = message.lower()
    # Ensure app has basic tabs scaffolding
    if "tab" in m or "navbar" in m or "about" in m or "contact" in m or "faq" in m or "products" in m:
        if "useState('home')" not in app_js and 'useState("home")' not in app_js:
            # Wrap current UI into a tabbed shell
            body = app_js
            # Try to capture inner JSX of return(...)
            # Fallback: append tab UI
            tab_shell = """ export default function App(){ const [tab,setTab]=React.useState('home'); const Link = ({id,children}) => <button onClick={()=>setTab(id)} style={{padding:8,marginRight:8,borderRadius:8,border:'1px solid #334155',background:tab===id?'#0f172a':'#111827',color:'#d7e7ff'}}>{children}</button>; return ( <div style={{minHeight:'100vh',background:'#0b0f16',color:'#d7e7ff',fontFamily:'system-ui',padding:24}}> <nav style={{marginBottom:16}}> <Link id="home">Home</Link> <Link id="about">About</Link> <Link id="products">Products</Link> <Link id="faq">FAQ</Link> <Link id="contact">Contact</Link> </nav> {tab==='home' && (<div><h1>Home</h1><p>Welcome to Digital Ninja.</p></div>)} {tab==='about' && (<div><h1>About</h1><p>About our project.</p></div>)} {tab==='products' && (<div><h1>Products</h1><ul><li>Product A</li><li>Product B</li></ul></div>)} {tab==='faq' && (<div><h1>FAQ</h1><p>Q: What is this? A: An AI-built demo.</p></div>)} {tab==='contact' && (<div><h1>Contact</h1><p>Email: hello@example.com</p></div>)} </div> ); } """
            app_js = tab_shell
    # Targeted content updates
    if "about" in m and "About" in app_js:
        app_js = re.sub(r"\{tab==='about'[^}]+\}", "{tab==='about' && (<div><h1>About</h1><p>About our project. Updated per your request.</p></div>)}", app_js)
    if "contact" in m and "Contact" in app_js:
        app_js = re.sub(r"\{tab==='contact'[^}]+\}", "{tab==='contact' && (<div><h1>Contact</h1><p>Email: contact@digital.ninja</p><p>Twitter: @digitalninja</p></div>)}", app_js)
    if "faq" in m and "FAQ" in app_js:
        app_js = re.sub(r"\{tab==='faq'[^}]+\}", "{tab==='faq' && (<div><h1>FAQ</h1><ul><li>How does this work? It is AI-built.</li><li>Can I export? Yes.</li></ul></div>)}", app_js)
    # Simple theme color tweak
    theme_match = re.search(r"(color|theme).*(#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}))", m)
    if theme_match:
        hex_color = theme_match.group(2)
        app_js = app_js.replace("#20d6ff", hex_color).replace("#46ff9b", hex_color)
    return app_js

@api_router.post("/projects/{project_id}/chat/build", response_model=ChatBuildResponse)
async def project_chat_build(project_id: str, req: ChatRequest, current_user: User = Depends(get_current_user)):
    project = await db.projects.find_one({"project_id": project_id, "user_id": current_user.user_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    files = project.get("files", [])
    app_file = None
    for f in files:
        if f.get("path", "").endswith("App.js") or f.get("path", "").endswith("App.jsx") or "App.js" in f.get("path",""):
            app_file = f
            break
    if not app_file:
        # create a minimal App.js if missing
        app_file = {"path": "src/App.js", "content": "export default function App(){return <div style={{padding:24}}>Hello</div>;}", "language": "js"}
        files.append(app_file)
    new_content = _apply_simple_build(req.message, app_file.get("content",""))
    if new_content == app_file.get("content",""):
        reply = "I evaluated your request, but no changes were necessary. Try asking to add tabs (Home, About, Contact, FAQ) or to change the theme color (e.g., set theme color to #ff4500)."
        return ChatBuildResponse(response=reply, file_updates=[])
    update = FileUpdate(path=app_file["path"], content=new_content)
    # Apply update in DB
    for i, f in enumerate(files):
        if f.get("path") == update.path:
            files[i] = {"path": update.path, "content": update.content, "language": f.get("language","js")}
            break
    else:
        files.append({"path": update.path, "content": update.content, "language": "js"})
    await db.projects.update_one(
        {"project_id": project_id, "user_id": current_user.user_id},
        {"$set": {"files": files, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    reply = "Applied your change. Preview should update. Ask me to add About/Contact/FAQ tabs or adjust theme colors for more."
    return ChatBuildResponse(response=reply, file_updates=[update])

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

# ==================== GITHUB PUSH ====================
class GitHubPushRequest(BaseModel):
    token: str
    owner: str
    repo: str
    branch: Optional[str] = "main"
    commit_message: Optional[str] = "Push from Digital Ninja"
    include_paths: Optional[List[str]] = None

IGNORE_DIRS = {".git", "node_modules", "build", "dist", ".next", ".cache", ".turbo", ".pytest_cache", "__pycache__"}
IGNORE_FILES = {".DS_Store", "yarn.lock", "package-lock.json"}

def _skip_path(path: Path) -> bool:
    if path.name in IGNORE_FILES:
        return True
    return any(part in IGNORE_DIRS for part in path.parts)

async def _gh_file_sha(client: httpx.AsyncClient, owner: str, repo: str, path: str, branch: Optional[str], headers: Dict[str, str]) -> Optional[str]:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    params = {"ref": branch} if branch else {}
    r = await client.get(url, headers=headers, params=params)
    if r.status_code == 200:
        return r.json().get("sha")
    return None

async def _gh_put_file(client: httpx.AsyncClient, owner: str, repo: str, path: str, content_b64: str, message: str, branch: Optional[str], sha: Optional[str], headers: Dict[str, str]) -> bool:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    payload = {"message": message, "content": content_b64}
    if branch:
        payload["branch"] = branch
    if sha:
        payload["sha"] = sha
    r = await client.put(url, headers=headers, json=payload)
    if r.status_code in (200, 201):
        return True
    if r.status_code == 422 and branch:
        r2 = await client.put(url, headers=headers, json={"message": message, "content": content_b64})
        return r2.status_code in (200, 201)
    return False

@api_router.post("/github/push")
async def push_github(req: GitHubPushRequest, current_user: User = Depends(get_current_user)):
    if not req.token or not req.owner or not req.repo:
        raise HTTPException(status_code=400, detail="Missing token/owner/repo")
    project_root = Path(__file__).resolve().parents[1]
    include = req.include_paths or ["frontend", "backend", "package.json", "pnpm-workspace.yaml", "docker-compose.yml", "README.md", "README_FINAL.md", "render.yaml", "vercel.json", ".gitignore"]
    files_to_push: List[Path] = []
    for p in include:
        target = (project_root / p).resolve()
        if target.is_file():
            if not _skip_path(target):
                files_to_push.append(target)
        elif target.is_dir():
            for path in target.rglob("*"):
                if path.is_file() and not _skip_path(path):
                    files_to_push.append(path)
    if not files_to_push:
        raise HTTPException(status_code=400, detail="No files found to push")
    headers = {
        "Authorization": f"token {req.token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "digital-ninja-app-builder"
    }
    pushed = 0
    async with httpx.AsyncClient(timeout=60.0) as client:
        for fpath in files_to_push:
            rel = str(fpath.relative_to(project_root)).replace("\\", "/")
            try:
                data = fpath.read_bytes()
                content_b64 = base64.b64encode(data).decode("utf-8")
                sha = await _gh_file_sha(client, req.owner, req.repo, rel, req.branch, headers)
                ok = await _gh_put_file(client, req.owner, req.repo, rel, content_b64, req.commit_message or "Push from Digital Ninja", req.branch, sha, headers)
                if ok:
                    pushed += 1
                else:
                    logging.error(f"Failed to push {rel}")
            except Exception as e:
                logging.error(f"Error pushing {rel}: {e}")
    return {"message": "Push completed", "files_pushed": pushed, "repo": f"{req.owner}/{req.repo}", "branch": req.branch or "default"}

# ==================== AUTONOMOUS AGENT ENDPOINT ====================
@api_router.post("/projects/autonomous/stream")
async def autonomous_agent_stream(project_data: ProjectCreate, current_user: User = Depends(get_current_user)):
    """
    Autonomous agent with 200-minute runtime, self-testing, and auto-fixing
    Like Replit Agent 3
    """
    async def event_generator():
        from autonomous_agent import AutonomousAgent

        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            error_payload = {
                "type": "error",
                "message": "Autonomous agent is not configured. Set OPENAI_API_KEY in the backend environment.",
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_payload)}\n\n"
            return

        progress_queue: asyncio.Queue = asyncio.Queue()

        async def progress_callback(update):
            payload = {
                "type": update.get("level", "info"),
                "message": update.get("message", ""),
                "timestamp": update.get("timestamp", datetime.now().isoformat())
            }
            await progress_queue.put(payload)

        agent = AutonomousAgent(
            project_id=str(uuid.uuid4()),
            openai_api_key=openai_key
        )

        await progress_queue.put({
            "type": "info",
            "message": "🤖 Autonomous Agent starting...",
            "timestamp": datetime.now().isoformat()
        })

        agent_task = asyncio.create_task(
            agent.run_autonomous_build(
                prompt=project_data.prompt,
                progress_callback=progress_callback,
                max_duration_minutes=200
            )
        )

        try:
            while True:
                if agent_task.done() and progress_queue.empty():
                    break

                try:
                    update = await asyncio.wait_for(progress_queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    continue

                yield f"data: {json.dumps(update)}\n\n"

            result = await agent_task

            if result.get("status") == "success":
                now = datetime.now(timezone.utc)
                project_id = str(uuid.uuid4())

                project_doc = {
                    "project_id": project_id,
                    "user_id": current_user.user_id,
                    "name": (project_data.prompt or "Autonomous Build")[:40],
                    "description": project_data.prompt or "",
                    "prompt": project_data.prompt or "",
                    "tech_stack": project_data.tech_stack,
                    "files": result["files"],
                    "status": "active",
                    "autonomous_build": True,
                    "test_results": result.get("test_results", {}),
                    "fixes_applied": result.get("fixes_applied", []),
                    "iterations": result.get("iterations", 0),
                    "duration_minutes": result.get("duration_minutes", 0),
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat()
                }
                await db.projects.insert_one(project_doc)

                completion_payload = {
                    "type": "complete",
                    "project_id": project_id,
                    "files": result["files"],
                    "test_results": result.get("test_results", {})
                }
                yield f"data: {json.dumps(completion_payload)}\n\n"
            else:
                error_payload = {
                    "type": "error",
                    "message": result.get("error", "Unknown error occurred during autonomous build."),
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(error_payload)}\n\n"

        except Exception as e:
            logger.error(f"Autonomous agent error: {e}")
            error_payload = {
                "type": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_payload)}\n\n"
        finally:
            if not agent_task.done():
                agent_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await agent_task
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ==================== VERSION CONTROL ENDPOINTS ====================
@api_router.post("/projects/{project_id}/snapshots")
async def create_snapshot(
    project_id: str,
    snapshot_data: SnapshotCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a snapshot of current project state"""
    project = await db.projects.find_one({"project_id": project_id, "user_id": current_user.user_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    result = await version_control.create_snapshot(
        project_id,
        current_user.user_id,
        project.get("files", []),
        snapshot_data.message,
        auto=False
    )
    return result

@api_router.get("/projects/{project_id}/snapshots")
async def list_snapshots(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """List all snapshots for a project"""
    snapshots = await version_control.list_snapshots(project_id)
    return {"snapshots": snapshots}

@api_router.post("/projects/{project_id}/snapshots/{snapshot_id}/restore")
async def restore_snapshot(
    project_id: str,
    snapshot_id: str,
    current_user: User = Depends(get_current_user)
):
    """Restore project to a specific snapshot"""
    result = await version_control.restore_snapshot(project_id, snapshot_id, current_user.user_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

# ==================== DISCUSSION MODE ENDPOINTS ====================
@api_router.post("/discuss", response_model=ChatResponse)
async def discussion_mode(
    request: DiscussionRequest,
    current_user: User = Depends(get_current_user)
):
    """Discussion mode - plan without building"""
    project_context = None
    if request.project_id:
        project = await db.projects.find_one({
            "project_id": request.project_id,
            "user_id": current_user.user_id
        })
        if project:
            project_context = {
                "name": project.get("name"),
                "files": project.get("files", [])
            }
    
    result = await discussion_service.discuss(
        request.message,
        project_context,
        request.history
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return ChatResponse(response=result["response"])

@api_router.post("/discuss/plan")
async def generate_implementation_plan(
    request: DiscussionRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate implementation plan for a feature"""
    result = await discussion_service.generate_implementation_plan(
        request.message,
        project_context=None
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result

@api_router.post("/discuss/analyze")
async def analyze_requirements(
    request: DiscussionRequest,
    current_user: User = Depends(get_current_user)
):
    """Analyze requirements and suggest clarifications"""
    result = await discussion_service.analyze_requirements(
        request.message,
        ask_questions=True
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result

# ==================== DEPLOYMENT ENDPOINTS ====================
@api_router.post("/projects/{project_id}/deploy")
async def deploy_project(
    project_id: str,
    deploy_req: DeployRequest,
    current_user: User = Depends(get_current_user)
):
    """One-click deployment to various platforms"""
    project = await db.projects.find_one({"project_id": project_id, "user_id": current_user.user_id})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    from deployment_service import DeploymentService
    deployment = DeploymentService()
    
    if deploy_req.platform == "vercel":
        result = await deployment.deploy_to_vercel(
            project.get("name"),
            project.get("files", []),
            deploy_req.env_vars
        )
    elif deploy_req.platform == "docker":
        result = await deployment.generate_docker_deployment(
            project.get("files", []),
            project.get("name")
        )
    else:
        result = await deployment.create_deployment_package(
            project.get("files", []),
            project.get("name")
        )
    
    # Save deployment info
    if result.get("success"):
        await db.projects.update_one(
            {"project_id": project_id},
            {"$set": {
                "deployment": result,
                "deployed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    return result

# ==================== FILE STORAGE ENDPOINTS ====================
@api_router.post("/storage/upload")
async def upload_file(
    file: bytes = Body(...),
    filename: str = Body(...),
    project_id: Optional[str] = Body(None),
    current_user: User = Depends(get_current_user)
):
    """Upload a file to storage"""
    result = await file_storage.upload_file(
        file,
        filename,
        current_user.user_id,
        project_id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    # Save file reference in database
    await db.project_files.insert_one(result)
    
    return result

@api_router.get("/storage/{file_id}")
async def get_file_info(file_id: str, current_user: User = Depends(get_current_user)):
    """Get file information"""
    file_info = await file_storage.get_file(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    return file_info

@api_router.delete("/storage/{file_id}")
async def delete_file(file_id: str, current_user: User = Depends(get_current_user)):
    """Delete a file from storage"""
    result = await file_storage.delete_file(file_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

# ==================== GENERIC CHAT ENDPOINT ====================
@api_router.post("/chat/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """Generic chat endpoint for general AI conversations"""
    try:
        ai_builder = AIBuilderService()
        # Use GPT-4 for general chat
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Build conversation history
        messages = [{"role": "system", "content": "You are a helpful AI assistant for the Digital Ninja App Builder. Help users with their questions about building applications, coding, and technical topics."}]
        for msg in request.history:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": request.message})
        
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        return ChatResponse(response=response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ONE-CLICK DEPLOYMENT ====================
@api_router.post("/projects/{project_id}/deploy")
async def deploy_project(
    project_id: str,
    platform: str = "vercel",
    current_user: User = Depends(get_current_user)
):
    """One-click deployment to Vercel, Netlify, or Railway"""
    try:
        # Get project
        project = await db.projects.find_one(
            {"project_id": project_id, "user_id": current_user.user_id},
            {"_id": 0}
        )
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        from one_click_deploy import OneClickDeployService
        deploy_service = OneClickDeployService()
        
        # Deploy
        result = await deploy_service.deploy(
            project_files=project.get("files", []),
            project_name=project.get("name", "digital-ninja-app"),
            platform=platform
        )
        
        if result["success"]:
            # Save deployment info
            await db.projects.update_one(
                {"project_id": project_id},
                {
                    "$set": {
                        "deployment": result,
                        "deployed_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        
        return result
    
    except Exception as e:
        logger.error(f"Deployment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/projects/{project_id}/deployment/status")
async def get_deployment_status(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Check deployment status"""
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": current_user.user_id},
        {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    deployment = project.get("deployment", {})
    if not deployment:
        return {"status": "not_deployed"}
    
    return deployment

# ==================== HEALTH CHECK & SETUP ====================
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "Digital Ninja App Builder", "version": "2.0.0"}

@app.get("/")
async def root():
    return {"message": "Digital Ninja App Builder API", "version": "2.0.0", "docs": "/docs"}

app.include_router(api_router)

import logging
logging.info("Setting up CORS for http://localhost:3000")
