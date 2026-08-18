from pathlib import Path

import pytest

from src.makefile_parser import parse_makefile


def get_fixture_makefile_path() -> Path:
    """
    Returns the path to the controlled Makefile fixture.
    """

    project_root = Path(__file__).parent.parent

    return (
        project_root
        / "tests"
        / "fixtures"
        / "compile_opt_example.mk"
    )


def test_parse_compile_options() -> None:
    """
    Verifies that the parser extracts the main compiler options.
    """

    result = parse_makefile(get_fixture_makefile_path())

    assert result["compiler"] == "iccarm.exe"
    assert result["cpu"] == "Cortex-M4F"
    assert result["fpu"] == "VFPv4-SP"
    assert result["instruction_mode"] == "Thumb"
    assert result["optimization"] == "-Oh"


def test_extract_define_macros() -> None:
    """
    Verifies that macros declared with -D are extracted correctly.
    """

    result = parse_makefile(get_fixture_makefile_path())

    expected_macros = [
        {"name": "DET_DEBUG_ENABLED", "value": "STD_OFF"},
        {"name": "INTEGRATION_TEST", "value": "0"},
        {"name": "LK_DEBUG", "value": None},
        {"name": "FEATURE_X", "value": "1"},
    ]

    assert result["macros"] == expected_macros


def test_extract_release_build_mode_definitions() -> None:
    """
    Verifies that definitions associated with Release are extracted.
    """

    result = parse_makefile(
        get_fixture_makefile_path(),
        build_mode="Release",
    )

    expected_definitions = [
        {"name": "LK_RELEASE", "value": "1"},
    ]

    expected_definitions = [
    {"name": "LK_RELEASE", "value": "1"},
]

    assert result["build_mode_definitions"] == expected_definitions


def test_missing_makefile_raises_error() -> None:
    """
    Verifies that a missing Makefile produces a clear error.
    """

    missing_path = Path("tests/fixtures/file_does_not_exist.mk")

    with pytest.raises(FileNotFoundError):
        parse_makefile(missing_path)