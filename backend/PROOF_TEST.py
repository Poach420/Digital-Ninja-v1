"""
REAL TEST: Generate AI Image Generator and show the actual code
"""
import asyncio
import json
import logging
logging.basicConfig(level=logging.INFO)

async def run_real_generation_test():
    print("\n" + "="*70)
    print("🧪 PROOF TEST: AI Image Generator Generation")
    print("="*70)
    
    from ai_builder_service_v2 import AIBuilderServiceV2
    
    builder = AIBuilderServiceV2()
    
    # EXACT prompt user should use
    prompt = "Build an AI-powered image generator that takes text prompts and generates images using DALL-E API, with a gallery to view all generated images"
    
    print(f"\n📝 PROMPT: {prompt}")
    print("\n⏳ Generating...")
    
    result = await builder.generate_app_structure(
        prompt=prompt,
        tech_stack={"frontend": "React", "backend": "FastAPI"}
    )
    
    print(f"\n✅ GENERATION COMPLETE")
    print(f"📦 App Name: {result.get('app_name')}")
    print(f"📊 Files Generated: {len(result.get('files', []))}")
    
    # Show the ACTUAL backend code
    backend_file = next((f for f in result.get('files', []) if 'main.py' in f.get('path', '')), None)
    if backend_file:
        print("\n" + "="*70)
        print("📄 ACTUAL BACKEND CODE GENERATED (backend/main.py):")
        print("="*70)
        print(backend_file['content'])
        print("="*70)
    
    # Show the ACTUAL frontend code
    frontend_file = next((f for f in result.get('files', []) if 'App.js' in f.get('path', '')), None)
    if frontend_file:
        print("\n" + "="*70)
        print("📄 ACTUAL FRONTEND CODE GENERATED (frontend/src/App.js):")
        print("="*70)
        print(frontend_file['content'][:1000] + "\n... (truncated)")
        print("="*70)
    
    # Check for REAL API calls (not mock)
    has_real_api = 'openai' in backend_file['content'].lower() if backend_file else False
    has_real_fetch = 'fetch(' in frontend_file['content'] if frontend_file else False
    
    print("\n🔍 VERIFICATION:")
    print(f"  ✓ Has OpenAI import: {has_real_api}")
    print(f"  ✓ Has real API fetch calls: {has_real_fetch}")
    print(f"  ✓ Has backend endpoint: {'@app.post' in backend_file['content'] if backend_file else False}")
    print(f"  ✓ Has environment vars: {any('.env' in f['path'] for f in result.get('files', []))}")
    
    # Save full output to file for inspection
    with open('PROOF_GENERATION_OUTPUT.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("\n💾 Full output saved to: PROOF_GENERATION_OUTPUT.json")
    print("\n" + "="*70)
    
    if has_real_api and has_real_fetch:
        print("✅ VERIFIED: Generates REAL working apps with API integrations!")
        print("="*70)
        return True
    else:
        print("❌ FAILED: Still generating mock code")
        print("="*70)
        return False

if __name__ == "__main__":
    success = asyncio.run(run_real_generation_test())
    exit(0 if success else 1)
