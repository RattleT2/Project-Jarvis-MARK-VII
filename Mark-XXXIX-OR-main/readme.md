# 🤖 MARK XXXIX-OR — Enhanced Edition
### The Ultimate Cross-Platform Personal AI Assistant — Forked & Refined from FatihMakes

> Original by [FatihMakes](https://github.com/FatihMakes/Mark-XXXIX-OR) — Enhanced with performance optimizations, smarter memory, and robust API management.

A real-time voice AI that can hear, see, understand, and control your computer — on any OS. Supporting Windows, macOS, and Linux. Local execution. Zero subscriptions. Engineered for total autonomy.

---

## ✨ Overview

MARK XXXIX-OR represents the pinnacle of the Jarvis series. It bridges the gap between the operating system and human intent. Through natural dialogue, Mark 39 analyzes your screen, processes uploaded documents, and executes complex workflows with a brand-new, adaptive interface.

This enhanced edition builds on the original with significant under-the-hood improvements for reliability, speed, and smarter context awareness.

---

## 🚀 Capabilities

### Core Features
| Feature | Description |
|---|---|
| 🎙️ Real-time Voice | Ultra-low latency conversation in any language |
| 🖥️ System Control | Launch apps, manage files, execute terminal commands |
| 🧩 Autonomous Tasks | High-level planning for complex, multi-step goals |
| 👁️ Visual Awareness | Real-time screen processing and webcam vision |
| 🧠 Persistent Memory | Deeply remembers your projects, preferences, and personal context |
| ⌨️ Hybrid Input | Seamlessly switch between keyboard typing and voice commands |

### Bonus Actions
| Action | Description |
|---|---|
| 🔍 Analyst | Multi-step web research + AI analysis with configurable depth |
| 🌐 Web Search | Real-time internet queries via DuckDuckGo |
| 📁 File Processor | Upload PDFs, images, source code for instant analysis |
| 🔧 Dev Agent | Code generation, debugging, and refactoring assistance |
| ✈️ Flight Finder | Real-time flight search and tracking |
| ⏰ Reminders | Time-based notifications and task scheduling |
| 🌤️ Weather | Live weather reports for any location |
| 🎮 Game Updater | Monitor and auto-update games |
| 📺 YouTube | Search, play, and download YouTube videos |
| 💬 Messenger | Send messages via supported platforms |

---

## 🔧 What's Enhanced

### Robust API Management
- **Multi-key rotation** — Load multiple Google API keys from `.env` or config; rotates randomly to distribute load and avoid quota limits.
- **Environment variable support** — All API keys can be set via `.env` instead of editing JSON config files.
- **Built-in diagnostic tool** — Run `python utils/api_diagnostic.py` to test all API connections, validate key formats, and get troubleshooting recommendations.

### Smarter Memory
- **Dual-engine fallback** — If OpenRouter is rate-limited or unavailable, the memory system automatically falls back to Gemini for extracting and storing memories. Your context is never lost.
- **Timeout protection** — Memory extraction runs with defensive timeouts (15s/30s), preventing the assistant from hanging on slow responses.

### Stability & Performance
- **Graceful shutdown** — Properly closes browser instances and the Qt application on exit — no lingering processes.
- **Reconnection logic** — Up to 10 automatic reconnect attempts with exponential backoff (was infinite, now bounded and smarter).
- **Faster OpenRouter** — Request timeout reduced from 60s to 15s; retry delay from 2s to 1s for snappier fallback responses.
- **Clear error feedback** — HTTP 401/403 responses now show actionable error messages instead of silent failures.

### Search Logging
- **JSONL log output** — All search operations written to `logs/search_log.jsonl` with query, provider, duration, and status.
- **Usage statistics** — Built-in `get_search_stats()` for monitoring search patterns over time.

### Personalization
- **User profile** — Configure your name, preferred title, and assistant name in `memory/long_term.json`.
- **Wake-word awareness** — Assistant responds only when called by its configured name.

---

## ⚡ Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/FatihMakes/Mark-XXXIX-OR.git
cd Mark-XXXIX-OR

# 2. Install dependencies
pip install -r requirements.txt
playwright install

# 3. Configure API keys (choose one method)

# Method A — .env file (recommended)
cp .env.example .env
# Edit .env and add your keys:
#   GOOGLE_API_KEY=your_key_here
#   OPENROUTER_API_KEY=your_key_here

# Method B — config/api_keys.json
# Edit config/api_keys.json and add your keys

# 4. Verify setup
python utils/api_diagnostic.py

# 5. Launch
python main.py
```

> ⚠️ **Installation Note:** To keep the repository lightweight, some OS-specific dependencies are not bundled in `requirements.txt`. If you run into a `ModuleNotFoundError`, simply install the missing package via `pip install <module_name>` for your specific system.

---

## 📋 Requirements

| Requirement | Details |
|---|---|
| **OS** | Windows 10/11, macOS, or Linux |
| **Python** | 3.11 or 3.12 |
| **Microphone** | Required for voice interaction |
| **API Keys** | Free Gemini API key + Free OpenRouter API key |
| **Browser** | Playwright (auto-installed via setup) |

---

## 🏗️ Project Structure

```
Mark-XXXIX-OR/
├── main.py                  # Entry point & real-time voice loop
├── ui.py                    # PyQt6 HUD interface
├── or_client.py             # OpenRouter API client
├── setup.py                 # First-run setup wizard
├── .env                     # Environment variables (API keys, OS)
│
├── config/
│   └── api_keys.json        # JSON-based API key storage
│
├── core/
│   └── prompt.txt           # System prompt & behavior rules
│
├── actions/                 # Tool-calling action modules
│   ├── analyst.py           # ✨ NEW — Deep research + AI analysis
│   ├── browser_control.py
│   ├── code_helper.py
│   ├── computer_control.py
│   ├── computer_settings.py
│   ├── desktop.py
│   ├── dev_agent.py
│   ├── file_controller.py
│   ├── file_processor.py
│   ├── flight_finder.py
│   ├── game_updater.py
│   ├── open_app.py
│   ├── reminder.py
│   ├── screen_processor.py
│   ├── send_message.py
│   ├── weather_report.py
│   ├── web_search.py
│   └── youtube_video.py
│
├── agent/                   # Task planning & execution
│   ├── error_handler.py
│   ├── executor.py
│   ├── planner.py
│   └── task_queue.py
│
├── memory/                  # Persistent memory & context
│   ├── memory_manager.py
│   ├── config_manager.py
│   └── long_term.json       # User profile & preferences
│
├── utils/                   # ✨ NEW — Utility & diagnostic modules
│   ├── api_utils.py         # Centralized API key management
│   ├── api_diagnostic.py    # API connection testing tool
│   └── search_logger.py     # Structured search logging
│
└── logs/                    # Runtime log output
    └── search_log.jsonl
```

---

## 🛠️ Diagnostics

Test your API setup at any time:

```bash
python utils/api_diagnostic.py
```

This checks:
- Google Gemini API key validity & connection
- OpenRouter API key validity & connection  
- Free model availability
- Search library status
- Provides targeted fix recommendations

---

## ⚠️ License

Personal and non-commercial use only.
Licensed under **[Creative Commons BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)**.

---

## 👤 Credits

Original project engineered by **[FatihMakes](https://github.com/FatihMakes)** — building a real-world JARVIS-style assistant.

This fork adds stability hardening, smarter memory fallback, centralized API management, diagnostic tooling, search logging, and a new analyst action module.

⭐ **Star the original repository to support the journey to Mark 100.**

| Platform | Link |
|---|---|
| YouTube | [@FatihMakes](https://www.youtube.com/@FatihMakes) |
| Instagram | [@fatihmakes](https://www.instagram.com/fatihmakes) |
