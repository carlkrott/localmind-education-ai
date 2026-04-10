---
name: morning-briefing
trigger: cron:daily-briefing
description: Daily morning briefing with learning suggestions
---

This skill runs automatically each morning at 08:00.

1. Recall recent sessions from memory to understand what the learner has been studying
2. Check for any pending curriculum tasks or learning goals
3. Search for one interesting fact related to their recent interests
4. Send a Telegram message:

```
🌅 Good morning! Here's your LocalMind daily briefing:

📚 *Continuing from yesterday:* [topic if applicable]

💡 *Today's suggested topics:*
1. [topic based on curriculum or interest]
2. [topic based on recent sessions]
3. [one new interesting area]

🔍 *Did you know?* [interesting fact from web_search or Kiwix]

Ready to learn? Try:
• /explain [topic]
• /quiz [topic]
• /lesson [topic]
```

Keep the message friendly and encouraging. If no recent sessions exist, suggest beginner-friendly topics based on commonly useful skills.
