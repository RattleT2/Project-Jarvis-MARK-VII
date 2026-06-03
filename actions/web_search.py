#web_search.py
import random
import sys
import time
from pathlib import Path


def _get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR        = _get_base_dir()


from utils.api_utils import get_google_api_key


def _log_search(query: str, provider: str, length: int, duration: float, status: str = "success", error: str = ""):
    try:
        from utils.search_logger import search_logger
        search_logger.log_search(
            query=query, provider=provider,
            response_length=length, duration_seconds=duration,
            status=status, error=error if error else None
        )
    except Exception:
        pass


def _log_fallback(from_provider: str, to_provider: str, reason: str):
    try:
        from utils.search_logger import search_logger
        search_logger.log_fallback(from_provider, to_provider, reason)
    except Exception:
        pass


def _gemini_search(query: str) -> str:
    from google import genai

    client   = genai.Client(api_key=get_google_api_key())
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=query,
        config={"tools": [{"google_search": {}}]},
    )

    # ✅ FIX: Handle null candidates array
    if not response or not response.candidates:
        raise ValueError("Gemini returned no candidates.")
    
    candidate = response.candidates[0]
    if not candidate or not candidate.content or not candidate.content.parts:
        raise ValueError("Gemini candidate has no content.")

    text = ""
    for part in candidate.content.parts:
        if hasattr(part, "text") and part.text:
            text += part.text

    text = text.strip()
    if not text:
        raise ValueError("Gemini returned an empty response.")
    return text


def _ddg_search(query: str, max_results: int = 6, attempt: int = 1, max_attempts: int = 2) -> list[dict]:
    """Search using DuckDuckGo with automatic retry logic."""
    import time
    import warnings
    
    # ✅ FIX: Handle both old (duckduckgo_search) and new (ddgs) libraries
    ddgs_module = None
    use_old_api = False
    
    try:
        from ddgs import DDGS
        ddgs_module = DDGS
        use_old_api = False
        print("[DDG] Using new ddgs library")
    except ImportError:
        try:
            # Fallback: use old duckduckgo_search library
            from duckduckgo_search import DDGS
            ddgs_module = DDGS
            use_old_api = True
            print("[DDG] Using legacy duckduckgo_search library")
            # Suppress the deprecation warning
            warnings.filterwarnings("ignore", message=".*has been renamed.*")
        except ImportError:
            raise RuntimeError(
                "No search library found! Install with: pip install ddgs"
                " (or legacy: pip install duckduckgo_search)"
            )

    try:
        if not query or not query.strip():
            return []
        
        results = []
        
        if use_old_api:
            # Old API: DDGS class without context manager
            ddgs = ddgs_module()
            for r in ddgs.text(query, max_results=max_results):
                if isinstance(r, dict):
                    results.append({
                        "title":   r.get("title",  ""),
                        "snippet": r.get("body",   ""),
                        "url":     r.get("href",   ""),
                    })
        else:
            # New API: DDGS with context manager and timeout
            with ddgs_module(timeout=10) as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    if isinstance(r, dict):
                        results.append({
                            "title":   r.get("title",  ""),
                            "snippet": r.get("body",   ""),
                            "url":     r.get("href",   ""),
                        })
        
        if not results:
            print(f"[DDG] ⚠️ No results for: {query}")
        
        return results
    except Exception as e:
        # ✅ FIX: Add retry logic with random backoff
        if attempt < max_attempts:
            wait_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff
            print(f"[DDG] Retry {attempt}/{max_attempts} after {wait_time:.1f}s: {e}")
            time.sleep(wait_time)
            return _ddg_search(query, max_results, attempt + 1, max_attempts)
        raise


def _format_ddg(query: str, results: list[dict]) -> str:
    if not results:
        return f"No results found for: {query}"

    lines = [f"Search results for: {query}\n"]
    for i, r in enumerate(results, 1):
        if r.get("title"):   lines.append(f"{i}. {r['title']}")
        if r.get("snippet"): lines.append(f"   {r['snippet']}")
        if r.get("url"):     lines.append(f"   {r['url']}")
        lines.append("")
    return "\n".join(lines).strip()

def _compare(items: list[str], aspect: str) -> str:
    """Compare items using OpenRouter (faster and more consistent)."""
    try:
        from or_client import client
        query = (
            f"Compare {', '.join(items)} in terms of {aspect}. "
            "Give specific facts and data in bullet points."
        )
        result = client.chat(
            query,
            system="You are a comparison expert. Provide concise, factual comparisons."
        )
        if result and result.strip():
            print(f"[WebSearch] ✅ Compare via OpenRouter OK.")
            return result.strip()
    except Exception as e:
        print(f"[WebSearch] ⚠️ OpenRouter compare failed: {e} — trying Gemini...")
        try:
            return _gemini_search(
                f"Compare {', '.join(items)} in terms of {aspect}. Give specific facts."
            )
        except Exception as e2:
            print(f"[WebSearch] ⚠️ Gemini compare failed: {e2} — falling back to DDG")

    # DDG fallback: fetch results per item and merge
    all_results: dict[str, list] = {}
    for item in items:
        try:
            all_results[item] = _ddg_search(f"{item} {aspect}", max_results=3)
        except Exception as err:
            print(f"[WebSearch] ⚠️ DDG {item} failed: {err}")
            all_results[item] = []

    lines = [f"Comparison — {aspect.upper()}", "─" * 40]
    for item in items:
        lines.append(f"\n▸ {item}")
        for r in all_results.get(item, [])[:2]:
            if r.get("snippet"):
                lines.append(f"  • {r['snippet']}")
    return "\n".join(lines)

# --- OpenRouter 401 cooldown cache ---
_openrouter_disabled_until = 0
_OR_COOLDOWN = 600  # 10 menit


def _try_openrouter_search(query: str) -> str | None:
    global _openrouter_disabled_until

    if time.time() < _openrouter_disabled_until:
        print(f"[WebSearch] ⏭️ Skipping OpenRouter (cooldown {int(_openrouter_disabled_until - time.time())}s left)")
        return None

    try:
        from or_client import client
        result = client.chat(
            query,
            system="You are a web search assistant. Answer factually and concisely."
        )
        if result and result.strip():
            print("[WebSearch] ✅ OpenRouter OK.")
            return result.strip()
    except Exception as e:
        err_str = str(e)
        if "401" in err_str or "UNAUTHORIZED" in err_str.upper():
            _openrouter_disabled_until = time.time() + _OR_COOLDOWN
            print(f"[WebSearch] ⚠️ OpenRouter 401 — disabled for {_OR_COOLDOWN}s")
        else:
            print(f"[WebSearch] ⚠️ OpenRouter failed: {e}")
    return None


def _try_gemini_search(query: str) -> str | None:
    try:
        result = _gemini_search(
            f"Search the web and answer concisely with factual information:\n{query}"
        )
        if result and result.strip():
            print("[WebSearch] ✅ Gemini OK.")
            return result.strip()
    except Exception as e:
        print(f"[WebSearch] ⚠️ Gemini failed: {e}")
    return None


def _try_ddg_search(query: str) -> str | None:
    try:
        results = _ddg_search(query)
        if not results:
            alt_queries = []
            words = query.split()
            if len(words) > 2:
                alt_queries.append(" ".join(words[:4]))
                alt_queries.append(" ".join(words[:3]))
            alt_queries.append(f"{query} news")
            alt_queries.append(f"{query} latest")
            for alt in alt_queries:
                alt = alt.strip()
                if alt == query:
                    continue
                print(f"[DDG] 🔄 Retrying with: {alt!r}")
                time.sleep(0.5)
                results = _ddg_search(alt)
                if results:
                    break
        result = _format_ddg(query, results)
        if results:
            print(f"[WebSearch] ✅ DDG: {len(results)} result(s).")
            return result
        print(f"[WebSearch] ⚠️ DDG: 0 results.")
    except Exception as e:
        print(f"[WebSearch] ⚠️ DDG failed: {e}")
    return None


def web_search(
    parameters:     dict,
    response=None,
    player=None,
    session_memory=None,
) -> str:
    import time
    from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError

    start_time = time.time()

    params = parameters or {}
    query  = params.get("query", "").strip()
    mode   = params.get("mode",  "search").lower().strip()
    items  = params.get("items", [])
    aspect = params.get("aspect", "general").strip() or "general"

    if not query and not items:
        return "Please provide a search query or items to compare, sir."

    if query and len(query) > 500:
        query = query[:500]

    if items and mode != "compare":
        mode = "compare"

    if player:
        player.write_log(f"[Search] {query or ', '.join(items)}")

    print(f"[WebSearch] 🔍 Query: {query!r}  Mode: {mode}")

    if mode == "compare":
        result = _compare(items, aspect)
        print(f"[WebSearch] ℹ️ Comparison completed in {time.time() - start_time:.2f}s")
        return result

    # ── Step 1: Try OpenRouter (skip if 401 cooldown) ──
    result = _try_openrouter_search(query)
    if result:
        _log_search(query, "openrouter", len(result), time.time() - start_time)
        return result

    _log_fallback("openrouter", "gemini+ddg", "")
    print("[WebSearch] 🔄 Falling back to parallel Gemini + DDG...")

    # ── Step 2: Gemini + DDG in parallel ──
    with ThreadPoolExecutor(max_workers=2) as executor:
        gemini_future = executor.submit(_try_gemini_search, query)
        ddg_future    = executor.submit(_try_ddg_search, query)

        gemini_result = None
        ddg_result    = None

        futures = [gemini_future, ddg_future]
        for future in as_completed(futures, timeout=10):
            try:
                res = future.result(timeout=0)
            except FuturesTimeoutError:
                continue
            except Exception:
                continue

            if not res:
                continue

            if future == gemini_future:
                gemini_result = res
            else:
                ddg_result = res

            if gemini_result:
                break

    # ── Step 3: Return best result ──
    if gemini_result:
        _log_search(query, "gemini", len(gemini_result), time.time() - start_time)
        return gemini_result

    if ddg_result:
        _log_search(query, "duckduckgo", len(ddg_result), time.time() - start_time)
        return ddg_result

    # ── Step 4: All failed ──
    duration = time.time() - start_time
    print(f"[WebSearch] ❌ All backends failed")
    _log_search(query, "all", 0, duration, "failed", "All backends failed")
    return f"Search failed, sir. Could not retrieve results for: {query}"
