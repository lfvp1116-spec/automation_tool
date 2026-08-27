from typing import Any, Iterable
import re

from src.macro_indexer import (
    get_effective_macro_definitions,
    get_macro_definition_evidence,
)
from src.macro_resolver import resolve_macro_alias


IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z_]\w*$"
)

C_INTEGER_LITERAL_PATTERN = re.compile(
    r"^(0[xX][0-9A-Fa-f]+|\d+)([uUlL]*)$"
)

C_NUMERIC_SUFFIX_PATTERN = re.compile(
    r"[uUlL]+$"
)

ENABLED_VALUES = {
    "1",
    "TRUE",
    "STD_ON",
    "ON",
    "ENABLE",
    "ENABLED",
}

DISABLED_VALUES = {
    "0",
    "FALSE",
    "STD_OFF",
    "OFF",
    "DISABLE",
    "DISABLED",
}


def resolve_macro_with_evidence(
    macro_name: str,
    macro_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    Resolves one macro through aliases and returns the effective state,
    resolution chain, primary-definition evidence, and terminal-value
    definition evidence.

    Primary definition:
        Definition of the requested macro.

    Terminal definition:
        Definition of the final macro in the resolution chain, such as
        STD_ON or STD_OFF.
    """

    effective_definitions = get_effective_macro_definitions(
        macro_index
    )

    resolution = resolve_macro_alias(
        macro_name=macro_name,
        definitions=effective_definitions,
    )

    resolution_chain = list(
        resolution["resolution_chain"]
    )

    primary_definition_evidence = (
        get_macro_definition_evidence(
            macro_name=macro_name,
            macro_index=macro_index,
        )
    )

    terminal_macro = _get_terminal_macro(
        resolution_chain=resolution_chain,
    )

    terminal_definition_evidence = None

    if terminal_macro:
        terminal_definition_evidence = (
            get_macro_definition_evidence(
                macro_name=terminal_macro,
                macro_index=macro_index,
            )
        )

    resolved_value = resolution["resolved_value"]

    effective_state, resolution_status = (
        _get_effective_state(
            resolved_value=resolved_value,
            is_resolved=bool(
                resolution["is_resolved"]
            ),
            has_cycle=bool(
                resolution["has_cycle"]
            ),
        )
    )

    return {
        "requested_macro": macro_name,
        "resolved_value": resolved_value,
        "effective_state": effective_state,
        "resolution_status": resolution_status,
        "resolution_chain": resolution_chain,
        "resolution_chain_text": _format_resolution_chain(
            resolution_chain=resolution_chain,
            resolved_value=resolved_value,
            has_cycle=bool(
                resolution["has_cycle"]
            ),
        ),
        "is_resolved": bool(
            resolution["is_resolved"]
        ),
        "has_cycle": bool(
            resolution["has_cycle"]
        ),

        # Evidence for requested macro.
        "primary_definition_source": _get_evidence_value(
            primary_definition_evidence,
            "source_file",
        ),
        "primary_definition_line": _get_evidence_value(
            primary_definition_evidence,
            "line_number",
        ),
        "primary_definition_source_type": (
            _get_evidence_value(
                primary_definition_evidence,
                "source_type",
            )
        ),
        "primary_definition_priority": _get_evidence_value(
            primary_definition_evidence,
            "priority",
        ),
                "primary_definition_condition": (
            _get_evidence_value(
                primary_definition_evidence,
                "conditional_context",
            )
        ),
        "resolved_primary_definition_condition": (
            _get_evidence_value(
                primary_definition_evidence,
                "resolved_conditional_context",
            )
        ),
        "primary_definition_condition_evaluation": (
            _get_evidence_value(
                primary_definition_evidence,
                "conditional_context_evaluation",
            )
        ),
        "primary_definition_selection_reason": (
            _get_evidence_value(
                primary_definition_evidence,
                "conditional_selection_reason",
            )
        ),

        # Evidence for terminal alias/value macro.
        "terminal_definition_source": _get_evidence_value(
            terminal_definition_evidence,
            "source_file",
        ),
        "terminal_definition_line": _get_evidence_value(
            terminal_definition_evidence,
            "line_number",
        ),
        "terminal_definition_source_type": (
            _get_evidence_value(
                terminal_definition_evidence,
                "source_type",
            )
        ),
        "terminal_definition_priority": _get_evidence_value(
            terminal_definition_evidence,
            "priority",
        ),

        # Compatibility fields retained for existing callers.
        "definition_source": _get_evidence_value(
            terminal_definition_evidence,
            "source_file",
        ),
        "definition_line": _get_evidence_value(
            terminal_definition_evidence,
            "line_number",
        ),
        "definition_source_type": _get_evidence_value(
            terminal_definition_evidence,
            "source_type",
        ),
        "definition_priority": _get_evidence_value(
            terminal_definition_evidence,
            "priority",
        ),
    }


def resolve_relevant_macros(
    findings: Iterable[dict[str, Any]],
    macro_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Resolves every unique relevant macro found in classified
    preprocessor findings.
    """

    grouped_macros: dict[
        tuple[str, str],
        dict[str, Any],
    ] = {}

    for finding in findings:
        if not finding.get("is_relevant", False):
            continue

        category = str(
            finding.get("category", "OTHER")
        )

        primary_macro = _get_primary_macro(
            finding=finding,
        )

        group_key = (
            category,
            primary_macro,
        )

        if group_key not in grouped_macros:
            grouped_macros[group_key] = {
                "category": category,
                "primary_macro": primary_macro,
                "occurrences": 0,
                "source_files": set(),
                "example_expression": str(
                    finding.get("expression", "")
                ),
                "example_source_file": str(
                    finding.get("path", "")
                ),
                "example_line": finding.get(
                    "line_number",
                    "",
                ),
            }

        grouped_macros[group_key]["occurrences"] += 1

        source_file = str(
            finding.get("path", "")
        )

        if source_file:
            grouped_macros[group_key][
                "source_files"
            ].add(source_file)

    resolved_macros: list[dict[str, Any]] = []

    for macro_data in grouped_macros.values():
        resolution = resolve_macro_with_evidence(
            macro_name=macro_data["primary_macro"],
            macro_index=macro_index,
        )

        resolved_macros.append(
            {
                "category": macro_data["category"],
                "primary_macro": macro_data[
                    "primary_macro"
                ],
                "occurrences": macro_data[
                    "occurrences"
                ],
                "files_affected": len(
                    macro_data["source_files"]
                ),
                "example_expression": macro_data[
                    "example_expression"
                ],
                "example_source_file": macro_data[
                    "example_source_file"
                ],
                "example_line": macro_data[
                    "example_line"
                ],
                **resolution,
            }
        )

    return sorted(
        resolved_macros,
        key=lambda item: (
            -int(item["occurrences"]),
            str(item["category"]),
            str(item["primary_macro"]),
        ),
    )


def _get_primary_macro(
    finding: dict[str, Any],
) -> str:
    """
    Returns the first parser macro as the representative switch.
    """

    macros = finding.get("macros", [])

    if isinstance(macros, list) and macros:
        return str(macros[0])

    if isinstance(macros, tuple) and macros:
        return str(macros[0])

    expression = str(
        finding.get("expression", "")
    )

    return expression or "UNRESOLVED_EXPRESSION"


def _get_terminal_macro(
    resolution_chain: list[str],
) -> str | None:
    """
    Returns the final macro visited during alias resolution.
    """

    if not resolution_chain:
        return None

    return resolution_chain[-1]


def _get_effective_state(
    resolved_value: Any,
    is_resolved: bool,
    has_cycle: bool,
) -> tuple[str, str]:
    """
    Converts a raw resolver result into a readable state/status.
    """

    if has_cycle:
        return (
            "Cycle detected",
            "Unresolved: cyclic alias",
        )

    if not is_resolved:
        return (
            "Unresolved",
            "Unresolved: definition not found",
        )

    if resolved_value is None:
        return (
            "Unresolved",
            "Unresolved: no resolved value",
        )

    normalized_value = str(
        resolved_value
    ).strip().upper()

    if normalized_value in ENABLED_VALUES:
        return (
            "Enabled",
            "Resolved",
        )

    if normalized_value in DISABLED_VALUES:
        return (
            "Disabled",
            "Resolved",
        )

    numeric_value = _parse_c_integer_literal(
        value=normalized_value,
    )

    if numeric_value == 1:
        return (
            "Enabled",
            "Resolved",
        )

    if numeric_value == 0:
        return (
            "Disabled",
            "Resolved",
        )

    if IDENTIFIER_PATTERN.fullmatch(
        normalized_value
    ):
        return (
            "Unresolved",
            "Unresolved: alias definition not found",
        )

    return (
        "Defined",
        "Resolved literal value",
    )


def _parse_c_integer_literal(
    value: str,
) -> int | None:
    """
    Parses a simple C integer literal with optional U/L suffixes.
    """

    if not C_INTEGER_LITERAL_PATTERN.fullmatch(
        value
    ):
        return None

    numeric_text = C_NUMERIC_SUFFIX_PATTERN.sub(
        "",
        value,
    )

    try:
        return int(
            numeric_text,
            base=0,
        )
    except ValueError:
        return None


def _format_resolution_chain(
    resolution_chain: list[str],
    resolved_value: Any,
    has_cycle: bool,
) -> str:
    """
    Formats a human-readable macro-resolution chain.
    """

    if not resolution_chain:
        return ""

    chain_parts = list(resolution_chain)

    if has_cycle:
        return " -> ".join(chain_parts) + " -> [cycle]"

    if resolved_value is not None:
        resolved_text = str(resolved_value)

        if (
            not chain_parts
            or chain_parts[-1] != resolved_text
        ):
            chain_parts.append(resolved_text)

    return " -> ".join(chain_parts)


def _get_evidence_value(
    evidence: dict[str, Any] | None,
    key: str,
) -> Any:
    """
    Returns an evidence value or None if no evidence is available.
    """

    if evidence is None:
        return None

    return evidence.get(key)