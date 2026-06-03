"""
api_utils.py — JARVIS Centralized API Key Management

Unified handler for all API keys (Google, OpenRouter, etc).
Reduces code duplication and improves maintainability.
"""

import json
import os
import random
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("api_utils")


def _get_base_dir() -> Path:
    """Get base directory (handle frozen executables)."""
    import sys
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = _get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"

# ✅ Cache API keys to reduce file I/O
_api_key_cache: dict[str, str] = {}


def _load_config() -> dict:
    """Load and cache API config from file."""
    try:
        if not API_CONFIG_PATH.exists():
            logger.warning(f"Config not found: {API_CONFIG_PATH}")
            return {}
        
        with open(API_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def get_google_api_key() -> str:
    """
    Get Google/Gemini API key from env or config.
    Priority: GOOGLE_API_KEY env var > config/api_keys.json
    """
    if "google" in _api_key_cache:
        return _api_key_cache["google"]

    # Try environment variable first
    env_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    if env_key:
        keys = [k.strip() for k in env_key.replace(";", ",").replace("\n", ",").split(",") if k.strip()]
        if keys:
            selected = random.choice(keys)
            _api_key_cache["google"] = selected
            logger.info("[API] ✅ Using Google API key from environment")
            return selected

    # Try config file
    try:
        config = _load_config()
        keys = []
        
        if isinstance(config.get("gemini_api_keys"), list):
            keys = [k.strip() for k in config["gemini_api_keys"] if isinstance(k, str) and k.strip()]
        
        if keys:
            selected = random.choice(keys)
            _api_key_cache["google"] = selected
            logger.info("[API] ✅ Using Google API key from config (list)")
            return selected
        
        single_key = config.get("gemini_api_key", "").strip()
        if single_key:
            _api_key_cache["google"] = single_key
            logger.info("[API] ✅ Using Google API key from config (single)")
            return single_key
    except Exception as e:
        logger.warning(f"Failed to load Google key from config: {e}")

    raise RuntimeError(
        "Google API key not found! Set GOOGLE_API_KEY environment variable "
        "or add gemini_api_key/gemini_api_keys to config/api_keys.json"
    )


def get_openrouter_api_key() -> str:
    """
    Get OpenRouter API key from env or config.
    Priority: OPENROUTER_API_KEY env var > config/api_keys.json
    """
    if "openrouter" in _api_key_cache:
        return _api_key_cache["openrouter"]

    # Try environment variable first
    env_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if env_key:
        _api_key_cache["openrouter"] = env_key
        logger.info("[API] ✅ Using OpenRouter API key from environment")
        return env_key

    # Try config file
    try:
        config = _load_config()
        key = config.get("openrouter_api_key", "").strip()
        if key:
            _api_key_cache["openrouter"] = key
            logger.info("[API] ✅ Using OpenRouter API key from config")
            return key
    except Exception as e:
        logger.warning(f"Failed to load OpenRouter key from config: {e}")

    raise RuntimeError(
        "OpenRouter API key not found! Set OPENROUTER_API_KEY environment variable "
        "or add openrouter_api_key to config/api_keys.json"
    )


def clear_cache() -> None:
    """Clear API key cache (useful for testing)."""
    _api_key_cache.clear()
    logger.info("[API] 🔄 Cache cleared")


def get_config_path() -> Path:
    """Get path to API config file."""
    return API_CONFIG_PATH
