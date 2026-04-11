---
name: create-lesson
trigger: /lesson
description: Generate a complete lesson plan on any topic
---

When triggered with `/lesson <topic>`:
1. Ask: "What age/grade level and how long should the lesson be?"
2. Search for content using web_search and Kiwix
3. Generate a lesson plan with: objectives, materials, introduction hook, main concepts with examples, practice activities, assessment questions, and references
4. Save to /vault/documents/lesson-<topic>-<date>.md
5. Offer: "Want quiz questions for this lesson?"
