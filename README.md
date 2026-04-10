# LocalMind — Offline-First AI Education Companion

> *Built for the [Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon)*

**LocalMind** is an AI education assistant that runs entirely on your local machine — no cloud, no internet required. Powered by a fine-tuned [Gemma 4](https://ai.google.dev/gemma) model, it provides personalised learning support to students and teachers even in schools with no reliable internet connection.

---

## What It Does

Talk to LocalMind via **Telegram** (works on any phone) and get:

- **Concept explanations** — Break down any topic at your learning level
- **Lesson plans** — Generate complete lesson plans with objectives, activities, and assessments
- **Interactive quizzes** — Test your knowledge with instant, constructive feedback
- **Research assistance** — Search offline Wikipedia + Khan Academy when offline, or the web when online
- **Document auditing** — Get educational materials reviewed for accuracy and readability
- **Learning curricula** — Build structured multi-week learning paths toward any goal

All outputs are saved to an Obsidian vault for persistent knowledge management.

---

## Why It Matters

Millions of students study in schools with unreliable internet. AI tutors, Wikipedia, and online learning platforms are effectively unavailable to them. LocalMind runs on any Windows PC — a school computer lab is enough. No subscription, no data leaving the building, no latency.

- **Accessibility score:** Runs on CPU (no GPU required), 8GB RAM, any Windows PC
- **Privacy:** Nothing leaves the local network
- **Reliability:** Works fully offline once set up

---

## Architecture

```
User (Telegram) ←→ ZeroClaw Agent ←→ Gemma 4 (llama.cpp, local)
                         ↓
              ┌──────────┴──────────┐
          SearXNG              Kiwix Server
        (web search)     (offline Wikipedia +
                           Khan Academy)
                         ↓
                   Obsidian Vault
               (persistent knowledge)
```

All components run via Docker Compose — one command to start everything.

---

## Quick Start

### Prerequisites

- Windows 10/11 (or Linux/macOS)
- [Docker Desktop](https://docker.com/products/docker-desktop) installed and running
- 8GB RAM minimum (16GB recommended)
- ~2GB disk space for the model + ZIM files if downloading Wikipedia
- A Telegram bot token (create one via [@BotFather](https://t.me/botfather))

### 1. Clone the repository

```bash
git clone https://github.com/your-username/localm ind-education-ai
cd localm ind-education-ai
```

### 2. Get the model

Place your fine-tuned Gemma 4 model (GGUF format) in the `models/` directory as `gemma-4-education.gguf`.

**Option A: Use the pre-quantized base model (no fine-tuning)**
Download `gemma-4-E2B-it-UD-Q4_K_XL.gguf` from [Unsloth on HuggingFace](https://huggingface.co/unsloth) and rename it.

**Option B: Fine-tune first** (recommended for best results)
See [Fine-Tuning Guide](#fine-tuning-guide) below.

### 3. Configure Telegram

Edit `configs/zeroclaw/config.toml` and set your bot token:
```toml
[channels_config.telegram]
bot_token = "YOUR_BOT_TOKEN_HERE"
allowed_users = ["YOUR_TELEGRAM_USER_ID"]
```

### 4. Run setup

```bash
bash scripts/setup.sh
```

This pulls Docker images, starts all services, and waits for the model to load.

### 5. Start learning!

Open Telegram, message your bot, and try:
- `/explain photosynthesis`
- `/lesson "The French Revolution" for grade 9`
- `/quiz algebra for beginners`

---

## Offline Knowledge (Optional)

Download Wikipedia and Khan Academy for fully offline use:

```bash
bash scripts/download-zim.sh
```

This downloads ~25GB. Without this, LocalMind uses SearXNG web search when internet is available.

---

## Fine-Tuning Guide

To fine-tune Gemma 4 on educational content:

### 1. Prepare the dataset

```bash
bash scripts/prepare-dataset.sh
```

This pulls educational content from your local sources and creates `dataset/education-dataset.jsonl`.

### 2. Fine-tune with Unsloth Studio

1. Download [Unsloth Studio](https://unsloth.ai/studio) for Windows
2. Open the application
3. Load base model: select the `gemma-4-E2B` or `gemma-4-E4B` GGUF file
4. Import dataset: `dataset/education-dataset.jsonl`
5. Configure training: QLoRA, 3 epochs, learning rate 2e-4
6. Run fine-tuning
7. Export merged model as GGUF → save to `models/gemma-4-education.gguf`
8. Run `docker compose restart llama-server`

---

## Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| llama-server | 8080 | Gemma 4 inference via llama.cpp |
| zeroclaw | 42617 | AI agent daemon + Telegram bot |
| searxng | 8888 | Local web search |
| kiwix | 9090 | Offline Wikipedia + Khan Academy |

---

## Skills Reference

| Command | Description |
|---------|-------------|
| `/explain <concept>` | Step-by-step explanation at your level |
| `/lesson <topic>` | Full lesson plan with objectives and exercises |
| `/quiz <topic>` | Interactive quiz with instant feedback |
| `/research <topic>` | Research summary from Wikipedia + web |
| `/audit` | Paste a document for accuracy/readability review |
| `/curriculum <goal>` | Multi-week learning path |

---

## Hackathon Details

**Competition:** [Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon) — Google/Kaggle/Unsloth  
**Category:** Education — AI for underserved communities  
**Model:** Gemma 4 E2B (fine-tuned with Unsloth)  
**Theme:** Offline-first, privacy-preserving, accessible AI education

---

## License

Apache 2.0 — same as the Gemma 4 model license.
