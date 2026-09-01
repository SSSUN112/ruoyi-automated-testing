from __future__ import annotations

from common.db_util import MySQLClient


def find_user_by_name(db: MySQLClient, user_name: str) -> dict | None:
    return db.query_one(
        """
        SELECT user_id, user_name, nick_name, status, del_flag
        FROM sys_user
        WHERE user_name = %s
        ORDER BY user_id DESC
        LIMIT 1
        """,
        (user_name,),
    )


def cleanup_users_by_names(
    db: MySQLClient,
    user_names: list[str],
) -> None:
    if not user_names:
        return

    placeholders = ",".join(["%s"] * len(user_names))
    rows = db.query_all(
        f"SELECT user_id FROM sys_user WHERE user_name IN ({placeholders})",
        tuple(user_names),
    )
    user_ids = [row["user_id"] for row in rows]

    if not user_ids:
        return

    id_placeholders = ",".join(["%s"] * len(user_ids))
    params = tuple(user_ids)

    db.execute(
        f"DELETE FROM sys_user_role WHERE user_id IN ({id_placeholders})",
        params,
    )
    db.execute(
        f"DELETE FROM sys_user_post WHERE user_id IN ({id_placeholders})",
        params,
    )
    db.execute(
        f"DELETE FROM sys_user WHERE user_id IN ({id_placeholders})",
        params,
    )


def cleanup_auto_users_by_names(
    db: MySQLClient,
    user_names: list[str],
    prefix: str = "api_auto_",
) -> None:
    cleanup_users_by_names(
        db,
        [user_name for user_name in user_names if user_name.startswith(prefix)],
    )
