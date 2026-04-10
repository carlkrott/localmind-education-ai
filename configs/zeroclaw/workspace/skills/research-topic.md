---
name: research-topic
trigger: /research
description: Research any topic using SearXNG + Kiwix offline Wikipedia
---

When triggered with `/research <topic>`:

1. Run searches in parallel:
   - web_search via SearXNG: "<topic> overview", "<topic> key concepts"
   - http_request to Kiwix search: http://kiwix/search?q=<topic>&books=wikipedia
2. Synthesize findings into a structured research summary:

```
# Research: <Topic>
**Date:** <date> | **Sources:** Wikipedia + web search

## Overview
[2-3 paragraph summary of the topic]

## Key Facts
- [bullet list of the most important facts]

## How It Works / History / Background
[relevant deep-dive based on topic type]

## Key Figures / Examples
[important people, events, or examples]

## Common Misconceptions
[what people get wrong]

## Further Reading
[links from search results]
```

3. Save to /vault/knowledge/<topic>-<date>.md
4. Send summary via Telegram
5. Offer: "Want me to explain any part in more depth, create a lesson, or quiz you on this?"

**Offline fallback:** If web_search fails (no internet), rely entirely on Kiwix Wikipedia. Note: "Web search unavailable — using offline Wikipedia."
