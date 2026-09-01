import json

import pytest

from common.allure_util import allure_step, set_case_metadata
from common.assert_util import assert_api_response
from config import PASSWORD, USERNAME
from ui_tests.pages.home_page import HomePage


UI_FEATURE = "UI 自动化"


@pytest.mark.ui
def test_login_page_should_be_loaded(login_page):
    set_case_metadata(
        {"id": "UI-LOGIN-PAGE-001", "title": "登录页应正常加载"},
        feature=UI_FEATURE,
        story="登录页",
    )

    with allure_step("打开登录页"):
        login_page.open()

    with allure_step("校验登录表单"):
        login_page.should_be_loaded()
        login_page.should_show_captcha_if_enabled()


@pytest.mark.ui
def test_login_success_with_page_operation(login_page, redis_client, auth_api):
    set_case_metadata(
        {"id": "UI-LOGIN-001", "title": "页面输入账号密码验证码应成功登录"},
        feature=UI_FEATURE,
        story="登录成功流程",
    )
    home_page = HomePage(login_page.page, login_page.base_url)
    captcha_route_pattern = "**/captchaImage**"

    try:
        with allure_step("通过接口准备页面验证码数据"):
            captcha_response = auth_api.get_captcha_image()
            captcha_result = assert_api_response(
                captcha_response,
                {
                    "http_status": 200,
                    "code": 200,
                    "required_fields": ["registerEnabled", "captchaEnabled", "uuid"],
                },
            )

        with allure_step("从 Redis 读取页面验证码答案"):
            captcha_code = None
            if captcha_result.get("captchaEnabled", True):
                uuid = captcha_result["uuid"]
                redis_key = f"captcha_codes:{uuid}"
                captcha_code = redis_client.get(redis_key)
                assert captcha_code is not None, f"Redis 中未找到验证码：{redis_key}"
                captcha_code = str(captcha_code)

        with allure_step("拦截验证码接口并打开登录页"):
            login_page.page.route(
                captcha_route_pattern,
                lambda route: route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(captcha_result, ensure_ascii=False),
                ),
            )
            with login_page.page.expect_response(lambda response: "captchaImage" in response.url) as response_info:
                login_page.open()
            page_captcha_result = response_info.value.json()
            assert page_captcha_result["uuid"] == captcha_result["uuid"], page_captcha_result

        with allure_step("输入账号密码验证码并点击登录"):
            with login_page.page.expect_response(
                lambda response: response.url.endswith("/login") and response.request.method == "POST"
            ):
                login_page.login(USERNAME, PASSWORD, captcha_code)

        with allure_step("校验已登录并进入首页"):
            home_page.should_be_logged_in()
    finally:
        login_page.page.unroute(captcha_route_pattern)
        token_cookie = next(
            (
                cookie
                for cookie in login_page.page.context.cookies()
                if cookie.get("name") == "Admin-Token"
            ),
            None,
        )
        if token_cookie:
            auth_api.logout(headers={"Authorization": f"Bearer {token_cookie['value']}"})
