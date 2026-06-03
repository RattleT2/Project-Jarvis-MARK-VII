"""
analyst.py — JARVIS Analytical & Research Tool

Opens websites, analyzes information, and provides deep insights.
Perfect for: economic analysis, research questions, current events, etc.

Usage:
  analyst({
    "topic": "rupiah di Indonesia",
    "research_depth": "comprehensive",  # quick | moderate | comprehensive
    "language": "id"  # language preference
  })
"""

import time
from typing import Optional
from pathlib import Path
import json
import os
import sys


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR        = _get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"


def _get_openrouter_client():
    """Get or initialize OpenRouter client for analysis."""
    try:
        from or_client import client
        return client
    except ImportError:
        return None


def _search_and_fetch(topic: str, max_results: int = 5) -> str:
    """Search web for topic information and compile results."""
    print(f"[Analyst] 🔍 Researching: {topic}")
    
    try:
        from actions.web_search import _ddg_search, _format_ddg
        results = _ddg_search(topic, max_results=max_results)
        formatted = _format_ddg(topic, results)
        print(f"[Analyst] ✅ Found {len(results)} relevant sources")
        return formatted
    except ImportError:
        try:
            from actions.web_search import _ddg_search, _format_ddg
        except ImportError:
            print("[Analyst] ⚠️ DuckDuckGo search unavailable, using research prompt")
            return ""
    except Exception as e:
        print(f"[Analyst] ⚠️ Search failed: {e}")
        return ""


def _analyze_with_gemini(topic: str, research_data: str, depth: str = "comprehensive") -> str:
    """Use Gemini for deep analysis & thinking."""
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get("GOOGLE_API_KEY", "")
        if not api_key:
            try:
                with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    keys = data.get("gemini_api_keys", [data.get("gemini_api_key", "")])
                    api_key = keys[0] if isinstance(keys, list) else keys
            except:
                pass
        
        if not api_key:
            return None
        
        genai.configure(api_key=api_key)
        
        depth_instruction = {
            "quick": "Provide a brief 2-3 paragraph analysis.",
            "moderate": "Provide a detailed 4-5 paragraph analysis with key insights.",
            "comprehensive": (
                "Provide a comprehensive analysis including: "
                "1) Current situation overview, "
                "2) Key factors & drivers, "
                "3) Recent trends & data, "
                "4) Impact & implications, "
                "5) Future outlook. "
                "Be thorough and data-driven."
            )
        }.get(depth, "Provide detailed analysis.")
        
        prompt = f"""
You are an expert analyst and researcher. Analyze this topic thoroughly:

TOPIC: {topic}

RESEARCH DATA:
{research_data if research_data else "(Use your knowledge to provide analysis)"}

INSTRUCTIONS:
{depth_instruction}

Provide a structured, insightful analysis. Use data and evidence. 
Be professional but accessible. If the topic is about Indonesia, 
provide local context and regional implications.
"""
        
        print("[Analyst] 🧠 Analyzing with Gemini...")
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction="You are an expert analyst providing deep insights and research."
        )
        
        response = model.generate_content(prompt, request_options={"timeout": 60})
        analysis = response.text.strip()
        print("[Analyst] ✅ Analysis complete")
        return analysis
        
    except Exception as e:
        print(f"[Analyst] ⚠️ Gemini analysis failed: {e}")
        return None


def _analyze_with_openrouter(topic: str, research_data: str, depth: str = "comprehensive") -> str:
    """Use OpenRouter for analysis as fallback."""
    try:
        client = _get_openrouter_client()
        if not client:
            return None
        
        depth_instruction = {
            "quick": "Provide a brief 2-3 paragraph analysis.",
            "moderate": "Provide a detailed 4-5 paragraph analysis with key insights.",
            "comprehensive": (
                "Provide comprehensive analysis with: "
                "1) Overview, 2) Key factors, 3) Trends, 4) Implications, 5) Outlook."
            )
        }.get(depth, "Provide detailed analysis.")
        
        prompt = f"""Analyze this topic thoroughly:

TOPIC: {topic}

DATA:
{research_data if research_data else "(Use your knowledge)"}

{depth_instruction}

Be professional, data-driven, and insightful."""
        
        print("[Analyst] 🧠 Analyzing with OpenRouter...")
        result = client.chat(
            prompt,
            system="You are an expert analyst providing deep insights and research."
        )
        print("[Analyst] ✅ OpenRouter analysis done")
        return result
        
    except Exception as e:
        print(f"[Analyst] ⚠️ OpenRouter analysis failed: {e}")
        return None


def _browse_and_analyze(topic: str, player=None, speak=None) -> str:
    """Use browser to directly search and analyze from website."""
    try:
        from actions.browser_control import browser_control
        
        print(f"[Analyst] 🌐 Opening browser for {topic}")
        
        # Search for topic
        search_result = browser_control(
            parameters={
                "action": "search",
                "query": topic,
                "engine": "google"
            },
            player=player
        )
        
        time.sleep(2)
        
        # Get page content
        page_content = browser_control(
            parameters={"action": "get_text"},
            player=player
        )
        
        print("[Analyst] ✅ Browser research retrieved")
        return page_content
        
    except Exception as e:
        print(f"[Analyst] ⚠️ Browser analysis failed: {e}")
        return ""


def analyst(
    parameters: dict,
    player=None,
    speak=None,
) -> str:
    """
    Main analyst function — Research, analyze, and explain topics.
    
    Parameters:
        topic : string (required) — What to analyze (e.g., "rupiah di Indonesia")
        research_depth: string (optional) — quick | moderate | comprehensive (default: comprehensive)
        use_browser: boolean (optional) — Use browser search (default: false)
        language: string (optional) — Response language (default: auto-detect from topic)
    """
    params = parameters or {}
    topic = params.get("topic", "").strip()
    depth = params.get("research_depth", "comprehensive").lower()
    use_browser = params.get("use_browser", False)
    language = params.get("language", "")
    
    if not topic:
        return "Please provide a topic to analyze, sir."
    
    if player:
        player.write_log(f"[Analyst] Analyzing: {topic}")
    
    if speak:
        speak(f"Let me research and analyze {topic} for you, sir.")
    
    print(f"\n[Analyst] 📊 Starting analysis: {topic}")
    print(f"[Analyst] 📋 Depth: {depth}")
    
    # Step 1: Research
    research_data = ""
    if use_browser:
        research_data = _browse_and_analyze(topic, player=player, speak=speak)
    else:
        research_data = _search_and_fetch(topic, max_results=6)
    
    if not research_data:
        print("[Analyst] ⚠️ No research data found, using knowledge base")
    
    # Step 2: Analyze with AI
    analysis = _analyze_with_gemini(topic, research_data, depth=depth)
    
    # Fallback to OpenRouter if Gemini fails
    if not analysis:
        print("[Analyst] Falling back to OpenRouter...")
        analysis = _analyze_with_openrouter(topic, research_data, depth=depth)
    
    if not analysis:
        return (
            f"I couldn't complete the analysis for '{topic}' at this time, sir. "
            "Please try again or check your API configuration."
        )
    
    # Add language instruction if requested
    if language and language.lower() != "english":
        print(f"[Analyst] 🌐 Translating to {language}")
        try:
            import google.generativeai as genai
            api_key = os.environ.get("GOOGLE_API_KEY", "")
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash-lite")
                translate_prompt = (
                    f"Translate the following analysis to {language}. "
                    f"Keep all facts and data intact:\n\n{analysis}"
                )
                translated = model.generate_content(translate_prompt)
                analysis = translated.text.strip()
        except:
            pass  # Keep original if translation fails
    
    # Log result
    log_msg = f"[Analyst] ✅ Analysis complete ({len(analysis)} chars)"
    print(log_msg)
    if player:
        player.write_log(log_msg)
    
    return analysis


if __name__ == "__main__":
    print("Testing analyst tool...\n")
    
    result = analyst({
        "topic": "rupiah terhadap dolar",
        "research_depth": "moderate"
    })
    
    print("\n" + "="*60)
    print(result)
    print("="*60)
