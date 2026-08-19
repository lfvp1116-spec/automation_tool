from pathlib import Path

from src.config_loader import load_project_config
from src.makefile_parser import parse_makefile
from src.preprocessor_parser import find_preprocessor_directives
from src.source_scanner import find_source_files


def print_makefile_results(title: str, makefile_data: dict) -> None:
    """
    Prints the results obtained from a parsed Makefile.
    """

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    print(f"Makefile: {makefile_data['makefile']}")
    print(f"Compiler: {makefile_data['compiler']}")
    print(f"CPU: {makefile_data['cpu']}")
    print(f"FPU: {makefile_data['fpu']}")
    print(f"Instruction mode: {makefile_data['instruction_mode']}")
    print(f"Optimization: {makefile_data['optimization']}")

    print("\nExplicit -D macros found:")
    print(f"  Total: {len(makefile_data['macros'])}")

    if makefile_data["macros"]:
        for macro in makefile_data["macros"]:
            print(f"  - {macro['name']} = {macro['value']}")
    else:
        print("  - None found")

    print("\nDefinitions associated with the configured build mode:")

    if makefile_data["build_mode_definitions"]:
        for definition in makefile_data["build_mode_definitions"]:
            print(
                f"  - {definition['name']} = "
                f"{definition['value']}"
            )
    else:
        print("  - None found")


def print_source_scanner_results(
    title: str,
    source_files: list[Path],
) -> None:
    """
    Prints a summary of source files found by the scanner.
    """

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    print(f"Source files found: {len(source_files)}")

    for source_file in source_files:
        print(f"  - {source_file.name}")


def print_preprocessor_results(
    title: str,
    findings: list[dict],
) -> None:
    """
    Prints preprocessor directives detected in a source file.
    """

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    print(f"Preprocessor directives found: {len(findings)}")

    for finding in findings:
        macros = ", ".join(finding["macros"])

        print(
            f"  - Line {finding['line_number']} | "
            f"{finding['directive']} | "
            f"{finding['expression']}"
        )

        print(f"    Macros: {macros}")


def main() -> None:
    """
    Main entry point of the automation tool.
    """

    project_folder = Path(__file__).parent
    config_path = project_folder / "config" / "project_paths.yaml"

    try:
        config = load_project_config(config_path)
    except (FileNotFoundError, ValueError) as error:
        print(f"ERROR: {error}")
        return

    print("=" * 60)
    print("AUTOMATION TOOL - PROJECT CONFIGURATION")
    print("=" * 60)

    print(f"Project: {config['project_name']}")
    print(f"Project root: {config['project_root']}")
    print(f"Core: {config['core']}")
    print(f"Build mode: {config['build_mode']}")

    print("\nMakefiles configured:")
    for makefile in config["makefiles"]:
        print(f"  - {makefile}")

    print("\nSource paths configured:")
    for source_path in config["source_paths"]:
        print(f"  - {source_path}")

    print("\nExcluded paths:")
    for excluded_path in config["exclude_paths"]:
        print(f"  - {excluded_path}")

    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Controlled Makefile example
    # ---------------------------------------------------------
    fixture_makefile = (
        project_folder
        / "tests"
        / "fixtures"
        / "compile_opt_example.mk"
    )

    try:
        fixture_makefile_data = parse_makefile(fixture_makefile)
    except (FileNotFoundError, ValueError) as error:
        print(f"\nERROR while reading controlled Makefile: {error}")
        return

    print_makefile_results(
        "MAKEFILE PARSER - CONTROLLED EXAMPLE",
        fixture_makefile_data,
    )

    # ---------------------------------------------------------
    # 2. Controlled source scanner example
    # ---------------------------------------------------------
    fixture_source_path = (
        project_folder
        / "tests"
        / "fixtures"
    )

    try:
        fixture_source_files = find_source_files(
            source_paths=[fixture_source_path],
            extensions=config["extensions"],
        )
    except (FileNotFoundError, ValueError) as error:
        print(f"\nERROR while scanning controlled source files: {error}")
        return

    print_source_scanner_results(
        "SOURCE SCANNER - CONTROLLED EXAMPLE",
        fixture_source_files,
    )

    # ---------------------------------------------------------
    # 3. Controlled preprocessor parser example
    # ---------------------------------------------------------
    fixture_c_file = (
        project_folder
        / "tests"
        / "fixtures"
        / "ExampleModule.c"
    )

    try:
        fixture_findings = find_preprocessor_directives(
            fixture_c_file
        )
    except (FileNotFoundError, ValueError) as error:
        print(
            "\nERROR while parsing controlled "
            f"source file: {error}"
        )
        return

    print_preprocessor_results(
        "PREPROCESSOR PARSER - CONTROLLED EXAMPLE",
        fixture_findings,
    )

    # ---------------------------------------------------------
    # 4. Real DMS Makefile: Core1 / Release
    # ---------------------------------------------------------
    dms_makefile_relative_path = config["makefiles"][0]

    dms_makefile_path = (
        Path(config["project_root"])
        / dms_makefile_relative_path
    )

    try:
        dms_makefile_data = parse_makefile(
            dms_makefile_path,
            config["build_mode"],
        )
    except (FileNotFoundError, ValueError) as error:
        print(f"\nERROR while reading DMS Makefile: {error}")
        return

    print_makefile_results(
        "MAKEFILE PARSER - DMS / CORE1 / RELEASE",
        dms_makefile_data,
    )

    # ---------------------------------------------------------
    # 5. Real DMS source scanner: Core1 / Release
    # ---------------------------------------------------------
    dms_source_paths = [
        Path(config["project_root"]) / source_path
        for source_path in config["source_paths"]
    ]

    try:
        dms_source_files = find_source_files(
            source_paths=dms_source_paths,
            extensions=config["extensions"],
            excluded_paths=config["exclude_paths"],
        )
    except (FileNotFoundError, ValueError) as error:
        print(f"\nERROR while scanning DMS source files: {error}")
        return

    print("\n" + "=" * 60)
    print("SOURCE SCANNER - DMS / CORE1 / RELEASE")
    print("=" * 60)

    print(f"Total source files found: {len(dms_source_files)}")

    extension_counts = {}

    for source_file in dms_source_files:
        extension = source_file.suffix.lower()

        extension_counts[extension] = (
            extension_counts.get(extension, 0) + 1
        )

    print("\nFiles by extension:")

    for extension in sorted(extension_counts):
        print(f"  - {extension}: {extension_counts[extension]}")

    print("\nFirst 10 source files found:")

    for source_file in dms_source_files[:10]:
        relative_path = source_file.relative_to(
            Path(config["project_root"])
        )

        print(f"  - {relative_path}")


    # ---------------------------------------------------------
    # 6. Real DMS preprocessor parser: CddOsph.c
    # ---------------------------------------------------------
    cddosph_file = (
        Path(config["project_root"])
        / "Source"
        / "Core1"
        / "BSW"
        / "CDDs"
        / "CddOsph"
        / "core"
        / "CddOsph.c"
    )

    try:
        cddosph_findings = find_preprocessor_directives(
            cddosph_file
        )
    except (FileNotFoundError, ValueError) as error:
        print(
            "\nERROR while parsing CddOsph.c: "
            f"{error}"
        )
        return

    print("\n" + "=" * 60)
    print("PREPROCESSOR PARSER - DMS / CddOsph.c")
    print("=" * 60)

    print(
        "Preprocessor directives found: "
        f"{len(cddosph_findings)}"
    )

    print("\nFirst 10 findings:")

    for finding in cddosph_findings[:10]:
        macros = ", ".join(finding["macros"])

        print(
            f"  - Line {finding['line_number']} | "
            f"{finding['directive']} | "
            f"{finding['expression']}"
        )

        print(f"    Macros: {macros}")  

    # ---------------------------------------------------------
    # 7. Full DMS preprocessor scan: Core1 / Release
    # ---------------------------------------------------------
    all_dms_findings = []

    for source_file in dms_source_files:
        try:
            file_findings = find_preprocessor_directives(
                source_file
            )
        except (FileNotFoundError, ValueError) as error:
            print(
                "\nWARNING: Source file could not be parsed: "
                f"{error}"
            )
            continue

        all_dms_findings.extend(file_findings)

    directive_counts = {}

    for finding in all_dms_findings:
        directive = finding["directive"]

        directive_counts[directive] = (
            directive_counts.get(directive, 0) + 1
        )

    print("\n" + "=" * 60)
    print("FULL PREPROCESSOR SCAN - DMS / CORE1 / RELEASE")
    print("=" * 60)

    print(f"Source files analyzed: {len(dms_source_files)}")
    print(
        "Preprocessor directives found: "
        f"{len(all_dms_findings)}"
    )

    print("\nDirectives by type:")

    for directive in sorted(directive_counts):
        print(f"  - {directive}: {directive_counts[directive]}")

    print("\nFirst 10 findings:")

    project_root = Path(config["project_root"])

    for finding in all_dms_findings[:10]:
        finding_path = Path(finding["path"])
        relative_path = finding_path.relative_to(project_root)
        macros = ", ".join(finding["macros"])

        print(
            f"  - {relative_path} | "
            f"Line {finding['line_number']} | "
            f"{finding['directive']} | "
            f"{finding['expression']}"
        )

        print(f"    Macros: {macros}")

if __name__ == "__main__":
    main()