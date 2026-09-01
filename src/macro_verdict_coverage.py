from typing import Any, Iterable


def build_macro_verdict_coverage(
    macro_resolutions: Iterable[dict[str, Any]],
    rule_results: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Creates one coverage record for every unique macro in
    Macro Resolution Summary.

    Macro rules are matched by macro name. Expression rules are not
    attached to one individual macro, so they remain available in
    Rule Verdicts only.

    Macros without an approved macro rule receive:
    - Verdict: NOT_APPLICABLE
    - Coverage Status: No approved macro rule configured
    """

    macro_rule_results = {
        str(result.get("macro", "")): result
        for result in rule_results
        if str(result.get("rule_type", "Macro")) == "Macro"
    }

    coverage_rows: list[dict[str, Any]] = []

    for resolution in macro_resolutions:
        macro_name = str(
            resolution.get("primary_macro", "")
        )

        rule_result = macro_rule_results.get(
            macro_name
        )

        if rule_result is None:
            coverage_rows.append(
                _build_uncovered_row(
                    resolution=resolution
                )
            )
            continue

        coverage_rows.append(
            _build_covered_row(
                resolution=resolution,
                rule_result=rule_result,
            )
        )

    return sorted(
        coverage_rows,
        key=lambda item: (
            _coverage_sort_priority(
                str(item.get("rule_verdict", ""))
            ),
            -int(item.get("occurrences", 0)),
            str(item.get("category", "")),
            str(item.get("macro", "")),
        ),
    )


def _build_covered_row(
    resolution: dict[str, Any],
    rule_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Builds one coverage row for a macro with a configured rule.
    """

    return {
        "category": str(
            resolution.get("category", "")
        ),
        "macro": str(
            resolution.get("primary_macro", "")
        ),
        "occurrences": resolution.get(
            "occurrences",
            0,
        ),
        "files_affected": resolution.get(
            "files_affected",
            0,
        ),
        "actual_state": str(
            resolution.get("effective_state", "")
        ),
        "resolved_value": _format_value(
            resolution.get("resolved_value")
        ),
        "resolution_status": str(
            resolution.get("resolution_status", "")
        ),
        "resolution_chain": str(
            resolution.get(
                "resolution_chain_text",
                "",
            )
        ),
        "rule_id": str(
            rule_result.get("rule_id", "")
        ),
        "expected_state": str(
            rule_result.get("expected_state", "")
        ),
        "expected_value": str(
            rule_result.get("expected_value", "")
        ),
        "rule_verdict": str(
            rule_result.get("verdict", "")
        ),
        "coverage_status": "Rule configured",
        "reason": str(
            rule_result.get("reason", "")
        ),
        "primary_definition_source": str(
            resolution.get(
                "primary_definition_source",
                "",
            )
        ),
        "primary_definition_line": resolution.get(
            "primary_definition_line",
            "",
        ),
        "primary_definition_source_type": str(
            resolution.get(
                "primary_definition_source_type",
                "",
            )
        ),
    }


def _build_uncovered_row(
    resolution: dict[str, Any],
) -> dict[str, Any]:
    """
    Builds one coverage row for a macro without an approved rule.
    """

    return {
        "category": str(
            resolution.get("category", "")
        ),
        "macro": str(
            resolution.get("primary_macro", "")
        ),
        "occurrences": resolution.get(
            "occurrences",
            0,
        ),
        "files_affected": resolution.get(
            "files_affected",
            0,
        ),
        "actual_state": str(
            resolution.get("effective_state", "")
        ),
        "resolved_value": _format_value(
            resolution.get("resolved_value")
        ),
        "resolution_status": str(
            resolution.get("resolution_status", "")
        ),
        "resolution_chain": str(
            resolution.get(
                "resolution_chain_text",
                "",
            )
        ),
        "rule_id": "",
        "expected_state": "",
        "expected_value": "",
        "rule_verdict": "NOT_APPLICABLE",
        "coverage_status": (
            "No approved macro rule configured"
        ),
        "reason": (
            "No approved macro rule is configured for this "
            "relevant macro."
        ),
        "primary_definition_source": str(
            resolution.get(
                "primary_definition_source",
                "",
            )
        ),
        "primary_definition_line": resolution.get(
            "primary_definition_line",
            "",
        ),
        "primary_definition_source_type": str(
            resolution.get(
                "primary_definition_source_type",
                "",
            )
        ),
    }


def _coverage_sort_priority(
    verdict: str,
) -> int:
    """
    Sorts actionable results before macros without a rule.
    """

    priorities = {
        "FAIL": 0,
        "REVIEW": 1,
        "PASS": 2,
        "NOT_APPLICABLE": 3,
    }

    return priorities.get(
        verdict,
        4,
    )


def _format_value(
    value: Any,
) -> str:
    """
    Converts an optional resolved value into readable text.
    """

    if value is None:
        return ""

    return str(value)

def summarize_macro_verdict_coverage(
    coverage_rows: Iterable[dict[str, Any]],
) -> dict[str, int | float]:
    """
    Calculates coverage metrics for relevant unique macros.

    A macro is considered covered only when it has an approved
    macro rule configured. Expression rules are evaluated separately
    and do not cover one individual macro.
    """

    rows = list(coverage_rows)

    covered_macros = [
        row
        for row in rows
        if row.get("coverage_status") == "Rule configured"
    ]

    uncovered_macros = [
        row
        for row in rows
        if (
            row.get("coverage_status")
            == "No approved macro rule configured"
        )
    ]

    total_macros = len(rows)

    if total_macros == 0:
        coverage_percentage = 0.0
    else:
        coverage_percentage = round(
            (len(covered_macros) / total_macros) * 100,
            2,
        )

    return {
        "total_macros": total_macros,
        "covered_macros": len(covered_macros),
        "uncovered_macros": len(uncovered_macros),
        "coverage_percentage": coverage_percentage,
    }