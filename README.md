# vomit

raw thoughts → clean todos

minimal framework for turning brain dumps into actionable todos across timeframes

## how it works

1. brain dump everything into `_1_vomit.txt`
2. use AI prompt to extract and organize tasks
3. AI writes clean todos to timeframe files
4. check `_2_today.md` for immediate actions

## quick start

```bash
# setup AI (choose your tool)
mv PROMPT.md CLAUDE.md  # for Claude Code
# or copy prompt to your AI of choice

# brain dump your chaos
echo "finish api today, apply to jobs this week, learn rust this month" > _1_vomit.txt

# let AI organize it
claude code  # or gemini/qwen/whatever

# check your organized tasks
cat _2_today.md
```

## file structure

- `_1_vomit.txt` - brain dump everything here
- `_2_today.md` - urgent tasks (AI populated)
- `_3_week.md` - short-term goals (AI populated)  
- `_4_month.md` - medium objectives (AI populated)
- `_5_year.md` - long-term vision (AI populated)

## the prompt

Universal AI prompt in `PROMPT.md` works with any AI CLI tool. Copy to your preferred AI's config file and run.

built for developers who are tired of productivity app bloat.