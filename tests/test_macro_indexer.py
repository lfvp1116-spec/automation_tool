from pathlib import Path

from src.macro_indexer import (
    BUILD_MODE_DEFINE_PRIORITY,
    MAKEFILE_DEFINE_PRIORITY,
    PROJECT_SOURCE_PRIORITY,
    MacroDefinition,
    build_macro_index,
    build_project_macro_index,
    create_macro_definition_records_from_makefile,
    extract_macro_definition_records,
    get_effective_macro_definitions,
    get_macro_definition_evidence,
    index_macro_definitions_from_files,
)


def get_project_root() -> Path:
    """
    Returns the root folder of the automation_tool project.
    """

    return Path(__file__).parent.parent


def get_fixture_path() -> Path:
    """
    Returns the macro-definition fixture path.
    """

    return (
        get_project_root()
        / "tests"
        / "fixtures"
        / "macro_definitions_example.h"
    )


def test_extracts_macro_definition_records() -> None:
    records = extract_macro_definition_records(
        source_file_path=get_fixture_path(),
        source_type="header",
        priority=2,
    )

    records_by_name = {
        record.name: record
        for record in records
    }

    assert records_by_name["STD_ON"].value == "1"

    assert (
        records_by_name[
            "PROJECT_FEATURE_ENABLED"
        ].value
        == "STD_ON"
    )

    assert records_by_name["EMPTY_SWITCH"].value == "1"

    assert (
        records_by_name["STD_ON"].source_file
        == str(get_fixture_path())
    )

    assert records_by_name["STD_ON"].source_type == "header"
    assert records_by_name["STD_ON"].priority == 2
    assert records_by_name["STD_ON"].line_number > 0


def test_ignores_function_like_macro_records() -> None:
    records = extract_macro_definition_records(
        source_file_path=get_fixture_path(),
    )

    record_names = {
        record.name
        for record in records
    }

    assert "FUNCTION_LIKE_MACRO" not in record_names


def test_uses_highest_priority_as_effective_definition() -> None:
    records = [
        MacroDefinition(
            name="FEATURE_X",
            value="STD_OFF",
            source_file="generic_config.h",
            line_number=10,
            source_type="generic_header",
            priority=1,
        ),
        MacroDefinition(
            name="FEATURE_X",
            value="STD_ON",
            source_file="core1_release_cfg.h",
            line_number=20,
            source_type="core_configuration",
            priority=5,
        ),
    ]

    macro_index = build_macro_index(records)

    effective_definition = macro_index["FEATURE_X"][
        "effective_definition"
    ]

    assert effective_definition["value"] == "STD_ON"

    assert (
        effective_definition["source_file"]
        == "core1_release_cfg.h"
    )

    assert len(
        macro_index["FEATURE_X"]["definitions"]
    ) == 2


def test_uses_later_definition_when_priority_matches() -> None:
    records = [
        MacroDefinition(
            name="FEATURE_X",
            value="STD_OFF",
            source_file="first_header.h",
            line_number=10,
            source_type="header",
            priority=2,
        ),
        MacroDefinition(
            name="FEATURE_X",
            value="STD_ON",
            source_file="second_header.h",
            line_number=20,
            source_type="header",
            priority=2,
        ),
    ]

    macro_index = build_macro_index(records)

    effective_definition = macro_index["FEATURE_X"][
        "effective_definition"
    ]

    assert effective_definition["value"] == "STD_ON"

    assert (
        effective_definition["source_file"]
        == "second_header.h"
    )


def test_converts_index_to_effective_name_value_definitions() -> None:
    records = [
        MacroDefinition(
            name="STD_ON",
            value="1",
            source_file="Std_Types.h",
            line_number=10,
            source_type="header",
            priority=1,
        ),
        MacroDefinition(
            name="FEATURE_X",
            value="STD_ON",
            source_file="Project_Cfg.h",
            line_number=20,
            source_type="generated_config",
            priority=4,
        ),
    ]

    macro_index = build_macro_index(records)

    effective_definitions = get_effective_macro_definitions(
        macro_index
    )

    assert effective_definitions == {
        "STD_ON": "1",
        "FEATURE_X": "STD_ON",
    }

def test_indexes_definitions_from_multiple_files() -> None:
    fixture_path = get_fixture_path()

    macro_index = index_macro_definitions_from_files(
        source_files=[
            fixture_path,
            fixture_path,
        ],
        source_type="header",
        priority=2,
    )

    assert "STD_ON" in macro_index
    assert "FEATURE_ALIAS" in macro_index

    assert (
        macro_index["STD_ON"]["effective_definition"][
            "value"
        ]
        == "1"
    )

    assert len(
        macro_index["STD_ON"]["definitions"]
    ) == 2


def test_returns_effective_definition_evidence() -> None:
    records = [
        MacroDefinition(
            name="FEATURE_X",
            value="STD_OFF",
            source_file="generic_config.h",
            line_number=10,
            source_type="generic_header",
            priority=1,
        ),
        MacroDefinition(
            name="FEATURE_X",
            value="STD_ON",
            source_file="core1_release_cfg.h",
            line_number=20,
            source_type="core_configuration",
            priority=5,
        ),
    ]

    macro_index = build_macro_index(records)

    evidence = get_macro_definition_evidence(
        macro_name="FEATURE_X",
        macro_index=macro_index,
    )

    assert evidence is not None
    assert evidence["value"] == "STD_ON"
    assert evidence["source_file"] == "core1_release_cfg.h"
    assert evidence["line_number"] == 20
    assert evidence["source_type"] == "core_configuration"
    assert evidence["priority"] == 5


def test_returns_none_when_macro_has_no_definition() -> None:
    evidence = get_macro_definition_evidence(
        macro_name="UNKNOWN_FEATURE",
        macro_index={},
    )

    assert evidence is None

def test_creates_records_from_makefile_definitions() -> None:
    makefile_data = {
        "makefile": "BuildTools/compile_opt.mk",
        "macros": [
            {
                "name": "DET_ENABLED",
                "value": "STD_ON",
            },
            {
                "name": "EMPTY_BUILD_FLAG",
                "value": None,
            },
        ],
        "build_mode_definitions": [],
    }

    records = create_macro_definition_records_from_makefile(
        makefile_data
    )

    records_by_name = {
        record.name: record
        for record in records
    }

    assert records_by_name["DET_ENABLED"].value == "STD_ON"

    assert (
        records_by_name["DET_ENABLED"].source_file
        == "BuildTools/compile_opt.mk"
    )

    assert (
        records_by_name["DET_ENABLED"].source_type
        == "makefile_define"
    )

    assert (
        records_by_name["DET_ENABLED"].priority
        == MAKEFILE_DEFINE_PRIORITY
    )

    assert records_by_name["EMPTY_BUILD_FLAG"].value == "1"


def test_build_mode_definition_has_higher_priority() -> None:
    makefile_data = {
        "makefile": "BuildTools/compile_opt.mk",
        "macros": [
            {
                "name": "FEATURE_X",
                "value": "STD_OFF",
            },
        ],
        "build_mode_definitions": [
            {
                "name": "FEATURE_X",
                "value": "STD_ON",
            },
        ],
    }

    records = create_macro_definition_records_from_makefile(
        makefile_data
    )

    macro_index = build_macro_index(records)

    effective_definition = macro_index["FEATURE_X"][
        "effective_definition"
    ]

    assert effective_definition["value"] == "STD_ON"

    assert (
        effective_definition["source_type"]
        == "build_mode_definition"
    )

    assert (
        effective_definition["priority"]
        == BUILD_MODE_DEFINE_PRIORITY
    )


def test_makefile_definition_overrides_header_definition() -> None:
    header_record = MacroDefinition(
        name="FEATURE_X",
        value="STD_OFF",
        source_file="Project_Cfg.h",
        line_number=42,
        source_type="generated_config",
        priority=4,
    )

    makefile_data = {
        "makefile": "BuildTools/compile_opt.mk",
        "macros": [
            {
                "name": "FEATURE_X",
                "value": "STD_ON",
            },
        ],
        "build_mode_definitions": [],
    }

    makefile_records = (
        create_macro_definition_records_from_makefile(
            makefile_data
        )
    )

    macro_index = build_macro_index(
        [
            header_record,
            *makefile_records,
        ]
    )

    effective_definition = macro_index["FEATURE_X"][
        "effective_definition"
    ]

    assert effective_definition["value"] == "STD_ON"

    assert (
        effective_definition["source_file"]
        == "BuildTools/compile_opt.mk"
    )

    assert (
        effective_definition["source_type"]
        == "makefile_define"
    )

def test_builds_project_index_from_source_files() -> None:
    fixture_path = get_fixture_path()

    macro_index = build_project_macro_index(
        source_files=[fixture_path],
        makefiles_data=[],
    )

    effective_definition = macro_index["STD_ON"][
        "effective_definition"
    ]

    assert effective_definition["value"] == "1"
    assert (
        effective_definition["source_file"]
        == str(fixture_path)
    )
    assert (
        effective_definition["source_type"]
        == "project_source"
    )
    assert (
        effective_definition["priority"]
        == PROJECT_SOURCE_PRIORITY
    )


def test_makefile_definition_overrides_project_source_definition(
) -> None:
    fixture_path = get_fixture_path()

    makefile_data = {
        "makefile": "BuildTools/compile_opt.mk",
        "macros": [
            {
                "name": "PROJECT_FEATURE_ENABLED",
                "value": "STD_OFF",
            },
        ],
        "build_mode_definitions": [],
    }

    macro_index = build_project_macro_index(
        source_files=[fixture_path],
        makefiles_data=[makefile_data],
    )

    effective_definition = macro_index[
        "PROJECT_FEATURE_ENABLED"
    ]["effective_definition"]

    # The fixture header defines PROJECT_FEATURE_ENABLED as STD_ON,
    # but the Makefile must override it with STD_OFF.
    assert effective_definition["value"] == "STD_OFF"

    assert (
        effective_definition["source_file"]
        == "BuildTools/compile_opt.mk"
    )

    assert (
        effective_definition["source_type"]
        == "makefile_define"
    )

    assert (
        effective_definition["priority"]
        == MAKEFILE_DEFINE_PRIORITY
    )