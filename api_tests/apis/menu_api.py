from common.request_util import RequestClient


class MenuApi:
    def __init__(self, client: RequestClient):
        self.client = client

    def get_menu_tree(self, headers: dict | None = None):
        return self.client.get(
            "/system/menu/treeselect",
            headers=headers,
        )

    def get_role_menu_tree(
        self,
        role_id: int | str,
        headers: dict | None = None,
    ):
        return self.client.get(
            f"/system/menu/roleMenuTreeselect/{role_id}",
            headers=headers,
        )

    def list_menus(
        self,
        headers: dict | None = None,
        params: dict | None = None,
    ):
        return self.client.get(
            "/system/menu/list",
            headers=headers,
            params=params,
        )

    def get_menu(
        self,
        menu_id: int | str,
        headers: dict | None = None,
    ):
        return self.client.get(
            f"/system/menu/{menu_id}",
            headers=headers,
        )

    def create_menu(
        self,
        payload: dict,
        headers: dict | None = None,
    ):
        return self.client.post(
            "/system/menu",
            json=payload,
            headers=headers,
        )

    def update_menu(
        self,
        payload: dict,
        headers: dict | None = None,
    ):
        return self.client.put(
            "/system/menu",
            json=payload,
            headers=headers,
        )

    def delete_menu(
        self,
        menu_ids: int | str,
        headers: dict | None = None,
    ):
        return self.client.delete(
            f"/system/menu/{menu_ids}",
            headers=headers,
        )
