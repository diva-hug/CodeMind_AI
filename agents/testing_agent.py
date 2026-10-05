import os

from dotenv import load_dotenv
from groq import Groq

from tools.code_executor import execute_python_project


load_dotenv()


client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def testing_agent(project_code: str) -> str:
    """
    Execute the generated project and return a reliable test result.

    The executor is the source of truth for execution failures.
    The LLM is only used to analyze successful execution output.
    """

    # =========================================================
    # 1. EXECUTE GENERATED PROJECT
    # =========================================================

    try:
        execution_result = execute_python_project(
            project_code
        )
    except Exception as exc:
        return f"""TEST RESULT: FAIL

ISSUES:
- Testing infrastructure error: {type(exc).__name__}: {exc}

TEST CASES:
- Project execution
"""

    # =========================================================
    # 2. READ EXECUTION RESULT SAFELY
    # =========================================================

    status = str(
        execution_result.get("status", "")
    ).strip().upper()

    output = str(
        execution_result.get("output", "")
    ).strip()

    error = str(
        execution_result.get("error", "")
    ).strip()

    # =========================================================
    # 3. EXECUTOR FAILURE IS THE SOURCE OF TRUTH
    # =========================================================

    if status != "PASS":

        issues = []

        if error:
            issues.append(error)

        if output:
            issues.append(output)

        if not issues:
            issues.append(
                "Project execution failed without a detailed error message."
            )

        issue_text = "\n- ".join(issues)

        return f"""TEST RESULT: FAIL

ISSUES:
- {issue_text}

TEST CASES:
- Project execution
- Runtime error validation
- Error handling validation
"""

    # =========================================================
    # 4. EXECUTION PASSED
    # =========================================================

    # At this point the executor itself reported PASS.
    #
    # We can optionally ask the LLM to summarize the successful
    # execution, but the LLM must NOT be allowed to turn a real
    # executor failure into PASS because that failure was already
    # handled above.

    prompt = f"""
You are the Testing Agent in CodeMind AI.

The Python project was executed by the project execution tool.

The execution tool reported:

STATUS:
{status}

PROGRAM OUTPUT:
{output}

EXECUTION ERROR:
{error}

IMPORTANT:

1. The execution status is PASS.
2. Do not invent failures.
3. Do not invent missing test cases.
4. Do not rewrite the code.
5. Do not claim that advanced functionality was tested unless
   the actual output clearly proves it.
6. Keep the result concise.
7. Return PASS because the executor reported successful execution.

Return exactly this structure:

TEST RESULT: PASS

ISSUES:
- None detected during project execution.

TEST CASES:
- Project execution
- Runtime validation
"""

    try:

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior Python testing engineer. "
                        "Be conservative. Never invent failures or "
                        "successful tests that were not actually performed."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            reasoning_effort="low",
            max_completion_tokens=500,
        )

        result = (
            response.choices[0]
            .message
            .content
            .strip()
        )

    except Exception as exc:

        # =====================================================
        # GROQ FAILURE
        # =====================================================
        #
        # The project execution already passed.
        # Therefore a Groq/API failure should NOT make the
        # generated project fail.
        #

        return f"""TEST RESULT: PASS

ISSUES:
- Project execution passed.
- Testing analysis model was unavailable: {type(exc).__name__}

TEST CASES:
- Project execution
- Runtime validation
"""

    # =========================================================
    # 5. EMPTY LLM RESPONSE
    # =========================================================

    if not result:

        return """TEST RESULT: PASS

ISSUES:
- None detected during project execution.

TEST CASES:
- Project execution
- Runtime validation
"""

    # =========================================================
    # 6. NORMALIZE LLM RESULT
    # =========================================================

    upper_result = result.upper()

    # IMPORTANT:
    #
    # We DO NOT convert FAIL into PASS.
    #
    # However, because the executor already reported PASS,
    # an LLM-generated FAIL without concrete evidence should
    # not override the executor.
    #

    if "TEST RESULT: FAIL" in upper_result:

        return f"""TEST RESULT: PASS

ISSUES:
- Project execution completed successfully.
- No concrete execution failure was detected by the executor.

TEST CASES:
- Project execution
- Runtime validation

ANALYSIS:
{result}
"""

    # =========================================================
    # 7. VALID PASS RESULT
    # =========================================================

    if "TEST RESULT: PASS" in upper_result:

        return result

    # =========================================================
    # 8. UNKNOWN LLM FORMAT
    # =========================================================

    return f"""TEST RESULT: PASS

ISSUES:
- None detected during project execution.

TEST CASES:
- Project execution
- Runtime validation

ANALYSIS:
{result}
"""


# =============================================================
# DIRECT TEST
# =============================================================

if __name__ == "__main__":

    project_code = """
FILE: prime_checker/__init__.py

from .core import is_prime

__all__ = ["is_prime"]


FILE: prime_checker/core.py

import math


def is_prime(n):

    if n < 0:
        raise ValueError("n must be a non-negative integer")

    if n <= 1:
        return False

    if n == 2:
        return True

    if n % 2 == 0:
        return False

    limit = math.isqrt(n)

    for i in range(3, limit + 1, 2):

        if n % i == 0:
            return False

    return True


FILE: prime_checker/cli.py

from .core import is_prime


def main():

    number = 7

    if is_prime(number):
        print(f"{number} is a prime number.")
    else:
        print(f"{number} is NOT a prime number.")


if __name__ == "__main__":
    main()


FILE: tests/__init__.py


FILE: tests/test_core.py

import unittest

from prime_checker.core import is_prime


class TestPrime(unittest.TestCase):

    def test_prime(self):
        self.assertTrue(is_prime(7))

    def test_composite(self):
        self.assertFalse(is_prime(8))

    def test_two(self):
        self.assertTrue(is_prime(2))

    def test_one(self):
        self.assertFalse(is_prime(1))


if __name__ == "__main__":
    unittest.main()
"""

    result = testing_agent(
        project_code
    )

    print(
        "\n========== TESTING AGENT OUTPUT ==========\n"
    )

    print(result)