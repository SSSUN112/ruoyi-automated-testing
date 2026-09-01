from typing import Any

import pytest
import requests

from common.allure_util import allure_step, attach_json, attach_text
from common.log_util import get_logger, mask_sensitive


logger = get_logger(__name__)


def _assert_http_status(
    response: requests.Response,
    expected_status: int,
) -> None:
    assert response.status_code == expected_status, (
        "HTTP 状态码不符合预期："
        f"expected={expected_status}, "
        f"actual={response.status_code}, "
        f"body={response.text}"
    )


def _assert_json_response(response: requests.Response) -> dict:
    content_type = response.headers.get("Content-Type", "")

    assert "application/json" in content_type.lower(), (
        "响应类型不是 JSON："
        f"Content-Type={content_type}, "
        f"body={response.text}"
    )

    try:
        result = response.json()
    except ValueError:
        pytest.fail(f"响应体不是合法 JSON：{response.text}")

    assert isinstance(result, dict), f"响应 JSON 顶层不是字典：{result}"
    return result


def _assert_business_fields(
    result: dict,
    expected: dict[str, Any],
) -> None:
    if "code" in expected:
        assert result.get("code") == expected["code"], result

    if "success" in expected:
        assert result.get("success") is expected["success"], result

    if "msg_contains" in expected:
        assert expected["msg_contains"] in result.get("msg", ""), result


def _assert_required_fields(
    result: dict,
    fields: list[str],
) -> None:
    for field in fields:
        value = result.get(field)

        assert value is not None, (
            f"响应缺少字段：{field}，完整响应：{result}"
        )

        if isinstance(value, str):
            assert value.strip(), (
                f"响应字段为空：{field}，完整响应：{result}"
            )


def assert_api_response(
    response: requests.Response,
    expected: dict[str, Any],
) -> dict:
    """
    通用接口响应断言。

    expected 示例：
    {
        "http_status": 200,
        "code": 200,
        "msg_contains": "登录成功",
        "success": True,
        "required_fields": ["token"]
    }

    返回解析后的 JSON 字典，供测试用例继续进行业务断言。
    """
    expected_http_status = expected.get("http_status", 200)

    with allure_step("断言接口响应"):
        attach_json("expected", mask_sensitive(expected))
        logger.info("接口断言期望：%s", mask_sensitive(expected))

        _assert_http_status(response, expected_http_status)
        result = _assert_json_response(response)

        attach_json("actual", mask_sensitive(result))
        logger.info("接口断言实际：%s", mask_sensitive(result))

        _assert_business_fields(result, expected)
        _assert_required_fields(result, expected.get("required_fields", []))

    return result


def assert_paginated_response(
    result: dict,
    *,
    rows_field: str = "rows",
    total_field: str = "total",
    min_rows: int = 0,
    min_total: int = 0,
) -> None:
    rows = result.get(rows_field)
    total = result.get(total_field)

    assert isinstance(rows, list), result
    assert isinstance(total, int), result
    assert len(rows) >= min_rows, result
    assert total >= min_total, result


def assert_response_list_contains(
    result: dict,
    *,
    rows_field: str = "rows",
    field: str,
    value: Any,
) -> None:
    rows = result.get(rows_field, [])

    assert isinstance(rows, list), result
    assert any(row.get(field) == value for row in rows), result


def assert_list_response(
    result: dict,
    *,
    rows_field: str = "data",
    min_items: int = 0,
) -> None:
    rows = result.get(rows_field)

    assert isinstance(rows, list), result
    assert len(rows) >= min_items, result


def assert_binary_response(
    response: requests.Response,
    expected: dict[str, Any],
) -> bytes:
    expected_http_status = expected.get("http_status", 200)

    with allure_step("断言文件响应"):
        attach_json("expected", mask_sensitive(expected))
        logger.info("文件响应断言期望：%s", mask_sensitive(expected))

        _assert_http_status(response, expected_http_status)
        content = response.content

        min_bytes = expected.get("min_bytes")
        if min_bytes is not None:
            assert len(content) >= min_bytes, (
                f"文件响应大小不符合预期：expected>={min_bytes}, actual={len(content)}"
            )

        startswith = expected.get("startswith")
        if startswith:
            assert content.startswith(startswith.encode()), (
                f"文件响应头不符合预期：expected={startswith!r}, actual={content[:20]!r}"
            )

        attach_text("response_size", str(len(content)))
        logger.info("文件响应实际大小：%s bytes", len(content))

    return content


def assert_case_response(
    response: requests.Response,
    case: dict[str, Any],
) -> dict:
    result = assert_api_response(
        response=response,
        expected=case["expected"],
    )

    if "page_assert" in case:
        assert_paginated_response(result, **case["page_assert"])

    if "list_assert" in case:
        assert_list_response(result, **case["list_assert"])

    if "contains_assert" in case:
        assert_response_list_contains(result, **case["contains_assert"])

    return result
