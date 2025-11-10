# Vomit AI Prompt

## Setup
```bash
# Claude Code
mv AI_PROMPT.md CLAUDE.md && claude code

# Gemini CLI  
mv AI_PROMPT.md GEMINI.md && gemini code

# Qwen CLI
mv AI_PROMPT.md QWEN.md && qwen code
```

---

**Extract tasks from `_1_vomit.txt` and organize into timeframe files.**

**Files:**
- `_1_vomit.txt` → input (brain dump)
- `_2_today.md` → urgent tasks  
- `_3_week.md` → short-term goals
- `_4_month.md` → medium-term objectives
- `_5_year.md` → long-term vision

**Rules:**
1. Find actionable items only
2. Use timeframe keywords to categorize
3. Format as `[ ] action verb + specific task`
4. Append to appropriate files
5. Clear `_1_vomit.txt` after

**Timeframe keywords:**
- **Today:** today, now, immediate, asap, tonight
- **Week:** week, this week, few days, weekend, by friday  
- **Month:** month, this month, few weeks, next month
- **Year:** year, this year, long-term, eventually

**Example:**
```
Input: need to finish api endpoint today, apply to jobs this week, learn rust this month

Output:
_2_today.md: [ ] Finish API endpoint
_3_week.md: [ ] Apply to jobs  
_4_month.md: [ ] Learn Rust
```

**Command:** `Extract and organize tasks from _1_vomit.txt`