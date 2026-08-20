from pathlib import Path
from typing import Any

import yaml

from src.execution_logger import write_execution_log
from src.makefile_parser import parse_makefile
from src.preprocessor_parser import find_preprocessor_directives
from src.report_generator import generate_excel_report
from src.source_scanner import find_source_files
from src.switch_classifier import (
    classify_preprocessor_finding,
)

CONFIGURATION_PATH = Path("config/project_paths.yaml")

OUTPUT_DIRECTORY = Path("output")
REPORT_PATH = OUTPUT_DIRECTORY / "compiler_switches_report.xlsx"
EXECUTION_LOG_PATH = OUTPUT_DIRECTORY / "execution_log.txt"

DEFAULT_EXCLUDED_PATHS = [
    ".venv",
    "venv",
    ".git",
    ".pytest_cache",
    "__pycache__",
    "tests",
    "output",
]


def load_project_configuration(
    configuration_path: Path,
) -> dict[str, Any]:
    """
    Loads project configuration from the YAML file.
    """

    if not configuration_path.exists():
        raise FileNotFoundError(
            "Project configuration file was not found: "
            f"{configuration_path}"
        )

    with configuration_path.open(
        "r",
        encoding="utf-8",
    ) as configuration_file:
        configuration = yaml.safe_load(
            configuration_file
        )

    if not isinstance(configuration, dict):
        raise ValueError(
            "The project configuration must contain "
            "a YAML dictionary."
        )

    return configuration


def resolve_project_paths(
    project_root: Path,
    relative_paths: list[str],
) -> list[Path]:
    """
    Converts configured relative paths into absolute project paths.
    """

    return [
        project_root / relative_path
        for relative_path in relative_paths
    ]


def parse_configured_makefiles(
    makefile_paths: list[Path],
    build_mode: str,
) -> dict[str, Any]:
    """
    Parses all configured Makefiles and combines the relevant
    compiler configuration fields for the Excel report.
    """

    parsed_makefiles: list[dict[str, Any]] = []

    for makefile_path in makefile_paths:
        if not makefile_path.exists():
            print(
                "Warning: Configured Makefile was not found: "
                f"{makefile_path}"
            )
            continue

        parsed_makefiles.append(
            parse_makefile(
                makefile_path=makefile_path,
                build_mode=build_mode,
            )
        )

    if not parsed_makefiles:
        return {
            "Compiler": "Not detected",
            "CPU": "Not detected",
            "FPU": "Not detected",
            "Instruction mode": "Not detected",
            "Optimization": "Not detected",
        }

    return {
        "Compiler": _get_first_detected_value(
            parsed_makefiles,
            "compiler",
        ),
        "CPU": _get_first_detected_value(
            parsed_makefiles,
            "cpu",
        ),
        "FPU": _get_first_detected_value(
            parsed_makefiles,
            "fpu",
        ),
        "Instruction mode": _get_first_detected_value(
            parsed_makefiles,
            "instruction_mode",
        ),
        "Optimization": _get_first_detected_value(
            parsed_makefiles,
            "optimization",
        ),
    }


def _get_first_detected_value(
    parsed_makefiles: list[dict[str, Any]],
    field_name: str,
) -> str:
    """
    Returns the first available value found across parsed Makefiles.
    """

    for makefile_data in parsed_makefiles:
        value = makefile_data.get(field_name)

        if value is not None and str(value).strip():
            return str(value)

    return "Not detected"


def scan_preprocessor_conditions(
    source_files: list[Path],
) -> list[dict[str, Any]]:
    """
    Scans every source file using preprocessor_parser.py.

    The returned findings contain:
    - path
    - file_name
    - line_number
    - directive
    - expression
    - macros
    """

    findings: list[dict[str, Any]] = []

    for source_file in source_files:
        try:
            file_findings = find_preprocessor_directives(
                source_file
            )

            findings.extend(file_findings)

        except (OSError, UnicodeDecodeError) as error:
            print(
                "Warning: Could not analyze source file: "
                f"{source_file}"
            )
            print(f"Reason: {error}")

    return findings


def main() -> None:
    """
    Main entry point for the Automation Tool.
    """

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    configuration = load_project_configuration(
        CONFIGURATION_PATH
    )

    project_name = str(
        configuration["project_name"]
    )
    project_root = Path(
        configuration["project_root"]
    )
    core = str(configuration["core"])
    build_mode = str(configuration["build_mode"])

    configured_source_paths = list(
        configuration.get("source_paths", [])
    )
    configured_makefiles = list(
        configuration.get("makefiles", [])
    )
    extensions = list(
        configuration.get("extensions", [])
    )
    configured_exclusions = list(
        configuration.get("exclude_paths", [])
    )

    excluded_paths = list(
        dict.fromkeys(
            configured_exclusions
            + DEFAULT_EXCLUDED_PATHS
        )
    )

    source_paths = resolve_project_paths(
        project_root=project_root,
        relative_paths=configured_source_paths,
    )

    makefile_paths = resolve_project_paths(
        project_root=project_root,
        relative_paths=configured_makefiles,
    )

    print("AUTOMATION TOOL STARTED")
    print(f"Project: {project_name}")
    print(f"Project root: {project_root}")
    print(f"Core: {core}")
    print(f"Build mode: {build_mode}")

    source_files = find_source_files(
        source_paths=source_paths,
        extensions=extensions,
        excluded_paths=excluded_paths,
    )

    raw_findings = scan_preprocessor_conditions(
    source_files
    )

    findings = classify_preprocessor_conditions(
    raw_findings
    )

    makefile_data = parse_configured_makefiles(
        makefile_paths=makefile_paths,
        build_mode=build_mode,
    )

    generated_report_path = generate_excel_report(
        output_path=REPORT_PATH,
        project_name=project_name,
        core=core,
        build_mode=build_mode,
        project_root=project_root,
        makefile_data=makefile_data,
        source_file_count=len(source_files),
        findings=findings,
    )

    generated_log_path = write_execution_log(
        log_path=EXECUTION_LOG_PATH,
        project_name=project_name,
        core=core,
        build_mode=build_mode,
        source_file_count=len(source_files),
        directive_count=len(findings),
        report_path=str(
            generated_report_path.resolve()
        ),
    )

    print(f"Source files analyzed: {len(source_files)}")
    print(
        "Preprocessor directives found: "
        f"{len(findings)}"
    )
    print(
        "Excel report generated: "
        f"{generated_report_path.resolve()}"
    )
    print(
        "Execution log generated: "
        f"{generated_log_path.resolve()}"
    )
    print("AUTOMATION TOOL FINISHED")

def classify_preprocessor_conditions(
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Adds classification and filtering information to every
    detected preprocessor condition.
    """

    classified_findings: list[dict[str, Any]] = []

    for finding in findings:
        classification = classify_preprocessor_finding(
            finding
        )

        classified_findings.append(
            {
                **finding,
                **classification,
            }
        )

    return classified_findings


if __name__ == "__main__":

    main()