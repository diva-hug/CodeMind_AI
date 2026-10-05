import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def reviewer_agent(code, test_result):
    """
    Perform a final software code review.
    """

    prompt = f"""
You are the Reviewer Agent in CodeMind AI.

Perform a concise final review of the generated Python project.

TEST RESULT:
{test_result}

PROJECT CODE:
{code}

Review only these areas:

1. Correctness
2. Code quality
3. Readability
4. Error handling
5. Security
6. Unnecessary complexity

IMPORTANT:

- The Testing Agent result is authoritative for execution.
- If TEST RESULT is PASS and there is no serious issue, use APPROVED.
- Do not invent problems.
- Do not report minor stylistic preferences as serious issues.
- Do not claim a bug without evidence in the code.
- Do not rewrite the code.
- Keep the review concise.

Return ONLY:

REVIEW STATUS: APPROVED or CHANGES REQUIRED

STRENGTHS:
- strength 1
- strength 2

ISSUES:
- issue 1

RECOMMENDATIONS:
- recommendation 1
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior Python software "
                    "code reviewer. Be accurate and concise."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        reasoning_effort="low",
        max_completion_tokens=600,
    )

    result = response.choices[0].message.content

    if not result or not result.strip():

        return """REVIEW STATUS: CHANGES REQUIRED

STRENGTHS:
- No review result was generated.

ISSUES:
- Reviewer Agent returned an empty response.

RECOMMENDATIONS:
- Run the review again.
"""

    return result


if __name__ == "__main__":

    code = """
def add(a, b):
    return a + b


def divide(a, b):

    if b == 0:
        raise ValueError(
            "Cannot divide by zero"
        )

    return a / b
"""

    test_result = """
TEST RESULT: PASS

TEST CASES:
- add(2, 3) -> 5
- add(-2, 2) -> 0
- divide(10, 2) -> 5
- divide(10, 0) -> handled correctly
"""

    result = reviewer_agent(
        code,
        test_result
    )

    print(
        "\n========== REVIEWER AGENT OUTPUT ==========\n"
    )

    print(result)