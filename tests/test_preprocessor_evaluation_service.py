from src.macro_indexer import (
    MacroDefinition,
    build_macro_index,
)
from src.preprocessor_evaluation_service import (
    evaluate_relevant_preprocessor_conditions,
)


def build_controlled_macro_index() -> dict:
    """
    Creates a controlled macro index for service tests.
    """

    return build_macro_index(
        [
            MacroDefinition(
                name="STD_OFF",
                value="0u",
                source_file="Std_Types.h",
                line_number=10,
                source_type="header",
                priority=1,
            ),
            MacroDefinition(
                name="STD_ON",
                value="1u",
                source_file="Std_Types.h",
                line_number=11,
                source_type="header",
                priority=1,
            ),
            MacroDefinition(
                name="FEATURE_ENABLED",
                value="STD_ON",
                source_file="Project_Cfg.h",
                line_number=20,
                source_type="generated_config",
                priority=4,
            ),
            MacroDefinition(
                name="FEATURE_DISABLED",
                value="STD_OFF",
                source_file="Project_Cfg.h",
                line_number=21,
                source_type="generated_config",
                priority=4,
            ),
        ]
    )


def test_evaluates_relevant_if_condition() -> None:
    findings = [
        {
            "path": "src/Example.c",
            "file_name": "Example.c",
            "line_number": 10,
            "directive": "#if",
            "expression": (
                "FEATURE_ENABLED == STD_ON"
            ),
            "category": "FEATURE",
            "is_relevant": True,
        }
    ]

    results = evaluate_relevant_preprocessor_conditions(
        findings=findings,
        macro_index=build_controlled_macro_index(),
    )

    assert len(results) == 1

    result = results[0]

    assert result["source_file"] == "src/Example.c"
    assert result["line_number"] == 10
    assert result["directive"] == "#if"
    assert result["category"] == "FEATURE"

    assert (
        result["original_expression"]
        == "FEATURE_ENABLED == STD_ON"
    )

    assert (
        result["evaluation_expression"]
        == "FEATURE_ENABLED == STD_ON"
    )

    assert result["evaluation"] is True
    assert result["verdict"] == "Active branch"
    assert result["evaluation_status"] == "Evaluated"


def test_evaluates_relevant_ifdef_condition() -> None:
    findings = [
        {
            "path": "src/Example.h",
            "file_name": "Example.h",
            "line_number": 20,
            "directive": "#ifdef",
            "expression": "FEATURE_ENABLED",
            "category": "FEATURE",
            "is_relevant": True,
        }
    ]

    results = evaluate_relevant_preprocessor_conditions(
        findings=findings,
        macro_index=build_controlled_macro_index(),
    )

    result = results[0]

    assert (
        result["evaluation_expression"]
        == "defined(FEATURE_ENABLED)"
    )

    assert result["evaluation"] is True
    assert result["verdict"] == "Active branch"


def test_evaluates_relevant_ifndef_condition() -> None:
    findings = [
        {
            "path": "src/Example.h",
            "file_name": "Example.h",
            "line_number": 30,
            "directive": "#ifndef",
            "expression": "FEATURE_DISABLED",
            "category": "FEATURE",
            "is_relevant": True,
        }
    ]

    results = evaluate_relevant_preprocessor_conditions(
        findings=findings,
        macro_index=build_controlled_macro_index(),
    )

    result = results[0]

    assert (
        result["evaluation_expression"]
        == "!defined(FEATURE_DISABLED)"
    )

    assert result["evaluation"] is False
    assert result["verdict"] == "Inactive branch"


def test_ignores_non_relevant_conditions() -> None:
    findings = [
        {
            "path": "src/Example.h",
            "file_name": "Example.h",
            "line_number": 1,
            "directive": "#ifndef",
            "expression": "EXAMPLE_H",
            "category": "OTHER",
            "is_relevant": False,
        }
    ]

    results = evaluate_relevant_preprocessor_conditions(
        findings=findings,
        macro_index=build_controlled_macro_index(),
    )

    assert results == []