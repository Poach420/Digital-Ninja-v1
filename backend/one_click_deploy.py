"""
One-Click Deployment Service
Deploy to Vercel, Netlify, or Railway with single click
"""
import os
import asyncio
import logging
from typing import Dict, Optional
import httpx
import json
import base64

logger = logging.getLogger(__name__)


class OneClickDeployService:
    """Deploy applications to various platforms with one click"""
    
    def __init__(self):
        self.vercel_token = os.getenv("VERCEL_TOKEN")
        self.netlify_token = os.getenv("NETLIFY_TOKEN")
        self.railway_token = os.getenv("RAILWAY_TOKEN")
    
    async def deploy_to_vercel(self, project_files: list, project_name: str) -> Dict:
        """Deploy to Vercel"""
        if not self.vercel_token:
            return {"success": False, "error": "VERCEL_TOKEN not configured"}
        
        try:
            # Create deployment
            deployment_data = {
                "name": project_name.lower().replace(" ", "-"),
                "files": [],
                "projectSettings": {
                    "framework": "create-react-app",
                    "buildCommand": "npm run build",
                    "outputDirectory": "build"
                }
            }
            
            # Add files
            for file in project_files:
                deployment_data["files"].append({
                    "file": file["path"],
                    "data": base64.b64encode(file["content"].encode()).decode()
                })
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.vercel.com/v13/deployments",
                    headers={
                        "Authorization": f"Bearer {self.vercel_token}",
                        "Content-Type": "application/json"
                    },
                    json=deployment_data
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    return {
                        "success": True,
                        "platform": "vercel",
                        "url": f"https://{result.get('url', '')}",
                        "deployment_id": result.get("id", ""),
                        "status": "deployed"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Vercel deployment failed: {response.text}"
                    }
        
        except Exception as e:
            logger.error(f"Vercel deployment error: {e}")
            return {"success": False, "error": str(e)}
    
    async def deploy_to_netlify(self, project_files: list, project_name: str) -> Dict:
        """Deploy to Netlify"""
        if not self.netlify_token:
            return {"success": False, "error": "NETLIFY_TOKEN not configured"}
        
        try:
            # Create site
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Create new site
                site_response = await client.post(
                    "https://api.netlify.com/api/v1/sites",
                    headers={
                        "Authorization": f"Bearer {self.netlify_token}",
                        "Content-Type": "application/json"
                    },
                    json={"name": project_name.lower().replace(" ", "-")}
                )
                
                if site_response.status_code not in [200, 201]:
                    return {"success": False, "error": "Failed to create Netlify site"}
                
                site_data = site_response.json()
                site_id = site_data["id"]
                
                # Prepare files for deployment
                files = {}
                for file in project_files:
                    files[file["path"]] = file["content"]
                
                # Deploy files
                deploy_response = await client.post(
                    f"https://api.netlify.com/api/v1/sites/{site_id}/deploys",
                    headers={
                        "Authorization": f"Bearer {self.netlify_token}",
                        "Content-Type": "application/zip"
                    },
                    json={"files": files}
                )
                
                if deploy_response.status_code in [200, 201]:
                    deploy_data = deploy_response.json()
                    return {
                        "success": True,
                        "platform": "netlify",
                        "url": deploy_data.get("ssl_url", deploy_data.get("url", "")),
                        "deployment_id": deploy_data.get("id", ""),
                        "status": "deployed"
                    }
                else:
                    return {"success": False, "error": "Netlify deployment failed"}
        
        except Exception as e:
            logger.error(f"Netlify deployment error: {e}")
            return {"success": False, "error": str(e)}
    
    async def deploy_to_railway(self, project_files: list, project_name: str) -> Dict:
        """Deploy to Railway"""
        if not self.railway_token:
            return {"success": False, "error": "RAILWAY_TOKEN not configured"}
        
        try:
            # Railway deployment via GraphQL API
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Create project
                create_project_query = """
                mutation {
                  projectCreate(input: {name: "%s"}) {
                    id
                  }
                }
                """ % project_name
                
                response = await client.post(
                    "https://backboard.railway.app/graphql/v2",
                    headers={
                        "Authorization": f"Bearer {self.railway_token}",
                        "Content-Type": "application/json"
                    },
                    json={"query": create_project_query}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    project_id = data.get("data", {}).get("projectCreate", {}).get("id")
                    
                    if project_id:
                        return {
                            "success": True,
                            "platform": "railway",
                            "project_id": project_id,
                            "url": f"https://railway.app/project/{project_id}",
                            "status": "created",
                            "message": "Project created. Connect your GitHub repo to complete deployment."
                        }
                
                return {"success": False, "error": "Railway project creation failed"}
        
        except Exception as e:
            logger.error(f"Railway deployment error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_deployment_status(self, platform: str, deployment_id: str) -> Dict:
        """Check deployment status"""
        try:
            if platform == "vercel":
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://api.vercel.com/v13/deployments/{deployment_id}",
                        headers={"Authorization": f"Bearer {self.vercel_token}"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "status": data.get("readyState", "UNKNOWN"),
                            "url": f"https://{data.get('url', '')}",
                            "created": data.get("createdAt", "")
                        }
            
            elif platform == "netlify":
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://api.netlify.com/api/v1/deploys/{deployment_id}",
                        headers={"Authorization": f"Bearer {self.netlify_token}"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "status": data.get("state", "unknown"),
                            "url": data.get("ssl_url", data.get("url", "")),
                            "created": data.get("created_at", "")
                        }
            
            return {"status": "unknown"}
        
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def deploy(self, project_files: list, project_name: str, platform: str = "vercel") -> Dict:
        """Deploy to specified platform"""
        if platform == "vercel":
            return await self.deploy_to_vercel(project_files, project_name)
        elif platform == "netlify":
            return await self.deploy_to_netlify(project_files, project_name)
        elif platform == "railway":
            return await self.deploy_to_railway(project_files, project_name)
        else:
            return {"success": False, "error": f"Unknown platform: {platform}"}
