import allure

from common.allure_util import allure_step, set_case_metadata
from common.assert_util import assert_api_response
from common.captcha_util import get_captcha_payload
from common.system_test_util import (
    cleanup_depts_by_names,
    cleanup_menus_by_names,
    cleanup_posts_by_codes,
    cleanup_roles_by_keys,
    find_dept_by_name,
    find_menu_by_name,
    find_post_by_code,
    find_role_by_key,
)
from common.user_test_util import cleanup_users_by_names, find_user_by_name


FLOW_FEATURE = "业务流程自动化"
INITIAL_PASSWORD = "Api@Test123"
RESET_PASSWORD = "Api@Test456"


def assert_success(response, msg_contains: str | None = None) -> dict:
    expected = {
        "http_status": 200,
        "code": 200,
        "success": True,
    }
    if msg_contains:
        expected["msg_contains"] = msg_contains

    return assert_api_response(response, expected)


def assert_row_exists(row: dict | None, message: str) -> dict:
    assert row is not None, message
    return row


def cleanup_flow_data(
    db,
    *,
    user_names: list[str] | None = None,
    role_keys: list[str] | None = None,
    menu_names: list[str] | None = None,
    post_codes: list[str] | None = None,
    dept_names: list[str] | None = None,
) -> None:
    cleanup_users_by_names(db, user_names or [])
    cleanup_roles_by_keys(db, role_keys or [])
    cleanup_menus_by_names(db, menu_names or [])
    cleanup_posts_by_codes(db, post_codes or [])
    cleanup_depts_by_names(db, dept_names or [])


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


def assert_user_not_listed(user_api, headers: dict, user_name: str) -> None:
    result = assert_success(
        user_api.list_users(
            params={
                "pageNum": 1,
                "pageSize": 10,
                "userName": user_name,
            },
            headers=headers,
        )
    )
    assert all(row.get("userName") != user_name for row in result["rows"]), result


def flatten_routes(routes: list[dict]) -> list[dict]:
    flattened = []
    for route in routes:
        flattened.append(route)
        flattened.extend(flatten_routes(route.get("children") or []))
    return flattened


def route_title_exists(routes: list[dict], title: str) -> bool:
    for route in flatten_routes(routes):
        if (route.get("meta") or {}).get("title") == title:
            return True
    return False


@allure.title("用户生命周期流程")
def test_user_lifecycle_flow(
    auth_headers_factory,
    user_api,
    auth_api,
    redis_client,
    db,
    unique_context,
):
    set_case_metadata(
        {"id": "FLOW-USER-LIFECYCLE-001", "title": "用户生命周期流程"},
        feature=FLOW_FEATURE,
        story="登录 -> 新增用户 -> 查询用户 -> 修改用户 -> 重置密码 -> 修改状态 -> 删除用户 -> 查询确认删除",
    )

    suffix = unique_context["unique"]
    user_name = f"api_auto_life_{suffix}"
    updated_nick = f"flow_user_updated_{suffix}"
    admin_headers = None
    user_id = None

    cleanup_flow_data(db, user_names=[user_name])

    try:
        with allure_step("管理员登录"):
            admin_headers = auth_headers_factory()

        with allure_step("新增用户"):
            assert_success(
                user_api.create_user(
                    payload={
                        "deptId": 105,
                        "userName": user_name,
                        "nickName": f"flow_user_{suffix}",
                        "password": INITIAL_PASSWORD,
                        "email": f"{user_name}@example.com",
                        "phonenumber": unique_context["unique_phone"],
                        "sex": "2",
                        "status": "0",
                        "roleIds": [2],
                        "postIds": [4],
                        "remark": "flow user lifecycle",
                    },
                    headers=admin_headers,
                ),
                "新增成功",
            )
            user_row = assert_row_exists(
                find_user_by_name(db, user_name),
                f"user was not created: {user_name}",
            )
            user_id = str(user_row["user_id"])

        with allure_step("查询用户"):
            list_result = assert_success(
                user_api.list_users(
                    params={
                        "pageNum": 1,
                        "pageSize": 10,
                        "userName": user_name,
                    },
                    headers=admin_headers,
                )
            )
            assert any(row.get("userName") == user_name for row in list_result["rows"]), list_result

            detail_result = assert_success(user_api.get_user(user_id, headers=admin_headers))
            assert detail_result["data"]["userName"] == user_name, detail_result

        with allure_step("修改用户"):
            assert_success(
                user_api.update_user(
                    payload={
                        "userId": user_id,
                        "deptId": 105,
                        "userName": user_name,
                        "nickName": updated_nick,
                        "email": f"{user_name}@example.com",
                        "phonenumber": unique_context["unique_phone"],
                        "sex": "1",
                        "status": "0",
                        "roleIds": [2],
                        "postIds": [4],
                        "role": [],
                    },
                    headers=admin_headers,
                ),
                "更新成功",
            )
            updated_detail = assert_success(user_api.get_user(user_id, headers=admin_headers))
            assert updated_detail["data"]["nickName"] == updated_nick, updated_detail

        with allure_step("重置密码"):
            assert_success(
                user_api.reset_user_password(
                    payload={
                        "userId": user_id,
                        "password": RESET_PASSWORD,
                    },
                    headers=admin_headers,
                ),
                "更新成功",
            )
            login_as_user(auth_api, redis_client, user_name, RESET_PASSWORD)

        with allure_step("修改用户状态"):
            assert_success(
                user_api.change_user_status(
                    payload={
                        "userId": user_id,
                        "status": "1",
                    },
                    headers=admin_headers,
                ),
                "更新成功",
            )
            status_row = assert_row_exists(
                find_user_by_name(db, user_name),
                f"user was not found after status change: {user_name}",
            )
            assert status_row["status"] == "1", status_row

        with allure_step("删除用户"):
            assert_success(user_api.delete_user(user_id, headers=admin_headers), "删除成功")

        with allure_step("查询确认用户已删除"):
            assert_user_not_listed(user_api, admin_headers, user_name)
            active_row = db.query_one(
                """
                SELECT user_id
                FROM sys_user
                WHERE user_name = %s AND del_flag = '0'
                LIMIT 1
                """,
                (user_name,),
            )
            assert active_row is None, active_row
    finally:
        with allure_step("清理用户生命周期流程测试数据"):
            cleanup_flow_data(db, user_names=[user_name])


@allure.title("部门岗位用户关联流程")
def test_dept_post_user_relation_flow(
    dept_api,
    post_api,
    user_api,
    auth_headers,
    db,
    unique_context,
):
    set_case_metadata(
        {"id": "FLOW-DEPT-POST-USER-001", "title": "部门岗位用户关联流程"},
        feature=FLOW_FEATURE,
        story="新增部门 -> 新增岗位 -> 新增用户绑定部门岗位 -> 查询用户详情 -> 删除用户 -> 删除岗位 -> 删除部门",
    )

    suffix = unique_context["unique"]
    dept_name = f"flow_dept_{suffix}"
    post_code = f"api_auto_post_flow_{suffix}"
    post_name = f"flow_post_{suffix}"
    user_name = f"api_auto_rel_{suffix}"
    dept_id = None
    post_id = None
    user_id = None

    cleanup_flow_data(
        db,
        user_names=[user_name],
        post_codes=[post_code],
        dept_names=[dept_name],
    )

    try:
        with allure_step("新增部门"):
            assert_success(
                dept_api.create_dept(
                    payload={
                        "parentId": 101,
                        "deptName": dept_name,
                        "orderNum": 99,
                        "leader": "flow",
                        "phone": "13800138000",
                        "email": "flow_dept@example.com",
                        "status": "0",
                    },
                    headers=auth_headers,
                ),
                "新增成功",
            )
            dept_row = assert_row_exists(
                find_dept_by_name(db, dept_name, parent_id=101),
                f"dept was not created: {dept_name}",
            )
            dept_id = str(dept_row["dept_id"])

        with allure_step("新增岗位"):
            assert_success(
                post_api.create_post(
                    payload={
                        "postCode": post_code,
                        "postName": post_name,
                        "postSort": 99,
                        "status": "0",
                        "remark": "flow temporary post",
                    },
                    headers=auth_headers,
                ),
                "新增成功",
            )
            post_row = assert_row_exists(
                find_post_by_code(db, post_code),
                f"post was not created: {post_code}",
            )
            post_id = str(post_row["post_id"])

        with allure_step("新增用户并绑定部门岗位"):
            assert_success(
                user_api.create_user(
                    payload={
                        "deptId": int(dept_id),
                        "userName": user_name,
                        "nickName": f"flow_relation_user_{suffix}",
                        "password": INITIAL_PASSWORD,
                        "email": f"{user_name}@example.com",
                        "phonenumber": unique_context["unique_phone"],
                        "sex": "2",
                        "status": "0",
                        "roleIds": [2],
                        "postIds": [int(post_id)],
                        "remark": "flow dept post user relation",
                    },
                    headers=auth_headers,
                ),
                "新增成功",
            )
            user_row = assert_row_exists(
                find_user_by_name(db, user_name),
                f"user was not created: {user_name}",
            )
            user_id = str(user_row["user_id"])

        with allure_step("查询用户详情并校验部门岗位关联"):
            result = assert_success(user_api.get_user(user_id, headers=auth_headers))
            assert result["data"]["userName"] == user_name, result
            assert str(result["data"]["deptId"]) == dept_id, result
            assert int(post_id) in result["postIds"], result

        with allure_step("删除用户"):
            assert_success(user_api.delete_user(user_id, headers=auth_headers), "删除成功")
            assert_user_not_listed(user_api, auth_headers, user_name)

        with allure_step("删除岗位"):
            assert_success(post_api.delete_post(post_id, headers=auth_headers), "删除成功")
            assert find_post_by_code(db, post_code) is None

        with allure_step("删除部门"):
            assert_success(dept_api.delete_dept(dept_id, headers=auth_headers), "删除成功")
            active_dept = db.query_one(
                """
                SELECT dept_id
                FROM sys_dept
                WHERE dept_name = %s AND parent_id = %s AND del_flag = '0'
                LIMIT 1
                """,
                (dept_name, 101),
            )
            assert active_dept is None, active_dept
    finally:
        with allure_step("清理部门岗位用户关联流程测试数据"):
            cleanup_flow_data(
                db,
                user_names=[user_name],
                post_codes=[post_code],
                dept_names=[dept_name],
            )


@allure.title("菜单权限流程")
def test_menu_permission_change_flow(
    menu_api,
    role_api,
    user_api,
    auth_api,
    auth_headers,
    redis_client,
    db,
    unique_context,
):
    set_case_metadata(
        {"id": "FLOW-MENU-PERMISSION-001", "title": "菜单权限流程"},
        feature=FLOW_FEATURE,
        story="新增菜单 -> 分配给角色 -> 普通用户登录 -> 验证菜单权限变化",
    )

    suffix = unique_context["unique"]
    menu_name = f"flow_permission_menu_{suffix}"
    menu_path = f"flow-permission-{suffix}"
    menu_perm = f"system:flow:permission:{suffix}"
    role_key = unique_context["unique_role_key"]
    role_name = f"flow_permission_role_{suffix}"
    user_name = f"api_auto_perm_{suffix}"
    menu_id = None
    role_id = None
    user_id = None

    cleanup_flow_data(
        db,
        user_names=[user_name],
        role_keys=[role_key],
        menu_names=[menu_name],
    )

    try:
        with allure_step("新增菜单"):
            assert_success(
                menu_api.create_menu(
                    payload={
                        "menuName": menu_name,
                        "parentId": 1,
                        "orderNum": 99,
                        "path": menu_path,
                        "component": "system/menu/index",
                        "query": "",
                        "routeName": "",
                        "isFrame": 1,
                        "isCache": 0,
                        "menuType": "C",
                        "visible": "0",
                        "status": "0",
                        "perms": menu_perm,
                        "icon": "tree-table",
                        "remark": "flow permission menu",
                    },
                    headers=auth_headers,
                ),
                "新增成功",
            )
            menu_row = assert_row_exists(
                find_menu_by_name(db, menu_name),
                f"menu was not created: {menu_name}",
            )
            menu_id = str(menu_row["menu_id"])

        with allure_step("新增未分配新菜单权限的角色"):
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
                        "remark": "flow menu permission role",
                    },
                    headers=auth_headers,
                ),
                "新增成功",
            )
            role_row = assert_row_exists(
                find_role_by_key(db, role_key),
                f"role was not created: {role_key}",
            )
            role_id = str(role_row["role_id"])

        with allure_step("新增绑定角色的普通用户"):
            assert_success(
                user_api.create_user(
                    payload={
                        "deptId": 105,
                        "userName": user_name,
                        "nickName": f"flow_permission_user_{suffix}",
                        "password": INITIAL_PASSWORD,
                        "email": f"{user_name}@example.com",
                        "phonenumber": unique_context["unique_phone"],
                        "sex": "2",
                        "status": "0",
                        "roleIds": [int(role_id)],
                        "postIds": [4],
                        "remark": "flow permission user",
                    },
                    headers=auth_headers,
                ),
                "新增成功",
            )
            user_row = assert_row_exists(
                find_user_by_name(db, user_name),
                f"user was not created: {user_name}",
            )
            user_id = str(user_row["user_id"])

        with allure_step("分配菜单前普通用户登录"):
            before_headers = login_as_user(auth_api, redis_client, user_name, INITIAL_PASSWORD)
            before_info = assert_success(auth_api.get_info(headers=before_headers))
            before_routers = assert_success(auth_api.get_routers(headers=before_headers))["data"]
            assert menu_perm not in before_info["permissions"], before_info
            assert not route_title_exists(before_routers, menu_name), before_routers

        with allure_step("分配菜单给角色"):
            assert_success(
                role_api.update_role(
                    payload={
                        "roleId": role_id,
                        "roleName": role_name,
                        "roleKey": role_key,
                        "roleSort": 99,
                        "status": "0",
                        "menuIds": [1, int(menu_id)],
                        "menuCheckStrictly": True,
                        "deptCheckStrictly": True,
                        "remark": "flow menu permission role updated",
                    },
                    headers=auth_headers,
                ),
                "更新成功",
            )
            relation = db.query_one(
                """
                SELECT role_id, menu_id
                FROM sys_role_menu
                WHERE role_id = %s AND menu_id = %s
                LIMIT 1
                """,
                (role_id, menu_id),
            )
            assert_row_exists(relation, "role-menu relation was not created")

        with allure_step("普通用户重新登录并验证菜单权限变化"):
            after_headers = login_as_user(auth_api, redis_client, user_name, INITIAL_PASSWORD)
            after_info = assert_success(auth_api.get_info(headers=after_headers))
            after_routers = assert_success(auth_api.get_routers(headers=after_headers))["data"]
            assert menu_perm in after_info["permissions"], after_info
            assert route_title_exists(after_routers, menu_name), after_routers

        with allure_step("删除用户、角色和菜单"):
            assert_success(user_api.delete_user(user_id, headers=auth_headers), "删除成功")
            assert_success(role_api.delete_role(role_id, headers=auth_headers), "删除成功")
            assert_success(menu_api.delete_menu(menu_id, headers=auth_headers), "删除成功")
    finally:
        with allure_step("清理菜单权限流程测试数据"):
            cleanup_flow_data(
                db,
                user_names=[user_name],
                role_keys=[role_key],
                menu_names=[menu_name],
            )
