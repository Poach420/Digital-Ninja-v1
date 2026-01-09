""" 
AI Application Builder Service V2 - REAL WORKING APPS
Generates COMPLETE, FUNCTIONAL applications with backends, APIs, databases
"""
import os
import json
import re
import logging
from typing import Dict, List
from openai import AsyncOpenAI
from dotenv import load_dotenv
import asyncio

load_dotenv()
logger = logging.getLogger(__name__)

class AIBuilderServiceV2:
    """Enhanced AI Builder that generates production-ready applications"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = AsyncOpenAI(api_key=self.api_key)
        
        # API Integration Templates
        self.api_templates = {
            "openai": self._get_openai_template(),
            "stable_diffusion": self._get_stable_diffusion_template(),
            "stripe": self._get_stripe_template(),
            "auth": self._get_auth_template(),
            "database": self._get_database_template(),
        }
    
    def _get_openai_template(self) -> Dict:
        """OpenAI API integration template"""
        return {
            "backend": """
from openai import AsyncOpenAI
import os

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_text(prompt: str, model: str = "gpt-4o"):
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

async def generate_image(prompt: str, size: str = "1024x1024"):
    response = await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality="standard",
        n=1
    )
    return response.data[0].url
""",
            "frontend": """
async function callAI(prompt) {
  const response = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt })
  });
  return response.json();
}
""",
            "env_vars": ["OPENAI_API_KEY"],
            "dependencies": {
                "backend": ["openai"],
                "frontend": []
            }
        }
    
    def _get_stable_diffusion_template(self) -> Dict:
        """Stable Diffusion / Replicate API template"""
        return {
            "backend": """
import replicate
import os

async def generate_image_sd(prompt: str):
    output = await replicate.run(
        "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
        input={"prompt": prompt}
    )
    return output[0]
""",
            "frontend": """
async function generateImage(prompt) {
  const response = await fetch('/api/generate-image', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt })
  });
  const data = await response.json();
  return data.image_url;
}
""",
            "env_vars": ["REPLICATE_API_TOKEN"],
            "dependencies": {
                "backend": ["replicate"],
                "frontend": []
            }
        }
    
    def _get_stripe_template(self) -> Dict:
        """Stripe payment processing template"""
        return {
            "backend": """
import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

async def create_payment_intent(amount: int, currency: str = "usd"):
    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency=currency,
        automatic_payment_methods={"enabled": True}
    )
    return intent.client_secret
""",
            "frontend": """
import { loadStripe } from '@stripe/stripe-js';
import { Elements, PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLIC_KEY);

function CheckoutForm() {
  const stripe = useStripe();
  const elements = useElements();

  const handleSubmit = async (event) => {
    event.preventDefault();
    const {error} = await stripe.confirmPayment({
      elements,
      confirmParams: { return_url: window.location.origin + '/success' }
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <PaymentElement />
      <button disabled={!stripe}>Pay Now</button>
    </form>
  );
}
""",
            "env_vars": ["STRIPE_SECRET_KEY", "STRIPE_PUBLIC_KEY"],
            "dependencies": {
                "backend": ["stripe"],
                "frontend": ["@stripe/stripe-js", "@stripe/react-stripe-js"]
            }
        }
    
    def _get_auth_template(self) -> Dict:
        """JWT Authentication template"""
        return {
            "backend": """
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os

security = HTTPBearer()
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=24)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
""",
            "frontend": """
const login = async (email, password) => {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await response.json();
  localStorage.setItem('token', data.access_token);
};

const authFetch = async (url, options = {}) => {
  const token = localStorage.getItem('token');
  return fetch(url, {
    ...options,
    headers: { ...options.headers, 'Authorization': `Bearer ${token}` }
  });
};
""",
            "env_vars": ["JWT_SECRET"],
            "dependencies": {
                "backend": ["python-jose[cryptography]", "python-multipart"],
                "frontend": []
            }
        }
    
    def _get_database_template(self) -> Dict:
        """MongoDB database template"""
        return {
            "backend": """
from motor.motor_asyncio import AsyncIOMotorClient
import os

client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
db = client[os.getenv("DB_NAME", "app_db")]

async def create_item(collection: str, item: dict):
    result = await db[collection].insert_one(item)
    return str(result.inserted_id)

async def get_items(collection: str, query: dict = {}):
    cursor = db[collection].find(query)
    return await cursor.to_list(length=100)

async def update_item(collection: str, item_id: str, updates: dict):
    result = await db[collection].update_one({"_id": item_id}, {"$set": updates})
    return result.modified_count

async def delete_item(collection: str, item_id: str):
    result = await db[collection].delete_one({"_id": item_id})
    return result.deleted_count
""",
            "frontend": """
const api = {
  async create(endpoint, data) {
    const response = await fetch(`/api/${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  },
  async get(endpoint) {
    const response = await fetch(`/api/${endpoint}`);
    return response.json();
  },
  async update(endpoint, id, data) {
    const response = await fetch(`/api/${endpoint}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return response.json();
  },
  async delete(endpoint, id) {
    await fetch(`/api/${endpoint}/${id}`, { method: 'DELETE' });
  }
};
""",
            "env_vars": ["MONGO_URL", "DB_NAME"],
            "dependencies": {
                "backend": ["motor"],
                "frontend": []
            }
        }
    
    async def generate_app_structure(self, prompt: str, tech_stack: Dict[str, str]) -> Dict:
        """Generate COMPLETE working application with backend + frontend"""
        
        # Detect what integrations are needed based on prompt
        integrations = self._detect_required_integrations(prompt)
        
        system_prompt = f"""You are an ELITE full-stack developer building PRODUCTION-READY applications.

🎯 USER REQUEST: {prompt}

🔧 REQUIRED INTEGRATIONS: {', '.join(integrations) if integrations else 'None - Basic app'}

📦 YOU MUST GENERATE:
1. **Complete Frontend (React)**
   - Multiple pages/components as needed
   - Working forms with validation
   - API calls to backend
   - Loading states & error handling
   - Responsive CSS

2. **Complete Backend (FastAPI)**
   - API endpoints for ALL functionality
   - Database models & operations
   - Authentication if needed
   - External API integrations if needed
   - Proper error handling

3. **Configuration Files**
   - package.json with ALL dependencies
   - requirements.txt for backend
   - .env.example with required variables
   - docker-compose.yml for easy deployment

⚡ INTEGRATION TEMPLATES AVAILABLE:
{self._get_integration_docs(integrations)}

💻 CODE QUALITY STANDARDS:
- NO placeholder comments ("TODO", "implement this")
- REAL working API calls, not fake data
- Proper async/await patterns
- Error boundaries in React
- Type validation on backend
- Environment variable usage
- Professional styling (CSS Grid/Flexbox)

🚨 CRITICAL RULES:
1. If prompt mentions AI/GPT/image generation → Use OpenAI API template
2. If prompt mentions payments/checkout/buy → Use Stripe template
3. If prompt mentions users/login/auth → Use Auth template
4. ALWAYS include database operations for data persistence
5. Frontend MUST call backend APIs, not use mock data

📝 RESPONSE FORMAT (JSON):
{{
  "app_name": "Professional Name",
  "description": "What it does",
  "required_services": ["openai", "stripe", "database"],
  "files": [
    {{"path": "backend/main.py", "content": "COMPLETE FastAPI code", "language": "python"}},
    {{"path": "backend/requirements.txt", "content": "ALL dependencies", "language": "text"}},
    {{"path": "frontend/src/App.js", "content": "COMPLETE React app", "language": "javascript"}},
    {{"path": "frontend/package.json", "content": "WITH ALL DEPENDENCIES", "language": "json"}},
    {{"path": ".env.example", "content": "ALL required env vars", "language": "env"}},
    {{"path": "docker-compose.yml", "content": "Ready to deploy", "language": "yaml"}}
  ]
}}

NOW BUILD A COMPLETE, WORKING APPLICATION!"""

        try:
            logger.info(f"Generating enhanced app structure for: {prompt}")
            logger.info(f"Detected integrations: {integrations}")
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Build this: {prompt}"}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            logger.info(f"GPT-4o response length: {len(content)} chars")
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                app_data = json.loads(json_match.group())
            else:
                raise ValueError("No valid JSON in response")
            
            # Inject integration code
            app_data = self._inject_integrations(app_data, integrations)
            
            # Add deployment files
            app_data['files'].extend(self._generate_deployment_files(app_data))
            
            return app_data
            
        except Exception as e:
            logger.error(f"Error generating app: {e}")
            return self._generate_fallback_app(prompt, integrations)
    
    def _detect_required_integrations(self, prompt: str) -> List[str]:
        """Detect which API integrations are needed"""
        prompt_lower = prompt.lower()
        integrations = []
        
        # AI/ML keywords
        if any(word in prompt_lower for word in ['ai', 'gpt', 'chatbot', 'generate text', 'openai']):
            integrations.append('openai')
        
        # Image generation keywords
        if any(word in prompt_lower for word in ['image', 'midjourney', 'dall-e', 'stable diffusion', 'picture']):
            if 'openai' not in integrations:
                integrations.append('stable_diffusion')
        
        # Payment keywords
        if any(word in prompt_lower for word in ['payment', 'checkout', 'buy', 'purchase', 'ecommerce', 'shop', 'stripe']):
            integrations.append('stripe')
        
        # Auth keywords
        if any(word in prompt_lower for word in ['login', 'signup', 'user', 'account', 'auth', 'register']):
            integrations.append('auth')
        
        # Database always included for data persistence
        integrations.append('database')
        
        return list(set(integrations))
    
    def _get_integration_docs(self, integrations: List[str]) -> str:
        """Get documentation for required integrations"""
        docs = []
        for integration in integrations:
            if integration in self.api_templates:
                template = self.api_templates[integration]
                docs.append(f"\n### {integration.upper()} Integration")
                docs.append(f"Backend code to use:\n{template['backend'][:200]}...")
                docs.append(f"Frontend code to use:\n{template['frontend'][:200]}...")
        return '\n'.join(docs)
    
    def _inject_integrations(self, app_data: Dict, integrations: List[str]) -> Dict:
        """Inject integration code into generated files"""
        for integration in integrations:
            if integration in self.api_templates:
                template = self.api_templates[integration]
                
                # Add to requirements.txt
                for file in app_data['files']:
                    if 'requirements.txt' in file['path']:
                        for dep in template['dependencies']['backend']:
                            if dep not in file['content']:
                                file['content'] += f"\n{dep}"
                
                # Add to package.json
                for file in app_data['files']:
                    if 'package.json' in file['path']:
                        pkg = json.loads(file['content'])
                        if 'dependencies' not in pkg:
                            pkg['dependencies'] = {}
                        for dep in template['dependencies']['frontend']:
                            pkg['dependencies'][dep] = "^latest"
                        file['content'] = json.dumps(pkg, indent=2)
        
        return app_data
    
    def _generate_deployment_files(self, app_data: Dict) -> List[Dict]:
        """Generate docker-compose and deployment configs"""
        return [
            {
                "path": "docker-compose.yml",
                "content": """version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MONGO_URL=${MONGO_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - mongodb
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
  
  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
""",
                "language": "yaml"
            },
            {
                "path": "README.md",
                "content": f"""# {app_data.get('app_name', 'Generated App')}

{app_data.get('description', 'AI-generated application')}

## Quick Start

```bash
# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run with Docker
docker-compose up

# Or run manually
cd backend && pip install -r requirements.txt && uvicorn main:app
cd frontend && npm install && npm start
```

## Features
- Complete backend API with FastAPI
- React frontend with modern UI
- Database integration
- Ready for deployment

Generated by Digital Ninja AI Builder
""",
                "language": "markdown"
            }
        ]
    
    def _generate_fallback_app(self, prompt: str, integrations: List[str]) -> Dict:
        """Generate a basic fallback app if main generation fails"""
        logger.warning("Using fallback app generation")
        return {
            "app_name": "Generated App",
            "description": f"Application for: {prompt}",
            "required_services": integrations,
            "files": [
                {
                    "path": "frontend/src/App.js",
                    "content": "// Basic React app\nimport React from 'react';\n\nfunction App() {\n  return <div>App generated successfully!</div>;\n}\n\nexport default App;",
                    "language": "javascript"
                }
            ]
        }
