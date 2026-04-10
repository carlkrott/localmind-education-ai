---
name: curriculum
trigger: /curriculum
description: Build a multi-session learning path toward any goal
---

When triggered with `/curriculum <goal>`:

1. Clarify:
   - "What's your current level on this topic?"
   - "How much time can you dedicate per day/week?"
   - "What's your end goal — understanding, exam prep, practical skill?"
2. Research the topic using web_search + Kiwix to understand prerequisites and key milestones
3. Generate a curriculum plan and save to /vault/curriculum/<goal>-curriculum.md:

```
# Learning Curriculum: <Goal>
**Created:** <date> | **Duration:** X weeks | **Daily time:** Y minutes

## Prerequisites
[what the learner needs to know first]

## Learning Objectives
By the end, you will be able to:
- [3-5 concrete outcomes]

## Week-by-Week Plan
### Week 1: <Theme>
- Day 1: <Topic> — [use /explain <topic>]
- Day 2: <Topic> — [use /explain <topic>]
- Day 3: Practice — [use /quiz <topics from week>]
- Day 4: <Topic>
- Day 5: Review & reflection

### Week 2: <Theme>
[...]

## Milestones & Check-ins
- End of Week 1: [what learner should be able to do]
- End of Week 2: [...]
- Final assessment: [project or quiz]

## Resources
[Kiwix + web links]
```

4. Send summary via Telegram
5. Offer: "Want to start with Week 1, Day 1 now? I'll create the first lesson."
