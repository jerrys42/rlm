# RLM Session Reference

**Purpose:** Quick reference for continuing RLM development after context clear

---

## Current State (2026-01-21)

### What's Done ✅
- [x] Core RLM implementation working
- [x] Anthropic backend with token tracking
- [x] Cost breakdown by model
- [x] Test suite (6/6 passing)
- [x] Tested on 2.2M char USTRL document
- [x] API key in `.env` (gitignored)
- [x] Skill `/rlm` created in `~/.claude/commands/`
- [x] Subagent `rlm-analyzer` created
- [x] Roadmap document with PRD

### What's Pending ❌
- [ ] Phase 1: Verification & Citation system
- [ ] Phase 2: Smart/semantic chunking
- [ ] Phase 3: German language optimization
- [ ] Phase 4: Hallucination prevention

---

## Quick Start Commands

```bash
# Run tests
cd /home/jerry/projects/rlm && python3 test.py

# Test with USTRL document
python3 run_rlm.py \
  -c sample_data/ustrl_text.txt \
  -q "welche voraussetzungen müssen erfüllt werden beim EUSt-Abzug bei kostenpflichtigen Reparaturen in fremdem Auftrag" \
  --verbose

# Expected: Rz 1859a with 8 Voraussetzungen
```

---

## Key Files

| File | Purpose |
|------|---------|
| `/home/jerry/projects/rlm/CLAUDE.md` | Project instructions |
| `/home/jerry/projects/rlm/docs/RLM_ROADMAP.md` | **Full PRD & improvement plan** |
| `/home/jerry/projects/rlm/docs/RLM_PORTABLE_INSTRUCTIONS.md` | For claude.ai usage |
| `/home/jerry/projects/rlm/.env` | API key (gitignored) |
| `~/.claude/commands/rlm.md` | Slash command definition |
| `~/.claude/subagents/rlm-analyzer.md` | Subagent instructions |
| `~/.claude/subagents/rlm-lessons.md` | Lessons learned |

---

## Test Case: EUSt-Abzug

**Query:** "welche voraussetzungen müssen erfüllt werden beim EUSt-Abzug bei kostenpflichtigen Reparaturen in fremdem Auftrag"

**Expected Answer (Rz 1859a):**

1. Weiterverrechnung der Reparaturkosten unterliegt der USt
2. Nachweis über diesen Umstand wird erbracht
3. Reparaturauftrag liegt vor
4. Getrennte Aufzeichnungen über entrichtete EUSt
5. Beleg bleibt beim inländischen Unternehmer
6. Vermerk auf Beleg (Regelung + Voranmeldungszeitraum)
7. Nachweis sämtlicher Voraussetzungen durch Unternehmer
8. Erstmalige Mitteilung ans zuständige Finanzamt

**Current Result:** RLM returns ~6 generic requirements (synthesized, not extracted)
**Target:** Return exact 8 requirements with Rz 1859a citation

---

## Ralph Wiggum Iteration Loop

### Cycle Steps
1. **Run** test query with `--verbose`
2. **Evaluate** output against expected answer
3. **Identify** specific gap (missing items, wrong section, etc.)
4. **Fix** one thing (prompt, chunking, verification)
5. **Re-test** and compare
6. **Commit** if improved

### Tracking Progress
Use this checklist after each iteration:

```
[ ] Answer includes "Rz 1859a" reference
[ ] Lists exactly 8 Voraussetzungen
[ ] Quotes are verbatim from document
[ ] No hallucinated content
[ ] Cost < $0.25
```

---

## Architecture Overview

```
User Query
    ↓
┌─────────────────────────────────────┐
│           RLM Orchestrator          │
│  - Manages iteration loop           │
│  - Extracts code from LLM response  │
│  - Detects FINAL() answers          │
└─────────────────┬───────────────────┘
                  ↓
┌─────────────────────────────────────┐
│         Root LLM (Sonnet)           │
│  - Receives system prompt           │
│  - Generates Python code            │
│  - Calls llm_query() for sub-tasks  │
└─────────────────┬───────────────────┘
                  ↓
┌─────────────────────────────────────┐
│         REPL Environment            │
│  - CONTEXT variable (the document)  │
│  - llm_query() → Sub-LLM (Haiku)    │
│  - FINAL() → return answer          │
│  - Sandboxed (no file/network)      │
└─────────────────────────────────────┘
```

---

## Pricing Reference (January 2026)

| Model | Input/MTok | Output/MTok |
|-------|------------|-------------|
| claude-sonnet-4 | $3.00 | $15.00 |
| claude-sonnet-4-5 | $3.00 | $15.00 |
| claude-haiku-3 | $0.25 | $1.25 |
| claude-haiku-4-5 | $1.00 | $5.00 |
| claude-opus-4-5 | $5.00 | $25.00 |

**Cost optimization:** Use Haiku for scanning, Sonnet for reasoning

---

## Next Session Checklist

When starting a new session:

1. [ ] Read this file first
2. [ ] Read `docs/RLM_ROADMAP.md` for full PRD
3. [ ] Read `~/.claude/subagents/rlm-lessons.md` for known issues
4. [ ] Run `python3 test.py` to verify setup
5. [ ] Check which phase to work on next
6. [ ] Start Ralph Wiggum loop for that phase

---

## Contact & Resources

- **Project:** `/home/jerry/projects/rlm/`
- **Research Paper:** [arXiv:2512.24601](https://arxiv.org/abs/2512.24601)
- **Official Repo:** [github.com/alexzhang13/rlm](https://github.com/alexzhang13/rlm)
