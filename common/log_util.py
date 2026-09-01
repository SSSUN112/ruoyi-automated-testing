from __future__ import annotations

import logging
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_DIR = Path(os.getenv("RUOYI_API_TEST_LOG_DIR", DEFAULT_LOG_DIR))
LOG_FILE = LOG_DIR / f"api_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
SENSITIVE_KEYS = {"authorization", "password", "token", "access_token"}


def _ensure_log_dir() -> Path:
    global LOG_DIR, LOG_FILE

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        LOG_DIR = Path(tempfile.gettempdir()) / "ruoyi-api-test-logs"
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        LOG_FILE = LOG_DIR / LOG_FILE.name

    return LOG_DIR


def _fallback_to_temp_log_dir() -> None:
    global LOG_DIR, LOG_FILE

    LOG_DIR = Path(tempfile.gettempdir()) / "ruoyi-api-test-logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE = LOG_DIR / LOG_FILE.name


def setup_logging() -> None:
    _ensure_log_dir()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if any(getattr(handler, "_api_auto_handler", False) for handler in root_logger.handlers):
        return

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    except PermissionError:
        _fallback_to_temp_log_dir()
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")

    file_handler.setFormatter(formatter)
    file_handler._api_auto_handler = True

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler._api_auto_handler = True

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)


def mask_sensitive(data: Any) -> Any:
    if isinstance(data, dict):
        return {
            key: "***"
            if str(key).lower() in SENSITIVE_KEYS
            else mask_sensitive(value)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [mask_sensitive(item) for item in data]

    if isinstance(data, tuple):
        return tuple(mask_sensitive(item) for item in data)

    if isinstance(data, str):
        data = re.sub(
            r"(Bearer\s+)[A-Za-z0-9._-]+",
            r"\1***",
            data,
        )
        data = re.sub(
            r'("(?:token|access_token|password)"\s*:\s*")[^"]+(")',
            r"\1***\2",
            data,
            flags=re.IGNORECASE,
        )
        return data

    return data
