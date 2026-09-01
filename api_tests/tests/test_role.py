import pytest

from common.allure_util import allure_step, set_case_metadata
from common.assert_util import assert_binary_response, assert_case_response
from common.case_util import render_case, request_headers
from common.db_assert_util import assert_database_case
from common.system_test_util import cleanup_auto_roles_by_keys
from common.yaml_util import load_yaml
from config import DATA_DIR


ROLE_CASES = load_yaml(DATA_DIR / "role.yaml")
ROLE_FEATURE = "角色管理模块"


def case_id(case: dict) -> str:
    return case["id"]


def set_role_case_metadata(case: dict, story: str) -> None:
    set_case_metadata(case, feature=ROLE_FEATURE, story=story)


def cleanup_created_role(db, payload: dict) -> None:
    role_key = payload.get("roleKey")
    if role_key:
        cleanup_auto_roles_by_keys(db, [role_key])


def assert_response_and_database(response, case: dict, db=None) -> None:
    with allure_step("校验接口响应"):
        assert_case_response(response, case)

    if db is not None and "database" in case:
        with allure_step("校验数据库结果"):
            assert_database_case(db, case["database"])


def assign_user_to_role(role_api, auth_headers, user_id: str, role_id: str) -> None:
    response = role_api.assign_users(
        params={
            "roleId": role_id,
            "userIds": user_id,
        },
        headers=auth_headers,
    )
    assert_response_and_database(
        response,
        {
            "expected": {
                "http_status": 200,
                "code": 200,
                "success": True,
            }
        },
    )


@pytest.mark.parametrize("case", ROLE_CASES["role_list_cases"], ids=case_id)
def test_role_list(case, role_api, auth_headers, unique_context):
    set_role_case_metadata(case, "获取角色分页列表接口")

    with allure_step("准备角色列表接口请求数据"):
        rendered_case = render_case(case, unique_context)
        request_data = rendered_case["request"]

    with allure_step("调用角色列表接口"):
        response = role_api.list_roles(
            headers=request_headers(request_data, auth_headers),
            params=request_data.get("params"),
        )

    assert_response_and_database(response, rendered_case)


@pytest.mark.parametrize("case", ROLE_CASES["role_create_cases"], ids=case_id)
def test_create_role(case, role_api, auth_headers, db, unique_context):
    set_role_case_metadata(case, "新增角色接口")

    with allure_step("准备新增角色接口请求数据"):
        rendered_case = render_case(case, unique_context)
        request_data = rendered_case["request"]
        payload = request_data["payload"]
        cleanup_created_role(db, payload)

    try:
        with allure_step("调用新增角色接口"):
            response = role_api.create_role(
                payload=payload,
                headers=request_headers(request_data, auth_headers),
            )

        assert_response_and_database(response, rendered_case, db)
    finally:
        with allure_step("清理新增角色接口测试数据"):
            cleanup_created_role(db, payload)


@pytest.mark.parametrize("case", ROLE_CASES["role_update_cases"], ids=case_id)
def test_update_role(case, role_api, auth_headers, db, managed_role):
    set_role_case_metadata(case, "编辑角色接口")

    with allure_step("准备编辑角色接口请求数据"):
        rendered_case = render_case(case, managed_role)
        request_data = rendered_case["request"]

    with allure_step("调用编辑角色接口"):
        response = role_api.update_role(
            payload=request_data["payload"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", ROLE_CASES["role_change_status_cases"], ids=case_id)
def test_change_role_status(case, role_api, auth_headers, db, managed_role):
    set_role_case_metadata(case, "修改角色状态接口")

    with allure_step("准备修改角色状态接口请求数据"):
        rendered_case = render_case(case, managed_role)
        request_data = rendered_case["request"]

    with allure_step("调用修改角色状态接口"):
        response = role_api.change_role_status(
            payload=request_data["payload"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", ROLE_CASES["role_data_scope_cases"], ids=case_id)
def test_update_role_data_scope(case, role_api, auth_headers, db, managed_role):
    set_role_case_metadata(case, "编辑角色数据权限接口")

    with allure_step("准备编辑角色数据权限接口请求数据"):
        rendered_case = render_case(case, managed_role)
        request_data = rendered_case["request"]

    with allure_step("调用编辑角色数据权限接口"):
        response = role_api.update_role_data_scope(
            payload=request_data["payload"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", ROLE_CASES["role_delete_cases"], ids=case_id)
def test_delete_role(case, role_api, auth_headers, db, managed_role):
    set_role_case_metadata(case, "删除角色接口")

    with allure_step("准备删除角色接口请求数据"):
        rendered_case = render_case(case, managed_role)
        request_data = rendered_case["request"]

    with allure_step("调用删除角色接口"):
        response = role_api.delete_role(
            role_ids=request_data["role_ids"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", ROLE_CASES["role_detail_cases"], ids=case_id)
def test_get_role_detail(case, role_api, auth_headers):
    set_role_case_metadata(case, "获取角色详情接口")

    with allure_step("准备角色详情接口请求数据"):
        request_data = case["request"]

    with allure_step("调用角色详情接口"):
        response = role_api.get_role(
            role_id=request_data["role_id"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, case)


@pytest.mark.parametrize("case", ROLE_CASES["role_dept_tree_cases"], ids=case_id)
def test_get_role_dept_tree(case, role_api, auth_headers):
    set_role_case_metadata(case, "获取角色数据权限部门树接口")

    with allure_step("准备角色数据权限部门树接口请求数据"):
        request_data = case["request"]

    with allure_step("调用角色数据权限部门树接口"):
        response = role_api.get_role_dept_tree(
            role_id=request_data["role_id"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, case)


@pytest.mark.parametrize("case", ROLE_CASES["role_allocated_user_cases"], ids=case_id)
def test_list_allocated_users(case, role_api, auth_headers):
    set_role_case_metadata(case, "获取角色已分配用户列表接口")

    with allure_step("准备已分配用户列表接口请求数据"):
        request_data = case["request"]

    with allure_step("调用已分配用户列表接口"):
        response = role_api.list_allocated_users(
            headers=request_headers(request_data, auth_headers),
            params=request_data.get("params"),
        )

    assert_response_and_database(response, case)


@pytest.mark.parametrize("case", ROLE_CASES["role_unallocated_user_cases"], ids=case_id)
def test_list_unallocated_users(case, role_api, auth_headers):
    set_role_case_metadata(case, "获取角色未分配用户列表接口")

    with allure_step("准备未分配用户列表接口请求数据"):
        request_data = case["request"]

    with allure_step("调用未分配用户列表接口"):
        response = role_api.list_unallocated_users(
            headers=request_headers(request_data, auth_headers),
            params=request_data.get("params"),
        )

    assert_response_and_database(response, case)


@pytest.mark.parametrize("case", ROLE_CASES["role_assign_user_cases"], ids=case_id)
def test_assign_users_to_role(case, role_api, auth_headers, db, managed_role, managed_user):
    set_role_case_metadata(case, "分配用户给角色接口")

    with allure_step("准备分配用户给角色接口请求数据"):
        rendered_case = render_case(case, {**managed_role, **managed_user})
        request_data = rendered_case["request"]

    with allure_step("调用分配用户给角色接口"):
        response = role_api.assign_users(
            params=request_data["params"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", ROLE_CASES["role_cancel_user_cases"], ids=case_id)
def test_cancel_role_user(case, role_api, auth_headers, db, managed_role, managed_user):
    set_role_case_metadata(case, "取消分配用户给角色接口")

    with allure_step("准备取消分配用户给角色接口请求数据"):
        rendered_case = render_case(case, {**managed_role, **managed_user})
        request_data = rendered_case["request"]
        if rendered_case.get("pre_assign"):
            assign_user_to_role(
                role_api,
                auth_headers,
                managed_user["managed_user_id"],
                managed_role["managed_role_id"],
            )

    with allure_step("调用取消分配用户给角色接口"):
        response = role_api.cancel_user(
            payload=request_data["payload"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", ROLE_CASES["role_batch_cancel_user_cases"], ids=case_id)
def test_batch_cancel_role_users(case, role_api, auth_headers, db, managed_role, managed_user):
    set_role_case_metadata(case, "批量取消分配用户给角色接口")

    with allure_step("准备批量取消分配用户给角色接口请求数据"):
        rendered_case = render_case(case, {**managed_role, **managed_user})
        request_data = rendered_case["request"]
        if rendered_case.get("pre_assign"):
            assign_user_to_role(
                role_api,
                auth_headers,
                managed_user["managed_user_id"],
                managed_role["managed_role_id"],
            )

    with allure_step("调用批量取消分配用户给角色接口"):
        response = role_api.batch_cancel_users(
            params=request_data["params"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", ROLE_CASES["role_export_cases"], ids=case_id)
def test_export_role(case, role_api, auth_headers):
    set_role_case_metadata(case, "导出角色列表接口")

    with allure_step("准备导出角色列表接口请求数据"):
        request_data = case["request"]

    with allure_step("调用导出角色列表接口"):
        response = role_api.export_roles(
            form_data=request_data.get("form", {}),
            headers=request_headers(request_data, auth_headers),
        )

    if "expected_file" in case:
        with allure_step("校验导出角色列表文件响应"):
            assert_binary_response(response, case["expected_file"])
        return

    assert_response_and_database(response, case)
