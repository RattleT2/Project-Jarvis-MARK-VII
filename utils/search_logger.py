"""
search_logger.py — JARVIS Search System Logging & Debugging

Comprehensive logging for search operations to track issues and performance.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("jarvis_search")


def _get_base_dir() -> Path:
    """Get base directory."""
    import sys
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


LOG_DIR = _get_base_dir() / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log file for search operations
SEARCH_LOG_FILE = LOG_DIR / "search_log.jsonl"


class SearchLogger:
    """
    Structured logging for search operations.
    Tracks every search query, response time, provider used, and errors.
    """

    @staticmethod
    def log_search(
        query: str,
        provider: str,
        response_length: int,
        duration_seconds: float,
        status: str = "success",
        error: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Log a search operation.

        Args:
            query: The search query
            provider: Which backend (openrouter, gemini, ddg, etc)
            response_length: Length of response text
            duration_seconds: How long the search took
            status: success | failed | timeout | rate_limited
            error: Error message if status != success
            metadata: Additional context (model used, retry count, etc)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query[:100],  # Truncate for log
            "provider": provider,
            "response_length": response_length,
            "duration_seconds": round(duration_seconds, 2),
            "status": status,
            "error": error,
            "metadata": metadata or {},
        }

        # Log to console
        log_msg = f"[{provider.upper()}] {status.upper()} - {query[:50]}"
        if error:
            log_msg += f" - Error: {error}"
        logger.info(log_msg)

        # Log to file (JSONL format for easy parsing)
        try:
            with open(SEARCH_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write search log: {e}")

    @staticmethod
    def log_fallback(
        original_provider: str,
        fallback_provider: str,
        reason: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Log when a service falls back to another provider."""
        logger.warning(
            f"[FALLBACK] {original_provider} → {fallback_provider}: {reason}"
        )

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "fallback",
            "original_provider": original_provider,
            "fallback_provider": fallback_provider,
            "reason": reason,
            "metadata": metadata or {},
        }

        try:
            with open(SEARCH_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write fallback log: {e}")

    @staticmethod
    def get_search_stats(hours: int = 1) -> dict[str, Any]:
        """
        Get search statistics from the past N hours.

        Returns:
            {
                "total_searches": int,
                "success_rate": float (0-1),
                "avg_duration": float (seconds),
                "providers": {"openrouter": count, "gemini": count, ...},
                "errors": [error messages]
            }
        """
        if not SEARCH_LOG_FILE.exists():
            return {
                "total_searches": 0,
                "success_rate": 1.0,
                "avg_duration": 0,
                "providers": {},
                "errors": [],
            }

        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=hours)
        stats = {
            "total_searches": 0,
            "successful": 0,
            "failed": 0,
            "avg_duration": 0,
            "providers": {},
            "error_summary": {},
        }

        durations = []

        try:
            with open(SEARCH_LOG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("type") == "fallback":
                            continue

                        ts = datetime.fromisoformat(entry.get("timestamp", ""))
                        if ts < cutoff_time:
                            continue

                        stats["total_searches"] += 1
                        provider = entry.get("provider", "unknown")
                        stats["providers"][provider] = stats["providers"].get(provider, 0) + 1

                        if entry.get("status") == "success":
                            stats["successful"] += 1
                            durations.append(entry.get("duration_seconds", 0))
                        else:
                            stats["failed"] += 1
                            error = entry.get("error", "unknown")
                            stats["error_summary"][error] = stats["error_summary"].get(error, 0) + 1

                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.warning(f"Failed to read search stats: {e}")

        if stats["total_searches"] > 0:
            stats["success_rate"] = round(stats["successful"] / stats["total_searches"], 2)
            if durations:
                stats["avg_duration"] = round(sum(durations) / len(durations), 2)

        return stats


# Global logger instance
search_logger = SearchLogger()
