---
name: audit-document
trigger: /audit
description: Review a document for accuracy, readability, and grade-level appropriateness
---

When triggered with `/audit`:
1. Ask user to paste the document text
2. Ask: "What audience/grade level? Accuracy check, readability, or both?"
3. Review and report:
   - Accuracy: flag incorrect or outdated facts, suggest corrections with sources
   - Readability: flag complex sentences/jargon, suggest simplified rewrites
   - Structure: note gaps in flow or missing transitions
4. Save report to /vault/documents/audit-<date>.md
5. Offer: "Want me to produce a revised version?"
