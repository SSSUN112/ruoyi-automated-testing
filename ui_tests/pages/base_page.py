from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url.rstrip("/")

    def goto(self, path: str = "/") -> None:
        self.page.goto(f"{self.base_url}/{path.lstrip('/')}", wait_until="networkidle")

#断言当前页面的 URL 中包含指定的文本
    def expect_url_contains(self, text: str) -> None:
        assert text in self.page.url, self.page.url
