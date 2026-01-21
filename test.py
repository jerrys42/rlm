#!/usr/bin/env python3
"""
RLM Test Suite

Run all tests:
    python test.py

Run specific test:
    python test.py --test repl
    python test.py --test security
    python test.py --test demo
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from rlm import RLM, RLMResult, RLMStats
        from rlm import REPLEnv, REPLResult, SecurityError
        from rlm import AnthropicBackend, OpenAICompatibleBackend, CallbackBackend
        from rlm import create_backend
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_repl_basic():
    """Test basic REPL functionality."""
    print("Testing REPL basic operations...")
    from rlm import REPLEnv

    def mock_llm(prompt):
        return f"Mock response to: {prompt[:30]}..."

    context = "Python is a programming language. It is widely used for AI."
    repl = REPLEnv(context, mock_llm)

    # Test 1: Context access
    result = repl.execute("print(len(CONTEXT))")
    assert result.success, f"Context access failed: {result.error}"
    assert result.stdout.strip().isdigit(), f"Should print a number: {result.stdout}"
    assert int(result.stdout.strip()) == len(context), f"Wrong context length: {result.stdout}"
    print("  ✓ Context access works")

    # Test 2: Regex search
    result = repl.execute("matches = re.findall(r'Python|AI', CONTEXT); print(len(matches))")
    assert result.success, f"Regex failed: {result.error}"
    assert "2" in result.stdout, f"Wrong match count: {result.stdout}"
    print("  ✓ Regex search works")

    # Test 3: llm_query function
    result = repl.execute("response = llm_query('test prompt'); print(response[:20])")
    assert result.success, f"llm_query failed: {result.error}"
    assert "Mock response" in result.stdout, f"Wrong llm_query response: {result.stdout}"
    print("  ✓ llm_query works")

    # Test 4: FINAL answer
    result = repl.execute('FINAL("Test answer complete")')
    assert result.success, f"FINAL failed: {result.error}"
    assert repl.get_final_answer() == "Test answer complete", "FINAL answer not captured"
    print("  ✓ FINAL() works")

    # Test 5: FINAL_VAR
    repl.reset_final_answer()
    result = repl.execute('my_var = "Variable answer"; FINAL_VAR("my_var")')
    assert result.success, f"FINAL_VAR failed: {result.error}"
    assert repl.get_final_answer() == "Variable answer", "FINAL_VAR not captured"
    print("  ✓ FINAL_VAR() works")

    return True


def test_repl_security():
    """Test REPL security restrictions."""
    print("Testing REPL security...")
    from rlm import REPLEnv, SecurityError

    repl = REPLEnv("test", lambda p: "mock")

    # Test blocked patterns
    blocked_codes = [
        ("import os", "import os"),
        ("import subprocess", "import subprocess"),
        ("open('file.txt')", "open()"),
        ("__import__('os')", "__import__"),
        ("x.__class__.__bases__", "__class__"),
    ]

    for code, description in blocked_codes:
        result = repl.execute(code)
        assert not result.success, f"Should have blocked: {description}"
        assert "SecurityError" in result.stderr or "Forbidden" in result.stderr, \
            f"Wrong error for {description}: {result.stderr}"
        print(f"  ✓ Blocks {description}")

    return True


def test_backends():
    """Test backend instantiation (without actual API calls)."""
    print("Testing backends...")
    from rlm.backends import CallbackBackend, LLMResponse

    # Test CallbackBackend
    def simple_callback(messages, model):
        return f"Response from {model}"

    backend = CallbackBackend(simple_callback)
    response = backend.complete([{"role": "user", "content": "test"}], "test-model")

    assert isinstance(response, LLMResponse), "Wrong response type"
    assert response.content == "Response from test-model", f"Wrong content: {response.content}"
    assert response.model == "test-model", f"Wrong model: {response.model}"
    print("  ✓ CallbackBackend works")

    return True


def test_rlm_orchestrator():
    """Test RLM orchestrator with mock backend."""
    print("Testing RLM orchestrator...")
    from rlm import RLM
    from rlm.backends import CallbackBackend

    # State tracker
    state = {"turn": 0}

    def mock_llm(messages, model):
        # Check if sub-call (no system message)
        has_system = any(m.get("role") == "system" for m in messages)
        if not has_system:
            return "Sub-LLM response"

        state["turn"] += 1
        if state["turn"] == 1:
            return '```python\nprint(f"Size: {len(CONTEXT)}")\n```'
        elif state["turn"] == 2:
            return '```python\nFINAL("Test complete")\n```'
        return '```python\nFINAL("Fallback")\n```'

    backend = CallbackBackend(mock_llm)
    rlm = RLM(backend, model="mock", verbose=False, max_iterations=5)

    result = rlm.completion(context="Test document content", query="Test query")

    assert result.success, f"RLM failed: {result.error}"
    assert result.answer == "Test complete", f"Wrong answer: {result.answer}"
    assert result.stats.iterations == 2, f"Wrong iterations: {result.stats.iterations}"
    print("  ✓ RLM orchestrator works")

    # Test cost summary
    summary = rlm.cost_summary()
    assert "iterations" in summary, "Missing iterations in summary"
    assert "root_calls" in summary, "Missing root_calls in summary"
    print("  ✓ Cost summary works")

    return True


def test_demo_callback():
    """Test the demo script with callback backend."""
    print("Testing demo with callback backend...")
    import subprocess

    result = subprocess.run(
        ["python3", "demo.py", "--backend", "callback"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent,
        timeout=30,
    )

    assert result.returncode == 0, f"Demo failed: {result.stderr}"
    assert "Success: True" in result.stdout, f"Demo didn't succeed: {result.stdout}"
    assert "Authentication Methods Found" in result.stdout, f"Missing expected output"
    print("  ✓ Demo callback works")

    return True


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("RLM Test Suite")
    print("=" * 60)
    print()

    tests = [
        ("Imports", test_imports),
        ("REPL Basic", test_repl_basic),
        ("REPL Security", test_repl_security),
        ("Backends", test_backends),
        ("RLM Orchestrator", test_rlm_orchestrator),
        ("Demo Callback", test_demo_callback),
    ]

    results = []
    for name, test_fn in tests:
        try:
            success = test_fn()
            results.append((name, success, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"  ✗ FAILED: {e}")
        print()

    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, s, _ in results if s)
    total = len(results)

    for name, success, error in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {name}")
        if error:
            print(f"         Error: {error}")

    print()
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


def main():
    import argparse

    parser = argparse.ArgumentParser(description="RLM Test Suite")
    parser.add_argument(
        "--test",
        choices=["imports", "repl", "security", "backends", "orchestrator", "demo", "all"],
        default="all",
        help="Which test to run",
    )
    args = parser.parse_args()

    test_map = {
        "imports": test_imports,
        "repl": test_repl_basic,
        "security": test_repl_security,
        "backends": test_backends,
        "orchestrator": test_rlm_orchestrator,
        "demo": test_demo_callback,
    }

    if args.test == "all":
        success = run_all_tests()
    else:
        print(f"Running test: {args.test}")
        try:
            success = test_map[args.test]()
            print(f"\n{'✓ PASS' if success else '✗ FAIL'}")
        except Exception as e:
            print(f"\n✗ FAIL: {e}")
            success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
