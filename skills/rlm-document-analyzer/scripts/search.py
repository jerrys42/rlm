#!/usr/bin/env python3
"""
RLM Search Script v2 - Find ALL occurrences with accurate positions.

Usage:
    python search.py <file> <keyword1> [keyword2] ...
    python search.py <file> --count <keyword>           # Just count matches
    python search.py <file> --all <keyword>             # List all with context

Examples:
    python search.py doc.txt "Prämie" "Prämien"
    python search.py doc.txt --count "Prämie"
    python search.py doc.txt --all "Sachprämie"
"""

import sys
import re
from pathlib import Path
from collections import defaultdict


def find_all_matches(text: str, keywords: list[str], context_chars: int = 100) -> list[dict]:
    """Find ALL occurrences of keywords with position and context."""
    matches = []

    # Use re.finditer for position tracking
    pattern = '|'.join(re.escape(k) for k in keywords)

    for m in re.finditer(pattern, text, re.IGNORECASE):
        pos = m.start()
        matched_text = m.group()

        # Extract context
        ctx_start = max(0, pos - context_chars)
        ctx_end = min(len(text), pos + len(matched_text) + context_chars)
        context = text[ctx_start:ctx_end].replace('\n', ' ').strip()

        # Find nearest Rz reference (search backwards up to 2000 chars)
        search_start = max(0, pos - 2000)
        before_text = text[search_start:pos]

        rz_match = None
        for rz in re.finditer(r'Rz\s*(\d+[a-z]?)', before_text):
            rz_match = rz  # Keep last (nearest) match

        # Find section header
        section_match = None
        for sec in re.finditer(r'(\d+\.\d+(?:\.\d+)*\.?\s+[A-ZÄÖÜ][^\n]{0,60})', before_text):
            section_match = sec

        # Calculate approximate line number
        line_num = text[:pos].count('\n') + 1

        matches.append({
            'position': pos,
            'line': line_num,
            'matched': matched_text,
            'rz': rz_match.group(1) if rz_match else None,
            'section': section_match.group(1).strip()[:60] if section_match else None,
            'context': context
        })

    return matches


def group_by_rz(matches: list[dict]) -> dict:
    """Group matches by Rz number for deduplication."""
    grouped = defaultdict(list)
    for m in matches:
        key = m['rz'] or m['section'] or f"line_{m['line']}"
        grouped[key].append(m)
    return dict(grouped)


def main():
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python search.py <file> <keyword1> [keyword2] ...  # Search with grouped results")
        print("  python search.py <file> --count <keyword>          # Count all occurrences")
        print("  python search.py <file> --all <keyword>            # List ALL matches")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    text = file_path.read_text(encoding='utf-8', errors='ignore')
    print(f"Loaded: {len(text):,} characters from {file_path.name}")

    # Mode: --count
    if sys.argv[2] == '--count':
        keyword = sys.argv[3] if len(sys.argv) > 3 else ''
        if not keyword:
            print("ERROR: --count requires a keyword")
            sys.exit(1)
        count = len(re.findall(re.escape(keyword), text, re.IGNORECASE))
        print(f"\nTotal occurrences of '{keyword}': {count}")
        return

    # Mode: --all (list every match)
    if sys.argv[2] == '--all':
        keywords = sys.argv[3:]
        if not keywords:
            print("ERROR: --all requires at least one keyword")
            sys.exit(1)

        print(f"Searching for: {', '.join(keywords)}")
        matches = find_all_matches(text, keywords, context_chars=80)

        print(f"\n{'='*70}")
        print(f"FOUND {len(matches)} TOTAL MATCHES")
        print('='*70)

        for i, m in enumerate(matches, 1):
            rz_info = f"Rz {m['rz']}" if m['rz'] else ""
            sec_info = m['section'] or ""
            location = rz_info or sec_info or f"Line {m['line']}"

            print(f"\n[{i}] {location} (pos {m['position']:,})")
            print(f"    Match: \"{m['matched']}\"")
            print(f"    Context: ...{m['context']}...")
        return

    # Default mode: grouped search
    keywords = sys.argv[2:]
    print(f"Searching for: {', '.join(keywords)}")
    print("-" * 60)

    matches = find_all_matches(text, keywords)

    if not matches:
        print("\nNo matches found.")
        return

    # Group and deduplicate
    grouped = group_by_rz(matches)

    print(f"\n{'='*60}")
    print(f"TOTAL MATCHES: {len(matches)} (in {len(grouped)} unique sections)")
    print('='*60)

    # Print grouped results
    for i, (key, group) in enumerate(grouped.items(), 1):
        first = group[0]
        rz_display = f"Rz {first['rz']}" if first['rz'] else ""
        sec_display = first['section'] or ""

        header = rz_display if rz_display else sec_display if sec_display else f"Around line {first['line']}"

        print(f"\n[{i}] {header}")
        print(f"    Matches in this section: {len(group)}")
        print(f"    Keywords: {', '.join(set(m['matched'] for m in group))}")
        print(f"    Preview: ...{first['context'][:150]}...")


if __name__ == '__main__':
    main()
