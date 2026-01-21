# RLM Improvement Roadmap

**Document Version:** 1.0
**Created:** 2026-01-21
**Purpose:** Iterative improvement plan for RLM (Recursive Language Model)

---

## Current State Assessment

### What Works
- ✅ Processes 2M+ character documents (919 pages)
- ✅ Cost-effective: $0.16 for full document analysis
- ✅ Iterative exploration with REPL sandbox
- ✅ Recursive sub-LLM calls with Haiku
- ✅ Detailed cost tracking by model

### What Needs Improvement
- ❌ Answer accuracy: Synthesizes instead of extracting verbatim
- ❌ No source citations (Rz numbers, page references)
- ❌ No verification step against source text
- ❌ Fixed-size chunking loses context
- ❌ No confidence scoring
- ❌ German legal text requires better prompts

---

## PRD: RLM v2.0

### Product Vision
Transform RLM from a "good enough" document analyzer into a **reliable, citable research assistant** that provides verified answers with source references.

### Target Users
1. **Tax professionals** - Need exact Rz/section citations
2. **Legal researchers** - Need verbatim quotes with page numbers
3. **Compliance officers** - Need traceable, auditable answers

### Success Metrics
| Metric | Current | Target |
|--------|---------|--------|
| Answer accuracy | ~70% | 95%+ |
| Source citation rate | 0% | 100% |
| Verification rate | 0% | 100% |
| Cost per query (2M doc) | $0.16 | <$0.25 |

---

## Improvement Phases

### Phase 1: Verification & Citation (Priority: HIGH)

**Goal:** Every answer includes source citations and is verified against original text.

#### 1.1 Source Citation System
```python
@dataclass
class Citation:
    section: str      # e.g., "Rz 1859a", "§ 12 UStG"
    page: int | None
    quote: str        # Verbatim extract (max 500 chars)
    confidence: float # 0.0-1.0
```

**Implementation:**
- Extract section markers (Rz, §, numbered sections)
- Store location mappings during chunking
- Include citations in FINAL() output format

#### 1.2 Verification Step
After finding answer, add verification iteration:
```python
verify_prompt = f"""
Verify this answer against the source:

ANSWER: {answer}

RELEVANT SOURCE TEXT:
{source_excerpt}

Is the answer accurate? Respond with:
- VERIFIED: [yes/no]
- CORRECTIONS: [any needed corrections]
- CONFIDENCE: [0-100%]
"""
```

#### 1.3 Deliverables
- [ ] `Citation` dataclass in `rlm/types.py`
- [ ] `verify_answer()` method in RLM class
- [ ] Updated prompts requiring citations
- [ ] Test: Verify EUSt question returns exact Rz 1859a content

#### 1.4 Tests
```python
def test_citation_extraction():
    """Citations must include section reference."""
    result = rlm.completion(context=ustrl, query="EUSt-Abzug Voraussetzungen")
    assert "Rz 1859a" in result.answer or "12.1.3.4.3" in result.answer
    assert result.citations is not None
    assert len(result.citations) > 0

def test_verification():
    """Answer must be verified against source."""
    result = rlm.completion(context=ustrl, query="...")
    assert result.verified == True
    assert result.confidence >= 0.8
```

---

### Phase 2: Smart Chunking (Priority: MEDIUM)

**Goal:** Preserve document structure during chunking.

#### 2.1 Semantic Chunking
Current: Fixed 100K character chunks (loses context)
Target: Section-aware chunking

```python
def semantic_chunk(text: str) -> list[Chunk]:
    """Chunk by document sections, not fixed size."""
    # Detect section patterns: ##, Rz, numbered sections
    # Keep sections together up to max_chunk_size
    # Overlap: Include previous section header
```

#### 2.2 Hierarchical Search
```
Level 1: Table of Contents scan → relevant chapters
Level 2: Chapter headers → relevant sections
Level 3: Section content → specific paragraphs
Level 4: Paragraph extraction → verbatim quotes
```

#### 2.3 Deliverables
- [ ] `semantic_chunk()` function
- [ ] `HierarchicalSearch` class
- [ ] Section index cache for repeated queries

#### 2.4 Tests
```python
def test_section_preservation():
    """Sections should not be split mid-content."""
    chunks = semantic_chunk(ustrl_text)
    for chunk in chunks:
        # Each chunk should start at a section boundary
        assert re.match(r'^(---|Rz|\d+\.)', chunk.text[:10])
```

---

### Phase 3: Language & Domain Optimization (Priority: MEDIUM)

**Goal:** Better handling of German legal/tax documents.

#### 3.1 German-Specific Prompts
```python
GERMAN_TAX_PROMPT = """
Du analysierst österreichische Steuerrichtlinien (UStR 2000).

Wichtige Begriffe:
- Rz = Randziffer (section number)
- EUSt = Einfuhrumsatzsteuer
- UStG = Umsatzsteuergesetz

Bei der Antwort:
1. Zitiere IMMER die Rz-Nummer
2. Gib den EXAKTEN Wortlaut an
3. Übersetze NICHT ins Englische
"""
```

#### 3.2 Domain Templates
- Austrian tax law (UStR, EStR, BAO)
- German tax law (UStAE, EStH)
- Legal documents (contracts, judgments)
- Technical documentation

#### 3.3 Deliverables
- [ ] `prompts/german_tax.py` with specialized prompts
- [ ] Domain detection from document content
- [ ] Auto-select appropriate prompt template

---

### Phase 4: Reliability & Robustness (Priority: HIGH)

**Goal:** Handle edge cases, never hallucinate.

#### 4.1 Hallucination Prevention
```python
def validate_answer(answer: str, context: str) -> bool:
    """Ensure answer content exists in context."""
    # Extract key claims from answer
    # Verify each claim appears in context
    # Flag unverifiable claims
```

#### 4.2 Graceful Degradation
```python
if confidence < 0.6:
    return RLMResult(
        answer="Keine eindeutige Antwort gefunden.",
        suggestions=["Versuchen Sie eine spezifischere Frage"],
        partial_findings=[...],
    )
```

#### 4.3 Deliverables
- [ ] `validate_answer()` function
- [ ] Confidence thresholds configuration
- [ ] Partial result handling
- [ ] "Not found" response with suggestions

---

### Phase 5: Performance Optimization (Priority: LOW)

**Goal:** Faster, cheaper queries.

#### 5.1 Caching
- Cache document index/TOC
- Cache section embeddings (if using)
- Cache repeated sub-queries

#### 5.2 Parallel Processing
- Chunk analysis in parallel (where independent)
- Async sub-LLM calls

#### 5.3 Model Selection
- Use Haiku for scanning/filtering
- Use Sonnet for synthesis
- Consider Opus for complex legal reasoning

---

## Implementation Schedule

### Sprint 1 (Week 1-2): Verification & Citation
- Day 1-2: Citation dataclass, extract section markers
- Day 3-4: Verification step implementation
- Day 5: Updated prompts with citation requirements
- Day 6-7: Tests and refinement

### Sprint 2 (Week 3-4): Smart Chunking
- Day 1-3: Semantic chunking implementation
- Day 4-5: Hierarchical search
- Day 6-7: Integration and testing

### Sprint 3 (Week 5-6): Language & Reliability
- Day 1-2: German prompts
- Day 3-4: Hallucination prevention
- Day 5-7: Domain templates and testing

---

## Testing Strategy

### Unit Tests
```bash
pytest tests/test_citation.py
pytest tests/test_verification.py
pytest tests/test_chunking.py
```

### Integration Tests
```bash
# Test with real USTRL document
python test_rlm_integration.py --doc sample_data/ustrl_text.txt

# Expected: Rz 1859a question returns exact 8 Voraussetzungen
```

### Acceptance Criteria
| Test Case | Expected Result |
|-----------|-----------------|
| EUSt-Abzug Reparaturen | Returns Rz 1859a with 8 exact Voraussetzungen |
| Non-existent topic | Returns "nicht gefunden" with confidence < 0.5 |
| Ambiguous query | Returns multiple relevant sections with citations |
| German response | Answer in German when document is German |

---

## Ralph Wiggum Loop Process

For iterative refinement, follow this cycle:

### 1. Run Test Query
```bash
python run_rlm.py -c sample_data/ustrl_text.txt \
  -q "EUSt-Abzug Voraussetzungen Reparaturen" --verbose
```

### 2. Evaluate Output
- [ ] Answer contains Rz 1859a reference?
- [ ] Lists all 8 Voraussetzungen?
- [ ] Verbatim quotes included?
- [ ] No hallucinated content?

### 3. Identify Gap
Example: "Answer mentions 6 prerequisites but document has 8"

### 4. Implement Fix
- Adjust prompt to require exhaustive listing
- Add verification step
- Improve chunking to capture full section

### 5. Re-test & Iterate
Repeat until all criteria pass.

---

## Quick Reference: Test Commands

```bash
# Run all tests
python test.py

# Run specific improvement test
python -m pytest tests/test_phase1.py -v

# Test with USTRL
python run_rlm.py -c sample_data/ustrl_text.txt \
  -q "welche voraussetzungen müssen erfüllt werden beim EUSt-Abzug bei kostenpflichtigen Reparaturen in fremdem Auftrag" \
  --verbose

# Expected answer must contain:
# - "Rz 1859a" or "12.1.3.4.3"
# - All 8 Voraussetzungen from the document
# - No invented/hallucinated requirements
```

---

## Files to Create/Modify

| File | Purpose | Phase |
|------|---------|-------|
| `rlm/types.py` | Citation, VerificationResult dataclasses | 1 |
| `rlm/verification.py` | Answer verification logic | 1 |
| `rlm/chunking.py` | Semantic chunking | 2 |
| `rlm/prompts/german_tax.py` | German tax document prompts | 3 |
| `tests/test_phase1.py` | Phase 1 tests | 1 |
| `tests/test_phase2.py` | Phase 2 tests | 2 |

---

## Success Definition

RLM v2.0 is complete when:

1. ✅ EUSt-Abzug query returns **exact 8 Voraussetzungen from Rz 1859a**
2. ✅ Every answer includes **section citation** (Rz/§ number)
3. ✅ Answers are **verified** against source (confidence score)
4. ✅ **No hallucinations** - all claims traceable to document
5. ✅ Cost remains **under $0.25** per 2M document query
6. ✅ Works as **Claude Code skill/subagent**
