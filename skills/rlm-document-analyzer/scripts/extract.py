#!/usr/bin/env python3
"""
RLM Extract Script - Extract verbatim content from document sections.

Usage:
    python extract.py <file_path> --rz <rz_number>
    python extract.py <file_path> --section <section_number>
    python extract.py <file_path> --around "<phrase>" [context_chars]

Examples:
    python extract.py doc.txt --rz 1859a
    python extract.py doc.txt --section 12.1.3.4.3
    python extract.py doc.txt --around "kostenpflichtige Reparaturen" 3000
"""

import sys
import re
from pathlib import Path


def extract_rz(text: str, rz: str, max_chars: int = 8000) -> str | None:
    """Extract complete Rz section with full content."""
    # Try to find the Rz and everything until next Rz
    pattern = rf'(Rz\s*{re.escape(rz)}[^\n]*)([\s\S]{{0,{max_chars}}}?)(?=\nRz\s*\d|\Z)'
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        header = match.group(1).strip()
        content = match.group(2).strip()
        return f"=== {header} ===\n\n{content}"

    return None


def extract_section(text: str, section: str, max_chars: int = 8000) -> str | None:
    """Extract content by section number (e.g., 12.1.3.4.3)."""
    # Escape dots for regex
    escaped = re.escape(section)
    pattern = rf'({escaped}[^\n]*)([\s\S]{{0,{max_chars}}}?)(?=\n\d+\.\d+|\nRz\s*\d|\Z)'
    match = re.search(pattern, text)

    if match:
        header = match.group(1).strip()
        content = match.group(2).strip()
        return f"=== {header} ===\n\n{content}"

    return None


def extract_around(text: str, phrase: str, context_chars: int = 3000) -> str | None:
    """Extract text around a specific phrase."""
    idx = text.lower().find(phrase.lower())
    if idx == -1:
        return None

    start = max(0, idx - context_chars)
    end = min(len(text), idx + len(phrase) + context_chars)

    # Try to find section reference in the extracted area
    extracted = text[start:end]

    # Find any Rz reference
    rz_match = re.search(r'Rz\s*(\d+[a-z]?)', extracted)
    section_match = re.search(r'(\d+\.\d+(?:\.\d+)*\.?\s+[A-Z][^\n]+)', extracted)

    header = ""
    if rz_match:
        header = f"Rz {rz_match.group(1)}"
    if section_match:
        header = f"{header} ({section_match.group(1)[:50]})" if header else section_match.group(1)[:80]

    if not header:
        header = f"Around '{phrase}'"

    return f"=== {header} ===\n\n{extracted}"


def count_list_items(text: str) -> list[str]:
    """Find numbered or bulleted list items in text."""
    items = []

    # Numbered items (1., 2., etc. or a), b), etc.)
    numbered = re.findall(r'^\s*(?:\d+\.|[a-z]\))\s*(.+)$', text, re.MULTILINE)
    items.extend(numbered)

    # Bullet points (-, •, *)
    bulleted = re.findall(r'^\s*[-•\*]\s*(.+)$', text, re.MULTILINE)
    items.extend(bulleted)

    # German "die/der/das" style lists
    die_items = re.findall(r'(?:^|\n)\s*(die|der|das)\s+([A-Z][^\n]+)', text, re.IGNORECASE)
    items.extend([f"{d[0]} {d[1]}" for d in die_items])

    return items


def main():
    if len(sys.argv) < 4:
        print("Usage:")
        print("  python extract.py <file> --rz <number>")
        print("  python extract.py <file> --section <number>")
        print("  python extract.py <file> --around <phrase> [context_chars]")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    mode = sys.argv[2]
    value = sys.argv[3]

    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    text = file_path.read_text(encoding='utf-8', errors='ignore')
    print(f"Source: {file_path.name} ({len(text):,} chars)")
    print("=" * 60)

    result = None

    if mode == '--rz':
        result = extract_rz(text, value)
    elif mode == '--section':
        result = extract_section(text, value)
    elif mode == '--around':
        context = int(sys.argv[4]) if len(sys.argv) > 4 else 3000
        result = extract_around(text, value, context)
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)

    if result:
        print(result)
        print("\n" + "=" * 60)

        # Count list items if present
        items = count_list_items(result)
        if items:
            print(f"\nFound {len(items)} list items in this section:")
            for i, item in enumerate(items[:15], 1):
                print(f"  {i}. {item[:100]}")
    else:
        print(f"Content not found for {mode} {value}")


if __name__ == '__main__':
    main()
