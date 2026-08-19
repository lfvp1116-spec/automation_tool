from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


HEADER_FILL = PatternFill(
    fill_type="solid",
    fgColor="1F4E78",
)

HEADER_FONT = Font(
    color="FFFFFF",
    bold=True,
)

HEADER_ALIGNMENT = Alignment(
    horizontal="center",
    vertical="center",
    wrap_text=True,
)

CELL_ALIGNMENT = Alignment(
    vertical="top",
    wrap_text=True,
)


def format_worksheet(worksheet) -> None:
    """
    Applies basic formatting to an Excel worksheet.
    """

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions

    for cell in worksheet[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = HEADER_ALIGNMENT

    for row in worksheet.iter_rows(
        min_row=2,
        max_row=worksheet.max_row,
    ):
        for cell in row:
            cell.alignment = CELL_ALIGNMENT

    for column_index, column_cells in enumerate(
        worksheet.columns,
        start=1,
    ):
        maximum_length = 0

        for cell in column_cells:
            cell_value = "" if cell.value is None else str(cell.value)

            maximum_length = max(
                maximum_length,
                len(cell_value),
            )

        column_letter = get_column_letter(column_index)

        worksheet.column_dimensions[column_letter].width = min(
            maximum_length + 2,
            60,
        )


def create_summary_sheet(
    workbook: Workbook,
    summary_data: dict,
) -> None:
    """
    Creates the Summary worksheet.
    """

    worksheet = workbook.active
    worksheet.title = "Summary"

    worksheet.append(
        [
            "Metric",
            "Value",
        ]
    )

    for metric, value in summary_data.items():
        worksheet.append(
            [
                metric,
                value,
            ]
        )

    format_worksheet(worksheet)


def create_compiler_switches_sheet(
    workbook: Workbook,
    project_name: str,
    core: str,
    build_mode: str,
    makefile_data: dict,
) -> None:
    """
    Creates the Compiler Switches worksheet.
    """

    worksheet = workbook.create_sheet(
        title="Compiler Switches"
    )

    worksheet.append(
        [
            "Project",
            "Core",
            "Build Mode",
            "Makefile",
            "Compiler",
            "CPU",
            "FPU",
            "Instruction Mode",
            "Optimization",
            "Entry Type",
            "Name",
            "Value",
        ]
    )

    common_data = [
        project_name,
        core,
        build_mode,
        makefile_data["makefile"],
        makefile_data["compiler"],
        makefile_data["cpu"],
        makefile_data["fpu"],
        makefile_data["instruction_mode"],
        makefile_data["optimization"],
    ]

    explicit_macros = makefile_data["macros"]
    build_definitions = makefile_data[
        "build_mode_definitions"
    ]

    if not explicit_macros and not build_definitions:
        worksheet.append(
            common_data
            + [
                "No macro found",
                None,
                None,
            ]
        )

    for macro in explicit_macros:
        worksheet.append(
            common_data
            + [
                "Explicit -D macro",
                macro["name"],
                macro["value"],
            ]
        )

    for definition in build_definitions:
        worksheet.append(
            common_data
            + [
                "Build-mode definition",
                definition["name"],
                definition["value"],
            ]
        )

    format_worksheet(worksheet)


def create_preprocessor_conditions_sheet(
    workbook: Workbook,
    project_name: str,
    core: str,
    build_mode: str,
    project_root: str | Path,
    findings: list[dict],
) -> None:
    """
    Creates the Preprocessor Conditions worksheet.
    """

    worksheet = workbook.create_sheet(
        title="Preprocessor Conditions"
    )

    worksheet.append(
        [
            "Project",
            "Core",
            "Build Mode",
            "Relative Path",
            "File Name",
            "Line Number",
            "Directive",
            "Expression",
            "Macros",
        ]
    )

    root_path = Path(project_root)

    for finding in findings:
        finding_path = Path(finding["path"])

        try:
            relative_path = finding_path.relative_to(root_path)
        except ValueError:
            relative_path = finding_path

        worksheet.append(
            [
                project_name,
                core,
                build_mode,
                str(relative_path),
                finding["file_name"],
                finding["line_number"],
                finding["directive"],
                finding["expression"],
                ", ".join(finding["macros"]),
            ]
        )

    format_worksheet(worksheet)


def generate_excel_report(
    output_path: str | Path,
    project_name: str,
    core: str,
    build_mode: str,
    project_root: str | Path,
    makefile_data: dict,
    source_file_count: int,
    findings: list[dict],
) -> Path:
    """
    Generates an Excel report containing summary data, compiler
    switches, and raw preprocessor-condition findings.

    Returns:
        Path to the generated Excel report.
    """

    report_path = Path(output_path)
    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    directive_counts = {}

    for finding in findings:
        directive = finding["directive"]

        directive_counts[directive] = (
            directive_counts.get(directive, 0) + 1
        )

    summary_data = {
        "Project": project_name,
        "Core": core,
        "Build Mode": build_mode,
        "Makefile": makefile_data["makefile"],
        "Source Files Analyzed": source_file_count,
        "Preprocessor Directives Found": len(findings),
        "#if Count": directive_counts.get("#if", 0),
        "#ifdef Count": directive_counts.get("#ifdef", 0),
        "#ifndef Count": directive_counts.get("#ifndef", 0),
        "#elif Count": directive_counts.get("#elif", 0),
        "Generated At": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    }

    workbook = Workbook()

    create_summary_sheet(
        workbook,
        summary_data,
    )

    create_compiler_switches_sheet(
        workbook,
        project_name,
        core,
        build_mode,
        makefile_data,
    )

    create_preprocessor_conditions_sheet(
        workbook,
        project_name,
        core,
        build_mode,
        project_root,
        findings,
    )

    workbook.save(report_path)

    return report_path