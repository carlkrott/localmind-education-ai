#!/usr/bin/env python3
"""
LocalMind Model Evaluation Suite
Tests 4 models across 7 capability areas, 3 runs each.

Tests:
  1. Tool Calling       - XML function call format (ZeroClaw xml dispatcher)
  2. Critical Thinking  - Multi-step logical reasoning
  3. Document Generation- Structured educational content
  4. Data Extraction    - Parse unformatted text into valid JSON
  5. Consistency        - Multi-constraint task, 3x for stability check
  6. Vision Analysis    - Real multimodal image understanding (requires --mmproj)
  7. Audio Reasoning    - Transcript analysis (production: Whisper → Gemma pipeline)

NOTE ON MULTIMODAL:
  Vision: llama.cpp supports Gemma 4 vision via mmproj file. Server must be
          started with --mmproj /models/mmproj-E4B-F16.gguf (or E2B variant).
          Without it, vision test auto-skips with a clear note.
  Audio:  Gemma 4's audio encoder is NOT exported to GGUF by any tool yet.
          This test uses the realistic production workflow: a Whisper transcript
          is passed to Gemma for educational audio analysis. This reveals how
          well the model reasons about spoken content, tone, and pedagogy.

Usage:
  # Single model test
  python model-eval.py --host http://localhost:8080

  # Full comparison (pauses between models for server swap)
  python model-eval.py --host http://localhost:8080 --all-models --runs 3

  # Enable vision (server must have --mmproj loaded)
  python model-eval.py --host http://localhost:8080 --vision

  # Skip specific tests
  python model-eval.py --skip tool_calling,consistency
"""

import argparse
import base64
import json
import re
import struct
import time
import zlib
from datetime import datetime
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# Test image generator (pure Python, no dependencies)
# Creates a simple educational bar chart PNG for vision test
# ---------------------------------------------------------------------------

def make_test_image_png():
    """
    Generate a 160x100 PNG showing a simple bar chart with 3 coloured bars.
    Bars (left to right): red=70px tall, green=50px tall, blue=85px tall.
    White background, grey baseline.
    Returns raw PNG bytes.
    """
    W, H = 160, 100
    # RGB pixel array (row-major)
    pixels = [[(255, 255, 255)] * W for _ in range(H)]

    baseline = 90  # y coordinate of baseline

    # Draw grey baseline
    for x in range(W):
        pixels[baseline][x] = (100, 100, 100)

    # Bar definitions: (x_start, x_end, height, colour)
    bars = [
        (15, 45, 70, (220, 60, 60)),    # red bar, height 70
        (60, 90, 50, (60, 180, 60)),    # green bar, height 50
        (105, 135, 85, (60, 60, 220)),  # blue bar, height 85
    ]
    for x0, x1, bh, col in bars:
        for y in range(baseline - bh, baseline):
            for x in range(x0, x1):
                pixels[y][x] = col

    # Build PNG
    def u32be(n):
        return struct.pack(">I", n)

    def png_chunk(tag, data):
        c = tag + data
        return u32be(len(data)) + c + u32be(zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = b""
    for row in pixels:
        raw += b"\x00"
        for r, g, b in row:
            raw += bytes([r, g, b])

    idat = zlib.compress(raw, 6)

    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", ihdr)
    png += png_chunk(b"IDAT", idat)
    png += png_chunk(b"IEND", b"")
    return png


TEST_IMAGE_B64 = base64.b64encode(make_test_image_png()).decode("ascii")

# ---------------------------------------------------------------------------
# Test definitions
# ---------------------------------------------------------------------------

TESTS = {
    "tool_calling": {
        "name": "Tool Calling (XML)",
        "description": "Must emit a valid XML tool call in ZeroClaw format",
        "system": (
            "You are an AI assistant with access to tools. "
            "When you need to use a tool, respond ONLY with XML in this exact format:\n"
            "<tool_call>\n"
            "  <tool_name>TOOL_NAME</tool_name>\n"
            "  <parameters>\n"
            "    <param_name>value</param_name>\n"
            "  </parameters>\n"
            "</tool_call>\n"
            "Available tools: web_search(query), file_read(path), calculator(expression)"
        ),
        "prompt": (
            "The student asks: 'What is the square root of 144 multiplied by the population "
            "of Australia?' Use a tool to help answer this."
        ),
        "multimodal": False,
    },
    "critical_thinking": {
        "name": "Critical Thinking",
        "description": "Multi-step logical reasoning with explicit chain-of-thought",
        "system": "You are a patient tutor. Think step by step before answering.",
        "prompt": (
            "A train travels from City A to City B at 60 km/h. "
            "The return journey is at 40 km/h. "
            "If the total journey time is 5 hours, what is the distance between the cities? "
            "Show ALL working steps."
        ),
        "multimodal": False,
    },
    "document_generation": {
        "name": "Document Generation",
        "description": "Structured lesson plan with all 6 required sections in markdown",
        "system": "You are an expert curriculum designer.",
        "prompt": (
            "Create a 45-minute lesson plan for teaching 'photosynthesis' to 12-year-olds. "
            "Include: Learning Objectives (3 bullet points), Materials Needed, "
            "Introduction (5 min), Main Activity (25 min), Assessment (10 min), "
            "Homework task. Use markdown formatting."
        ),
        "multimodal": False,
    },
    "data_extraction": {
        "name": "Structured Data Extraction",
        "description": "Unformatted text → valid JSON with correct fields and values",
        "system": "You are a data extraction assistant. Output only valid JSON, no other text.",
        "prompt": (
            "Extract all information from this text into JSON with keys: "
            "student_name, age, subjects (list), grade_average, teacher_comment.\n\n"
            "TEXT: Sarah Johnson who is 14 years old has been studying Mathematics, "
            "English Literature and Biology this term. Her average grade across all "
            "subjects is 78%. Her form teacher Mr. Davies noted that she shows "
            "excellent analytical skills but needs to improve participation in class discussions."
        ),
        "multimodal": False,
    },
    "consistency": {
        "name": "Instruction Following & Consistency",
        "description": "4-constraint sentence task run 3x — compliance + output stability",
        "system": "You are a helpful educational assistant. Follow ALL instructions precisely.",
        "prompt": (
            "Write exactly 3 sentences explaining gravity to a 7-year-old. "
            "Rules: (1) Each sentence must be under 15 words. "
            "(2) Do NOT use the words 'force' or 'mass'. "
            "(3) Include a real-world example in the last sentence. "
            "(4) Start each sentence on a new line."
        ),
        "multimodal": False,
    },
    "vision_analysis": {
        "name": "Vision Analysis (Multimodal)",
        "description": "Describe a bar chart image — requires server --mmproj flag",
        "system": (
            "You are an educational AI assistant with vision capabilities. "
            "Describe what you see in images clearly and accurately."
        ),
        "prompt": (
            "This image shows a simple bar chart. "
            "Describe: (1) how many bars are shown, (2) the colour of each bar, "
            "(3) which bar appears tallest, and (4) what educational use this chart could serve."
        ),
        "multimodal": True,
        # Image is the generated bar chart (3 bars: red, green, blue)
    },
    "audio_reasoning": {
        "name": "Audio Reasoning (Transcript Analysis)",
        "description": (
            "Realistic Whisper→Gemma pipeline: analyse a lesson transcript for "
            "pedagogy, tone, clarity, and finetuning improvement areas"
        ),
        "system": (
            "You are an educational AI specialist. You will be given a transcript of a "
            "recorded classroom lesson. Analyse it for educational quality."
        ),
        "prompt": (
            "Below is a transcript from a 3-minute audio recording of a Year 8 maths lesson.\n\n"
            "TRANSCRIPT:\n"
            "\"Right everyone, settle down. Today we're doing fractions. "
            "So a fraction is... um... it's like a piece of something. "
            "Like if you cut a pizza into 4 pieces and eat one, you have one-quarter. "
            "Okay so one over four. Does everyone get that? "
            "Good. Now, adding fractions. You need a common denominator. "
            "So one-half plus one-third... the denominator is... anyone? "
            "No? Okay it's six. So you get three-sixths plus two-sixths which is five-sixths. "
            "Right, open your textbooks page 47, questions 1 to 10.\"\n\n"
            "Provide a structured analysis covering:\n"
            "1. Teaching Style (formal/informal, engagement level 1-10)\n"
            "2. Subject Clarity (are concepts explained well? what is missing?)\n"
            "3. Student Engagement Indicators (from speech patterns)\n"
            "4. Specific Improvement Suggestions (3 bullet points)\n"
            "5. Recommended Finetuning Focus (what this model should learn to do better "
            "for audio lesson analysis)"
        ),
        "multimodal": False,
    },
}

# ---------------------------------------------------------------------------
# Scorers
# ---------------------------------------------------------------------------

def score_tool_calling(response):
    text = response.strip()
    notes = []
    score = 0

    if "<tool_call>" in text and "</tool_call>" in text:
        score += 40
        notes.append("has <tool_call>")
    else:
        notes.append("MISSING <tool_call>")
        return score, "; ".join(notes)

    if "<tool_name>" in text and "</tool_name>" in text:
        score += 20
        m = re.search(r"<tool_name>(.*?)</tool_name>", text, re.DOTALL)
        notes.append("tool=" + (m.group(1).strip() if m else "?"))
    else:
        notes.append("MISSING <tool_name>")

    if "<parameters>" in text and "</parameters>" in text:
        score += 20
        notes.append("has <parameters>")
    else:
        notes.append("MISSING <parameters>")

    outside = re.sub(r"<tool_call>.*?</tool_call>", "", text, flags=re.DOTALL).strip()
    if len(outside) < 50:
        score += 20
        notes.append("clean output")
    else:
        notes.append("extra prose ({} chars)".format(len(outside)))

    return score, "; ".join(notes)


def score_critical_thinking(response):
    text = response.lower()
    notes = []
    score = 0

    indicators = ["step", "let", "first", "therefore", "=", "km/h", "km"]
    found = sum(1 for s in indicators if s in text)
    if found >= 5:
        score += 40
        notes.append("clear steps ({})".format(found))
    elif found >= 3:
        score += 20
        notes.append("some steps ({})".format(found))
    else:
        notes.append("minimal steps ({})".format(found))

    if "120" in text:
        score += 40
        notes.append("correct answer 120 km")
    else:
        notes.append("WRONG/MISSING (want 120 km)")

    score += 20 if len(text) > 300 else (10 if len(text) > 150 else 0)
    notes.append("len={}".format(len(text)))

    return min(score, 100), "; ".join(notes)


def score_document_generation(response):
    text = response.lower()
    notes = []
    score = 0

    for keyword, pts in [
        ("learning objective", 15), ("material", 15), ("introduction", 15),
        ("main activit", 15), ("assessment", 15), ("homework", 15),
    ]:
        if keyword in text:
            score += pts
            notes.append(keyword[:8] + "=ok")
        else:
            notes.append("MISS:" + keyword[:8])

    if "##" in response or "**" in response or "- " in response:
        score += 10
        notes.append("markdown=ok")
    else:
        notes.append("no markdown")

    return min(score, 100), "; ".join(notes)


def score_data_extraction(response):
    notes = []
    score = 0

    m = re.search(r"\{.*\}", response, re.DOTALL)
    if not m:
        return 0, "NO JSON"

    try:
        data = json.loads(m.group(0))
        score += 20
        notes.append("valid JSON")
    except json.JSONDecodeError as e:
        return 10, "invalid JSON: " + str(e)

    for key, expected, pts in [
        ("student_name", "sarah", 20), ("age", "14", 15),
        ("subjects", None, 15), ("grade_average", "78", 15),
        ("teacher_comment", None, 15),
    ]:
        if key in data:
            val = str(data[key]).lower()
            if expected is None or expected in val:
                score += pts
                notes.append(key[:8] + "=ok")
            else:
                score += pts // 2
                notes.append(key[:8] + "=wrong")
        else:
            notes.append("MISS:" + key[:8])

    return min(score, 100), "; ".join(notes)


def score_single_consistency(response):
    text = response.strip()
    notes = []
    score = 0

    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 10]
    if len(lines) == 3:
        score += 30
        notes.append("3 lines=ok")
    else:
        notes.append("{} lines (want 3)".format(len(lines)))

    violations = [w for w in ["force", "mass"] if w in text.lower()]
    if not violations:
        score += 30
        notes.append("no forbidden words")
    else:
        notes.append("USED: " + str(violations))

    long_lines = [l for l in lines if len(l.split()) > 15]
    if not long_lines:
        score += 20
        notes.append("lengths=ok")
    else:
        notes.append("{} lines too long".format(len(long_lines)))

    example_words = ["ball", "fall", "drop", "earth", "apple", "jump", "throw",
                     "planet", "like", "example", "when you", "if you"]
    if lines and any(w in lines[-1].lower() for w in example_words):
        score += 20
        notes.append("example=ok")
    else:
        notes.append("example missing?")

    return score, "; ".join(notes)


def score_consistency(responses):
    scores = [score_single_consistency(r)[0] for r in responses if r]
    if not scores:
        return 0, "no responses"
    variance = max(scores) - min(scores)
    avg = sum(scores) / len(scores)
    # Consistency bonus: low variance earns extra points
    consistency_pts = max(0, 20 - variance)
    final = min(100, int(avg + consistency_pts * 0.3))
    return final, "runs={} var={} avg={:.0f}".format(scores, variance, avg)


def score_vision_analysis(response):
    """Score based on correct identification of the test chart:
    3 bars, red/green/blue colours, blue is tallest."""
    text = response.lower()
    notes = []
    score = 0

    # Bar count
    if "3" in text or "three" in text:
        score += 25
        notes.append("3 bars=ok")
    elif "2" in text or "two" in text:
        notes.append("wrong bar count (saw 2)")
    else:
        notes.append("bar count?")

    # Colour identification
    colours_found = [c for c in ["red", "green", "blue"] if c in text]
    score += len(colours_found) * 15
    notes.append("colours={}/3 {}".format(len(colours_found), colours_found))

    # Tallest bar (blue is tallest at 85px)
    if "blue" in text and any(w in text for w in ["tall", "highest", "largest", "biggest"]):
        score += 20
        notes.append("tallest=blue(ok)")
    else:
        notes.append("tallest bar not identified")

    # Educational context suggested
    edu_words = ["chart", "graph", "data", "compare", "lesson", "student", "teach",
                 "visual", "learning", "class", "present"]
    if any(w in text for w in edu_words):
        score += 5
        notes.append("edu_context=ok")

    # Penalise hallucinations (model describes things not in image)
    hallucinations = ["text", "label", "number", "axis", "title", "legend", "word"]
    hall_found = [w for w in hallucinations if w in text]
    if hall_found:
        score -= 10
        notes.append("hallucinated: {}".format(hall_found[:3]))

    return max(0, min(score, 100)), "; ".join(notes)


def score_audio_reasoning(response):
    """Score quality of lesson transcript analysis."""
    text = response.lower()
    notes = []
    score = 0

    # Required sections present
    required = [
        ("teaching style", 15), ("clarity", 15), ("engagement", 15),
        ("improvement", 20), ("suggest", 0),  # alternative word
    ]
    for keyword, pts in required:
        if keyword in text:
            score += pts
            notes.append(keyword[:8] + "=ok")
        else:
            notes.append("MISS:" + keyword[:8])

    # Specific observations about the transcript content
    specifics = ["fraction", "common denominator", "pizza", "informal", "filler",
                 "um", "questioning", "participation"]
    found = sum(1 for w in specifics if w in text)
    if found >= 4:
        score += 20
        notes.append("specific observations={}/{}".format(found, len(specifics)))
    elif found >= 2:
        score += 10
        notes.append("some specifics ({})".format(found))
    else:
        notes.append("generic (lacks specifics)")

    # Finetuning recommendation present
    if "finetuning" in text or "fine-tuning" in text or "fine tuning" in text or "train" in text:
        score += 15
        notes.append("finetune_rec=ok")
    else:
        notes.append("no finetune rec")

    # Response depth (audio analysis should be detailed)
    if len(text) > 500:
        score += 5  # bonus for depth
        notes.append("detailed=ok")

    return min(score, 100), "; ".join(notes)


SCORERS = {
    "tool_calling": score_tool_calling,
    "critical_thinking": score_critical_thinking,
    "document_generation": score_document_generation,
    "data_extraction": score_data_extraction,
    "consistency": None,   # handled specially
    "vision_analysis": score_vision_analysis,
    "audio_reasoning": score_audio_reasoning,
}

# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

def chat_completion(host, model, system, prompt, temperature=0.7, image_b64=None):
    """
    Call the llama.cpp OpenAI-compatible chat completions endpoint.
    If image_b64 is provided, sends a multimodal request with the image.
    """
    url = host.rstrip("/") + "/v1/chat/completions"

    if image_b64:
        # Multimodal message format
        user_content = [
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + image_b64}},
            {"type": "text", "text": prompt},
        ]
    else:
        user_content = prompt

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        "temperature": temperature,
        "max_tokens": 1024,
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            elapsed = time.time() - t0
            data = json.loads(resp.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            comp_tokens = usage.get("completion_tokens", 0)
            tps = comp_tokens / elapsed if elapsed > 0 else 0
            return {"content": content, "elapsed": elapsed, "tps": tps, "error": None}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"content": "", "elapsed": time.time() - t0, "tps": 0,
                "error": "HTTP {}: {}".format(exc.code, body[:200])}
    except Exception as exc:
        return {"content": "", "elapsed": time.time() - t0, "tps": 0, "error": str(exc)}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_eval(host, model, runs=3, skip_tests=None, vision_enabled=False):
    skip_tests = skip_tests or []

    print("\n" + "=" * 72)
    print("  MODEL: {}".format(model))
    print("  Host: {}  |  Runs: {}  |  {}".format(
        host, runs, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    if not vision_enabled:
        print("  NOTE: Vision test will be skipped (use --vision when mmproj is loaded)")
    print("=" * 72)

    results = {}

    for test_key, test in TESTS.items():
        if test_key in skip_tests:
            print("\n[SKIP] {}".format(test["name"]))
            results[test_key] = {"score": None, "tps": 0, "notes": "skipped"}
            continue

        is_vision = test.get("multimodal", False)
        if is_vision and not vision_enabled:
            print("\n[SKIP] {} — server not loaded with --mmproj".format(test["name"]))
            print("       Restart server with: --mmproj /models/mmproj-E4B-F16.gguf (or E2B)")
            results[test_key] = {"score": None, "tps": 0,
                                  "notes": "SKIP: server needs --mmproj flag"}
            continue

        print("\n-- {} --".format(test["name"]))
        print("   {}".format(test["description"]))

        responses = []
        timings = []
        image = TEST_IMAGE_B64 if is_vision else None

        for run in range(runs):
            print("   run {}/{}...".format(run + 1, runs), end=" ", flush=True)
            r = chat_completion(host, model, test["system"], test["prompt"],
                                image_b64=image)
            if r["error"]:
                print("ERROR:", r["error"])
                responses.append("")
                timings.append(0.0)
            else:
                responses.append(r["content"])
                timings.append(r["tps"])
                print("{:.1f}s | {:.1f} tok/s".format(r["elapsed"], r["tps"]))

        if test_key == "consistency":
            score, notes = score_consistency(responses)
        else:
            scorer = SCORERS[test_key]
            run_scores = [scorer(resp) for resp in responses if resp]
            score = int(sum(s for s, _ in run_scores) / len(run_scores)) if run_scores else 0
            notes = run_scores[0][1] if run_scores else "no response"

        avg_tps = sum(timings) / len(timings) if timings else 0.0
        results[test_key] = {"score": score, "tps": avg_tps, "notes": notes}

        bar = "#" * (score // 10) + "." * (10 - score // 10)
        print("   Score: {}/100 [{}]  avg {:.1f} tok/s".format(score, bar, avg_tps))
        print("   Notes:", notes)
        if responses and responses[0]:
            snippet = responses[0][:200].replace("\n", " ")
            print("   Preview:", snippet, "...")

    # Summary
    active = {k: v for k, v in results.items() if v["score"] is not None}
    total = sum(r["score"] for r in active.values())
    overall = total / len(active) if active else 0

    print("\n" + "=" * 72)
    print("  SUMMARY: {}".format(model))
    print("=" * 72)
    for test_key, test in TESTS.items():
        r = results.get(test_key, {"score": None, "tps": 0})
        if r["score"] is None:
            print("  {:<37}  [----------]  SKIP".format(test["name"]))
        else:
            bar = chr(9608) * (r["score"] // 10) + chr(9617) * (10 - r["score"] // 10)
            print("  {:<37} [{}] {:3d}/100  {:.1f} t/s".format(
                test["name"], bar, r["score"], r["tps"]))
    print("  " + "-" * 63)
    print("  {:<37}  {:3.0f}/100".format("OVERALL (active tests)", overall))
    print("=" * 72)
    return results, overall


def compare_models(host, model_list, runs, vision_enabled):
    all_results = {}
    for model_id, label, mmproj_hint in model_list:
        print("\n" + "=" * 72)
        print("  NEXT: {} ({})".format(label, model_id))
        if vision_enabled:
            print("  Load server with: --mmproj /models/{}".format(mmproj_hint))
        input("  Press ENTER when server is ready...")
        res, overall = run_eval(host, model_id, runs, vision_enabled=vision_enabled)
        all_results[label] = (res, overall)

    # Comparison table
    print("\n" + "=" * 80)
    print("  FINAL MODEL COMPARISON")
    print("=" * 80)
    col = 13
    header = "  {:<37}".format("Test")
    for _, label, _ in model_list:
        header += " {:>{}}".format(label[:col], col)
    print(header)
    print("  " + "-" * (37 + (col + 1) * len(model_list)))

    for test_key, test in TESTS.items():
        row = "  {:<37}".format(test["name"])
        for _, label, _ in model_list:
            if label in all_results:
                s = all_results[label][0].get(test_key, {}).get("score")
                row += " {:>{}}".format("SKIP" if s is None else "{}/100".format(s), col)
        print(row)

    print("  " + "-" * (37 + (col + 1) * len(model_list)))
    row = "  {:<37}".format("OVERALL")
    for _, label, _ in model_list:
        if label in all_results:
            row += " {:>{}}".format("{:.0f}/100".format(all_results[label][1]), col)
    print(row)
    print("=" * 80)

    # Finetuning recommendations
    print("\n  FINETUNING FOCUS RECOMMENDATIONS")
    print("  (tests scoring below 50 indicate high-value training areas)")
    print("  " + "-" * 63)
    for test_key, test in TESTS.items():
        weak_models = []
        for _, label, _ in model_list:
            if label in all_results:
                s = all_results[label][0].get(test_key, {}).get("score")
                if s is not None and s < 50:
                    weak_models.append("{} ({}%)".format(label, s))
        if weak_models:
            print("  {:<30} WEAK: {}".format(test["name"], ", ".join(weak_models)))
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LocalMind Model Evaluation")
    parser.add_argument("--host", default="http://localhost:8080")
    parser.add_argument("--model", default="gemma-4-education.gguf")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--vision", action="store_true",
                        help="Enable vision test (server must have --mmproj loaded)")
    parser.add_argument("--skip", default="",
                        help="Comma-separated test keys to skip")
    parser.add_argument("--all-models", action="store_true",
                        help="Cycle through all 4 models with comparison table")
    args = parser.parse_args()

    skip_list = [s.strip() for s in args.skip.split(",") if s.strip()]

    if args.all_models:
        models = [
            ("gemma-4-education.gguf",         "E4B Q4_K_XL",  "mmproj-E4B-F16.gguf"),
            ("gemma-4-E4B-it-UD-IQ3_XXS.gguf", "E4B IQ3_XXS",  "mmproj-E4B-F16.gguf"),
            ("gemma-4-E2B-it-IQ4_XS.gguf",     "E2B IQ4_XS",   "mmproj-E2B-F16.gguf"),
            ("gemma-4-E2B-it-UD-IQ3_XXS.gguf", "E2B IQ3_XXS",  "mmproj-E2B-F16.gguf"),
        ]
        compare_models(args.host, models, args.runs, args.vision)
    else:
        run_eval(args.host, args.model, args.runs,
                 skip_tests=skip_list, vision_enabled=args.vision)
