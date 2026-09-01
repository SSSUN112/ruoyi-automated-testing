from playwright.sync_api import Page, expect

from ui_tests.pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/login"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.form = page.locator(".login-form")
        self.username_input = page.locator("input").nth(0)
        self.password_input = page.locator("input[type='password']").first
        self.captcha_input = page.locator(".login-code").locator("xpath=../descendant::input").first
        self.login_button = page.locator(".login-form button").last
        self.captcha_image = page.locator(".login-code-img")

    def open(self) -> None:
        self.goto(self.path)

    def should_be_loaded(self) -> None:
        expect(self.form).to_be_visible()
        expect(self.username_input).to_be_visible()
        expect(self.password_input).to_be_visible()

    def should_show_captcha_if_enabled(self) -> None:
        if self.captcha_image.count() > 0:
            expect(self.captcha_image).to_be_visible()

    def login(self, username: str, password: str, captcha_code: str | None = None) -> None:
        self.username_input.fill(username)
        self.password_input.fill(password)
        if captcha_code is not None and self.captcha_input.count() > 0:  #返回 locator 匹配到的元素数量
            self.captcha_input.fill(captcha_code)
        self.login_button.click()
