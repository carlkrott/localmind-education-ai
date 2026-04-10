#!/usr/bin/env bash
# Prepare fine-tuning dataset for Unsloth Studio
# Pulls educational content from Dell NAS and converts to JSONL format
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATASET_DIR="$REPO_DIR/dataset"
mkdir -p "$DATASET_DIR"

DELL_NAS="root@100.64.0.7"
NAS_EDUCATION="/mnt/nas/toshiba2tb-a/knowledge/education"
NAS_GUTENBERG="/mnt/nas/toshiba2tb-a/gutenberg"

echo "Preparing LocalMind fine-tuning dataset"
echo ""

# Step 1: Pull Khan Academy exercises from NAS
echo "Pulling Khan Academy exercises from Dell NAS..."
if ssh -o ConnectTimeout=10 "$DELL_NAS" "ls $NAS_EDUCATION/khan-exercises" &>/dev/null; then
    rsync -avz --progress "$DELL_NAS:$NAS_EDUCATION/khan-exercises/" "$DATASET_DIR/khan-raw/"
    echo "✓ Khan exercises synced"
else
    echo "⚠ Khan exercises not found at $NAS_EDUCATION/khan-exercises — skipping"
fi

# Step 2: Pull Gutenberg educational texts
echo "Pulling Gutenberg texts from Dell NAS..."
if ssh -o ConnectTimeout=10 "$DELL_NAS" "ls $NAS_GUTENBERG" &>/dev/null; then
    rsync -avz --progress --include="*.txt" --include="*.html" --exclude="*" \
        "$DELL_NAS:$NAS_GUTENBERG/" "$DATASET_DIR/gutenberg-raw/" 2>/dev/null || true
    echo "✓ Gutenberg texts synced"
else
    echo "⚠ Gutenberg not found at $NAS_GUTENBERG — skipping"
fi

# Step 3: Convert to JSONL instruction format
echo ""
echo "Converting to instruction-response JSONL format..."
python3 - <<'PYEOF'
import os, json, re, glob

dataset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dataset")
output_file = os.path.join(dataset_dir, "education-dataset.jsonl")

records = []

# Process Khan Academy exercises
khan_dir = os.path.join(dataset_dir, "khan-raw")
if os.path.exists(khan_dir):
    for f in glob.glob(os.path.join(khan_dir, "**/*.json"), recursive=True)[:500]:
        try:
            with open(f) as fh:
                data = json.load(fh)
            # Extract Q&A pairs from Khan exercise format
            if isinstance(data, dict) and "question" in data:
                q = data.get("question", {}).get("content", "")
                a = data.get("solution", data.get("answer", ""))
                if q and a:
                    records.append({
                        "instruction": q,
                        "response": str(a),
                        "source": "khan_academy"
                    })
        except Exception:
            pass
    print(f"Processed {len(records)} Khan Academy records")

# Add hardcoded educational instruction pairs as seed data
seed_pairs = [
    {"instruction": "Explain the water cycle to a 10-year-old", "response": "The water cycle is nature's way of recycling water! Here's how it works:\n\n1. **Evaporation**: When the sun heats up water in oceans, lakes, and rivers, the water turns into water vapor (like invisible steam) and rises into the air.\n\n2. **Condensation**: As water vapor rises high into the sky where it's cooler, it turns back into tiny water droplets. These droplets clump together to form clouds.\n\n3. **Precipitation**: When the clouds collect too much water, it falls back down as rain, snow, or hail.\n\n4. **Collection**: The water collects in rivers, lakes, and oceans — and the whole cycle starts again!\n\nThink of it like the Earth recycling its water over and over, never losing a drop.", "source": "seed"},
    {"instruction": "What is photosynthesis?", "response": "Photosynthesis is the process plants use to make their own food using sunlight.\n\n**The simple equation:**\nSunlight + Water + Carbon dioxide → Sugar (food) + Oxygen\n\n**Where it happens:** Inside special parts of plant cells called chloroplasts, which contain a green pigment called chlorophyll (that's why plants are green!).\n\n**Why it matters:**\n- Plants get the energy they need to grow\n- Animals (including us) eat plants for energy\n- Plants release oxygen as a byproduct — the oxygen we breathe!\n\n**A helpful analogy:** Think of a plant as a tiny solar-powered factory. The sun is the power source, water and CO₂ are the raw materials, and sugar is the product that fuels the plant.", "source": "seed"},
    {"instruction": "How do I solve a quadratic equation?", "response": "A quadratic equation has the form **ax² + bx + c = 0**. Here are three methods:\n\n## Method 1: Factoring (easiest when it works)\nExample: x² + 5x + 6 = 0\nFind two numbers that multiply to 6 and add to 5 → (2 and 3)\n(x + 2)(x + 3) = 0 → x = -2 or x = -3\n\n## Method 2: Quadratic Formula (always works)\nx = (-b ± √(b² - 4ac)) / 2a\n\nExample: 2x² - 4x - 6 = 0\na=2, b=-4, c=-6\nx = (4 ± √(16 + 48)) / 4 = (4 ± 8) / 4\nx = 3 or x = -1\n\n## Method 3: Completing the Square\n(Advanced — useful for understanding the formula derivation)\n\n**Tip:** Always check your answers by plugging them back into the original equation!", "source": "seed"},
    {"instruction": "What caused World War I?", "response": "World War I (1914-1918) had several interconnected causes, often remembered by the acronym **MAIN**:\n\n**M — Militarism**\nEuropean nations were building up huge armies and navies, creating an arms race and a culture where war seemed like a solution.\n\n**A — Alliances**\nEurope was divided into two armed camps:\n- Triple Alliance: Germany, Austria-Hungary, Italy\n- Triple Entente: France, Russia, Britain\nThis meant a small conflict could drag in everyone.\n\n**I — Imperialism**\nEuropean powers competed for colonies and resources, creating tensions and rivalries.\n\n**N — Nationalism**\nStrong national pride and the desire for self-determination (especially in the Balkans) created instability.\n\n**The Spark:** Archduke Franz Ferdinand of Austria-Hungary was assassinated in Sarajevo (June 28, 1914), triggering the alliance system like dominoes falling.", "source": "seed"},
    {"instruction": "Explain Newton's three laws of motion simply", "response": "Newton's three laws explain how objects move:\n\n**Law 1 — Inertia:** An object at rest stays at rest, and an object in motion stays in motion, unless a force acts on it.\n→ *Think:* A ball on the floor won't move until you kick it. A rolling ball would roll forever if there was no friction.\n\n**Law 2 — F = ma:** Force = mass × acceleration. The bigger the force, the more acceleration. The heavier the object, the more force needed.\n→ *Think:* It's easier to push an empty shopping cart than a full one.\n\n**Law 3 — Action/Reaction:** For every action, there is an equal and opposite reaction.\n→ *Think:* When you jump, you push the ground down — the ground pushes you up. Rockets work this way: they push exhaust down, which pushes the rocket up!\n\nThese three laws form the foundation of classical mechanics and explain almost all everyday motion.", "source": "seed"},
]
records.extend(seed_pairs)

print(f"Total records (including seed): {len(records)}")

with open(output_file, "w") as fh:
    for r in records:
        fh.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"Dataset saved to: {output_file}")
print(f"Ready to import into Unsloth Studio!")
PYEOF

echo ""
echo "✓ Dataset preparation complete!"
echo ""
echo "Next steps for fine-tuning in Unsloth Studio:"
echo "  1. Open Unsloth Studio on your PC"
echo "  2. Load base model: gemma-4-E2B-it-UD-Q4_K_XL.gguf"
echo "  3. Import dataset: dataset/education-dataset.jsonl"
echo "  4. Run fine-tuning (QLoRA recommended, 3 epochs)"
echo "  5. Export merged model as GGUF → save to models/gemma-4-education.gguf"
