from pathlib import Path
import re
from typing import Any

from src.preprocessor_parser import (
    join_multiline_directives,
    read_source_file,
    remove_comments_from_text,
)


DEFINE_PATTERN = re.compile(
    r"^\s*#\s*define\s+([A-Za-z_]\w*)(.*)$"
)

IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z_]\w*$"
)


def extract_macro_definitions(
    source_file_path: str | Path,
) -> dict[str, str]:
    """
    Extracts object-like #define macro definitions from a C/C++ file.

    Function-like macros are intentionally ignored in this first
    implementation because they require argument expansion.

    Examples:
        #define STD_ON  1
        #define FEATURE_ENABLED STD_ON
        #define EMPTY_FLAG

    Returns:
        A dictionary in the format:
        {
            "STD_ON": "1",
            "FEATURE_ENABLED": "STD_ON",
            "EMPTY_FLAG": "1",
        }
    """

    lines = read_source_file(source_file_path)

    definitions: dict[str, str] = {}

    for _, directive_line in join_multiline_directives(lines):
        clean_line = remove_comments_from_text(
            directive_line
        )

        match = DEFINE_PATTERN.match(clean_line)

        if match is None:
            continue

        macro_name = match.group(1)
        raw_value = match.group(2)

        # A macro immediately followed by "(" is function-like:
        # #define MAX(a, b) ...
        # These are not resolved in the first version.
        if raw_value.startswith("("):
            continue

        macro_value = raw_value.strip()

        # A macro without an explicit replacement value is normally
        # used as a defined/undefined flag. Treat it as enabled.
        if not macro_value:
            macro_value = "1"

        definitions[macro_name] = macro_value

    return definitions


def merge_macro_definitions(
    definitions_list: list[dict[str, str]],
) -> dict[str, str]:
    """
    Merges macro-definition dictionaries.

    Definitions from later dictionaries overwrite previous values.
    This will later allow build configuration and project-specific
    headers to take precedence over generic headers.
    """

    merged_definitions: dict[str, str] = {}

    for definitions in definitions_list:
        merged_definitions.update(definitions)

    return merged_definitions


def resolve_macro_alias(
    macro_name: str,
    definitions: dict[str, str],
) -> dict[str, Any]:
    """
    Resolves a macro value through direct identifier aliases.

    Example:
        FEATURE_FLAG -> PROJECT_FEATURE_FLAG -> STD_ON -> 1

    This first version resolves:
    - direct literal values;
    - aliases composed of a single identifier;
    - empty macros represented as "1".

    It does not yet evaluate arithmetic expressions, function-like
    macros, logical expressions, or #if expressions.
    """

    resolution_chain: list[str] = []
    visited_macros: set[str] = set()

    current_macro = macro_name

    while True:
        if current_macro in visited_macros:
            return {
                "requested_macro": macro_name,
                "resolved_value": None,
                "resolution_chain": resolution_chain,
                "is_resolved": False,
                "has_cycle": True,
            }

        visited_macros.add(current_macro)
        resolution_chain.append(current_macro)

        macro_value = definitions.get(current_macro)

        if macro_value is None:
            return {
                "requested_macro": macro_name,
                "resolved_value": None,
                "resolution_chain": resolution_chain,
                "is_resolved": False,
                "has_cycle": False,
            }

        normalized_value = _strip_outer_parentheses(
            macro_value
        )
        if not IDENTIFIER_PATTERN.fullmatch(
            normalized_value
        ):
            return {
                "requested_macro": macro_name,
                "resolved_value": normalized_value,
                "resolution_chain": resolution_chain,
                "is_resolved": True,
                "has_cycle": False,
            }

        if normalized_value not in definitions:
            return {
                "requested_macro": macro_name,
                "resolved_value": normalized_value,
                "resolution_chain": resolution_chain,
                "is_resolved": True,
                "has_cycle": False,
            }

        current_macro = normalized_value

def _strip_outer_parentheses(
    value: str,
) -> str:
    """
    Removes balanced outer parentheses from a macro value.

    Examples:
    - (STD_ON) -> STD_ON
    - ((STD_OFF)) -> STD_OFF
    - (VALUE + 1) remains unchanged if the parentheses are part
      of a larger expression.
    """

    normalized_value = value.strip()

    while (
        normalized_value.startswith("(")
        and normalized_value.endswith(")")
        and _has_balanced_outer_parentheses(
            normalized_value
        )
    ):
        normalized_value = normalized_value[
            1:-1
        ].strip()

    return normalized_value


def _has_balanced_outer_parentheses(
    value: str,
) -> bool:
    """
    Checks whether the first opening parenthesis matches the final
    closing parenthesis of the complete value.
    """

    depth = 0

    for index, character in enumerate(value):
        if character == "(":
            depth += 1

        elif character == ")":
            depth -= 1

            if depth == 0 and index != len(value) - 1:
                return False

            if depth < 0:
                return False

    return depth == 0