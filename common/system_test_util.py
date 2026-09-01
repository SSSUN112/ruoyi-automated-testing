from __future__ import annotations

from common.db_util import MySQLClient


def find_menu_by_name(db: MySQLClient, menu_name: str) -> dict | None:
    return db.query_one(
        """
        SELECT menu_id, menu_name, parent_id, path, perms, menu_type, status
        FROM sys_menu
        WHERE menu_name = %s
        ORDER BY menu_id DESC
        LIMIT 1
        """,
        (menu_name,),
    )


def cleanup_menus_by_names(db: MySQLClient, menu_names: list[str]) -> None:
    if not menu_names:
        return

    placeholders = ",".join(["%s"] * len(menu_names))
    rows = db.query_all(
        f"SELECT menu_id FROM sys_menu WHERE menu_name IN ({placeholders})",
        tuple(menu_names),
    )
    menu_ids = [row["menu_id"] for row in rows]

    if not menu_ids:
        return

    id_placeholders = ",".join(["%s"] * len(menu_ids))
    params = tuple(menu_ids)

    db.execute(
        f"DELETE FROM sys_role_menu WHERE menu_id IN ({id_placeholders})",
        params,
    )
    db.execute(
        f"DELETE FROM sys_menu WHERE menu_id IN ({id_placeholders})",
        params,
    )


def cleanup_auto_menus_by_names(
    db: MySQLClient,
    menu_names: list[str],
    prefix: str = "接口自动化菜单",
) -> None:
    cleanup_menus_by_names(
        db,
        [menu_name for menu_name in menu_names if menu_name.startswith(prefix)],
    )


def find_dept_by_name(
    db: MySQLClient,
    dept_name: str,
    parent_id: int | None = None,
) -> dict | None:
    sql = """
        SELECT dept_id, dept_name, parent_id, ancestors, status, del_flag
        FROM sys_dept
        WHERE dept_name = %s
    """
    params: list = [dept_name]

    if parent_id is not None:
        sql += " AND parent_id = %s"
        params.append(parent_id)

    sql += " ORDER BY dept_id DESC LIMIT 1"

    return db.query_one(sql, tuple(params))


def cleanup_depts_by_names(db: MySQLClient, dept_names: list[str]) -> None:
    if not dept_names:
        return

    placeholders = ",".join(["%s"] * len(dept_names))
    db.execute(
        f"DELETE FROM sys_dept WHERE dept_name IN ({placeholders})",
        tuple(dept_names),
    )


def cleanup_auto_depts_by_names(
    db: MySQLClient,
    dept_names: list[str],
    prefix: str = "接口自动化部门",
) -> None:
    cleanup_depts_by_names(
        db,
        [dept_name for dept_name in dept_names if dept_name.startswith(prefix)],
    )


def find_post_by_code(db: MySQLClient, post_code: str) -> dict | None:
    return db.query_one(
        """
        SELECT post_id, post_code, post_name, post_sort, status
        FROM sys_post
        WHERE post_code = %s
        ORDER BY post_id DESC
        LIMIT 1
        """,
        (post_code,),
    )


def cleanup_posts_by_codes(db: MySQLClient, post_codes: list[str]) -> None:
    if not post_codes:
        return

    placeholders = ",".join(["%s"] * len(post_codes))
    rows = db.query_all(
        f"SELECT post_id FROM sys_post WHERE post_code IN ({placeholders})",
        tuple(post_codes),
    )
    post_ids = [row["post_id"] for row in rows]

    if not post_ids:
        return

    id_placeholders = ",".join(["%s"] * len(post_ids))
    params = tuple(post_ids)

    db.execute(
        f"DELETE FROM sys_user_post WHERE post_id IN ({id_placeholders})",
        params,
    )
    db.execute(
        f"DELETE FROM sys_post WHERE post_id IN ({id_placeholders})",
        params,
    )


def cleanup_auto_posts_by_codes(
    db: MySQLClient,
    post_codes: list[str],
    prefix: str = "api_auto_post_",
) -> None:
    cleanup_posts_by_codes(
        db,
        [post_code for post_code in post_codes if post_code.startswith(prefix)],
    )


def find_role_by_key(db: MySQLClient, role_key: str) -> dict | None:
    return db.query_one(
        """
        SELECT role_id, role_name, role_key, role_sort, data_scope, status, del_flag
        FROM sys_role
        WHERE role_key = %s
        ORDER BY role_id DESC
        LIMIT 1
        """,
        (role_key,),
    )


def cleanup_roles_by_keys(db: MySQLClient, role_keys: list[str]) -> None:
    if not role_keys:
        return

    placeholders = ",".join(["%s"] * len(role_keys))
    rows = db.query_all(
        f"SELECT role_id FROM sys_role WHERE role_key IN ({placeholders})",
        tuple(role_keys),
    )
    role_ids = [row["role_id"] for row in rows]

    if not role_ids:
        return

    id_placeholders = ",".join(["%s"] * len(role_ids))
    params = tuple(role_ids)

    db.execute(
        f"DELETE FROM sys_user_role WHERE role_id IN ({id_placeholders})",
        params,
    )
    db.execute(
        f"DELETE FROM sys_role_menu WHERE role_id IN ({id_placeholders})",
        params,
    )
    db.execute(
        f"DELETE FROM sys_role_dept WHERE role_id IN ({id_placeholders})",
        params,
    )
    db.execute(
        f"DELETE FROM sys_role WHERE role_id IN ({id_placeholders})",
        params,
    )


def cleanup_auto_roles_by_keys(
    db: MySQLClient,
    role_keys: list[str],
    prefix: str = "api_auto_role_",
) -> None:
    cleanup_roles_by_keys(
        db,
        [role_key for role_key in role_keys if role_key.startswith(prefix)],
    )


def find_user_role(db: MySQLClient, user_id: int | str, role_id: int | str) -> dict | None:
    return db.query_one(
        """
        SELECT user_id, role_id
        FROM sys_user_role
        WHERE user_id = %s AND role_id = %s
        LIMIT 1
        """,
        (user_id, role_id),
    )
