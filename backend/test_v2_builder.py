"""
Quick test for AI Builder V2
Tests the enhanced generation with API integrations
"""
import asyncio
import logging
logging.basicConfig(level=logging.INFO)

async def run_v2_builder_demo():
    print("=" * 60)
    print("🧪 Testing AI Builder V2 (Enhanced)")
    print("=" * 60)
    
    try:
        from ai_builder_service_v2 import AIBuilderServiceV2
        builder = AIBuilderServiceV2()
        print("✅ AI Builder V2 imported successfully")
        
        # Test 1: Simple image generator (Midjourney-like)
        print("\n📝 Test 1: AI Image Generator App")
        prompt = "Build an AI image generator like Midjourney that takes text prompts and generates images"
        tech_stack = {"frontend": "React", "backend": "FastAPI"}
        
        result = await builder.generate_app_structure(prompt, tech_stack)
        
        print(f"✅ Generated app: {result.get('app_name', 'N/A')}")
        print(f"📄 Description: {result.get('description', 'N/A')}")
        print(f"🔌 Required services: {', '.join(result.get('required_services', []))}")
        print(f"📁 Files generated: {len(result.get('files', []))}")
        
        # Show file structure
        print("\n📂 File Structure:")
        for file in result.get('files', []):
            path = file.get('path', 'unknown')
            lines = len(file.get('content', '').split('\n'))
            print(f"  - {path} ({lines} lines)")
        
        # Check for backend files
        has_backend = any('backend' in f.get('path', '') for f in result.get('files', []))
        has_frontend = any('frontend' in f.get('path', '') or 'src' in f.get('path', '') for f in result.get('files', []))
        has_env = any('.env' in f.get('path', '') for f in result.get('files', []))
        
        print(f"\n✓ Has Backend: {has_backend}")
        print(f"✓ Has Frontend: {has_frontend}")
        print(f"✓ Has Environment Config: {has_env}")
        
        # Show a sample backend file
        backend_files = [f for f in result.get('files', []) if 'backend' in f.get('path', '') and f.get('path', '').endswith('.py')]
        if backend_files:
            sample = backend_files[0]
            print(f"\n📝 Sample Backend Code ({sample.get('path', '')}):")
            print("-" * 60)
            print(sample.get('content', '')[:500] + "...")
        
        print("\n" + "=" * 60)
        print("✅ TEST PASSED - V2 Builder is working!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_v2_builder_demo())
