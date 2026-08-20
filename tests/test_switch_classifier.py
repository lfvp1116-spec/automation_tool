from src.switch_classifier import (
    classify_preprocessor_finding,
)


def test_classifies_debug_condition() -> None:
    finding = {
        "file_name": "Det.c",
        "line_number": 10,
        "directive": "#if",
        "expression": (
            "DET_DEBUG_ENABLED == STD_ON"
        ),
        "macros": [
            "DET_DEBUG_ENABLED",
            "STD_ON",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "DEBUG"
    assert result["is_relevant"] is True
    assert result["filter_reason"] == ""


def test_classifies_test_condition() -> None:
    finding = {
        "file_name": "ExampleModule.c",
        "line_number": 10,
        "directive": "#if",
        "expression": "defined(TEST_MODE)",
        "macros": ["TEST_MODE"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "TEST"
    assert result["is_relevant"] is True


def test_classifies_integration_condition() -> None:
    finding = {
        "file_name": "ExampleModule.c",
        "line_number": 20,
        "directive": "#if",
        "expression": (
            "defined(INTEGRATION_TEST_MODE)"
        ),
        "macros": ["INTEGRATION_TEST_MODE"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "INTEGRATION"
    assert result["is_relevant"] is True


def test_classifies_feature_condition() -> None:
    finding = {
        "file_name": "ExampleModule.c",
        "line_number": 30,
        "directive": "#ifdef",
        "expression": "FEATURE_X",
        "macros": ["FEATURE_X"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "FEATURE"
    assert result["is_relevant"] is True


def test_marks_header_guard_as_not_relevant() -> None:
    finding = {
        "file_name": "ExampleModule.h",
        "line_number": 1,
        "directive": "#ifndef",
        "expression": "EXAMPLE_MODULE_H",
        "macros": ["EXAMPLE_MODULE_H"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["is_header_guard"] is True
    assert result["is_relevant"] is False
    assert result["filter_reason"] == "Header guard"


def test_marks_memmap_condition_as_not_relevant() -> None:
    finding = {
        "file_name": "ExampleModule.c",
        "line_number": 50,
        "directive": "#ifdef",
        "expression": "START_SEC_CODE",
        "macros": ["START_SEC_CODE"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["is_memmap"] is True
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "MemMap section marker"
    )


def test_marks_toolchain_condition_as_not_relevant() -> None:
    finding = {
        "file_name": "ExampleModule.c",
        "line_number": 60,
        "directive": "#ifdef",
        "expression": "__GNUC__",
        "macros": ["__GNUC__"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["is_toolchain_condition"] is True
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Toolchain or architecture condition"
    )


def test_marks_static_analysis_condition_as_not_relevant() -> None:
    finding = {
        "file_name": "ExampleModule.c",
        "line_number": 70,
        "directive": "#ifdef",
        "expression": "PRQA_S 1234",
        "macros": ["PRQA_S"],
    }

    result = classify_preprocessor_finding(finding)

    assert (
        result["is_static_analysis_condition"]
        is True
    )
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Static-analysis condition"
    )


def test_marks_other_condition_as_not_relevant() -> None:
    finding = {
        "file_name": "ExampleModule.c",
        "line_number": 80,
        "directive": "#if",
        "expression": "VALUE > 0",
        "macros": ["VALUE"],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "OTHER"
    assert result["is_relevant"] is False
    assert result["filter_reason"] == ""

def test_marks_generated_test_condition_as_not_relevant() -> None:
    finding = {
        "file_name": "Cdd_test_Cbk.h",
        "line_number": 64,
        "directive": "#ifndef",
        "expression": "CDD_TEST_DUMMY_STATEMENT",
        "macros": [
            "CDD_TEST_DUMMY_STATEMENT",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "TEST"
    assert (
        result["is_generated_test_condition"]
        is True
    )
    assert result["is_relevant"] is False
    assert (
        result["filter_reason"]
        == "Generated or internal test condition"
    )


def test_keeps_regular_test_condition_relevant() -> None:
    finding = {
        "file_name": "Watchdog.c",
        "line_number": 84,
        "directive": "#if",
        "expression": (
            "INTEGRATION_WATCHDOG_TESTS == WDG_STD_ON"
        ),
        "macros": [
            "INTEGRATION_WATCHDOG_TESTS",
            "WDG_STD_ON",
        ],
    }

    result = classify_preprocessor_finding(finding)

    assert result["category"] == "INTEGRATION"
    assert (
        result["is_generated_test_condition"]
        is False
    )
    assert result["is_relevant"] is True
    assert result["filter_reason"] == ""