---
name: explain-concept
trigger: /explain
description: Explain any concept clearly at the appropriate level
---

When triggered with `/explain <concept>`:

1. Ask the learner their current level if not obvious: "What grade/level are you at, or shall I start from the basics?"
2. Give a clear, structured explanation:
   - Start with a one-sentence summary
   - Break into 3-5 key ideas
   - Provide at least one concrete real-world example or analogy
   - Mention any common misconceptions
3. Check understanding: "Does that make sense so far? Want me to go deeper on any part?"
4. If the learner wants more depth, use web_search and Kiwix to find additional details
5. Save key facts to /vault/knowledge/<concept>.md for future reference

Keep explanations appropriately concise. Use markdown for structure but keep it readable in Telegram.
