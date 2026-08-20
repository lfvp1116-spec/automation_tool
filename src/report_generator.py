from pathlib import Path
from typing import Any, Iterable

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.worksheet import Worksheet


TITLE_FILL = PatternFill(
    fill_type="solid",
    fgColor="1F4E78",
)

HEADER_FILL = PatternFill(
    fill_type="solid",
    fgColor="5B9BD5",
)

TITLE_FONT = Font(
    bold=True,
    color="FFFFFF",
    size=14,
)

HEADER_FONT = Font(
    bold=True,
    color="FFFFFF",
)


def generate_excel_report(
    output_path: Path,
    project_name: str,
    core: str,
    build_mode: str,
    project_root: Path,
    makefile_data: dict[str, Any],
    source_file_count: int,
    findings: Iterable[dict[str, Any]],
) -> Path:
    """
    Generates an Excel report with:

    - Summary
    - Compiler Switches
    - Preprocessor Conditions
    """

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    findings_list = list(findings)

    workbook = Workbook()

    summary_sheet = workbook.active
    summary_sheet.title = "Summary"

    switches_sheet = workbook.create_sheet(
        title="Compiler Switches"
    )

    conditions_sheet = workbook.create_sheet(
        title="Preprocessor Conditions"
    )

    filtered_switches_sheet = workbook.create_sheet(
    title="Filtered Compiler Switches"
    )

    excluded_conditions_sheet = workbook.create_sheet(
    title="Excluded Conditions"
    )

    _write_summary_sheet(
        worksheet=summary_sheet,
        project_name=project_name,
        core=core,
        build_mode=build_mode,
        project_root=project_root,
        source_file_count=source_file_count,
        directive_count=len(findings_list),
    )

    _write_compiler_switches_sheet(
        worksheet=switches_sheet,
        project_name=project_name,
        core=core,
        build_mode=build_mode,
        makefile_data=makefile_data,
        source_file_count=source_file_count,
    )

    _write_preprocessor_conditions_sheet(
        worksheet=conditions_sheet,
        project_name=project_name,
        core=core,
        build_mode=build_mode,
        findings=findings_list,
    )

    _write_filtered_compiler_switches_sheet(
        worksheet=filtered_switches_sheet,
        findings=findings_list,
    )

    _write_excluded_conditions_sheet(
        worksheet=excluded_conditions_sheet,
        findings=findings_list,
    )

    workbook.save(output_path)
    workbook.close()

    return output_path


def create_compiler_switches_report(
    report_path: Path,
    findings: Iterable[dict[str, Any]],
) -> Path:
    """
    Simplified report-generation function used by main.py.

    This preserves compatibility with the current main.py integration.
    """

    return generate_excel_report(
        output_path=report_path,
        project_name="Release_DMS",
        core="Core1",
        build_mode="Release",
        project_root=Path("."),
        makefile_data={},
        source_file_count=0,
        findings=findings,
    )


def _write_summary_sheet(
    worksheet: Worksheet,
    project_name: str,
    core: str,
    build_mode: str,
    project_root: Path,
    source_file_count: int,
    directive_count: int,
) -> None:
    """
    Writes the Summary worksheet.
    """

    worksheet["A1"] = "Metric"
    worksheet["B1"] = "Value"

    _format_header_row(
        worksheet=worksheet,
        row_number=1,
        column_count=2,
    )

    summary_rows = [
        ("Project", project_name),
        ("Core", core),
        ("Build mode", build_mode),
        ("Project root", str(project_root)),
        ("Source files analyzed", source_file_count),
        ("Preprocessor directives found", directive_count),
    ]

    for row_number, (metric, value) in enumerate(
        summary_rows,
        start=2,
    ):
        worksheet.cell(
            row=row_number,
            column=1,
            value=metric,
        )

        worksheet.cell(
            row=row_number,
            column=2,
            value=value,
        )

    worksheet.column_dimensions["A"].width = 35
    worksheet.column_dimensions["B"].width = 80
    worksheet.freeze_panes = "A2"


def _write_compiler_switches_sheet(
    worksheet: Worksheet,
    project_name: str,
    core: str,
    build_mode: str,
    makefile_data: dict[str, Any],
    source_file_count: int,
) -> None:
    """
    Writes build/compiler data extracted from the Makefile.
    """

    headers = [
        "Project",
        "Core",
        "Build Mode",
        "Source Files",
        "Makefile Parameter",
        "Value",
        "Makefile Source",
        "Build Configuration",
        "Detected",
        "Entry Type",
    ]

    for column_number, header in enumerate(
        headers,
        start=1,
    ):
        worksheet.cell(
            row=1,
            column=column_number,
            value=header,
        )

    _format_header_row(
        worksheet=worksheet,
        row_number=1,
        column_count=len(headers),
    )

    report_entries = list(
    makefile_data.items()
)[:5]

    for row_number, (parameter, value) in enumerate(
    report_entries,
    start=2,
):
        display_value = _format_value(value)

        worksheet.cell(row=row_number, column=1, value=project_name)
        worksheet.cell(row=row_number, column=2, value=core)
        worksheet.cell(row=row_number, column=3, value=build_mode)
        worksheet.cell(
            row=row_number,
            column=4,
            value=source_file_count,
        )
        worksheet.cell(
            row=row_number,
            column=5,
            value=str(parameter),
        )
        worksheet.cell(
            row=row_number,
            column=6,
            value=display_value,
        )
        worksheet.cell(
            row=row_number,
            column=7,
            value="Makefile",
        )
        worksheet.cell(
            row=row_number,
            column=8,
            value=build_mode,
        )
        worksheet.cell(
            row=row_number,
            column=9,
            value="Yes",
        )
        worksheet.cell(
            row=row_number,
            column=10,
            value=_get_entry_type(parameter),
        )

    _format_table(
        worksheet=worksheet,
        column_widths={
            "A": 24,
            "B": 14,
            "C": 16,
            "D": 14,
            "E": 35,
            "F": 65,
            "G": 18,
            "H": 22,
            "I": 14,
            "J": 22,
        },
    )


def _write_preprocessor_conditions_sheet(
    worksheet: Worksheet,
    project_name: str,
    core: str,
    build_mode: str,
    findings: list[dict[str, Any]],
) -> None:
    """
    Writes C/C++ preprocessor directives found by preprocessor_parser.py.
    """

    headers = [
    "Source File",
    "File Name",
    "Line",
    "Directive",
    "Expression",
    "Macros",
    ]

    for column_number, header in enumerate(
        headers,
        start=1,
    ):
        worksheet.cell(
            row=1,
            column=column_number,
            value=header,
        )

    _format_header_row(
        worksheet=worksheet,
        row_number=1,
        column_count=len(headers),
    )

    for row_number, finding in enumerate(
        findings,
        start=2,
    ):
        macros = finding.get("macros", [])

        if isinstance(macros, list):
            macros_text = ", ".join(
                str(macro)
                for macro in macros
            )
        else:
            macros_text = str(macros)

        # These names match src/preprocessor_parser.py.
        worksheet.cell(
            row=row_number,
            column=1,
            value=finding.get("path", ""),
        )
        worksheet.cell(
            row=row_number,
            column=2,
            value=finding.get("file_name", ""),
        )
        worksheet.cell(
            row=row_number,
            column=3,
            value=finding.get("line_number", ""),
        )
        worksheet.cell(
            row=row_number,
            column=4,
            value=finding.get("directive", ""),
        )
        worksheet.cell(
            row=row_number,
            column=5,
            value=finding.get("expression", ""),
        )
        worksheet.cell(
            row=row_number,
            column=6,
            value=macros_text,
        )

    _format_table(
        worksheet=worksheet,
        column_widths={
            "A": 80,
            "B": 30,
            "C": 12,
            "D": 16,
            "E": 85,
            "F": 65,
        },
    )


def _format_header_row(
    worksheet: Worksheet,
    row_number: int,
    column_count: int,
) -> None:
    """
    Applies common formatting to worksheet headers.
    """

    for column_number in range(1, column_count + 1):
        cell = worksheet.cell(
            row=row_number,
            column=column_number,
        )

        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )


def _format_table(
    worksheet: Worksheet,
    column_widths: dict[str, int],
) -> None:
    """
    Formats an Excel worksheet containing tabular data.
    """

    worksheet.freeze_panes = "A2"

    if worksheet.max_row >= 1:
        worksheet.auto_filter.ref = (
            f"A1:{worksheet.cell(1, worksheet.max_column).coordinate}"
            f"{worksheet.max_row}"
        )

    for column_letter, width in column_widths.items():
        worksheet.column_dimensions[column_letter].width = width

    for row in worksheet.iter_rows(
        min_row=2,
        max_row=worksheet.max_row,
        min_col=1,
        max_col=worksheet.max_column,
    ):
        for cell in row:
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )


def _format_value(value: Any) -> str:
    """
    Converts Makefile values into readable Excel text.
    """

    if isinstance(value, list):
        return " ".join(
            str(item)
            for item in value
        )

    if isinstance(value, tuple):
        return " ".join(
            str(item)
            for item in value
        )

    if isinstance(value, dict):
        return "; ".join(
            f"{key}={item}"
            for key, item in value.items()
        )

    return str(value)


def _get_entry_type(parameter: Any) -> str:
    """
    Classifies a Makefile entry for report readability.
    """

    parameter_name = str(parameter).lower()

    if "define" in parameter_name:
        return "Compiler definition"

    if "flag" in parameter_name:
        return "Compiler flag"

    if "optimization" in parameter_name:
        return "Optimization setting"

    if "compiler" in parameter_name:
        return "Compiler setting"

    return "Build setting"

def _write_filtered_compiler_switches_sheet(
    worksheet: Worksheet,
    findings: list[dict[str, Any]],
) -> None:
    """
    Writes only relevant functional compiler switches.

    Relevant findings are identified by switch_classifier.py.
    """

    headers = [
        "Source File",
        "File Name",
        "Line",
        "Directive",
        "Expression",
        "Macros",
        "Category",
        "Matched Keywords",
    ]

    _write_headers(
        worksheet=worksheet,
        headers=headers,
    )

    relevant_findings = [
        finding
        for finding in findings
        if finding.get("is_relevant", False)
    ]

    for row_number, finding in enumerate(
        relevant_findings,
        start=2,
    ):
        worksheet.cell(
            row=row_number,
            column=1,
            value=str(finding.get("path", "")),
        )
        worksheet.cell(
            row=row_number,
            column=2,
            value=str(finding.get("file_name", "")),
        )
        worksheet.cell(
            row=row_number,
            column=3,
            value=finding.get("line_number", ""),
        )
        worksheet.cell(
            row=row_number,
            column=4,
            value=str(finding.get("directive", "")),
        )
        worksheet.cell(
            row=row_number,
            column=5,
            value=str(finding.get("expression", "")),
        )
        worksheet.cell(
            row=row_number,
            column=6,
            value=_format_list_value(
                finding.get("macros", [])
            ),
        )
        worksheet.cell(
            row=row_number,
            column=7,
            value=str(finding.get("category", "OTHER")),
        )
        worksheet.cell(
            row=row_number,
            column=8,
            value=_format_list_value(
                finding.get("matched_keywords", [])
            ),
        )

    _format_table(
        worksheet=worksheet,
        column_widths={
            "A": 80,
            "B": 30,
            "C": 12,
            "D": 16,
            "E": 85,
            "F": 65,
            "G": 18,
            "H": 30,
        },
    )


def _write_excluded_conditions_sheet(
    worksheet: Worksheet,
    findings: list[dict[str, Any]],
) -> None:
    """
    Writes non-relevant conditions and the reason why they were
    excluded from the functional-switch report.
    """

    headers = [
        "Source File",
        "File Name",
        "Line",
        "Directive",
        "Expression",
        "Macros",
        "Category",
        "Filter Reason",
    ]

    _write_headers(
        worksheet=worksheet,
        headers=headers,
    )

    excluded_findings = [
        finding
        for finding in findings
        if not finding.get("is_relevant", False)
    ]

    for row_number, finding in enumerate(
        excluded_findings,
        start=2,
    ):
        worksheet.cell(
            row=row_number,
            column=1,
            value=str(finding.get("path", "")),
        )
        worksheet.cell(
            row=row_number,
            column=2,
            value=str(finding.get("file_name", "")),
        )
        worksheet.cell(
            row=row_number,
            column=3,
            value=finding.get("line_number", ""),
        )
        worksheet.cell(
            row=row_number,
            column=4,
            value=str(finding.get("directive", "")),
        )
        worksheet.cell(
            row=row_number,
            column=5,
            value=str(finding.get("expression", "")),
        )
        worksheet.cell(
            row=row_number,
            column=6,
            value=_format_list_value(
                finding.get("macros", [])
            ),
        )
        worksheet.cell(
            row=row_number,
            column=7,
            value=str(finding.get("category", "OTHER")),
        )
        worksheet.cell(
            row=row_number,
            column=8,
            value=str(finding.get("filter_reason", "")),
        )

    _format_table(
        worksheet=worksheet,
        column_widths={
            "A": 80,
            "B": 30,
            "C": 12,
            "D": 16,
            "E": 85,
            "F": 65,
            "G": 18,
            "H": 38,
        },
    )


def _write_headers(
    worksheet: Worksheet,
    headers: list[str],
) -> None:
    """
    Writes and formats a header row beginning in row 1.
    """

    for column_number, header in enumerate(
        headers,
        start=1,
    ):
        worksheet.cell(
            row=1,
            column=column_number,
            value=header,
        )

    _format_header_row(
        worksheet=worksheet,
        row_number=1,
        column_count=len(headers),
    )


def _format_list_value(value: Any) -> str:
    """
    Converts list-like values into comma-separated Excel text.
    """

    if isinstance(value, list):
        return ", ".join(
            str(item)
            for item in value
        )

    if isinstance(value, tuple):
        return ", ".join(
            str(item)
            for item in value
        )

    return str(value)