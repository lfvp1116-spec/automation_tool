from dataclasses import dataclass
from pathlib import Path
import re

from src.preprocessor_parser import (
    join_multiline_directives,
    read_source_file,
    remove_comments_from_text,
)


DEFINE_PATTERN = re.compile(
    r"^\s*#\s*define\s+([A-Za-z_]\w*)(.*)$"
)

IF_PATTERN = re.compile(
    r"^\s*#\s*if\s+(.+)$"
)

IFDEF_PATTERN = re.compile(
    r"^\s*#\s*ifdef\s+([A-Za-z_]\w*)\s*$"
)

IFNDEF_PATTERN = re.compile(
    r"^\s*#\s*ifndef\s+([A-Za-z_]\w*)\s*$"
)

ELIF_PATTERN = re.compile(
    r"^\s*#\s*elif\s+(.+)$"
)

ELSE_PATTERN = re.compile(
    r"^\s*#\s*else\b"
)

ENDIF_PATTERN = re.compile(
    r"^\s*#\s*endif\b"
)

NOT_DEFINED_GUARD_PATTERN = re.compile(
    r"""
    ^!\s*defined
    (?:
        \s*\(\s*([A-Za-z_]\w*)\s*\)
        |
        \s+([A-Za-z_]\w*)
    )
    \s*$
    """,
    re.VERBOSE,
)


@dataclass(frozen=True)
class ConditionalMacroDefinition:
    """
    Represents one object-like #define and the conditional context
    under which the definition is active.
    """

    name: str
    value: str
    source_file: str
    line_number: int
    conditional_context: str | None


@dataclass
class ConditionalBlock:
    """
    Tracks one #if / #elif / #else / #endif block.
    """

    branch_conditions: list[str]
    current_branch_context: str


def extract_conditional_macro_definitions(
    source_file_path: str | Path,
) -> list[ConditionalMacroDefinition]:
    """
    Extracts object-like #define macros and records the #if context
    that governs each definition.

    Supports:
    - #if
    - #ifdef
    - #ifndef
    - #elif
    - #else
    - #endif

    Conventional outer header guards are ignored because they are
    structural include-protection mechanisms, not build conditions.
    """

    path = Path(source_file_path)
    lines = read_source_file(path)

    joined_directives = join_multiline_directives(
        lines
    )

    definitions: list[ConditionalMacroDefinition] = []
    conditional_stack: list[ConditionalBlock] = []

    for directive_index, (
        line_number,
        directive_line,
    ) in enumerate(joined_directives):
        clean_line = remove_comments_from_text(
            directive_line
        )

        if not clean_line:
            continue

        if_match = IF_PATTERN.match(clean_line)

        if if_match is not None:
            condition = if_match.group(1).strip()

            guard_macro_name = _extract_if_guard_macro(
                condition
            )

            if (
                guard_macro_name is not None
                and _is_outer_header_guard(
                    joined_directives=joined_directives,
                    directive_index=directive_index,
                    guard_macro_name=guard_macro_name,
                )
            ):
                continue

            conditional_stack.append(
                ConditionalBlock(
                    branch_conditions=[condition],
                    current_branch_context=condition,
                )
            )
            continue

        ifdef_match = IFDEF_PATTERN.match(clean_line)

        if ifdef_match is not None:
            macro_name = ifdef_match.group(1)

            condition = f"defined({macro_name})"

            conditional_stack.append(
                ConditionalBlock(
                    branch_conditions=[condition],
                    current_branch_context=condition,
                )
            )
            continue

        ifndef_match = IFNDEF_PATTERN.match(clean_line)

        if ifndef_match is not None:
            macro_name = ifndef_match.group(1)

            if _is_outer_header_guard(
                joined_directives=joined_directives,
                directive_index=directive_index,
                guard_macro_name=macro_name,
            ):
                continue

            condition = f"!defined({macro_name})"

            conditional_stack.append(
                ConditionalBlock(
                    branch_conditions=[condition],
                    current_branch_context=condition,
                )
            )
            continue

        elif_match = ELIF_PATTERN.match(clean_line)

        if elif_match is not None:
            _handle_elif(
                condition=elif_match.group(1).strip(),
                conditional_stack=conditional_stack,
            )
            continue

        if ELSE_PATTERN.match(clean_line) is not None:
            _handle_else(
                conditional_stack=conditional_stack,
            )
            continue

        if ENDIF_PATTERN.match(clean_line) is not None:
            if conditional_stack:
                conditional_stack.pop()

            continue

        define_match = DEFINE_PATTERN.match(clean_line)

        if define_match is None:
            continue

        macro_name = define_match.group(1)
        raw_value = define_match.group(2)

        # Function-like macros have the opening parenthesis directly
        # after the macro name, for example:
        #
        # #define MAX(value) ((value) + 1)
        #
        # They are intentionally ignored in this implementation.
        if raw_value.startswith("("):
            continue

        macro_value = raw_value.strip()

        # A macro declared without an explicit value is treated as a
        # defined/enabled flag.
        if not macro_value:
            macro_value = "1"

        definitions.append(
            ConditionalMacroDefinition(
                name=macro_name,
                value=macro_value,
                source_file=str(path),
                line_number=line_number,
                conditional_context=_build_context(
                    conditional_stack
                ),
            )
        )

    return definitions


def _extract_if_guard_macro(
    condition: str,
) -> str | None:
    """
    Returns the guard macro name when an #if condition represents an
    include guard, for example:

        #if !defined(MODULE_H)
        #if !defined (MODULE_H)
        #if (!defined(MODULE_H))
        #if ((!defined(MODULE_H)))
        #if !defined MODULE_H
    """

    normalized_condition = _strip_outer_parentheses(
        condition
    )

    match = NOT_DEFINED_GUARD_PATTERN.match(
        normalized_condition
    )

    if match is None:
        return None

    return match.group(1) or match.group(2)


def _strip_outer_parentheses(
    value: str,
) -> str:
    """
    Removes balanced outer parentheses from an expression.

    Examples:
        (!defined(MODULE_H))
        -> !defined(MODULE_H)

        ((!defined(MODULE_H)))
        -> !defined(MODULE_H)
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
    Returns True when the outermost opening parenthesis is paired
    with the final closing parenthesis in the expression.
    """

    depth = 0

    for index, character in enumerate(value):
        if character == "(":
            depth += 1

        elif character == ")":
            depth -= 1

            if depth < 0:
                return False

            if depth == 0 and index != len(value) - 1:
                return False

    return depth == 0


def _is_outer_header_guard(
    joined_directives: list[tuple[int, str]],
    directive_index: int,
    guard_macro_name: str,
) -> bool:
    """
    Detects a conventional outer header guard:

        #ifndef MODULE_H
        #define MODULE_H

    or:

        #if !defined(MODULE_H)
        #define MODULE_H

    The guard may appear after a license or documentation block.
    Blank lines, comments and non-directive text between the opening
    guard and the matching #define are ignored.

    The candidate is rejected only when another conditional directive
    appears before the matching #define.
    """

    for _, next_directive_line in joined_directives[
        directive_index + 1:
    ]:
        clean_next_line = remove_comments_from_text(
            next_directive_line
        )

        if not clean_next_line:
            continue

        define_match = DEFINE_PATTERN.match(
            clean_next_line
        )

        if define_match is not None:
            return define_match.group(1) == guard_macro_name

        if (
            IF_PATTERN.match(clean_next_line) is not None
            or IFDEF_PATTERN.match(clean_next_line) is not None
            or IFNDEF_PATTERN.match(clean_next_line) is not None
            or ELIF_PATTERN.match(clean_next_line) is not None
            or ELSE_PATTERN.match(clean_next_line) is not None
            or ENDIF_PATTERN.match(clean_next_line) is not None
        ):
            return False

        # Ignore ordinary text, license content or documentation.
        continue

    return False


def _handle_elif(
    condition: str,
    conditional_stack: list[ConditionalBlock],
) -> None:
    """
    Updates the current branch context for an #elif directive.
    """

    if not conditional_stack:
        return

    current_block = conditional_stack[-1]

    previous_conditions = list(
        current_block.branch_conditions
    )

    current_block.current_branch_context = (
        _build_elif_context(
            previous_conditions=previous_conditions,
            condition=condition,
        )
    )

    current_block.branch_conditions.append(condition)


def _handle_else(
    conditional_stack: list[ConditionalBlock],
) -> None:
    """
    Updates the current branch context for an #else directive.
    """

    if not conditional_stack:
        return

    current_block = conditional_stack[-1]

    current_block.current_branch_context = (
        _build_else_context(
            previous_conditions=(
                current_block.branch_conditions
            )
        )
    )


def _build_context(
    conditional_stack: list[ConditionalBlock],
) -> str | None:
    """
    Combines nested conditional branch contexts using &&.
    """

    if not conditional_stack:
        return None

    contexts = [
        f"({block.current_branch_context})"
        for block in conditional_stack
    ]

    return " && ".join(contexts)


def _build_elif_context(
    previous_conditions: list[str],
    condition: str,
) -> str:
    """
    Creates the effective context for an #elif branch.

    Example:

        #if A
        #elif B

    Produces:

        (!(A) && (B))
    """

    previous_expression = _join_or_conditions(
        previous_conditions
    )

    return (
        f"(!({previous_expression}) && "
        f"({condition}))"
    )


def _build_else_context(
    previous_conditions: list[str],
) -> str:
    """
    Creates the effective context for an #else branch.

    Example:

        #if A
        #elif B
        #else

    Produces:

        !(A || B)
    """

    previous_expression = _join_or_conditions(
        previous_conditions
    )

    return f"!({previous_expression})"


def _join_or_conditions(
    conditions: list[str],
) -> str:
    """
    Combines branch conditions with logical OR.
    """

    if len(conditions) == 1:
        return conditions[0]

    return " || ".join(
        f"({condition})"
        for condition in conditions
    )