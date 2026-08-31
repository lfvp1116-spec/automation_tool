from pathlib import Path
from typing import Any

import yaml


VALID_EXPECTED_STATES = {
    "Enabled",
    "Disabled",
    "Defined",
    "Undefined",
}


def load_expected_rules(
    rules_path: str | Path,
) -> list[dict[str, Any]]:
    """
    Loads macro-state and macro-value rules from a YAML file.

    Macro rules are stored under the YAML key:

        rules:
    """

    macro_rules, _ = _load_rule_configuration(
        rules_path
    )

    return macro_rules


def load_expression_rules(
    rules_path: str | Path,
) -> list[dict[str, Any]]:
    """
    Loads preprocessor-expression rules from a YAML file.

    Expression rules are stored under the YAML key:

        expression_rules:
    """

    _, expression_rules = _load_rule_configuration(
        rules_path
    )

    return expression_rules


def _load_rule_configuration(
    rules_path: str | Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Loads, validates, and normalizes the complete YAML rule
    configuration.

    Returns:
        A tuple containing:
        - macro rules;
        - expression rules.
    """

    path = Path(rules_path)

    if not path.exists():
        raise FileNotFoundError(
            "Expected-rules file was not found: "
            f"{path}"
        )

    if not path.is_file():
        raise ValueError(
            "The configured expected-rules path is not a file: "
            f"{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as rules_file:
        configuration = yaml.safe_load(
            rules_file
        )

    if not isinstance(configuration, dict):
        raise ValueError(
            "Expected-rules configuration must contain "
            "a YAML dictionary."
        )

    raw_macro_rules = configuration.get("rules")

    if not isinstance(raw_macro_rules, list):
        raise ValueError(
            "Expected-rules configuration must contain "
            "a 'rules' list."
        )

    raw_expression_rules = configuration.get(
        "expression_rules",
        [],
    )

    if not isinstance(raw_expression_rules, list):
        raise ValueError(
            "'expression_rules' must be a YAML list."
        )

    macro_rules = [
        _validate_macro_rule(
            rule=rule,
            rule_index=index,
        )
        for index, rule in enumerate(
            raw_macro_rules,
            start=1,
        )
    ]

    expression_rules = [
        _validate_expression_rule(
            rule=rule,
            rule_index=index,
        )
        for index, rule in enumerate(
            raw_expression_rules,
            start=1,
        )
    ]

    _validate_unique_rule_ids(
        [
            *macro_rules,
            *expression_rules,
        ]
    )

    return macro_rules, expression_rules


def _validate_macro_rule(
    rule: Any,
    rule_index: int,
) -> dict[str, Any]:
    """
    Validates and normalizes one macro rule.

    A macro rule may define:
    - expected_state; or
    - expected_value; or
    - neither, for NOT_APPLICABLE traceability rules.
    """

    if not isinstance(rule, dict):
        raise ValueError(
            "Each macro rule must be a YAML dictionary. "
            f"Invalid rule index: {rule_index}"
        )

    rule_id = str(
        rule.get("id", "")
    ).strip()

    macro_name = str(
        rule.get("macro", "")
    ).strip()

    description = str(
        rule.get("description", "")
    ).strip()

    expected_state = rule.get(
        "expected_state"
    )

    expected_value = rule.get(
        "expected_value"
    )

    if not rule_id:
        raise ValueError(
            f"Macro rule {rule_index} is missing an 'id'."
        )

    if not macro_name:
        raise ValueError(
            f"Rule {rule_id} is missing a 'macro'."
        )

    if not description:
        raise ValueError(
            f"Rule {rule_id} is missing a description."
        )

    if (
        expected_state is not None
        and expected_value is not None
    ):
        raise ValueError(
            f"Rule {rule_id} cannot define both "
            "expected_state and expected_value."
        )

    if expected_state is not None:
        expected_state = str(
            expected_state
        ).strip()

        if expected_state not in VALID_EXPECTED_STATES:
            raise ValueError(
                f"Rule {rule_id} contains an unsupported "
                f"expected_state: {expected_state}"
            )

    if expected_value is not None:
        expected_value = str(
            expected_value
        ).strip()

        if not expected_value:
            raise ValueError(
                f"Rule {rule_id} contains an empty "
                "expected_value."
            )

    return {
        "id": rule_id,
        "macro": macro_name,
        "expected_state": expected_state,
        "expected_value": expected_value,
        "description": description,
    }


def _validate_expression_rule(
    rule: Any,
    rule_index: int,
) -> dict[str, Any]:
    """
    Validates and normalizes one expression rule.

    Expression rules require:
    - id;
    - expression;
    - expected_result;
    - description.
    """

    if not isinstance(rule, dict):
        raise ValueError(
            "Each expression rule must be a YAML dictionary. "
            f"Invalid rule index: {rule_index}"
        )

    rule_id = str(
        rule.get("id", "")
    ).strip()

    expression = str(
        rule.get("expression", "")
    ).strip()

    description = str(
        rule.get("description", "")
    ).strip()

    expected_result = rule.get(
        "expected_result"
    )

    if not rule_id:
        raise ValueError(
            f"Expression rule {rule_index} is missing an 'id'."
        )

    if not expression:
        raise ValueError(
            f"Rule {rule_id} is missing an 'expression'."
        )

    if not description:
        raise ValueError(
            f"Rule {rule_id} is missing a description."
        )

    if not isinstance(expected_result, bool):
        raise ValueError(
            f"Rule {rule_id} must define a boolean "
            "'expected_result'."
        )

    return {
        "id": rule_id,
        "expression": expression,
        "expected_result": expected_result,
        "description": description,
    }


def _validate_unique_rule_ids(
    rules: list[dict[str, Any]],
) -> None:
    """
    Ensures every macro-rule and expression-rule identifier is unique.
    """

    rule_ids = [
        str(rule["id"])
        for rule in rules
    ]

    duplicated_rule_ids = {
        rule_id
        for rule_id in rule_ids
        if rule_ids.count(rule_id) > 1
    }

    if duplicated_rule_ids:
        duplicated_ids_text = ", ".join(
            sorted(duplicated_rule_ids)
        )

        raise ValueError(
            "Duplicate rule identifiers found: "
            f"{duplicated_ids_text}"
        )