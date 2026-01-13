import asyncio
import requests
import json

async def run_generation_demo():
    # Login first
    login_response = requests.post(
        'http://127.0.0.1:8000/api/auth/login',
        json={
            'email': 'copilot_test@test.com',
            'password': 'TestPass123!'
        }
    )
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json()['access_token']
    print(f"✓ Logged in successfully")
    
    # Generate a project
    print(f"\n🚀 Generating project with UPGRADED prompts...")
    print(f"Prompt: 'Build an operations dashboard for an electric vehicle fleet'" )
    
    gen_response = requests.post(
        'http://127.0.0.1:8000/api/projects/generate',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'name': 'TEST - EV Fleet Dashboard',
            'description': 'Build an operations dashboard for an electric vehicle fleet with maintenance schedules, charging insights, and driver shift planning',
            'tech_stack': {
                'frontend': 'React',
                'backend': 'FastAPI',
                'database': 'MongoDB'
            }
        }
    )
    
    if gen_response.status_code != 200:
        print(f"\n❌ Generation failed: {gen_response.status_code}")
        print(gen_response.text)
        return
    
    result = gen_response.json()
    print(f"\n{'='*80}")
    print(f"✓ PROJECT GENERATED SUCCESSFULLY")
    print(f"{'='*80}")
    print(f"Project ID: {result.get('project_id')}")
    print(f"Name: {result.get('name')}")
    print(f"Number of files: {len(result.get('files', []))}")
    print(f"\nFile Structure:")
    
    total_chars = 0
    for file in result.get('files', []):
        path = file.get('path', 'unknown')
        content_len = len(file.get('content', ''))
        total_chars += content_len
        print(f"  📄 {path:50s} {content_len:>8,} chars")
    
    print(f"\n{'='*80}")
    print(f"TOTAL CODE SIZE: {total_chars:,} characters")
    print(f"{'='*80}")
    
    # Analyze the main App.js
    app_file = next((f for f in result.get('files', []) if 'App.js' in f.get('path', '')), None)
    if app_file:
        content = app_file.get('content', '')
        
        # Check for multi-page indicators
        has_router = 'BrowserRouter' in content or 'Router' in content or 'Route' in content or 'Routes' in content
        has_pages = 'pages/' in content or '/pages/' in content or 'Page' in content
        has_components = 'components/' in content or '/components/' in content
        has_navigation = 'nav' in content.lower() or 'navbar' in content.lower() or 'menu' in content.lower()
        
        # Count pages/sections
        section_count = content.count('<section') + content.count('section')
        div_count = content.count('<div')
        
        print(f"\n🔍 APP.JS ANALYSIS:")
        print(f"  - Has React Router/Routing: {'✓ YES' if has_router else '✗ NO'}")
        print(f"  - References Pages: {'✓ YES' if has_pages else '✗ NO'}")
        print(f"  - References Components: {'✓ YES' if has_components else '✗ NO'}")
        print(f"  - Has Navigation: {'✓ YES' if has_navigation else '✗ NO'}")
        print(f"  - Section elements: {section_count}")
        print(f"  - Div elements: {div_count}")
        print(f"  - Code length: {len(content):,} characters")
        
        print(f"\n📝 First 1500 characters of App.js:")
        print(f"{'='*80}")
        print(content[:1500])
        print(f"\n... (truncated)")
        
        # VERDICT
        print(f"\n{'='*80}")
        if has_router and (has_pages or section_count >= 5):
            print(f"🎉 VERDICT: MULTI-PAGE APPLICATION DETECTED!")
            print(f"   This matches the upgraded requirements!")
        else:
            print(f"⚠️  VERDICT: SINGLE-PAGE APPLICATION")
            print(f"   This does NOT match the upgraded requirements.")
            print(f"   Expected: React Router + multiple pages/routes")
        print(f"{'='*80}")

if __name__ == '__main__':
    asyncio.run(run_generation_demo())
