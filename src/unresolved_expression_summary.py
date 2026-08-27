import re
from typing import Any, Iterable


MISSING_DEFINITION_PATTERN = re.compile(
    r"^Macro definition not found:\s*(.+)$"
)

NON_INTEGER_MACRO_PATTERN = re.compile(
    r"^Macro does not resolve to an integer:\s*"
    r"([A-Za-z_]\w*)"
)


def summarize_unresolved_expressions(
    expression_evaluations: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Groups unresolved preprocessor-expression evaluations by their
    technical cause.

    The result contains one row per unique issue instead of one row
    per source occurrence.
    """

    grouped_issues: dict[
        tuple[str, str],
        dict[str, Any],
    ] = {}

    for evaluation in expression_evaluations:
        if (
            evaluation.get("evaluation_status")
            == "Evaluated"
        ):
            continue

        error_message = str(
            evaluation.get("error_message", "")
        )

        error_type, issue_key = _classify_error(
            error_message=error_message,
        )

        group_key = (
            error_type,
            issue_key,
        )

        if group_key not in grouped_issues:
            grouped_issues[group_key] = {
                "error_type": error_type,
                "issue_key": issue_key,
                "error_message": error_message,
                "category": str(
                    evaluation.get("category", "OTHER")
                ),
                "occurrences": 0,
                "source_files": set(),
                "example_original_expression": str(
                    evaluation.get(
                        "original_expression",
                        "",
                    )
                ),
                "example_source_file": str(
                    evaluation.get(
                        "source_file",
                        "",
                    )
                ),
                "example_line": evaluation.get(
                    "line_number",
                    "",
                ),
                "example_directive": str(
                    evaluation.get("directive", "")
                ),
            }

        grouped_issues[group_key]["occurrences"] += 1

        source_file = str(
            evaluation.get("source_file", "")
        )

        if source_file:
            grouped_issues[group_key][
                "source_files"
            ].add(source_file)

    summary_rows: list[dict[str, Any]] = []

    for issue_data in grouped_issues.values():
        summary_rows.append(
            {
                "error_type": issue_data["error_type"],
                "issue_key": issue_data["issue_key"],
                "category": issue_data["category"],
                "occurrences": issue_data["occurrences"],
                "files_affected": len(
                    issue_data["source_files"]
                ),
                "error_message": issue_data[
                    "error_message"
                ],
                "example_original_expression": issue_data[
                    "example_original_expression"
                ],
                "example_source_file": issue_data[
                    "example_source_file"
                ],
                "example_line": issue_data["example_line"],
                "example_directive": issue_data[
                    "example_directive"
                ],
            }
        )

    return sorted(
        summary_rows,
        key=lambda item: (
            -int(item["occurrences"]),
            str(item["error_type"]),
            str(item["issue_key"]),
        ),
    )


def _classify_error(
    error_message: str,
) -> tuple[str, str]:
    """
    Converts an evaluator error message into a readable issue type
    and a stable grouping key.
    """

    missing_definition_match = (
        MISSING_DEFINITION_PATTERN.match(
            error_message
        )
    )

    if missing_definition_match is not None:
        macro_name = missing_definition_match.group(1)

        return (
            "Missing macro definition",
            macro_name,
        )

    non_integer_macro_match = (
        NON_INTEGER_MACRO_PATTERN.match(
            error_message
        )
    )

    if non_integer_macro_match is not None:
        macro_name = non_integer_macro_match.group(1)

        return (
            "Macro resolves to non-integer expression",
            macro_name,
        )

    if error_message.startswith(
        "Unsupported expression content near:"
    ):
        return (
            "Unsupported expression syntax",
            error_message,
        )

    if error_message.startswith(
        "Cyclic macro alias detected for:"
    ):
        return (
            "Cyclic macro alias",
            error_message,
        )

    return (
        "Other evaluation error",
        error_message or "No error message",
    )