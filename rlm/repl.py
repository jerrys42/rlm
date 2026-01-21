"""
Sandboxed Python REPL environment for RLM.

Provides a safe execution environment with:
- CONTEXT variable holding the document
- llm_query() function for recursive LLM calls
- FINAL() / FINAL_VAR() for returning answers

NOTE: This uses Python's exec() intentionally for dynamic code execution
within a sandboxed environment. This is a core RLM requirement.
"""

from __future__ import annotations

import io
import re
import sys
import time
import threading
from dataclasses import dataclass, field
from typing import Callable, Any
from contextlib import redirect_stdout, redirect_stderr


@dataclass
class REPLResult:
    """Result of executing code in the REPL."""
    stdout: str
    stderr: str
    locals: dict[str, Any]
    execution_time: float
    success: bool
    error: str | None = None


# Builtins that are safe to expose
SAFE_BUILTINS = {
    # Basic functions
    'print', 'len', 'range', 'enumerate', 'zip', 'map', 'filter',
    'sorted', 'reversed', 'list', 'dict', 'set', 'tuple', 'frozenset',
    'str', 'int', 'float', 'bool', 'bytes', 'bytearray',
    'min', 'max', 'sum', 'abs', 'round', 'pow', 'divmod',
    'all', 'any', 'iter', 'next', 'slice',
    # Type checking
    'isinstance', 'issubclass', 'type', 'hasattr', 'getattr', 'setattr', 'delattr',
    'callable', 'id', 'hash', 'repr', 'ascii', 'chr', 'ord',
    # Constants
    'True', 'False', 'None',
    # Exceptions (needed for try/except)
    'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError',
    'AttributeError', 'StopIteration', 'RuntimeError', 'ZeroDivisionError',
}

# Modules that can be imported
ALLOWED_IMPORTS = {'re', 'json', 'math', 'collections', 'itertools', 'functools', 'textwrap'}


class REPLEnv:
    """
    Sandboxed Python REPL environment.

    Provides CONTEXT variable and llm_query() function for RLM execution.
    """

    def __init__(
        self,
        context: str,
        llm_query_fn: Callable[[str], str],
        max_output_chars: int = 50000,
    ):
        """
        Initialize REPL environment.

        Args:
            context: The document/text to make available as CONTEXT
            llm_query_fn: Function to call for recursive LLM queries
            max_output_chars: Maximum characters to capture from stdout
        """
        self.context = context
        self.llm_query_fn = llm_query_fn
        self.max_output_chars = max_output_chars

        self._final_answer: str | None = None
        self._lock = threading.Lock()

        # Build the execution namespace
        self._globals = self._build_globals()
        self._locals: dict[str, Any] = {}

    def _build_globals(self) -> dict[str, Any]:
        """Build the restricted globals namespace."""
        import builtins

        # Start with safe builtins
        safe_builtin_dict = {
            name: getattr(builtins, name)
            for name in SAFE_BUILTINS
            if hasattr(builtins, name)
        }

        # Add __builtins__ with restricted set
        globals_dict = {
            '__builtins__': safe_builtin_dict,
            '__name__': '__rlm_repl__',
        }

        # Add CONTEXT
        globals_dict['CONTEXT'] = self.context

        # Add llm_query function
        globals_dict['llm_query'] = self.llm_query_fn

        # Add FINAL functions
        globals_dict['FINAL'] = self._final
        globals_dict['FINAL_VAR'] = self._final_var

        # Pre-import allowed modules
        for module_name in ALLOWED_IMPORTS:
            try:
                globals_dict[module_name] = __import__(module_name)
            except ImportError:
                pass

        return globals_dict

    def _final(self, answer: str) -> str:
        """Set the final answer (called from REPL code)."""
        with self._lock:
            self._final_answer = str(answer)
        return f"[FINAL ANSWER SET: {answer[:100]}{'...' if len(str(answer)) > 100 else ''}]"

    def _final_var(self, var_name: str) -> str:
        """Set the final answer from a variable (called from REPL code)."""
        # Look up variable in locals first, then globals
        if var_name in self._locals:
            value = self._locals[var_name]
        elif var_name in self._globals:
            value = self._globals[var_name]
        else:
            return f"[ERROR: Variable '{var_name}' not found]"

        with self._lock:
            self._final_answer = str(value)
        return f"[FINAL ANSWER SET FROM {var_name}]"

    def execute(self, code: str) -> REPLResult:
        """
        Execute Python code in the sandbox.

        Args:
            code: Python code to execute

        Returns:
            REPLResult with stdout, stderr, locals, and timing info
        """
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        start_time = time.perf_counter()
        success = True
        error = None

        try:
            # Validate code doesn't try to escape sandbox
            self._validate_code(code)

            # Execute with captured output
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Use Python's built-in code execution for dynamic REPL
                # This is intentional and sandboxed via restricted globals/builtins
                compiled = compile(code, '<rlm_repl>', 'exec')
                eval(compiled, self._globals, self._locals)  # noqa: S307 - intentional sandboxed execution

        except SyntaxError as e:
            success = False
            error = f"SyntaxError: {e}"
            stderr_capture.write(error)
        except Exception as e:
            success = False
            error = f"{type(e).__name__}: {e}"
            stderr_capture.write(error)

        execution_time = time.perf_counter() - start_time

        # Get captured output
        stdout = stdout_capture.getvalue()
        stderr = stderr_capture.getvalue()

        # Truncate if too long
        if len(stdout) > self.max_output_chars:
            stdout = stdout[:self.max_output_chars] + f"\n... [truncated, total {len(stdout)} chars]"

        return REPLResult(
            stdout=stdout,
            stderr=stderr,
            locals=dict(self._locals),
            execution_time=execution_time,
            success=success,
            error=error,
        )

    def _validate_code(self, code: str) -> None:
        """Validate code doesn't attempt forbidden operations."""
        # Block obvious escape attempts
        forbidden_patterns = [
            r'\b__import__\b',
            r'\bimport\s+os\b',
            r'\bimport\s+sys\b',
            r'\bimport\s+subprocess\b',
            r'\bimport\s+shutil\b',
            r'\bopen\s*\(',
            r'\bglobals\s*\(',
            r'\blocals\s*\(',
            r'\bvars\s*\(',
            r'\bdir\s*\(',
            r'\b__class__\b',
            r'\b__bases__\b',
            r'\b__subclasses__\b',
            r'\b__mro__\b',
            r'\b__globals__\b',
            r'\b__code__\b',
        ]

        for pattern in forbidden_patterns:
            if re.search(pattern, code):
                raise SecurityError(f"Forbidden pattern detected: {pattern}")

    def get_final_answer(self) -> str | None:
        """Get the final answer if one was set."""
        with self._lock:
            return self._final_answer

    def reset_final_answer(self) -> None:
        """Reset the final answer."""
        with self._lock:
            self._final_answer = None

    def get_variable(self, name: str) -> Any:
        """Get a variable from the REPL namespace."""
        if name in self._locals:
            return self._locals[name]
        if name in self._globals:
            return self._globals[name]
        raise KeyError(f"Variable '{name}' not found")


class SecurityError(Exception):
    """Raised when code attempts forbidden operations."""
    pass
