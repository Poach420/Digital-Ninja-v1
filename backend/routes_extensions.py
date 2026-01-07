# CRM, Blog, Landing Pages, SMTP, PDF Routes Extension
# Import this in server.py to add all missing modules

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from pathlib import Path

# Import services
import sys
sys.path.insert(0, str(Path(__file__).parent))
from services.email_service import email_service
from services.pdf_service import pdf_service

# Create extension router
ext_router = APIRouter(prefix="/api")

# ==================== CRM MODELS ====================
class Contact(BaseModel):
    model_config = ConfigDict(extra="ignore")
    contact_id: str
    team_id: str
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    status: str = "active"
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

class ContactCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    tags: List[str] = []

class Lead(BaseModel):
    model_config = ConfigDict(extra="ignore")
    lead_id: str
    team_id: str
    contact_id: Optional[str] = None
    title: str
    value: float
    stage: str = "new"
    probability: int = 0
    expected_close_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class LeadCreate(BaseModel):
    contact_id: Optional[str] = None
    title: str
    value: float
    stage: str = "new"
    probability: int = 0

# ==================== BLOG MODELS ====================
class BlogPost(BaseModel):
    model_config = ConfigDict(extra="ignore")
    post_id: str
    team_id: str
    author_id: str
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    published: bool = False
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class BlogPostCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    featured_image: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    published: bool = False

# ==================== LANDING PAGE MODELS ====================
class LandingPage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    landing_id: str
    team_id: str
    name: str
    slug: str
    template: str = "default"
    sections: List[dict] = []
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    published: bool = False
    created_at: datetime
    updated_at: datetime

class LandingPageCreate(BaseModel):
    name: str
    slug: str
    template: str = "default"
    sections: List[dict] = []

# ==================== HELPER IMPORTS ====================
# These will be imported from main server.py
from server import get_current_user, User, db

# ==================== CRM ENDPOINTS ====================
@ext_router.get("/crm/contacts", response_model=List[Contact])
async def get_contacts(current_user: User = Depends(get_current_user)):
    contacts = await db.contacts.find({"team_id": current_user.team_id}, {"_id": 0}).to_list(100)
    for contact in contacts:
        if isinstance(contact.get('created_at'), str):
            contact['created_at'] = datetime.fromisoformat(contact['created_at'])
        if isinstance(contact.get('updated_at'), str):
            contact['updated_at'] = datetime.fromisoformat(contact['updated_at'])
    return contacts

@ext_router.post("/crm/contacts", response_model=Contact)
async def create_contact(contact_data: ContactCreate, current_user: User = Depends(get_current_user)):
    contact = Contact(
        contact_id=f"contact_{uuid.uuid4().hex[:12]}",
        team_id=current_user.team_id,
        name=contact_data.name,
        email=contact_data.email,
        phone=contact_data.phone,
        company=contact_data.company,
        tags=contact_data.tags,
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    contact_dict = contact.model_dump()
    contact_dict['created_at'] = contact_dict['created_at'].isoformat()
    contact_dict['updated_at'] = contact_dict['updated_at'].isoformat()
    await db.contacts.insert_one(contact_dict)
    return contact

@ext_router.get("/crm/contacts/{contact_id}", response_model=Contact)
async def get_contact(contact_id: str, current_user: User = Depends(get_current_user)):
    contact = await db.contacts.find_one({"contact_id": contact_id, "team_id": current_user.team_id}, {"_id": 0})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    if isinstance(contact.get('created_at'), str):
        contact['created_at'] = datetime.fromisoformat(contact['created_at'])
    if isinstance(contact.get('updated_at'), str):
        contact['updated_at'] = datetime.fromisoformat(contact['updated_at'])
    return Contact(**contact)

@ext_router.delete("/crm/contacts/{contact_id}")
async def delete_contact(contact_id: str, current_user: User = Depends(get_current_user)):
    result = await db.contacts.delete_one({"contact_id": contact_id, "team_id": current_user.team_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted successfully"}

@ext_router.get("/crm/leads", response_model=List[Lead])
async def get_leads(current_user: User = Depends(get_current_user)):
    leads = await db.leads.find({"team_id": current_user.team_id}, {"_id": 0}).to_list(100)
    for lead in leads:
        if isinstance(lead.get('created_at'), str):
            lead['created_at'] = datetime.fromisoformat(lead['created_at'])
        if isinstance(lead.get('updated_at'), str):
            lead['updated_at'] = datetime.fromisoformat(lead['updated_at'])
        if lead.get('expected_close_date') and isinstance(lead['expected_close_date'], str):
            lead['expected_close_date'] = datetime.fromisoformat(lead['expected_close_date'])
    return leads

@ext_router.post("/crm/leads", response_model=Lead)
async def create_lead(lead_data: LeadCreate, current_user: User = Depends(get_current_user)):
    lead = Lead(
        lead_id=f"lead_{uuid.uuid4().hex[:12]}",
        team_id=current_user.team_id,
        contact_id=lead_data.contact_id,
        title=lead_data.title,
        value=lead_data.value,
        stage=lead_data.stage,
        probability=lead_data.probability,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    lead_dict = lead.model_dump()
    lead_dict['created_at'] = lead_dict['created_at'].isoformat()
    lead_dict['updated_at'] = lead_dict['updated_at'].isoformat()
    await db.leads.insert_one(lead_dict)
    return lead

# ==================== BLOG ENDPOINTS ====================
@ext_router.get("/blog/posts", response_model=List[BlogPost])
async def get_blog_posts(published_only: bool = False, current_user: User = Depends(get_current_user)):
    query = {"team_id": current_user.team_id}
    if published_only:
        query["published"] = True
    posts = await db.blog_posts.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    for post in posts:
        if isinstance(post.get('created_at'), str):
            post['created_at'] = datetime.fromisoformat(post['created_at'])
        if isinstance(post.get('updated_at'), str):
            post['updated_at'] = datetime.fromisoformat(post['updated_at'])
        if post.get('published_at') and isinstance(post['published_at'], str):
            post['published_at'] = datetime.fromisoformat(post['published_at'])
    return posts

@ext_router.post("/blog/posts", response_model=BlogPost)
async def create_blog_post(post_data: BlogPostCreate, current_user: User = Depends(get_current_user)):
    slug = post_data.title.lower().replace(" ", "-").replace("'", "")
    post = BlogPost(
        post_id=f"post_{uuid.uuid4().hex[:12]}",
        team_id=current_user.team_id,
        author_id=current_user.user_id,
        title=post_data.title,
        slug=slug,
        content=post_data.content,
        excerpt=post_data.excerpt,
        featured_image=post_data.featured_image,
        category=post_data.category,
        tags=post_data.tags,
        published=post_data.published,
        published_at=datetime.now(timezone.utc) if post_data.published else None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    post_dict = post.model_dump()
    post_dict['created_at'] = post_dict['created_at'].isoformat()
    post_dict['updated_at'] = post_dict['updated_at'].isoformat()
    if post_dict.get('published_at'):
        post_dict['published_at'] = post_dict['published_at'].isoformat()
    await db.blog_posts.insert_one(post_dict)
    return post

@ext_router.get("/blog/posts/{post_id}", response_model=BlogPost)
async def get_blog_post(post_id: str, current_user: User = Depends(get_current_user)):
    post = await db.blog_posts.find_one({"post_id": post_id, "team_id": current_user.team_id}, {"_id": 0})
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    if isinstance(post.get('created_at'), str):
        post['created_at'] = datetime.fromisoformat(post['created_at'])
    if isinstance(post.get('updated_at'), str):
        post['updated_at'] = datetime.fromisoformat(post['updated_at'])
    if post.get('published_at') and isinstance(post['published_at'], str):
        post['published_at'] = datetime.fromisoformat(post['published_at'])
    return BlogPost(**post)

@ext_router.delete("/blog/posts/{post_id}")
async def delete_blog_post(post_id: str, current_user: User = Depends(get_current_user)):
    result = await db.blog_posts.delete_one({"post_id": post_id, "team_id": current_user.team_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return {"message": "Blog post deleted successfully"}

# ==================== LANDING PAGES ENDPOINTS ====================
@ext_router.get("/landing-pages", response_model=List[LandingPage])
async def get_landing_pages(current_user: User = Depends(get_current_user)):
    pages = await db.landing_pages.find({"team_id": current_user.team_id}, {"_id": 0}).to_list(100)
    for page in pages:
        if isinstance(page.get('created_at'), str):
            page['created_at'] = datetime.fromisoformat(page['created_at'])
        if isinstance(page.get('updated_at'), str):
            page['updated_at'] = datetime.fromisoformat(page['updated_at'])
    return pages

@ext_router.post("/landing-pages", response_model=LandingPage)
async def create_landing_page(page_data: LandingPageCreate, current_user: User = Depends(get_current_user)):
    page = LandingPage(
        landing_id=f"landing_{uuid.uuid4().hex[:12]}",
        team_id=current_user.team_id,
        name=page_data.name,
        slug=page_data.slug,
        template=page_data.template,
        sections=page_data.sections,
        published=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    page_dict = page.model_dump()
    page_dict['created_at'] = page_dict['created_at'].isoformat()
    page_dict['updated_at'] = page_dict['updated_at'].isoformat()
    await db.landing_pages.insert_one(page_dict)
    return page

@ext_router.get("/landing-pages/{landing_id}", response_model=LandingPage)
async def get_landing_page(landing_id: str, current_user: User = Depends(get_current_user)):
    page = await db.landing_pages.find_one({"landing_id": landing_id, "team_id": current_user.team_id}, {"_id": 0})
    if not page:
        raise HTTPException(status_code=404, detail="Landing page not found")
    if isinstance(page.get('created_at'), str):
        page['created_at'] = datetime.fromisoformat(page['created_at'])
    if isinstance(page.get('updated_at'), str):
        page['updated_at'] = datetime.fromisoformat(page['updated_at'])
    return LandingPage(**page)

@ext_router.delete("/landing-pages/{landing_id}")
async def delete_landing_page(landing_id: str, current_user: User = Depends(get_current_user)):
    result = await db.landing_pages.delete_one({"landing_id": landing_id, "team_id": current_user.team_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Landing page not found")
    return {"message": "Landing page deleted successfully"}

# ==================== EMAIL & PDF ENDPOINTS ====================
@ext_router.post("/email/send-verification")
async def send_verification(email: EmailStr, current_user: User = Depends(get_current_user)):
    verification_link = f"https://your-app.com/verify?token=verification_token"
    result = await email_service.send_verification_email(email, verification_link)
    return {"success": result, "message": "Verification email sent" if result else "Email service not configured"}

@ext_router.post("/email/send-password-reset")
async def send_password_reset(email: EmailStr):
    reset_link = f"https://your-app.com/reset-password?token=reset_token"
    result = await email_service.send_password_reset_email(email, reset_link)
    return {"success": result, "message": "Reset email sent" if result else "Email service not configured"}

@ext_router.post("/pdf/generate-invoice")
async def generate_invoice(current_user: User = Depends(get_current_user)):
    invoice_data = {
        "invoice_number": f"INV-{uuid.uuid4().hex[:8].upper()}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "customer_name": current_user.name,
        "customer_email": current_user.email,
        "items": [
            {"description": "Pro Plan Subscription", "amount": 299.0}
        ],
        "subtotal": 299.0,
        "vat_rate": 15.0
    }
    output_path = f"/tmp/invoice_{invoice_data['invoice_number']}.pdf"
    result = await pdf_service.generate_invoice_pdf(invoice_data, output_path)
    return {"success": result, "invoice_number": invoice_data['invoice_number'], "path": output_path if result else None}
