import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_projects():
    client = AsyncIOMotorClient('mongodb+srv://Poach420:Osc00sKdELuHKezH@cluster0.tavzohv.mongodb.net/digital_ninja_app')
    db = client.digital_ninja_app
    
    # Get the most recent projects
    projects = await db.projects.find().sort('created_at', -1).limit(2).to_list(length=2)
    
    for idx, proj in enumerate(projects, 1):
        print(f'\n{"="*60}')
        print(f'PROJECT {idx} - {proj.get("name", "N/A")}')
        print(f'{"="*60}')
        print(f'ID: {proj.get("project_id")}')
        print(f'Description: {proj.get("description", "N/A")}')
        print(f'Total Files: {len(proj.get("files", []))}')
        print(f'\nFile Structure:')
        
        for file in proj.get('files', []):
            path = file.get('path', 'unknown')
            content_len = len(file.get('content', ''))
            print(f'  📄 {path:40s} ({content_len:,} characters)')
        
        # Check index.html for multi-page indicators
        index_file = next((f for f in proj.get('files', []) if 'index.html' in f.get('path', '')), None)
        if index_file:
            content = index_file.get('content', '')
            
            # Look for navigation/links
            nav_count = content.lower().count('<nav')
            link_count = content.lower().count('<a href')
            section_count = content.lower().count('<section')
            
            print(f'\n  Analysis of index.html:')
            print(f'    - Navigation elements: {nav_count}')
            print(f'    - Links/anchors: {link_count}')
            print(f'    - Sections: {section_count}')
            print(f'    - Total size: {len(content):,} characters')

if __name__ == '__main__':
    asyncio.run(check_projects())
