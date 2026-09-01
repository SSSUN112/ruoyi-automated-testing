from common.request_util import RequestClient


class UserApi:
    def __init__(self, client: RequestClient):
        self.client = client

    def list_users(
        self,
        headers: dict | None = None,
        params: dict | None = None,
    ):
        return self.client.get(
            "/system/user/list",
            headers=headers,
            params=params,
        )

    def get_user(
        self,
        user_id: int | str,
        headers: dict | None = None,
    ):
        return self.client.get(
            f"/system/user/{user_id}",
            headers=headers,
        )

    def get_user_options(self, headers: dict | None = None):
        return self.client.get(
            "/system/user/",
            headers=headers,
        )

    def create_user(
        self,
        payload: dict,
        headers: dict,
    ):
        return self.client.post(
            "/system/user",
            json=payload,
            headers=headers,
        )

    def update_user(
        self,
        payload: dict,
        headers: dict,
    ):
        return self.client.put(
            "/system/user",
            json=payload,
            headers=headers,
        )

    def delete_user(
        self,
        user_ids: int | str,
        headers: dict,
    ):
        return self.client.delete(
            f"/system/user/{user_ids}",
            headers=headers,
        )

    def reset_user_password(
        self,
        payload: dict,
        headers: dict,
    ):
        return self.client.put(
            "/system/user/resetPwd",
            json=payload,
            headers=headers,
        )

    def change_user_status(
        self,
        payload: dict,
        headers: dict,
    ):
        return self.client.put(
            "/system/user/changeStatus",
            json=payload,
            headers=headers,
        )

    def get_user_profile(
        self,
        headers: dict | None = None,
    ):
        return self.client.get(
            "/system/user/profile",
            headers=headers,
        )

    def update_user_profile(
        self,
        payload: dict,
        headers: dict,
    ):
        return self.client.put(
            "/system/user/profile",
            json=payload,
            headers=headers,
        )

    def upload_user_avatar(
        self,
        files: dict,
        headers: dict | None = None,
    ):
        return self.client.post(
            "/system/user/profile/avatar",
            files=files,
            headers=headers,
        )
