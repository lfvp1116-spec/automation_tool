from pathlib import Path

from src.conditional_macro_parser import (
    extract_conditional_macro_definitions,
)
from src.conditional_macro_resolution import (
    evaluate_conditional_macro_definitions,
    group_conditional_definitions_by_macro,
    select_active_conditional_definitions,
)
from src.macro_indexer import (
    MacroDefinition,
    build_macro_index,
)


def get_project_root() -> Path:
    """
    Returns the root folder of the automation_tool project.
    """

    return Path(__file__).parent.parent


def get_fixture_path() -> Path:
    """
    Returns the conditional macro-definition fixture path.
    """

    return (
        get_project_root()
        / "tests"
        / "fixtures"
        / "conditional_macro_definitions_example.h"
    )


def build_controlled_macro_index() -> dict:
    """
    Creates the configuration values used to evaluate the fixture.

    FEATURE_SELECTOR is STD_OFF, therefore:
    - #if FEATURE_SELECTOR == STD_ON is False
    - #elif defined(FEATURE_FALLBACK) is False
    - #else is active
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
                name="FEATURE_SELECTOR",
                value="STD_OFF",
                source_file="Project_Cfg.h",
                line_number=20,
                source_type="generated_config",
                priority=4,
            ),
            MacroDefinition(
                name="NESTED_SELECTOR",
                value="STD_ON",
                source_file="Project_Cfg.h",
                line_number=21,
                source_type="generated_config",
                priority=4,
            ),
        ]
    )


def test_evaluates_if_elif_else_definition_contexts() -> None:
    definitions = extract_conditional_macro_definitions(
        get_fixture_path()
    )

    evaluated_definitions = (
        evaluate_conditional_macro_definitions(
            definitions=definitions,
            macro_index=build_controlled_macro_index(),
        )
    )

    feature_definitions = [
        definition
        for definition in evaluated_definitions
        if definition["name"] == "FEATURE_STATE"
    ]

    assert len(feature_definitions) == 3

    assert feature_definitions[0]["value"] == "STD_ON"
    assert feature_definitions[0]["context_evaluation"] is False
    assert (
        feature_definitions[0]["context_verdict"]
        == "Inactive definition"
    )

    assert feature_definitions[1]["value"] == "STD_ON"
    assert feature_definitions[1]["context_evaluation"] is False
    assert (
        feature_definitions[1]["context_verdict"]
        == "Inactive definition"
    )

    assert feature_definitions[2]["value"] == "STD_OFF"
    assert feature_definitions[2]["context_evaluation"] is True
    assert (
        feature_definitions[2]["context_verdict"]
        == "Active definition"
    )


def test_selects_only_active_definition_from_else_branch() -> None:
    definitions = extract_conditional_macro_definitions(
        get_fixture_path()
    )

    evaluated_definitions = (
        evaluate_conditional_macro_definitions(
            definitions=definitions,
            macro_index=build_controlled_macro_index(),
        )
    )

    active_definitions = (
        select_active_conditional_definitions(
            evaluated_definitions
        )
    )

    active_feature_definitions = [
        definition
        for definition in active_definitions
        if definition["name"] == "FEATURE_STATE"
    ]

    assert len(active_feature_definitions) == 1
    assert active_feature_definitions[0]["value"] == "STD_OFF"
    assert (
        active_feature_definitions[0]["context_evaluation"]
        is True
    )


def test_evaluates_nested_definition_context() -> None:
    definitions = extract_conditional_macro_definitions(
        get_fixture_path()
    )

    evaluated_definitions = (
        evaluate_conditional_macro_definitions(
            definitions=definitions,
            macro_index=build_controlled_macro_index(),
        )
    )

    nested_definitions = [
        definition
        for definition in evaluated_definitions
        if definition["name"] == "NESTED_FEATURE_STATE"
    ]

    assert len(nested_definitions) == 2

    active_nested_definition = next(
        definition
        for definition in nested_definitions
        if definition["context_evaluation"] is True
    )

    assert active_nested_definition["value"] == "STD_ON"
    assert (
        active_nested_definition["context_verdict"]
        == "Active definition"
    )


def test_groups_conditional_definitions_by_macro_name() -> None:
    definitions = extract_conditional_macro_definitions(
        get_fixture_path()
    )

    evaluated_definitions = (
        evaluate_conditional_macro_definitions(
            definitions=definitions,
            macro_index=build_controlled_macro_index(),
        )
    )

    grouped_definitions = (
        group_conditional_definitions_by_macro(
            evaluated_definitions
        )
    )

    assert "FEATURE_STATE" in grouped_definitions
    assert len(grouped_definitions["FEATURE_STATE"]) == 3

    assert "NESTED_FEATURE_STATE" in grouped_definitions
    assert len(
        grouped_definitions["NESTED_FEATURE_STATE"]
    ) == 2