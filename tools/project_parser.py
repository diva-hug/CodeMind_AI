import re


def parse_project(generated_text):
    """
    Convert Coding Agent FILE sections into a dictionary
    containing file paths and file contents.

    Supports formats such as:

    FILE: calculator.py

    <code>

    and:

    **FILE: calculator.py**

    <code>

    and accidental markdown code fences.
    """

    files = {}

    if not generated_text:
        return files

    # ---------------------------------------------------------
    # Normalize line endings
    # ---------------------------------------------------------

    generated_text = generated_text.replace(
        "\r\n",
        "\n"
    )

    lines = generated_text.split("\n")

    current_file = None
    current_content = []

    # ---------------------------------------------------------
    # FILE header pattern
    #
    # Supports:
    # FILE: calculator.py
    # **FILE: calculator.py**
    # ---------------------------------------------------------

    file_pattern = re.compile(
        r"^\s*\*{0,2}\s*FILE:\s*(.+?)\s*\*{0,2}\s*$",
        re.IGNORECASE
    )

    def clean_content(content):
        """
        Remove accidental markdown code fences
        from generated file content.
        """

        content = content.strip()

        if content.startswith("```python"):
            content = content[len("```python"):].lstrip()

        elif content.startswith("```py"):
            content = content[len("```py"):].lstrip()

        elif content.startswith("```"):
            content = content[3:].lstrip()

        if content.endswith("```"):
            content = content[:-3].rstrip()

        return content

    def save_current_file():
        """
        Save the currently collected file.
        """

        nonlocal current_file
        nonlocal current_content

        if current_file is None:
            return

        content = clean_content(
            "\n".join(current_content)
        )

        if current_file.strip():
            files[current_file.strip()] = content

    # ---------------------------------------------------------
    # Parse every line
    # ---------------------------------------------------------

    for line in lines:

        match = file_pattern.match(line)

        if match:

            # Save previous file
            save_current_file()

            current_file = match.group(1).strip()

            # Remove accidental markdown bold markers
            current_file = current_file.strip("*").strip()

            current_content = []

        else:

            if current_file is not None:
                current_content.append(line)

    # ---------------------------------------------------------
    # Save final file
    # ---------------------------------------------------------

    save_current_file()

    return files


# =========================================================
# Standalone Parser Test
# =========================================================

if __name__ == "__main__":

    test_project = """
**FILE: calculator.py**

def add(a, b):
    return a + b


**FILE: cli.py**

from calculator import add

print(add(2, 3))


**FILE: gui.py**

print("GUI")
"""

    project_files = parse_project(
        test_project
    )

    print("\nPROJECT FILES FOUND:")
    print("====================")

    for file_path, content in project_files.items():

        print("\nFILE:", file_path)
        print("CONTENT:")
        print(content)
        print("-" * 50)

    print(
        f"\nTOTAL FILES: {len(project_files)}"
    )