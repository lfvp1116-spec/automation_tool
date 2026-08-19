from pathlib import Path

import pytest

from src.preprocessor_parser import (
    find_preprocessor_directives,
    remove_comments_from_text,
)

def get_fixture_path(file_name: str) -> Path:
    """
    Returns the path to a controlled fixture file.
    """

    project_root = Path(__file__).parent.parent

    return (
        project_root
        / "tests"
        / "fixtures"
        / file_name
    )


def test_find_directives_in_c_file() -> None:
    """
    Verifies that directives are detected in ExampleModule.c.
    """

    findings = find_preprocessor_directives(
        get_fixture_path("ExampleModule.c")
    )

    assert len(findings) == 5

    assert findings[0]["line_number"] == 4
    assert findings[0]["directive"] == "#if"
    assert findings[0]["expression"] == (
        "(DET_DEBUG_ENABLED == STD_ON)"
    )
    assert findings[0]["macros"] == [
        "DET_DEBUG_ENABLED",
        "STD_ON",
    ]

    assert findings[1]["line_number"] == 10
    assert findings[1]["directive"] == "#ifdef"
    assert findings[1]["expression"] == "FEATURE_X"
    assert findings[1]["macros"] == [
        "FEATURE_X",
    ]

    assert findings[2]["line_number"] == 16
    assert findings[2]["directive"] == "#if"
    assert findings[2]["expression"] == (
        "defined(INTEGRATION_TEST_VARM_TASK_PERIOD)"
    )
    assert findings[2]["macros"] == [
        "INTEGRATION_TEST_VARM_TASK_PERIOD",
    ]

    assert findings[3]["line_number"] == 20
    assert findings[3]["directive"] == "#elif"
    assert findings[3]["expression"] == "defined(TEST_MODE)"
    assert findings[3]["macros"] == [
        "TEST_MODE",
    ]

    assert findings[4]["line_number"] == 26
    assert findings[4]["directive"] == "#if"
    assert findings[4]["expression"] == (
        "(DET_DEBUG_ENABLED == STD_ON) && "
        "(DET_DLTFILTERSIZE > 0)"
    )
    assert findings[4]["macros"] == [
        "DET_DEBUG_ENABLED",
        "STD_ON",
        "DET_DLTFILTERSIZE",
    ]


def test_find_header_guard_in_h_file() -> None:
    """
    Verifies that a header guard is detected in ExampleModule.h.

    At this stage, header guards are registered as raw findings.
    They will be filtered during the false-positive classification phase.
    """

    findings = find_preprocessor_directives(
        get_fixture_path("ExampleModule.h")
    )

    assert len(findings) == 1
    assert findings[0]["line_number"] == 1
    assert findings[0]["directive"] == "#ifndef"
    assert findings[0]["expression"] == "EXAMPLEMODULE_H"
    assert findings[0]["macros"] == [
        "EXAMPLEMODULE_H",
    ]


def test_missing_source_file_raises_error() -> None:
    """
    Verifies that a missing source file produces a clear error.
    """

    missing_file = Path(
        "tests/fixtures/file_does_not_exist.c"
    )

    with pytest.raises(FileNotFoundError):
        find_preprocessor_directives(missing_file)

def test_remove_comments_from_expression() -> None:
    """
    Verifies that comments are removed before macro extraction.
    """

    expression = (
        "(defined CAN_CFG_MAJOR_VERSION) "
        "/* to prevent double declaration */"
    )

    cleaned_expression = remove_comments_from_text(expression)

    assert cleaned_expression == "(defined CAN_CFG_MAJOR_VERSION)"