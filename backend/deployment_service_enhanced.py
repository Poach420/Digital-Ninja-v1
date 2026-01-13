"""
One-Click Deployment Service
Supports Vercel, Render, Railway, and custom deployments
"""
import os
import asyncio
import logging
import json
import httpx
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DeploymentService:
    """One-click deployment to multiple platforms"""
    
    def __init__(self):
        self.vercel_token = os.getenv("VERCEL_TOKEN")
        self.render_token = os.getenv("RENDER_API_KEY")
        self.railway_token = os.getenv("RAILWAY_TOKEN")
    
    async def deploy_to_vercel(self, project_files: List[Dict], project_name: str) -> Dict:
        """Deploy to Vercel"""
        try:
            if not self.vercel_token:
                return {"success": False, "error": "VERCEL_TOKEN not configured"}
            
            # Create deployment payload
            files = []
            for file in project_files:
                files.append({
                    "file": file["path"],
                    "data": file["content"]
                })
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.vercel.com/v13/deployments",
                    headers={
                        "Authorization": f"Bearer {self.vercel_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "name": project_name.lower().replace(" ", "-"),
                        "files": files,
                        "projectSettings": {
                            "framework": "create-react-app"
                        }
                    },
                    timeout=60.0
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    return {
                        "success": True,
                        "platform": "vercel",
                        "url": f"https://{data.get('url')}",
                        "deployment_id": data.get("id"),
                        "status": "deploying"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Vercel API error: {response.status_code}"
                    }
        
        except Exception as e:
            logger.error(f"Vercel deployment error: {e}")
            return {"success": False, "error": str(e)}
    
    async def deploy_to_render(self, project_files: List[Dict], project_name: str, repo_url: str) -> Dict:
        """Deploy to Render"""
        try:
            if not self.render_token:
                return {"success": False, "error": "RENDER_API_KEY not configured"}
            
            # Create a new web service on Render
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.render.com/v1/services",
                    headers={
                        "Authorization": f"Bearer {self.render_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "type": "web_service",
                        "name": project_name.lower().replace(" ", "-"),
                        "repo": repo_url,
                        "branch": "main",
                        "buildCommand": "cd frontend && npm install && npm run build",
                        "startCommand": "cd frontend && npm start",
                        "envVars": []
                    },
                    timeout=60.0
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    return {
                        "success": True,
                        "platform": "render",
                        "url": data.get("service", {}).get("serviceDetails", {}).get("url"),
                        "service_id": data.get("service", {}).get("id"),
                        "status": "deploying"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Render API error: {response.status_code}"
                    }
        
        except Exception as e:
            logger.error(f"Render deployment error: {e}")
            return {"success": False, "error": str(e)}
    
    async def deploy_to_railway(self, project_files: List[Dict], project_name: str) -> Dict:
        """Deploy to Railway"""
        try:
            if not self.railway_token:
                return {"success": False, "error": "RAILWAY_TOKEN not configured"}
            
            # Railway GraphQL API
            query = """
            mutation CreateProject($name: String!) {
                projectCreate(input: { name: $name }) {
                    id
                    name
                }
            }
            """
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://backboard.railway.app/graphql/v2",
                    headers={
                        "Authorization": f"Bearer {self.railway_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "query": query,
                        "variables": {
                            "name": project_name
                        }
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    project_id = data.get("data", {}).get("projectCreate", {}).get("id")
                    
                    return {
                        "success": True,
                        "platform": "railway",
                        "project_id": project_id,
                        "status": "created",
                        "message": "Project created. Push code to deploy."
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Railway API error: {response.status_code}"
                    }
        
        except Exception as e:
            logger.error(f"Railway deployment error: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_deployment_config(self, project_files: List[Dict], tech_stack: Dict) -> Dict:
        """Generate deployment configuration files"""
        configs = {}
        
        # Vercel config
        configs["vercel.json"] = {
            "version": 2,
            "builds": [
                {
                    "src": "frontend/package.json",
                    "use": "@vercel/static-build",
                    "config": {
                        "distDir": "build"
                    }
                }
            ],
            "routes": [
                {
                    "src": "/api/(.*)",
                    "dest": "/api/$1"
                },
                {
                    "src": "/(.*)",
                    "dest": "/index.html"
                }
            ]
        }
        
        # Render config
        configs["render.yaml"] = """
services:
  - type: web
    name: {name}-frontend
    env: node
    buildCommand: cd frontend && npm install && npm run build
    startCommand: cd frontend && npx serve -s build
    
  - type: web
    name: {name}-backend
    env: python
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT
"""
        
        # Docker Compose (for any platform)
        configs["docker-compose.yml"] = """
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - backend
      
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - MONGO_URL=${MONGO_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - mongodb
      
  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
"""
        
        # Dockerfile for frontend
        configs["frontend/Dockerfile"] = """
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

RUN npm install -g serve

EXPOSE 3000

CMD ["serve", "-s", "build", "-l", "3000"]
"""
        
        # Dockerfile for backend
        configs["backend/Dockerfile"] = """
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        
        return configs
    
    async def check_deployment_status(self, platform: str, deployment_id: str) -> Dict:
        """Check deployment status"""
        try:
            if platform == "vercel":
                if not self.vercel_token:
                    return {"error": "VERCEL_TOKEN not configured"}
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://api.vercel.com/v13/deployments/{deployment_id}",
                        headers={"Authorization": f"Bearer {self.vercel_token}"},
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "status": data.get("readyState"),
                            "url": f"https://{data.get('url')}",
                            "created": data.get("createdAt")
                        }
            
            elif platform == "render":
                if not self.render_token:
                    return {"error": "RENDER_API_KEY not configured"}
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://api.render.com/v1/services/{deployment_id}",
                        headers={"Authorization": f"Bearer {self.render_token}"},
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "status": data.get("service", {}).get("serviceDetails", {}).get("deployStatus"),
                            "url": data.get("service", {}).get("serviceDetails", {}).get("url")
                        }
            
            return {"error": f"Platform {platform} not supported"}
            
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return {"error": str(e)}
    
    async def setup_custom_domain(self, platform: str, deployment_id: str, domain: str) -> Dict:
        """Setup custom domain for deployment"""
        try:
            if platform == "vercel":
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"https://api.vercel.com/v9/projects/{deployment_id}/domains",
                        headers={
                            "Authorization": f"Bearer {self.vercel_token}",
                            "Content-Type": "application/json"
                        },
                        json={"name": domain},
                        timeout=30.0
                    )
                    
                    if response.status_code in [200, 201]:
                        return {
                            "success": True,
                            "domain": domain,
                            "status": "configuring"
                        }
            
            return {"success": False, "error": "Custom domain setup not available for this platform"}
            
        except Exception as e:
            logger.error(f"Domain setup error: {e}")
            return {"success": False, "error": str(e)}
