from pathlib import Path
import re


def read_source_file(source_file_path: str | Path) -> list[str]:
    """
    Reads a C/C++ source file and returns its lines.
    """

    path = Path(source_file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Source file was not found: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"The configured source path is not a file: {path}"
        )

    try:
        with path.open("r", encoding="utf-8") as file:
            return file.readlines()
    except UnicodeDecodeError:
        with path.open("r", encoding="latin-1") as file:
            return file.readlines()


def remove_comments_from_text(text: str) -> str:
    """
    Removes C/C++ inline comments from a text string.

    Supports:
    - // single-line comments
    - /* block comments */
    """

    text_without_block_comments = re.sub(
        r"/\*.*?\*/",
        "",
        text,
        flags=re.DOTALL,
    )

    text_without_comments = re.sub(
        r"//.*$",
        "",
        text_without_block_comments,
    )

    return text_without_comments.strip()


def join_multiline_directives(
    lines: list[str],
) -> list[tuple[int, str]]:
    """
    Joins preprocessor directives that continue with a backslash.

    Returns tuples containing:
    - original starting line number
    - joined directive text
    """

    joined_directives = []
    current_directive = ""
    starting_line_number = 0

    for line_number, line in enumerate(lines, start=1):
        stripped_line = line.rstrip()

        if not current_directive:
            starting_line_number = line_number

        if stripped_line.endswith("\\"):
            current_directive += stripped_line[:-1] + " "
        else:
            current_directive += stripped_line

            joined_directives.append(
                (starting_line_number, current_directive)
            )

            current_directive = ""

    if current_directive:
        joined_directives.append(
            (starting_line_number, current_directive)
        )

    return joined_directives


def extract_expression_macros(expression: str) -> list[str]:
    """
    Extracts identifier-like macro names from a preprocessor expression.
    """

    identifier_pattern = re.compile(
        r"\b[A-Za-z_]\w*\b"
    )

    ignored_tokens = {
        "defined",
    }

    macros = []
    seen_macros = set()

    for match in identifier_pattern.finditer(expression):
        macro_name = match.group(0)

        if macro_name in ignored_tokens:
            continue

        if macro_name not in seen_macros:
            macros.append(macro_name)
            seen_macros.add(macro_name)

    return macros


def find_preprocessor_directives(
    source_file_path: str | Path,
) -> list[dict]:
    """
    Detects #if, #ifdef, #ifndef and #elif directives
    inside a C/C++ source file.
    """

    lines = read_source_file(source_file_path)

    directive_pattern = re.compile(
        r"^\s*#\s*(if|ifdef|ifndef|elif)\b\s*(.*)$"
    )

    path = Path(source_file_path)
    findings = []

    for line_number, directive_line in join_multiline_directives(lines):
        clean_directive_line = remove_comments_from_text(
            directive_line
        )

        match = directive_pattern.match(clean_directive_line)

        if not match:
            continue

        directive_name = match.group(1)
        expression = match.group(2).strip()

        findings.append(
            {
                "path": str(path),
                "file_name": path.name,
                "line_number": line_number,
                "directive": f"#{directive_name}",
                "expression": expression,
                "macros": extract_expression_macros(expression),
            }
        )

    return findings