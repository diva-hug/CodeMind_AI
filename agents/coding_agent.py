import os
import re

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


FILE_HEADER_PATTERN = (
    r"\*{0,2}\s*FILE:\s*([^\n*]+?)\s*\*{0,2}"
)


def extract_file_from_project(
    project_code: str,
    file_path: str,
) -> str:
    """
    Extract one file from the generated project.

    Supports:
    FILE: calculator.py
    **FILE: calculator.py**
    """

    pattern = (
        rf"\*{{0,2}}\s*FILE:\s*"
        rf"{re.escape(file_path)}"
        rf"\s*\*{{0,2}}\s*\n"
        rf"(.*?)(?=\n\s*\*{{0,2}}\s*FILE:\s*|\Z)"
    )

    match = re.search(
        pattern,
        project_code,
        re.DOTALL | re.IGNORECASE,
    )

    if match:
        return match.group(1).strip()

    return ""


def extract_failed_file(
    test_result: str,
) -> str:
    """
    Find a Python file mentioned in the test result.
    """

    match = re.search(
        r"([\w./\\-]+\.py)",
        test_result,
        re.IGNORECASE,
    )

    if match:
        return match.group(1).replace("\\", "/")

    return ""


def extract_last_file(
    project_code: str,
) -> tuple[str, str]:
    """
    Extract the last FILE section from the generated project.
    """

    matches = list(
        re.finditer(
            rf"{FILE_HEADER_PATTERN}\s*\n"
            rf"(.*?)(?=\n\s*\*{{0,2}}\s*FILE:\s*|\Z)",
            project_code,
            re.DOTALL | re.IGNORECASE,
        )
    )

    if not matches:
        return "", ""

    last_match = matches[-1]

    file_path = last_match.group(1).strip()
    file_content = last_match.group(2).strip()

    return file_path, file_content


def merge_file_into_project(
    project_code: str,
    file_path: str,
    fixed_file: str,
) -> str:
    """
    Replace one file inside the generated project.
    """

    pattern = (
        rf"\*{{0,2}}\s*FILE:\s*"
        rf"{re.escape(file_path)}"
        rf"\s*\*{{0,2}}\s*\n"
        rf".*?"
        rf"(?=\n\s*\*{{0,2}}\s*FILE:\s*|\Z)"
    )

    replacement = (
        f"FILE: {file_path}\n"
        f"{fixed_file.strip()}"
    )

    updated_project, count = re.subn(
        pattern,
        replacement,
        project_code,
        count=1,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if count == 0:

        if not project_code.endswith("\n"):
            project_code += "\n"

        project_code += (
            f"\nFILE: {file_path}\n"
            f"{fixed_file.strip()}\n"
        )

    return updated_project


def repair_known_python_issue(
    file_path: str,
    file_content: str,
    test_result: str,
) -> str:
    """
    Apply deterministic repairs for known Python compatibility issues.
    """

    combined_result = test_result.lower()

    # ---------------------------------------------------------
    # Python 3.14 compatibility:
    # ast.Num is not available in this environment.
    #
    # ast.Constant is the correct modern representation
    # for numeric literals.
    # ---------------------------------------------------------

    if (
        file_path.endswith("calculator.py")
        and (
            "ast.num" in combined_result
            or "module 'ast' has no attribute 'num'" in combined_result
        )
    ):

        fixed_content = re.sub(
            r"""
            \n?
            \s*if\s+isinstance\s*\(\s*node\s*,\s*ast\.Num\s*\)
            \s*:\s*
            \n
            \s*return\s+float\s*\(\s*node\.n\s*\)
            """,
            "",
            file_content,
            flags=re.VERBOSE,
        )

        return fixed_content.strip()

    return ""


def coding_agent(
    research_plan: str,
    previous_code: str = "",
    test_result: str = "",
) -> str:

    # =========================================================
    # FIRST GENERATION
    # =========================================================

    if not previous_code.strip():

        prompt = f"""
You are the Coding Agent in CodeMind AI.

Create a SMALL, COMPLETE and RUNNABLE Python calculator project.

Use the research plan only for useful technical guidance.
Do NOT add unnecessary complexity.

RESEARCH PLAN:
{research_plan}

PROJECT SCOPE:

Create EXACTLY these three files:

FILE: calculator.py
FILE: cli.py
FILE: gui.py

The project must:

1. Perform addition.
2. Perform subtraction.
3. Perform multiplication.
4. Perform division.
5. Perform percentage.
6. Perform power.
7. Perform square root.
8. Use Python's built-in ast module for safe expression evaluation.
9. Use ast.Constant for numeric literals.
10. Do NOT use ast.Num.
11. Never use eval().
12. Never use exec().
13. Do not use asteval.
14. Do not use external calculator libraries.
15. Handle division by zero.
16. Handle invalid expressions.
17. Handle invalid mathematical operations.
18. Provide a simple CLI.
19. Provide a simple Tkinter GUI.
20. Keep the implementation simple and practical.
21. Use complete imports.
22. Use useful type hints.
23. Use short useful docstrings.
24. Every file must be complete.
25. Do not create any other files.

The implementation must be compatible with Python 3.14.

The CLI must be able to perform at least one basic calculation
and then exit without hanging indefinitely.

IMPORTANT:

The response must contain the complete code for all three files.

Do not truncate the response.
Do not use placeholders.
Do not write "...".
Do not write "rest of code here".

Do not include README files.
Do not include pyproject.toml.
Do not include Poetry.
Do not include CI/CD.
Do not include documentation files.
Do not include test files.

OUTPUT FORMAT:

FILE: calculator.py

<complete code>

FILE: cli.py

<complete code>

FILE: gui.py

<complete code>

Return ONLY the three files.
"""

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a practical Python software engineer. "
                        "Generate concise, complete code compatible "
                        "with Python 3.14."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
            reasoning_effort="low",
            max_completion_tokens=3000,
        )

        return response.choices[0].message.content


    # =========================================================
    # RETRY / REPAIR
    # =========================================================

    failed_file = extract_failed_file(
        test_result
    )

    if failed_file:

        broken_file = extract_file_from_project(
            previous_code,
            failed_file,
        )

    else:

        failed_file, broken_file = extract_last_file(
            previous_code,
        )

    # =========================================================
    # NO IDENTIFIABLE FILE
    # =========================================================

    if not failed_file or not broken_file:
        return previous_code

    # =========================================================
    # DETERMINISTIC KNOWN-ISSUE REPAIR
    # =========================================================

    known_fix = repair_known_python_issue(
        failed_file,
        broken_file,
        test_result,
    )

    if known_fix:

        return merge_file_into_project(
            previous_code,
            failed_file,
            known_fix,
        )

    # =========================================================
    # GROQ REPAIR FOR OTHER FAILURES
    # =========================================================

    prompt = f"""
You are the Coding Agent in CodeMind AI.

The Testing Agent found a problem in ONE Python file.

Repair ONLY that file.

FAILING FILE:
{failed_file}

CURRENT FILE:
{broken_file}

TEST RESULT:
{test_result}

INSTRUCTIONS:

1. Fix the exact problem reported by the Testing Agent.
2. Return the COMPLETE corrected file.
3. Preserve existing functionality.
4. Do not modify unrelated files.
5. Keep the implementation simple.
6. Make the file syntactically valid.
7. Include all required imports.
8. The code must be compatible with Python 3.14.
9. Use ast.Constant for numeric literals.
10. Do not use ast.Num.
11. Do not use eval().
12. Do not use exec().
13. Do not use asteval.
14. Do not add external calculator libraries.
15. Do not introduce unnecessary dependencies.
16. Do not use placeholders.
17. Do not write "...".
18. Do not explain anything.

OUTPUT FORMAT:

FILE: {failed_file}

<complete corrected code>

Return ONLY the corrected file.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a practical Python debugging engineer. "
                    "Return only complete corrected code compatible "
                    "with Python 3.14."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
        reasoning_effort="low",
        max_completion_tokens=2500,
    )

    fixed_file = response.choices[0].message.content

    return merge_file_into_project(
        previous_code,
        failed_file,
        fixed_file,
    )