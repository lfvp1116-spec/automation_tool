from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable

from src.conditional_macro_parser import (
    ConditionalMacroDefinition,
    extract_conditional_macro_definitions,
)
from src.conditional_macro_resolution import (
    evaluate_conditional_macro_definitions,
)
from src.macro_indexer import (
    MacroDefinition,
    build_macro_index,
)


CONDITIONAL_DEFINITION_PRIORITY = 5


def create_active_conditional_macro_records(
    definitions: Iterable[ConditionalMacroDefinition],
    macro_index: dict[str, dict[str, Any]],
    source_type: str = "conditional_definition",
    priority: int = CONDITIONAL_DEFINITION_PRIORITY,
) -> list[MacroDefinition]:
    """
    Evaluates conditional macro definitions and converts only active
    definitions into MacroDefinition records.

    A conditional definition is selected only when its #if, #elif,
    or #else context evaluates to True.

    Definitions without a conditional context are ignored here because
    they are already handled by macro_indexer.py.
    """

    evaluated_definitions = (
        evaluate_conditional_macro_definitions(
            definitions=definitions,
            macro_index=macro_index,
        )
    )

    active_records: list[MacroDefinition] = []

    for definition in evaluated_definitions:
        if definition.get("conditional_context") is None:
            continue

        if definition.get("context_evaluation") is not True:
            continue

        active_records.append(
            MacroDefinition(
                name=str(definition["name"]),
                value=str(definition["value"]),
                source_file=str(definition["source_file"]),
                line_number=int(definition["line_number"]),
                source_type=source_type,
                priority=priority,
                conditional_context=definition.get(
                    "conditional_context"
                ),
                resolved_conditional_context=definition.get(
                    "resolved_context"
                ),
                conditional_context_evaluation=definition.get(
                    "context_evaluation"
                ),
                conditional_selection_reason=(
                    "Conditional branch evaluated as active"
                ),
            )
        )

    return active_records


def build_active_conditional_macro_index(
    source_files: Iterable[str | Path],
    base_macro_index: dict[str, dict[str, Any]],
    source_type: str = "conditional_definition",
    priority: int = CONDITIONAL_DEFINITION_PRIORITY,
) -> dict[str, dict[str, Any]]:
    """
    Builds an index containing active conditional macro definitions
    from multiple source/header files.

    The supplied base_macro_index provides the configuration macros
    required to evaluate the conditional contexts.
    """

    active_records: list[MacroDefinition] = []

    for source_file in source_files:
        definitions = extract_conditional_macro_definitions(
            source_file_path=source_file,
        )

        active_records.extend(
            create_active_conditional_macro_records(
                definitions=definitions,
                macro_index=base_macro_index,
                source_type=source_type,
                priority=priority,
            )
        )

    return build_macro_index(active_records)


def get_active_definition_details(
    definitions: Iterable[ConditionalMacroDefinition],
    macro_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Returns evaluated conditional-definition evidence for reporting
    or debugging purposes.

    This function is not yet connected to Excel; it helps validate
    which branch was selected and why.
    """

    return [
        asdict(definition)
        for definition in evaluate_conditional_macro_definitions(
            definitions=definitions,
            macro_index=macro_index,
        )
    ]

def merge_macro_index_with_active_conditional_definitions(
    base_macro_index: dict[str, dict[str, Any]],
    active_conditional_records: Iterable[MacroDefinition],
) -> dict[str, dict[str, Any]]:
    """
    Builds a new macro index containing all base definitions plus the
    definitions selected from active conditional branches.

    Active conditional records normally have a higher priority than
    regular project-source records. Therefore, a value selected from:

        #if CONDITION
        # define MACRO VALUE_A
        #else
        # define MACRO VALUE_B
        #endif

    becomes the effective definition when CONDITION can be evaluated.
    """

def merge_macro_index_with_active_conditional_definitions(
    base_macro_index: dict[str, dict[str, Any]],
    active_conditional_records: Iterable[MacroDefinition],
) -> dict[str, dict[str, Any]]:
    """
    Builds a new macro index containing all base definitions plus the
    definitions selected from active conditional branches.

    Active conditional records have a higher priority than ordinary
    project-source definitions, so an active #if/#else branch can
    become the effective macro definition.
    """

    combined_records: list[MacroDefinition] = []

    for macro_entry in base_macro_index.values():
        for definition_data in macro_entry["definitions"]:
            combined_records.append(
                MacroDefinition(
                    name=str(definition_data["name"]),
                    value=str(definition_data["value"]),
                    source_file=str(
                        definition_data["source_file"]
                    ),
                    line_number=int(
                        definition_data["line_number"]
                    ),
                    source_type=str(
                        definition_data["source_type"]
                    ),
                    priority=int(
                        definition_data["priority"]
                    ),
                    conditional_context=definition_data.get(
                        "conditional_context"
                    ),
                    resolved_conditional_context=(
                        definition_data.get(
                            "resolved_conditional_context"
                        )
                    ),
                    conditional_context_evaluation=(
                        definition_data.get(
                            "conditional_context_evaluation"
                        )
                    ),
                    conditional_selection_reason=str(
                        definition_data.get(
                            "conditional_selection_reason",
                            "",
                        )
                    ),
                )
            )

    combined_records.extend(
        active_conditional_records
    )

    return build_macro_index(
        combined_records
    )