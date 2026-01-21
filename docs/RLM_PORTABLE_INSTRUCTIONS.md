# RLM - Portable Instructions for Claude.ai

**Version:** 1.0
**Purpose:** Self-contained instructions for document analysis using RLM approach

---

## What is RLM?

RLM (Recursive Language Model) is a technique for analyzing documents that are too large to fit in your context window. Instead of trying to read the entire document at once, you:

1. Treat the document as an **external variable** (CONTEXT)
2. Write **Python code** to explore it iteratively
3. Use **sub-queries** to analyze chunks
4. Return a **verified answer** with citations

---

## How to Use This (Copy-Paste to Claude.ai)

### Step 1: Upload Your Document
Upload your PDF or text file to the Claude.ai conversation.

### Step 2: Ask Claude to Analyze Using RLM Approach
Copy and paste this prompt:

```
I have uploaded a large document. Please analyze it using the RLM (Recursive Language Model) approach:

1. **Don't try to read it all at once** - that will overflow your context
2. **Explore iteratively** - check size, find structure, locate relevant sections
3. **Search strategically** - use regex patterns to find specific terms
4. **Cite sources** - always include section numbers (Rz, §, page numbers)
5. **Verify before answering** - confirm claims exist in the document

My question: [YOUR QUESTION HERE]

Please work through this step by step, showing your exploration process.
```

---

## Detailed RLM Process (For Claude to Follow)

### Phase 1: Document Discovery
```
First, I'll explore the document structure:
- Total size: [X] characters
- Number of pages/sections: [Y]
- Document type: [legal/technical/etc.]
- Language: [German/English/etc.]
- Key section markers: [Rz/§/##/numbered sections]
```

### Phase 2: Strategic Search
```
Searching for relevant content:
- Primary keywords: [from user query]
- Section patterns: [Rz \d+, § \d+, etc.]
- Found [N] potential matches

Relevant sections identified:
1. [Section reference]: [brief description]
2. [Section reference]: [brief description]
```

### Phase 3: Deep Analysis
```
Analyzing section [X] in detail:
- Full text of relevant passage: "[quote]"
- Key findings: [bullet points]
```

### Phase 4: Verification & Answer
```
## Answer

[Your answer with inline citations]

### Source Citations

| Reference | Quote | Location |
|-----------|-------|----------|
| Rz 1859a | "..." | Page 500 |

### Verification
- ✓ All claims verified against source text
- Confidence: [X]%
- Limitations: [if any]
```

---

## Example Query Formats

### For Legal/Tax Documents (German)
```
Welche Voraussetzungen müssen erfüllt werden bei [topic]?
Zitiere bitte den exakten Wortlaut und nenne die Rz-Nummer.
```

### For Technical Documentation
```
What are the specific requirements for [feature]?
Include section numbers and direct quotes.
```

### For Research Papers
```
What methodology did the authors use for [topic]?
Cite the specific sections with page numbers.
```

---

## Tips for Best Results

### DO:
- ✅ Ask specific questions ("What are the 8 requirements in section X?")
- ✅ Request citations ("Include Rz numbers")
- ✅ Ask in the document's language (German doc → German question)
- ✅ Specify format ("List all points")

### DON'T:
- ❌ Ask vague questions ("Tell me about this document")
- ❌ Expect instant answers for complex queries
- ❌ Skip verification step
- ❌ Assume correctness without checking

---

## Quick Reference: German Legal Documents

### Common Section Markers
- **Rz** = Randziffer (section number in guidelines)
- **§** = Paragraph (in laws)
- **Abs.** = Absatz (subsection)
- **Z** = Ziffer (numbered point)

### Document Types
- **UStR** = Umsatzsteuerrichtlinien (VAT guidelines)
- **EStR** = Einkommensteuerrichtlinien (Income tax guidelines)
- **UStG** = Umsatzsteuergesetz (VAT law)
- **EStG** = Einkommensteuergesetz (Income tax law)

---

## Troubleshooting

### "I can't find that information"
- Try alternative search terms
- Check if topic exists in document
- Ask for table of contents first

### "The answer seems incomplete"
- Ask "Are there additional requirements not mentioned?"
- Request "List ALL points from section X"

### "I'm not sure this is accurate"
- Ask for verbatim quote
- Request verification against source
- Compare with other sections

---

## Self-Contained RLM Prompt (Copy All)

```
You are analyzing a large document using the RLM (Recursive Language Model) approach.

RULES:
1. NEVER hallucinate - if information isn't in the document, say "nicht gefunden"
2. ALWAYS cite sources with section numbers (Rz, §, page)
3. VERIFY claims by locating them in the source text
4. ANSWER in the document's language unless asked otherwise

PROCESS:
1. Explore: Check document size, structure, language
2. Search: Find sections relevant to the query
3. Analyze: Extract key information from relevant sections
4. Cite: Include exact references and quotes
5. Verify: Confirm answer against source before responding

FORMAT YOUR ANSWER:
- Main answer with inline citations
- Source table with reference, quote, location
- Confidence level and any limitations

MY QUERY: [INSERT YOUR QUESTION]
```

---

*This document can be used standalone in any Claude conversation for document analysis.*
