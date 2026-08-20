from pathlib import Path

from openpyxl import load_workbook

from src.makefile_parser import parse_makefile
from src.preprocessor_parser import find_preprocessor_directives
from src.report_generator import generate_excel_report

from src.switch_classifier import (
    classify_preprocessor_finding,
)

def get_project_root() -> Path:
    """
    Returns the root folder of the automation_tool project.
    """

    return Path(__file__).parent.parent

def get_summary_value(
    worksheet,
    label: str,
):
    """
    Returns the value in column B for the row whose column A matches
    the requested Summary label.
    """

    for row_number in range(
        1,
        worksheet.max_row + 1,
    ):
        if (
            worksheet.cell(
                row=row_number,
                column=1,
            ).value
            == label
        ):
            return worksheet.cell(
                row=row_number,
                column=2,
            ).value

    raise AssertionError(
        f"Summary label not found: {label}"
    )


def test_generate_excel_report_with_controlled_data(
    tmp_path: Path,
) -> None:
    """
    Verifies that an Excel report is generated with the expected
    worksheets and controlled data.
    """

    project_root = get_project_root()

    fixture_makefile = (
        project_root
        / "tests"
        / "fixtures"
        / "compile_opt_example.mk"
    )

    fixture_c_file = (
        project_root
        / "tests"
        / "fixtures"
        / "ExampleModule.c"
    )

    makefile_data = parse_makefile(
        fixture_makefile,
        build_mode="Release",
    )

    findings = find_preprocessor_directives(
        fixture_c_file
    )

    report_path = (
        tmp_path
        / "compiler_switches_report.xlsx"
    )

    generated_report_path = generate_excel_report(
        output_path=report_path,
        project_name="Controlled_Project",
        core="Core1",
        build_mode="Release",
        project_root=project_root,
        makefile_data=makefile_data,
        source_file_count=3,
        findings=findings,
    )

    assert generated_report_path.exists()

    workbook = load_workbook(
        generated_report_path,
        read_only=True,
    )

    assert workbook.sheetnames == [
        "Summary",
        "Compiler Switches",
        "Preprocessor Conditions",
        "Filtered Compiler Switches",
        "Excluded Conditions",
        "Relevant Switch Summary",
    ]

    summary_sheet = workbook["Summary"]
    switches_sheet = workbook["Compiler Switches"]
    conditions_sheet = workbook[
        "Preprocessor Conditions"
    ]

    filtered_switches_sheet = workbook[
    "Filtered Compiler Switches"
    ]

    excluded_conditions_sheet = workbook[
    "Excluded Conditions"
    ]

    relevant_switch_summary_sheet = workbook[
        "Relevant Switch Summary"
    ]

    assert summary_sheet["A1"].value == "Metric"
    assert summary_sheet["B1"].value == "Value"

    assert switches_sheet["A1"].value == "Project"
    assert switches_sheet["J1"].value == "Entry Type"
    assert switches_sheet.max_row == 6

    assert conditions_sheet["A1"].value == "Source File"
    assert conditions_sheet["E1"].value == "Expression"
    assert conditions_sheet.max_row == 6

    assert (
    filtered_switches_sheet["A1"].value
    == "Source File"
    )
    assert (
    filtered_switches_sheet["G1"].value
    == "Category"
    )

    assert (
    excluded_conditions_sheet["A1"].value
    == "Source File"
    )
    assert (
    excluded_conditions_sheet["H1"].value
    == "Filter Reason"
    )

    workbook.close()

def test_summary_includes_classification_metrics(
    tmp_path: Path,
) -> None:
    """
    Verifies that Summary contains overall, exclusion, and category
    metrics derived from classified findings.
    """

    findings = [
        {
            "path": "src/Example.c",
            "file_name": "Example.c",
            "line_number": 10,
            "directive": "#if",
            "expression": "FEATURE_X",
            "macros": ["FEATURE_X"],
        },
        {
            "path": "src/Example.c",
            "file_name": "Example.c",
            "line_number": 20,
            "directive": "#ifdef",
            "expression": "__GNUC__",
            "macros": ["__GNUC__"],
        },
        {
            "path": "src/Example.h",
            "file_name": "Example.h",
            "line_number": 1,
            "directive": "#ifndef",
            "expression": "EXAMPLE_H",
            "macros": ["EXAMPLE_H"],
        },
        {
            "path": "src/Example.c",
            "file_name": "Example.c",
            "line_number": 30,
            "directive": "#if",
            "expression": "VALUE > 0",
            "macros": ["VALUE"],
        },
    ]

    classified_findings = [
        finding | classify_preprocessor_finding(finding)
        for finding in findings
    ]

    report_path = (
        tmp_path
        / "summary_metrics_report.xlsx"
    )

    generated_report_path = generate_excel_report(
        output_path=report_path,
        project_name="Metrics_Project",
        core="Core1",
        build_mode="Release",
        project_root=get_project_root(),
        makefile_data={},
        source_file_count=2,
        findings=classified_findings,
    )

    workbook = load_workbook(
        generated_report_path,
        read_only=True,
    )

    summary_sheet = workbook["Summary"]

    relevant_switch_summary_sheet = workbook[
    "Relevant Switch Summary"
    ]

    assert get_summary_value(
        summary_sheet,
        "Total preprocessor directives analyzed",
    ) == 4

    assert get_summary_value(
        summary_sheet,
        "Relevant compiler switches",
    ) == 1

    assert get_summary_value(
        summary_sheet,
        "Excluded conditions",
    ) == 2

    assert get_summary_value(
        summary_sheet,
        "Pending OTHER conditions for review",
    ) == 1

    assert get_summary_value(
        summary_sheet,
        "Header guard",
    ) == 1

    assert get_summary_value(
        summary_sheet,
        "Toolchain or architecture condition",
    ) == 1

    assert get_summary_value(
        summary_sheet,
        "FEATURE",
    ) == 1

    assert get_summary_value(
        summary_sheet,
        "TOTAL",
    ) == 1

    assert (
        relevant_switch_summary_sheet["A1"].value
        == "Category"
    )
    assert (
        relevant_switch_summary_sheet["B1"].value
        == "Primary Macro"
    )
    assert (
        relevant_switch_summary_sheet["C1"].value
        == "Occurrences"
    )
    assert (
        relevant_switch_summary_sheet["D1"].value
        == "Files Affected"
    )

def test_relevant_switch_summary_groups_repeated_macros(
    tmp_path: Path,
) -> None:
    """
    Verifies that repeated relevant conditions are consolidated
    into one summary row per category and primary macro.
    """

    findings = [
        {
            "path": "src/BswM.c",
            "file_name": "BswM.c",
            "line_number": 10,
            "directive": "#if",
            "expression": (
                "BSWM_ENABLE_CANSM == STD_ON"
            ),
            "macros": [
                "BSWM_ENABLE_CANSM",
                "STD_ON",
            ],
            "category": "FEATURE",
            "is_relevant": True,
            "filter_reason": "",
        },
        {
            "path": "src/BswM.c",
            "file_name": "BswM.c",
            "line_number": 25,
            "directive": "#if",
            "expression": (
                "BSWM_ENABLE_CANSM == STD_ON"
            ),
            "macros": [
                "BSWM_ENABLE_CANSM",
                "STD_ON",
            ],
            "category": "FEATURE",
            "is_relevant": True,
            "filter_reason": "",
        },
        {
            "path": "src/BswM_Cfg.h",
            "file_name": "BswM_Cfg.h",
            "line_number": 40,
            "directive": "#ifdef",
            "expression": "BSWM_ENABLE_CANSM",
            "macros": [
                "BSWM_ENABLE_CANSM",
            ],
            "category": "FEATURE",
            "is_relevant": True,
            "filter_reason": "",
        },
        {
            "path": "src/Det.c",
            "file_name": "Det.c",
            "line_number": 90,
            "directive": "#if",
            "expression": (
                "DET_DEBUG_ENABLED == STD_ON"
            ),
            "macros": [
                "DET_DEBUG_ENABLED",
                "STD_ON",
            ],
            "category": "DEBUG",
            "is_relevant": True,
            "filter_reason": "",
        },
    ]

    report_path = (
        tmp_path
        / "relevant_switch_summary.xlsx"
    )

    generated_report_path = generate_excel_report(
        output_path=report_path,
        project_name="Summary_Project",
        core="Core1",
        build_mode="Release",
        project_root=get_project_root(),
        makefile_data={},
        source_file_count=2,
        findings=findings,
    )

    workbook = load_workbook(
        generated_report_path,
        read_only=True,
    )

    worksheet = workbook[
        "Relevant Switch Summary"
    ]

    assert worksheet.max_row == 3

    assert worksheet["A2"].value == "FEATURE"
    assert worksheet["B2"].value == "BSWM_ENABLE_CANSM"
    assert worksheet["C2"].value == 3
    assert worksheet["D2"].value == 2

    assert worksheet["A3"].value == "DEBUG"
    assert worksheet["B3"].value == "DET_DEBUG_ENABLED"
    assert worksheet["C3"].value == 1
    assert worksheet["D3"].value == 1

    workbook.close()