import re
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from playwright.sync_api import Browser, BrowserContext, Error, Page, sync_playwright

from common.assert_util import assert_api_response
from common.allure_util import attach_text
from common.captcha_util import get_captcha_payload
from config import (
    BASE_DIR,
    FRONTEND_URL,
    PASSWORD,
    UI_BROWSER,
    UI_HEADLESS,
    UI_SLOW_MO,
    UI_TIMEOUT,
    UI_VIEWPORT_HEIGHT,
    UI_VIEWPORT_WIDTH,
    USERNAME,
)
from ui_tests.pages.login_page import LoginPage

try:
    import allure
except ImportError:
    allure = None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """保存每个用例阶段的执行结果，供 teardown 阶段判断用例是否失败。"""
    outcome = yield       #先让 pytest 自己正常生成报告
    report = outcome.get_result()   #拿到 pytest 刚生成的阶段报告对象
    setattr(item, f"rep_{report.when}", report)    #把这个报告对象保存到当前用例 item 上


@pytest.fixture(scope="session")
def ui_base_url() -> str:
    """检查前端服务是否可访问，并把 UI 测试使用的前端地址提供给用例。"""
    try:
        with urlopen(FRONTEND_URL, timeout=5):  # 尝试访问前端
            pass
    except (OSError, URLError):
        pytest.skip(f"UI frontend is not available: {FRONTEND_URL}")  # 不可用则跳过测试
    return FRONTEND_URL


@pytest.fixture(scope="session")
def playwright_instance():
    """启动 Playwright 主对象，整个测试会话共用一次。"""
    with sync_playwright() as playwright:  # 启动 Playwright
        yield playwright  # 提供给测试使用
    # 测试结束后自动关闭


@pytest.fixture(scope="session")
def browser(ui_base_url: str, playwright_instance) -> Browser:
    """根据配置启动浏览器实例，所有 UI 用例共用这个浏览器。"""
    browser_launcher = getattr(playwright_instance, UI_BROWSER)  # 获取浏览器类型（chromium/firefox/webkit）
    browser = browser_launcher.launch(
        headless=UI_HEADLESS,  # 是否无头模式
        slow_mo=UI_SLOW_MO,    # 操作间隔时间
    )
    yield browser
    browser.close()  # 测试结束后关闭浏览器


@pytest.fixture()
def browser_context(browser: Browser, request) -> BrowserContext:
    """为每条 UI 用例创建独立浏览器上下文，并开启失败诊断采集。"""
    context = browser.new_context(
        viewport={"width": UI_VIEWPORT_WIDTH, "height": UI_VIEWPORT_HEIGHT},  # 设置窗口大小
        ignore_https_errors=True,  # 忽略 HTTPS 错误
        accept_downloads=True,  # 允许 UI 导出用例捕获下载文件
    )
    context.set_default_timeout(UI_TIMEOUT)  # 设置默认超时
    start_ui_diagnostics(context, request)     #对一条测试用例进行监听
    yield context
    stop_ui_diagnostics(context, request)     #失败是，将失败信息写入allure
    context.close()  # 关闭上下文


@pytest.fixture()
def page(browser_context: BrowserContext, request) -> Page:
    """创建普通页面对象，适合不需要提前登录的 UI 用例使用。"""
    page = browser_context.new_page()  # 创建新页面
    watch_page_events(page, request)    #对页面进行监听
    yield page
    attach_failure_screenshot(page, request)  # 失败时截图
    page.close()  # 关闭页面


@pytest.fixture()
def ui_auth_token(auth_api, redis_client):
    """通过接口登录获取 token，供 UI 用例注入登录态使用。"""
    # 1. 获取验证码
    _, captcha_payload = get_captcha_payload(auth_api, redis_client)
    # 2. 登录获取 token
    response = auth_api.login(
        username=USERNAME,
        password=PASSWORD,
        **captcha_payload,
    )
    # 3. 验证响应并提取 token
    result = assert_api_response(
        response,
        {
            "http_status": 200,
            "code": 200,
            "required_fields": ["token"],
        },
    )
    token = result["token"]
    yield token
    # 4. 登出清理
    auth_api.logout(headers={"Authorization": f"Bearer {token}"})


@pytest.fixture()
def authenticated_page(browser_context, request, ui_auth_token, ui_base_url) -> Page:
    """创建已登录页面，把 token 写入 Cookie 后直接进入后台页面。"""
    # 添加 token 到 cookie
    browser_context.add_cookies([
        {
            "name": "Admin-Token",
            "value": ui_auth_token,
            "url": ui_base_url,
        }
    ])
    page = browser_context.new_page()
    watch_page_events(page, request)    #开启监听
    yield page
    attach_failure_screenshot(page, request)
    page.close()


def start_ui_diagnostics(context: BrowserContext, request) -> None:
    """启动 UI 失败诊断：监听新页面、收集浏览器日志、开启 Playwright trace。"""
    request.node._ui_browser_events = []   #request.node 表示 当前这条测试用例对象
    request.node._ui_watched_pages = set()
    context.on("page", lambda new_page: watch_page_events(new_page, request))
    context.tracing.start(
        screenshots=True,
        snapshots=True,
        sources=True,
    )


def stop_ui_diagnostics(context: BrowserContext, request) -> None:
    """结束 UI 失败诊断；失败时把 trace 和 浏览器日志写入 Allure 报告。"""
    report = getattr(request.node, "rep_call", None)     #item.rep_call.failed == True 意思就是测试失败了
    test_failed = bool(report and report.failed)

    try:
        if test_failed:
            trace_dir = BASE_DIR / "reports" / "ui-traces"
            trace_dir.mkdir(parents=True, exist_ok=True)
            trace_path = trace_dir / f"{safe_artifact_name(request.node.nodeid)}.zip"
            context.tracing.stop(path=str(trace_path))
            attach_ui_trace(trace_path)
            attach_browser_events(request)
        else:
            context.tracing.stop()
    except Error as error:
        attach_text("UI 诊断采集异常", f"采集 trace 或浏览器日志失败：{error}")


def watch_page_events(page: Page, request) -> None:
    """给页面绑定 console/pageerror 监听，捕获前端控制台日志和 JS 异常。"""
    watched_pages = getattr(request.node, "_ui_watched_pages", set())
    if id(page) in watched_pages:
        return

    watched_pages.add(id(page))
    request.node._ui_watched_pages = watched_pages

    page.on("console",
            lambda message: watched_pages(
            request,
            f"console.{message.type}: {message.text}",
        ),
    )     #页面里只要出现浏览器 console 日志，就执行后面的函数
    page.on(
        "pageerror",
        lambda error: add_browser_event(request, f"pageerror: {error}"),
    )   #表示：页面出现未捕获的 JS 异常时触发。


def add_browser_event(request, message: str) -> None:
    """把浏览器事件暂存到当前 pytest 用例对象上，失败后统一写报告。"""
    events = getattr(request.node, "_ui_browser_events", [])
    events.append(message)
    request.node._ui_browser_events = events
    #等用例失败后，stop_ui_diagnostics 会取出来写进 Allure


def attach_browser_events(request) -> None:
    """把已捕获的 console/pageerror 日志作为文本附件写入 Allure。"""
    events = getattr(request.node, "_ui_browser_events", [])
    if not events:
        attach_text("浏览器 console/pageerror", "未捕获到浏览器 console/pageerror 日志")
        return

    attach_text("浏览器 console/pageerror", "\n".join(events[-200:]))


def attach_ui_trace(trace_path: Path) -> None:
    """把 Playwright trace 压缩包作为附件写入 Allure。"""
    if allure is None:
        return

    allure.attach.file(
        str(trace_path),
        name="failure trace",
        extension="zip",
    )


def attach_failure_screenshot(page: Page, request) -> None:
    """用例失败时保存当前页面截图，并把截图附件写入 Allure。"""
    report = getattr(request.node, "rep_call", None)  # 获取测试结果
    if report and report.failed:  # 如果测试失败
        # 保存截图
        screenshot_dir = BASE_DIR / "reports" / "ui-screenshots"
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = screenshot_dir / f"{safe_artifact_name(request.node.nodeid)}.png"
        try:
            page.screenshot(path=str(screenshot_path), full_page=True)
        except Error as error:
            attach_text("失败截图采集异常", f"采集失败截图失败：{error}")
            return
        # 如果有 allure，附加到报告
        if allure is not None:
            allure.attach.file(
                str(screenshot_path),
                name="failure screenshot",
                attachment_type=allure.attachment_type.PNG,
            )


def safe_artifact_name(nodeid: str) -> str:
    """把 pytest nodeid 转成安全文件名，避免路径特殊字符导致保存失败。"""
    return re.sub(r'[<>:"/\\|?*\[\]\s]+', "_", nodeid).strip("_")


@pytest.fixture()
def login_page(page: Page, ui_base_url: str) -> LoginPage:
    """创建登录页 Page Object，登录页相关用例直接使用这个对象。"""
    return LoginPage(page, ui_base_url)
