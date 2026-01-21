---
name: rlm-document-analyzer
description: Analyze large documents (1M+ characters) using iterative search and extraction. Use when asked to find specific information, extract verbatim quotes, or cite sections from long legal texts, regulations, contracts, or technical documents. Provides exact citations with section references. Works by running Python scripts and analyzing their output iteratively.
---

# RLM Document Analyzer

Analyze large documents using the Recursive Language Model methodology. You have Python scripts that search and extract content - run them iteratively until you find the exact answer.

## CRITICAL RULES

1. **EXTRACT, DON'T SYNTHESIZE**: Find and extract VERBATIM text. Never paraphrase.
2. **ALWAYS CITE SOURCES**: Include section/paragraph/page references.
3. **PRESERVE LANGUAGE**: Respond in the document's language.
4. **BE EXHAUSTIVE**: Find ALL items in lists, not just some.
5. **ITERATE**: Run scripts multiple times to refine your search.
6. **EXPAND SYNONYMS**: Before searching, generate synonyms and related terms.

## Synonym Expansion (Important!)

Before running search.py, think about:
- **Synonyms**: "requirements" → "conditions", "prerequisites", "criteria"
- **Abbreviations**: "VAT" → "Value Added Tax", "USt" → "Umsatzsteuer"
- **Related terms**: "deduction" → "credit", "refund", "offset"
- **Legal variations**: "§ 12" → "Section 12", "Paragraph 12"

**Example workflow:**
```
User asks: "VAT deduction requirements"

You think: Synonyms are "VAT input tax", "Vorsteuerabzug", "input credit"

You search: python scripts/search.py doc.txt "VAT" "input tax" "deduction" "Vorsteuer"
```

This compensates for the keyword-based search by using YOUR knowledge of synonyms.

## Available Scripts

### 1. search.py - Find relevant sections

```bash
python scripts/search.py <file> <keyword1> [keyword2] ...
```

**Output:** List of matching sections with references and previews.

### 2. extract.py - Get verbatim content

```bash
# By section reference (Rz, §, etc.)
python scripts/extract.py <file> --rz <number>

# By section number
python scripts/extract.py <file> --section <number>

# Around a phrase
python scripts/extract.py <file> --around "<phrase>" [context_chars]
```

**Output:** Complete section content with list item count.

## Workflow

### Step 1: Search for keywords

```bash
python scripts/search.py document.txt "keyword1" "keyword2"
```

Read the output. Note which section references appear relevant.

### Step 2: Extract specific section

```bash
python scripts/extract.py document.txt --rz 1859a
```

Read the output. Check if it contains the answer.

### Step 3: Refine if needed

If the section doesn't have the full answer:
- Try a different section from search results
- Search with different keywords
- Extract with more context:
  ```bash
  python scripts/extract.py document.txt --around "specific phrase" 5000
  ```

### Step 4: Verify and respond

Once you have the content:
1. Count list items (script shows count)
2. Verify ALL items are present
3. Quote VERBATIM in your response
4. Include the section reference

## Example Session

**User asks about requirements in a document**

**You run:**
```bash
python scripts/search.py doc.txt "requirement" "condition"
```

**Output shows relevant sections**

**You run:**
```bash
python scripts/extract.py doc.txt --rz 1859a
```

**Output shows full section with 8 items**

**Your response:**
```
According to Section 1859a:

[Complete verbatim quote]

The 8 requirements are:
1. [verbatim]
2. [verbatim]
...

Source: [Document], Section 1859a
```

## When to Use

- Document is large (100k+ characters)
- User needs exact quotes with citations
- Questions asking for requirements, conditions, definitions
- Legal, regulatory, or technical documents

## Iteration Tips

- **Not finding results?** Try broader keywords, then narrow down
- **Partial list?** The extract script counts items - verify you have all
- **Wrong section?** Go back to search, try another reference
- **Need more context?** Use `--around` with larger context value

Run scripts as many times as needed until you have the exact, complete, verbatim answer with proper citation.
