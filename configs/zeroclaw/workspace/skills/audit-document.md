---
name: audit-document
trigger: /audit
description: Review a document for accuracy, readability, and grade-level appropriateness
---

When triggered with `/audit`:

1. Ask the user to paste the document text (or provide a file path if on local machine)
2. Ask: "What grade level / audience is this for? And what type of audit — accuracy, readability, or both?"
3. Analyse the document:

**Accuracy audit:**
- Cross-check key factual claims using web_search and Kiwix
- Flag anything that appears incorrect or outdated
- Suggest corrections with sources

**Readability audit:**
- Assess reading level (Flesch-Kincaid equivalent)
- Identify overly complex sentences or jargon
- Flag unclear passages
- Suggest simplified rewrites for flagged sections

**Structure audit:**
- Check logical flow
- Identify missing transitions or jumps in reasoning
- Note any sections that need expansion or examples

4. Output a structured report:
```
# Document Audit Report
**Date:** <date> | **Target audience:** <level>

## Summary
[1-2 sentence overall assessment]

## Accuracy Issues
[numbered list of issues with corrections]

## Readability Suggestions
[numbered list with original → improved text]

## Structure Feedback
[notes on flow and organisation]

## Overall Score
Accuracy: X/10 | Readability: X/10 | Structure: X/10
```

5. Save report to /vault/documents/audit-<date>.md
6. Offer: "Want me to produce a revised version of the document?"
