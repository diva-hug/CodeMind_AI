import os
import subprocess
import sys
import tempfile


from tools.project_parser import parse_project


EXECUTION_TIMEOUT = 10
TEST_TIMEOUT = 15


def _normalize_path(path: str) -> str:
    """Normalize a project path to forward-slash format."""
    return path.replace("\\", "/")


def _is_safe_relative_path(path: str) -> bool:
    """Check that a generated file cannot escape the temporary project."""
    normalized = os.path.normpath(path)

    if os.path.isabs(normalized):
        return False

    if normalized == "..":
        return False

    if normalized.startswith(".." + os.sep):
        return False

    return True


def _run_python_file(
    file_path: str,
    project_dir: str,
):
    """Run one Python file inside the generated project."""

    return subprocess.run(
        [
            sys.executable,
            file_path,
        ],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=EXECUTION_TIMEOUT,
    )


def _find_entry_point(project_files: dict):
    """
    Find a practical executable entry point.

    Priority:
    1. package/__main__.py
    2. root main.py
    3. root cli.py
    4. package/cli.py
    """

    normalized_files = {
        _normalize_path(path)
        for path in project_files
    }

    # =========================================================
    # 1. package/__main__.py
    # =========================================================

    for file_path in normalized_files:

        parts = file_path.split("/")

        if (
            len(parts) >= 2
            and parts[-1] == "__main__.py"
        ):

            package_name = parts[-2]

            return {
                "command": [
                    sys.executable,
                    "-m",
                    package_name,
                ],
                "interactive": True,
                "entry_point": file_path,
            }

    # =========================================================
    # 2. root main.py
    # =========================================================

    if "main.py" in normalized_files:

        return {
            "command": [
                sys.executable,
                "main.py",
            ],
            "interactive": False,
            "entry_point": "main.py",
        }

    # =========================================================
    # 3. root cli.py
    # =========================================================

    if "cli.py" in normalized_files:

        return {
            "command": [
                sys.executable,
                "cli.py",
            ],
            "interactive": True,
            "entry_point": "cli.py",
        }

    # =========================================================
    # 4. package/cli.py
    # =========================================================

    for file_path in normalized_files:

        parts = file_path.split("/")

        if (
            len(parts) >= 2
            and parts[-1] == "cli.py"
        ):

            package_parts = parts[:-1]

            package_path = "/".join(
                package_parts
            )

            init_file = (
                f"{package_path}/__init__.py"
            )

            if init_file in normalized_files:

                module_name = ".".join(
                    package_parts + ["cli"]
                )

                return {
                    "command": [
                        sys.executable,
                        "-m",
                        module_name,
                    ],
                    "interactive": True,
                    "entry_point": file_path,
                }

    return None


def _run_unittest_tests(
    project_dir: str,
):
    """Run unittest discovery if a tests directory exists."""

    tests_directory = os.path.join(
        project_dir,
        "tests",
    )

    if not os.path.isdir(tests_directory):
        return None

    return subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-t",
            ".",
        ],
        cwd=project_dir,
        capture_output=True,
        text=True,
        timeout=TEST_TIMEOUT,
    )


def execute_python_project(generated_text: str):
    """
    Create, validate, execute, and test a generated Python project.

    The generated project must use FILE sections.
    """

    # =========================================================
    # 1. PARSE GENERATED PROJECT
    # =========================================================

    try:

        project_files = parse_project(
            generated_text
        )

    except Exception as exc:

        return {
            "status": "FAIL",
            "output": "",
            "error": (
                "Project parsing failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        }

    if not project_files:

        return {
            "status": "FAIL",
            "output": "",
            "error": "No project files found.",
        }

    # =========================================================
    # 2. CREATE TEMPORARY PROJECT
    # =========================================================

    try:

        with tempfile.TemporaryDirectory() as project_dir:

            # =====================================================
            # 2A. WRITE FILES
            # =====================================================

            for file_path, content in project_files.items():

                if not _is_safe_relative_path(
                    file_path
                ):

                    return {
                        "status": "FAIL",
                        "output": "",
                        "error": (
                            f"Unsafe file path: {file_path}"
                        ),
                    }

                safe_path = os.path.normpath(
                    file_path
                )

                full_path = os.path.join(
                    project_dir,
                    safe_path,
                )

                parent_directory = os.path.dirname(
                    full_path
                )

                if parent_directory:

                    os.makedirs(
                        parent_directory,
                        exist_ok=True,
                    )

                with open(
                    full_path,
                    "w",
                    encoding="utf-8",
                ) as file:

                    file.write(content)

            # =====================================================
            # 3. PYTHON SYNTAX VALIDATION
            # =====================================================

            for file_path in project_files:

                normalized = _normalize_path(
                    file_path
                )

                if not normalized.endswith(".py"):
                    continue

                syntax_result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "py_compile",
                        normalized,
                    ],
                    cwd=project_dir,
                    capture_output=True,
                    text=True,
                    timeout=EXECUTION_TIMEOUT,
                )

                if syntax_result.returncode != 0:

                    syntax_output = (
                        syntax_result.stdout
                        + syntax_result.stderr
                    ).strip()

                    return {
                        "status": "FAIL",
                        "output": syntax_output,
                        "error": (
                            "Python syntax validation failed "
                            f"for {normalized}."
                        ),
                    }

            # =====================================================
            # 4. FIND ENTRY POINT
            # =====================================================

            entry_point = _find_entry_point(
                project_files
            )

            if entry_point is None:

                return {
                    "status": "FAIL",
                    "output": "",
                    "error": (
                        "No runnable Python entry point found. "
                        "Expected one of: "
                        "package/__main__.py, main.py, "
                        "cli.py, or package/cli.py."
                    ),
                }

            command = entry_point["command"]
            interactive = entry_point["interactive"]
            entry_file = entry_point["entry_point"]

            # =====================================================
            # 5. PREPARE CLI INPUT
            # =====================================================

            input_data = None

            if interactive:

                # A simple smoke-test input.
                #
                # The generated CodeMind calculator CLI is
                # expected to accept an expression and then exit.
                #
                # If the CLI does not need input, the extra input
                # is harmless for most normal CLI programs.

                input_data = (
                    "2 + 3\n"
                    "/exit\n"
                )

            # =====================================================
            # 6. EXECUTE APPLICATION
            # =====================================================

            try:

                result = subprocess.run(
                    command,
                    cwd=project_dir,
                    input=input_data,
                    capture_output=True,
                    text=True,
                    timeout=EXECUTION_TIMEOUT,
                )

            except subprocess.TimeoutExpired:

                return {
                    "status": "FAIL",
                    "output": "",
                    "error": (
                        "Project execution timed out after "
                        f"{EXECUTION_TIMEOUT} seconds. "
                        f"Entry point: {entry_file}"
                    ),
                }

            project_output = (
                result.stdout
                + result.stderr
            ).strip()

            # =====================================================
            # 7. APPLICATION EXECUTION FAILURE
            # =====================================================

            if result.returncode != 0:

                return {
                    "status": "FAIL",
                    "output": project_output,
                    "error": (
                        "Project execution failed "
                        f"with exit code {result.returncode}. "
                        f"Entry point: {entry_file}"
                    ),
                }

            # =====================================================
            # 8. RUN AUTOMATED UNIT TESTS
            # =====================================================

            test_result = _run_unittest_tests(
                project_dir
            )

            test_output = ""

            if test_result is not None:

                test_output = (
                    test_result.stdout
                    + test_result.stderr
                ).strip()

                # =================================================
                # UNIT TEST FAILURE
                # =================================================

                if test_result.returncode != 0:

                    return {
                        "status": "FAIL",
                        "output": (
                            project_output
                            + "\n\n"
                            + test_output
                        ).strip(),
                        "error": (
                            "Automated unit tests failed.\n"
                            "The Testing Agent should use the "
                            "traceback below to identify the "
                            "actual implementation problem."
                        ),
                    }

            # =====================================================
            # 9. BUILD FINAL OUTPUT
            # =====================================================

            output_parts = []

            if project_output:
                output_parts.append(
                    "APPLICATION OUTPUT:\n"
                    + project_output
                )

            if test_output:
                output_parts.append(
                    "UNIT TEST OUTPUT:\n"
                    + test_output
                )

            combined_output = (
                "\n\n".join(output_parts)
            ).strip()

            # =====================================================
            # 10. SUCCESS
            # =====================================================

            return {
                "status": "PASS",
                "output": combined_output,
                "error": "",
            }

    # =============================================================
    # TIMEOUT / PROCESS ERRORS
    # =============================================================

    except subprocess.TimeoutExpired:

        return {
            "status": "FAIL",
            "output": "",
            "error": (
                "Project execution timed out."
            ),
        }

    except Exception as exc:

        return {
            "status": "FAIL",
            "output": "",
            "error": (
                f"{type(exc).__name__}: {exc}"
            ),
        }


# =================================================================
# STANDALONE TEST
# =================================================================

if __name__ == "__main__":

    test_project = """
FILE: prime_checker/__init__.py

from .core import is_prime


FILE: prime_checker/core.py

def is_prime(n):

    if n < 2:
        return False

    if n == 2:
        return True

    if n % 2 == 0:
        return False

    divisor = 3

    while divisor * divisor <= n:

        if n % divisor == 0:
            return False

        divisor += 2

    return True


FILE: prime_checker/cli.py

from .core import is_prime


def main():

    number = 7

    if is_prime(number):
        print(f"{number} is prime")
    else:
        print(f"{number} is not prime")


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

    result = execute_python_project(
        test_project
    )

    print(
        "\n=============================="
    )

    print(
        "CODE EXECUTOR RESULT"
    )

    print(
        "=============================="
    )

    print("\nSTATUS:")
    print(result["status"])

    print("\nOUTPUT:")
    print(result["output"])

    print("\nERROR:")
    print(result["error"])