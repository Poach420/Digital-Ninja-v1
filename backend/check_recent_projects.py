import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def check_projects():
    client = AsyncIOMotorClient("mongodb+srv://Poach420:Poach420@cluster0.tavzohv.mongodb.net/digital_ninja_app")
    db = client.digital_ninja_app
    
    # Get most recent 3 projects
    projects = await db.projects.find().sort("created_at", -1).limit(3).to_list(length=3)
    
    for i, project in enumerate(projects, 1):
        print(f"\n{'='*60}")
        print(f"PROJECT {i}: {project.get('name', 'Unnamed')}")
        print(f"{'='*60}")
        print(f"ID: {project['_id']}")
        print(f"Description: {project.get('description', 'N/A')}")
        print(f"Created: {project.get('created_at', 'N/A')}")
        print(f"Number of files: {len(project.get('files', []))}")
        
        print(f"\nFile structure:")
        for file in project.get('files', []):
            path = file.get('path', 'unknown')
            content_len = len(file.get('content', ''))
            print(f"  📄 {path} ({content_len:,} chars)")
        
        # Check for multi-page indicators
        all_content = ' '.join([f.get('content', '') for f in project.get('files', [])])
        has_router = 'BrowserRouter' in all_content or 'react-router' in all_content
        has_route = 'Route' in all_content and 'path=' in all_content
        
        file_paths = [f.get('path', '') for f in project.get('files', [])]
        has_components_folder = any('components/' in p for p in file_paths)
        has_pages_folder = any('pages/' in p or 'Page.js' in p for p in file_paths)
        
        print(f"\n📊 Analysis:")
        print(f"  React Router: {'✅ YES' if has_router else '❌ NO'}")
        print(f"  Routes defined: {'✅ YES' if has_route else '❌ NO'}")
        print(f"  Components folder: {'✅ YES' if has_components_folder else '❌ NO'}")
        print(f"  Multiple pages: {'✅ YES' if has_pages_folder else '❌ NO'}")
        
        # Sample first file content
        if project.get('files'):
            first_file = project['files'][0]
            content_preview = first_file.get('content', '')[:500]
            print(f"\n📝 First file preview ({first_file.get('path', 'unknown')}):")
            print(content_preview[:400] + "..." if len(content_preview) > 400 else content_preview)
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_projects())
