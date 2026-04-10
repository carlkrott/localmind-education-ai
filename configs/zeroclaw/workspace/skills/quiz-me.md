---
name: quiz-me
trigger: /quiz
description: Interactive quiz on any topic with instant feedback
---

When triggered with `/quiz <topic>`:

1. Ask: "How many questions? And what difficulty — beginner, intermediate, or advanced?"
2. Generate questions one at a time (do NOT reveal all at once):
   - Ask one question
   - Wait for user's answer
   - Give immediate feedback: correct/incorrect + explanation of why
   - Move to next question
3. Mix question types: multiple choice, short answer, "explain in your own words"
4. Keep score: "Question 3 of 5 — Score so far: 2/2 ✓"
5. At the end, give a summary:
   - Final score
   - Topics the learner did well on
   - Topics to review (link to /explain or /lesson for weak areas)
6. Offer: "Want to try harder questions, or review a topic you missed?"

For wrong answers, be constructive: "Not quite — the answer is X. Here's why: ..."
For correct answers, reinforce: "Exactly right! [add one interesting related fact]"
