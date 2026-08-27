from src.macro_indexer import (
    MacroDefinition,
    build_macro_index,
)
from src.preprocessor_expression_evaluator import (
    evaluate_preprocessor_expression,
)


def build_controlled_macro_index() -> dict:
    """
    Creates a controlled index for expression-evaluator tests.
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
            MacroDefinition(
                name="BUFFER_SIZE",
                value="3u",
                source_file="Project_Cfg.h",
                line_number=22,
                source_type="generated_config",
                priority=4,
            ),
            MacroDefinition(
                name="MASK_A",
                value="0x01u",
                source_file="Project_Cfg.h",
                line_number=23,
                source_type="generated_config",
                priority=4,
            ),
            MacroDefinition(
                name="MASK_B",
                value="0x04u",
                source_file="Project_Cfg.h",
                line_number=24,
                source_type="generated_config",
                priority=4,
            ),
            MacroDefinition(
                name="MASK_COMBINED",
                value="(MASK_A | MASK_B)",
                source_file="Project_Cfg.h",
                line_number=25,
                source_type="generated_config",
                priority=4,
            ),
            MacroDefinition(
                name="COUNT_A",
                value="1u",
                source_file="Project_Cfg.h",
                line_number=26,
                source_type="generated_config",
                priority=4,
            ),
            MacroDefinition(
                name="COUNT_B",
                value="2u",
                source_file="Project_Cfg.h",
                line_number=27,
                source_type="generated_config",
                priority=4,
            ),
        ]
    )


def test_evaluates_equal_enabled_condition() -> None:
    result = evaluate_preprocessor_expression(
        expression=(
            "FEATURE_ENABLED == STD_ON"
        ),
        macro_index=build_controlled_macro_index(),
    )

    assert result["evaluation"] is True
    assert result["verdict"] == "Active branch"
    assert result["evaluation_status"] == "Evaluated"

    assert (
        result["resolved_expression"]
        == "(1u == 1u)"
    )

    assert result["referenced_macros"] == [
        "FEATURE_ENABLED",
        "STD_ON",
    ]


def test_evaluates_not_equal_disabled_condition() -> None:
    result = evaluate_preprocessor_expression(
        expression=(
            "FEATURE_DISABLED != STD_ON"
        ),
        macro_index=build_controlled_macro_index(),
    )

    assert result["evaluation"] is True
    assert result["verdict"] == "Active branch"

    assert (
        result["resolved_expression"]
        == "(0u != 1u)"
    )


def test_evaluates_defined_expression() -> None:
    result = evaluate_preprocessor_expression(
        expression="defined(FEATURE_ENABLED)",
        macro_index=build_controlled_macro_index(),
    )

    assert result["evaluation"] is True
    assert result["verdict"] == "Active branch"

    assert (
        result["resolved_expression"]
        == "defined(FEATURE_ENABLED)=1"
    )

    assert result["referenced_macros"] == [
        "FEATURE_ENABLED",
    ]


def test_evaluates_negated_defined_expression() -> None:
    result = evaluate_preprocessor_expression(
        expression="!defined(MISSING_FEATURE)",
        macro_index=build_controlled_macro_index(),
    )

    assert result["evaluation"] is True
    assert result["verdict"] == "Active branch"

    assert (
        result["resolved_expression"]
        == "!(defined(MISSING_FEATURE)=0)"
    )


def test_evaluates_and_expression() -> None:
    result = evaluate_preprocessor_expression(
        expression=(
            "(FEATURE_ENABLED == STD_ON) && "
            "(FEATURE_DISABLED == STD_OFF)"
        ),
        macro_index=build_controlled_macro_index(),
    )

    assert result["evaluation"] is True
    assert result["verdict"] == "Active branch"


def test_evaluates_or_expression() -> None:
    result = evaluate_preprocessor_expression(
        expression=(
            "(FEATURE_DISABLED == STD_ON) || "
            "(FEATURE_ENABLED == STD_ON)"
        ),
        macro_index=build_controlled_macro_index(),
    )

    assert result["evaluation"] is True
    assert result["verdict"] == "Active branch"


def test_evaluates_relational_expression() -> None:
    result = evaluate_preprocessor_expression(
        expression="BUFFER_SIZE > 0",
        macro_index=build_controlled_macro_index(),
    )

    assert result["evaluation"] is True
    assert result["verdict"] == "Active branch"

    assert (
        result["resolved_expression"]
        == "(3u > 0)"
    )


def test_marks_missing_macro_as_unresolved() -> None:
    result = evaluate_preprocessor_expression(
        expression="UNKNOWN_FEATURE == STD_ON",
        macro_index=build_controlled_macro_index(),
    )

    assert result["evaluation"] is None
    assert result["verdict"] == "Unresolved expression"
    assert result["evaluation_status"] == "Unresolved"

    assert (
        result["error_message"]
        == "Macro definition not found: UNKNOWN_FEATURE"
    )


def test_rejects_unsupported_multiplication_expression() -> None:
    result = evaluate_preprocessor_expression(
        expression="BUFFER_SIZE * 2 > 0",
        macro_index=build_controlled_macro_index(),
    )

    assert result["evaluation"] is None
    assert result["verdict"] == "Unresolved expression"

    assert (
        "Unsupported expression content near:"
        in result["error_message"]
    )

def test_evaluates_bitwise_or_macro_expression() -> None:
    result = evaluate_preprocessor_expression(
        expression="MASK_COMBINED == 0x05u",
        macro_index=build_controlled_macro_index(),
    )

    assert result["evaluation"] is True
    assert result["verdict"] == "Active branch"

    assert (
    result["resolved_expression"]
    == "((0x01u | 0x04u) == 0x05u)"
    )


def test_evaluates_bitwise_and_expression() -> None:
    result = evaluate_preprocessor_expression(
        expression="(MASK_COMBINED & MASK_B) != 0u",
        macro_index=build_controlled_macro_index(),
    )

    assert result["evaluation"] is True
    assert result["verdict"] == "Active branch"

    resolved_expression = result["resolved_expression"]

    assert "0x01u | 0x04u" in resolved_expression
    assert "& 0x04u" in resolved_expression
    assert "!= 0u" in resolved_expression


def test_evaluates_additive_expression() -> None:
    result = evaluate_preprocessor_expression(
        expression="COUNT_A + COUNT_B == 3u",
        macro_index=build_controlled_macro_index(),
    )

    assert result["evaluation"] is True
    assert result["verdict"] == "Active branch"

    assert (
        result["resolved_expression"]
        == "((1u + 2u) == 3u)"
    )