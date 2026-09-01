from __future__ import annotations

import socket
from typing import Any


class RedisClient:
    def __init__(
        self,
        host: str,
        port: int,
        db: int = 0,
        password: str = "",
        timeout: int = 5,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.timeout = timeout

    def get(self, key: str) -> str | None:
        return self.execute("GET", key)

    def set(self, key: str, value: str) -> str:
        result = self.execute("SET", key, value)
        assert result == "OK", f"Redis SET 失败：key={key}, result={result}"
        return result

    def close(self) -> None:
        return None

    def execute(self, *parts: Any) -> Any:
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            if self.password:
                self._send_command(sock, "AUTH", self.password)
                self._read_response(sock)

            self._send_command(sock, "SELECT", self.db)
            self._read_response(sock)

            self._send_command(sock, *parts)
            return self._read_response(sock)

    def _send_command(self, sock: socket.socket, *parts: Any) -> None:
        encoded_parts = [str(part).encode("utf-8") for part in parts]
        payload = [f"*{len(encoded_parts)}\r\n".encode("utf-8")]

        for part in encoded_parts:
            payload.append(f"${len(part)}\r\n".encode("utf-8"))
            payload.append(part)
            payload.append(b"\r\n")

        sock.sendall(b"".join(payload))

    def _read_response(self, sock: socket.socket) -> Any:
        prefix = self._read_exact(sock, 1)

        if prefix == b"+":
            return self._read_line(sock).decode("utf-8")

        if prefix == b"-":
            message = self._read_line(sock).decode("utf-8")
            raise RuntimeError(f"Redis error: {message}")

        if prefix == b":":
            return int(self._read_line(sock))

        if prefix == b"$":
            length = int(self._read_line(sock))
            if length == -1:
                return None
            data = self._read_exact(sock, length)
            self._read_exact(sock, 2)
            return data.decode("utf-8")

        if prefix == b"*":
            length = int(self._read_line(sock))
            return [self._read_response(sock) for _ in range(length)]

        raise RuntimeError(f"无法解析 Redis 响应：prefix={prefix!r}")

    def _read_line(self, sock: socket.socket) -> bytes:
        chunks = []

        while True:
            char = self._read_exact(sock, 1)
            if char == b"\r":
                self._read_exact(sock, 1)
                return b"".join(chunks)
            chunks.append(char)

    def _read_exact(self, sock: socket.socket, length: int) -> bytes:
        data = b""

        while len(data) < length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                raise RuntimeError("Redis 连接已关闭")
            data += chunk

        return data
