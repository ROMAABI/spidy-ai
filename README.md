<div align="center">

```
                                     _     __         ___    ____
                         _________  (_)___/ /_  __   /   |  /  _/
                        / ___/ __ \/ / __  / / / /  / /| |  / /  
                       (__  ) /_/ / / /_/ / /_/ /  / ___ |_/ /   
                      /____/ .___/_/\__,_/\__, /  /_/  |_/___/   
                          /_/            /____/                  
```

# Spidy AI

**Your personal, system-aware AI assistant that lives in your terminal.**

Not a chatbot. An AI OS layer that understands your hardware, your configs, your running services, and your habits.

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Arch Linux](https://img.shields.io/badge/Platform-Arch%20Linux-1793D1.svg)](https://archlinux.org)

</div>

---

## What is Spidy AI?

Spidy sits on your machine and acts like a senior Linux engineer who happens to be a great assistant. It launches your apps, manages your files, controls your media, monitors your system, writes code, remembers your habits, and speaks your language — literally.

```bash
# Open an app
you:  open firefox
spydy: Opening Firefox.

# Check your system
you:  how's my RAM
spydy: RAM: 34% used (5.2 GB / 15.3 GB)

# Voice interaction
you:  "Hey Spidy, play some music"
spydy: [opens Spotify, starts playback]

# Multi-step commands
you:  open firefox and close it after 5 seconds
spydy: [opens Firefox, waits, closes it]
```

---

## Demo

> **Note:** Screenshots and GIFs are generated from the actual running application.
> Run `python3 main.py --ui tui` to see Spidy in action.

| Feature | Preview |
|---------|---------|
| **Chat Interface** | `docs/screenshots/main-ui.png` |
| **Voice Mode** | `docs/screenshots/voice-mode.png` |
| **Skills Execution** | `docs/screenshots/skills.png` |
| **Theme Engine** | `docs/screenshots/themes.png` |
| **Context Panel** | `docs/screenshots/context-panel.png` |

---

## Features

### Core Capabilities

| Capability | Status | Description |
|------------|--------|-------------|
| **Local LLM** | ✅ | Ollama + OpenRouter with streaming responses |
| **System Profile** | ✅ | Auto-detects hardware, OS, desktop, installed tools |
| **Diagnostics** | ✅ | Full system health: CPU, RAM, disk, services, logs |
| **Memory** | ✅ | Persistent conversation + semantic vector search (SQLite + ChromaDB) |
| **Skills** | ✅ | 62 skills for system control, files, media, coding, schedule |
| **Voice** | ✅ | Wake word detection, STT (Whisper), streaming TTS (gTTS) |
| **Terminal UI** | ✅ | Textual-based with chat, sidebar, themes, real-time stats |
| **CLI** | ✅ | `diagnose`, `profile`, `snapshot`, `doctor` commands |
| **Agent Modes** | ✅ | @plan, @build, @general, @system, @research |
| **Permission System** | ✅ | Risk-based safety controls for dangerous commands |
| **Bilingual** | ✅ | Tamil + English + Tanglish automatic detection |

### 62 Built-in Skills

<details>
<summary><b>System Control (15 skills)</b></summary>

| Skill | What it does |
|-------|-------------|
| AppControlSkill | Open, close, focus apps and websites by name |
| VolumeSkill | Volume up/down/mute/unmute |
| BrightnessSkill | Screen brightness control |
| ScreenshotSkill | Capture screenshots (area, window, full) |
| ScreenRecordSkill | Start/stop screen recording |
| WifiSkill | WiFi on/off, scan networks |
| BluetoothSkill | Bluetooth management |
| BatterySkill | Battery status and monitoring |
| DisplaySkill | Display resolution and settings |
| WorkspaceSkill | Hyprland workspace management |
| WallpaperSkill | Change wallpaper |
| NightModeSkill | Night light/blue filter |
| DoNotDisturbSkill | Notification suppression |
| ProcessSkill | Kill/list processes |
| SystemStatsSkill | CPU, RAM, disk, network stats |

</details>

<details>
<summary><b>Schedule & Productivity (15 skills)</b></summary>

| Skill | What it does |
|-------|-------------|
| SetReminderSkill | Set one-time reminders |
| ListRemindersSkill | View all active reminders |
| DeleteReminderSkill | Remove reminders |
| RecurringAlarmSkill | Daily/weekly recurring alarms |
| AddTodoSkill | Create todo items |
| ListTodosSkill | View todo list |
| MarkTodoSkill | Mark todos as complete |
| DailyBriefingSkill | Morning briefing with schedule |
| PomodoroSkill | Pomodoro timer for focus sessions |
| StudyTrackerSkill | Track study time |
| DeadlineAlertSkill | Deadline notifications |
| CalendarSyncSkill | Calendar integration |
| QuickNoteSkill | Jot quick notes |
| NoteSearchSkill | Search through notes |
| WeeklySummarySkill | Weekly activity summary |

</details>

<details>
<summary><b>File Management (20 skills)</b></summary>

| Skill | What it does |
|-------|-------------|
| FindFileSkill | Find files by name/pattern |
| GrepFileSkill | Search file contents |
| OpenFileSkill | Open files with default app |
| MoveCopyDeleteSkill | Move, copy, delete files |
| RenameSkill | Rename files with patterns |
| CreateFolderSkill | Create directory structures |
| ArchiveSkill | Compress/extract archives |
| DuplicatesSkill | Find duplicate files |
| LargeFilesSkill | Find large files consuming space |
| OldFilesSkill | Find old/stale files |
| DownloadUrlSkill | Download files from URLs |
| MonitorDownloadsSkill | Watch download directory |
| AutoSortSkill | Auto-organize files by type |
| TorrentSkill | Torrent management |
| YtDlpSkill | YouTube video/audio downloading |
| AnimeRenameSkill | Rename anime episodes |
| DotfilesSkill | Manage dotfiles |
| SyncExternalSkill | Sync external drives |
| DiskUsageSkill | Disk space analysis |
| TrashSkill | Manage trash/recycle bin |

</details>

<details>
<summary><b>Coding Assistant (15 skills)</b></summary>

| Skill | What it does |
|-------|-------------|
| ReadAndSummarizeSkill | Summarize files and codebases |
| ExplainFunctionSkill | Explain what a function does |
| TraceExecutionSkill | Trace code execution flow |
| DetectCodeSmellsSkill | Identify code quality issues |
| ExplainProjectStructureSkill | Map project architecture |
| ParseErrorSkill | Debug error messages |
| FindDeadCodeSkill | Find unused code |
| ExplainRegexSkill | Explain regex patterns |
| ExplainSqlSkill | Explain SQL queries |
| ExplainConfigSkill | Explain config file formats |
| GenerateFunctionSkill | Generate functions from description |
| GenerateBoilerplateSkill | Generate project boilerplate |
| GenerateTestsSkill | Generate test cases |
| GenerateTypeHintsSkill | Add type hints to Python |
| GenerateDocstringsSkill | Generate docstrings |

</details>

<details>
<summary><b>Standalone Skills (7 skills)</b></summary>

| Skill | What it does |
|-------|-------------|
| AppsSkill | Application launching |
| SysinfoSkill | System information queries |
| MediaSkill | Music/video control |
| SearchSkill | Web and local search |
| MessagingSkill | Message composition |
| CodeExecutorSkill | Execute code snippets |
| ClipboardSkill | Clipboard operations |

</details>

### Agent Modes

| Mode | Description | Can Modify Files |
|------|-------------|-----------------|
| `@plan` | Read-only planning and analysis | No |
| `@build` | Full implementation mode | Yes |
| `@general` | Standard chat mode | Yes |
| `@system` | Linux system administration | Yes |
| `@research` | Deep codebase analysis | No |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Spidy AI TUI                         │
│  ┌──────────┬──────────────────┬─────────────────────┐  │
│  │  Header  │    Chat View     │   Context Panel     │  │
│  │  Status  │  Streaming LLM   │   • Model Status    │  │
│  ├──────────┤  Messages        │   • TTS Status      │  │
│  │  Prompt  │  Skill Execution │   • Git Status      │  │
│  │  Bar     │  Thinking Blocks │   • System Health   │  │
│  ├──────────┴──────────────────┴─────────────────────┤  │
│  │                    Footer                         │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                   Backend Manager                       │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │   Intent    │  │  Streaming   │  │   Permission  │   │
│  │   Router    │  │  LLM Engine  │  │   System      │   │
│  │  (pre-LLM)  │  │  (OpenRouter │  │  (risk-based  │   │
│  │             │  │   + Ollama)  │  │   safety)     │   │
│  └──────┬──────┘  └──────┬───────┘  └───────┬───────┘   │
└─────────┼────────────────┼───────────────────┼──────────┘
          │                │                   │
┌─────────▼────────────────▼───────────────────▼────────-──┐
│                    Core Engine                           │
│  ┌────────┐ ┌────────┐ ┌───────-─┐ ┌──────────────────-┐ │
│  │  TTS   │ │  STT   │ │ Memory  │ │  System Profile   │ │
│  │(stream)│ │ Whisper│ │(SQLite  │ │  (hw, OS, tools)  │ │
│  │        │ │        │ │+Chroma) │ │                   │ │
│  └────────┘ └────────┘ └────────-┘ └──────────────────-┘ │
└─────────────────────────────────────────────────────────-┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                      Skills                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │  System  │ │ Schedule │ │  Files   │ │  Coding  │    │
│  │  (15)    │ │  (15)    │ │  (20)    │ │  (15)    │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
│  ┌─────────-─┐ ┌──────────┐ ┌──────────┐                │
│  │ Standalone│ │  Search  │ │  Media   │                │
│  │   (7)     │ │          │ │          │                │
│  └──────────-┘ └──────────┘ └──────────┘                │
└─────────────────────────────────────────────────────────┘
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

---

## Quick Start

### Prerequisites

```bash
# Python 3.12+
python3 --version

# Ollama (for local models)
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

1. **API Key** — Create `.env`:
   ```bash
   echo "OPENROUTER_API_KEY=your-key-here" > .env
   ```
   Get a key at [openrouter.ai/keys](https://openrouter.ai/keys)

2. **Config** — Edit `config.yaml`:
   ```yaml
   brain:
     provider: openrouter
     cloud_model: deepseek/deepseek-chat-v3-0324
     local_model: gemma4:e2b
   tts:
     volume: 85
   ```

### Run

```bash
# Terminal UI (recommended)
python3 main.py --ui tui

# CLI interactive mode
python3 main.py

# Single query
python3 main.py "how much RAM am I using?"

# System commands
python3 main.py diagnose
python3 main.py profile
python3 main.py snapshot take
python3 main.py doctor
```

---

## Usage

### Terminal UI

```bash
python3 main.py --ui tui
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
| `F1` | Help dialog |
| `Ctrl+J` / `Ctrl+K` | Navigate messages |
| `Ctrl+Home` / `Ctrl+End` | Jump to top/bottom |
| `Ctrl+R` | Toggle thinking display |

### Voice Mode

1. Press `Ctrl+V` to arm the wake word detector
2. Say **"Spidy"** followed by your command
3. Speak naturally in Tamil, English, or Tanglish
4. Spidy responds with voice when TTS is enabled
5. Press `Ctrl+V` again to disarm

**Wake words:** Spidy, Spidey, Spider, Speedy

### Slash Commands

| Command | Description |
|---------|-------------|
| `/clear` | Clear chat history |
| `/sidebar` | Toggle context panel |
| `/tts` | Toggle text-to-speech |
| `/voice` | Toggle wake word detection |
| `/model <name>` | Switch AI model |
| `/theme` | Toggle dark/light theme |
| `/think` | Show/hide AI thinking |
| `/check` | Run system diagnostics |
| `/summarize` | Summarize session |
| `/help` | Show help dialog |

---

## Configuration Reference

```yaml
assistant:
  name: Spidy
  language: auto        # auto-detect Tamil / English / Tanglish
  voice_mode: true

brain:
  provider: openrouter  # "openrouter" or "ollama"
  cloud_model: deepseek/deepseek-chat-v3-0324
  local_model: gemma4:e2b
  temperature: 0.7

stt:
  model: small
  device: cpu
  compute_type: int8
  sample_rate: 16000

tts:
  volume: 85
  english:
    engine: google

memory:
  sqlite_path: memory/spidy.db
  chroma_path: memory/chroma
  max_history: 20

wake:
  words: ["spidy", "spidey", "spider", "speedy"]
  model: tiny
```

---

## Provider Setup

### OpenRouter (Recommended)

Access 200+ models including DeepSeek, Claude, Gemini, Llama, Mistral, Qwen.

```yaml
brain:
  provider: openrouter
  cloud_model: deepseek/deepseek-chat-v3-0324
```

### Ollama (Local, Offline)

Run models locally without internet.

```yaml
brain:
  provider: ollama
  local_model: gemma4:e2b
```

### Dual Provider

When `provider: openrouter`, Spidy attempts cloud first. If it fails, it falls back to Ollama automatically — no interruption.

---

## Project Structure

```
spidy-ai/
├── main.py                  # Entry point
├── config.yaml              # Configuration
├── app.tcss                 # TUI stylesheet
├── .env                     # API keys (gitignored)
│
├── core/
│   ├── tts.py               # Streaming TTS engine
│   ├── stt.py               # Speech-to-text (Whisper)
│   ├── actions.py           # System action execution
│   ├── permissions.py       # Risk-based permission system
│   ├── brain.py             # LLM interaction
│   ├── assistant.py         # Full assistant logic
│   └── memory.py            # SQLite + ChromaDB memory
│
├── spidy_tui/
│   ├── app.py               # Textual TUI
│   ├── backend.py           # Async streaming backend
│   ├── theme_manager.py     # Dynamic themes
│   └── components/          # UI widgets
│
├── skills/
│   ├── system/              # System control (15 skills)
│   ├── schedule/            # Productivity (15 skills)
│   ├── files/               # File management (20 skills)
│   ├── coding/              # Code assistant (15 skills)
│   └── *.py                 # Standalone skills (7)
│
├── spidy/
│   ├── system_prompt.py     # AI identity
│   ├── profile.py           # Hardware discovery
│   ├── commands/            # Slash commands (20+)
│   ├── agents/              # Agent modes (5)
│   ├── memory/              # Memory management
│   ├── rag/                 # RAG pipeline
│   └── diagnostics/         # System diagnostics
│
└── docs/                    # Documentation assets
    ├── screenshots/
    ├── gifs/
    ├── videos/
    └── architecture/
```

---

## Safety

Spidy uses a risk-based permission system:

| Risk Level | Examples | Behavior |
|------------|----------|----------|
| **CRITICAL** | `rm -rf`, `mkfs`, `shutdown` | Safety phrase confirmation required |
| **HIGH** | System config changes | Confirmation prompt |
| **MEDIUM** | File operations, app launching | Auto-executed |
| **LOW** | Reading files, system info | No restrictions |

All actions logged to `~/.spidy/audit.jsonl`.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `textual` | Terminal UI framework |
| `ollama` | Local LLM client |
| `openai` | OpenRouter API client |
| `gtts` | Text-to-speech |
| `faster-whisper` | Speech-to-text |
| `sounddevice` | Audio playback |
| `chromadb` | Vector database |
| `pyyaml` | Configuration |
| `psutil` | System monitoring |
| `python-dotenv` | Environment variables |

---

## Roadmap

- [ ] Gemini / OpenAI / Anthropic provider support
- [ ] Plugin system for custom skills
- [ ] Web UI companion
- [ ] Multi-machine sync
- [ ] Voice cloning
- [ ] Plugin marketplace
- [ ] Docker deployment
- [ ] System tray integration

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with for the Linux community**

[Report Bug](https://github.com/ROMAABI/spidy-ai/issues) · [Request Feature](https://github.com/ROMAABI/spidy-ai/issues)

</div>
