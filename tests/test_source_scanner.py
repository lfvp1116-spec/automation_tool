from pathlib import Path

import pytest

from src.source_scanner import find_source_files


def get_fixture_directory() -> Path:
    """
    Returns the directory containing controlled test files.
    """

    project_root = Path(__file__).parent.parent

    return project_root / "tests" / "fixtures"


def test_find_allowed_source_files() -> None:
    """
    Verifies that allowed C/C++ source files are found.
    """

    source_files = find_source_files(
        source_paths=[get_fixture_directory()],
        extensions=[".c", ".h", ".cpp", ".hpp"],
    )

    file_names = [
        source_file.name
        for source_file in source_files
    ]

    expected_file_names = [
    "conditional_macro_definitions_example.h",
    "ExampleModule.c",
    "ExampleModule.h",
    "ExampleModule_Cfg.h",
    "macro_definitions_example.h",
    ]

    assert file_names == expected_file_names


def test_makefile_is_not_included_as_source_file() -> None:
    """
    Verifies that .mk files are ignored when not included
    in the allowed extensions.
    """

    source_files = find_source_files(
        source_paths=[get_fixture_directory()],
        extensions=[".c", ".h", ".cpp", ".hpp"],
    )

    file_names = [
        source_file.name
        for source_file in source_files
    ]

    assert "compile_opt_example.mk" not in file_names


def test_missing_source_directory_raises_error() -> None:
    """
    Verifies that a missing source directory produces
    a clear error.
    """

    missing_directory = Path(
        "tests/fixtures/directory_does_not_exist"
    )

    with pytest.raises(FileNotFoundError):
        find_source_files(
            source_paths=[missing_directory],
            extensions=[".c", ".h"],
        )