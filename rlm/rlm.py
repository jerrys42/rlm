"""
Core RLM (Recursive Language Model) orchestrator.

Coordinates the iterative loop between LLM and REPL execution.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Callable, Any

from .repl import REPLEnv, REPLResult
from .backends import LLMBackend, LLMResponse
from .prompts import build_system_prompt, build_user_prompt


@dataclass
class RLMStats:
    """Statistics for an RLM completion."""
    iterations: int = 0
    root_calls: int = 0
    recursive_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    execution_time: float = 0.0


@dataclass
class RLMResult:
    """Result from an RLM completion."""
    answer: str
    stats: RLMStats
    history: list[dict] = field(default_factory=list)
    success: bool = True
    error: str | None = None


class RLM:
    """
    Recursive Language Model orchestrator.

    Coordinates the iterative process of:
    1. Sending query to root LLM
    2. Extracting and executing code blocks in REPL
    3. Feeding output back to LLM
    4. Detecting final answer
    """

    # Pattern to extract code blocks from LLM response
    CODE_BLOCK_PATTERN = re.compile(r'```(?:python)?\s*\n(.*?)```', re.DOTALL)

    def __init__(
        self,
        backend: LLMBackend,
        model: str = "claude-sonnet-4-20250514",
        recursive_model: str | None = None,
        max_iterations: int = 10,
        max_depth: int = 3,
        verbose: bool = False,
        compact_prompt: bool = False,
    ):
        """
        Initialize RLM.

        Args:
            backend: LLM backend to use
            model: Model for root LLM calls
            recursive_model: Model for recursive llm_query calls (defaults to model)
            max_iterations: Maximum iterations before giving up
            max_depth: Maximum recursion depth for llm_query
            verbose: Print debug output
            compact_prompt: Use shorter system prompt
        """
        self.backend = backend
        self.model = model
        self.recursive_model = recursive_model or model
        self.max_iterations = max_iterations
        self.max_depth = max_depth
        self.verbose = verbose
        self.compact_prompt = compact_prompt

        self._stats: RLMStats | None = None

    def _log(self, message: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"[RLM] {message}")

    def _extract_code_blocks(self, response: str) -> list[str]:
        """Extract Python code blocks from LLM response."""
        matches = self.CODE_BLOCK_PATTERN.findall(response)
        return [m.strip() for m in matches if m.strip()]

    def _create_llm_query_fn(self, depth: int = 0) -> Callable[[str], str]:
        """
        Create the llm_query function for REPL use.

        Args:
            depth: Current recursion depth

        Returns:
            Function that queries the sub-LLM
        """
        def llm_query(prompt: str) -> str:
            """Query the sub-LLM with a prompt."""
            if self._stats:
                self._stats.recursive_calls += 1

            self._log(f"llm_query called (depth={depth}): {prompt[:100]}...")

            if depth >= self.max_depth:
                self._log(f"Max depth reached, using direct LLM call")

            messages = [{"role": "user", "content": prompt}]
            response = self.backend.complete(messages, self.recursive_model)

            if self._stats:
                self._stats.total_input_tokens += response.input_tokens
                self._stats.total_output_tokens += response.output_tokens
                self._stats.total_cost += response.cost

            return response.content

        return llm_query

    def _build_context_info(self, context: str) -> str:
        """Build context information string for the user prompt."""
        size = len(context)
        lines = context.count('\n') + 1
        preview = context[:500] + "..." if len(context) > 500 else context

        return f"""- Size: {size:,} characters, {lines:,} lines
- Preview (first 500 chars):
```
{preview}
```"""

    def completion(self, context: str, query: str) -> RLMResult:
        """
        Process a query against a context using RLM.

        Args:
            context: The document/text to analyze
            query: The user's question

        Returns:
            RLMResult with answer and statistics
        """
        start_time = time.perf_counter()

        # Initialize stats
        self._stats = RLMStats()

        # Create REPL environment
        llm_query_fn = self._create_llm_query_fn(depth=0)
        repl = REPLEnv(context, llm_query_fn)

        # Build prompts
        system_prompt = build_system_prompt(compact=self.compact_prompt)
        context_info = self._build_context_info(context)
        user_prompt = build_user_prompt(query, context_info)

        # Initialize message history
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        history = []
        answer = None
        error = None

        self._log(f"Starting RLM with context size: {len(context):,} chars")
        self._log(f"Query: {query}")

        try:
            for iteration in range(self.max_iterations):
                self._stats.iterations = iteration + 1
                self._stats.root_calls += 1

                self._log(f"\n=== Iteration {iteration + 1} ===")

                # Call root LLM
                response = self.backend.complete(messages, self.model)
                self._stats.total_input_tokens += response.input_tokens
                self._stats.total_output_tokens += response.output_tokens
                self._stats.total_cost += response.cost

                llm_response = response.content
                self._log(f"LLM response ({len(llm_response)} chars)")

                # Add LLM response to history
                messages.append({"role": "assistant", "content": llm_response})
                history.append({
                    "iteration": iteration + 1,
                    "type": "llm_response",
                    "content": llm_response,
                })

                # Extract and execute code blocks
                code_blocks = self._extract_code_blocks(llm_response)
                if not code_blocks:
                    self._log("No code blocks found")
                    # If no code and no final answer, prompt for code
                    if not repl.get_final_answer():
                        messages.append({
                            "role": "user",
                            "content": "Please write Python code to analyze the CONTEXT and answer the query. Remember to call FINAL() with your answer when done.",
                        })
                    continue

                # Execute each code block
                all_output = []
                for i, code in enumerate(code_blocks):
                    self._log(f"Executing code block {i + 1}:\n{code[:200]}...")

                    result = repl.execute(code)
                    output = f"[Code Block {i + 1}]\n"

                    if result.stdout:
                        output += f"Output:\n{result.stdout}\n"
                    if result.stderr:
                        output += f"Error:\n{result.stderr}\n"
                    if not result.stdout and not result.stderr and result.success:
                        output += "(no output)\n"

                    all_output.append(output)
                    history.append({
                        "iteration": iteration + 1,
                        "type": "code_execution",
                        "code": code,
                        "result": {
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "success": result.success,
                            "error": result.error,
                        },
                    })

                    self._log(f"Execution result: success={result.success}")
                    if result.stdout:
                        self._log(f"Output: {result.stdout[:200]}...")

                # Check for final answer
                if final_answer := repl.get_final_answer():
                    answer = final_answer
                    self._log(f"Final answer found: {answer[:200]}...")
                    break

                # Add execution results to messages
                combined_output = "\n".join(all_output)
                messages.append({
                    "role": "user",
                    "content": f"Execution results:\n\n{combined_output}\n\nContinue analyzing or call FINAL() with your answer.",
                })

            # If no answer after max iterations
            if answer is None:
                error = f"No final answer after {self.max_iterations} iterations"
                self._log(error)
                # Try to extract any useful information
                answer = "Unable to determine answer within iteration limit."

        except Exception as e:
            error = f"Error during RLM execution: {type(e).__name__}: {e}"
            self._log(error)
            answer = f"Error: {e}"

        self._stats.execution_time = time.perf_counter() - start_time

        return RLMResult(
            answer=answer or "",
            stats=self._stats,
            history=history,
            success=error is None,
            error=error,
        )

    async def acompletion(self, context: str, query: str) -> RLMResult:
        """
        Async version of completion.

        Args:
            context: The document/text to analyze
            query: The user's question

        Returns:
            RLMResult with answer and statistics
        """
        start_time = time.perf_counter()

        # Initialize stats
        self._stats = RLMStats()

        # Create REPL environment (llm_query is sync for simplicity)
        llm_query_fn = self._create_llm_query_fn(depth=0)
        repl = REPLEnv(context, llm_query_fn)

        # Build prompts
        system_prompt = build_system_prompt(compact=self.compact_prompt)
        context_info = self._build_context_info(context)
        user_prompt = build_user_prompt(query, context_info)

        # Initialize message history
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        history = []
        answer = None
        error = None

        self._log(f"Starting async RLM with context size: {len(context):,} chars")

        try:
            for iteration in range(self.max_iterations):
                self._stats.iterations = iteration + 1
                self._stats.root_calls += 1

                self._log(f"\n=== Iteration {iteration + 1} ===")

                # Call root LLM (async)
                response = await self.backend.acomplete(messages, self.model)
                self._stats.total_input_tokens += response.input_tokens
                self._stats.total_output_tokens += response.output_tokens
                self._stats.total_cost += response.cost

                llm_response = response.content

                # Add LLM response to history
                messages.append({"role": "assistant", "content": llm_response})
                history.append({
                    "iteration": iteration + 1,
                    "type": "llm_response",
                    "content": llm_response,
                })

                # Extract and execute code blocks
                code_blocks = self._extract_code_blocks(llm_response)
                if not code_blocks:
                    if not repl.get_final_answer():
                        messages.append({
                            "role": "user",
                            "content": "Please write Python code to analyze the CONTEXT. Call FINAL() when done.",
                        })
                    continue

                # Execute each code block
                all_output = []
                for i, code in enumerate(code_blocks):
                    result = repl.execute(code)
                    output = f"[Code Block {i + 1}]\n"
                    if result.stdout:
                        output += f"Output:\n{result.stdout}\n"
                    if result.stderr:
                        output += f"Error:\n{result.stderr}\n"
                    if not result.stdout and not result.stderr and result.success:
                        output += "(no output)\n"
                    all_output.append(output)
                    history.append({
                        "iteration": iteration + 1,
                        "type": "code_execution",
                        "code": code,
                        "result": {
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "success": result.success,
                        },
                    })

                # Check for final answer
                if final_answer := repl.get_final_answer():
                    answer = final_answer
                    break

                # Add execution results
                combined_output = "\n".join(all_output)
                messages.append({
                    "role": "user",
                    "content": f"Execution results:\n\n{combined_output}\n\nContinue or call FINAL().",
                })

            if answer is None:
                error = f"No final answer after {self.max_iterations} iterations"
                answer = "Unable to determine answer within iteration limit."

        except Exception as e:
            error = f"Error: {type(e).__name__}: {e}"
            answer = f"Error: {e}"

        self._stats.execution_time = time.perf_counter() - start_time

        return RLMResult(
            answer=answer or "",
            stats=self._stats,
            history=history,
            success=error is None,
            error=error,
        )

    def cost_summary(self) -> dict:
        """Get a summary of costs from the last completion."""
        if not self._stats:
            return {}

        return {
            "iterations": self._stats.iterations,
            "root_calls": self._stats.root_calls,
            "recursive_calls": self._stats.recursive_calls,
            "total_input_tokens": self._stats.total_input_tokens,
            "total_output_tokens": self._stats.total_output_tokens,
            "total_cost_usd": round(self._stats.total_cost, 4),
            "execution_time_seconds": round(self._stats.execution_time, 2),
        }
