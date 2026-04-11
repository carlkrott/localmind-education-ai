---
name: morning-briefing
trigger: cron:daily-briefing
description: Daily morning briefing with learning suggestions
---

Runs daily at 08:00. Send a Telegram message:
1. Recall recent sessions from memory — note what was studied
2. Suggest 3 topics to study today (based on history or beginner-friendly defaults)
3. Include one interesting fact from web_search or Kiwix
4. Keep it short, friendly, and encouraging
