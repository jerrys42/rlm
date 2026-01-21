#!/usr/bin/env python3
"""
RLM Runner with Cost Breakdown

Usage:
    python run_rlm.py --context-file sample_data/ustrl_text.txt --query "Your question"
    python run_rlm.py --context-file sample_data/ustrl_text.txt --query "..." --verbose
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent / ".env")

from rlm import RLM
from rlm.backends import AnthropicBackend


def main():
    parser = argparse.ArgumentParser(description="RLM Runner with Cost Breakdown")
    parser.add_argument("--context-file", "-c", required=True, help="Path to context file")
    parser.add_argument("--query", "-q", required=True, help="Question to ask")
    parser.add_argument("--model", "-m", default="claude-sonnet-4-20250514", help="Root model")
    parser.add_argument("--recursive-model", "-r", default="claude-3-haiku-20240307", help="Model for llm_query")
    parser.add_argument("--max-iterations", type=int, default=10, help="Max iterations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--compact", action="store_true", help="Use compact prompt")

    args = parser.parse_args()

    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        print("Set it in .env file or environment")
        sys.exit(1)

    # Load context
    context_path = Path(args.context_file)
    if not context_path.exists():
        print(f"ERROR: Context file not found: {context_path}")
        sys.exit(1)

    context = context_path.read_text(encoding="utf-8")
    print(f"Loaded context: {len(context):,} characters from {context_path}")

    # Initialize backend and RLM
    backend = AnthropicBackend(api_key=api_key, max_tokens=4096)

    rlm = RLM(
        backend=backend,
        model=args.model,
        recursive_model=args.recursive_model,
        max_iterations=args.max_iterations,
        verbose=args.verbose,
        compact_prompt=args.compact,
    )

    print(f"\nRoot model: {args.model}")
    print(f"Recursive model: {args.recursive_model}")
    print(f"Query: {args.query}")
    print("\n" + "=" * 60)
    print("Processing...")
    print("=" * 60 + "\n")

    # Run completion
    result = rlm.completion(context=context, query=args.query)

    # Display results
    print("\n" + "=" * 60)
    print("ANSWER")
    print("=" * 60)
    print(result.answer)

    print("\n" + "=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)
    print(f"Success: {result.success}")
    if result.error:
        print(f"Error: {result.error}")
    print(f"Iterations: {result.stats.iterations}")
    print(f"Execution time: {result.stats.execution_time:.2f}s")

    # Print detailed cost breakdown
    print()
    rlm.print_cost_breakdown()


if __name__ == "__main__":
    main()
