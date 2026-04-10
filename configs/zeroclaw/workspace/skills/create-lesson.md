---
name: create-lesson
trigger: /lesson
description: Generate a complete lesson plan on any topic
---

When triggered with `/lesson <topic>`:

1. Ask: "What age/grade level is this for, and how long should the lesson be?"
2. Search for relevant content: use web_search and check Kiwix for authoritative sources
3. Generate a structured lesson plan and write it to /vault/documents/lesson-<topic>-<date>.md:

```
# Lesson: <Topic>
**Grade level:** X | **Duration:** Y minutes | **Date:** <date>

## Learning Objectives
By the end of this lesson, students will be able to:
- [3-5 measurable objectives]

## Materials Needed
- [list]

## Introduction (X min)
[Hook activity or question to engage students]

## Main Content (X min)
### Key Concept 1
[Explanation + example]

### Key Concept 2
[Explanation + example]

## Activities & Practice (X min)
[Hands-on activity or worked examples]

## Assessment
[3-5 questions to check understanding]

## Extension Activities
[For advanced learners]

## References
[Sources used]
```

4. Send the lesson plan via Telegram and confirm: "Lesson saved to your Obsidian vault. Want me to create quiz questions for this lesson?"
