#!/usr/bin/env bash
# Download Kiwix ZIM files for offline use
# Fetches Wikipedia (mini) and Khan Academy
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ZIM_DIR="$REPO_DIR/kiwix-data"
mkdir -p "$ZIM_DIR"

echo "Downloading Kiwix ZIM files to $ZIM_DIR"
echo "This will download ~22GB total. Ctrl+C to cancel."
echo ""

# Wikipedia English Mini (~22GB)
WIKIPEDIA_URL="https://download.kiwix.org/zim/wikipedia/wikipedia_en_wp_mini_2024-10.zim"
echo "1/2 Wikipedia (mini) — ~22GB"
wget -c -q --show-progress -O "$ZIM_DIR/wikipedia_en_mini.zim" "$WIKIPEDIA_URL"
echo "✓ Wikipedia downloaded"

# Khan Academy (~3GB)
KHAN_URL="https://download.kiwix.org/zim/khan_academy/khan_academy_en_all_2024-04.zim"
echo "2/2 Khan Academy — ~3GB"
wget -c -q --show-progress -O "$ZIM_DIR/khan_academy_en.zim" "$KHAN_URL"
echo "✓ Khan Academy downloaded"

echo ""
echo "All ZIM files downloaded to $ZIM_DIR"
echo "Restart the kiwix container to pick up new files:"
echo "  docker compose restart kiwix"
