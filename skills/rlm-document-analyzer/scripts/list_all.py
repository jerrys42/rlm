#!/usr/bin/env python3
"""
RLM List All Script - Find and list EVERY occurrence of a term with full context.

Specifically designed for tasks like "find all mentions of X in the document".

Usage:
    python list_all.py <file> <term> [--context CHARS] [--format table|full|compact]

Examples:
    python list_all.py doc.txt "Prämie"
    python list_all.py doc.txt "Prämie" --context 120
    python list_all.py doc.txt "Prämie" --format table
    python list_all.py doc.txt "Prämie" "Prämien" --format full
"""

import sys
import re
from pathlib import Path
import argparse


def find_all_occurrences(text: str, terms: list[str], context_chars: int = 100) -> list[dict]:
    """Find every single occurrence of terms with context and references."""
    results = []
    lines = text.split('\n')

    # Build cumulative position index for line lookup
    line_positions = [0]
    for line in lines:
        line_positions.append(line_positions[-1] + len(line) + 1)

    def pos_to_line(pos: int) -> int:
        for i, lp in enumerate(line_positions):
            if lp > pos:
                return i
        return len(lines)

    # Search for each term
    pattern = '|'.join(re.escape(t) for t in terms)

    for match in re.finditer(pattern, text, re.IGNORECASE):
        pos = match.start()
        matched = match.group()
        line_num = pos_to_line(pos)

        # Get context
        ctx_start = max(0, pos - context_chars)
        ctx_end = min(len(text), pos + len(matched) + context_chars)
        context = text[ctx_start:ctx_end].replace('\n', ' ').replace('  ', ' ').strip()

        # Find nearest Rz (search backwards)
        search_start = max(0, pos - 3000)
        before = text[search_start:pos]

        rz = None
        for m in re.finditer(r'Rz\s*(\d+[a-z]?)', before):
            rz = m.group(1)

        # Find section header
        section = None
        for m in re.finditer(r'(\d+\.\d+(?:\.\d+)*\.?)\s+([A-ZÄÖÜ][^\n]{0,50})', before):
            section = f"{m.group(1)} {m.group(2)}"

        results.append({
            'num': len(results) + 1,
            'term': matched,
            'line': line_num,
            'pos': pos,
            'rz': rz,
            'section': section[:60] if section else None,
            'context': context
        })

    return results


def format_table(results: list[dict]) -> str:
    """Format results as a compact table."""
    output = []
    output.append(f"{'#':<4} {'Term':<15} {'Rz':<8} {'Line':<8} Context")
    output.append("-" * 100)

    for r in results:
        rz = r['rz'] or '-'
        ctx = r['context'][:60] + '...' if len(r['context']) > 60 else r['context']
        output.append(f"{r['num']:<4} {r['term']:<15} {rz:<8} {r['line']:<8} {ctx}")

    return '\n'.join(output)


def format_full(results: list[dict]) -> str:
    """Format results with full context."""
    output = []

    for r in results:
        output.append(f"\n[{r['num']}] {r['term']}")
        output.append(f"    Location: Rz {r['rz']}" if r['rz'] else f"    Location: Line {r['line']}")
        if r['section']:
            output.append(f"    Section: {r['section']}")
        output.append(f"    Context: ...{r['context']}...")

    return '\n'.join(output)


def format_compact(results: list[dict]) -> str:
    """Format results as a minimal list."""
    output = []

    for r in results:
        loc = f"Rz {r['rz']}" if r['rz'] else f"Line {r['line']}"
        output.append(f"{r['num']}. [{loc}] \"{r['term']}\" - {r['context'][:80]}...")

    return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(description='List all occurrences of terms in a document')
    parser.add_argument('file', help='Path to the document')
    parser.add_argument('terms', nargs='+', help='Terms to search for')
    parser.add_argument('--context', type=int, default=100, help='Characters of context (default: 100)')
    parser.add_argument('--format', choices=['table', 'full', 'compact'], default='full',
                        help='Output format (default: full)')

    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    text = file_path.read_text(encoding='utf-8', errors='ignore')
    print(f"Document: {file_path.name} ({len(text):,} characters)")
    print(f"Searching for: {', '.join(args.terms)}")
    print("=" * 70)

    results = find_all_occurrences(text, args.terms, args.context)

    if not results:
        print("\nNo occurrences found.")
        return

    # Summary
    print(f"\nFOUND {len(results)} TOTAL OCCURRENCES")

    # Term breakdown
    term_counts = {}
    for r in results:
        term_counts[r['term']] = term_counts.get(r['term'], 0) + 1

    if len(term_counts) > 1:
        print("\nBreakdown by term:")
        for term, count in sorted(term_counts.items(), key=lambda x: -x[1]):
            print(f"  - {term}: {count}")

    # Unique Rz sections
    rz_set = set(r['rz'] for r in results if r['rz'])
    if rz_set:
        print(f"\nFound in {len(rz_set)} unique Rz sections: {', '.join(sorted(rz_set, key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0))}")

    print("\n" + "=" * 70)
    print("DETAILED RESULTS:")
    print("=" * 70)

    # Format output
    if args.format == 'table':
        print(format_table(results))
    elif args.format == 'full':
        print(format_full(results))
    else:
        print(format_compact(results))


if __name__ == '__main__':
    main()
