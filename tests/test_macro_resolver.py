from pathlib import Path

from src.macro_resolver import (
    extract_macro_definitions,
    merge_macro_definitions,
    resolve_macro_alias,
)


def get_project_root() -> Path:
    """
    Returns the root folder of the automation_tool project.
    """

    return Path(__file__).parent.parent


def get_fixture_path() -> Path:
    """
    Returns the controlled macro-definition fixture path.
    """

    return (
        get_project_root()
        / "tests"
        / "fixtures"
        / "macro_definitions_example.h"
    )


def test_extracts_object_like_macro_definitions() -> None:
    definitions = extract_macro_definitions(
        get_fixture_path()
    )

    assert definitions["STD_OFF"] == "0"
    assert definitions["STD_ON"] == "1"

    assert (
        definitions["PROJECT_FEATURE_ENABLED"]
        == "STD_ON"
    )

    assert definitions["EMPTY_SWITCH"] == "1"


def test_ignores_function_like_macro_definitions() -> None:
    definitions = extract_macro_definitions(
        get_fixture_path()
    )

    assert "FUNCTION_LIKE_MACRO" not in definitions


def test_resolves_direct_alias_chain() -> None:
    definitions = extract_macro_definitions(
        get_fixture_path()
    )

    result = resolve_macro_alias(
        macro_name="FEATURE_ALIAS",
        definitions=definitions,
    )

    assert result["is_resolved"] is True
    assert result["has_cycle"] is False
    assert result["resolved_value"] == "1"

    assert result["resolution_chain"] == [
        "FEATURE_ALIAS",
        "PROJECT_FEATURE_ENABLED",
        "STD_ON",
    ]


def test_returns_literal_macro_value() -> None:
    definitions = extract_macro_definitions(
        get_fixture_path()
    )

    result = resolve_macro_alias(
        macro_name="LITERAL_VALUE",
        definitions=definitions,
    )

    assert result["is_resolved"] is True
    assert result["resolved_value"] == "42"

    assert result["resolution_chain"] == [
        "LITERAL_VALUE",
    ]


def test_detects_alias_cycle() -> None:
    definitions = extract_macro_definitions(
        get_fixture_path()
    )

    result = resolve_macro_alias(
        macro_name="CYCLE_A",
        definitions=definitions,
    )

    assert result["is_resolved"] is False
    assert result["has_cycle"] is True

    assert result["resolution_chain"] == [
        "CYCLE_A",
        "CYCLE_B",
    ]


def test_merges_definitions_with_later_values_winning() -> None:
    merged_definitions = merge_macro_definitions(
        [
            {
                "STD_ON": "1",
                "FEATURE_X": "STD_OFF",
            },
            {
                "FEATURE_X": "STD_ON",
            },
        ]
    )

    assert merged_definitions["STD_ON"] == "1"
    assert merged_definitions["FEATURE_X"] == "STD_ON"

def test_resolves_alias_wrapped_in_parentheses() -> None:
    definitions = {
        "STD_ON": "1u",
        "FEATURE_X": "(STD_ON)",
    }

    result = resolve_macro_alias(
        macro_name="FEATURE_X",
        definitions=definitions,
    )

    assert result["is_resolved"] is True
    assert result["has_cycle"] is False
    assert result["resolved_value"] == "1u"

    assert result["resolution_chain"] == [
        "FEATURE_X",
        "STD_ON",
    ]


def test_preserves_complex_expression_with_parentheses() -> None:
    definitions = {
        "FEATURE_X": "(VALUE + 1)",
    }

    result = resolve_macro_alias(
        macro_name="FEATURE_X",
        definitions=definitions,
    )

    assert result["is_resolved"] is True
    assert result["resolved_value"] == "VALUE + 1"

    assert result["resolution_chain"] == [
        "FEATURE_X",
    ]