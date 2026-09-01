import pytest

from common.allure_util import allure_step, set_case_metadata
from common.case_util import render_case
from common.system_test_util import cleanup_roles_by_keys
from common.yaml_util import load_yaml
from config import UI_DATA_DIR
from ui_tests.pages.role_manage_page import RoleManagePage


UI_PARENT_SUITE = "RuoYi UI 自动化测试"
ROLE_FEATURE = "角色管理"
ROLE_CASES = load_yaml(UI_DATA_DIR / "role.yaml")


@pytest.mark.ui
def test_role_manage_lifecycle_flow(
    authenticated_page,
    ui_base_url,
    db,
    unique_context,
):
    case = render_case(ROLE_CASES["role_manage_lifecycle"], unique_context)
    role = case["role"]
    updated_role = case["updated_role"]
    role_page = RoleManagePage(authenticated_page, ui_base_url)

    set_case_metadata(
        case,
        feature=ROLE_FEATURE,
        story="角色生命周期",
        parent_suite=UI_PARENT_SUITE,
    )

    cleanup_roles_by_keys(db, [role["roleKey"]])

    try:
        with allure_step("打开角色管理页面"):
            role_page.open()

        with allure_step("新增角色"):
            role_page.create_role(role)

        with allure_step("查询角色"):
            role_page.search_role(role_name=role["roleName"])
            role_page.should_contain_role(role["roleName"])

        with allure_step("修改角色"):
            role_page.update_role(role["roleName"], updated_role)

        with allure_step("查询确认角色修改成功"):
            role_page.search_role(role_name=updated_role["roleName"])
            role_page.should_contain_role(updated_role["roleName"])

        with allure_step("修改状态"):
            role_page.disable_role(updated_role["roleName"])

        with allure_step("删除角色"):
            role_page.delete_role(updated_role["roleName"])

        with allure_step("查询确认角色已删除"):
            role_page.search_role(role_name=updated_role["roleName"])
            role_page.should_not_contain_role(updated_role["roleName"])
    finally:
        cleanup_roles_by_keys(db, [role["roleKey"]])


@pytest.mark.ui
def test_role_manage_required_field_validation(
    authenticated_page,
    ui_base_url,
):
    case = ROLE_CASES["role_manage_required_validation"]
    role_page = RoleManagePage(authenticated_page, ui_base_url)

    set_case_metadata(
        case,
        feature=ROLE_FEATURE,
        story="新增角色表单校验",
        parent_suite=UI_PARENT_SUITE,
    )

    with allure_step("打开角色管理页面"):
        role_page.open()

    with allure_step("提交空白新增角色表单"):
        role_page.submit_empty_add_form()

    with allure_step("校验必填项错误提示"):
        role_page.should_show_form_errors(case["expected_errors"])


@pytest.mark.ui
def test_role_manage_duplicate_role_key_validation(
    authenticated_page,
    ui_base_url,
    db,
    unique_context,
):
    case = render_case(ROLE_CASES["role_manage_duplicate_role_key"], unique_context)
    role = case["role"]
    role_page = RoleManagePage(authenticated_page, ui_base_url)

    set_case_metadata(
        case,
        feature=ROLE_FEATURE,
        story="新增角色重复校验",
        parent_suite=UI_PARENT_SUITE,
    )

    cleanup_roles_by_keys(db, [role["roleKey"]])

    try:
        with allure_step("打开角色管理页面"):
            role_page.open()

        with allure_step("先新增一个角色"):
            role_page.create_role(role)

        with allure_step("再次新增相同权限字符的角色"):
            role_page.create_role_expect_error(
                case["duplicate_role"],
                case["expected_error"],
            )
    finally:
        cleanup_roles_by_keys(db, [role["roleKey"]])


@pytest.mark.ui
def test_role_manage_search_empty_result(
    authenticated_page,
    ui_base_url,
    unique_context,
):
    case = render_case(ROLE_CASES["role_manage_search_empty"], unique_context)
    role_page = RoleManagePage(authenticated_page, ui_base_url)

    set_case_metadata(
        case,
        feature=ROLE_FEATURE,
        story="角色查询",
        parent_suite=UI_PARENT_SUITE,
    )

    with allure_step("打开角色管理页面"):
        role_page.open()

    with allure_step("查询不存在的角色"):
        role_page.search_role(role_name=case["roleName"])

    with allure_step("校验搜索结果为空"):
        role_page.should_not_contain_role(case["roleName"])
        role_page.should_show_empty_table()
