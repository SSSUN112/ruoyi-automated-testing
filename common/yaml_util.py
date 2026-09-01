from pathlib import Path
from typing import Any

import yaml


def load_yaml(file_path: str | Path) -> Any:
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def load_cases(
    file_path: str | Path,
    key: str,
) -> list[dict]:
    data = load_yaml(file_path)
    return data[key]