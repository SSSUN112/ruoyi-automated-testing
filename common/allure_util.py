from __future__ import annotations

import json
from contextlib import contextmanager, nullcontext
from typing import Any

try:
    import allure
except ImportError:
    allure = None


def is_allure_available() -> bool:
    return allure is not None


@contextmanager
def allure_step(title: str):
    if allure is None:
        with nullcontext():
            yield
        return

    with allure.step(title):
        yield


def attach_text(
    name: str,
    content: Any,
) -> None:
    if allure is None:
        return

    allure.attach(
        str(content),
        name=name,
        attachment_type=allure.attachment_type.TEXT,
    )


def attach_json(
    name: str,
    content: Any,
) -> None:
    if allure is None:
        return

    allure.attach(
        json.dumps(content, ensure_ascii=False, indent=2, default=str),
        name=name,
        attachment_type=allure.attachment_type.JSON,
    )


def set_case_metadata(
    case: dict[str, Any],
    *,
    feature: str,
    story: str,
    parent_suite: str = "RuoYi 接口自动化测试",
) -> None:
    if allure is None:
        return

    case_id = case.get("id", "")
    title = case.get("title", "")
    display_title = f"{case_id} {title}".strip()

    allure.dynamic.parent_suite(parent_suite)
    allure.dynamic.suite(feature)
    allure.dynamic.sub_suite(story)
    allure.dynamic.feature(feature)
    allure.dynamic.story(story)

    if display_title:
        allure.dynamic.title(display_title)
