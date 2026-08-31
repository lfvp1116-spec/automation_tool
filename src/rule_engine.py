import re
from typing import Any, Iterable


VALID_EXPECTED_STATES = {
    "Enabled",
    "Disabled",
    "Defined",
    "Undefined",
}

C_INTEGER_LITERAL_PATTERN = re.compile(
    r"^(0[xX][0-9A-Fa-f]+|\d+)[uUlL]*$"
)

C_NUMERIC_SUFFIX_PATTERN = re.compile(
    r"[uUlL]+$"
)


def evaluate_rule(
    rule: dict[str, Any],
    macro_resolution: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Compares one expected rule with the resolution result of a macro.

    Rules may use either:
    - expected_state
    - expected_value

    Possible verdicts:
    - PASS
    - FAIL
    - REVIEW
    - NOT_APPLICABLE
    """

    rule_id = str(
        rule.get("id", "")
    )

    macro_name = str(
        rule.get("macro", "")
    )

    description = str(
        rule.get("description", "")
    )

    expected_value = rule.get(
        "expected_value"
    )

    expected_state = rule.get(
        "expected_state"
    )

    if expected_value is not None:
        return _evaluate_value_rule(
            rule_id=rule_id,
            macro_name=macro_name,
            description=description,
            expected_value=str(expected_value).strip(),
            macro_resolution=macro_resolution,
        )

    if expected_state is None:
        return _build_rule_result(
            rule_id=rule_id,
            macro_name=macro_name,
            description=description,
            expected_state="",
            expected_value="",
            macro_resolution=macro_resolution,
            verdict="NOT_APPLICABLE",
            reason=(
                "No expected state or expected value is configured "
                "for this rule."
            ),
        )

    expected_state_text = str(
        expected_state
    ).strip()

    if expected_state_text not in VALID_EXPECTED_STATES:
        return _build_rule_result(
            rule_id=rule_id,
            macro_name=macro_name,
            description=description,
            expected_state=expected_state_text,
            expected_value="",
            macro_resolution=macro_resolution,
            verdict="REVIEW",
            reason=(
                "The configured expected state is not supported: "
                f"{expected_state_text}"
            ),
        )

    if expected_state_text == "Undefined":
        return _evaluate_undefined_rule(
            rule_id=rule_id,
            macro_name=macro_name,
            description=description,
            macro_resolution=macro_resolution,
        )

    if macro_resolution is None:
        return _build_rule_result(
            rule_id=rule_id,
            macro_name=macro_name,
            description=description,
            expected_state=expected_state_text,
            expected_value="",
            macro_resolution=None,
            verdict="REVIEW",
            reason=(
                "The macro does not appear in the macro-resolution "
                "results."
            ),
        )

    actual_state = _get_actual_state(
        macro_resolution
    )

    if actual_state in {
        "Unresolved",
        "Cycle detected",
        "",
    }:
        return _build_rule_result(
            rule_id=rule_id,
            macro_name=macro_name,
            description=description,
            expected_state=expected_state_text,
            expected_value="",
            macro_resolution=macro_resolution,
            verdict="REVIEW",
            reason=(
                "The macro state cannot be verified because its "
                "resolution is incomplete."
            ),
        )

    if actual_state == expected_state_text:
        return _build_rule_result(
            rule_id=rule_id,
            macro_name=macro_name,
            description=description,
            expected_state=expected_state_text,
            expected_value="",
            macro_resolution=macro_resolution,
            verdict="PASS",
            reason=(
                "The actual macro state matches the expected state."
            ),
        )

    return _build_rule_result(
        rule_id=rule_id,
        macro_name=macro_name,
        description=description,
        expected_state=expected_state_text,
        expected_value="",
        macro_resolution=macro_resolution,
        verdict="FAIL",
        reason=(
            "The actual macro state does not match the expected "
            "state."
        ),
    )


def evaluate_rules(
    rules: Iterable[dict[str, Any]],
    macro_resolutions: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Evaluates all configured rules against macro-resolution results.
    """

    resolutions_by_macro = {
        str(result.get("primary_macro", "")): result
        for result in macro_resolutions
    }

    return [
        evaluate_rule(
            rule=rule,
            macro_resolution=resolutions_by_macro.get(
                str(rule.get("macro", ""))
            ),
        )
        for rule in rules
    ]


def summarize_rule_verdicts(
    rule_results: Iterable[dict[str, Any]],
) -> dict[str, int]:
    """
    Counts each verdict type for reporting purposes.
    """

    summary = {
        "total_rules": 0,
        "pass_count": 0,
        "fail_count": 0,
        "review_count": 0,
        "not_applicable_count": 0,
    }

    for result in rule_results:
        summary["total_rules"] += 1

        verdict = str(
            result.get("verdict", "")
        )

        if verdict == "PASS":
            summary["pass_count"] += 1

        elif verdict == "FAIL":
            summary["fail_count"] += 1

        elif verdict == "REVIEW":
            summary["review_count"] += 1

        elif verdict == "NOT_APPLICABLE":
            summary["not_applicable_count"] += 1

    return summary


def _evaluate_value_rule(
    rule_id: str,
    macro_name: str,
    description: str,
    expected_value: str,
    macro_resolution: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Evaluates a rule requiring an exact resolved macro value.

    C integer literals are normalized before comparison, so values
    such as 0, 0u, 0U and 0UL are treated as equivalent.
    """

    if not expected_value:
        return _build_rule_result(
            rule_id=rule_id,
            macro_name=macro_name,
            description=description,
            expected_state="",
            expected_value="",
            macro_resolution=macro_resolution,
            verdict="REVIEW",
            reason=(
                "The configured expected value is empty."
            ),
        )

    if macro_resolution is None:
        return _build_rule_result(
            rule_id=rule_id,
            macro_name=macro_name,
            description=description,
            expected_state="",
            expected_value=expected_value,
            macro_resolution=None,
            verdict="REVIEW",
            reason=(
                "The macro does not appear in the macro-resolution "
                "results."
            ),
        )

    actual_state = _get_actual_state(
        macro_resolution
    )

    actual_value = _get_resolved_value(
        macro_resolution
    )

    if actual_state in {
        "Unresolved",
        "Cycle detected",
        "",
    } or not actual_value:
        return _build_rule_result(
            rule_id=rule_id,
            macro_name=macro_name,
            description=description,
            expected_state="",
            expected_value=expected_value,
            macro_resolution=macro_resolution,
            verdict="REVIEW",
            reason=(
                "The macro value cannot be verified because its "
                "resolution is incomplete."
            ),
        )

    resolution_chain = _get_resolution_field(
        macro_resolution,
        "resolution_chain",
    )

    if (
        _values_match(
            actual_value=actual_value,
            expected_value=expected_value,
        )
        or _expected_value_appears_in_chain(
            expected_value=expected_value,
            resolution_chain=resolution_chain,
        )
    ):
        
        return _build_rule_result(
            rule_id=rule_id,
            macro_name=macro_name,
            description=description,
            expected_state="",
            expected_value=expected_value,
            macro_resolution=macro_resolution,
            verdict="PASS",
            reason=(
                "The resolved macro value matches the expected value."
            ),
        )

    return _build_rule_result(
        rule_id=rule_id,
        macro_name=macro_name,
        description=description,
        expected_state="",
        expected_value=expected_value,
        macro_resolution=macro_resolution,
        verdict="FAIL",
        reason=(
            "The resolved macro value does not match the expected "
            "value."
        ),
    )


def _evaluate_undefined_rule(
    rule_id: str,
    macro_name: str,
    description: str,
    macro_resolution: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Evaluates a rule that requires a macro to be undefined.
    """

    if macro_resolution is None:
        return _build_rule_result(
            rule_id=rule_id,
            macro_name=macro_name,
            description=description,
            expected_state="Undefined",
            expected_value="",
            macro_resolution=None,
            verdict="PASS",
            reason=(
                "The macro is not present in the macro-resolution "
                "results, as expected."
            ),
        )

    actual_state = _get_actual_state(
        macro_resolution
    )

    resolution_status = _get_resolution_status(
        macro_resolution
    )

    if (
        actual_state == "Unresolved"
        and "definition not found"
        in resolution_status.lower()
    ):
        return _build_rule_result(
            rule_id=rule_id,
            macro_name=macro_name,
            description=description,
            expected_state="Undefined",
            expected_value="",
            macro_resolution=macro_resolution,
            verdict="PASS",
            reason=(
                "The macro definition was not found, as expected "
                "for this configuration."
            ),
        )

    if actual_state in {
        "Unresolved",
        "Cycle detected",
        "",
    }:
        return _build_rule_result(
            rule_id=rule_id,
            macro_name=macro_name,
            description=description,
            expected_state="Undefined",
            expected_value="",
            macro_resolution=macro_resolution,
            verdict="REVIEW",
            reason=(
                "The macro cannot be confirmed as undefined because "
                "its resolution is incomplete or ambiguous."
            ),
        )

    return _build_rule_result(
        rule_id=rule_id,
        macro_name=macro_name,
        description=description,
        expected_state="Undefined",
        expected_value="",
        macro_resolution=macro_resolution,
        verdict="FAIL",
        reason=(
            "The macro is defined, but the rule requires it to "
            "remain undefined."
        ),
    )


def _build_rule_result(
    rule_id: str,
    macro_name: str,
    description: str,
    expected_state: str,
    expected_value: str,
    macro_resolution: dict[str, Any] | None,
    verdict: str,
    reason: str,
) -> dict[str, Any]:
    """
    Creates one normalized rule result with macro-resolution evidence.
    """

    return {
        "rule_id": rule_id,
        "macro": macro_name,
        "description": description,
        "expected_state": expected_state,
        "expected_value": expected_value,
        "actual_state": _get_actual_state(
            macro_resolution
        ),
        "resolved_value": _get_resolved_value(
            macro_resolution
        ),
        "resolution_status": _get_resolution_status(
            macro_resolution
        ),
        "resolution_chain": _get_resolution_field(
            macro_resolution,
            "resolution_chain_text",
        ),
        "primary_definition_source": _get_resolution_field(
            macro_resolution,
            "primary_definition_source",
        ),
        "primary_definition_line": _get_resolution_field(
            macro_resolution,
            "primary_definition_line",
        ),
        "primary_definition_source_type": (
            _get_resolution_field(
                macro_resolution,
                "primary_definition_source_type",
            )
        ),
        "primary_definition_priority": (
            _get_resolution_field(
                macro_resolution,
                "primary_definition_priority",
            )
        ),
        "primary_definition_condition": (
            _get_resolution_field(
                macro_resolution,
                "primary_definition_condition",
            )
        ),
        "resolved_primary_definition_condition": (
            _get_resolution_field(
                macro_resolution,
                "resolved_primary_definition_condition",
            )
        ),
        "primary_definition_condition_evaluation": (
            _get_resolution_field(
                macro_resolution,
                "primary_definition_condition_evaluation",
            )
        ),
        "primary_definition_selection_reason": (
            _get_resolution_field(
                macro_resolution,
                "primary_definition_selection_reason",
            )
        ),
        "verdict": verdict,
        "reason": reason,
    }

def _expected_value_appears_in_chain(
    expected_value: str,
    resolution_chain: Any,
) -> bool:
    """
    Checks whether an expected symbolic value appears in the macro
    alias-resolution chain.

    Example:
        WDGM_TEST_ENABLED
        -> WDGM_TEST_ENABLED_Startup
        -> 1u

    A rule expecting WDGM_TEST_ENABLED_Startup is considered valid,
    even when the final resolved value is the numeric literal 1u.
    """

    if not isinstance(resolution_chain, list):
        return False

    normalized_expected = expected_value.strip()

    return any(
        str(chain_item).strip() == normalized_expected
        for chain_item in resolution_chain
    )

def _values_match(
    actual_value: str,
    expected_value: str,
) -> bool:
    """
    Compares values directly or as normalized C integer literals.
    """

    normalized_actual = actual_value.strip()
    normalized_expected = expected_value.strip()

    actual_number = _parse_c_integer_literal(
        normalized_actual
    )

    expected_number = _parse_c_integer_literal(
        normalized_expected
    )

    if actual_number is not None and expected_number is not None:
        return actual_number == expected_number

    return normalized_actual == normalized_expected


def _parse_c_integer_literal(
    value: str,
) -> int | None:
    """
    Parses a decimal or hexadecimal C integer literal with optional
    unsigned/long suffixes.
    """

    if not C_INTEGER_LITERAL_PATTERN.fullmatch(
        value
    ):
        return None

    numeric_text = C_NUMERIC_SUFFIX_PATTERN.sub(
        "",
        value,
    )

    try:
        return int(
            numeric_text,
            base=0,
        )
    except ValueError:
        return None


def _get_actual_state(
    macro_resolution: dict[str, Any] | None,
) -> str:
    """
    Returns a readable actual macro state.
    """

    if macro_resolution is None:
        return "Not found"

    return str(
        macro_resolution.get(
            "effective_state",
            "",
        )
    )


def _get_resolved_value(
    macro_resolution: dict[str, Any] | None,
) -> str:
    """
    Returns the resolved macro value when available.
    """

    if macro_resolution is None:
        return ""

    resolved_value = macro_resolution.get(
        "resolved_value"
    )

    if resolved_value is None:
        return ""

    return str(resolved_value)


def _get_resolution_status(
    macro_resolution: dict[str, Any] | None,
) -> str:
    """
    Returns the macro-resolution diagnostic status.
    """

    if macro_resolution is None:
        return "No macro resolution result found"

    return str(
        macro_resolution.get(
            "resolution_status",
            "",
        )
    )


def _get_resolution_field(
    macro_resolution: dict[str, Any] | None,
    field_name: str,
) -> Any:
    """
    Returns one resolution-evidence field when available.
    """

    if macro_resolution is None:
        return ""

    value = macro_resolution.get(
        field_name,
        "",
    )

    if value is None:
        return ""

    return value