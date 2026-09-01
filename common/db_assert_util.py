from typing import Any

from common.db_util import MySQLClient


def assert_db_row_exists(
    db: MySQLClient,
    sql: str,
    params: tuple | list | None = None,
    expected_fields: dict[str, Any] | None = None,
) -> dict:
    """
    断言数据库中存在记录，并可继续校验字段值。
    """
    row = db.query_one(sql, params)

    assert row is not None, (
        f"数据库中未查询到预期记录。\n"
        f"SQL：{sql}\n"
        f"参数：{params}"
    )

    if expected_fields:
        for field, expected_value in expected_fields.items():
            actual_value = row.get(field)

            assert actual_value == expected_value, (
                f"数据库字段断言失败："
                f"field={field}, "
                f"expected={expected_value!r}, "
                f"actual={actual_value!r}, "
                f"row={row}"
            )

    return row


def assert_db_row_not_exists(
    db: MySQLClient,
    sql: str,
    params: tuple | list | None = None,
) -> None:
    """
    断言数据库中不存在记录。
    """
    row = db.query_one(sql, params)

    assert row is None, (
        f"数据库中仍然存在不应存在的记录：{row}\n"
        f"SQL：{sql}\n"
        f"参数：{params}"
    )


def assert_database_case(
    db: MySQLClient,
    database_case: dict,
) -> dict | None:
    assertion_type = database_case.get("assert", "exists")

    if assertion_type == "not_exists":
        assert_db_row_not_exists(
            db=db,
            sql=database_case["sql"],
            params=tuple(database_case.get("params", [])),
        )
        return None

    return assert_db_row_exists(
        db=db,
        sql=database_case["sql"],
        params=tuple(database_case.get("params", [])),
        expected_fields=database_case.get("expected_fields"),
    )
