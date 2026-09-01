from playwright.sync_api import Page, expect

from ui_tests.pages.base_page import BasePage


class MenuManagePage(BasePage):
    path = "/system/menu"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.query_form = page.locator(".el-form").first
        self.toolbar = page.locator(".mb8").first
        self.add_button = self.toolbar.get_by_role("button", name="新增")
        self.search_button = self.query_form.get_by_role("button", name="搜索")
        self.menu_name_query_input = self.query_form.get_by_placeholder("请输入菜单名称")
        self.table_rows = page.locator(".el-table__body-wrapper tbody tr")

    def open(self) -> None:
        self.goto(self.path)
        expect(self.add_button).to_be_visible()
        expect(self.menu_name_query_input).to_be_visible()

    def add_dialog(self):
        return self.page.locator(".el-dialog", has_text="添加菜单")

    def edit_dialog(self):
        return self.page.locator(".el-dialog", has_text="修改菜单")

    def message_box(self):
        return self.page.locator(".el-message-box")

    def row_by_menu_name(self, menu_name: str):
        return self.table_rows.filter(has_text=menu_name)

    def row_action_button(self, menu_name: str, button_name: str):
        return self.row_by_menu_name(menu_name).get_by_role("button", name=button_name)

    def success_message(self, text: str):
        return self.page.locator(".el-message", has_text=text).last

    def error_message(self, text: str):
        return self.page.locator(".el-message", has_text=text).last

    def form_error(self, text: str):
        return self.page.locator(".el-form-item__error", has_text=text).last

    def open_add_dialog(self):
        with self.page.expect_response(
            lambda response: "/system/menu/list" in response.url
            and response.request.method == "GET"
        ):
            self.add_button.click()
        dialog = self.add_dialog()
        expect(dialog).to_be_visible()
        return dialog

    def fill_menu_form(self, dialog, menu: dict) -> None:
        if menu.get("menuType") == "C":
            dialog.locator(".el-radio", has_text="菜单").click()
        if "menuName" in menu:
            dialog.get_by_placeholder("请输入菜单名称").fill(menu["menuName"])
        if "orderNum" in menu:
            dialog.get_by_role("spinbutton").fill(str(menu["orderNum"]))
        if "path" in menu:
            dialog.get_by_placeholder("请输入路由地址").fill(menu["path"])
        if "component" in menu:
            dialog.get_by_placeholder("请输入组件路径").fill(menu["component"])
        if "perms" in menu:
            dialog.get_by_placeholder("请输入权限标识").fill(menu["perms"])

    def submit_add_form(self) -> None:
        self.add_dialog().get_by_role("button", name="确 定").click()

    def create_menu(self, menu: dict) -> None:
        dialog = self.open_add_dialog()
        self.fill_menu_form(dialog, menu)

        with self.page.expect_response(
            lambda response: "/system/menu" in response.url
            and response.request.method == "POST"
        ):
            self.submit_add_form()

        expect(self.success_message("新增成功")).to_be_visible()
        expect(dialog).to_be_hidden()

    def create_menu_expect_error(self, menu: dict, error_text: str) -> None:
        dialog = self.open_add_dialog()
        self.fill_menu_form(dialog, menu)

        with self.page.expect_response(
            lambda response: "/system/menu" in response.url
            and response.request.method == "POST"
        ):
            self.submit_add_form()

        expect(self.error_message(error_text)).to_be_visible()
        expect(dialog).to_be_visible()

    def submit_empty_add_form(self) -> None:
        dialog = self.open_add_dialog()
        dialog.get_by_placeholder("请输入菜单名称").fill("")
        dialog.get_by_role("spinbutton").fill("")
        dialog.get_by_placeholder("请输入路由地址").fill("")
        self.submit_add_form()
        expect(dialog).to_be_visible()

    def should_show_form_errors(self, error_texts: list[str]) -> None:
        for error_text in error_texts:
            expect(self.form_error(error_text)).to_be_visible()

    def search_menu(self, menu_name: str) -> None:
        self.menu_name_query_input.fill(menu_name)
        with self.page.expect_response(
            lambda response: "/system/menu/list" in response.url
            and response.request.method == "GET"
        ):
            self.search_button.click()
        self.page.wait_for_load_state("networkidle")

    def should_contain_menu(self, menu_name: str) -> None:
        expect(self.row_by_menu_name(menu_name)).to_have_count(1)

    def should_contain_menu_text(self, menu_name: str, text: str) -> None:
        expect(self.row_by_menu_name(menu_name).filter(has_text=text)).to_have_count(1)

    def should_not_contain_menu(self, menu_name: str) -> None:
        expect(self.row_by_menu_name(menu_name)).to_have_count(0)

    def should_show_empty_table(self) -> None:
        expect(self.page.locator(".el-table__empty-text")).to_be_visible()

    def update_menu(self, menu_name: str, updated_menu: dict) -> None:
        row = self.row_by_menu_name(menu_name)
        expect(row).to_have_count(1)

        with self.page.expect_response(
            lambda response: "/system/menu/" in response.url
            and response.request.method == "GET"
        ):
            self.row_action_button(menu_name, "修改").click()

        dialog = self.edit_dialog()
        expect(dialog).to_be_visible()
        self.fill_menu_form(dialog, updated_menu)

        with self.page.expect_response(
            lambda response: "/system/menu" in response.url
            and response.request.method == "PUT"
        ):
            dialog.get_by_role("button", name="确 定").click()

        expect(self.success_message("修改成功")).to_be_visible()
        expect(dialog).to_be_hidden()
        self.page.wait_for_load_state("networkidle")

    def delete_menu(self, menu_name: str) -> None:
        row = self.row_by_menu_name(menu_name)
        expect(row).to_have_count(1)
        self.row_action_button(menu_name, "删除").click()

        with self.page.expect_response(
            lambda response: "/system/menu/" in response.url
            and response.request.method == "DELETE"
        ):
            self.message_box().get_by_role("button", name="确定").click()

        expect(self.success_message("删除成功")).to_be_visible()
