import re
from typing import Any, Iterable


def evaluate_expression_rule(
    rule: dict[str, Any],
    expression_evaluations: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """
    Evaluates one rule that expects a preprocessor expression to
    produce True or False.

    A rule passes only when every matching expression occurrence was
    evaluated successfully and matches the expected result.
    """

    rule_id = str(
        rule.get("id", "")
    )

    expression = str(
        rule.get("expression", "")
    )

    description = str(
        rule.get("description", "")
    )

    expected_result = rule.get(
        "expected_result"
    )

    if not isinstance(expected_result, bool):
        return _build_expression_rule_result(
            rule_id=rule_id,
            expression=expression,
            description=description,
            expected_result="",
            actual_result="",
            occurrences=0,
            files_affected=0,
            verdict="REVIEW",
            reason=(
                "The expression rule does not contain a valid "
                "boolean expected_result."
            ),
        )

    normalized_expression = _normalize_expression(
        expression
    )

    matching_evaluations = [
        evaluation
        for evaluation in expression_evaluations
        if _normalize_expression(
            str(
                evaluation.get(
                    "original_expression",
                    "",
                )
            )
        )
        == normalized_expression
    ]

    if not matching_evaluations:
        return _build_expression_rule_result(
            rule_id=rule_id,
            expression=expression,
            description=description,
            expected_result=str(expected_result),
            actual_result="Not found",
            occurrences=0,
            files_affected=0,
            verdict="REVIEW",
            reason=(
                "No matching expression evaluation result was found."
            ),
        )

    unresolved_evaluations = [
        evaluation
        for evaluation in matching_evaluations
        if evaluation.get("evaluation_status") != "Evaluated"
    ]

    source_files = {
        str(evaluation.get("source_file", ""))
        for evaluation in matching_evaluations
        if evaluation.get("source_file")
    }

    if unresolved_evaluations:
        return _build_expression_rule_result(
            rule_id=rule_id,
            expression=expression,
            description=description,
            expected_result=str(expected_result),
            actual_result="Unresolved",
            occurrences=len(matching_evaluations),
            files_affected=len(source_files),
            verdict="REVIEW",
            reason=(
                "One or more matching expression occurrences could "
                "not be evaluated."
            ),
        )

    evaluation_values = [
        bool(evaluation.get("evaluation"))
        for evaluation in matching_evaluations
    ]

    if all(
        value == expected_result
        for value in evaluation_values
    ):
        return _build_expression_rule_result(
            rule_id=rule_id,
            expression=expression,
            description=description,
            expected_result=str(expected_result),
            actual_result=str(expected_result),
            occurrences=len(matching_evaluations),
            files_affected=len(source_files),
            verdict="PASS",
            reason=(
                "All matching expression occurrences match the "
                "expected result."
            ),
        )

    if len(set(evaluation_values)) > 1:
        actual_result = "Mixed"
    else:
        actual_result = str(evaluation_values[0])

    return _build_expression_rule_result(
        rule_id=rule_id,
        expression=expression,
        description=description,
        expected_result=str(expected_result),
        actual_result=actual_result,
        occurrences=len(matching_evaluations),
        files_affected=len(source_files),
        verdict="FAIL",
        reason=(
            "One or more matching expression occurrences do not "
            "match the expected result."
        ),
    )


def evaluate_expression_rules(
    rules: Iterable[dict[str, Any]],
    expression_evaluations: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Evaluates all configured expression rules.
    """

    evaluations_list = list(expression_evaluations)

    return [
        evaluate_expression_rule(
            rule=rule,
            expression_evaluations=evaluations_list,
        )
        for rule in rules
    ]


def _normalize_expression(
    expression: str,
) -> str:
    """
    Normalizes an expression for whitespace-insensitive comparison.
    """

    return re.sub(
        r"\s+",
        "",
        expression,
    )


def _build_expression_rule_result(
    rule_id: str,
    expression: str,
    description: str,
    expected_result: str,
    actual_result: str,
    occurrences: int,
    files_affected: int,
    verdict: str,
    reason: str,
) -> dict[str, Any]:
    """
    Creates one normalized result for an expression rule.
    """

    return {
        "rule_id": rule_id,
        "rule_type": "Expression",
        "macro": expression,
        "description": description,
        "expected_state": "",
        "expected_value": "",
        "expected_result": expected_result,
        "actual_state": actual_result,
        "actual_result": actual_result,
        "resolved_value": "",
        "resolution_status": "Expression evaluation",
        "resolution_chain": "",
        "primary_definition_source": "",
        "primary_definition_line": "",
        "primary_definition_source_type": "",
        "primary_definition_priority": "",
        "primary_definition_condition": "",
        "resolved_primary_definition_condition": "",
        "primary_definition_condition_evaluation": "",
        "primary_definition_selection_reason": "",
        "occurrences": occurrences,
        "files_affected": files_affected,
        "verdict": verdict,
        "reason": reason,
    }