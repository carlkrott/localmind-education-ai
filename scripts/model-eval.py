#!/usr/bin/env python3
"""
LocalMind Model Evaluation Suite
Tests 4 models across 5 capability areas, 3 runs each.

Tests:
  1. Tool Calling       - XML function call format (ZeroClaw xml dispatcher)
  2. Critical Thinking  - Multi-step logical reasoning
  3. Document Generation- Structured educational content
  4. Data Extraction    - Parse and structure unformatted text into JSON
  5. Consistency        - Multi-constraint task run 3x, check stability

Usage:
  python model-eval.py --host http://localhost:8080
  python model-eval.py --host http://localhost:8080 --runs 3 --all-models
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime
import urllib.request

# ---------------------------------------------------------------------------
# Test definitions
# ---------------------------------------------------------------------------

TESTS = {
    "tool_calling": {
        "name": "Tool Calling (XML)",
        "description": "Model must emit a valid XML tool call in ZeroClaw format",
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
    },
    "critical_thinking": {
        "name": "Critical Thinking",
        "description": "Multi-step logical reasoning with chain-of-thought",
        "system": "You are a patient tutor. Think step by step before answering.",
        "prompt": (
            "A train travels from City A to City B at 60 km/h. "
            "The return journey is at 40 km/h. "
            "If the total journey time is 5 hours, what is the distance between the cities? "
            "Show ALL working steps."
        ),
    },
    "document_generation": {
        "name": "Document Generation",
        "description": "Generate a structured lesson plan with all required sections",
        "system": "You are an expert curriculum designer.",
        "prompt": (
            "Create a 45-minute lesson plan for teaching 'photosynthesis' to 12-year-olds. "
            "Include: Learning Objectives (3 bullet points), Materials Needed, "
            "Introduction (5 min), Main Activity (25 min), Assessment (10 min), "
            "Homework task. Use markdown formatting."
        ),
    },
    "data_extraction": {
        "name": "Structured Data Extraction",
        "description": "Extract and structure unformatted text into valid JSON",
        "system": "You are a data extraction assistant. Output only valid JSON, no other text.",
        "prompt": (
            "Extract all information from this text into JSON with keys: "
            "student_name, age, subjects (list), grade_average, teacher_comment.\n\n"
            "TEXT: Sarah Johnson who is 14 years old has been studying Mathematics, "
            "English Literature and Biology this term. Her average grade across all "
            "subjects is 78%. Her form teacher Mr. Davies noted that she shows "
            "excellent analytical skills but needs to improve participation in class discussions."
        ),
    },
    "consistency": {
        "name": "Instruction Following & Consistency",
        "description": "Multi-constraint task run 3x — checks compliance and stability",
        "system": "You are a helpful educational assistant. Follow ALL instructions precisely.",
        "prompt": (
            "Write exactly 3 sentences explaining gravity to a 7-year-old. "
            "Rules: (1) Each sentence must be under 15 words. "
            "(2) Do NOT use the words 'force' or 'mass'. "
            "(3) Include a real-world example in the last sentence. "
            "(4) Start each sentence on a new line."
        ),
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
        match = re.search(r"<tool_name>(.*?)</tool_name>", text, re.DOTALL)
        if match:
            notes.append("tool=" + match.group(1).strip())
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
        notes.append("clean (no extra prose)")
    else:
        notes.append("extra prose outside XML ({} chars)".format(len(outside)))

    return score, "; ".join(notes)


def score_critical_thinking(response):
    text = response.lower()
    notes = []
    score = 0

    indicators = ["step", "let", "first", "therefore", "so ", "=", "km/h"]
    found = sum(1 for s in indicators if s in text)
    if found >= 5:
        score += 40
        notes.append("clear steps ({} indicators)".format(found))
    elif found >= 3:
        score += 20
        notes.append("some steps ({})".format(found))
    else:
        notes.append("minimal steps ({})".format(found))

    if "120" in text:
        score += 40
        notes.append("correct answer 120 km")
    else:
        notes.append("WRONG/MISSING answer (expected 120 km)")

    if len(text) > 300:
        score += 20
        notes.append("detailed")
    elif len(text) > 150:
        score += 10
        notes.append("brief")
    else:
        notes.append("very short")

    return min(score, 100), "; ".join(notes)


def score_document_generation(response):
    text = response.lower()
    notes = []
    score = 0

    sections = [
        ("learning objective", 15),
        ("material", 15),
        ("introduction", 15),
        ("main activit", 15),
        ("assessment", 15),
        ("homework", 15),
    ]
    for keyword, pts in sections:
        if keyword in text:
            score += pts
            notes.append(keyword)
        else:
            notes.append("MISSING:" + keyword)

    if "##" in response or "**" in response or "- " in response:
        score += 10
        notes.append("markdown ok")
    else:
        notes.append("no markdown")

    return min(score, 100), "; ".join(notes)


def score_data_extraction(response):
    notes = []
    score = 0

    match = re.search(r"\{.*\}", response, re.DOTALL)
    if not match:
        return 0, "NO JSON found"

    try:
        data = json.loads(match.group(0))
        score += 20
        notes.append("valid JSON")
    except json.JSONDecodeError as exc:
        return 10, "invalid JSON: " + str(exc)

    checks = [
        ("student_name", "sarah", 20),
        ("age", "14", 15),
        ("subjects", None, 15),
        ("grade_average", "78", 15),
        ("teacher_comment", None, 15),
    ]
    for key, expected, pts in checks:
        if key in data:
            val = str(data[key]).lower()
            if expected is None or expected in val:
                score += pts
                notes.append(key + "=ok")
            else:
                score += pts // 2
                notes.append(key + "=wrong_val")
        else:
            notes.append("MISSING:" + key)

    return min(score, 100), "; ".join(notes)


def score_single_consistency(response):
    text = response.strip()
    notes = []
    score = 0

    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 10]
    if len(lines) == 3:
        score += 30
        notes.append("3 sentences")
    else:
        notes.append("{} sentences (want 3)".format(len(lines)))

    violations = [w for w in ["force", "mass"] if w in text.lower()]
    if not violations:
        score += 30
        notes.append("no forbidden words")
    else:
        notes.append("USED forbidden: " + str(violations))

    long_lines = [l for l in lines if len(l.split()) > 15]
    if not long_lines:
        score += 20
        notes.append("sentences <=15 words")
    else:
        notes.append("{} sentences too long".format(len(long_lines)))

    example_words = ["like", "when", "ball", "fall", "drop", "earth", "planet", "jump", "apple", "throw"]
    if lines and any(w in lines[-1].lower() for w in example_words):
        score += 20
        notes.append("example in last sentence")
    else:
        notes.append("example may be missing")

    return score, "; ".join(notes)


def score_consistency(responses):
    scores = [score_single_consistency(r)[0] for r in responses]
    variance = max(scores) - min(scores) if scores else 0
    avg = sum(scores) / len(scores) if scores else 0
    consistency_pts = max(0, 20 - variance)
    final = min(100, int(avg + consistency_pts * 0.3))
    note = "runs={} var={} avg={:.0f} final={}".format(scores, variance, avg, final)
    return final, note


SCORERS = {
    "tool_calling": score_tool_calling,
    "critical_thinking": score_critical_thinking,
    "document_generation": score_document_generation,
    "data_extraction": score_data_extraction,
    "consistency": None,  # handled separately
}

# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------

def chat_completion(host, model, system, prompt, temperature=0.7):
    url = host.rstrip("/") + "/v1/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
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
    except Exception as exc:
        return {"content": "", "elapsed": time.time() - t0, "tps": 0, "error": str(exc)}


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_eval(host, model, runs=3):
    print("\n" + "=" * 70)
    print("  MODEL: {}".format(model))
    print("  Host: {}  |  Runs: {}  |  {}".format(host, runs, datetime.now().strftime("%H:%M:%S")))
    print("=" * 70)

    results = {}

    for test_key, test in TESTS.items():
        print("\n-- {} --".format(test["name"]))
        responses = []
        timings = []

        for run in range(runs):
            print("  run {}/{}...".format(run + 1, runs), end=" ", flush=True)
            r = chat_completion(host, model, test["system"], test["prompt"])
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

        bar = chr(9608) * (score // 10) + chr(9617) * (10 - score // 10)
        print("  Score: {}/100 [{}]  avg {:.1f} tok/s".format(score, bar, avg_tps))
        print("  Notes:", notes)
        if responses[0]:
            snippet = responses[0][:180].replace("\n", " ")
            print("  Preview:", snippet, "...")

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY: {}".format(model))
    print("=" * 70)
    total = 0
    for test_key, test in TESTS.items():
        r = results[test_key]
        bar = chr(9608) * (r["score"] // 10) + chr(9617) * (10 - r["score"] // 10)
        print("  {:<35} [{}] {:3d}/100  {:.1f} t/s".format(
            test["name"], bar, r["score"], r["tps"]
        ))
        total += r["score"]
    overall = total / len(TESTS)
    print("  " + "-" * 60)
    print("  {:<35}  {:3.0f}/100".format("OVERALL", overall))
    print("=" * 70)
    return results, overall


def compare_models(host, model_list, runs):
    all_results = {}
    for model_id, label in model_list:
        input("\n>>> Load model '{}'\n    then press ENTER to start tests...".format(label))
        res, overall = run_eval(host, model_id, runs)
        all_results[label] = (res, overall)

    # Final comparison table
    print("\n" + "=" * 80)
    print("  FINAL COMPARISON")
    print("=" * 80)
    col = 14
    header = "  {:<33}".format("Test")
    for _, label in model_list:
        header += " {:>{}}".format(label[:col], col)
    print(header)
    print("  " + "-" * (33 + col * len(model_list) + len(model_list)))
    for test_key, test in TESTS.items():
        row = "  {:<33}".format(test["name"])
        for _, label in model_list:
            if label in all_results:
                s = all_results[label][0][test_key]["score"]
                row += " {:>{}}".format(str(s) + "/100", col)
        print(row)
    print("  " + "-" * (33 + col * len(model_list) + len(model_list)))
    row = "  {:<33}".format("OVERALL")
    for _, label in model_list:
        if label in all_results:
            row += " {:>{}}".format("{:.0f}/100".format(all_results[label][1]), col)
    print(row)
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LocalMind Model Evaluation")
    parser.add_argument("--host", default="http://localhost:8080")
    parser.add_argument("--model", default="gemma-4-education.gguf")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--all-models", action="store_true",
                        help="Cycle through all 4 models (pauses between each for server swap)")
    args = parser.parse_args()

    if args.all_models:
        models = [
            ("gemma-4-education.gguf",         "E4B Q4_K_XL"),
            ("gemma-4-E4B-it-UD-IQ3_XXS.gguf", "E4B IQ3_XXS"),
            ("gemma-4-E2B-it-IQ4_XS.gguf",     "E2B IQ4_XS"),
            ("gemma-4-E2B-it-UD-IQ3_XXS.gguf", "E2B IQ3_XXS"),
        ]
        compare_models(args.host, models, args.runs)
    else:
        run_eval(args.host, args.model, args.runs)
