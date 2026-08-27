from pathlib import Path

from src.conditional_macro_parser import (
    extract_conditional_macro_definitions,
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


def test_extracts_unconditional_macro_definition() -> None:
    definitions = extract_conditional_macro_definitions(
        get_fixture_path()
    )

    std_on_definition = next(
        definition
        for definition in definitions
        if definition.name == "STD_ON"
    )

    assert std_on_definition.value == "1u"
    assert std_on_definition.conditional_context is None


def test_extracts_if_else_macro_definitions_with_context() -> None:
    definitions = extract_conditional_macro_definitions(
        get_fixture_path()
    )

    feature_definitions = [
        definition
        for definition in definitions
        if definition.name == "FEATURE_STATE"
    ]

    assert len(feature_definitions) == 3

    if_definition = feature_definitions[0]
    elif_definition = feature_definitions[1]
    else_definition = feature_definitions[2]

    assert if_definition.value == "STD_ON"

    assert (
    "FEATURE_SELECTOR == STD_ON"
    in if_definition.conditional_context
    )

    assert elif_definition.value == "STD_ON"

    assert (
        "FEATURE_SELECTOR == STD_ON"
        in elif_definition.conditional_context
    )

    assert (
        "defined(FEATURE_FALLBACK)"
        in elif_definition.conditional_context
    )

    assert else_definition.value == "STD_OFF"

    assert (
        "FEATURE_SELECTOR == STD_ON"
        in else_definition.conditional_context
    )

    assert (
        "defined(FEATURE_FALLBACK)"
        in else_definition.conditional_context
    )

    assert "!" in else_definition.conditional_context


def test_extracts_nested_conditional_context() -> None:
    definitions = extract_conditional_macro_definitions(
        get_fixture_path()
    )

    nested_definition = next(
        definition
        for definition in definitions
        if (
            definition.name
            == "NESTED_FEATURE_STATE"
        )
        and definition.value == "STD_ON"
    )

    context = nested_definition.conditional_context

    assert "defined(NESTED_SELECTOR)" in context

    assert (
        "FEATURE_SELECTOR == STD_OFF"
        in context
    )

    assert "&&" in context


def test_ignores_function_like_macro_definition() -> None:
    definitions = extract_conditional_macro_definitions(
        get_fixture_path()
    )

    definition_names = {
        definition.name
        for definition in definitions
    }

    assert "FUNCTION_MACRO" not in definition_names

def test_ignores_outer_header_guard_context(
    tmp_path: Path,
) -> None:
    fixture_path = tmp_path / "HeaderGuardExample.h"

    fixture_path.write_text(
        """
#ifndef HEADER_GUARD_EXAMPLE_H
#define HEADER_GUARD_EXAMPLE_H

#if (FEATURE_SELECTOR == STD_ON)
# define FEATURE_STATE STD_ON
#else
# define FEATURE_STATE STD_OFF
#endif

#endif
""".strip(),
        encoding="utf-8",
    )

    definitions = extract_conditional_macro_definitions(
        fixture_path
    )

    feature_definitions = [
        definition
        for definition in definitions
        if definition.name == "FEATURE_STATE"
    ]

    assert len(feature_definitions) == 2

    assert (
        "HEADER_GUARD_EXAMPLE_H"
        not in feature_definitions[0].conditional_context
    )

    assert (
        "HEADER_GUARD_EXAMPLE_H"
        not in feature_definitions[1].conditional_context
    )