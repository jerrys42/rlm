#!/usr/bin/env python3
"""
RLM Extract Script v2 - Extract verbatim content from document sections.

Usage:
    python extract.py <file> --rz <number>                    # Extract Rz section
    python extract.py <file> --section <number>               # Extract by section number
    python extract.py <file> --around "<phrase>" [chars]      # Extract around phrase
    python extract.py <file> --line <number> [context]        # Extract around line number

Examples:
    python extract.py doc.txt --rz 851
    python extract.py doc.txt --section 6.1.9.3
    python extract.py doc.txt --around "Sachprämien" 2000
    python extract.py doc.txt --line 5501 500
"""

import sys
import re
from pathlib import Path


def extract_rz(text: str, rz: str, max_chars: int = 8000) -> str | None:
    """Extract complete Rz section with full content."""
    # Find Rz start
    pattern = rf'\bRz\s*{re.escape(rz)}\b'
    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return None

    start = match.start()

    # Find end: next Rz or section header or max_chars
    remaining = text[start:start + max_chars]

    # Look for next Rz marker (but not the current one)
    end_match = re.search(r'\n\s*Rz\s*\d', remaining[20:])
    if end_match:
        end = start + 20 + end_match.start()
    else:
        # Look for next major section
        section_match = re.search(r'\n\d+\.\d+\.\d+\.[^\n]+\n', remaining[20:])
        if section_match:
            end = start + 20 + section_match.start()
        else:
            end = start + max_chars

    content = text[start:end].strip()

    # Try to find section header above
    before = text[max(0, start-500):start]
    section_match = re.search(r'(\d+\.\d+(?:\.\d+)*\.?\s+[A-ZÄÖÜ][^\n]+)\n', before)
    header = section_match.group(1) if section_match else f"Rz {rz}"

    return f"=== Rz {rz} ({header}) ===\n\n{content}"


def extract_section(text: str, section: str, max_chars: int = 8000) -> str | None:
    """Extract content by section number (e.g., 6.1.9.3)."""
    escaped = re.escape(section)
    pattern = rf'{escaped}\.?\s+[A-ZÄÖÜ]'
    match = re.search(pattern, text)

    if not match:
        # Try without requiring uppercase start
        pattern = rf'\n{escaped}[^\n]*\n'
        match = re.search(pattern, text)

    if not match:
        return None

    start = match.start()

    # Find header line
    line_end = text.find('\n', start + 1)
    header = text[start:line_end].strip() if line_end > start else section

    # Find end
    remaining = text[line_end:line_end + max_chars]
    next_section = re.search(r'\n\d+\.\d+\.\d+\.?\s+[A-ZÄÖÜ]', remaining)

    if next_section:
        end = line_end + next_section.start()
    else:
        end = line_end + max_chars

    content = text[start:end].strip()
    return f"=== {header[:80]} ===\n\n{content}"


def extract_around(text: str, phrase: str, context_chars: int = 3000) -> str | None:
    """Extract text around a specific phrase."""
    idx = text.lower().find(phrase.lower())
    if idx == -1:
        return None

    start = max(0, idx - context_chars)
    end = min(len(text), idx + len(phrase) + context_chars)

    extracted = text[start:end]

    # Find Rz and section references
    rz_match = re.search(r'Rz\s*(\d+[a-z]?)', extracted)
    section_match = re.search(r'(\d+\.\d+(?:\.\d+)*\.?\s+[A-ZÄÖÜ][^\n]+)', extracted)

    header_parts = []
    if rz_match:
        header_parts.append(f"Rz {rz_match.group(1)}")
    if section_match:
        header_parts.append(section_match.group(1)[:50])

    header = " / ".join(header_parts) if header_parts else f"Around '{phrase}'"

    return f"=== {header} ===\n\n{extracted}"


def extract_by_line(text: str, line_num: int, context_lines: int = 20) -> str | None:
    """Extract content around a specific line number."""
    lines = text.split('\n')

    if line_num < 1 or line_num > len(lines):
        return None

    start_line = max(0, line_num - context_lines - 1)
    end_line = min(len(lines), line_num + context_lines)

    extracted_lines = lines[start_line:end_line]
    extracted = '\n'.join(extracted_lines)

    # Find references
    rz_match = re.search(r'Rz\s*(\d+[a-z]?)', extracted)

    header = f"Lines {start_line+1}-{end_line}"
    if rz_match:
        header += f" (near Rz {rz_match.group(1)})"

    return f"=== {header} ===\n\n{extracted}"


def count_list_items(text: str) -> list[str]:
    """Find numbered or bulleted list items in text."""
    items = []

    # Numbered items
    numbered = re.findall(r'^\s*(?:\d+\.|[a-z]\))\s*(.{10,100})', text, re.MULTILINE)
    items.extend(numbered)

    # Bullet points
    bulleted = re.findall(r'^\s*[-•\*]\s*(.{10,100})', text, re.MULTILINE)
    items.extend(bulleted)

    return items


def main():
    if len(sys.argv) < 4:
        print("Usage:")
        print("  python extract.py <file> --rz <number>")
        print("  python extract.py <file> --section <number>")
        print("  python extract.py <file> --around <phrase> [context_chars]")
        print("  python extract.py <file> --line <number> [context_lines]")
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
    elif mode == '--line':
        context = int(sys.argv[4]) if len(sys.argv) > 4 else 20
        result = extract_by_line(text, int(value), context)
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)

    if result:
        print(result)
        print("\n" + "=" * 60)

        items = count_list_items(result)
        if items:
            print(f"\nFound {len(items)} list items in this section:")
            for i, item in enumerate(items[:15], 1):
                print(f"  {i}. {item[:80]}")
    else:
        print(f"Content not found for {mode} {value}")


if __name__ == '__main__':
    main()
