from src.rule_engine import (
    evaluate_rule,
    evaluate_rules,
    summarize_rule_verdicts,
)


def build_resolution(
    macro_name: str,
    effective_state: str,
    resolved_value: str = "1u",
    resolution_status: str = "Resolved",
) -> dict:
    """
    Creates controlled macro-resolution data for tests.
    """

    return {
        "primary_macro": macro_name,
        "effective_state": effective_state,
        "resolved_value": resolved_value,
        "resolution_status": resolution_status,
    }


def test_returns_pass_when_state_matches_rule() -> None:
    rule = {
        "id": "RULE-001",
        "macro": "FEATURE_X",
        "expected_state": "Enabled",
        "description": "Feature X must be enabled.",
    }

    resolution = build_resolution(
        macro_name="FEATURE_X",
        effective_state="Enabled",
    )

    result = evaluate_rule(
        rule=rule,
        macro_resolution=resolution,
    )

    assert result["verdict"] == "PASS"
    assert result["actual_state"] == "Enabled"
    assert result["expected_state"] == "Enabled"


def test_returns_fail_when_state_differs_from_rule() -> None:
    rule = {
        "id": "RULE-002",
        "macro": "FEATURE_X",
        "expected_state": "Disabled",
        "description": "Feature X must be disabled.",
    }

    resolution = build_resolution(
        macro_name="FEATURE_X",
        effective_state="Enabled",
    )

    result = evaluate_rule(
        rule=rule,
        macro_resolution=resolution,
    )

    assert result["verdict"] == "FAIL"
    assert result["actual_state"] == "Enabled"
    assert result["expected_state"] == "Disabled"


def test_returns_review_for_unresolved_macro() -> None:
    rule = {
        "id": "RULE-003",
        "macro": "FEATURE_X",
        "expected_state": "Enabled",
        "description": "Feature X must be enabled.",
    }

    resolution = build_resolution(
        macro_name="FEATURE_X",
        effective_state="Unresolved",
        resolved_value="",
        resolution_status=(
            "Unresolved: definition not found"
        ),
    )

    result = evaluate_rule(
        rule=rule,
        macro_resolution=resolution,
    )

    assert result["verdict"] == "REVIEW"

    assert (
        "cannot be verified"
        in result["reason"]
    )


def test_returns_review_when_macro_is_not_found() -> None:
    rule = {
        "id": "RULE-004",
        "macro": "UNKNOWN_FEATURE",
        "expected_state": "Enabled",
        "description": "Unknown feature must be enabled.",
    }

    result = evaluate_rule(
        rule=rule,
        macro_resolution=None,
    )

    assert result["verdict"] == "REVIEW"
    assert result["actual_state"] == "Not found"


def test_returns_not_applicable_without_expected_state() -> None:
    rule = {
        "id": "RULE-005",
        "macro": "NVM_API_CONFIG_CLASS",
        "expected_state": None,
        "description": "Traceability-only rule.",
    }

    resolution = build_resolution(
        macro_name="NVM_API_CONFIG_CLASS",
        effective_state="Defined",
        resolved_value="7u",
        resolution_status="Resolved literal value",
    )

    result = evaluate_rule(
        rule=rule,
        macro_resolution=resolution,
    )

    assert result["verdict"] == "NOT_APPLICABLE"
    assert result["actual_state"] == "Defined"
    assert result["expected_state"] == ""


def test_evaluates_multiple_rules_and_summarizes_verdicts() -> None:
    rules = [
        {
            "id": "RULE-001",
            "macro": "FEATURE_ENABLED",
            "expected_state": "Enabled",
            "description": "Expected enabled.",
        },
        {
            "id": "RULE-002",
            "macro": "FEATURE_DISABLED",
            "expected_state": "Enabled",
            "description": "Expected enabled.",
        },
        {
            "id": "RULE-003",
            "macro": "UNKNOWN_FEATURE",
            "expected_state": "Disabled",
            "description": "Expected disabled.",
        },
        {
            "id": "RULE-004",
            "macro": "CONFIG_CLASS",
            "expected_state": None,
            "description": "Traceability only.",
        },
    ]

    macro_resolutions = [
        build_resolution(
            macro_name="FEATURE_ENABLED",
            effective_state="Enabled",
        ),
        build_resolution(
            macro_name="FEATURE_DISABLED",
            effective_state="Disabled",
            resolved_value="0u",
        ),
        build_resolution(
            macro_name="CONFIG_CLASS",
            effective_state="Defined",
            resolved_value="7u",
            resolution_status="Resolved literal value",
        ),
    ]

    results = evaluate_rules(
        rules=rules,
        macro_resolutions=macro_resolutions,
    )

    summary = summarize_rule_verdicts(results)

    assert len(results) == 4

    assert results[0]["verdict"] == "PASS"
    assert results[1]["verdict"] == "FAIL"
    assert results[2]["verdict"] == "REVIEW"
    assert results[3]["verdict"] == "NOT_APPLICABLE"

    assert summary == {
        "total_rules": 4,
        "pass_count": 1,
        "fail_count": 1,
        "review_count": 1,
        "not_applicable_count": 1,
    }

def test_preserves_macro_resolution_evidence_in_rule_result(
) -> None:
    rule = {
        "id": "RULE-006",
        "macro": "FEATURE_X",
        "expected_state": "Enabled",
        "description": "Feature X must be enabled.",
    }

    resolution = {
        "primary_macro": "FEATURE_X",
        "effective_state": "Enabled",
        "resolved_value": "1u",
        "resolution_status": "Resolved",
        "resolution_chain_text": (
            "FEATURE_X -> STD_ON -> 1u"
        ),
        "primary_definition_source": "Project_Cfg.h",
        "primary_definition_line": 45,
        "primary_definition_source_type": (
            "conditional_definition"
        ),
        "primary_definition_priority": 5,
        "primary_definition_condition": (
            "FEATURE_SELECTOR == STD_ON"
        ),
        "resolved_primary_definition_condition": (
            "1u == 1u"
        ),
        "primary_definition_condition_evaluation": True,
        "primary_definition_selection_reason": (
            "Conditional branch evaluated as active"
        ),
    }

    result = evaluate_rule(
        rule=rule,
        macro_resolution=resolution,
    )

    assert result["verdict"] == "PASS"

    assert (
        result["resolution_chain"]
        == "FEATURE_X -> STD_ON -> 1u"
    )

    assert (
        result["primary_definition_source"]
        == "Project_Cfg.h"
    )

    assert result["primary_definition_line"] == 45

    assert (
        result["primary_definition_source_type"]
        == "conditional_definition"
    )

    assert result["primary_definition_priority"] == 5

    assert (
        result["primary_definition_condition"]
        == "FEATURE_SELECTOR == STD_ON"
    )

    assert (
        result[
            "primary_definition_condition_evaluation"
        ]
        is True
    )

    assert (
        result["primary_definition_selection_reason"]
        == "Conditional branch evaluated as active"
    )

def test_returns_pass_when_numeric_value_matches_with_suffix(
) -> None:
    rule = {
        "id": "RULE-010",
        "macro": "RAMTEST_IMMEDIATE_SECTIONS_NUM",
        "expected_value": "0",
        "description": (
            "No immediate RAM test sections are expected."
        ),
    }

    resolution = build_resolution(
        macro_name="RAMTEST_IMMEDIATE_SECTIONS_NUM",
        effective_state="Defined",
        resolved_value="0u",
        resolution_status="Resolved literal value",
    )

    result = evaluate_rule(
        rule=rule,
        macro_resolution=resolution,
    )

    assert result["verdict"] == "PASS"
    assert result["expected_state"] == ""
    assert result["expected_value"] == "0"


def test_returns_pass_when_symbolic_value_matches() -> None:
    rule = {
        "id": "RULE-011",
        "macro": "WDGM_TEST_ENABLED",
        "expected_value": "WDGM_TEST_ENABLED_Startup",
        "description": (
            "Watchdog test mode must select Startup."
        ),
    }

    resolution = build_resolution(
        macro_name="WDGM_TEST_ENABLED",
        effective_state="Defined",
        resolved_value="WDGM_TEST_ENABLED_Startup",
        resolution_status="Resolved literal value",
    )

    result = evaluate_rule(
        rule=rule,
        macro_resolution=resolution,
    )

    assert result["verdict"] == "PASS"
    assert (
        result["expected_value"]
        == "WDGM_TEST_ENABLED_Startup"
    )


def test_returns_fail_when_value_does_not_match() -> None:
    rule = {
        "id": "RULE-012",
        "macro": "DET_DLTFILTERSIZE",
        "expected_value": "0",
        "description": (
            "DET DLT filter size must remain zero."
        ),
    }

    resolution = build_resolution(
        macro_name="DET_DLTFILTERSIZE",
        effective_state="Defined",
        resolved_value="4u",
        resolution_status="Resolved literal value",
    )

    result = evaluate_rule(
        rule=rule,
        macro_resolution=resolution,
    )

    assert result["verdict"] == "FAIL"

def test_returns_pass_when_expected_alias_appears_in_chain(
) -> None:
    rule = {
        "id": "RULE-013",
        "macro": "WDGM_TEST_ENABLED",
        "expected_value": "WDGM_TEST_ENABLED_Startup",
        "description": (
            "Watchdog test mode must select Startup."
        ),
    }

    resolution = {
        "primary_macro": "WDGM_TEST_ENABLED",
        "effective_state": "Enabled",
        "resolved_value": "1u",
        "resolution_status": "Resolved",
        "resolution_chain": [
            "WDGM_TEST_ENABLED",
            "WDGM_TEST_ENABLED_Startup",
        ],
        "resolution_chain_text": (
            "WDGM_TEST_ENABLED -> "
            "WDGM_TEST_ENABLED_Startup -> 1u"
        ),
    }

    result = evaluate_rule(
        rule=rule,
        macro_resolution=resolution,
    )

    assert result["verdict"] == "PASS"

    assert (
        result["expected_value"]
        == "WDGM_TEST_ENABLED_Startup"
    )