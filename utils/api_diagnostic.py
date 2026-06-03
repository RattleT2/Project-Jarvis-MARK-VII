#!/usr/bin/env python3
"""
api_diagnostic.py — JARVIS API Key & Configuration Checker

Helps diagnose API key, library, and configuration issues.
Run: python utils/api_diagnostic.py
"""

import os
import sys
import json
from pathlib import Path

def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

def check_google_api_key():
    """Check Google/Gemini API key configuration."""
    print("\n" + "="*60)
    print("🔍 CHECKING GOOGLE API KEY")
    print("="*60)
    
    # Check env variable
    env_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if env_key:
        masked = env_key[:10] + "***" + env_key[-5:] if len(env_key) > 15 else "***"
        print(f"✅ GOOGLE_API_KEY found in environment: {masked}")
        return True
    else:
        print(f"⚠️  GOOGLE_API_KEY not in environment vars")
    
    # Check config file
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        if "gemini_api_key" in config:
            key = config["gemini_api_key"]
            if isinstance(key, str) and key.strip():
                masked = key[:10] + "***" + key[-5:] if len(key) > 15 else "***"
                print(f"✅ gemini_api_key found in config: {masked}")
                return True
        
        if "gemini_api_keys" in config:
            keys = config["gemini_api_keys"]
            if isinstance(keys, list) and keys:
                print(f"✅ gemini_api_keys found in config: {len(keys)} key(s)")
                return True
    except FileNotFoundError:
        print(f"❌ Config file not found: {CONFIG_PATH}")
    except Exception as e:
        print(f"❌ Error reading config: {e}")
    
    print("❌ NO GOOGLE API KEY FOUND")
    return False

def check_openrouter_api_key():
    """Check OpenRouter API key configuration."""
    print("\n" + "="*60)
    print("🔍 CHECKING OPENROUTER API KEY")
    print("="*60)
    
    # Check env variable
    env_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if env_key:
        masked = env_key[:10] + "***" + env_key[-5:] if len(env_key) > 15 else "***"
        print(f"✅ OPENROUTER_API_KEY found in environment: {masked}")
        
        # Validate API key format
        if env_key.startswith("sk-"):
            print(f"✅ API key format looks valid (starts with 'sk-')")
            return True
        else:
            print(f"⚠️  API key doesn't start with 'sk-' (might be invalid)")
            return False
    else:
        print(f"⚠️  OPENROUTER_API_KEY not in environment vars")
    
    # Check config file
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        if "openrouter_api_key" in config:
            key = config["openrouter_api_key"]
            if isinstance(key, str) and key.strip():
                masked = key[:10] + "***" + key[-5:] if len(key) > 15 else "***"
                print(f"✅ openrouter_api_key found in config: {masked}")
                
                if key.startswith("sk-"):
                    print(f"✅ API key format looks valid (starts with 'sk-')")
                    return True
                else:
                    print(f"⚠️  API key doesn't start with 'sk-' (might be invalid)")
                    return False
    except FileNotFoundError:
        print(f"❌ Config file not found: {CONFIG_PATH}")
    except Exception as e:
        print(f"❌ Error reading config: {e}")
    
    print("❌ NO OPENROUTER API KEY FOUND")
    return False

def check_search_libraries():
    """Check which search libraries are installed."""
    print("\n" + "="*60)
    print("🔍 CHECKING SEARCH LIBRARIES")
    print("="*60)
    
    # Check ddgs (new library)
    try:
        import ddgs
        print(f"✅ ddgs library installed (version {ddgs.__version__})")
        return "ddgs"
    except ImportError:
        print(f"⚠️  ddgs library not installed")
    
    # Check duckduckgo_search (old library)
    try:
        import duckduckgo_search
        print(f"✅ duckduckgo_search library installed (OLD, deprecated)")
        print(f"⚠️  Recommendation: pip install ddgs")
        return "duckduckgo_search"
    except ImportError:
        print(f"❌ duckduckgo_search library not installed")
    
    print("❌ NO SEARCH LIBRARY FOUND - Install with: pip install ddgs")
    return None

def test_openrouter_connection():
    """Test OpenRouter API connection."""
    print("\n" + "="*60)
    print("🔍 TESTING OPENROUTER CONNECTION")
    print("="*60)
    
    try:
        from or_client import client
        
        # Try simple request
        print("⏳ Sending test request to OpenRouter...")
        result = client.chat(
            "Say 'Hello World' in one word",
            system="You are a helpful assistant.",
            max_tokens=10
        )
        
        if result:
            print(f"✅ OpenRouter connection OK")
            print(f"   Response: {result[:50]}...")
            return True
        else:
            print(f"⚠️  OpenRouter returned empty response")
            return False
            
    except Exception as e:
        error_str = str(e)
        if "401" in error_str or "Unauthorized" in error_str:
            print(f"❌ AUTHENTICATION FAILED (HTTP 401)")
            print(f"   Your API key is invalid or expired")
            print(f"   Error: {error_str[:100]}")
        else:
            print(f"❌ Connection failed: {error_str[:100]}")
        return False

def test_duckduckgo_search():
    """Test DuckDuckGo search."""
    print("\n" + "="*60)
    print("🔍 TESTING DUCKDUCKGO SEARCH")
    print("="*60)
    
    try:
        from actions.web_search import _ddg_search
        
        print("⏳ Sending test search to DuckDuckGo...")
        results = _ddg_search("python programming", max_results=3)
        
        if results:
            print(f"✅ DuckDuckGo search OK")
            print(f"   Found {len(results)} result(s)")
            for i, r in enumerate(results[:2], 1):
                print(f"   {i}. {r['title']}")
            return True
        else:
            print(f"⚠️  DuckDuckGo returned 0 results")
            return False
            
    except Exception as e:
        print(f"❌ DuckDuckGo search failed: {e}")
        return False

def show_recommendations():
    """Show recommendations based on diagnostics."""
    print("\n" + "="*60)
    print("💡 RECOMMENDATIONS")
    print("="*60)
    
    print("""
1. **For HTTP 401 Error (OpenRouter):**
   - Check if your API key is valid
   - Go to https://openrouter.ai/keys to verify key
   - Make sure key starts with 'sk-'
   - Regenerate key if needed
   
2. **For Zero DDG Results:**
   - Query might be too specific or invalid
   - Try with simpler search terms
   - Check internet connection
   
3. **For Library Warnings:**
   - Upgrade with: pip install ddgs --upgrade
   - Or uninstall old: pip uninstall duckduckgo_search
   
4. **For All API Key Issues:**
   - Set environment variable:
     $env:OPENROUTER_API_KEY="sk-your-key-here"
   - Or update config/api_keys.json with valid keys
""")

def main():
    print("\n" + "█"*60)
    print("JARVIS API DIAGNOSTIC TOOL")
    print("█"*60)
    
    results = {
        "google": check_google_api_key(),
        "openrouter": check_openrouter_api_key(),
        "library": check_search_libraries(),
    }
    
    # Test connections
    if results["openrouter"]:
        results["openrouter_conn"] = test_openrouter_connection()
    else:
        results["openrouter_conn"] = False
    
    results["ddg_search"] = test_duckduckgo_search()
    
    # Summary
    print("\n" + "="*60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*60)
    
    status_map = {True: "✅ OK", False: "❌ FAIL", None: "⚠️  WARNING"}
    
    print(f"Google API Key:        {status_map.get(results['google'], '?')}")
    print(f"OpenRouter API Key:    {status_map.get(results['openrouter'], '?')}")
    print(f"Search Library:        {status_map.get(results['library'] is not None, '?')}")
    print(f"OpenRouter Connection: {status_map.get(results.get('openrouter_conn'), '?')}")
    print(f"DuckDuckGo Search:     {status_map.get(results.get('ddg_search'), '?')}")
    
    show_recommendations()
    
    if results["openrouter_conn"]:
        print("\n✅ System is mostly working! Search should work.")
    elif results["ddg_search"]:
        print("\n⚠️  OpenRouter not working, but DDG fallback is available.")
    else:
        print("\n❌ System has issues. Check recommendations above.")

if __name__ == "__main__":
    main()
