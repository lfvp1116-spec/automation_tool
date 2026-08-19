from pathlib import Path


def contains_path_sequence(
    path_parts: tuple[str, ...],
    sequence: tuple[str, ...],
) -> bool:
    """
    Checks whether a sequence of path parts appears inside another path.
    """

    if not sequence:
        return False

    sequence_length = len(sequence)

    for index in range(
        len(path_parts) - sequence_length + 1
    ):
        if path_parts[index:index + sequence_length] == sequence:
            return True

    return False


def is_excluded_path(
    file_path: Path,
    excluded_paths: list[str],
) -> bool:
    """
    Checks whether a file belongs to an excluded directory.

    A single directory name such as BuildTools is matched anywhere
    in the path. A relative path such as Source/Core0 must match
    as a complete consecutive path sequence.
    """

    file_parts = tuple(
        part.lower()
        for part in file_path.parts
    )

    for excluded_path in excluded_paths:
        excluded_parts = tuple(
            part.lower()
            for part in Path(excluded_path).parts
        )

        if not excluded_parts:
            continue

        # Example: BuildTools or .metadata
        if len(excluded_parts) == 1:
            if excluded_parts[0] in file_parts:
                return True

        # Example: Source/Core0
        elif contains_path_sequence(
            file_parts,
            excluded_parts,
        ):
            return True

    return False


def find_source_files(
    source_paths: list[str | Path],
    extensions: list[str],
    excluded_paths: list[str] | None = None,
) -> list[Path]:
    """
    Recursively finds source files with allowed extensions.

    Args:
        source_paths: Directories to scan.
        extensions: Allowed file extensions, for example .c and .h.
        excluded_paths: Directory names or relative paths to exclude.

    Returns:
        A sorted list of source file paths.
    """

    excluded_paths = excluded_paths or []

    allowed_extensions = {
        extension.lower()
        for extension in extensions
    }

    source_files = []

    for source_path in source_paths:
        path = Path(source_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Source path was not found: {path}"
            )

        if not path.is_dir():
            raise ValueError(
                f"The configured source path is not a directory: {path}"
            )

        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in allowed_extensions:
                continue

            if is_excluded_path(
                file_path,
                excluded_paths,
            ):
                continue

            source_files.append(file_path)

    return sorted(source_files)