from pathlib import Path

from src.conditional_macro_indexer import (
    CONDITIONAL_DEFINITION_PRIORITY,
    build_active_conditional_macro_index,
    create_active_conditional_macro_records,
    merge_macro_index_with_active_conditional_definitions,
)

from src.conditional_macro_parser import (
    extract_conditional_macro_definitions,
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
    Creates values that determine the active conditional branches.

    FEATURE_SELECTOR is STD_OFF:
    - FEATURE_STATE #if branch is inactive.
    - FEATURE_STATE #elif branch is inactive.
    - FEATURE_STATE #else branch is active.

    NESTED_SELECTOR is defined:
    - The outer nested branch is active.
    - FEATURE_SELECTOR == STD_OFF is true.
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


def test_creates_record_only_for_active_else_definition() -> None:
    definitions = extract_conditional_macro_definitions(
        get_fixture_path()
    )

    records = create_active_conditional_macro_records(
        definitions=definitions,
        macro_index=build_controlled_macro_index(),
    )

    feature_records = [
        record
        for record in records
        if record.name == "FEATURE_STATE"
    ]

    assert len(feature_records) == 1

    active_record = feature_records[0]

    assert active_record.value == "STD_OFF"
    assert (
        active_record.source_file
        == str(get_fixture_path())
    )
    assert active_record.source_type == (
        "conditional_definition"
    )
    assert active_record.priority == (
        CONDITIONAL_DEFINITION_PRIORITY
    )


def test_creates_record_for_active_nested_definition() -> None:
    definitions = extract_conditional_macro_definitions(
        get_fixture_path()
    )

    records = create_active_conditional_macro_records(
        definitions=definitions,
        macro_index=build_controlled_macro_index(),
    )

    nested_records = [
        record
        for record in records
        if record.name == "NESTED_FEATURE_STATE"
    ]

    assert len(nested_records) == 1
    assert nested_records[0].value == "STD_ON"


def test_builds_index_from_active_conditional_definitions() -> None:
    conditional_index = build_active_conditional_macro_index(
        source_files=[get_fixture_path()],
        base_macro_index=build_controlled_macro_index(),
    )

    feature_definition = conditional_index[
        "FEATURE_STATE"
    ]["effective_definition"]

    assert feature_definition["value"] == "STD_OFF"

    assert (
        feature_definition["source_type"]
        == "conditional_definition"
    )

    assert (
        feature_definition["priority"]
        == CONDITIONAL_DEFINITION_PRIORITY
    )

    nested_definition = conditional_index[
        "NESTED_FEATURE_STATE"
    ]["effective_definition"]

    assert nested_definition["value"] == "STD_ON"

def test_active_conditional_definition_overrides_base_index() -> None:
    definitions = extract_conditional_macro_definitions(
        get_fixture_path()
    )

    base_macro_index = build_controlled_macro_index()

    active_records = create_active_conditional_macro_records(
        definitions=definitions,
        macro_index=base_macro_index,
    )

    final_macro_index = (
        merge_macro_index_with_active_conditional_definitions(
            base_macro_index=base_macro_index,
            active_conditional_records=active_records,
        )
    )

    effective_definition = final_macro_index[
        "FEATURE_STATE"
    ]["effective_definition"]

    assert effective_definition["value"] == "STD_OFF"

    assert (
        effective_definition["source_type"]
        == "conditional_definition"
    )

    assert (
        effective_definition["priority"]
        == CONDITIONAL_DEFINITION_PRIORITY
    )


def test_keeps_base_definitions_when_no_conditional_override_exists(
) -> None:
    base_macro_index = build_controlled_macro_index()

    final_macro_index = (
        merge_macro_index_with_active_conditional_definitions(
            base_macro_index=base_macro_index,
            active_conditional_records=[],
        )
    )

    effective_definition = final_macro_index[
        "FEATURE_SELECTOR"
    ]["effective_definition"]

    assert effective_definition["value"] == "STD_OFF"
    assert effective_definition["source_file"] == "Project_Cfg.h"
    assert effective_definition["source_type"] == "generated_config"

def test_active_record_preserves_conditional_evidence() -> None:
    definitions = extract_conditional_macro_definitions(
        get_fixture_path()
    )

    records = create_active_conditional_macro_records(
        definitions=definitions,
        macro_index=build_controlled_macro_index(),
    )

    feature_record = next(
        record
        for record in records
        if record.name == "FEATURE_STATE"
    )

    assert feature_record.value == "STD_OFF"

    assert feature_record.conditional_context is not None

    assert (
        "FEATURE_SELECTOR == STD_ON"
        in feature_record.conditional_context
    )

    assert (
        feature_record.conditional_context_evaluation
        is True
    )

    assert (
        feature_record.conditional_selection_reason
        == "Conditional branch evaluated as active"
    )

def test_merged_index_preserves_conditional_evidence() -> None:
    definitions = extract_conditional_macro_definitions(
        get_fixture_path()
    )

    base_macro_index = build_controlled_macro_index()

    active_records = create_active_conditional_macro_records(
        definitions=definitions,
        macro_index=base_macro_index,
    )

    final_macro_index = (
        merge_macro_index_with_active_conditional_definitions(
            base_macro_index=base_macro_index,
            active_conditional_records=active_records,
        )
    )

    effective_definition = final_macro_index[
        "FEATURE_STATE"
    ]["effective_definition"]

    assert (
        effective_definition["conditional_context"]
        is not None
    )

    assert (
        "FEATURE_SELECTOR == STD_ON"
        in effective_definition["conditional_context"]
    )

    assert (
        effective_definition[
            "conditional_context_evaluation"
        ]
        is True
    )

    assert (
        effective_definition[
            "conditional_selection_reason"
        ]
        == "Conditional branch evaluated as active"
    )