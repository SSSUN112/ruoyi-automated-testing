from common.request_util import RequestClient


class DeptApi:
    def __init__(self, client: RequestClient):
        self.client = client

    def list_depts(
        self,
        headers: dict | None = None,
        params: dict | None = None,
    ):
        return self.client.get(
            "/system/dept/list",
            headers=headers,
            params=params,
        )

    def list_depts_exclude(
        self,
        dept_id: int | str,
        headers: dict | None = None,
    ):
        return self.client.get(
            f"/system/dept/list/exclude/{dept_id}",
            headers=headers,
        )

    def get_dept(
        self,
        dept_id: int | str,
        headers: dict | None = None,
    ):
        return self.client.get(
            f"/system/dept/{dept_id}",
            headers=headers,
        )

    def create_dept(
        self,
        payload: dict,
        headers: dict | None = None,
    ):
        return self.client.post(
            "/system/dept",
            json=payload,
            headers=headers,
        )

    def update_dept(
        self,
        payload: dict,
        headers: dict | None = None,
    ):
        return self.client.put(
            "/system/dept",
            json=payload,
            headers=headers,
        )

    def delete_dept(
        self,
        dept_ids: int | str,
        headers: dict | None = None,
    ):
        return self.client.delete(
            f"/system/dept/{dept_ids}",
            headers=headers,
        )
