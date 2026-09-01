from typing import Any

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor


class MySQLClient:
    """
    MySQL 查询工具。

    默认返回字典：
    {
        "user_id": 1,
        "user_name": "admin"
    }
    """

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
    ):
        self._connection_options: dict[str, Any] = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
            "charset": "utf8mb4",
            "cursorclass": DictCursor,
            "autocommit": True,
            "connect_timeout": 5,
            "read_timeout": 10,
            "write_timeout": 10,
        }
        self.connection = self._connect()

    def _connect(self) -> Connection:
        return pymysql.connect(
            **self._connection_options,
        )

    def _ensure_connection(self) -> None:
        """
        长时间运行时检查连接，断开后重新创建连接。
        """
        try:
            self.connection.ping()
        except pymysql.MySQLError:
            self.connection = self._connect()

    def query_one(
        self,
        sql: str,
        params: tuple | list | None = None,
    ) -> dict | None:
        self._ensure_connection()

        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def query_all(
        self,
        sql: str,
        params: tuple | list | None = None,
    ) -> list[dict]:
        self._ensure_connection()

        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())

    def execute(
        self,
        sql: str,
        params: tuple | list | None = None,
    ) -> int:
        """
        返回受影响行数。

        当前主要用于必要的数据清理，业务数据优先通过接口清理。
        """
        self._ensure_connection()

        with self.connection.cursor() as cursor:
            return cursor.execute(sql, params)

    def close(self) -> None:
        self.connection.close()
