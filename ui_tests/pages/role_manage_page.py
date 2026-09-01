from playwright.sync_api import Page, expect

from ui_tests.pages.base_page import BasePage


class RoleManagePage(BasePage):
    path = "/system/role"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.query_form = page.locator(".el-form").first
        self.toolbar = page.locator(".mb8").first
        self.add_button = self.toolbar.get_by_role("button", name="新增")
        self.delete_button = self.toolbar.get_by_role("button", name="删除")
        self.search_button = self.query_form.get_by_role("button", name="搜索")
        self.role_name_query_input = self.query_form.get_by_placeholder("请输入角色名称")
        self.role_key_query_input = self.query_form.get_by_placeholder("请输入权限字符")
        self.table_rows = page.locator(".el-table__body-wrapper tbody tr")

    def open(self) -> None:
        self.goto(self.path)
        expect(self.add_button).to_be_visible()
        expect(self.role_name_query_input).to_be_visible()

    def add_dialog(self):
        return self.page.locator(".el-dialog", has_text="添加角色")

    def edit_dialog(self):
        return self.page.locator(".el-dialog", has_text="修改角色")

    def message_box(self):
        return self.page.locator(".el-message-box")

    def row_by_role_name(self, role_name: str):
        return self.table_rows.filter(has_text=role_name)

    def row_action_buttons(self, role_name: str):
        return self.row_by_role_name(role_name).locator("button")

    def success_message(self, text: str):
        return self.page.locator(".el-message", has_text=text).last

    def error_message(self, text: str):
        return self.page.locator(".el-message", has_text=text).last

    def form_error(self, text: str):
        return self.page.locator(".el-form-item__error", has_text=text).last

    def open_add_dialog(self):
        with self.page.expect_response(
            lambda response: "/system/menu/treeselect" in response.url
            and response.request.method == "GET"
        ):
            self.add_button.click()
        dialog = self.add_dialog()
        expect(dialog).to_be_visible()
        return dialog

    def fill_role_form(self, dialog, role: dict) -> None:
        if "roleName" in role:
            dialog.get_by_placeholder("请输入角色名称").fill(role["roleName"])
        if "roleKey" in role:
            dialog.get_by_placeholder("请输入权限字符").fill(role["roleKey"])
        if "roleSort" in role:
            dialog.get_by_role("spinbutton").fill(str(role["roleSort"]))
        if "remark" in role:
            dialog.get_by_placeholder("请输入内容").fill(role["remark"])

    def check_menu_permission(self, dialog, menu_name: str) -> None:
        menu_node = dialog.locator(".el-tree-node", has_text=menu_name).last
        expect(menu_node).to_be_visible()
        menu_node.locator(".el-checkbox").first.click()

    def submit_add_form(self) -> None:
        self.add_dialog().get_by_role("button", name="确 定").click()

    def create_role(self, role: dict) -> None:
        dialog = self.open_add_dialog()
        self.fill_role_form(dialog, role)
        for menu_name in role.get("menuNames", []):
            self.check_menu_permission(dialog, menu_name)

        with self.page.expect_response(
            lambda response: "/system/role" in response.url
            and response.request.method == "POST"
        ):
            self.submit_add_form()

        expect(self.success_message("新增成功")).to_be_visible()
        expect(dialog).to_be_hidden()

    def assign_menu_to_role(self, role_name: str, menu_name: str) -> None:
        row = self.row_by_role_name(role_name)
        expect(row).to_have_count(1)

        with self.page.expect_response(
            lambda response: "/system/role/" in response.url
            and response.request.method == "GET"
        ):
            self.row_action_buttons(role_name).nth(0).click()

        dialog = self.edit_dialog()
        expect(dialog).to_be_visible()
        self.check_menu_permission(dialog, menu_name)

        with self.page.expect_response(
            lambda response: "/system/role" in response.url
            and response.request.method == "PUT"
        ):
            dialog.get_by_role("button", name="确 定").click()

        expect(self.success_message("修改成功")).to_be_visible()
        expect(dialog).to_be_hidden()

    def create_role_expect_error(self, role: dict, error_text: str) -> None:
        dialog = self.open_add_dialog()
        self.fill_role_form(dialog, role)

        with self.page.expect_response(
            lambda response: "/system/role" in response.url
            and response.request.method == "POST"
        ):
            self.submit_add_form()

        expect(self.error_message(error_text)).to_be_visible()
        expect(dialog).to_be_visible()

    def submit_empty_add_form(self) -> None:
        dialog = self.open_add_dialog()
        dialog.get_by_placeholder("请输入角色名称").fill("")
        dialog.get_by_placeholder("请输入权限字符").fill("")
        self.submit_add_form()
        expect(dialog).to_be_visible()

    def should_show_form_errors(self, error_texts: list[str]) -> None:
        for error_text in error_texts:
            expect(self.form_error(error_text)).to_be_visible()

    def search_role(self, role_name: str | None = None, role_key: str | None = None) -> None:
        if role_name is not None:
            self.role_name_query_input.fill(role_name)
        if role_key is not None:
            self.role_key_query_input.fill(role_key)
        with self.page.expect_response(
            lambda response: "/system/role/list" in response.url
            and response.request.method == "GET"
        ):
            self.search_button.click()
        self.page.wait_for_load_state("networkidle")

    def should_contain_role(self, role_name: str) -> None:
        expect(self.row_by_role_name(role_name)).to_have_count(1)

    def should_contain_role_text(self, role_name: str, text: str) -> None:
        expect(self.row_by_role_name(role_name).filter(has_text=text)).to_have_count(1)

    def should_not_contain_role(self, role_name: str) -> None:
        expect(self.row_by_role_name(role_name)).to_have_count(0)

    def should_show_empty_table(self) -> None:
        expect(self.page.locator(".el-table__empty-text")).to_be_visible()

    def update_role(self, role_name: str, updated_role: dict) -> None:
        row = self.row_by_role_name(role_name)
        expect(row).to_have_count(1)

        with self.page.expect_response(
            lambda response: "/system/role/" in response.url
            and response.request.method == "GET"
        ):
            self.row_action_buttons(role_name).nth(0).click()

        dialog = self.edit_dialog()
        expect(dialog).to_be_visible()
        self.fill_role_form(dialog, updated_role)

        with self.page.expect_response(
            lambda response: "/system/role" in response.url
            and response.request.method == "PUT"
        ):
            dialog.get_by_role("button", name="确 定").click()

        expect(self.success_message("修改成功")).to_be_visible()
        expect(dialog).to_be_hidden()
        self.page.wait_for_load_state("networkidle")

    def disable_role(self, role_name: str) -> None:
        row = self.row_by_role_name(role_name)
        expect(row).to_have_count(1)

        row.locator(".el-switch").click()
        with self.page.expect_response(
            lambda response: "/system/role/changeStatus" in response.url
            and response.request.method == "PUT"
        ):
            self.message_box().get_by_role("button", name="确定").click()

        expect(self.success_message("停用成功")).to_be_visible()

    def delete_role(self, role_name: str) -> None:
        row = self.row_by_role_name(role_name)
        expect(row).to_have_count(1)

        row.locator(".el-checkbox").click()
        expect(self.delete_button).to_be_enabled()
        self.delete_button.click()

        with self.page.expect_response(
            lambda response: "/system/role/" in response.url
            and response.request.method == "DELETE"
        ):
            self.page.get_by_role("button", name="确定").click()

        expect(self.success_message("删除成功")).to_be_visible()
