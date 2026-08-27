from src.unresolved_expression_summary import (
    summarize_unresolved_expressions,
)


def test_groups_repeated_missing_macro_definitions() -> None:
    evaluations = [
        {
            "source_file": "src/Dem_A.c",
            "file_name": "Dem_A.c",
            "line_number": 100,
            "directive": "#if",
            "category": "FEATURE",
            "original_expression": (
                "DEM_FEATURE_FAST == STD_ON"
            ),
            "evaluation_status": "Unresolved",
            "error_message": (
                "Macro definition not found: "
                "DEM_FEATURE_FAST"
            ),
        },
        {
            "source_file": "src/Dem_B.c",
            "file_name": "Dem_B.c",
            "line_number": 200,
            "directive": "#if",
            "category": "FEATURE",
            "original_expression": (
                "DEM_FEATURE_FAST == STD_ON"
            ),
            "evaluation_status": "Unresolved",
            "error_message": (
                "Macro definition not found: "
                "DEM_FEATURE_FAST"
            ),
        },
    ]

    summary = summarize_unresolved_expressions(
        evaluations
    )

    assert len(summary) == 1

    result = summary[0]

    assert (
        result["error_type"]
        == "Missing macro definition"
    )
    assert result["issue_key"] == "DEM_FEATURE_FAST"
    assert result["occurrences"] == 2
    assert result["files_affected"] == 2
    assert result["category"] == "FEATURE"

    assert result["example_source_file"] == "src/Dem_A.c"
    assert result["example_line"] == 100


def test_groups_non_integer_macro_expression() -> None:
    evaluations = [
        {
            "source_file": "src/SbcDrv.c",
            "file_name": "SbcDrv.c",
            "line_number": 1405,
            "directive": "#if",
            "category": "FEATURE",
            "original_expression": (
                "SBCDRV_SLEEP_CONFIG == STD_ON"
            ),
            "evaluation_status": "Unresolved",
            "error_message": (
                "Macro does not resolve to an integer: "
                "SBCDRV_SLEEP_CONFIG -> "
                "SBCDRV_SLEEP_VCC | SBCDRV_SLEEP_HW"
            ),
        }
    ]

    summary = summarize_unresolved_expressions(
        evaluations
    )

    assert len(summary) == 1

    result = summary[0]

    assert (
        result["error_type"]
        == "Macro resolves to non-integer expression"
    )

    assert result["issue_key"] == "SBCDRV_SLEEP_CONFIG"
    assert result["occurrences"] == 1
    assert result["files_affected"] == 1


def test_ignores_successfully_evaluated_expressions() -> None:
    evaluations = [
        {
            "source_file": "src/Example.c",
            "line_number": 10,
            "directive": "#if",
            "category": "FEATURE",
            "evaluation_status": "Evaluated",
            "evaluation": True,
            "error_message": "",
        }
    ]

    summary = summarize_unresolved_expressions(
        evaluations
    )

    assert summary == []


def test_groups_unsupported_syntax() -> None:
    evaluations = [
        {
            "source_file": "src/Example.c",
            "line_number": 20,
            "directive": "#if",
            "category": "FEATURE",
            "original_expression": (
                "BUFFER_SIZE * 2 > 0"
            ),
            "evaluation_status": "Unresolved",
            "error_message": (
                "Unsupported expression content near: "
                "* 2 > 0"
            ),
        }
    ]

    summary = summarize_unresolved_expressions(
        evaluations
    )

    assert len(summary) == 1

    result = summary[0]

    assert (
        result["error_type"]
        == "Unsupported expression syntax"
    )

    assert (
        result["issue_key"]
        == "Unsupported expression content near: * 2 > 0"
    )