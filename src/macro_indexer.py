from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any, Iterable

from src.preprocessor_parser import (
    join_multiline_directives,
    read_source_file,
    remove_comments_from_text,
)


DEFINE_PATTERN = re.compile(
    r"^\s*#\s*define\s+([A-Za-z_]\w*)(.*)$"
)

MAKEFILE_DEFINE_PRIORITY = 10

BUILD_MODE_DEFINE_PRIORITY = 11

PROJECT_SOURCE_PRIORITY = 1

@dataclass(frozen=True)
class MacroDefinition:
    """
    Represents one object-like macro definition and its evidence.
    """

    name: str
    value: str
    source_file: str
    line_number: int
    source_type: str
    priority: int


def extract_macro_definition_records(
    source_file_path: str | Path,
    source_type: str = "source_file",
    priority: int = 0,
) -> list[MacroDefinition]:
    """
    Extracts object-like #define records from a source/header file.

    Function-like macros are intentionally ignored because they
    require argument expansion, which will be handled later.
    """

    path = Path(source_file_path)
    lines = read_source_file(path)

    records: list[MacroDefinition] = []

    for line_number, directive_line in join_multiline_directives(
        lines
    ):
        clean_line = remove_comments_from_text(
            directive_line
        )

        match = DEFINE_PATTERN.match(clean_line)

        if match is None:
            continue

        macro_name = match.group(1)
        raw_value = match.group(2)

        # Function-like macro:
        # #define MAX(value) ...
        #
        # The opening parenthesis immediately after the macro name
        # identifies it as function-like.
        if raw_value.startswith("("):
            continue

        macro_value = raw_value.strip()

        # #define FLAG
        # is commonly an enabled/defined flag.
        if not macro_value:
            macro_value = "1"

        records.append(
            MacroDefinition(
                name=macro_name,
                value=macro_value,
                source_file=str(path),
                line_number=line_number,
                source_type=source_type,
                priority=priority,
            )
        )

    return records


def build_macro_index(
    definition_records: Iterable[MacroDefinition],
) -> dict[str, dict[str, Any]]:
    """
    Builds an index of macro definitions.

    For every macro, all definitions are retained under
    'definitions'. The effective_definition is selected using the
    highest priority. If priorities match, the later record wins.

    This supports later precedence rules, for example:

    generic header < module config < Core1 Release config < Makefile -D
    """

    macro_index: dict[str, dict[str, Any]] = {}

    for record in definition_records:
        record_data = asdict(record)

        if record.name not in macro_index:
            macro_index[record.name] = {
                "effective_definition": record_data,
                "definitions": [record_data],
            }
            continue

        macro_entry = macro_index[record.name]

        macro_entry["definitions"].append(
            record_data
        )

        effective_definition = macro_entry[
            "effective_definition"
        ]

        if record.priority >= effective_definition["priority"]:
            macro_entry["effective_definition"] = record_data

    return macro_index


def get_effective_macro_definitions(
    macro_index: dict[str, dict[str, Any]],
) -> dict[str, str]:
    """
    Converts a macro index into the simple name/value format used by
    resolve_macro_alias().

    Example result:
        {
            "STD_ON": "1",
            "FEATURE_X": "STD_ON",
        }
    """

    effective_definitions: dict[str, str] = {}

    for macro_name, macro_entry in macro_index.items():
        effective_definition = macro_entry[
            "effective_definition"
        ]

        effective_definitions[macro_name] = str(
            effective_definition["value"]
        )

    return effective_definitions

def index_macro_definitions_from_files(
    source_files: Iterable[str | Path],
    source_type: str = "source_file",
    priority: int = 0,
) -> dict[str, dict[str, Any]]:
    """
    Extracts object-like macro definitions from multiple source files
    and builds an evidence-preserving macro index.

    Args:
        source_files: Source/header files to inspect.
        source_type: Label stored as definition evidence.
        priority: Priority assigned to all definitions in this batch.

    Returns:
        An index containing all definitions and one effective
        definition per macro.
    """

    all_records: list[MacroDefinition] = []

    for source_file in source_files:
        all_records.extend(
            extract_macro_definition_records(
                source_file_path=source_file,
                source_type=source_type,
                priority=priority,
            )
        )

    return build_macro_index(all_records)


def get_macro_definition_evidence(
    macro_name: str,
    macro_index: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Returns the effective definition evidence for one macro.

    Returns None when the macro is absent from the index.
    """

    macro_entry = macro_index.get(macro_name)

    if macro_entry is None:
        return None

    return macro_entry["effective_definition"]

def create_macro_definition_records_from_makefile(
    makefile_data: dict[str, Any],
) -> list[MacroDefinition]:
    """
    Converts parsed Makefile macros into MacroDefinition records.

    Generic -D compiler definitions receive a high priority.
    Definitions specifically associated with the selected build mode,
    such as Release, receive a slightly higher priority.

    Expected data structure from parse_makefile():
    {
        "makefile": ".../compile_opt.mk",
        "macros": [
            {"name": "FEATURE_X", "value": "STD_ON"},
        ],
        "build_mode_definitions": [
            {"name": "FEATURE_X", "value": "STD_OFF"},
        ],
    }
    """

    makefile_path = str(
        makefile_data.get(
            "makefile",
            "Unknown Makefile",
        )
    )

    records: list[MacroDefinition] = []

    compiler_macros = makefile_data.get(
        "macros",
        [],
    )

    for macro_data in compiler_macros:
        macro_name = str(
            macro_data.get("name", "")
        ).strip()

        if not macro_name:
            continue

        macro_value = macro_data.get("value")

        if macro_value is None or not str(
            macro_value
        ).strip():
            macro_value = "1"

        records.append(
            MacroDefinition(
                name=macro_name,
                value=str(macro_value),
                source_file=makefile_path,
                line_number=0,
                source_type="makefile_define",
                priority=MAKEFILE_DEFINE_PRIORITY,
            )
        )

    build_mode_macros = makefile_data.get(
        "build_mode_definitions",
        [],
    )

    for macro_data in build_mode_macros:
        macro_name = str(
            macro_data.get("name", "")
        ).strip()

        if not macro_name:
            continue

        macro_value = macro_data.get("value")

        if macro_value is None or not str(
            macro_value
        ).strip():
            macro_value = "1"

        records.append(
            MacroDefinition(
                name=macro_name,
                value=str(macro_value),
                source_file=makefile_path,
                line_number=0,
                source_type="build_mode_definition",
                priority=BUILD_MODE_DEFINE_PRIORITY,
            )
        )

    return records

def build_project_macro_index(
    source_files: Iterable[str | Path],
    makefiles_data: Iterable[dict[str, Any]],
    source_type: str = "project_source",
    source_priority: int = PROJECT_SOURCE_PRIORITY,
) -> dict[str, dict[str, Any]]:
    """
    Builds one macro index from project source/header definitions and
    parsed Makefile -D definitions.

    Source/header definitions use a lower priority than Makefile
    definitions. Therefore, a value defined through -D or through
    a build-mode definition becomes the effective value.

    Args:
        source_files: Project .c/.h/.cpp/.hpp files to inspect.
        makefiles_data: Results returned by parse_makefile().
        source_type: Evidence label for source/header definitions.
        source_priority: Priority assigned to source/header records.

    Returns:
        A macro index containing all definition evidence and the
        selected effective definition for each macro.
    """

    all_records: list[MacroDefinition] = []

    for source_file in source_files:
        all_records.extend(
            extract_macro_definition_records(
                source_file_path=source_file,
                source_type=source_type,
                priority=source_priority,
            )
        )

    for makefile_data in makefiles_data:
        all_records.extend(
            create_macro_definition_records_from_makefile(
                makefile_data=makefile_data,
            )
        )

    return build_macro_index(all_records)