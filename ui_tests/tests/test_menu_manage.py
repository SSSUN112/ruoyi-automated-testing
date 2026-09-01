import pytest

from common.allure_util import allure_step, set_case_metadata
from common.case_util import render_case
from common.system_test_util import cleanup_menus_by_names
from common.yaml_util import load_yaml
from config import UI_DATA_DIR
from ui_tests.pages.menu_manage_page import MenuManagePage


UI_PARENT_SUITE = "RuoYi UI 自动化测试"
MENU_FEATURE = "菜单管理"
MENU_CASES = load_yaml(UI_DATA_DIR / "menu.yaml")


@pytest.mark.ui
def test_menu_manage_lifecycle_flow(
    authenticated_page,
    ui_base_url,
    db,
    unique_context,
):
    case = render_case(MENU_CASES["menu_manage_lifecycle"], unique_context)
    menu = case["menu"]
    updated_menu = case["updated_menu"]
    menu_page = MenuManagePage(authenticated_page, ui_base_url)

    set_case_metadata(
        case,
        feature=MENU_FEATURE,
        story="菜单生命周期",
        parent_suite=UI_PARENT_SUITE,
    )

    cleanup_menus_by_names(db, [menu["menuName"], updated_menu["menuName"]])

    try:
        with allure_step("打开菜单管理页面"):
            menu_page.open()

        with allure_step("新增菜单"):
            menu_page.create_menu(menu)

        with allure_step("查询菜单"):
            menu_page.search_menu(menu["menuName"])
            menu_page.should_contain_menu(menu["menuName"])

        with allure_step("修改菜单"):
            menu_page.update_menu(menu["menuName"], updated_menu)

        with allure_step("查询确认菜单修改成功"):
            menu_page.search_menu(updated_menu["menuName"])
            menu_page.should_contain_menu(updated_menu["menuName"])

        with allure_step("删除菜单"):
            menu_page.delete_menu(updated_menu["menuName"])

        with allure_step("查询确认菜单已删除"):
            menu_page.search_menu(updated_menu["menuName"])
            menu_page.should_not_contain_menu(updated_menu["menuName"])
    finally:
        cleanup_menus_by_names(db, [menu["menuName"], updated_menu["menuName"]])


@pytest.mark.ui
def test_menu_manage_required_field_validation(
    authenticated_page,
    ui_base_url,
):
    case = MENU_CASES["menu_manage_required_validation"]
    menu_page = MenuManagePage(authenticated_page, ui_base_url)

    set_case_metadata(
        case,
        feature=MENU_FEATURE,
        story="新增菜单表单校验",
        parent_suite=UI_PARENT_SUITE,
    )

    with allure_step("打开菜单管理页面"):
        menu_page.open()

    with allure_step("提交空白新增菜单表单"):
        menu_page.submit_empty_add_form()

    with allure_step("校验必填项错误提示"):
        menu_page.should_show_form_errors(case["expected_errors"])


@pytest.mark.ui
def test_menu_manage_duplicate_name_validation(
    authenticated_page,
    ui_base_url,
    db,
    unique_context,
):
    case = render_case(MENU_CASES["menu_manage_duplicate_name"], unique_context)
    menu = case["menu"]
    menu_page = MenuManagePage(authenticated_page, ui_base_url)

    set_case_metadata(
        case,
        feature=MENU_FEATURE,
        story="新增菜单重复校验",
        parent_suite=UI_PARENT_SUITE,
    )

    cleanup_menus_by_names(db, [menu["menuName"]])

    try:
        with allure_step("打开菜单管理页面"):
            menu_page.open()

        with allure_step("先新增一个菜单"):
            menu_page.create_menu(menu)

        with allure_step("再次新增同名菜单"):
            menu_page.create_menu_expect_error(
                case["duplicate_menu"],
                case["expected_error"],
            )
    finally:
        cleanup_menus_by_names(db, [menu["menuName"]])


@pytest.mark.ui
def test_menu_manage_search_empty_result(
    authenticated_page,
    ui_base_url,
    unique_context,
):
    case = render_case(MENU_CASES["menu_manage_search_empty"], unique_context)
    menu_page = MenuManagePage(authenticated_page, ui_base_url)

    set_case_metadata(
        case,
        feature=MENU_FEATURE,
        story="菜单查询",
        parent_suite=UI_PARENT_SUITE,
    )

    with allure_step("打开菜单管理页面"):
        menu_page.open()

    with allure_step("查询不存在的菜单"):
        menu_page.search_menu(case["menuName"])

    with allure_step("校验搜索结果为空"):
        menu_page.should_not_contain_menu(case["menuName"])
        menu_page.should_show_empty_table()
