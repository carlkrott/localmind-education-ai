---
name: research-topic
trigger: /research
description: Research any topic using SearXNG + Kiwix offline Wikipedia
---

When triggered with `/research <topic>`:
1. Search in parallel: web_search for overview + http_request to `http://kiwix/search?pattern=<topic>&lang=eng`
2. Synthesize into: overview paragraph, key facts, background/history, common misconceptions
3. Save to /vault/knowledge/<topic>-<date>.md
4. Offer: "Want a deeper explanation, lesson plan, or quiz on this?"

Offline fallback: if web_search fails, rely on Kiwix only and note it.
