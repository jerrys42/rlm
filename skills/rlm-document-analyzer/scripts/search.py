#!/usr/bin/env python3
"""
RLM Search Script - Find relevant sections in large documents.

Usage:
    python search.py <file_path> <keywords...>
    python search.py document.txt "EUSt-Abzug" "Reparatur" "Voraussetzung"

Output:
    Structured results with section references and context.
"""

import sys
import re
from pathlib import Path


def find_sections(text: str, keywords: list[str], context_chars: int = 2000) -> list[dict]:
    """Find sections containing all or some keywords."""
    results = []

    # Build pattern for any keyword
    pattern = rf'.{{0,{context_chars}}}({"|".join(re.escape(k) for k in keywords)}).{{0,{context_chars}}}'

    matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)

    for i, match in enumerate(matches[:10]):  # Limit to 10 matches
        # Try to find Rz reference near the match
        rz_pattern = r'Rz\s*(\d+[a-z]?)'
        section_pattern = r'(\d+\.\d+(?:\.\d+)*)'

        # Search in surrounding context
        start = max(0, text.find(match) - 500)
        end = min(len(text), text.find(match) + len(match) + 500)
        context = text[start:end]

        rz_match = re.search(rz_pattern, context)
        section_match = re.search(section_pattern, context)

        results.append({
            'index': i + 1,
            'rz': rz_match.group(1) if rz_match else None,
            'section': section_match.group(1) if section_match else None,
            'matched_keyword': match if len(match) < 50 else match[:50],
            'context_preview': context[:500].replace('\n', ' ')
        })

    return results


def find_rz_section(text: str, rz_number: str, max_chars: int = 5000) -> str | None:
    """Extract complete Rz section."""
    pattern = rf'(Rz\s*{re.escape(rz_number)})\s*([\s\S]{{0,{max_chars}}}?)(?=Rz\s*\d|$)'
    match = re.search(pattern, text)
    if match:
        return f"=== {match.group(1)} ===\n{match.group(2)}"
    return None


def main():
    if len(sys.argv) < 3:
        print("Usage: python search.py <file_path> <keyword1> [keyword2] ...")
        print("       python search.py <file_path> --rz <rz_number>")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    text = file_path.read_text(encoding='utf-8', errors='ignore')
    print(f"Loaded: {len(text):,} characters from {file_path.name}")

    # Check for --rz mode
    if sys.argv[2] == '--rz' and len(sys.argv) >= 4:
        rz_number = sys.argv[3]
        result = find_rz_section(text, rz_number)
        if result:
            print(f"\n{result}")
        else:
            print(f"Rz {rz_number} not found")
        return

    # Keyword search mode
    keywords = sys.argv[2:]
    print(f"Searching for: {', '.join(keywords)}")
    print("-" * 60)

    results = find_sections(text, keywords)

    if not results:
        print("No matches found.")
        return

    print(f"Found {len(results)} relevant sections:\n")

    for r in results:
        ref = f"Rz {r['rz']}" if r['rz'] else f"Section {r['section']}" if r['section'] else "Unknown"
        print(f"[{r['index']}] {ref}")
        print(f"    Preview: {r['context_preview'][:200]}...")
        print()


if __name__ == '__main__':
    main()
