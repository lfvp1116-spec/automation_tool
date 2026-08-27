from src.macro_indexer import (
    MacroDefinition,
    build_macro_index,
)

from src.macro_resolution_service import (
    resolve_macro_with_evidence,
    resolve_relevant_macros,
)

from src.macro_resolution_service import (
    resolve_macro_with_evidence,
    resolve_relevant_macros,
)

def test_resolves_enabled_alias_with_evidence() -> None:
    macro_index = build_macro_index(
        [
            MacroDefinition(
                name="STD_ON",
                value="1",
                source_file="Std_Types.h",
                line_number=20,
                source_type="header",
                priority=1,
            ),
            MacroDefinition(
                name="FEATURE_X",
                value="STD_ON",
                source_file="Project_Cfg.h",
                line_number=45,
                source_type="generated_config",
                priority=4,
            ),
        ]
    )

    result = resolve_macro_with_evidence(
        macro_name="FEATURE_X",
        macro_index=macro_index,
    )

    assert result["requested_macro"] == "FEATURE_X"
    assert result["resolved_value"] == "1"
    assert result["effective_state"] == "Enabled"
    assert result["resolution_status"] == "Resolved"

    assert result["resolution_chain"] == [
        "FEATURE_X",
        "STD_ON",
    ]

    assert (
        result["resolution_chain_text"]
        == "FEATURE_X -> STD_ON -> 1"
    )

    assert result["definition_source"] == "Std_Types.h"
    assert result["definition_line"] == 20
    assert result["definition_source_type"] == "header"
    assert result["definition_priority"] == 1

    assert (
        result["primary_definition_source"]
        == "Project_Cfg.h"
    )
    assert result["primary_definition_line"] == 45

    assert (
        result["primary_definition_source_type"]
        == "generated_config"
    )
    assert result["primary_definition_priority"] == 4

    assert (
        result["terminal_definition_source"]
        == "Std_Types.h"
    )
    assert result["terminal_definition_line"] == 20
    assert result["terminal_definition_source_type"] == "header"
    assert result["terminal_definition_priority"] == 1


def test_resolves_disabled_alias_with_evidence() -> None:
    macro_index = build_macro_index(
        [
            MacroDefinition(
                name="STD_OFF",
                value="0",
                source_file="Std_Types.h",
                line_number=21,
                source_type="header",
                priority=1,
            ),
            MacroDefinition(
                name="FEATURE_X",
                value="STD_OFF",
                source_file="Project_Cfg.h",
                line_number=60,
                source_type="generated_config",
                priority=4,
            ),
        ]
    )

    result = resolve_macro_with_evidence(
        macro_name="FEATURE_X",
        macro_index=macro_index,
    )

    assert result["resolved_value"] == "0"
    assert result["effective_state"] == "Disabled"
    assert result["resolution_status"] == "Resolved"
    assert result["definition_source"] == "Std_Types.h"


def test_marks_literal_value_as_defined() -> None:
    macro_index = build_macro_index(
        [
            MacroDefinition(
                name="NVM_API_CONFIG_CLASS",
                value="2",
                source_file="NvM_Cfg.h",
                line_number=100,
                source_type="generated_config",
                priority=4,
            ),
        ]
    )

    result = resolve_macro_with_evidence(
        macro_name="NVM_API_CONFIG_CLASS",
        macro_index=macro_index,
    )

    assert result["resolved_value"] == "2"
    assert result["effective_state"] == "Defined"

    assert (
        result["resolution_status"]
        == "Resolved literal value"
    )

    assert (
        result["resolution_chain_text"]
        == "NVM_API_CONFIG_CLASS -> 2"
    )

    assert result["definition_source"] == "NvM_Cfg.h"
    assert result["definition_line"] == 100


def test_marks_unknown_macro_as_unresolved() -> None:
    result = resolve_macro_with_evidence(
        macro_name="UNKNOWN_FEATURE",
        macro_index={},
    )

    assert result["resolved_value"] is None
    assert result["effective_state"] == "Unresolved"

    assert (
        result["resolution_status"]
        == "Unresolved: definition not found"
    )

    assert result["definition_source"] is None
    assert result["definition_line"] is None


def test_marks_missing_alias_definition_as_unresolved() -> None:
    macro_index = build_macro_index(
        [
            MacroDefinition(
                name="FEATURE_X",
                value="EXTERNAL_ALIAS",
                source_file="Project_Cfg.h",
                line_number=70,
                source_type="generated_config",
                priority=4,
            ),
        ]
    )

    result = resolve_macro_with_evidence(
        macro_name="FEATURE_X",
        macro_index=macro_index,
    )

    assert result["resolved_value"] == "EXTERNAL_ALIAS"
    assert result["effective_state"] == "Unresolved"

    assert (
        result["resolution_status"]
        == "Unresolved: alias definition not found"
    )

    assert (
        result["resolution_chain_text"]
        == "FEATURE_X -> EXTERNAL_ALIAS"
    )

    assert result["definition_source"] == "Project_Cfg.h"
    assert result["definition_line"] == 70


def test_detects_cycle_with_evidence() -> None:
    macro_index = build_macro_index(
        [
            MacroDefinition(
                name="CYCLE_A",
                value="CYCLE_B",
                source_file="Cycle.h",
                line_number=10,
                source_type="header",
                priority=1,
            ),
            MacroDefinition(
                name="CYCLE_B",
                value="CYCLE_A",
                source_file="Cycle.h",
                line_number=11,
                source_type="header",
                priority=1,
            ),
        ]
    )

    result = resolve_macro_with_evidence(
        macro_name="CYCLE_A",
        macro_index=macro_index,
    )

    assert result["resolved_value"] is None
    assert result["effective_state"] == "Cycle detected"

    assert (
        result["resolution_status"]
        == "Unresolved: cyclic alias"
    )

    assert result["resolution_chain"] == [
        "CYCLE_A",
        "CYCLE_B",
    ]

    assert (
        result["resolution_chain_text"]
        == "CYCLE_A -> CYCLE_B -> [cycle]"
    )

def test_resolves_and_groups_repeated_relevant_macros() -> None:
    macro_index = build_macro_index(
        [
            MacroDefinition(
                name="STD_ON",
                value="1",
                source_file="Std_Types.h",
                line_number=20,
                source_type="header",
                priority=1,
            ),
            MacroDefinition(
                name="BSWM_ENABLE_CANSM",
                value="STD_ON",
                source_file="BswM_Cfg.h",
                line_number=45,
                source_type="generated_config",
                priority=4,
            ),
        ]
    )

    findings = [
        {
            "path": "src/BswM.c",
            "file_name": "BswM.c",
            "line_number": 10,
            "expression": (
                "BSWM_ENABLE_CANSM == STD_ON"
            ),
            "macros": [
                "BSWM_ENABLE_CANSM",
                "STD_ON",
            ],
            "category": "FEATURE",
            "is_relevant": True,
        },
        {
            "path": "src/BswM.c",
            "file_name": "BswM.c",
            "line_number": 25,
            "expression": (
                "BSWM_ENABLE_CANSM == STD_ON"
            ),
            "macros": [
                "BSWM_ENABLE_CANSM",
                "STD_ON",
            ],
            "category": "FEATURE",
            "is_relevant": True,
        },
        {
            "path": "src/BswM_Cfg.h",
            "file_name": "BswM_Cfg.h",
            "line_number": 40,
            "expression": "BSWM_ENABLE_CANSM",
            "macros": [
                "BSWM_ENABLE_CANSM",
            ],
            "category": "FEATURE",
            "is_relevant": True,
        },
    ]

    results = resolve_relevant_macros(
        findings=findings,
        macro_index=macro_index,
    )

    assert len(results) == 1

    result = results[0]

    assert result["category"] == "FEATURE"
    assert result["primary_macro"] == "BSWM_ENABLE_CANSM"
    assert result["occurrences"] == 3
    assert result["files_affected"] == 2

    assert result["resolved_value"] == "1"
    assert result["effective_state"] == "Enabled"

    assert (
        result["resolution_chain_text"]
        == "BSWM_ENABLE_CANSM -> STD_ON -> 1"
    )

    assert result["definition_source"] == "Std_Types.h"


def test_ignores_non_relevant_findings() -> None:
    findings = [
        {
            "path": "src/Example.h",
            "file_name": "Example.h",
            "line_number": 1,
            "expression": "EXAMPLE_H",
            "macros": ["EXAMPLE_H"],
            "category": "OTHER",
            "is_relevant": False,
        },
    ]

    results = resolve_relevant_macros(
        findings=findings,
        macro_index={},
    )

    assert results == []

def test_marks_unsigned_zero_as_disabled() -> None:
    macro_index = build_macro_index(
        [
            MacroDefinition(
                name="FEATURE_X",
                value="0u",
                source_file="Project_Cfg.h",
                line_number=20,
                source_type="generated_config",
                priority=4,
            ),
        ]
    )

    result = resolve_macro_with_evidence(
        macro_name="FEATURE_X",
        macro_index=macro_index,
    )

    assert result["resolved_value"] == "0u"
    assert result["effective_state"] == "Disabled"
    assert result["resolution_status"] == "Resolved"


def test_marks_unsigned_one_as_enabled() -> None:
    macro_index = build_macro_index(
        [
            MacroDefinition(
                name="FEATURE_X",
                value="1UL",
                source_file="Project_Cfg.h",
                line_number=20,
                source_type="generated_config",
                priority=4,
            ),
        ]
    )

    result = resolve_macro_with_evidence(
        macro_name="FEATURE_X",
        macro_index=macro_index,
    )

    assert result["resolved_value"] == "1UL"
    assert result["effective_state"] == "Enabled"
    assert result["resolution_status"] == "Resolved"


def test_keeps_non_boolean_integer_as_defined() -> None:
    macro_index = build_macro_index(
        [
            MacroDefinition(
                name="NVM_API_CONFIG_CLASS",
                value="2u",
                source_file="NvM_Cfg.h",
                line_number=100,
                source_type="generated_config",
                priority=4,
            ),
        ]
    )

    result = resolve_macro_with_evidence(
        macro_name="NVM_API_CONFIG_CLASS",
        macro_index=macro_index,
    )

    assert result["resolved_value"] == "2u"
    assert result["effective_state"] == "Defined"

    assert (
        result["resolution_status"]
        == "Resolved literal value"
    )

def test_resolves_parenthesized_std_off_as_disabled() -> None:
    macro_index = build_macro_index(
        [
            MacroDefinition(
                name="STD_OFF",
                value="0u",
                source_file="Std_Types.h",
                line_number=21,
                source_type="header",
                priority=1,
            ),
            MacroDefinition(
                name="NVM_CSM_CIPHERING_ENABLED",
                value="(STD_OFF)",
                source_file="NvM_Cfg.h",
                line_number=150,
                source_type="generated_config",
                priority=4,
            ),
        ]
    )

    result = resolve_macro_with_evidence(
        macro_name="NVM_CSM_CIPHERING_ENABLED",
        macro_index=macro_index,
    )

    assert result["resolved_value"] == "0u"
    assert result["effective_state"] == "Disabled"
    assert result["resolution_status"] == "Resolved"

    assert (
        result["resolution_chain_text"]
        == (
            "NVM_CSM_CIPHERING_ENABLED "
            "-> STD_OFF -> 0u"
        )
    )

def test_returns_conditional_definition_evidence() -> None:
    macro_index = build_macro_index(
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
                name="FEATURE_X",
                value="STD_OFF",
                source_file="Project_Cfg.h",
                line_number=40,
                source_type="conditional_definition",
                priority=5,
                conditional_context=(
                    "!(FEATURE_SELECTOR == STD_ON)"
                ),
                resolved_conditional_context=(
                    "!((0u == 1u))"
                ),
                conditional_context_evaluation=True,
                conditional_selection_reason=(
                    "Conditional branch evaluated as active"
                ),
            ),
        ]
    )

    result = resolve_macro_with_evidence(
        macro_name="FEATURE_X",
        macro_index=macro_index,
    )

    assert (
        result["primary_definition_condition"]
        == "!(FEATURE_SELECTOR == STD_ON)"
    )

    assert (
        result[
            "resolved_primary_definition_condition"
        ]
        == "!((0u == 1u))"
    )

    assert (
        result[
            "primary_definition_condition_evaluation"
        ]
        is True
    )

    assert (
        result[
            "primary_definition_selection_reason"
        ]
        == "Conditional branch evaluated as active"
    )