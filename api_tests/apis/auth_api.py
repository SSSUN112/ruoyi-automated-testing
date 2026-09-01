from common.request_util import RequestClient


class AuthApi:
    def __init__(self, client: RequestClient):
        self.client = client

    def get_captcha_image(self):
        return self.client.get("/captchaImage")

    def login(
        self,
        username: str,
        password: str,
        code: str | None = None,
        uuid: str | None = None,
    ):
        data = {
            "username": username,
            "password": password,
        }

        if code is not None:
            data["code"] = code

        if uuid is not None:
            data["uuid"] = uuid

        return self.client.post(
            "/login",
            data=data,
        )

    def register(self, payload: dict):
        return self.client.post(
            "/register",
            json=payload,
        )

    def get_info(self, headers: dict | None = None):
        return self.client.get(
            "/getInfo",
            headers=headers,
        )

    def get_routers(self, headers: dict | None = None):
        return self.client.get(
            "/getRouters",
            headers=headers,
        )

    def logout(self, headers: dict | None = None):
        return self.client.post(
            "/logout",
            headers=headers,
        )
