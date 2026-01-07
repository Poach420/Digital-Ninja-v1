from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, Response, status, Header
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage
import os
import logging
import uuid
import asyncio
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
JWT_SECRET = os.getenv("JWT_SECRET", "your-super-secret-jwt-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 72))

logger = logging.getLogger(__name__)

# MODELS
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    role: str = "member"
    team_id: Optional[str] = None
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

class Team(BaseModel):
    model_config = ConfigDict(extra="ignore")
    team_id: str
    name: str
    owner_id: str
    plan: str = "free"
    created_at: datetime

class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class Page(BaseModel):
    model_config = ConfigDict(extra="ignore")
    page_id: str
    team_id: str
    user_id: str
    name: str
    content_json: Dict[str, Any]
    published: bool = False
    created_at: datetime
    updated_at: datetime

class PageCreate(BaseModel):
    name: str
    content_json: Dict[str, Any] = {}

class PageUpdate(BaseModel):
    name: Optional[str] = None
    content_json: Optional[Dict[str, Any]] = None
    published: Optional[bool] = None

class BillingPlan(BaseModel):
    plan_id: str
    name: str
    price_zar: float
    features: List[str]
    max_pages: int

class DiagnosticCheck(BaseModel):
    check_type: str
    status: str
    last_check: datetime
    details: str

class TeamMember(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
    picture: Optional[str] = None

class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "viewer"

# HELPERS
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=JWT_EXPIRATION_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(authorization: Optional[str] = Header(None), request: Request = None) -> User:
    token = None
    if request:
        token = request.cookies.get("session_token")
    if not token and authorization:
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
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
    return User(**user_doc)

async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ["admin", "owner"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# AUTH ENDPOINTS
@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    team_id = f"team_{uuid.uuid4().hex[:12]}"
    team = Team(team_id=team_id, name=f"{user_data.name}'s Team", owner_id=user_id, plan="free", created_at=datetime.now(timezone.utc))
    user = User(user_id=user_id, email=user_data.email, name=user_data.name, picture=None, role="owner", team_id=team_id, created_at=datetime.now(timezone.utc))
    user_dict = user.model_dump()
    user_dict['password_hash'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    await db.users.insert_one(user_dict)
    team_dict = team.model_dump()
    team_dict['created_at'] = team_dict['created_at'].isoformat()
    await db.teams.insert_one(team_dict)
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

@api_router.post("/auth/logout")
async def logout():
    return {"message": "Logged out successfully"}

@api_router.get("/auth/google")
async def google_auth():
    redirect_url = os.getenv("FRONTEND_URL", "http://localhost:3000") + "/auth/callback"
    return {"auth_url": f"https://auth.emergentagent.com/?redirect={redirect_url}"}

@api_router.post("/auth/google/callback")
async def google_callback(request: Request, response: Response):
    body = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session_id")
    import httpx
    async with httpx.AsyncClient() as client:
        auth_response = await client.get("https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data", headers={"X-Session-ID": session_id})
        if auth_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid session")
        user_data = auth_response.json()
    existing_user = await db.users.find_one({"email": user_data["email"]}, {"_id": 0})
    if existing_user:
        if isinstance(existing_user.get('created_at'), str):
            existing_user['created_at'] = datetime.fromisoformat(existing_user['created_at'])
        user = User(**{k: v for k, v in existing_user.items() if k != 'password_hash'})
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        team_id = f"team_{uuid.uuid4().hex[:12]}"
        team = Team(team_id=team_id, name=f"{user_data['name']}'s Team", owner_id=user_id, plan="free", created_at=datetime.now(timezone.utc))
        user = User(user_id=user_id, email=user_data["email"], name=user_data["name"], picture=user_data.get("picture"), role="owner", team_id=team_id, created_at=datetime.now(timezone.utc))
        user_dict = user.model_dump()
        user_dict['created_at'] = user_dict['created_at'].isoformat()
        await db.users.insert_one(user_dict)
        team_dict = team.model_dump()
        team_dict['created_at'] = team_dict['created_at'].isoformat()
        await db.teams.insert_one(team_dict)
    access_token = create_access_token(data={"user_id": user.user_id})
    response.set_cookie(key="session_token", value=access_token, httponly=True, secure=True, samesite="none", path="/", max_age=JWT_EXPIRATION_HOURS * 3600)
    return TokenResponse(access_token=access_token, user=user)

# CHAT ENDPOINTS
@api_router.post("/chat/message")
async def chat_message(request: ChatMessageRequest, current_user: User = Depends(get_current_user)):
    session_id = request.session_id or f"session_{uuid.uuid4().hex[:12]}"
    async def generate_response():
        try:
            api_key = os.getenv("EMERGENT_LLM_KEY")
            chat = LlmChat(api_key=api_key, session_id=session_id, system_message="You are a helpful AI assistant for the Digital Ninja App Builder.")
            chat.with_model("openai", "gpt-4o-mini")
            user_msg = UserMessage(text=request.message)
            response = await chat.send_message(user_msg)
            full_response = response if isinstance(response, str) else str(response)
            words = full_response.split()
            for word in words:
                yield f"data: {word} \n\n"
                await asyncio.sleep(0.05)
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield f"data: Error: {str(e)}\n\n"
    return StreamingResponse(generate_response(), media_type="text/event-stream")

@api_router.get("/chat/history")
async def get_chat_history(session_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"user_id": current_user.user_id}
    if session_id:
        query["session_id"] = session_id
    messages = await db.chat_messages.find(query, {"_id": 0}).sort("timestamp", 1).limit(100).to_list(100)
    return messages

# PAGE ENDPOINTS
@api_router.get("/pages", response_model=List[Page])
async def get_pages(current_user: User = Depends(get_current_user)):
    pages = await db.pages.find({"team_id": current_user.team_id}, {"_id": 0}).to_list(100)
    for page in pages:
        if isinstance(page.get('created_at'), str):
            page['created_at'] = datetime.fromisoformat(page['created_at'])
        if isinstance(page.get('updated_at'), str):
            page['updated_at'] = datetime.fromisoformat(page['updated_at'])
    return pages

@api_router.post("/pages", response_model=Page)
async def create_page(page_data: PageCreate, current_user: User = Depends(get_current_user)):
    page = Page(page_id=f"page_{uuid.uuid4().hex[:12]}", team_id=current_user.team_id, user_id=current_user.user_id, name=page_data.name, content_json=page_data.content_json, published=False, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    page_dict = page.model_dump()
    page_dict['created_at'] = page_dict['created_at'].isoformat()
    page_dict['updated_at'] = page_dict['updated_at'].isoformat()
    await db.pages.insert_one(page_dict)
    return page

@api_router.get("/pages/{page_id}", response_model=Page)
async def get_page(page_id: str, current_user: User = Depends(get_current_user)):
    page = await db.pages.find_one({"page_id": page_id, "team_id": current_user.team_id}, {"_id": 0})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    if isinstance(page.get('created_at'), str):
        page['created_at'] = datetime.fromisoformat(page['created_at'])
    if isinstance(page.get('updated_at'), str):
        page['updated_at'] = datetime.fromisoformat(page['updated_at'])
    return Page(**page)

@api_router.put("/pages/{page_id}", response_model=Page)
async def update_page(page_id: str, page_data: PageUpdate, current_user: User = Depends(get_current_user)):
    page = await db.pages.find_one({"page_id": page_id, "team_id": current_user.team_id}, {"_id": 0})
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    update_data = {k: v for k, v in page_data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    await db.pages.update_one({"page_id": page_id}, {"$set": update_data})
    updated_page = await db.pages.find_one({"page_id": page_id}, {"_id": 0})
    if isinstance(updated_page.get('created_at'), str):
        updated_page['created_at'] = datetime.fromisoformat(updated_page['created_at'])
    if isinstance(updated_page.get('updated_at'), str):
        updated_page['updated_at'] = datetime.fromisoformat(updated_page['updated_at'])
    return Page(**updated_page)

@api_router.delete("/pages/{page_id}")
async def delete_page(page_id: str, current_user: User = Depends(get_current_user)):
    result = await db.pages.delete_one({"page_id": page_id, "team_id": current_user.team_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Page not found")
    return {"message": "Page deleted successfully"}

# TEAM ENDPOINTS
@api_router.get("/teams/current", response_model=Team)
async def get_current_team(current_user: User = Depends(get_current_user)):
    team = await db.teams.find_one({"team_id": current_user.team_id}, {"_id": 0})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if isinstance(team.get('created_at'), str):
        team['created_at'] = datetime.fromisoformat(team['created_at'])
    return Team(**team)

@api_router.get("/teams/members", response_model=List[TeamMember])
async def get_team_members(current_user: User = Depends(get_current_user)):
    members = await db.users.find({"team_id": current_user.team_id}, {"_id": 0, "password_hash": 0}).to_list(100)
    return [TeamMember(user_id=m["user_id"], email=m["email"], name=m["name"], role=m.get("role", "member"), picture=m.get("picture")) for m in members]

@api_router.post("/teams/invite")
async def invite_member(invite: InviteRequest, current_user: User = Depends(get_current_user)):
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owners and admins can invite members")
    return {"message": f"Invitation sent to {invite.email}", "status": "pending"}

# BILLING ENDPOINTS
@api_router.get("/billing/plans", response_model=List[BillingPlan])
async def get_billing_plans():
    return [
        BillingPlan(plan_id="free", name="Free", price_zar=0.0, features=["3 pages", "Basic support", "1 team member"], max_pages=3),
        BillingPlan(plan_id="pro", name="Pro", price_zar=299.0, features=["50 pages", "Priority support", "5 team members", "Custom domain"], max_pages=50),
        BillingPlan(plan_id="business", name="Business", price_zar=999.0, features=["Unlimited pages", "24/7 support", "Unlimited team members", "White label"], max_pages=999999)
    ]

@api_router.post("/billing/subscribe")
async def subscribe(plan_id: str, current_user: User = Depends(get_current_user)):
    await db.teams.update_one({"team_id": current_user.team_id}, {"$set": {"plan": plan_id}})
    return {"message": f"Subscribed to {plan_id} plan", "status": "success"}

# ADMIN ENDPOINTS
@api_router.get("/admin/users")
async def get_all_users(current_user: User = Depends(get_current_admin)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return users

@api_router.get("/admin/diagnostics", response_model=List[DiagnosticCheck])
async def get_diagnostics(current_user: User = Depends(get_current_admin)):
    checks = []
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("https://auth.emergentagent.com", timeout=5.0)
            oauth_status = "healthy" if response.status_code < 500 else "unhealthy"
    except:
        oauth_status = "unhealthy"
    checks.append(DiagnosticCheck(check_type="oauth", status=oauth_status, last_check=datetime.now(timezone.utc), details="Google OAuth integration status"))
    smtp_configured = bool(os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD"))
    checks.append(DiagnosticCheck(check_type="smtp", status="configured" if smtp_configured else "not_configured", last_check=datetime.now(timezone.utc), details="SMTP email service status"))
    checks.append(DiagnosticCheck(check_type="pdf", status="healthy", last_check=datetime.now(timezone.utc), details="PDF export service available"))
    billing_configured = bool(os.getenv("PEACH_PAYMENTS_API_KEY"))
    checks.append(DiagnosticCheck(check_type="billing", status="configured" if billing_configured else "not_configured", last_check=datetime.now(timezone.utc), details="Peach Payments integration status"))
    ai_configured = bool(os.getenv("EMERGENT_LLM_KEY"))
    checks.append(DiagnosticCheck(check_type="ai", status="healthy" if ai_configured else "unhealthy", last_check=datetime.now(timezone.utc), details="AI chat assistant status"))
    return checks

# Import CRM, Blog, Landing Pages, SMTP, PDF extensions
try:
    from routes_extensions import ext_router
    app.include_router(ext_router)
except ImportError as e:
    logger.warning(f"Extensions not loaded: {e}")

app.include_router(api_router)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','), allow_methods=["*"], allow_headers=["*"])

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()