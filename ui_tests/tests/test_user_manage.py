from pathlib import Path

import pytest

from common.allure_util import allure_step, set_case_metadata
from common.case_util import render_case
from config import BASE_DIR
from common.user_test_util import cleanup_users_by_names
from common.yaml_util import load_yaml
from config import UI_DATA_DIR
from ui_tests.pages.user_manage_page import UserManagePage


UI_PARENT_SUITE = "RuoYi UI 自动化测试"
USER_FEATURE = "用户管理"
USER_CASES = load_yaml(UI_DATA_DIR / "user.yaml")


@pytest.mark.ui
def test_user_manage_lifecycle_flow(
    authenticated_page,
    ui_base_url,
    db,
    unique_context,
):
    case = render_case(USER_CASES["user_manage_lifecycle"], unique_context)
    user = case["user"]
    updated_user = case["updated_user"]
    user_page = UserManagePage(authenticated_page, ui_base_url)

    set_case_metadata(
        case,
        feature=USER_FEATURE,
        story="用户生命周期",
        parent_suite=UI_PARENT_SUITE,
    )

    cleanup_users_by_names(db, [user["userName"]])

    try:
        with allure_step("打开用户管理页面"):
            user_page.open()

        with allure_step("新增用户"):
            user_page.create_user(user)

        with allure_step("查询用户"):
            user_page.search_user(user["userName"])
            user_page.should_contain_user(user["userName"])

        with allure_step("修改用户"):
            user_page.update_user(user["userName"], updated_user)

        with allure_step("查询确认用户修改成功"):
            user_page.search_user(user["userName"])
            user_page.should_contain_user_text(user["userName"], updated_user["nickName"])

        with allure_step("重置密码"):
            user_page.reset_password(user["userName"], case["reset_password"])

        with allure_step("修改状态"):
            user_page.search_user(user["userName"])
            user_page.disable_user(user["userName"])

        with allure_step("删除用户"):
            user_page.delete_user(user["userName"])

        with allure_step("查询确认用户已删除"):
            user_page.search_user(user["userName"])
            user_page.should_not_contain_user(user["userName"])
    finally:
        cleanup_users_by_names(db, [user["userName"]])


@pytest.mark.ui
def test_user_manage_required_field_validation(
    authenticated_page,
    ui_base_url,
):
    case = USER_CASES["user_manage_required_validation"]
    user_page = UserManagePage(authenticated_page, ui_base_url)

    set_case_metadata(
        case,
        feature=USER_FEATURE,
        story="新增用户表单校验",
        parent_suite=UI_PARENT_SUITE,
    )

    with allure_step("打开用户管理页面"):
        user_page.open()

    with allure_step("提交空白新增用户表单"):
        user_page.submit_empty_add_form()

    with allure_step("校验必填项错误提示"):
        user_page.should_show_form_errors(case["expected_errors"])


@pytest.mark.ui
def test_user_manage_format_validation(
    authenticated_page,
    ui_base_url,
    unique_context,
):
    case = render_case(USER_CASES["user_manage_format_validation"], unique_context)
    user_page = UserManagePage(authenticated_page, ui_base_url)

    set_case_metadata(
        case,
        feature=USER_FEATURE,
        story="新增用户表单校验",
        parent_suite=UI_PARENT_SUITE,
    )

    with allure_step("打开用户管理页面"):
        user_page.open()

    with allure_step("填写手机号和邮箱格式错误的新增用户表单"):
        user_page.open_add_dialog()
        user_page.fill_add_user_form(case["user"])
        user_page.submit_add_form()

    with allure_step("校验格式错误提示"):
        user_page.should_show_form_errors(case["expected_errors"])


@pytest.mark.ui
def test_user_manage_duplicate_username_validation(
    authenticated_page,
    ui_base_url,
    db,
    unique_context,
):
    case = render_case(USER_CASES["user_manage_duplicate_username"], unique_context)
    user = case["user"]
    user_page = UserManagePage(authenticated_page, ui_base_url)

    set_case_metadata(
        case,
        feature=USER_FEATURE,
        story="新增用户重复校验",
        parent_suite=UI_PARENT_SUITE,
    )

    cleanup_users_by_names(db, [user["userName"]])

    try:
        with allure_step("打开用户管理页面"):
            user_page.open()

        with allure_step("先新增一个用户"):
            user_page.create_user(user)

        with allure_step("再次新增同名用户"):
            user_page.create_user_expect_error(
                case["duplicate_user"],
                case["expected_error"],
            )
    finally:
        cleanup_users_by_names(db, [user["userName"]])


@pytest.mark.ui
def test_user_manage_search_empty_result(
    authenticated_page,
    ui_base_url,
    unique_context,
):
    case = render_case(USER_CASES["user_manage_search_empty"], unique_context)
    user_page = UserManagePage(authenticated_page, ui_base_url)

    set_case_metadata(
        case,
        feature=USER_FEATURE,
        story="查询不存在用户",
        parent_suite=UI_PARENT_SUITE,
    )

    with allure_step("打开用户管理页面"):
        user_page.open()

    with allure_step("查询不存在的用户"):
        user_page.search_user(case["userName"])

    with allure_step("校验搜索结果为空"):
        user_page.should_not_contain_user(case["userName"])
        user_page.should_show_empty_table()


@pytest.mark.ui
def test_user_manage_export_download(
    authenticated_page,
    ui_base_url,
):
    case = USER_CASES["user_manage_export"]
    user_page = UserManagePage(authenticated_page, ui_base_url)
    download_file: Path | None = None

    set_case_metadata(
        case,
        feature=USER_FEATURE,
        story="用户导出",
        parent_suite=UI_PARENT_SUITE,
    )

    try:
        with allure_step("打开用户管理页面"):
            user_page.open()

        with allure_step("导出用户列表"):
            download = user_page.export_users()

        with allure_step("校验导出文件"):
            download_dir = BASE_DIR / "reports" / "downloads"
            download_dir.mkdir(parents=True, exist_ok=True)
            download_file = download_dir / download.suggested_filename
            download.save_as(str(download_file))

            assert download.suggested_filename.startswith(case["expected"]["filename_prefix"])
            assert download.suggested_filename.endswith(case["expected"]["filename_suffix"])
            assert download_file.stat().st_size >= case["expected"]["min_bytes"]
    finally:
        if download_file is not None and download_file.exists():
            download_file.unlink()
