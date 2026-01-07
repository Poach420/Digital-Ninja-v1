# Migration Guide - Remove Emergent Dependencies

## Overview
This guide helps you migrate from Emergent LLM API to direct OpenAI integration and deploy independently.

---

## 1. REPLACE EMERGENT LLM WITH OPENAI

### Current (Emergent Integration)
```python
# backend/ai_builder_service.py
from emergentintegrations.llm.chat import LlmChat, UserMessage

chat = LlmChat(
    api_key=os.getenv("EMERGENT_LLM_KEY"),
    session_id=session_id,
    system_message=system_message
)
chat.with_model("openai", "gpt-4o")
response = await chat.send_message(user_msg)
```

### Replace With (Direct OpenAI)
```python
# backend/ai_builder_service.py
import openai
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = await client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=4000
)

result = response.choices[0].message.content
```

### Update requirements.txt
```bash
# Remove
emergentintegrations

# Add
openai>=1.12.0
```

### Update .env
```bash
# Remove
EMERGENT_LLM_KEY=sk-emergent-76924Ca13Fe786dC7E

# Add
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_KEY
```

### Get OpenAI Key
1. Go to: https://platform.openai.com/api-keys
2. Create new secret key
3. Copy to .env file
4. Cost: ~$0.01 per app generation (GPT-4o)

---

## 2. DEPLOY TO RENDER + VERCEL

### Backend Deployment (Render)

**Step 1: Create Render Account**
- Sign up: https://dashboard.render.com/register
- Connect GitHub repository

**Step 2: Create Web Service**
```yaml
# render.yaml (create in root)
services:
  - type: web
    name: ai-app-builder-backend
    env: python
    region: oregon
    plan: free  # or starter ($7/month)
    buildCommand: pip install -r backend/requirements.txt
    startCommand: cd backend && uvicorn builder_server:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: MONGO_URL
        sync: false
      - key: DB_NAME
        value: ai_builder_db
      - key: JWT_SECRET
        generateValue: true
      - key: OPENAI_API_KEY
        sync: false
      - key: CORS_ORIGINS
        value: "*"
```

**Step 3: Add Environment Variables**
```bash
# In Render dashboard
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/db
DB_NAME=ai_builder_db
JWT_SECRET=your-random-secret-key-32-chars
OPENAI_API_KEY=sk-proj-YOUR_KEY
CORS_ORIGINS=https://your-app.vercel.app
```

**Step 4: Deploy**
- Push to GitHub main branch
- Render auto-deploys
- Get URL: https://ai-app-builder-backend.onrender.com

---

### Frontend Deployment (Vercel)

**Step 1: Install Vercel CLI**
```bash
npm install -g vercel
vercel login
```

**Step 2: Configure Project**
```bash
cd frontend
vercel
# Follow prompts:
# - Set root directory: frontend
# - Override build command: yarn build
# - Override output directory: build
```

**Step 3: Add Environment Variable**
```bash
# In Vercel dashboard or CLI
vercel env add REACT_APP_BACKEND_URL
# Value: https://ai-app-builder-backend.onrender.com
```

**Step 4: Deploy**
```bash
vercel --prod
# Get URL: https://your-app.vercel.app
```

**Step 5: Update Backend CORS**
```bash
# In Render, update CORS_ORIGINS
CORS_ORIGINS=https://your-app.vercel.app
```

---

## 3. MONGODB ATLAS SETUP

### Create Database

**Step 1: Create Account**
- Go to: https://www.mongodb.com/cloud/atlas/register
- Select free M0 cluster

**Step 2: Create Cluster**
- Choose AWS or Google Cloud
- Select region closest to Render deployment
- Cluster name: AIBuilder

**Step 3: Create Database User**
```
Username: aibuilder_user
Password: Generate secure password
Role: Read and write to any database
```

**Step 4: Configure Network Access**
```
IP Address: 0.0.0.0/0 (allow all)
Or add Render's IP ranges
```

**Step 5: Get Connection String**
```
mongodb+srv://aibuilder_user:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

**Step 6: Add to Render Environment**
```bash
MONGO_URL=mongodb+srv://aibuilder_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/ai_builder_db?retryWrites=true&w=majority
```

---

## 4. PAYFAST INTEGRATION (ZAR PAYMENTS)

### Why PayFast Instead of Peach Payments?
- PayFast is South Africa's leading payment gateway
- Better integration, lower fees
- Supports ZAR directly

### Setup PayFast

**Step 1: Create Account**
- Go to: https://www.payfast.co.za
- Sign up for merchant account
- Get test credentials

**Step 2: Get API Credentials**
```
Merchant ID: 10000100
Merchant Key: 46f0cd694581a
Passphrase: jt7NOE43FZPn (set in settings)
```

**Step 3: Update Backend**

```python
# backend/billing_service.py
import hashlib
import urllib.parse

class PayFastService:
    def __init__(self):
        self.merchant_id = os.getenv("PAYFAST_MERCHANT_ID")
        self.merchant_key = os.getenv("PAYFAST_MERCHANT_KEY")
        self.passphrase = os.getenv("PAYFAST_PASSPHRASE")
        self.sandbox = os.getenv("PAYFAST_SANDBOX", "true") == "true"
        
    def generate_payment_url(self, amount, item_name, user_email):
        """Generate PayFast payment URL"""
        
        # Payment data
        data = {
            'merchant_id': self.merchant_id,
            'merchant_key': self.merchant_key,
            'return_url': f'{os.getenv("FRONTEND_URL")}/payment/success',
            'cancel_url': f'{os.getenv("FRONTEND_URL")}/payment/cancel',
            'notify_url': f'{os.getenv("BACKEND_URL")}/api/payfast/notify',
            'email_address': user_email,
            'amount': f'{amount:.2f}',
            'item_name': item_name,
        }
        
        # Generate signature
        signature = self.generate_signature(data)
        data['signature'] = signature
        
        # Build URL
        base_url = 'https://sandbox.payfast.co.za/eng/process' if self.sandbox else 'https://www.payfast.co.za/eng/process'
        query_string = urllib.parse.urlencode(data)
        
        return f'{base_url}?{query_string}'
    
    def generate_signature(self, data):
        """Generate MD5 signature"""
        # Sort data
        sorted_data = sorted(data.items())
        # Create parameter string
        param_string = '&'.join([f'{k}={urllib.parse.quote_plus(str(v))}' for k, v in sorted_data])
        # Add passphrase
        param_string += f'&passphrase={urllib.parse.quote_plus(self.passphrase)}'
        # Generate signature
        return hashlib.md5(param_string.encode()).hexdigest()

payfast = PayFastService()
```

**Step 4: Add Payment Endpoints**

```python
# backend/builder_server.py

@api_router.post("/billing/create-payment")
async def create_payment(
    plan_id: str,
    current_user: User = Depends(get_current_user)
):
    """Create PayFast payment for plan subscription"""
    
    plans = {
        'pro': {'amount': 299.0, 'name': 'Pro Plan - Monthly'},
        'agency': {'amount': 999.0, 'name': 'Agency Plan - Monthly'}
    }
    
    if plan_id not in plans:
        raise HTTPException(400, "Invalid plan")
    
    plan = plans[plan_id]
    
    # Generate payment URL
    payment_url = payfast.generate_payment_url(
        amount=plan['amount'],
        item_name=plan['name'],
        user_email=current_user.email
    )
    
    return {"payment_url": payment_url}

@api_router.post("/payfast/notify")
async def payfast_notify(request: Request):
    """Handle PayFast payment notification"""
    
    form_data = await request.form()
    
    # Verify signature
    if not payfast.verify_signature(dict(form_data)):
        raise HTTPException(400, "Invalid signature")
    
    # Update user subscription
    # ... implementation
    
    return {"status": "ok"}
```

**Step 5: Environment Variables**
```bash
# Add to Render
PAYFAST_MERCHANT_ID=10000100
PAYFAST_MERCHANT_KEY=46f0cd694581a
PAYFAST_PASSPHRASE=jt7NOE43FZPn
PAYFAST_SANDBOX=true  # false for production
```

**Step 6: Test Payment Flow**
```bash
# Test credentials (sandbox)
Card Number: 4000000000000002
CVV: 123
Expiry: Any future date
```

---

## 5. REMOVE ALL EMERGENT DEPENDENCIES

### Files to Update

**backend/requirements.txt**
```diff
- emergentintegrations
+ openai>=1.12.0
```

**backend/ai_builder_service.py**
```diff
- from emergentintegrations.llm.chat import LlmChat, UserMessage
+ from openai import AsyncOpenAI
```

**backend/.env**
```diff
- EMERGENT_LLM_KEY=sk-emergent-76924Ca13Fe786dC7E
+ OPENAI_API_KEY=sk-proj-YOUR_KEY
```

**Remove Emergent Auth (if using Google OAuth)**
```python
# Replace backend OAuth endpoints with standard Google OAuth flow
# Use google-auth library instead
```

### Verification Checklist
- [ ] No `emergentintegrations` imports
- [ ] No `EMERGENT_` environment variables
- [ ] All API calls use direct OpenAI
- [ ] All deployments on your infrastructure
- [ ] No Emergent URLs in code

---

## 6. CUSTOM DOMAIN SETUP

### Add Custom Domain to Vercel

```bash
# In Vercel dashboard
1. Go to Domains
2. Add domain: app.yourdomain.com
3. Configure DNS:

# DNS Records (at your domain registrar)
Type: CNAME
Name: app
Value: cname.vercel-dns.com
```

### SSL Certificate
- Automatic via Vercel
- Or use Cloudflare for additional security

---

## 7. COST BREAKDOWN

### Monthly Costs (Self-Hosted)

**Development/Testing:**
```
Render Free Tier: $0
Vercel Hobby: $0
MongoDB Atlas M0: $0
OpenAI API (100 generations): ~$1
Total: ~$1/month
```

**Production (50-100 users):**
```
Render Starter: $7/month
Vercel Pro: $20/month
MongoDB M10: $57/month
OpenAI API (1000 generations): ~$10
PayFast fees: 2.9% + R2 per transaction
Total: ~$94/month + transaction fees
```

**Revenue (50 users):**
```
50 users × R299 = R14,950/month (~$800)
Costs: ~$100/month
Profit: ~$700/month (87% margin)
```

---

## 8. TESTING MIGRATION

### Test OpenAI Integration
```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Expected: List of models including gpt-4o
```

### Test Deployment
```bash
# Backend
curl https://your-app.onrender.com/api/auth/register \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","password":"test123"}'

# Frontend
open https://your-app.vercel.app
```

### Test PayFast
```bash
# Create test payment
curl https://your-app.onrender.com/api/billing/create-payment \
  -X POST \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"plan_id":"pro"}'

# Opens PayFast sandbox
```

---

## 9. PRODUCTION CHECKLIST

### Before Going Live

**Security:**
- [ ] Change all JWT secrets
- [ ] Use production MongoDB cluster
- [ ] Enable CORS whitelist (not *)
- [ ] Use HTTPS everywhere
- [ ] Rotate API keys monthly

**Performance:**
- [ ] Enable MongoDB indexes
- [ ] Add Redis caching
- [ ] CDN for static assets
- [ ] Database backups enabled

**Monitoring:**
- [ ] Render/Vercel error logging
- [ ] MongoDB Atlas alerts
- [ ] OpenAI usage monitoring
- [ ] PayFast transaction logs

**Legal:**
- [ ] Privacy policy
- [ ] Terms of service
- [ ] POPIA compliance (South Africa)
- [ ] Cookie consent

---

## 10. SUPPORT & MAINTENANCE

### Updating OpenAI Model
```python
# Change model version
chat.with_model("openai", "gpt-4o-mini")  # Cheaper
chat.with_model("openai", "gpt-4-turbo")  # Faster
chat.with_model("openai", "o1")           # Best quality
```

### Scaling Up
```
Free → Paid tiers as you grow:
- Render: Free → Starter ($7) → Standard ($25)
- MongoDB: M0 (free) → M10 ($57) → M20 ($120)
- Vercel: Hobby (free) → Pro ($20)
```

### Backup Strategy
```bash
# MongoDB backup
mongodump --uri="$MONGO_URL" --out=/backup

# GitHub auto-backup
git push origin main  # Automatic on every change
```

---

## SUMMARY

### Migration Steps:
1. ✅ Replace Emergent LLM with OpenAI SDK
2. ✅ Deploy backend to Render
3. ✅ Deploy frontend to Vercel
4. ✅ Setup MongoDB Atlas
5. ✅ Integrate PayFast for payments
6. ✅ Remove all Emergent dependencies
7. ✅ Test everything thoroughly
8. ✅ Go live!

### Time Required:
- OpenAI migration: 30 minutes
- Render deployment: 1 hour
- Vercel deployment: 30 minutes
- MongoDB setup: 30 minutes
- PayFast integration: 2 hours
- **Total: ~5 hours**

### Result:
- ✅ Fully independent platform
- ✅ No Emergent dependencies
- ✅ Deployed on your infrastructure
- ✅ ZAR payments via PayFast
- ✅ ~87% profit margin

**You now own and control everything!** 🚀
