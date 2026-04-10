#!/usr/bin/env bash
# LocalMind setup script — run once after cloning the repo
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║          LocalMind — Setup Script                ║"
echo "║   Offline-First AI Education Companion           ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Check Docker
if ! command -v docker &>/dev/null; then
    echo "ERROR: Docker not found. Install Docker Desktop from https://docker.com"
    exit 1
fi

if ! docker ps &>/dev/null; then
    echo "ERROR: Docker daemon not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✓ Docker is running ($(docker --version | cut -d' ' -f3 | tr -d ','))"

# Check for model file
if [ -z "$(ls models/*.gguf 2>/dev/null)" ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "STEP REQUIRED: Place your fine-tuned Gemma model in the models/ directory."
    echo ""
    echo "Expected filename: models/gemma-4-education.gguf"
    echo ""
    echo "If you haven't fine-tuned yet, you can use the base model:"
    echo "  Download gemma-4-E2B-it-UD-Q4_K_XL.gguf from HuggingFace or your NAS"
    echo "  Rename it to: models/gemma-4-education.gguf"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    read -p "Press Enter once you've placed the model file, or Ctrl+C to exit..."
fi

# Rename model if needed
if [ ! -f "models/gemma-4-education.gguf" ] && [ -n "$(ls models/*.gguf 2>/dev/null)" ]; then
    FIRST_MODEL=$(ls models/*.gguf | head -1)
    echo "Found model: $FIRST_MODEL"
    cp "$FIRST_MODEL" models/gemma-4-education.gguf
    echo "✓ Copied as models/gemma-4-education.gguf"
fi

# Create Obsidian vault structure
mkdir -p obsidian-vault/{knowledge,documents,curriculum,sessions}
echo "✓ Obsidian vault directories created"

# Download SearXNG secret key generation
if grep -q "localm ind-secret-change-in-production" configs/searxng/settings.yml; then
    NEW_SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/localm ind-secret-change-in-production/$NEW_SECRET/g" configs/searxng/settings.yml
    echo "✓ Generated SearXNG secret key"
fi

# Check for Kiwix ZIM files
if [ -z "$(ls kiwix-data/*.zim 2>/dev/null)" ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "OPTIONAL: Download offline Wikipedia for Kiwix"
    echo "Run: bash scripts/download-zim.sh"
    echo "(This downloads ~22GB — skip for initial testing)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi

# Pull Docker images
echo "Pulling Docker images (this may take a few minutes)..."
docker compose pull --quiet
echo "✓ Docker images pulled"

# Start the stack
echo ""
echo "Starting LocalMind stack..."
docker compose up -d

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✓ LocalMind is starting up!"
echo ""
echo "Services:"
echo "  AI Model (llama.cpp):  http://localhost:8080"
echo "  Search (SearXNG):      http://localhost:8888"
echo "  Offline Docs (Kiwix):  http://localhost:9090"
echo "  ZeroClaw gateway:      http://localhost:42617"
echo ""
echo "Waiting for llama-server to load model (~30-60 seconds)..."
echo ""

# Wait for llama-server health
for i in {1..30}; do
    if curl -sf http://localhost:8080/health &>/dev/null; then
        echo "✓ AI model loaded and ready!"
        break
    fi
    echo -n "."
    sleep 3
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TELEGRAM SETUP"
echo "Configure the bot token in: configs/zeroclaw/config.toml"
echo "  [channels_config.telegram]"
echo "  bot_token = \"YOUR_BOT_TOKEN\""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Setup complete! LocalMind is running."
