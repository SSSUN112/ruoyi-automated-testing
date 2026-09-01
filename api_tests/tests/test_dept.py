import pytest

from common.allure_util import allure_step, set_case_metadata
from common.assert_util import assert_case_response
from common.case_util import render_case, request_headers
from common.db_assert_util import assert_database_case
from common.system_test_util import cleanup_auto_depts_by_names
from common.yaml_util import load_yaml
from config import DATA_DIR


DEPT_CASES = load_yaml(DATA_DIR / "dept.yaml")
DEPT_FEATURE = "部门管理模块"


def case_id(case: dict) -> str:
    return case["id"]


def set_dept_case_metadata(case: dict, story: str) -> None:
    set_case_metadata(case, feature=DEPT_FEATURE, story=story)


def cleanup_created_dept(db, payload: dict) -> None:
    dept_name = payload.get("deptName")
    if dept_name:
        cleanup_auto_depts_by_names(db, [dept_name])


def assert_response_and_database(response, case: dict, db=None) -> None:
    with allure_step("校验接口响应"):
        assert_case_response(response, case)

    if db is not None and "database" in case:
        with allure_step("校验数据库结果"):
            assert_database_case(db, case["database"])


@pytest.mark.parametrize("case", DEPT_CASES["dept_exclude_cases"], ids=case_id)
def test_get_dept_exclude_tree(case, dept_api, auth_headers):
    set_dept_case_metadata(case, "获取编辑部门下拉树接口")

    with allure_step("准备编辑部门下拉树接口请求数据"):
        request_data = case["request"]

    with allure_step("调用编辑部门下拉树接口"):
        response = dept_api.list_depts_exclude(
            dept_id=request_data["dept_id"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, case)


@pytest.mark.parametrize("case", DEPT_CASES["dept_list_cases"], ids=case_id)
def test_dept_list(case, dept_api, auth_headers):
    set_dept_case_metadata(case, "获取部门列表接口")

    with allure_step("准备部门列表接口请求数据"):
        request_data = case["request"]

    with allure_step("调用部门列表接口"):
        response = dept_api.list_depts(
            headers=request_headers(request_data, auth_headers),
            params=request_data.get("params"),
        )

    assert_response_and_database(response, case)


@pytest.mark.parametrize("case", DEPT_CASES["dept_create_cases"], ids=case_id)
def test_create_dept(case, dept_api, auth_headers, db, unique_context):
    set_dept_case_metadata(case, "新增部门接口")

    with allure_step("准备新增部门接口请求数据"):
        rendered_case = render_case(case, unique_context)
        request_data = rendered_case["request"]
        payload = request_data["payload"]
        cleanup_created_dept(db, payload)

    try:
        with allure_step("调用新增部门接口"):
            response = dept_api.create_dept(
                payload=payload,
                headers=request_headers(request_data, auth_headers),
            )

        assert_response_and_database(response, rendered_case, db)
    finally:
        with allure_step("清理新增部门接口测试数据"):
            cleanup_created_dept(db, payload)


@pytest.mark.parametrize("case", DEPT_CASES["dept_update_cases"], ids=case_id)
def test_update_dept(case, dept_api, auth_headers, db, managed_dept):
    set_dept_case_metadata(case, "编辑部门接口")

    with allure_step("准备编辑部门接口请求数据"):
        rendered_case = render_case(case, managed_dept)
        request_data = rendered_case["request"]

    with allure_step("调用编辑部门接口"):
        response = dept_api.update_dept(
            payload=request_data["payload"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", DEPT_CASES["dept_delete_cases"], ids=case_id)
def test_delete_dept(case, dept_api, auth_headers, db, managed_dept):
    set_dept_case_metadata(case, "删除部门接口")

    with allure_step("准备删除部门接口请求数据"):
        rendered_case = render_case(case, managed_dept)
        request_data = rendered_case["request"]

    with allure_step("调用删除部门接口"):
        response = dept_api.delete_dept(
            dept_ids=request_data["dept_ids"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", DEPT_CASES["dept_detail_cases"], ids=case_id)
def test_get_dept_detail(case, dept_api, auth_headers):
    set_dept_case_metadata(case, "获取部门详情接口")

    with allure_step("准备部门详情接口请求数据"):
        request_data = case["request"]

    with allure_step("调用部门详情接口"):
        response = dept_api.get_dept(
            dept_id=request_data["dept_id"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, case)
