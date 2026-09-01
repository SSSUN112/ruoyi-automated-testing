from pathlib import Path

from playwright.sync_api import Page, expect

from ui_tests.pages.base_page import BasePage


class ProfilePage(BasePage):
    path = "/user/profile"

    def __init__(self, page: Page, base_url: str):
        super().__init__(page, base_url)
        self.profile_card = page.locator(".box-card", has_text="个人信息")
        self.avatar_head = page.locator(".user-info-head")

    def open(self) -> None:
        with self.page.expect_response(
            lambda response: "/system/user/profile" in response.url
            and response.request.method == "GET"
        ):
            self.goto(self.path)
        expect(self.profile_card).to_be_visible()
        expect(self.avatar_head).to_be_visible()

    def avatar_dialog(self):
        return self.page.locator(".el-dialog:visible", has_text="修改头像")

    def success_message(self, text: str):
        return self.page.locator(".el-message", has_text=text).last

    def upload_avatar(self, file_path: str | Path) -> None:
        self.avatar_head.click()

        dialog = self.avatar_dialog()
        expect(dialog).to_be_visible()

        dialog.locator("input[type=file]").set_input_files(str(file_path))
        expect(dialog.locator(".cropper-box")).to_be_visible()
        self.page.wait_for_timeout(500)
        submit_button = dialog.locator("button.el-button--primary", has_text="提 交")
        expect(submit_button).to_be_enabled()

        with self.page.expect_response(
            lambda response: "/system/user/profile/avatar" in response.url
            and response.request.method == "POST"
        ):
            submit_button.click(force=True)

        expect(self.success_message("修改成功")).to_be_visible()
        expect(dialog).to_be_hidden()
