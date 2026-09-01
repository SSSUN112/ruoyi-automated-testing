from pathlib import Path

import pytest

from common.allure_util import allure_step, attach_text, set_case_metadata
from common.yaml_util import load_yaml
from config import BASE_DIR, UI_DATA_DIR
from ui_tests.pages.profile_page import ProfilePage


UI_PARENT_SUITE = "RuoYi UI 自动化测试"
PROFILE_FEATURE = "个人中心"
USER_CASES = load_yaml(UI_DATA_DIR / "user.yaml")


@pytest.mark.ui
def test_user_profile_avatar_upload(
    authenticated_page,
    ui_base_url,
    db,
):
    case = USER_CASES["user_profile_avatar_upload"]
    profile_page = ProfilePage(authenticated_page, ui_base_url)
    avatar_file = BASE_DIR / case["file"]["path"]
    browser_errors: list[str] = []

    set_case_metadata(
        case,
        feature=PROFILE_FEATURE,
        story="头像上传",
        parent_suite=UI_PARENT_SUITE,
    )

    def collect_console_error(message) -> None:
        text = message.text
        if message.type in {"error", "warning"} or "err" in text.lower() or "error" in text.lower():
            browser_errors.append(f"console.{message.type}: {text}")

    authenticated_page.on("console", collect_console_error)
    authenticated_page.on("pageerror", lambda error: browser_errors.append(f"pageerror: {error}"))

    old_avatar = db.query_one(
        "SELECT avatar FROM sys_user WHERE user_name = %s LIMIT 1",
        ("admin",),
    )
    old_avatar_value = old_avatar["avatar"] if old_avatar else ""

    try:
        with allure_step("打开个人中心页面"):
            profile_page.open()

        with allure_step("上传用户头像"):
            try:
                profile_page.upload_avatar(avatar_file)
            except Exception as error:
                browser_error_text = "\n".join(browser_errors) or "未捕获到浏览器 console/pageerror 错误"
                attach_text("头像上传浏览器错误", browser_error_text)
                raise AssertionError(
                    "头像上传失败：点击提交后未完成头像上传请求。\n"
                    f"浏览器错误：\n{browser_error_text}"
                ) from error
    finally:
        with allure_step("恢复头像测试数据"):
            db.execute(
                "UPDATE sys_user SET avatar = %s WHERE user_name = %s",
                (old_avatar_value, "admin"),
            )
