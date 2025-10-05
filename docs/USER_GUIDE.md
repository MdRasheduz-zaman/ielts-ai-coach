# User Guide

## Overview

IELTS AI Coach helps you practice IELTS Writing tasks with instant AI feedback.

## Features

### 1. Question Bank
- Save questions for future practice
- Organize by task type
- Track all attempts per question

### 2. Task Types

**Task 1 (20 minutes)**
- Upload chart/graph/table image
- Optional question text
- 150+ word requirement

**Task 2 (40 minutes)**
- Essay question text
- 250+ word requirement

### 3. Evaluation
- Detailed band score breakdown
- Specific improvement suggestions
- Comparative feedback across attempts

## Workflow

### Starting Practice

1. **Select Question Source**
   - New Question: Create fresh question
   - From Question Bank: Load saved question

2. **Choose Task Type**
   - Module: Academic or General Training
   - Task: Task 1 or Task 2

3. **Setup Question**
   - Task 1: Upload image and/or add text
   - Task 2: Paste question text

4. **Start Practice**
   - Click "Start Timed Writing Practice"
   - Timer starts automatically

### During Practice

- Write in the text area
- Word count updates live
- Timer shows remaining time
- Submit when ready (before time's up!)

### After Submission

- Get AI evaluation
- Review band scores
- Read detailed feedback
- Save to history (optional)

### Using Question Bank

**Save Question:**
- Check "Save to question bank" before starting
- Question saved automatically

**Load Question:**
- Open sidebar
- Browse saved questions
- Click "Load" on any question

**View History:**
- Click "History" on saved question
- See all previous attempts
- Compare improvements

**Delete:**
- Delete Question: Removes question and all history
- Delete Attempt: Removes single evaluation

## Tips for Best Results

### Task 1
1. Study the visual carefully
2. Write overview first
3. Include specific numbers
4. Compare and contrast data
5. Use formal academic language

### Task 2
1. Read question thoroughly
2. Plan your answer
3. Clear introduction with thesis
4. Two-three body paragraphs
5. Conclusion summarizing view

### General Tips
- Practice regularly with timer
- Review feedback carefully
- Track progress over time
- Focus on persistent weaknesses
- Try same question multiple times

## Keyboard Shortcuts

- `Ctrl/Cmd + Enter`: Quick submit (when essay area focused)
- `Ctrl/Cmd + S`: Save (auto-saves anyway)

## Understanding Feedback

### Band Scores
- **Task Achievement/Response**: How well you answered
- **Coherence & Cohesion**: Organization and flow
- **Lexical Resource**: Vocabulary range
- **Grammatical Range**: Grammar variety and accuracy

### Improvement Tips
- Specific, actionable suggestions
- Examples of better phrasing
- Common errors highlighted
- Comparative notes (if multiple attempts)

## Data Management

### Question Bank
- Location: `data/question_bank/`
- Format: JSON files
- Portable: Can backup/restore

### Evaluation History
- Location: `data/evaluation_history/`
- Linked to questions by ID
- Chronological tracking

## Privacy & Data

- All data stored locally
- Images processed in-memory
- API calls to chosen LLM provider only
- No data sent elsewhere

## Troubleshooting

### Essay Not Saving
- Check "Save to history" is checked
- Ensure question was saved first
- Verify data folder permissions

### Image Not Loading
- Supported: PNG, JPG, JPEG, PDF
- Max size: Reasonable (auto-resized)
- Clear browser cache if issues

### Slow Evaluation
- Depends on LLM provider speed
- Try different model
- Check internet connection

## Next Steps

- Try different LLM providers
- Build question bank
- Track progress over weeks
- Focus on weak areas

Need help? See [SETUP_GUIDE.md](SETUP_GUIDE.md) or open an issue.
