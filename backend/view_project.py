import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def view_project():
    client = AsyncIOMotorClient('mongodb+srv://Poach420:Osc00sKdELuHKezH@cluster0.tavzohv.mongodb.net/digital_ninja_app')
    db = client.digital_ninja_app
    
    # Get the most recent project
    project = await db.projects.find_one({'project_id': 'proj_894fb3e9705d'})
    
    if not project:
        print("Project not found")
        return
    
    print(f'\n{"="*80}')
    print(f'PROJECT: {project.get("name")}')
    print(f'{"="*80}\n')
    
    # Check the main App.js file
    app_file = next((f for f in project.get('files', []) if 'App.js' in f.get('path', '')), None)
    
    if app_file:
        content = app_file.get('content', '')
        print(f'App.js Content (first 2000 characters):')
        print('='*80)
        print(content[:2000])
        print('\n...\n')
        
        # Check for routing/pages
        has_router = 'BrowserRouter' in content or 'Router' in content or 'Route' in content
        has_pages = 'pages/' in content or '/pages/' in content
        has_components = 'components/' in content or '/components/' in content
        
        print(f'\n{"="*80}')
        print(f'ANALYSIS:')
        print(f'  - Has React Router: {has_router}')
        print(f'  - References pages/: {has_pages}')
        print(f'  - References components/: {has_components}')
        print(f'  - Total length: {len(content):,} characters')
        print(f'  - Number of files: {len(project.get("files", []))}')

if __name__ == '__main__':
    asyncio.run(view_project())
