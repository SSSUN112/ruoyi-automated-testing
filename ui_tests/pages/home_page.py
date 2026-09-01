import re

from playwright.sync_api import Page, expect

from ui_tests.pages.base_page import BasePage


class HomePage(BasePage):
    path = "/"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.navbar = page.locator(".navbar")
        self.sidebar = page.locator(".sidebar-container")
        self.main_area = page.locator(".app-main")

    def open(self) -> None:
        self.goto(self.path)

    def should_be_logged_in(self) -> None:
        expect(self.page).not_to_have_url(re.compile(r".*/login.*"))
        expect(self.navbar).to_be_visible()
        expect(self.sidebar).to_be_visible()
        expect(self.main_area).to_be_visible()

    def should_show_sidebar_menu(self, menu_name: str) -> None:
        expect(self.sidebar.get_by_text(menu_name, exact=True)).to_be_visible()

    def should_not_show_sidebar_menu(self, menu_name: str) -> None:
        expect(self.sidebar.get_by_text(menu_name, exact=True)).to_have_count(0)
