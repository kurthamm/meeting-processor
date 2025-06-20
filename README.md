# 📅 Meeting Processor

A **Docker-ized** meeting transcription & analysis pipeline that:

* 🗄️ **Ingests** MP4 recordings from a watched folder
* 🔊 **Converts** video to high-quality FLAC audio (mono, 16 kHz)
* 🔪 **Chunks** large audio files for Whisper’s API limits
* 🤖 **Transcribes** with OpenAI Whisper (verbose JSON, verbatim)
* 🧠 **Analyzes** (summaries, decisions, action‐items, speaker labels) via Anthropic Claude
* 📝 **Saves** nicely‐formatted Markdown notes into an Obsidian vault
* 🚚 **Archives** processed MP4s into a “processed” directory

---

## 🚀 Features

* **Hands-off operation**: drops your MP4 in `/app/input`, it auto-processes end-to-end.
* **Robust chunking** for recordings > 25 MB.
* **Timeout safeguards** & retry logic for long-running API calls.
* **Rich Obsidian templates**: executive summary, action items, full transcript with speaker labels.
* **Cross‐platform friendly**: runs in Docker on Linux, macOS, Windows (WSL2).
* **Idempotent**: skips files already processed, with periodic “backup” scans.

---

## 📋 Prerequisites

* Docker & Docker Compose installed
* Valid API keys for:

  * [OpenAI Whisper](https://platform.openai.com/)
  * [Anthropic Claude](https://console.anthropic.com/)

---

## 🛠️ Installation

1. **Clone the repo**

   ```bash
   git clone https://github.com/YourUser/meeting-processor.git
   cd meeting-processor
   ```

2. **Copy & fill your environment**

   ```bash
   cp .env.sample .env
   # Open `.env` in your editor and add your API keys!
   ```

3. **Build & run in Docker**

   ```bash
   docker compose up --build -d
   ```

---

## ⚙️ Configuration & Environment

All settings live in `.env`. Key variables:

```env
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...

# Folder mounts inside container
INPUT_DIR=/app/input
OUTPUT_DIR=/app/output
PROCESSED_DIR=/app/processed

# Obsidian vault (host-mounted)
OBSIDIAN_VAULT_PATH=/path/to/your/vault
OBSIDIAN_FOLDER_PATH=00-Capture/meeting-transcripts

# (Optional) Permissions tuning
HOST_UID=1000
HOST_GID=1000

# Debug / test flags
TESTING_MODE=true
COMPOSE_BAKE=true
```

---

## 📂 Directory Layout

```
.
├── .env.sample           # Template for your secrets
├── docker-compose.yml
├── Dockerfile
├── meeting_processor.py  # Main application
├── requirements.txt      # Python dependencies
├── .gitignore
└── README.md             # ← you are here
```

When the container runs, it will **auto-create**:

```
input/      # drop your MP4s here
output/     # FLAC, transcripts, analyses, MD exports
processed/  # original MP4s get moved here when done
logs/       # application logs (if enabled)
```

---

## 🎯 Usage

1. **Drop** your `meeting.mp4` into the `input/` folder.
2. The processor logs will show progress:

   ```
   Converting meeting.mp4 → meeting.flac
   Splitting into chunks…
   Transcribing chunk 1/2…
   Analyzing transcript with Claude AI…
   Saving to Obsidian vault…
   Moving original to processed/
   ```
3. **Open** `/app/output/Your-Topic_YYYY-MM-DD_HH-MM_meeting.md` in Obsidian.

---

## ❓ Troubleshooting

* **File never moves to `processed/`**

  * Check your host→container bind mount is **read-write** (`:rw`).
  * Verify UID/GID match your host user (use `HOST_UID`/`HOST_GID` in `.env`).
* **API timeouts or errors**

  * Ensure your API keys are valid and have quota.
  * Increase `timeout` or chunk size in `meeting_processor.py`.
* **Logs are sparse**

  * Set `LOG_LEVEL=DEBUG` in `.env` (and adjust `logging.basicConfig`).

---

## 🤝 Contributing

1. Fork & create a new branch
2. Make your feature or fix
3. Submit a PR with a clear description
4. We’ll review & merge — thanks!

---

## 📜 License

This project is released under the [MIT License](LICENSE). Feel free to use, modify, and redistribute with attribution.

---

*Built with ❤️ by Kurt Hamm*
*For any questions, open an issue or reach out on GitHub!*
