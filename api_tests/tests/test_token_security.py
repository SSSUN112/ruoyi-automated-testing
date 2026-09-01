import allure

from common.allure_util import allure_step, set_case_metadata
from common.assert_util import assert_api_response
from common.captcha_util import get_captcha_payload
from common.system_test_util import cleanup_roles_by_keys, find_role_by_key
from common.user_test_util import cleanup_users_by_names, find_user_by_name


TOKEN_FEATURE = "Token 安全异常"
NORMAL_USER_PASSWORD = "Api@Test123"


def assert_token_rejected(response, msg_contains: str = "重新登录") -> dict:
    return assert_api_response(
        response,
        {
            "http_status": 200,
            "code": 401,
            "success": False,
            "msg_contains": msg_contains,
        },
    )


def assert_forbidden(response) -> dict:
    return assert_api_response(
        response,
        {
            "http_status": 200,
            "code": 403,
            "success": False,
            "msg_contains": "无此接口权限",
        },
    )


def assert_success(response, msg_contains: str | None = None) -> dict:
    expected = {
        "http_status": 200,
        "code": 200,
        "success": True,
    }
    if msg_contains:
        expected["msg_contains"] = msg_contains
    return assert_api_response(response, expected)


def login_as_user(auth_api, redis_client, user_name: str, password: str) -> dict[str, str]:
    _, captcha_payload = get_captcha_payload(auth_api, redis_client)
    response = auth_api.login(
        username=user_name,
        password=password,
        **captcha_payload,
    )
    result = assert_api_response(
        response,
        {
            "http_status": 200,
            "code": 200,
            "success": True,
            "required_fields": ["token"],
        },
    )
    return {"Authorization": f"Bearer {result['token']}"}



def test_invalid_token_rejected(user_api):
    set_case_metadata(
        {"id": "TOKEN-SECURITY-001", "title": "错误 Token 应被拒绝"},
        feature=TOKEN_FEATURE,
        story="错误 Token",
    )

    with allure_step("携带错误 Token 请求受保护接口"):
        response = user_api.list_users(
            params={"pageNum": 1, "pageSize": 10},
            headers={"Authorization": "Bearer invalid.token.value"},
        )

    with allure_step("校验 Token 被拒绝"):
        assert_token_rejected(response)



def test_logged_out_token_rejected(
    auth_api,
    auth_headers_factory,
    user_api,
):
    set_case_metadata(
        {"id": "TOKEN-SECURITY-002", "title": "已退出登录 Token 应被拒绝"},
        feature=TOKEN_FEATURE,
        story="已失效 Token",
    )

    with allure_step("管理员登录"):
        headers = auth_headers_factory()

    with allure_step("退出登录使 Token 失效"):
        assert_success(auth_api.logout(headers=headers), "退出成功")

    with allure_step("使用旧 Token 请求受保护接口"):
        response = user_api.list_users(
            params={"pageNum": 1, "pageSize": 10},
            headers=headers,
        )

    with allure_step("校验旧 Token 被拒绝"):
        assert_token_rejected(response)



def test_normal_user_without_permission_forbidden(
    auth_api,
    role_api,
    user_api,
    auth_headers,
    redis_client,
    db,
    unique_context,
):
    set_case_metadata(
        {"id": "TOKEN-SECURITY-003", "title": "普通用户无权限访问应被拒绝"},
        feature=TOKEN_FEATURE,
        story="无权限访问",
    )

    suffix = unique_context["unique"]
    role_key = unique_context["unique_role_key"]
    role_name = f"sec_role_{suffix}"
    user_name = f"api_auto_sec_{suffix}"
    role_id = None

    cleanup_users_by_names(db, [user_name])
    cleanup_roles_by_keys(db, [role_key])

    try:
        with allure_step("新增低权限角色"):
            assert_success(
                role_api.create_role(
                    payload={
                        "roleName": role_name,
                        "roleKey": role_key,
                        "roleSort": 99,
                        "status": "0",
                        "menuIds": [1],
                        "menuCheckStrictly": True,
                        "deptCheckStrictly": True,
                        "remark": "token security low permission role",
                    },
                    headers=auth_headers,
                ),
                "新增成功",
            )
            role_row = find_role_by_key(db, role_key)
            assert role_row is not None, f"role was not created: {role_key}"
            role_id = str(role_row["role_id"])

        with allure_step("新增绑定低权限角色的普通用户"):
            assert_success(
                user_api.create_user(
                    payload={
                        "deptId": 105,
                        "userName": user_name,
                        "nickName": f"sec_user_{suffix}",
                        "password": NORMAL_USER_PASSWORD,
                        "email": f"{user_name}@example.com",
                        "phonenumber": unique_context["unique_phone"],
                        "sex": "2",
                        "status": "0",
                        "roleIds": [int(role_id)],
                        "postIds": [4],
                        "remark": "token security normal user",
                    },
                    headers=auth_headers,
                ),
                "新增成功",
            )
            user_row = find_user_by_name(db, user_name)
            assert user_row is not None, f"user was not created: {user_name}"

        with allure_step("普通用户登录"):
            normal_headers = login_as_user(
                auth_api,
                redis_client,
                user_name,
                NORMAL_USER_PASSWORD,
            )

        with allure_step("使用普通用户请求用户列表接口"):
            response = user_api.list_users(
                params={"pageNum": 1, "pageSize": 10},
                headers=normal_headers,
            )

        with allure_step("校验无权限响应"):
            assert_forbidden(response)
    finally:
        with allure_step("清理 Token 安全异常测试数据"):
            cleanup_users_by_names(db, [user_name])
            cleanup_roles_by_keys(db, [role_key])
