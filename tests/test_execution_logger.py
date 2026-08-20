from pathlib import Path

from src.execution_logger import write_execution_log


def test_write_execution_log(tmp_path: Path) -> None:
    """
    Verifies that an execution log is created with the expected data.
    """

    log_path = tmp_path / "execution_log.txt"

    generated_log_path = write_execution_log(
        log_path=log_path,
        project_name="Controlled_Project",
        core="Core1",
        build_mode="Release",
        source_file_count=3,
        directive_count=5,
        report_path="output/compiler_switches_report.xlsx",
    )

    assert generated_log_path.exists()

    log_content = generated_log_path.read_text(
        encoding="utf-8"
    )

    assert "AUTOMATION TOOL - EXECUTION LOG" in log_content
    assert "Project: Controlled_Project" in log_content
    assert "Core: Core1" in log_content
    assert "Build mode: Release" in log_content
    assert "Source files analyzed: 3" in log_content
    assert "Preprocessor directives found: 5" in log_content
    assert (
        "Excel report generated: "
        "output/compiler_switches_report.xlsx"
    ) in log_content