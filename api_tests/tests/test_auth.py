import pytest

from common.allure_util import allure_step, set_case_metadata
from common.assert_util import assert_api_response, assert_case_response
from common.case_util import render_case
from common.captcha_util import get_captcha_payload
from common.db_assert_util import assert_database_case
from common.user_test_util import cleanup_auto_users_by_names
from common.yaml_util import load_yaml
from config import DATA_DIR


AUTH_CASES = load_yaml(DATA_DIR / "auth.yaml")
AUTH_FEATURE = "登录模块"


def case_id(case: dict) -> str:
    return case["id"]


def cleanup_register_user(db, payload: dict) -> None:
    username = payload.get("username")
    if username:
        cleanup_auto_users_by_names(db, [username])


@pytest.mark.parametrize("case", AUTH_CASES["login_cases"], ids=case_id)
def test_login(case, auth_api, redis_client):
    set_case_metadata(case, feature=AUTH_FEATURE, story="登录接口")

    with allure_step("准备登录接口请求数据"):
        request_data = case["request"]
        _, captcha_payload = get_captcha_payload(auth_api, redis_client)

    with allure_step("调用登录接口"):
        response = auth_api.login(
            username=request_data["username"],
            password=request_data["password"],
            **captcha_payload,
        )

    with allure_step("校验登录接口响应"):
        assert_api_response(
            response,
            case["expected"],
        )


@pytest.mark.parametrize("case", AUTH_CASES["logout_cases"], ids=case_id)
def test_logout(
    case,
    auth_api,
    auth_headers_factory,
):
    set_case_metadata(case, feature=AUTH_FEATURE, story="退出登录接口")

    with allure_step("准备退出登录接口请求数据"):
        request_data = case["request"]
        headers = auth_headers_factory() if request_data.get("auth", True) else None

    with allure_step("调用退出登录接口"):
        response = auth_api.logout(headers=headers)

    with allure_step("校验退出登录接口响应"):
        assert_case_response(response, case)


@pytest.mark.parametrize("case", AUTH_CASES["register_cases"], ids=case_id)
def test_register(
    case,
    auth_api,
    redis_client,
    db,
    unique_context,
):
    set_case_metadata(case, feature=AUTH_FEATURE, story="注册接口")

    with allure_step("获取并检查当前环境注册配置"):
        captcha_result, captcha_payload = get_captcha_payload(auth_api, redis_client)

        precheck = case.get("precheck", {})
        if precheck.get("register_enabled") and not captcha_result["registerEnabled"]:
            pytest.skip("当前环境未开启注册，跳过注册正向用例")

        if precheck.get("captcha_enabled") and not captcha_result["captchaEnabled"]:
            pytest.skip("当前环境未开启验证码，跳过验证码相关用例")

    with allure_step("准备注册接口请求数据"):
        captcha_context = {
            **unique_context,
            "captcha_uuid": captcha_payload.get("uuid", ""),
            "captcha_code": captcha_payload.get("code", ""),
        }
        rendered_case = render_case(case, captcha_context)
        payload = rendered_case["request"]["payload"]

        if captcha_result["captchaEnabled"] and rendered_case["request"].get("captcha") == "wrong":
            payload["code"] = f"wrong_{payload['code']}"

        cleanup_register_user(db, payload)

    try:
        with allure_step("调用注册接口"):
            response = auth_api.register(payload=payload)

        with allure_step("校验注册接口响应"):
            assert_case_response(response, rendered_case)

        if "database" in rendered_case:
            with allure_step("校验注册用户数据库记录"):
                assert_database_case(db, rendered_case["database"])
    finally:
        with allure_step("清理注册接口测试数据"):
            cleanup_register_user(db, payload)
