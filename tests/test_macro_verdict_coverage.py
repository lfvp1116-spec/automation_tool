from src.macro_verdict_coverage import (
    build_macro_verdict_coverage,
)

from src.macro_verdict_coverage import (
    build_macro_verdict_coverage,
    summarize_macro_verdict_coverage,
)

def build_resolution(
    macro: str,
    category: str,
    state: str,
    value: str,
    occurrences: int,
) -> dict:
    """
    Creates controlled macro-resolution data.
    """

    return {
        "primary_macro": macro,
        "category": category,
        "occurrences": occurrences,
        "files_affected": 2,
        "effective_state": state,
        "resolved_value": value,
        "resolution_status": "Resolved",
        "resolution_chain_text": (
            f"{macro} -> {value}"
        ),
        "primary_definition_source": (
            f"cfg/{macro}_Cfg.h"
        ),
        "primary_definition_line": 42,
        "primary_definition_source_type": (
            "conditional_definition"
        ),
    }


def test_marks_macro_with_configured_rule() -> None:
    macro_resolutions = [
        build_resolution(
            macro="DET_ENABLED",
            category="FEATURE",
            state="Enabled",
            value="1u",
            occurrences=8,
        )
    ]

    rule_results = [
        {
            "rule_id": "REL-002",
            "rule_type": "Macro",
            "macro": "DET_ENABLED",
            "expected_state": "Enabled",
            "expected_value": "",
            "verdict": "PASS",
            "reason": (
                "The actual macro state matches the expected state."
            ),
        }
    ]

    coverage = build_macro_verdict_coverage(
        macro_resolutions=macro_resolutions,
        rule_results=rule_results,
    )

    assert len(coverage) == 1

    result = coverage[0]

    assert result["macro"] == "DET_ENABLED"
    assert result["rule_id"] == "REL-002"
    assert result["expected_state"] == "Enabled"
    assert result["rule_verdict"] == "PASS"
    assert result["coverage_status"] == "Rule configured"


def test_marks_macro_without_rule_as_not_applicable() -> None:
    macro_resolutions = [
        build_resolution(
            macro="VSECPRIM_AES128_ENABLED",
            category="FEATURE",
            state="Enabled",
            value="1u",
            occurrences=4,
        )
    ]

    coverage = build_macro_verdict_coverage(
        macro_resolutions=macro_resolutions,
        rule_results=[],
    )

    assert len(coverage) == 1

    result = coverage[0]

    assert result["macro"] == "VSECPRIM_AES128_ENABLED"
    assert result["rule_id"] == ""
    assert result["rule_verdict"] == "NOT_APPLICABLE"

    assert (
        result["coverage_status"]
        == "No approved macro rule configured"
    )


def test_ignores_expression_rules_for_macro_coverage() -> None:
    macro_resolutions = [
        build_resolution(
            macro="DET_DEBUG_ENABLED",
            category="DEBUG",
            state="Enabled",
            value="1u",
            occurrences=15,
        )
    ]

    rule_results = [
        {
            "rule_id": "REL-033",
            "rule_type": "Expression",
            "macro": (
                "(DET_DEBUG_ENABLED == STD_ON) && "
                "(DET_DLTFILTERSIZE > 0)"
            ),
            "verdict": "PASS",
        }
    ]

    coverage = build_macro_verdict_coverage(
        macro_resolutions=macro_resolutions,
        rule_results=rule_results,
    )

    assert coverage[0]["rule_verdict"] == "NOT_APPLICABLE"


def test_sorts_fail_before_pass_and_not_applicable() -> None:
    macro_resolutions = [
        build_resolution(
            macro="FEATURE_A",
            category="FEATURE",
            state="Enabled",
            value="1u",
            occurrences=1,
        ),
        build_resolution(
            macro="FEATURE_B",
            category="FEATURE",
            state="Disabled",
            value="0u",
            occurrences=9,
        ),
        build_resolution(
            macro="FEATURE_C",
            category="FEATURE",
            state="Enabled",
            value="1u",
            occurrences=3,
        ),
    ]

    rule_results = [
        {
            "rule_id": "REL-001",
            "rule_type": "Macro",
            "macro": "FEATURE_A",
            "expected_state": "Disabled",
            "expected_value": "",
            "verdict": "FAIL",
            "reason": "State mismatch.",
        },
        {
            "rule_id": "REL-002",
            "rule_type": "Macro",
            "macro": "FEATURE_B",
            "expected_state": "Disabled",
            "expected_value": "",
            "verdict": "PASS",
            "reason": "State matches.",
        },
    ]

    coverage = build_macro_verdict_coverage(
        macro_resolutions=macro_resolutions,
        rule_results=rule_results,
    )

    assert coverage[0]["macro"] == "FEATURE_A"
    assert coverage[0]["rule_verdict"] == "FAIL"

    assert coverage[1]["macro"] == "FEATURE_B"
    assert coverage[1]["rule_verdict"] == "PASS"

    assert coverage[2]["macro"] == "FEATURE_C"
    assert coverage[2]["rule_verdict"] == "NOT_APPLICABLE"

def test_summarizes_macro_verdict_coverage() -> None:
    coverage_rows = [
        {
            "macro": "DET_ENABLED",
            "coverage_status": "Rule configured",
        },
        {
            "macro": "DET_DEBUG_ENABLED",
            "coverage_status": "Rule configured",
        },
        {
            "macro": "VSECPRIM_AES128_ENABLED",
            "coverage_status": (
                "No approved macro rule configured"
            ),
        },
        {
            "macro": "DCM_SVC_11_01_SUPPORT_ENABLED",
            "coverage_status": (
                "No approved macro rule configured"
            ),
        },
    ]

    summary = summarize_macro_verdict_coverage(
        coverage_rows
    )

    assert summary == {
        "total_macros": 4,
        "covered_macros": 2,
        "uncovered_macros": 2,
        "coverage_percentage": 50.0,
    }