from pathlib import Path
import re


def read_makefile(makefile_path: str | Path) -> list[str]:
    """
    Reads a Makefile and returns its lines.

    Args:
        makefile_path: Path to the Makefile.

    Returns:
        List of lines read from the file.
    """

    path = Path(makefile_path)

    if not path.exists():
        raise FileNotFoundError(f"Makefile was not found: {path}")

    if not path.is_file():
        raise ValueError(f"The configured Makefile path is not a file: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            return file.readlines()
    except UnicodeDecodeError:
        # Some Makefiles may not use UTF-8 encoding.
        with path.open("r", encoding="latin-1") as file:
            return file.readlines()


def join_continued_lines(lines: list[str]) -> list[str]:
    """
    Joins Makefile lines that end with a backslash.
    """

    joined_lines = []
    current_line = ""

    for line in lines:
        clean_line = line.strip()

        if clean_line.endswith("\\"):
            current_line += clean_line[:-1] + " "
        else:
            current_line += clean_line
            joined_lines.append(current_line)
            current_line = ""

    if current_line:
        joined_lines.append(current_line)

    return joined_lines


def extract_define_macros(lines: list[str]) -> list[dict[str, str | None]]:
    """
    Extracts compiler macros declared with -D.

    Ignores text contained in Makefile comments.

    Examples:
        -DDEBUG
        -DDET_DEBUG_ENABLED=STD_OFF
    """

    macro_pattern = re.compile(
        r"(?<!\S)-D([A-Za-z_]\w*)(?:=([^\s]+))?"
    )

    macros = []
    seen_macros = set()

    for line in lines:
        # In Makefiles, everything after # is considered a comment.
        line_without_comment = line.split("#", 1)[0]

        for match in macro_pattern.finditer(line_without_comment):
            macro_name = match.group(1)
            macro_value = match.group(2)

            macro_key = (macro_name, macro_value)

            if macro_key not in seen_macros:
                macros.append(
                    {
                        "name": macro_name,
                        "value": macro_value,
                    }
                )
                seen_macros.add(macro_key)

    return macros

def extract_build_mode_definitions(
    lines: list[str],
    build_mode: str,
) -> list[dict[str, str | None]]:
    """
    Extracts macro definitions associated with a build mode.

    Example:
        CC_DEFLIST_RELEASE = LK_RELEASE=1
    """

    mode_name = build_mode.upper()

    definition_pattern = re.compile(
        rf"^\s*CC_DEFLIST_{mode_name}\s*(?::=|=)\s*(.+)$"
    )

    macro_pattern = re.compile(
        r"([A-Za-z_]\w*)=([^\s]+)"
    )

    definitions = []

    for line in lines:
        line_without_comment = line.split("#", 1)[0]

        definition_match = definition_pattern.match(
            line_without_comment
        )

        if not definition_match:
            continue

        definition_value = definition_match.group(1)

        for macro_match in macro_pattern.finditer(definition_value):
            definitions.append(
                {
                    "name": macro_match.group(1),
                    "value": macro_match.group(2),
                }
            )

    return definitions

def parse_makefile(
    makefile_path: str | Path,
    build_mode: str | None = None,
) -> dict:
    """
    Extracts relevant compiler options and -D macros from a Makefile.
    """

    lines = read_makefile(makefile_path)
    normalized_lines = join_continued_lines(lines)
    content = "\n".join(normalized_lines)

    compiler_match = re.search(
        r"^\s*CC\s*(?::=|=)\s*(.+?)\s*$",
        content,
        re.MULTILINE,
    )

    cpu_match = re.search(r"--cpu=([^\s]+)", content)
    fpu_match = re.search(r"--fpu=([^\s]+)", content)
    optimization_match = re.search(r"(?<!\S)(-O[^\s]+)", content)

    instruction_mode = None

    if re.search(r"--thumb2?\b", content):
        instruction_mode = "Thumb"

    result = {
        "makefile": str(makefile_path),
        "compiler": compiler_match.group(1).strip() if compiler_match else None,
        "cpu": cpu_match.group(1) if cpu_match else None,
        "fpu": fpu_match.group(1) if fpu_match else None,
        "instruction_mode": instruction_mode,
        "optimization": (
            optimization_match.group(1)
            if optimization_match
            else None
        ),
        "macros": extract_define_macros(normalized_lines),
        "build_mode_definitions": (
            extract_build_mode_definitions(
                normalized_lines,
                build_mode,
            )
            if build_mode
            else []
        ),
    }

    return result