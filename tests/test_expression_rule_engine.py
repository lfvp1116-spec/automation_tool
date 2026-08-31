from src.expression_rule_engine import (
    evaluate_expression_rule,
    evaluate_expression_rules,
)


DET_DLT_EXPRESSION = (
    "(DET_DEBUG_ENABLED == STD_ON) && "
    "(DET_DLTFILTERSIZE > 0)"
)


def build_evaluation(
    expression: str,
    result: bool | None,
    status: str = "Evaluated",
    source_file: str = "src/Det.c",
) -> dict:
    """
    Creates controlled expression-evaluation data.
    """

    return {
        "original_expression": expression,
        "evaluation": result,
        "evaluation_status": status,
        "source_file": source_file,
    }


def test_returns_pass_when_all_occurrences_match() -> None:
    rule = {
        "id": "REL-DET-EXPR-001",
        "expression": DET_DLT_EXPRESSION,
        "expected_result": False,
        "description": (
            "DET DLT-filter code must remain inactive."
        ),
    }

    evaluations = [
        build_evaluation(
            DET_DLT_EXPRESSION,
            False,
            source_file="src/Det.c",
        ),
        build_evaluation(
            "( DET_DEBUG_ENABLED == STD_ON ) && "
            "( DET_DLTFILTERSIZE > 0 )",
            False,
            source_file="src/Det.h",
        ),
    ]

    result = evaluate_expression_rule(
        rule=rule,
        expression_evaluations=evaluations,
    )

    assert result["verdict"] == "PASS"
    assert result["expected_result"] == "False"
    assert result["actual_result"] == "False"
    assert result["occurrences"] == 2
    assert result["files_affected"] == 2


def test_returns_fail_when_one_occurrence_differs() -> None:
    rule = {
        "id": "REL-DET-EXPR-002",
        "expression": DET_DLT_EXPRESSION,
        "expected_result": False,
        "description": (
            "DET DLT-filter code must remain inactive."
        ),
    }

    evaluations = [
        build_evaluation(
            DET_DLT_EXPRESSION,
            False,
        ),
        build_evaluation(
            DET_DLT_EXPRESSION,
            True,
        ),
    ]

    result = evaluate_expression_rule(
        rule=rule,
        expression_evaluations=evaluations,
    )

    assert result["verdict"] == "FAIL"
    assert result["actual_result"] == "Mixed"


def test_returns_review_when_occurrence_is_unresolved() -> None:
    rule = {
        "id": "REL-DET-EXPR-003",
        "expression": DET_DLT_EXPRESSION,
        "expected_result": False,
        "description": (
            "DET DLT-filter code must remain inactive."
        ),
    }

    evaluations = [
        build_evaluation(
            DET_DLT_EXPRESSION,
            None,
            status="Unresolved",
        ),
    ]

    result = evaluate_expression_rule(
        rule=rule,
        expression_evaluations=evaluations,
    )

    assert result["verdict"] == "REVIEW"
    assert result["actual_result"] == "Unresolved"


def test_returns_review_when_expression_is_not_found() -> None:
    rule = {
        "id": "REL-DET-EXPR-004",
        "expression": DET_DLT_EXPRESSION,
        "expected_result": False,
        "description": (
            "DET DLT-filter code must remain inactive."
        ),
    }

    result = evaluate_expression_rule(
        rule=rule,
        expression_evaluations=[],
    )

    assert result["verdict"] == "REVIEW"
    assert result["actual_result"] == "Not found"


def test_evaluates_multiple_expression_rules() -> None:
    rules = [
        {
            "id": "RULE-001",
            "expression": DET_DLT_EXPRESSION,
            "expected_result": False,
            "description": "First rule.",
        },
        {
            "id": "RULE-002",
            "expression": "(FEATURE_X == STD_ON)",
            "expected_result": True,
            "description": "Second rule.",
        },
    ]

    evaluations = [
        build_evaluation(
            DET_DLT_EXPRESSION,
            False,
        ),
        build_evaluation(
            "(FEATURE_X == STD_ON)",
            True,
        ),
    ]

    results = evaluate_expression_rules(
        rules=rules,
        expression_evaluations=evaluations,
    )

    assert len(results) == 2
    assert results[0]["verdict"] == "PASS"
    assert results[1]["verdict"] == "PASS"