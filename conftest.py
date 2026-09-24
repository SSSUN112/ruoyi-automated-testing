import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

from api_tests.apis.auth_api import AuthApi
from api_tests.apis.dept_api import DeptApi
from api_tests.apis.menu_api import MenuApi
from api_tests.apis.post_api import PostApi
from api_tests.apis.role_api import RoleApi
from api_tests.apis.user_api import UserApi
from common.assert_util import assert_api_response
from common.db_util import MySQLClient
from common.log_util import LOG_FILE, get_logger, setup_logging
from common.captcha_util import get_captcha_payload
from common.redis_util import RedisClient
from common.request_util import RequestClient
from common.system_test_util import (
    cleanup_auto_depts_by_names,
    cleanup_auto_menus_by_names,
    cleanup_auto_posts_by_codes,
    cleanup_auto_roles_by_keys,
    find_dept_by_name,
    find_menu_by_name,
    find_post_by_code,
    find_role_by_key,
)
from common.user_test_util import cleanup_users_by_names, find_user_by_name
from config import (
    BASE_URL,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    ENV_FILE,
    BASE_DIR,
    PASSWORD,
    REQUEST_TIMEOUT,
    REDIS_DB,
    REDIS_HOST,
    REDIS_PASSWORD,
    REDIS_PORT,
    TEST_ENV,
    USERNAME,
)


logger = get_logger(__name__)


def _is_api_test_item(item) -> bool:
    return "api_tests/tests" in Path(str(item.fspath)).as_posix()


def _is_smoke_case(case: dict) -> bool:
    return bool(case.get("smoke", False))


#pytest 先把所有测试用例收集起来，然后这个函数逐条检查：
#如果这条用例的数据里有 smoke: true，就给它加上 @pytest.mark.smoke。

@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    for item in items:
        if not _is_api_test_item(item) or item.get_closest_marker("smoke"):
            continue

        callspec = getattr(item, "callspec", None)
        case = callspec.params.get("case") if callspec else None
        if isinstance(case, dict) and _is_smoke_case(case):
            item.add_marker(pytest.mark.smoke)


def pytest_configure(config):
    setup_logging()
    logger.info("Test environment: %s, env file: %s", TEST_ENV, ENV_FILE)
    logger.info("测试日志文件：%s", LOG_FILE)


def pytest_runtest_logstart(nodeid, location):
    logger.info("开始执行用例：%s", nodeid)


def pytest_runtest_logreport(report):
    if report.when != "call":
        return

    if report.passed:
        logger.info("用例执行通过：%s", report.nodeid)
    elif report.skipped:
        logger.warning("用例执行跳过：%s", report.nodeid)
    else:
        logger.error("用例执行失败：%s", report.nodeid)


def pytest_sessionfinish(session, exitstatus):
    # CI由Jenkins发布Allure，避免读取本地旧报告。
    if os.getenv("CI") == "true":
        return
    if session.config.option.collectonly:
        return

    allure_command = shutil.which("allure")
    if not allure_command:
        logger.warning(
            "未找到 Allure CLI，已保留 Allure 原始结果；"
            "请安装 Allure 命令行后生成 HTML 报告。"
        )
        return

    results_dir = BASE_DIR / "reports" / "allure-results"
    html_report_dir = BASE_DIR / "reports" / "html-report"

    if not results_dir.exists():
        logger.warning("未找到 Allure 原始结果目录：%s", results_dir)
        return

    command = [
        allure_command,
        "generate",
        str(results_dir),
        "-o",
        str(html_report_dir),
        "--clean",
    ]
    logger.info("开始生成 Allure HTML 报告：%s", " ".join(command))

    completed = subprocess.run(
        command,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if completed.returncode == 0:
        logger.info("Allure HTML 报告已生成：%s", html_report_dir)
        return

    logger.error(
        "Allure HTML 报告生成失败，returncode=%s，stdout=%s，stderr=%s",
        completed.returncode,
        completed.stdout,
        completed.stderr,
    )


@pytest.fixture(scope="session")
def request_client() -> RequestClient:
    client = RequestClient(
        base_url=BASE_URL,
        timeout=REQUEST_TIMEOUT,
    )

    yield client

    client.close()


@pytest.fixture(scope="session")
def auth_api(request_client: RequestClient) -> AuthApi:
    return AuthApi(request_client)


@pytest.fixture(scope="session")
def user_api(request_client: RequestClient) -> UserApi:
    return UserApi(request_client)


@pytest.fixture(scope="session")
def menu_api(request_client: RequestClient) -> MenuApi:
    return MenuApi(request_client)


@pytest.fixture(scope="session")
def dept_api(request_client: RequestClient) -> DeptApi:
    return DeptApi(request_client)


@pytest.fixture(scope="session")
def post_api(request_client: RequestClient) -> PostApi:
    return PostApi(request_client)


@pytest.fixture(scope="session")
def role_api(request_client: RequestClient) -> RoleApi:
    return RoleApi(request_client)


@pytest.fixture(scope="session")
def db() -> MySQLClient:
    client = MySQLClient(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

    yield client

    client.close()


@pytest.fixture(scope="session")
def redis_client() -> RedisClient:
    client = RedisClient(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
    )

    yield client

    client.close()


@pytest.fixture(scope="session")
def login_token(auth_api: AuthApi, redis_client: RedisClient) -> str:
    _, captcha_payload = get_captcha_payload(auth_api, redis_client)
    response = auth_api.login(
        username=USERNAME,
        password=PASSWORD,
        **captcha_payload,
    )

    result = assert_api_response(
        response,
        {
            "http_status": 200,
            "code": 200,
            "required_fields": ["token"],
        },
    )

    return result["token"]


@pytest.fixture(scope="session")
def auth_headers(login_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {login_token}",
    }


@pytest.fixture()
def auth_headers_factory(auth_api: AuthApi, redis_client: RedisClient):
    def _factory() -> dict[str, str]:
        _, captcha_payload = get_captcha_payload(auth_api, redis_client)
        response = auth_api.login(
            username=USERNAME,
            password=PASSWORD,
            **captcha_payload,
        )
        result = assert_api_response(
            response,
            {
                "http_status": 200,
                "code": 200,
                "required_fields": ["token"],
            },
        )
        return {
            "Authorization": f"Bearer {result['token']}",
        }

    return _factory





@pytest.fixture()
def unique_context() -> dict[str, str]:
    #生成一个随机UUID(uuid.uuid4());将UUID转换为不带连字符的十六进制字符串(.hex); 只取前八个数([:8])
    suffix = uuid.uuid4().hex[:8]
    phone_suffix = str(int(suffix, 16) % 100000000).zfill(8)
    return {
        "unique": suffix,
        "unique_user": f"api_auto_{suffix}",
        "unique_nick": f"接口自动化{suffix}",
        "unique_email": f"api_auto_{suffix}@example.com",
        "unique_phone": f"139{phone_suffix}",
        "unique_phone_alt": f"138{phone_suffix}",
        "unique_menu_name": f"接口自动化菜单{suffix}",
        "unique_menu_path": f"api-auto-menu-{suffix}",
        "unique_menu_perms": f"system:api:auto:{suffix}",
        "unique_dept_name": f"接口自动化部门{suffix}",
        "unique_post_code": f"api_auto_post_{suffix}",
        "unique_role_key": f"api_auto_role_{suffix}",
        "unique_post_name": f"接口自动化岗位{suffix}",
    }


@pytest.fixture()
def managed_user(
    user_api: UserApi,
    auth_headers: dict[str, str],
    db: MySQLClient,
    unique_context: dict[str, str],
) -> dict:
    user_name = unique_context["unique_user"]
    cleanup_users_by_names(db, [user_name])

    payload = {
        "deptId": 105,
        "userName": user_name,
        "nickName": unique_context["unique_nick"],
        "password": "Api@Test123",
        "email": unique_context["unique_email"],
        "phonenumber": unique_context["unique_phone"],
        "sex": "2",
        "status": "0",
        "roleIds": [2],
        "postIds": [4],
        "remark": "接口自动化临时用户",
    }

    response = user_api.create_user(
        payload=payload,
        headers=auth_headers,
    )
    assert_api_response(
        response,
        {
            "http_status": 200,
            "code": 200,
            "success": True,
        },
    )

    user_row = find_user_by_name(db, user_name)
    assert user_row is not None, f"临时用户创建后未在数据库中找到：{user_name}"

    context = {
        **unique_context,
        "managed_user_id": str(user_row["user_id"]),
        "managed_user_name": user_name,
        "managed_nick": unique_context["unique_nick"],
        "managed_email": unique_context["unique_email"],
        "managed_phone": unique_context["unique_phone"],
    }

    yield context

    cleanup_users_by_names(db, [user_name])


@pytest.fixture()
def managed_menu(
    menu_api: MenuApi,
    auth_headers: dict[str, str],
    db: MySQLClient,
    unique_context: dict[str, str],
) -> dict:
    menu_name = unique_context["unique_menu_name"]
    cleanup_auto_menus_by_names(db, [menu_name])

    payload = {
        "menuName": menu_name,
        "parentId": 1,
        "orderNum": 99,
        "path": unique_context["unique_menu_path"],
        "component": "system/menu/index",
        "query": "",
        "routeName": "",
        "isFrame": 1,
        "isCache": 0,
        "menuType": "C",
        "visible": "0",
        "status": "0",
        "perms": unique_context["unique_menu_perms"],
        "icon": "tree-table",
        "remark": "接口自动化临时菜单",
    }

    response = menu_api.create_menu(
        payload=payload,
        headers=auth_headers,
    )
    assert_api_response(
        response,
        {
            "http_status": 200,
            "code": 200,
            "success": True,
        },
    )

    menu_row = find_menu_by_name(db, menu_name)
    assert menu_row is not None, f"临时菜单创建后未在数据库中找到：{menu_name}"

    context = {
        **unique_context,
        "managed_menu_id": str(menu_row["menu_id"]),
        "managed_menu_name": menu_name,
    }

    yield context

    cleanup_auto_menus_by_names(db, [menu_name])


@pytest.fixture()
def managed_dept(
    dept_api: DeptApi,
    auth_headers: dict[str, str],
    db: MySQLClient,
    unique_context: dict[str, str],
) -> dict:
    dept_name = unique_context["unique_dept_name"]
    cleanup_auto_depts_by_names(db, [dept_name])

    payload = {
        "parentId": 101,
        "deptName": dept_name,
        "orderNum": 99,
        "leader": "接口自动化",
        "phone": "13800138000",
        "email": "api_auto_dept@example.com",
        "status": "0",
    }

    response = dept_api.create_dept(
        payload=payload,
        headers=auth_headers,
    )
    assert_api_response(
        response,
        {
            "http_status": 200,
            "code": 200,
            "success": True,
        },
    )

    dept_row = find_dept_by_name(db, dept_name, parent_id=101)
    assert dept_row is not None, f"临时部门创建后未在数据库中找到：{dept_name}"

    context = {
        **unique_context,
        "managed_dept_id": str(dept_row["dept_id"]),
        "managed_dept_name": dept_name,
    }

    yield context

    cleanup_auto_depts_by_names(db, [dept_name])


@pytest.fixture()
def managed_post(
    post_api: PostApi,
    auth_headers: dict[str, str],
    db: MySQLClient,
    unique_context: dict[str, str],
) -> dict:
    post_code = unique_context["unique_post_code"]
    cleanup_auto_posts_by_codes(db, [post_code])

    payload = {
        "postCode": post_code,
        "postName": unique_context["unique_post_name"],
        "postSort": 99,
        "status": "0",
        "remark": "接口自动化临时岗位",
    }

    response = post_api.create_post(
        payload=payload,
        headers=auth_headers,
    )
    assert_api_response(
        response,
        {
            "http_status": 200,
            "code": 200,
            "success": True,
        },
    )

    post_row = find_post_by_code(db, post_code)
    assert post_row is not None, f"临时岗位创建后未在数据库中找到：{post_code}"

    context = {
        **unique_context,
        "managed_post_id": str(post_row["post_id"]),
        "managed_post_code": post_code,
        "managed_post_name": unique_context["unique_post_name"],
    }

    yield context

    cleanup_auto_posts_by_codes(db, [post_code])


@pytest.fixture()
def managed_role(
    role_api: RoleApi,
    auth_headers: dict[str, str],
    db: MySQLClient,
    unique_context: dict[str, str],
) -> dict:
    role_key = unique_context["unique_role_key"]
    role_name = f"auto_role_{unique_context['unique']}"
    cleanup_auto_roles_by_keys(db, [role_key])

    payload = {
        "roleName": role_name,
        "roleKey": role_key,
        "roleSort": 99,
        "status": "0",
        "menuIds": [1],
        "menuCheckStrictly": True,
        "deptCheckStrictly": True,
        "remark": "api automation managed role",
    }

    response = role_api.create_role(
        payload=payload,
        headers=auth_headers,
    )
    assert_api_response(
        response,
        {
            "http_status": 200,
            "code": 200,
            "success": True,
        },
    )

    role_row = find_role_by_key(db, role_key)
    assert role_row is not None, f"managed role not found after create: {role_key}"

    context = {
        **unique_context,
        "managed_role_id": str(role_row["role_id"]),
        "managed_role_key": role_key,
        "managed_role_name": role_name,
    }

    yield context

    cleanup_auto_roles_by_keys(db, [role_key])
