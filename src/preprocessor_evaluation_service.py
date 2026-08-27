from typing import Any, Iterable

from src.preprocessor_expression_evaluator import (
    evaluate_preprocessor_expression,
)


def evaluate_relevant_preprocessor_conditions(
    findings: Iterable[dict[str, Any]],
    macro_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Evaluates relevant #if and #elif conditions using the effective
    macro definitions available in the macro index.

    #ifdef and #ifndef are converted into defined(MACRO) expressions
    so they can use the same secure evaluator.
    """

    evaluation_results: list[dict[str, Any]] = []

    for finding in findings:
        if not finding.get("is_relevant", False):
            continue

        expression = str(
            finding.get("expression", "")
        )

        directive = str(
            finding.get("directive", "")
        )

        evaluation_expression = _build_evaluation_expression(
            directive=directive,
            expression=expression,
        )

        evaluation = evaluate_preprocessor_expression(
            expression=evaluation_expression,
            macro_index=macro_index,
        )

        evaluation_results.append(
            {
                "source_file": str(
                    finding.get("path", "")
                ),
                "file_name": str(
                    finding.get("file_name", "")
                ),
                "line_number": finding.get(
                    "line_number",
                    "",
                ),
                "directive": directive,
                "category": str(
                    finding.get("category", "OTHER")
                ),
                "original_expression": expression,
                "evaluation_expression": (
                    evaluation_expression
                ),
                **evaluation,
            }
        )

    return evaluation_results


def _build_evaluation_expression(
    directive: str,
    expression: str,
) -> str:
    """
    Converts #ifdef and #ifndef expressions into defined() syntax.

    Examples:
        #ifdef FEATURE_X
        -> defined(FEATURE_X)

        #ifndef FEATURE_X
        -> !defined(FEATURE_X)

        #if (FEATURE_X == STD_ON)
        -> (FEATURE_X == STD_ON)
    """

    normalized_directive = directive.strip().lower()
    normalized_expression = expression.strip()

    if normalized_directive == "#ifdef":
        return (
            f"defined({normalized_expression})"
        )

    if normalized_directive == "#ifndef":
        return (
            f"!defined({normalized_expression})"
        )

    return normalized_expression