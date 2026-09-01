from __future__ import annotations

import base64
import mimetypes
from copy import deepcopy
from pathlib import Path
from string import Template
from typing import Any

from config import BASE_DIR


def render_data(data: Any, context: dict[str, Any]) -> Any:
    if isinstance(data, dict):
        return {key: render_data(value, context) for key, value in data.items()}

    if isinstance(data, list):
        return [render_data(item, context) for item in data]

    if isinstance(data, str):
        return Template(data).safe_substitute(context)

    return data


def render_case(case: dict, context: dict[str, Any] | None = None) -> dict:
    return render_data(deepcopy(case), context or {})


def request_headers(
    request_data: dict,
    auth_headers: dict[str, str],
) -> dict[str, str] | None:
    return auth_headers if request_data.get("auth", True) else None


def build_upload_files(file_data: dict) -> dict:
    field_name = file_data["field_name"]
    filename = file_data["filename"]
    content_type = file_data.get("content_type") or mimetypes.guess_type(filename)[0]

    if "path" in file_data:
        file_path = Path(file_data["path"])
        if not file_path.is_absolute():
            file_path = BASE_DIR / file_path

        return {
            field_name: (
                filename,
                file_path.read_bytes(),
                content_type,
            )
        }

    if "text" in file_data:
        content = file_data["text"].encode(file_data.get("encoding", "utf-8"))
    elif "size_bytes" in file_data:
        fill_byte = int(file_data.get("fill_byte", 0))
        content = bytes([fill_byte]) * int(file_data["size_bytes"])
    else:
        content = base64.b64decode(file_data["base64"])

    return {
        field_name: (
            filename,
            content,
            content_type,
        )
    }
