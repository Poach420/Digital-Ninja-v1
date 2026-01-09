import asyncio
import sys
import os
from ai_builder_service import AIBuilderService

async def test_generation():
    print("=" * 70)
    print("DIRECT TEST OF AI BUILDER SERVICE")
    print("=" * 70)
    
    ai_service = AIBuilderService()
    
    prompt = "Build a professional website that promotes natural medicine with product catalog, articles, testimonials, and contact information"
    tech_stack = {"framework": "react", "styling": "css"}
    
    print(f"\nPrompt: {prompt}")
    print(f"Tech Stack: {tech_stack}")
    print("\n🚀 Generating application...")
    print("(This may take 30-60 seconds with the new complex prompts)\n")
    
    try:
        result = await ai_service.generate_app_structure(prompt, tech_stack)
        
        print("\n" + "=" * 70)
        print("✅ GENERATION COMPLETE!")
        print("=" * 70)
        
        files = result.get('files', [])
        print(f"\nNumber of files generated: {len(files)}")
        print("\nFile structure:")
        for file in files:
            path = file.get('path', 'unknown')
            content = file.get('content', '')
            print(f"  📄 {path} - {len(content):,} characters")
        
        # Analysis
        print("\n" + "=" * 70)
        print("📊 MULTI-PAGE ANALYSIS")
        print("=" * 70)
        
        all_content = ' '.join([f.get('content', '') for f in files])
        file_paths = [f.get('path', '') for f in files]
        
        has_router = 'BrowserRouter' in all_content or 'react-router' in all_content or 'react-router-dom' in all_content
        has_routes = all_content.count('<Route ') + all_content.count('<Route>')
        has_components_folder = any('components/' in p for p in file_paths)
        has_pages_folder = any('pages/' in p or 'Page.js' in p or 'Page.jsx' in p for p in file_paths)
        
        print(f"\n✓ React Router installed: {'✅ YES' if has_router else '❌ NO'}")
        print(f"✓ Number of routes defined: {has_routes}")
        print(f"✓ Components folder: {'✅ YES' if has_components_folder else '❌ NO'}")
        print(f"✓ Multiple page files: {'✅ YES' if has_pages_folder else '❌ NO'}")
        
        # Show package.json to verify dependencies
        package_json = next((f for f in files if f.get('path') == 'package.json'), None)
        if package_json:
            print("\n" + "-" * 70)
            print("📦 package.json dependencies:")
            print("-" * 70)
            content = package_json.get('content', '')
            # Extract dependencies section
            if '"dependencies"' in content:
                dep_start = content.find('"dependencies"')
                dep_end = content.find('}', dep_start) + 1
                print(content[dep_start:dep_end])
        
        # Show main App.js structure
        app_file = next((f for f in files if 'App.js' in f.get('path', '') or 'App.jsx' in f.get('path', '')), None)
        if app_file:
            print("\n" + "-" * 70)
            print(f"📝 {app_file.get('path')} preview (first 1000 chars):")
            print("-" * 70)
            content = app_file.get('content', '')
            print(content[:1000])
            if len(content) > 1000:
                print(f"\n... ({len(content) - 1000} more characters)")
        
        print("\n" + "=" * 70)
        print("VERDICT:")
        print("=" * 70)
        
        if has_router and has_routes >= 3 and len(files) >= 8:
            print("✅ SUCCESS! This is a MULTI-PAGE application with:")
            print(f"   - {has_routes} routes")
            print(f"   - {len(files)} files")
            print("   - Professional structure")
            print("\n🎉 THE UPGRADE WORKS! This matches top-tier AI builders!")
        else:
            print("❌ FAILED - This is still a basic demo:")
            print(f"   - Router: {'YES' if has_router else 'NO'}")
            print(f"   - Routes: {has_routes}")
            print(f"   - Files: {len(files)}")
            print("\n😞 The upgrade did NOT work as expected")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_generation())
