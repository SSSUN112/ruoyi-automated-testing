import json

import pytest

from common.allure_util import allure_step, set_case_metadata
from common.case_util import render_case
from common.captcha_util import get_captcha_payload
from common.system_test_util import cleanup_menus_by_names, cleanup_roles_by_keys
from common.user_test_util import cleanup_users_by_names
from common.yaml_util import load_yaml
from config import (
    UI_DATA_DIR,
    UI_TIMEOUT,
    UI_VIEWPORT_HEIGHT,
    UI_VIEWPORT_WIDTH,
)
from ui_tests.pages.home_page import HomePage
from ui_tests.pages.login_page import LoginPage
from ui_tests.pages.menu_manage_page import MenuManagePage
from ui_tests.pages.role_manage_page import RoleManagePage
from ui_tests.pages.user_manage_page import UserManagePage


UI_PARENT_SUITE = "RuoYi UI 自动化测试"
MENU_FEATURE = "菜单管理"
MENU_CASES = load_yaml(UI_DATA_DIR / "menu.yaml")


def login_with_page_captcha(login_page, auth_api, redis_client, username: str, password: str) -> None:
    captcha_route_pattern = "**/captchaImage**"

    try:
        with allure_step("通过接口准备页面验证码数据"):
            captcha_result, captcha_payload = get_captcha_payload(auth_api, redis_client)
            captcha_code = captcha_payload.get("code")

        with allure_step("拦截验证码接口并打开登录页"):
            login_page.page.route(
                captcha_route_pattern,
                lambda route: route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(captcha_result, ensure_ascii=False),
                ),
            )
            with login_page.page.expect_response(
                lambda response: "captchaImage" in response.url
            ) as response_info:
                login_page.open()
            page_captcha_result = response_info.value.json()
            assert page_captcha_result["uuid"] == captcha_result["uuid"], page_captcha_result

        with allure_step("输入普通用户账号密码验证码并登录"):
            login_response = login_page.page.expect_response(
                lambda response: response.url.endswith("/login")
                and response.request.method == "POST"
            )
            with login_response as response_info:
                login_page.login(username, password, captcha_code)
            assert response_info.value.status == 200, response_info.value.text()
    finally:
        login_page.page.unroute(captcha_route_pattern)


def logout_and_close(context, auth_api) -> None:
    token_cookie = next(
        (
            cookie
            for cookie in context.cookies()
            if cookie.get("name") == "Admin-Token"
        ),
        None,
    )
    if token_cookie:
        auth_api.logout(headers={"Authorization": f"Bearer {token_cookie['value']}"})
    context.close()


def new_normal_user_page(browser, ui_base_url: str):
    context = browser.new_context(
        viewport={"width": UI_VIEWPORT_WIDTH, "height": UI_VIEWPORT_HEIGHT},
        ignore_https_errors=True,
    )
    context.set_default_timeout(UI_TIMEOUT)
    page = context.new_page()
    return context, page, LoginPage(page, ui_base_url), HomePage(page, ui_base_url)


@pytest.mark.ui
def test_menu_permission_change_flow(
    authenticated_page,
    browser,
    ui_base_url,
    auth_api,
    redis_client,
    db,
    unique_context,
):
    case = render_case(MENU_CASES["menu_permission_flow"], unique_context)
    menu = case["menu"]
    role = case["role"]
    user = case["user"]
    user["roleNames"] = [role["roleName"]]

    menu_page = MenuManagePage(authenticated_page, ui_base_url)
    role_page = RoleManagePage(authenticated_page, ui_base_url)
    user_page = UserManagePage(authenticated_page, ui_base_url)

    set_case_metadata(
        case,
        feature=MENU_FEATURE,
        story="菜单权限变化",
        parent_suite=UI_PARENT_SUITE,
    )

    cleanup_users_by_names(db, [user["userName"]])
    cleanup_roles_by_keys(db, [role["roleKey"]])
    cleanup_menus_by_names(db, [menu["menuName"]])

    before_context = None
    after_context = None

    try:
        with allure_step("新增菜单"):
            menu_page.open()
            menu_page.create_menu(menu)

        with allure_step("新增未分配该菜单权限的角色"):
            role_page.open()
            role_page.create_role(role)

        with allure_step("新增绑定该角色的普通用户"):
            user_page.open()
            user_page.create_user(user)

        with allure_step("分配菜单前普通用户登录并确认菜单不可见"):
            before_context, _, before_login_page, before_home_page = new_normal_user_page(
                browser,
                ui_base_url,
            )
            login_with_page_captcha(
                before_login_page,
                auth_api,
                redis_client,
                user["userName"],
                user["password"],
            )
            before_home_page.should_be_logged_in()
            before_home_page.should_not_show_sidebar_menu(menu["menuName"])
            logout_and_close(before_context, auth_api)
            before_context = None

        with allure_step("分配菜单给角色"):
            role_page.open()
            role_page.search_role(role_name=role["roleName"])
            role_page.assign_menu_to_role(role["roleName"], menu["menuName"])

        with allure_step("普通用户重新登录并确认菜单可见"):
            after_context, _, after_login_page, after_home_page = new_normal_user_page(
                browser,
                ui_base_url,
            )
            login_with_page_captcha(
                after_login_page,
                auth_api,
                redis_client,
                user["userName"],
                user["password"],
            )
            after_home_page.should_be_logged_in()
            after_home_page.should_show_sidebar_menu(menu["menuName"])
    finally:
        if before_context is not None:
            logout_and_close(before_context, auth_api)
        if after_context is not None:
            logout_and_close(after_context, auth_api)
        cleanup_users_by_names(db, [user["userName"]])
        cleanup_roles_by_keys(db, [role["roleKey"]])
        cleanup_menus_by_names(db, [menu["menuName"]])
