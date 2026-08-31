from pathlib import Path

import pytest

from src.rule_config_loader import (
    load_expected_rules,
    load_expression_rules,
)


def write_rules_file(
    file_path: Path,
    content: str,
) -> Path:
    """
    Writes controlled YAML rule content for testing.
    """

    file_path.write_text(
        content.strip(),
        encoding="utf-8",
    )

    return file_path


def test_loads_valid_expected_rules(
    tmp_path: Path,
) -> None:
    rules_path = write_rules_file(
        tmp_path / "expected_rules.yaml",
        """
rules:
  - id: "RULE-001"
    macro: "FEATURE_X"
    expected_state: "Enabled"
    description: "Feature X must be enabled."

  - id: "RULE-002"
    macro: "CONFIG_CLASS"
    expected_state: null
    description: "Traceability-only rule."
""",
    )

    rules = load_expected_rules(
        rules_path
    )

    assert len(rules) == 2

    assert rules[0] == {
        "id": "RULE-001",
        "macro": "FEATURE_X",
        "expected_state": "Enabled",
        "expected_value": None,
        "description": (
            "Feature X must be enabled."
        ),
    }

    assert rules[1]["id"] == "RULE-002"
    assert rules[1]["macro"] == "CONFIG_CLASS"
    assert rules[1]["expected_state"] is None
    assert rules[1]["expected_value"] is None


def test_raises_error_when_rules_file_does_not_exist(
    tmp_path: Path,
) -> None:
    missing_path = tmp_path / "missing_rules.yaml"

    with pytest.raises(
        FileNotFoundError,
    ):
        load_expected_rules(missing_path)


def test_raises_error_when_rules_key_is_missing(
    tmp_path: Path,
) -> None:
    rules_path = write_rules_file(
        tmp_path / "expected_rules.yaml",
        """
project: "Release_DMS"
""",
    )

    with pytest.raises(
        ValueError,
        match="must contain a 'rules' list",
    ):
        load_expected_rules(rules_path)


def test_raises_error_for_unsupported_expected_state(
    tmp_path: Path,
) -> None:
    rules_path = write_rules_file(
        tmp_path / "expected_rules.yaml",
        """
rules:
  - id: "RULE-001"
    macro: "FEATURE_X"
    expected_state: "Unknown"
    description: "Invalid expected state."
""",
    )

    with pytest.raises(
        ValueError,
        match="unsupported expected_state",
    ):
        load_expected_rules(rules_path)


def test_raises_error_for_duplicate_rule_identifiers(
    tmp_path: Path,
) -> None:
    rules_path = write_rules_file(
        tmp_path / "expected_rules.yaml",
        """
rules:
  - id: "RULE-001"
    macro: "FEATURE_X"
    expected_state: "Enabled"
    description: "First rule."

  - id: "RULE-001"
    macro: "FEATURE_Y"
    expected_state: "Disabled"
    description: "Second rule."
""",
    )

    with pytest.raises(
        ValueError,
        match="Duplicate rule identifiers",
    ):
        load_expected_rules(rules_path)

def test_loads_undefined_expected_state(
    tmp_path: Path,
) -> None:
    rules_path = write_rules_file(
        tmp_path / "expected_rules.yaml",
        """
rules:
  - id: "RULE-001"
    macro: "VMEMACCM_COMPONENT_TEST"
    expected_state: "Undefined"
    description: "Component test macro must remain undefined."
""",
    )

    rules = load_expected_rules(
        rules_path
    )

    assert rules[0]["expected_state"] == "Undefined"

def test_loads_expected_value_rule(
    tmp_path: Path,
) -> None:
    rules_path = write_rules_file(
        tmp_path / "expected_rules.yaml",
        """
rules:
  - id: "RULE-001"
    macro: "RAMTEST_IMMEDIATE_SECTIONS_NUM"
    expected_value: "0"
    description: "No immediate sections are expected."
""",
    )

    rules = load_expected_rules(
        rules_path
    )

    assert rules[0]["expected_state"] is None
    assert rules[0]["expected_value"] == "0"


def test_rejects_rule_with_state_and_value(
    tmp_path: Path,
) -> None:
    rules_path = write_rules_file(
        tmp_path / "expected_rules.yaml",
        """
rules:
  - id: "RULE-001"
    macro: "FEATURE_X"
    expected_state: "Enabled"
    expected_value: "1"
    description: "Invalid mixed rule."
""",
    )

    with pytest.raises(
        ValueError,
        match="cannot define both",
    ):
        load_expected_rules(rules_path)

def test_loads_valid_expression_rules(
    tmp_path: Path,
) -> None:
    rules_path = write_rules_file(
        tmp_path / "expected_rules.yaml",
        """
rules:
  - id: "REL-001"
    macro: "FEATURE_X"
    expected_state: "Enabled"
    description: "Feature X must be enabled."

expression_rules:
  - id: "REL-EXPR-001"
    expression: >
      (DET_DEBUG_ENABLED == STD_ON) &&
      (DET_DLTFILTERSIZE > 0)
    expected_result: false
    description: >
      DET DLT-filter code must remain inactive.
""",
    )

    expression_rules = load_expression_rules(
        rules_path
    )

    assert len(expression_rules) == 1

    assert expression_rules[0] == {
        "id": "REL-EXPR-001",
        "expression": (
            "(DET_DEBUG_ENABLED == STD_ON) "
            "&& (DET_DLTFILTERSIZE > 0)"
        ),
        "expected_result": False,
        "description": (
            "DET DLT-filter code must remain inactive."
        ),
    }


def test_rejects_expression_rule_without_boolean_result(
    tmp_path: Path,
) -> None:
    rules_path = write_rules_file(
        tmp_path / "expected_rules.yaml",
        """
rules:
  - id: "REL-001"
    macro: "FEATURE_X"
    expected_state: "Enabled"
    description: "Feature X must be enabled."

expression_rules:
  - id: "REL-EXPR-001"
    expression: "(FEATURE_X == STD_ON)"
    expected_result: "false"
    description: "Invalid result type."
""",
    )

    with pytest.raises(
        ValueError,
        match="boolean 'expected_result'",
    ):
        load_expression_rules(rules_path)


def test_rejects_duplicate_ids_between_rule_types(
    tmp_path: Path,
) -> None:
    rules_path = write_rules_file(
        tmp_path / "expected_rules.yaml",
        """
rules:
  - id: "REL-001"
    macro: "FEATURE_X"
    expected_state: "Enabled"
    description: "Feature X must be enabled."

expression_rules:
  - id: "REL-001"
    expression: "(FEATURE_X == STD_ON)"
    expected_result: true
    description: "Duplicate identifier."
""",
    )

    with pytest.raises(
        ValueError,
        match="Duplicate rule identifiers",
    ):
        load_expected_rules(rules_path)