from datetime import datetime
from pathlib import Path


def write_execution_log(
    log_path: str | Path,
    project_name: str,
    core: str,
    build_mode: str,
    source_file_count: int,
    directive_count: int,
    report_path: str | Path,
) -> Path:
    """
    Writes a basic execution summary to a text log file.

    Returns:
        Path to the generated log file.
    """

    path = Path(log_path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    log_content = (
        "AUTOMATION TOOL - EXECUTION LOG\n"
        + "=" * 60
        + "\n"
        + f"Execution timestamp: {timestamp}\n"
        + f"Project: {project_name}\n"
        + f"Core: {core}\n"
        + f"Build mode: {build_mode}\n"
        + f"Source files analyzed: {source_file_count}\n"
        + f"Preprocessor directives found: {directive_count}\n"
        + f"Excel report generated: {report_path}\n"
    )

    path.write_text(
        log_content,
        encoding="utf-8",
    )

    return path