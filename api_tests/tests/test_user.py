import pytest

from common.allure_util import allure_step, set_case_metadata
from common.assert_util import assert_api_response, assert_case_response
from common.case_util import build_upload_files, render_case, request_headers
from common.db_assert_util import assert_database_case
from common.user_test_util import cleanup_auto_users_by_names
from common.yaml_util import load_yaml
from config import DATA_DIR


USER_CASES = load_yaml(DATA_DIR / "user.yaml")
USER_FEATURE = "用户管理模块"


def case_id(case: dict) -> str:
    return case["id"]


def set_user_case_metadata(case: dict, story: str) -> None:
    set_case_metadata(case, feature=USER_FEATURE, story=story)


def cleanup_created_user(db, payload: dict) -> None:
    user_name = payload.get("userName")
    if user_name:
        cleanup_auto_users_by_names(db, [user_name])


def assert_response_and_database(
    response,
    case: dict,
    db=None,
) -> None:
    with allure_step("校验接口响应"):
        assert_case_response(response, case)

    if db is not None and "database" in case:
        with allure_step("校验数据库结果"):
            assert_database_case(db, case["database"])


@pytest.mark.parametrize("case", USER_CASES["user_list_cases"], ids=case_id)
def test_user_list(
    case,
    user_api,
    auth_headers,
    db,
):
    set_user_case_metadata(case, "获取用户分页列表接口")

    with allure_step("准备用户列表接口请求数据"):
        request_data = case["request"]

    with allure_step("调用用户列表接口"):
        response = user_api.list_users(
            headers=request_headers(request_data, auth_headers),
            params=request_data.get("params"),
        )

    assert_response_and_database(response, case, db)


@pytest.mark.parametrize("case", USER_CASES["user_create_cases"], ids=case_id)
def test_create_user(
    case,
    user_api,
    auth_headers,
    db,
    unique_context,
):
    set_user_case_metadata(case, "新增用户接口")

    with allure_step("准备新增用户接口请求数据"):
        rendered_case = render_case(case, unique_context)
        request_data = rendered_case["request"]
        payload = request_data["payload"]
        cleanup_created_user(db, payload)

    try:
        with allure_step("调用新增用户接口"):
            response = user_api.create_user(
                payload=payload,
                headers=request_headers(request_data, auth_headers),
            )

        assert_response_and_database(response, rendered_case, db)
    finally:
        with allure_step("清理新增用户接口测试数据"):
            cleanup_created_user(db, payload)


@pytest.mark.parametrize("case", USER_CASES["user_update_cases"], ids=case_id)
def test_update_user(
    case,
    user_api,
    auth_headers,
    db,
    managed_user,
):
    set_user_case_metadata(case, "编辑用户接口")

    with allure_step("准备编辑用户接口请求数据"):
        rendered_case = render_case(case, managed_user)
        request_data = rendered_case["request"]

    with allure_step("调用编辑用户接口"):
        response = user_api.update_user(
            payload=request_data["payload"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", USER_CASES["user_delete_cases"], ids=case_id)
def test_delete_user(
    case,
    user_api,
    auth_headers,
    db,
    managed_user,
):
    set_user_case_metadata(case, "删除用户接口")

    with allure_step("准备删除用户接口请求数据"):
        rendered_case = render_case(case, managed_user)
        request_data = rendered_case["request"]

    with allure_step("调用删除用户接口"):
        response = user_api.delete_user(
            user_ids=request_data["user_ids"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", USER_CASES["user_reset_pwd_cases"], ids=case_id)
def test_reset_user_password(
    case,
    user_api,
    auth_headers,
    managed_user,
):
    set_user_case_metadata(case, "重置用户密码接口")

    with allure_step("准备重置用户密码接口请求数据"):
        rendered_case = render_case(case, managed_user)
        request_data = rendered_case["request"]

    with allure_step("调用重置用户密码接口"):
        response = user_api.reset_user_password(
            payload=request_data["payload"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case)


@pytest.mark.parametrize("case", USER_CASES["user_change_status_cases"], ids=case_id)
def test_change_user_status(
    case,
    user_api,
    auth_headers,
    db,
    managed_user,
):
    set_user_case_metadata(case, "修改用户状态接口")

    with allure_step("准备修改用户状态接口请求数据"):
        rendered_case = render_case(case, managed_user)
        request_data = rendered_case["request"]

    with allure_step("调用修改用户状态接口"):
        response = user_api.change_user_status(
            payload=request_data["payload"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case, db)


@pytest.mark.parametrize("case", USER_CASES["user_profile_get_cases"], ids=case_id)
def test_get_user_profile(
    case,
    user_api,
    auth_headers,
):
    set_user_case_metadata(case, "获取用户个人信息接口")

    with allure_step("准备获取个人信息接口请求数据"):
        request_data = case["request"]

    with allure_step("调用获取个人信息接口"):
        response = user_api.get_user_profile(
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, case)


@pytest.mark.parametrize("case", USER_CASES["user_profile_update_cases"], ids=case_id)
def test_update_user_profile(
    case,
    user_api,
    auth_headers,
    db,
    unique_context,
):
    set_user_case_metadata(case, "修改用户个人信息接口")

    with allure_step("准备修改个人信息接口请求数据"):
        rendered_case = render_case(case, unique_context)
        request_data = rendered_case["request"]
        profile_response = user_api.get_user_profile(headers=auth_headers)
        profile_result = assert_api_response(
            profile_response,
            {
                "http_status": 200,
                "code": 200,
                "required_fields": ["data"],
            },
        )
        old_profile = profile_result["data"]

    try:
        with allure_step("调用修改个人信息接口"):
            response = user_api.update_user_profile(
                payload=request_data["payload"],
                headers=request_headers(request_data, auth_headers),
            )

        assert_response_and_database(response, rendered_case)
    finally:
        with allure_step("恢复个人信息测试数据"):
            user_api.update_user_profile(
                payload={
                    "nickName": old_profile.get("nickName"),
                    "email": old_profile.get("email"),
                    "phonenumber": old_profile.get("phonenumber"),
                    "sex": old_profile.get("sex"),
                },
                headers=auth_headers,
            )


@pytest.mark.parametrize("case", USER_CASES["user_options_cases"], ids=case_id)
def test_get_user_options(
    case,
    user_api,
    auth_headers,
):
    set_user_case_metadata(case, "获取用户岗位和角色列表接口")

    with allure_step("准备获取岗位和角色列表接口请求数据"):
        request_data = case["request"]

    with allure_step("调用获取岗位和角色列表接口"):
        response = user_api.get_user_options(
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, case)


@pytest.mark.parametrize("case", USER_CASES["user_detail_cases"], ids=case_id)
def test_get_user_detail(
    case,
    user_api,
    auth_headers,
    managed_user,
):
    set_user_case_metadata(case, "获取用户详情接口")

    with allure_step("准备获取用户详情接口请求数据"):
        rendered_case = render_case(case, managed_user)
        request_data = rendered_case["request"]

    with allure_step("调用获取用户详情接口"):
        response = user_api.get_user(
            user_id=request_data["user_id"],
            headers=request_headers(request_data, auth_headers),
        )

    assert_response_and_database(response, rendered_case)


@pytest.mark.parametrize("case", USER_CASES["user_avatar_cases"], ids=case_id)
def test_upload_user_avatar(
    case,
    user_api,
    auth_headers,
    db,
):
    set_user_case_metadata(case, "修改用户头像接口")

    with allure_step("准备上传头像接口请求数据"):
        request_data = case["request"]
        old_avatar = db.query_one(
            "SELECT avatar FROM sys_user WHERE user_name = %s LIMIT 1",
            ("admin",),
        )
        old_avatar_value = old_avatar["avatar"] if old_avatar else ""

    try:
        with allure_step("调用上传头像接口"):
            response = user_api.upload_user_avatar(
                files=build_upload_files(request_data["file"]),
                headers=request_headers(request_data, auth_headers),
            )

        assert_response_and_database(response, case)
    finally:
        with allure_step("恢复头像测试数据"):
            db.execute(
                "UPDATE sys_user SET avatar = %s WHERE user_name = %s",
                (old_avatar_value, "admin"),
            )
