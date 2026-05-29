# 🕷️ Spidy AI

**Your personal, system-aware AI assistant that lives in your terminal.**

Spidy is not a chatbot — it's an AI OS layer that understands your hardware, your configs, your running services, and your habits. It talks to your local LLM (Ollama) or a cloud provider (OpenRouter), manages windows, files, media, schedule, and code, and adapts to how you actually work.

Built for Arch Linux / EndeavourOS with Hyprland/Wayland, but works on any Linux with minimal setup.

---

## ✨ What Spidy Can Do

### 🖥️ System Control
- Launch apps (`open firefox`, `run vscode`)
- System monitoring ("how's my CPU?", "check memory")
- Window management via Hyprland
- Screenshots and screen control
- System diagnostics and health reports

### 📁 File Management
- Find files, search content with grep
- Move, copy, delete, rename files
- Create folders, archive/compress
- Download files and torrents
- Sort and organize downloads
- Monitor directories for changes

### 🎵 Media & Apps
- Control Spotify playback
- YouTube downloading (yt-dlp)
- Play music and manage media
- App launcher and window focus

### ⏰ Schedule & Productivity
- Set reminders and alarms
- Create and manage todos
- Recurring alarms for daily routines
- Pomodoro timer for focused work
- Study tracker and deadlines
- Calendar sync
- Quick notes and note search

### 💻 Coding Assistant
- Generate code, tests, and docstrings
- Add type hints and refactor code
- Debug and understand codebases
- Multi-file code generation
- Code review and quality checks

### 🧠 Memory & Knowledge
- Persistent conversation history (SQLite)
- Semantic search via ChromaDB vector database
- Long-term memory of user preferences and habits
- RAG knowledge base from docs, configs, and logs
- Session continuity across restarts

### 🗣️ Speech & Voice
- Wake word detection ("Spidy", "Spidey", "Spider")
- Speech-to-text via faster-whisper
- **Streaming text-to-speech** — starts speaking while the LLM is still generating (sentence-level buffering, human-like conversation)
- Text preprocessing for TTS (removes emojis, markdown, decorative characters)
- Dual-language support (Tamil + English)
- Background voice interaction mode

### 🎨 Terminal UI
- Textual-based TUI with rich chat interface
- **Context panel** with real-time system stats, git status, model info, TTS status
- Dark/light theme support
- Splash screen with spider ASCII art
- Keyboard-driven navigation
- OpenCode-inspired dense layout

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.12+
python3 --version

# Ollama with at least one model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma4:e2b

# System dependencies
sudo pacman -S ffmpeg portaudio   # Arch
sudo apt install ffmpeg portaudio  # Debian/Ubuntu
```

### Installation

```bash
# Clone
git clone https://github.com/ROMAABI/spidy-ai.git
cd spidy-ai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .
pip install pyyaml ollama chromadb gtts sounddevice numpy
pip install textual textual-dev
pip install "openai>=1.0" python-dotenv
pip install faster-whisper psutil
```

### Configuration

1. **API Key** — Create `.env` in the project root:
   ```bash
   echo "OPENROUTER_API_KEY=your-key-here" > .env
   ```
   Get a key at [openrouter.ai/keys](https://openrouter.ai/keys). OpenRouter provides access to 200+ models including DeepSeek, Claude, Gemini, and more.

2. **Config** — Edit `config.yaml` to set your preferred model:
   ```yaml
   brain:
     provider: openrouter          # or "ollama"
     cloud_model: deepseek/deepseek-chat-v3-0324
     local_model: gemma4:e2b       # fallback when offline
   tts:
     volume: 85
   ```

---

## 🎮 How to Use

### Terminal UI (Recommended)

```bash
python3 main.py --ui tui
# or just:
python3 main.py
```

**Key Bindings:**

| Key | Action |
|-----|--------|
| `Ctrl+C` | Quit |
| `Ctrl+L` | Clear chat |
| `Ctrl+S` | Toggle sidebar |
| `Ctrl+T` | Toggle TTS on/off |
| `Ctrl+V` | Toggle voice mode |
| `Ctrl+P` | Command palette |
| `F1` | Help |
| `Ctrl+J` / `Ctrl+K` | Navigate messages |
| `Ctrl+R` | Toggle thinking display |

### CLI Mode

```bash
# Interactive chat
python3 main.py --cli

# Single query
python3 main.py "how much RAM am I using?"

# Commands
python3 main.py profile          # Show system profile
python3 main.py diagnose         # Full system health check
python3 main.py doctor           # Fix common issues
python3 main.py snapshot take    # Take system snapshot
```

### Slash Commands

| Command | Description |
|---------|-------------|
| `/clear` | Clear chat history |
| `/sidebar` | Toggle sidebar |
| `/tts` | Toggle text-to-speech |
| `/voice` | Toggle voice/wake-word mode |
| `/model <name>` | Switch AI model |
| `/theme` | Toggle dark/light theme |
| `/think` | Show/hide AI thinking |
| `/check` | Run system diagnostics |
| `/summarize` | Summarize session context |
| `/help` | Show help dialog |

### Voice Mode

1. Press `Ctrl+V` or type `/voice` to arm the wake word detector
2. Say **"Spidy"** followed by your command
3. Speak naturally — Spidy handles Tamil, English, or Tanglish
4. Spidy responds with voice when TTS is enabled
5. Press `Ctrl+V` again to disarm

---

## 🔧 Architecture

```
                  ┌──────────────────────────────┐
                  │     Spidy TUI (Textual)       │
                  │  ChatView  Sidebar  Footer    │
                  └──────────┬───────────────────┘
                             │
                  ┌──────────▼───────────────────┐
                  │    BackendManager             │
                  │  • Intent Router              │
                  │  • Permission System          │
                  │  • Streaming LLM              │
                  │  • Sentence-buffered TTS      │
                  └──┬───────────────┬───────────┘
                     │               │
          ┌──────────▼──────┐  ┌─────▼──────────┐
          │   Core Engine   │  │    Skills       │
          │  • TTS (gTTS)   │  │  • Apps/Media   │
          │  • STT (Whisper)│  │  • Files/Coding │
          │  • Memory/SQLite│  │  • System/Sched │
          │  • ChromaDB RAG │  │  • Search/etc   │
          └─────────────────┘  └────────────────┘
```

### Streaming TTS Pipeline

```
LLM Token Stream
    │
    ▼
Sentence Buffer — splits on . ! ? / newlines / 300-char limit
    │
    ▼
clean_text() — removes emojis, markdown, symbols, borders
    │
    ▼
Thread-safe Queue → Background Worker
                        │
                    gTTS → ffmpeg → normalize → sd.play()
                        │
                    Next sentence generates while current plays
```

### Intent Routing

Spidy classifies every input before deciding what to do:

1. **COMMAND** (confidence ≥ 90%) — Execute directly via skills (no LLM round-trip)
2. **QUESTION** — Route to LLM for answer
3. **CHAT** — Route to LLM for conversation
4. **SEARCH** — Route to search skill or LLM

---

## 📁 Project Structure

```
spidy-ai/
├── main.py                  # Entry point (CLI + TUI)
├── config.yaml              # All configuration
├── app.tcss                 # TUI stylesheet
├── .env                     # API keys (gitignored)
├── pyproject.toml           # Python package config
│
├── core/
│   ├── tts.py               # Streaming TTS engine
│   ├── stt.py               # Speech-to-text (Whisper)
│   ├── actions.py           # System action execution
│   ├── permissions.py       # Risk-based permission system
│   ├── brain.py             # LLM interaction layer
│   ├── assistant.py         # Full assistant logic
│   └── memory.py            # SQLite + ChromaDB memory
│
├── spidy_tui/
│   ├── app.py               # Textual TUI application
│   ├── backend.py           # Async streaming backend
│   ├── theme_manager.py     # Dynamic theme system
│   └── components/
│       ├── chat_view.py     # Chat message display
│       ├── sidebar.py       # Context panel (stats, TTS, git)
│       ├── prompt_bar.py    # Input bar
│       ├── header.py        # Top header
│       ├── footer.py        # Status bar
│       └── dialogs.py       # Help, exit, command dialogs
│
├── skills/
│   ├── apps.py              # Application launcher
│   ├── media.py             # Spotify, yt-dlp, media control
│   ├── search.py            # Web and local search
│   ├── sysinfo.py           # System information
│   ├── hyprland.py          # Hyprland window manager
│   ├── clipboard.py         # Clipboard management
│   ├── code_executor.py     # Code execution
│   ├── screenshot.py        # Screenshot capture
│   ├── alarm.py             # Reminders and alarms
│   ├── files/               # 20+ file management skills
│   ├── schedule/            # Calendar, todos, pomodoro
│   ├── coding/              # Code generation, review, debug
│   └── system/              # App control, system commands
│
├── spidy/
│   ├── system_prompt.py     # System prompt builder
│   ├── profile.py           # System profile discovery
│   ├── config.py            # Configuration loading
│   ├── context.py           # Context aggregation
│   └── agents/              # Agent mode definitions
│
└── tools/
    ├── executor.py          # Tool execution framework
    └── base_tool.py         # Base tool class
```

---

## 🛡️ Safety & Permissions

Spidy uses a risk-based permission system:

| Risk Level | Examples | Behavior |
|------------|----------|----------|
| **CRITICAL** | `rm -rf`, `mkfs`, `shutdown` | Requires explicit safety phrase confirmation |
| **HIGH** | System config changes, package removal | Confirmation prompt required |
| **MEDIUM** | File operations, app launching | Executed automatically |
| **LOW** | Reading files, system info | No restrictions |

All permission decisions are logged to `~/.spidy/audit.jsonl`.

---

## 🎨 Themes

Spidy supports dark and light themes. Toggle with `/theme` or `Ctrl+T`.

The theme system dynamically adjusts:
- Primary/accent colors
- Surface and panel backgrounds
- Text contrast and readability
- Sidebar and header styling

### Custom CSS

The TUI is styled via `app.tcss`. You can customize any element by editing this file. The stylesheet uses Textual's built-in CSS variables (`$primary`, `$accent`, `$surface`, etc.) plus custom `--spidy-*` properties.

---

## 🔄 Provider Configuration

### OpenRouter (Default)

```yaml
brain:
  provider: openrouter
  cloud_model: deepseek/deepseek-chat-v3-0324  # or any OpenRouter model
```

Models available via OpenRouter: DeepSeek, Claude, Gemini, Llama, Mistral, Qwen, and 200+ more.

### Ollama (Local, Fallback)

```yaml
brain:
  provider: ollama
  local_model: gemma4:e2b
```

Spidy automatically falls back to Ollama if OpenRouter is unreachable.

### Dual Provider (Recommended)

When `provider: openrouter`, Spidy attempts OpenRouter first. If it fails, it falls back to Ollama transparently — no interruption.

---

## 🧠 Memory System

Spidy maintains two memory layers:

1. **Short-term** — Recent conversation history (up to 20 messages by default, stored in SQLite)
2. **Long-term** — Semantic vector memory via ChromaDB. Spidy remembers:
   - User preferences ("prefers dark mode", "uses vim")
   - Recurring tasks ("daily backup at 6pm")
   - Past decisions and outcomes
   - Project context and codebase knowledge

Memory is persistent across sessions and automatically retrieved when contextually relevant.

---

## 📊 Context Panel (Sidebar)

The sidebar shows real-time information:

| Section | Data |
|---------|------|
| **Goal** | Current objective, TTS status, queue, latency |
| **Project** | Directory name, git branch, pending changes |
| **Model** | Active model, provider, tokens/sec, online status |
| **TTS** | Engine, volume, queue depth, latency, speaking state |
| **Git** | Branch, uncommitted files, last commit message |
| **System** | CPU%, RAM%, Disk%, uptime (with sparklines) |
| **Actions** | Keyboard shortcut reference |

Toggle the sidebar with `Ctrl+S` or `/sidebar`.

---

## 🌐 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes (for OpenRouter) | — | API key from openrouter.ai |
| `OLLAMA_HOST` | No | `http://localhost:11434` | Ollama server URL |

---

## 🐛 Troubleshooting

### "Ollama not reachable"
```bash
# Check if Ollama is running
systemctl --user status ollama

# Start Ollama
ollama serve
```

### TTS doesn't work (no audio)
```bash
# Check ffmpeg is installed
which ffmpeg

# Test audio output
python -c "import sounddevice; print(sounddevice.query_devices())"
```

### Module not found
```bash
# Ensure virtual environment is active
source venv/bin/activate

# Reinstall
pip install -e .
```

### OpenRouter fails, check API key
```bash
# Verify .env exists
cat .env

# Test key
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/auth/key
```

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Built with [Textual](https://textual.textualize.io/) — the Python TUI framework
- Powered by [Ollama](https://ollama.com/) and [OpenRouter](https://openrouter.ai/)
- Speech by [gTTS](https://github.com/pndurette/gTTS) and [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- Memory via [ChromaDB](https://www.trychroma.com/) and SQLite
