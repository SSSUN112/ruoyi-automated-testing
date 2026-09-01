from common.request_util import RequestClient


class RoleApi:
    def __init__(self, client: RequestClient):
        self.client = client

    def list_roles(
        self,
        headers: dict | None = None,
        params: dict | None = None,
    ):
        return self.client.get(
            "/system/role/list",
            headers=headers,
            params=params,
        )

    def get_role_dept_tree(
        self,
        role_id: int | str,
        headers: dict | None = None,
    ):
        return self.client.get(
            f"/system/role/deptTree/{role_id}",
            headers=headers,
        )

    def get_role(
        self,
        role_id: int | str,
        headers: dict | None = None,
    ):
        return self.client.get(
            f"/system/role/{role_id}",
            headers=headers,
        )

    def create_role(
        self,
        payload: dict,
        headers: dict | None = None,
    ):
        return self.client.post(
            "/system/role",
            json=payload,
            headers=headers,
        )

    def update_role(
        self,
        payload: dict,
        headers: dict | None = None,
    ):
        return self.client.put(
            "/system/role",
            json=payload,
            headers=headers,
        )

    def update_role_data_scope(
        self,
        payload: dict,
        headers: dict | None = None,
    ):
        return self.client.put(
            "/system/role/dataScope",
            json=payload,
            headers=headers,
        )

    def change_role_status(
        self,
        payload: dict,
        headers: dict | None = None,
    ):
        return self.client.put(
            "/system/role/changeStatus",
            json=payload,
            headers=headers,
        )

    def delete_role(
        self,
        role_ids: int | str,
        headers: dict | None = None,
    ):
        return self.client.delete(
            f"/system/role/{role_ids}",
            headers=headers,
        )

    def export_roles(
        self,
        form_data: dict,
        headers: dict | None = None,
    ):
        return self.client.post(
            "/system/role/export",
            data=form_data,
            headers=headers,
        )

    def list_allocated_users(
        self,
        headers: dict | None = None,
        params: dict | None = None,
    ):
        return self.client.get(
            "/system/role/authUser/allocatedList",
            headers=headers,
            params=params,
        )

    def list_unallocated_users(
        self,
        headers: dict | None = None,
        params: dict | None = None,
    ):
        return self.client.get(
            "/system/role/authUser/unallocatedList",
            headers=headers,
            params=params,
        )

    def assign_users(
        self,
        params: dict,
        headers: dict | None = None,
    ):
        return self.client.put(
            "/system/role/authUser/selectAll",
            params=params,
            headers=headers,
        )

    def cancel_user(
        self,
        payload: dict,
        headers: dict | None = None,
    ):
        return self.client.put(
            "/system/role/authUser/cancel",
            json=payload,
            headers=headers,
        )

    def batch_cancel_users(
        self,
        params: dict,
        headers: dict | None = None,
    ):
        return self.client.put(
            "/system/role/authUser/cancelAll",
            params=params,
            headers=headers,
        )
