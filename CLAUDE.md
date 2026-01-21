# Claude Code Instructions for RLM Project

This file provides context for Claude Code sessions working on this project.

## 📚 Continuation Documents (Read First!)

If continuing RLM development after context clear:

| Document | Purpose |
|----------|---------|
| `docs/SESSION_REFERENCE.md` | **Quick start for new session** |
| `docs/RLM_ROADMAP.md` | Full PRD, phases, tests, deliverables |
| `docs/RLM_PORTABLE_INSTRUCTIONS.md` | Instructions for claude.ai usage |
| `~/.claude/subagents/rlm-lessons.md` | Known issues and workarounds |

**Current Focus:** Phase 1 - Verification & Citation System

---

## Quick Test Command

**To verify the implementation works, run:**
```bash
cd /home/jerry/projects/rlm && python3 test.py
```

This runs the full test suite (imports, REPL, security, backends, orchestrator, demo).

For specific tests:
```bash
python3 test.py --test repl      # REPL functionality
python3 test.py --test security  # Security restrictions
python3 test.py --test demo      # Full demo with callback
```

Expected output: `Results: 6/6 tests passed`

---

## Project Overview

**RLM (Recursive Language Model)** is a Python implementation of the MIT CSAIL research paradigm that enables LLMs to process arbitrarily long documents by treating them as external variables in a sandboxed Python REPL.

**Key Insight:** Instead of stuffing documents into the prompt, the LLM writes Python code to explore a `CONTEXT` variable, using `llm_query()` for recursive sub-processing and `FINAL()` to return answers.

## File Structure & Responsibilities

```
/home/jerry/projects/rlm/
├── rlm/
│   ├── __init__.py      # Exports: RLM, RLMResult, REPLEnv, backends
│   ├── repl.py          # REPLEnv class - sandboxed Python execution
│   ├── backends.py      # LLM backends: Anthropic, OpenAI-compatible, Callback
│   ├── prompts.py       # System prompts that teach LLM to use REPL
│   └── rlm.py           # RLM class - main orchestrator
├── demo.py              # CLI demo with Anthropic/Ollama/Callback examples
├── sample_data/         # Test documents
├── requirements.txt     # anthropic, openai (optional), httpx
└── README.md            # User documentation
```

## Key Classes & Their Roles

### `REPLEnv` (repl.py)
Sandboxed Python execution environment.

```python
repl = REPLEnv(
    context="document text...",     # Becomes CONTEXT variable
    llm_query_fn=lambda p: "...",   # Injected llm_query function
    max_output_chars=50000,         # Truncate long outputs
)
result = repl.execute("print(len(CONTEXT))")
# result.stdout, result.stderr, result.success, result.error
final = repl.get_final_answer()  # Returns str if FINAL() was called
```

**Security features:**
- Restricted builtins (no `open`, `__import__`, etc.)
- Pattern validation blocks escape attempts (`__class__`, `__globals__`, etc.)
- Pre-imported safe modules only: `re`, `json`, `math`, `collections`, `itertools`

### `RLM` (rlm.py)
Main orchestrator that coordinates LLM + REPL loop.

```python
rlm = RLM(
    backend=AnthropicBackend(),
    model="claude-sonnet-4-20250514",
    recursive_model="claude-haiku-3-20250813",  # For llm_query calls
    max_iterations=10,
    max_depth=3,
    verbose=True,
)
result = rlm.completion(context=doc, query="Question?")
# result.answer, result.stats, result.success
```

**Iteration loop:**
1. Send query + system prompt to LLM
2. Extract code blocks from response (```python ... ```)
3. Execute each block in REPL
4. If `FINAL()` called → return answer
5. Otherwise, feed output back to LLM and repeat

### Backends (backends.py)

| Class | Purpose | Init Args |
|-------|---------|-----------|
| `AnthropicBackend` | Direct Anthropic API | `api_key`, `max_tokens` |
| `OpenAICompatibleBackend` | Ollama, vLLM, local | `base_url`, `api_key` |
| `CallbackBackend` | Custom integration | `callback(messages, model) -> str` |

All backends implement:
- `complete(messages, model) -> LLMResponse`
- `acomplete(messages, model) -> LLMResponse` (async)

### Prompts (prompts.py)

- `SYSTEM_PROMPT` - Full instructions for root LLM
- `COMPACT_PROMPT` - Shorter version to save tokens
- `build_system_prompt(compact=False)` - Returns appropriate prompt
- `build_user_prompt(query, context_info)` - Builds user message

## Common Tasks

### Running Tests
```bash
# Basic import test
python3 -c "from rlm import RLM, REPLEnv; print('OK')"

# Demo with mock backend
python demo.py --backend callback --verbose

# Demo with Anthropic (needs ANTHROPIC_API_KEY)
python demo.py --verbose

# Demo with Ollama
python demo.py --backend ollama --model llama3.2 --verbose
```

### Adding a New Backend

1. Create class in `backends.py` implementing:
   ```python
   def complete(self, messages: list[dict], model: str) -> LLMResponse
   async def acomplete(self, messages: list[dict], model: str) -> LLMResponse
   ```

2. Export in `__init__.py`

3. Optionally add to `create_backend()` factory

### Modifying REPL Security

Edit `SAFE_BUILTINS` and `ALLOWED_IMPORTS` in `repl.py`:
```python
SAFE_BUILTINS = {'print', 'len', 'range', ...}
ALLOWED_IMPORTS = {'re', 'json', 'math', ...}
```

Add patterns to `_validate_code()` for additional blocking.

### Changing System Prompts

Edit `prompts.py`. The prompt teaches the LLM:
1. `CONTEXT` exists but shouldn't be printed directly
2. `llm_query(prompt)` for sub-LLM calls
3. `FINAL(answer)` or `FINAL_VAR(var)` to complete
4. Strategies: check size, regex search, chunk+process, synthesize

## Future Integration Plans

The user (Jerry) wants to create **Claude Code skills/commands** for RLM:

### Potential `/rlm` Slash Command
```yaml
---
description: Process large documents with Recursive Language Model
arguments:
  - name: query
    description: Question to answer about the document
    required: true
  - name: file
    description: Path to document file
    required: false
---
```

**Implementation ideas:**
1. Load document from file or clipboard
2. Initialize RLM with appropriate backend
3. Run completion and display results
4. Show iteration history if verbose

### Potential Skill for Document Analysis
Could wrap RLM for:
- Analyzing meeting transcripts
- Processing long PDFs
- Multi-document synthesis
- Research paper analysis

### Claude Max Integration via CallbackBackend
For using Jerry's Claude Max subscription:
```python
def claude_max_callback(messages, model):
    # Could use subprocess to call claude CLI
    # Or integrate with Claude Code's Task tool
    pass
```

## Debugging Tips

### Verbose Mode
Always use `verbose=True` during development:
```python
rlm = RLM(backend, verbose=True)
```

This shows:
- Each iteration number
- LLM response length
- Code being executed
- Execution success/failure
- Output snippets

### Common Issues

1. **"No final answer after X iterations"**
   - LLM not calling `FINAL()` - check prompt or increase `max_iterations`

2. **SecurityError in REPL**
   - Code tried forbidden operation - check `_validate_code` patterns

3. **Empty llm_query results**
   - Sub-model not responding well - try different `recursive_model`

4. **Token cost too high**
   - Use `compact_prompt=True`
   - Use cheaper `recursive_model` (Haiku)
   - Reduce `max_iterations`

## API Pricing Reference (Anthropic, as of 2025)

| Model | Input $/1M | Output $/1M |
|-------|------------|-------------|
| claude-opus-4-20250514 | $15.00 | $75.00 |
| claude-sonnet-4-20250514 | $3.00 | $15.00 |
| claude-haiku-3-20250813 | $0.25 | $1.25 |

**Recommendation:** Use Sonnet for root, Haiku for recursive calls.

## Research References

- **Paper:** [arXiv:2512.24601](https://arxiv.org/abs/2512.24601)
- **Authors:** Alex L. Zhang, Tim Kraska, Omar Khattab (MIT CSAIL)
- **Blog:** [alexzhang13.github.io/blog/2025/rlm/](https://alexzhang13.github.io/blog/2025/rlm/)
- **Official repo:** [github.com/alexzhang13/rlm](https://github.com/alexzhang13/rlm)

## Code Style

- Python 3.11+ features OK (type hints, walrus operator, etc.)
- Dataclasses for simple data containers
- Protocols for interface definitions
- f-strings for formatting
- No external dependencies beyond anthropic/openai

## Testing Checklist

Before considering changes complete:
- [ ] `python3 -c "from rlm import RLM"` works
- [ ] `python demo.py --backend callback --verbose` completes
- [ ] REPL blocks `import os` (security)
- [ ] `FINAL()` properly captured
- [ ] `llm_query()` properly tracked in stats
