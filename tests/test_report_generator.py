from pathlib import Path

from openpyxl import load_workbook

from src.makefile_parser import parse_makefile
from src.preprocessor_parser import find_preprocessor_directives
from src.report_generator import generate_excel_report


def get_project_root() -> Path:
    """
    Returns the root folder of the automation_tool project.
    """

    return Path(__file__).parent.parent


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
    ]

    summary_sheet = workbook["Summary"]
    switches_sheet = workbook["Compiler Switches"]
    conditions_sheet = workbook[
        "Preprocessor Conditions"
    ]

    assert summary_sheet["A1"].value == "Metric"
    assert summary_sheet["B1"].value == "Value"

    assert switches_sheet["A1"].value == "Project"
    assert switches_sheet["J1"].value == "Entry Type"
    assert switches_sheet.max_row == 6

    assert conditions_sheet["A1"].value == "Project"
    assert conditions_sheet["H1"].value == "Expression"
    assert conditions_sheet.max_row == 6

    workbook.close()