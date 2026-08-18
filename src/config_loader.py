from pathlib import Path
import yaml


def load_project_config(config_path: str | Path) -> dict:
    """
    Reads a YAML configuration file and returns its content as a dictionary.
    """

    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file was not found: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"The configured path is not a file: {path}"
        )

    try:
        with path.open("r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except yaml.YAMLError as error:
        raise ValueError(
            f"Invalid YAML configuration: {error}"
        ) from error

    if not config:
        raise ValueError(
            "The configuration file is empty."
        )

    return config