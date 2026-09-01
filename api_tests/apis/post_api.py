from common.request_util import RequestClient


class PostApi:
    def __init__(self, client: RequestClient):
        self.client = client

    def list_posts(
        self,
        headers: dict | None = None,
        params: dict | None = None,
    ):
        return self.client.get(
            "/system/post/list",
            headers=headers,
            params=params,
        )

    def get_post(
        self,
        post_id: int | str,
        headers: dict | None = None,
    ):
        return self.client.get(
            f"/system/post/{post_id}",
            headers=headers,
        )

    def create_post(
        self,
        payload: dict,
        headers: dict | None = None,
    ):
        return self.client.post(
            "/system/post",
            json=payload,
            headers=headers,
        )

    def update_post(
        self,
        payload: dict,
        headers: dict | None = None,
    ):
        return self.client.put(
            "/system/post",
            json=payload,
            headers=headers,
        )

    def delete_post(
        self,
        post_ids: int | str,
        headers: dict | None = None,
    ):
        return self.client.delete(
            f"/system/post/{post_ids}",
            headers=headers,
        )

    def export_posts(
        self,
        form_data: dict,
        headers: dict | None = None,
    ):
        return self.client.post(
            "/system/post/export",
            data=form_data,
            headers=headers,
        )
