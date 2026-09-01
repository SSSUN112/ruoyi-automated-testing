import pytest

from common.allure_util import allure_step, set_case_metadata
from common.assert_util import assert_binary_response, assert_case_response
from common.case_util import render_case, request_headers
from common.db_assert_util import assert_database_case
from common.system_test_util import cleanup_auto_posts_by_codes
from common.yaml_util import load_yaml
from config import DATA_DIR


POST_CASES = load_yaml(DATA_DIR / "post.yaml")
POST_FEATURE = "岗位管理模块"


def case_id(case: dict) -> str:
    return case["id"]


def set_post_case_metadata(case: dict, story: str) -> None:
    set_case_metadata(case, feature=POST_FEATURE, story=story)


def cleanup_created_post(db, payload: dict) -> None:
    post_code = payload.get("postCode")
    if post_code:
        cleanup_auto_posts_by_codes(db, [post_code])


def assert_response_and_database(response, case: dict, db=None) -> None:
    with allure_step("校验接口响应"):
        assert_case_response(response, case)

    if db is not None and "database" in case:
        with allure_step("校验数据库结果"):
            assert_database_case(db, case["database"])


@pytest.mark.parametrize("case", POST_CASES["post_list_cases"], ids=case_id)
def test_post_list(case, post_api, auth_headers):
    set_post_case_metadata(case, "获取岗位分页列表接口")

    with allure_step("准备岗位列表接口请求数据"):
        request_data = case["request"]

    with allure_step("调用岗位列表接口"):
        response = post_api.list_posts(
            headers=request_headers(request_data, auth_headers),
            params=request_data.get("params"),
        )

    assert_response_and_database(response, case)


@pytest.mark.parametrize("case", POST_CASES["post_create_cases"], ids=case_id)
def test_create_post(case, post_api, auth_headers, db, unique_context):
    set_post_case_metadata(case, "新增岗位接口")

    with allure_step("准备新增岗位接口请求数据"):
        rendered_case = render_case(case, unique_context)
        request_data = rendered_case["request"]
        payload = request_data["payload"]
        cleanup_created_post(db, payload)

    try:
        with allure_step("调用新增岗位接口"):
            response = post_api.create_post(
                payload=payload,
                headers=request_headers(request_data, auth_headers),
            )

        assert_response_and_database(response, rendered_case, db)
    finally:
        with allure_step("清理新增岗位接口测试数据"):
            cleanup_created_post(db, payload)


@pytest.mark.parametrize("case", POST_CASES["post_update_cases"], ids=case_id)
def test_update_post(case, post_api, auth_headers, db, managed_post):
    set_post_case_metadata(case, "编辑岗位接口")

    with allure_step("准备编辑岗位接口请求数据"):
        rendered_case = render_case(case, managed_post)
        request_data = rendered_case["request"]

    with allure_step("调用编辑岗位接口"):
        response = post_api.update_post(
            payload=request_data["payload"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", POST_CASES["post_delete_cases"], ids=case_id)
def test_delete_post(case, post_api, auth_headers, db, managed_post):
    set_post_case_metadata(case, "删除岗位接口")

    with allure_step("准备删除岗位接口请求数据"):
        rendered_case = render_case(case, managed_post)
        request_data = rendered_case["request"]

    with allure_step("调用删除岗位接口"):
        response = post_api.delete_post(
            post_ids=request_data["post_ids"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", POST_CASES["post_detail_cases"], ids=case_id)
def test_get_post_detail(case, post_api, auth_headers):
    set_post_case_metadata(case, "获取岗位详情接口")

    with allure_step("准备岗位详情接口请求数据"):
        request_data = case["request"]

    with allure_step("调用岗位详情接口"):
        response = post_api.get_post(
            post_id=request_data["post_id"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, case)


@pytest.mark.parametrize("case", POST_CASES["post_export_cases"], ids=case_id)
def test_export_post(case, post_api, auth_headers):
    set_post_case_metadata(case, "导出岗位列表接口")

    with allure_step("准备导出岗位列表接口请求数据"):
        request_data = case["request"]

    with allure_step("调用导出岗位列表接口"):
        response = post_api.export_posts(
            form_data=request_data.get("form", {}),
            headers=request_headers(request_data, auth_headers),
        )

    if "expected_file" in case:
        with allure_step("校验导出岗位列表文件响应"):
            assert_binary_response(response, case["expected_file"])
        return

    assert_response_and_database(response, case)
