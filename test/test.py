# 🔧 DIAGNOSTIC: Check Gemini API Connection
print("=" * 70)
print("🔧 GEMINI API DIAGNOSTIC")
print("=" * 70)

import os
import google.generativeai as genai

# 1. Check API Key
print("\n1️⃣ Checking API Key...")
api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyDb3B5gPGV8pGgHFBmwEC4XwfzmBgnJCW0")
if api_key:
    print(f"   ✅ API Key found: {api_key[:20]}...{api_key[-4:]}")
else:
    print(f"   ❌ No API key found!")

# 2. Configure
print("\n2️⃣ Configuring Gemini...")
try:
    genai.configure(api_key=api_key)
    print("   ✅ Configuration successful")
except Exception as e:
    print(f"   ❌ Configuration failed: {e}")

# 3. List available models
print("\n3️⃣ Listing available models...")
try:
    models = genai.list_models()
    print(f"   ✅ Found {len(list(models))} total models")
    
    # Re-list to iterate (generator consumed above)
    models = genai.list_models()
    embedding_models = [m for m in models if 'embed' in m.name.lower()]
    
    if embedding_models:
        print(f"\n   📋 Embedding models available:")
        for model in embedding_models:
            print(f"      • {model.name}")
            if hasattr(model, 'supported_generation_methods'):
                print(f"        Methods: {model.supported_generation_methods}")
    else:
        print("   ⚠️  No embedding models found")
        
except Exception as e:
    print(f"   ❌ Failed to list models: {type(e).__name__}: {e}")

# 4. Test simple embedding (no timeout)
print("\n4️⃣ Testing basic embedding call...")
try:
    result = genai.embed_content(
        model="models/text-embedding-004",
        content="test"
    )
    print(f"   ✅ SUCCESS! Got embedding with {len(result['embedding'])} dimensions")
    
except Exception as e:
    error_type = type(e).__name__
    error_msg = str(e)
    print(f"   ❌ FAILED: {error_type}")
    print(f"   📄 Error details: {error_msg[:300]}")
    
    # Provide specific guidance
    if "404" in error_msg or "not found" in error_msg.lower():
        print("\n   💡 Model not found - Try these:")
        print("      • models/embedding-001")
        print("      • models/text-embedding-004") 
        print("      • Check model list above")
    elif "401" in error_msg or "authentication" in error_msg.lower():
        print("\n   💡 Authentication failed:")
        print("      • API key might be invalid/expired")
        print("      • Get new key: https://makersuite.google.com/app/apikey")
    elif "429" in error_msg or "quota" in error_msg.lower():
        print("\n   💡 Quota exceeded:")
        print("      • Free tier limit reached")
        print("      • Wait or upgrade plan")
    elif "400" in error_msg:
        print("\n   💡 Bad request - parameter issue")
        print("      • Try removing task_type parameter")
        print("      • Check model name format")

print("\n" + "=" * 70)