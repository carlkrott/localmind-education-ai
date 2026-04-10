# LocalMind — Available Tools

## AI Model
- Provider: llama-server at http://llama-server:8080
- Model: Gemma 4 (fine-tuned for education)
- Used for: all reasoning, explanation, lesson generation

## Search & Information
- **web_search** (built-in tool) → DuckDuckGo for general web searches
- **http_request** → SearXNG JSON API for structured search results:
  `GET http://searxng:8080/search?q=<query>&format=json`
- **web_fetch** → Fetch any URL for full article content

## Offline Knowledge Base
- **Kiwix** at http://kiwix — offline Wikipedia, Khan Academy, and more
  - Search: `http://kiwix/search?pattern=<query>&lang=eng`
  - Always try Kiwix first for factual educational content — reliable offline source

## File System (Obsidian Vault)
- **file_read** and **file_write** for /vault/ directory
- /vault/knowledge/ — save key facts and concepts
- /vault/documents/ — lesson plans, audits, generated content
- /vault/curriculum/ — learning paths
- /vault/sessions/ — daily session summaries

## Skills
All skills are available via trigger commands or naturally in conversation:
- /explain <concept>
- /lesson <topic>
- /quiz <topic>
- /research <topic>
- /audit — paste document text
- /curriculum <goal>

## Cron Jobs
- Daily 08:00 — Morning briefing with suggested topics
- Weekly Sunday — Knowledge vault sync and memory hygiene
