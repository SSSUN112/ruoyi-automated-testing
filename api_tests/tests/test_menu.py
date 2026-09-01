import pytest

from common.allure_util import allure_step, set_case_metadata
from common.assert_util import assert_case_response
from common.case_util import render_case, request_headers
from common.db_assert_util import assert_database_case
from common.system_test_util import cleanup_auto_menus_by_names
from common.yaml_util import load_yaml
from config import DATA_DIR


MENU_CASES = load_yaml(DATA_DIR / "menu.yaml")
MENU_FEATURE = "菜单管理模块"


def case_id(case: dict) -> str:
    return case["id"]


def set_menu_case_metadata(case: dict, story: str) -> None:
    set_case_metadata(case, feature=MENU_FEATURE, story=story)


def cleanup_created_menu(db, payload: dict) -> None:
    menu_name = payload.get("menuName")
    if menu_name:
        cleanup_auto_menus_by_names(db, [menu_name])


def assert_response_and_database(response, case: dict, db=None) -> None:
    with allure_step("校验接口响应"):
        assert_case_response(response, case)

    if db is not None and "database" in case:
        with allure_step("校验数据库结果"):
            assert_database_case(db, case["database"])


@pytest.mark.parametrize("case", MENU_CASES["menu_tree_cases"], ids=case_id)
def test_get_menu_tree(case, menu_api, auth_headers):
    set_menu_case_metadata(case, "获取菜单树接口")

    with allure_step("准备菜单树接口请求数据"):
        request_data = case["request"]

    with allure_step("调用菜单树接口"):
        response = menu_api.get_menu_tree(
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, case)


@pytest.mark.parametrize("case", MENU_CASES["menu_role_tree_cases"], ids=case_id)
def test_get_role_menu_tree(case, menu_api, auth_headers):
    set_menu_case_metadata(case, "获取角色菜单树接口")

    with allure_step("准备角色菜单树接口请求数据"):
        request_data = case["request"]

    with allure_step("调用角色菜单树接口"):
        response = menu_api.get_role_menu_tree(
            role_id=request_data["role_id"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, case)


@pytest.mark.parametrize("case", MENU_CASES["menu_list_cases"], ids=case_id)
def test_menu_list(case, menu_api, auth_headers):
    set_menu_case_metadata(case, "获取菜单列表接口")

    with allure_step("准备菜单列表接口请求数据"):
        request_data = case["request"]

    with allure_step("调用菜单列表接口"):
        response = menu_api.list_menus(
            headers=request_headers(request_data, auth_headers),
            params=request_data.get("params"),
        )

    assert_response_and_database(response, case)


@pytest.mark.parametrize("case", MENU_CASES["menu_create_cases"], ids=case_id)
def test_create_menu(case, menu_api, auth_headers, db, unique_context):
    set_menu_case_metadata(case, "新增菜单接口")

    with allure_step("准备新增菜单接口请求数据"):
        rendered_case = render_case(case, unique_context)
        request_data = rendered_case["request"]
        payload = request_data["payload"]
        cleanup_created_menu(db, payload)

    try:
        with allure_step("调用新增菜单接口"):
            response = menu_api.create_menu(
                payload=payload,
                headers=request_headers(request_data, auth_headers),
            )

        assert_response_and_database(response, rendered_case, db)
    finally:
        with allure_step("清理新增菜单接口测试数据"):
            cleanup_created_menu(db, payload)


@pytest.mark.parametrize("case", MENU_CASES["menu_update_cases"], ids=case_id)
def test_update_menu(case, menu_api, auth_headers, db, managed_menu):
    set_menu_case_metadata(case, "编辑菜单接口")

    with allure_step("准备编辑菜单接口请求数据"):
        rendered_case = render_case(case, managed_menu)
        request_data = rendered_case["request"]

    with allure_step("调用编辑菜单接口"):
        response = menu_api.update_menu(
            payload=request_data["payload"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", MENU_CASES["menu_delete_cases"], ids=case_id)
def test_delete_menu(case, menu_api, auth_headers, db, managed_menu):
    set_menu_case_metadata(case, "删除菜单接口")

    with allure_step("准备删除菜单接口请求数据"):
        rendered_case = render_case(case, managed_menu)
        request_data = rendered_case["request"]

    with allure_step("调用删除菜单接口"):
        response = menu_api.delete_menu(
            menu_ids=request_data["menu_ids"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", MENU_CASES["menu_detail_cases"], ids=case_id)
def test_get_menu_detail(case, menu_api, auth_headers):
    set_menu_case_metadata(case, "获取菜单详情接口")

    with allure_step("准备菜单详情接口请求数据"):
        request_data = case["request"]

    with allure_step("调用菜单详情接口"):
        response = menu_api.get_menu(
            menu_id=request_data["menu_id"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, case)
