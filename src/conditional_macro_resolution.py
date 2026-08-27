from dataclasses import asdict
from typing import Any, Iterable

from src.conditional_macro_parser import (
    ConditionalMacroDefinition,
)
from src.preprocessor_expression_evaluator import (
    evaluate_preprocessor_expression,
)


def evaluate_conditional_macro_definitions(
    definitions: Iterable[ConditionalMacroDefinition],
    macro_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Evaluates the conditional context of every extracted macro
    definition.

    A definition without conditional context is considered active.

    The result preserves the original definition evidence and adds:
    - conditional context
    - context evaluation
    - selection status
    """

    evaluated_definitions: list[dict[str, Any]] = []

    for definition in definitions:
        definition_data = asdict(definition)

        context = definition.conditional_context

        if context is None:
            evaluated_definitions.append(
                {
                    **definition_data,
                    "context_evaluation": True,
                    "context_verdict": "Active definition",
                    "context_status": "No conditional context",
                    "context_error_message": "",
                }
            )
            continue

        evaluation = evaluate_preprocessor_expression(
            expression=context,
            macro_index=macro_index,
        )

        context_evaluation = evaluation["evaluation"]

        if context_evaluation is True:
            context_verdict = "Active definition"
        elif context_evaluation is False:
            context_verdict = "Inactive definition"
        else:
            context_verdict = "Unresolved definition context"

        evaluated_definitions.append(
            {
                **definition_data,
                "context_evaluation": context_evaluation,
                "context_verdict": context_verdict,
                "context_status": evaluation[
                    "evaluation_status"
                ],
                "context_error_message": evaluation[
                    "error_message"
                ],
                "resolved_context": evaluation[
                    "resolved_expression"
                ],
            }
        )

    return evaluated_definitions


def select_active_conditional_definitions(
    evaluated_definitions: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Returns only definitions whose conditional context is active.

    Definitions with an unresolved context are retained separately
    by callers, but are not selected as active definitions.
    """

    return [
        definition
        for definition in evaluated_definitions
        if definition.get("context_evaluation") is True
    ]


def group_conditional_definitions_by_macro(
    evaluated_definitions: Iterable[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """
    Groups conditional definition records by macro name.

    This helps identify whether exactly one branch became active,
    multiple definitions remain active, or the context is unresolved.
    """

    grouped_definitions: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for definition in evaluated_definitions:
        macro_name = str(definition["name"])

        grouped_definitions.setdefault(
            macro_name,
            [],
        ).append(definition)

    return grouped_definitions