from playwright.sync_api import Download, Page, expect

from ui_tests.pages.base_page import BasePage


class UserManagePage(BasePage):
    path = "/system/user"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.query_form = page.locator(".el-form").first
        self.toolbar = page.locator(".mb8").first
        self.add_button = self.toolbar.get_by_role("button", name="新增")
        self.delete_button = self.toolbar.get_by_role("button", name="删除")
        self.export_button = self.toolbar.get_by_role("button", name="导出")
        self.search_button = self.query_form.get_by_role("button", name="搜索")
        self.user_name_query_input = self.query_form.get_by_placeholder("请输入用户名称")
        self.table_rows = page.locator(".el-table__body-wrapper tbody tr")

    def open(self) -> None:
        self.goto(self.path)
        expect(self.add_button).to_be_visible()
        expect(self.user_name_query_input).to_be_visible()

    def add_dialog(self):
        return self.page.locator(".el-dialog", has_text="添加用户")

    def edit_dialog(self):
        return self.page.locator(".el-dialog", has_text="修改用户")

    def message_box(self):
        return self.page.locator(".el-message-box")

    def row_by_user_name(self, user_name: str):
        return self.table_rows.filter(has_text=user_name)

    def row_action_buttons(self, user_name: str):
        return self.row_by_user_name(user_name).locator("button")

    def success_message(self, text: str):
        return self.page.locator(".el-message", has_text=text).last

    def error_message(self, text: str):
        return self.page.locator(".el-message", has_text=text).last

    def form_error(self, text: str):
        return self.page.locator(".el-form-item__error", has_text=text).last

    def open_add_dialog(self):
        with self.page.expect_response(
            lambda response: "/system/user/" in response.url
            and "/system/user/list" not in response.url
            and response.request.method == "GET"
        ):
            self.add_button.click()
        dialog = self.add_dialog()
        expect(dialog).to_be_visible()
        return dialog

    def fill_add_user_form(self, user: dict) -> None:
        dialog = self.add_dialog()
        expect(dialog).to_be_visible()

        if "nickName" in user:
            dialog.get_by_placeholder("请输入用户昵称").fill(user["nickName"])
        if "userName" in user:
            dialog.get_by_placeholder("请输入用户名称").fill(user["userName"])
        if "password" in user:
            dialog.get_by_placeholder("请输入用户密码").fill(user["password"])
        if "email" in user:
            dialog.get_by_placeholder("请输入邮箱").fill(user["email"])
        if "phonenumber" in user:
            dialog.get_by_placeholder("请输入手机号码").fill(user["phonenumber"])
        if "remark" in user:
            dialog.get_by_placeholder("请输入内容").fill(user["remark"])
        for role_name in user.get("roleNames", []):
            self.select_role(dialog, role_name)

    def select_role(self, dialog, role_name: str) -> None:
        role_item = dialog.locator(".el-form-item", has_text="角色").last
        role_item.locator(".el-select").click()
        role_option = self.page.locator(".el-select-dropdown:visible").get_by_text(
            role_name,
            exact=True,
        )
        expect(role_option).to_be_visible()
        role_option.click()
        self.page.keyboard.press("Escape")

    def submit_add_form(self) -> None:
        self.add_dialog().get_by_role("button", name="确 定").click()

    def create_user(self, user: dict) -> None:
        dialog = self.open_add_dialog()
        self.fill_add_user_form(user)

        with self.page.expect_response(
            lambda response: "/system/user" in response.url
            and response.request.method == "POST"
        ):
            self.submit_add_form()

        expect(self.success_message("新增成功")).to_be_visible()
        expect(dialog).to_be_hidden()

    def create_user_expect_error(self, user: dict, error_text: str) -> None:
        dialog = self.open_add_dialog()
        self.fill_add_user_form(user)

        with self.page.expect_response(
            lambda response: "/system/user" in response.url
            and response.request.method == "POST"
        ):
            self.submit_add_form()

        expect(self.error_message(error_text)).to_be_visible()
        expect(dialog).to_be_visible()

    def submit_empty_add_form(self) -> None:
        dialog = self.open_add_dialog()
        dialog.get_by_placeholder("请输入用户密码").fill("")
        self.submit_add_form()
        expect(dialog).to_be_visible()

    def should_show_form_errors(self, error_texts: list[str]) -> None:
        for error_text in error_texts:
            expect(self.form_error(error_text)).to_be_visible()

    def search_user(self, user_name: str) -> None:
        self.user_name_query_input.fill(user_name)
        with self.page.expect_response(
            lambda response: "/system/user/list" in response.url
            and response.request.method == "GET"
        ):
            self.search_button.click()

    def should_contain_user(self, user_name: str) -> None:
        expect(self.row_by_user_name(user_name)).to_have_count(1)

    def should_contain_user_text(self, user_name: str, text: str) -> None:
        expect(self.row_by_user_name(user_name).filter(has_text=text)).to_have_count(1)

    def should_not_contain_user(self, user_name: str) -> None:
        expect(self.row_by_user_name(user_name)).to_have_count(0)

    def should_show_empty_table(self) -> None:
        expect(self.page.locator(".el-table__empty-text")).to_be_visible()

    def update_user(self, user_name: str, updated_user: dict) -> None:
        row = self.row_by_user_name(user_name)
        expect(row).to_have_count(1)

        with self.page.expect_response(
            lambda response: "/system/user/" in response.url
            and "/system/user/list" not in response.url
            and response.request.method == "GET"
        ):
            self.row_action_buttons(user_name).nth(0).click()

        dialog = self.edit_dialog()
        expect(dialog).to_be_visible()

        dialog.get_by_placeholder("请输入用户昵称").fill(updated_user["nickName"])
        dialog.get_by_placeholder("请输入邮箱").fill(updated_user["email"])
        dialog.get_by_placeholder("请输入手机号码").fill(updated_user["phonenumber"])
        dialog.get_by_placeholder("请输入内容").fill(updated_user["remark"])

        with self.page.expect_response(
            lambda response: "/system/user" in response.url
            and response.request.method == "PUT"
        ):
            dialog.get_by_role("button", name="确 定").click()

        expect(self.success_message("修改成功")).to_be_visible()
        expect(dialog).to_be_hidden()

    def reset_password(self, user_name: str, new_password: str) -> None:
        row = self.row_by_user_name(user_name)
        expect(row).to_have_count(1)

        self.row_action_buttons(user_name).nth(2).click()
        box = self.message_box()
        expect(box).to_be_visible()

        box.locator("input").fill(new_password)
        with self.page.expect_response(
            lambda response: "/system/user/resetPwd" in response.url
            and response.request.method == "PUT"
        ):
            box.get_by_role("button", name="确定").click()

        expect(self.success_message("修改成功")).to_be_visible()

    def disable_user(self, user_name: str) -> None:
        row = self.row_by_user_name(user_name)
        expect(row).to_have_count(1)

        row.locator(".el-switch").click()
        with self.page.expect_response(
            lambda response: "/system/user/changeStatus" in response.url
            and response.request.method == "PUT"
        ):
            self.message_box().get_by_role("button", name="确定").click()

        expect(self.success_message("停用成功")).to_be_visible()

    def delete_user(self, user_name: str) -> None:
        row = self.row_by_user_name(user_name)
        expect(row).to_have_count(1)

        row.locator(".el-checkbox").click()
        expect(self.delete_button).to_be_enabled()
        self.delete_button.click()

        with self.page.expect_response(
            lambda response: "/system/user/" in response.url
            and response.request.method == "DELETE"
        ):
            self.page.get_by_role("button", name="确定").click()

        expect(self.success_message("删除成功")).to_be_visible()

    def export_users(self) -> Download:
        expect(self.export_button).to_be_visible()
        with self.page.expect_download() as download_info:
            self.export_button.click()
        return download_info.value
