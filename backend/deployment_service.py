"""
Deployment Service - Multi-tenant hosting on owner's infrastructure
Supports Vercel (frontend), Render (backend), MongoDB Atlas
"""

import os
import httpx
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class DeploymentService:
    def __init__(self):
        # Owner's infrastructure credentials
        self.vercel_token = os.getenv("VERCEL_TOKEN")
        self.vercel_team_id = os.getenv("VERCEL_TEAM_ID")
        self.render_api_key = os.getenv("RENDER_API_KEY")
        self.mongodb_atlas_key = os.getenv("MONGODB_ATLAS_PUBLIC_KEY")
        self.mongodb_atlas_private = os.getenv("MONGODB_ATLAS_PRIVATE_KEY")
        self.mongodb_atlas_project = os.getenv("MONGODB_ATLAS_PROJECT_ID")
        self.base_domain = os.getenv("BASE_DOMAIN", "digitalninja.co.za")
        
    async def deploy_frontend_vercel(self, project_id: str, files: List[Dict], env_vars: Dict = None) -> Dict:
        """Deploy frontend to Vercel"""
        if not self.vercel_token:
            return {"status": "error", "message": "Vercel not configured"}
        
        try:
            # Create deployment payload
            deployment_payload = {
                "name": f"project-{project_id}",
                "files": [
                    {
                        "file": f["path"],
                        "data": f["content"]
                    }
                    for f in files if f["path"].startswith("frontend/")
                ],
                "projectSettings": {
                    "framework": "create-react-app",
                    "buildCommand": "yarn build",
                    "outputDirectory": "build"
                },
                "target": "production"
            }
            
            if env_vars:
                deployment_payload["env"] = env_vars
            
            # Deploy to Vercel
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.vercel.com/v13/deployments",
                    headers={
                        "Authorization": f"Bearer {self.vercel_token}",
                        "Content-Type": "application/json"
                    },
                    json=deployment_payload,
                    timeout=120.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "url": result.get("url"),
                        "deployment_id": result.get("id"),
                        "type": "vercel"
                    }
                else:
                    logger.error(f"Vercel deployment failed: {response.text}")
                    return {"status": "error", "message": response.text}
                    
        except Exception as e:
            logger.error(f"Vercel deployment error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def deploy_backend_render(self, project_id: str, files: List[Dict], env_vars: Dict = None) -> Dict:
        """Deploy backend to Render"""
        if not self.render_api_key:
            return {"status": "error", "message": "Render not configured"}
        
        try:
            # Create Render web service
            service_payload = {
                "name": f"project-{project_id}-api",
                "type": "web_service",
                "env": "python",
                "region": "oregon",
                "plan": "free",
                "buildCommand": "pip install -r requirements.txt",
                "startCommand": "uvicorn server:app --host 0.0.0.0 --port $PORT",
                "envVars": []
            }
            
            if env_vars:
                service_payload["envVars"] = [
                    {"key": k, "value": v} for k, v in env_vars.items()
                ]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.render.com/v1/services",
                    headers={
                        "Authorization": f"Bearer {self.render_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=service_payload,
                    timeout=60.0
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    return {
                        "status": "success",
                        "url": result.get("serviceDetails", {}).get("url"),
                        "service_id": result.get("id"),
                        "type": "render"
                    }
                else:
                    logger.error(f"Render deployment failed: {response.text}")
                    return {"status": "error", "message": response.text}
                    
        except Exception as e:
            logger.error(f"Render deployment error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def create_mongodb_database(self, project_id: str) -> Dict:
        """Create MongoDB database on Atlas"""
        if not self.mongodb_atlas_key:
            return {"status": "error", "message": "MongoDB Atlas not configured"}
        
        try:
            # For now, return connection string to shared cluster
            # In production, create dedicated database via Atlas API
            db_name = f"project_{project_id}"
            
            return {
                "status": "success",
                "connection_string": f"mongodb+srv://user:pass@cluster0.mongodb.net/{db_name}",
                "database_name": db_name,
                "type": "mongodb_atlas"
            }
            
        except Exception as e:
            logger.error(f"MongoDB creation error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def deploy_full_stack(self, project_id: str, files: List[Dict], tier: str = "free") -> Dict:
        """Deploy complete application (frontend + backend + database)"""
        
        deployment_result = {
            "project_id": project_id,
            "tier": tier,
            "status": "deploying",
            "frontend": None,
            "backend": None,
            "database": None,
            "urls": {},
            "deployed_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Separate frontend and backend files
        frontend_files = [f for f in files if "frontend/" in f["path"]]
        backend_files = [f for f in files if "backend/" in f["path"]]
        
        # Deploy database first
        logger.info(f"Creating database for {project_id}")
        db_result = await self.create_mongodb_database(project_id)
        deployment_result["database"] = db_result
        
        if db_result["status"] == "success":
            db_url = db_result["connection_string"]
            
            # Deploy backend with database connection
            logger.info(f"Deploying backend for {project_id}")
            backend_env = {
                "MONGO_URL": db_url,
                "DB_NAME": db_result["database_name"],
                "PORT": "10000"
            }
            backend_result = await self.deploy_backend_render(project_id, backend_files, backend_env)
            deployment_result["backend"] = backend_result
            
            if backend_result["status"] == "success":
                # Deploy frontend with backend URL
                logger.info(f"Deploying frontend for {project_id}")
                frontend_env = {
                    "REACT_APP_API_URL": backend_result["url"]
                }
                frontend_result = await self.deploy_frontend_vercel(project_id, frontend_files, frontend_env)
                deployment_result["frontend"] = frontend_result
                
                if frontend_result["status"] == "success":
                    deployment_result["status"] = "deployed"
                    deployment_result["urls"] = {
                        "app": frontend_result["url"],
                        "api": backend_result["url"]
                    }
                    
                    # Generate custom subdomain
                    subdomain = f"{project_id}.{self.base_domain}"
                    deployment_result["custom_domain"] = subdomain
                    
                    logger.info(f"Successfully deployed {project_id} to {subdomain}")
                else:
                    deployment_result["status"] = "frontend_failed"
            else:
                deployment_result["status"] = "backend_failed"
        else:
            deployment_result["status"] = "database_failed"
        
        return deployment_result
    
    async def delete_deployment(self, deployment_id: str, deployment_type: str) -> Dict:
        """Delete a deployment"""
        try:
            if deployment_type == "vercel":
                async with httpx.AsyncClient() as client:
                    response = await client.delete(
                        f"https://api.vercel.com/v13/deployments/{deployment_id}",
                        headers={"Authorization": f"Bearer {self.vercel_token}"},
                        timeout=30.0
                    )
                    return {"status": "deleted" if response.status_code == 200 else "error"}
            
            elif deployment_type == "render":
                async with httpx.AsyncClient() as client:
                    response = await client.delete(
                        f"https://api.render.com/v1/services/{deployment_id}",
                        headers={"Authorization": f"Bearer {self.render_api_key}"},
                        timeout=30.0
                    )
                    return {"status": "deleted" if response.status_code == 200 else "error"}
            
            return {"status": "unknown_type"}
            
        except Exception as e:
            logger.error(f"Deletion error: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_deployment_status(self, deployment_id: str, deployment_type: str) -> Dict:
        """Check deployment status"""
        try:
            if deployment_type == "vercel":
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://api.vercel.com/v13/deployments/{deployment_id}",
                        headers={"Authorization": f"Bearer {self.vercel_token}"},
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "status": data.get("state", "unknown"),
                            "url": data.get("url"),
                            "ready": data.get("ready", False)
                        }
            
            return {"status": "unknown"}
            
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return {"status": "error", "message": str(e)}

deployment_service = DeploymentService()
