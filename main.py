from pathlib import Path

from src.config_loader import load_project_config
from src.makefile_parser import parse_makefile


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
    # 2. Real DMS Makefile: Core1 / Release
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


if __name__ == "__main__":
    main()