from typing import Any

import requests

from common.allure_util import allure_step, attach_json, attach_text
from common.log_util import get_logger, mask_sensitive


logger = get_logger(__name__)


def _response_body_for_report(response: requests.Response) -> str:
    content_type = response.headers.get("Content-Type", "").lower()

    if "application/json" in content_type or content_type.startswith("text/"):
        return response.text

    return f"<binary response: {len(response.content)} bytes>"


class RequestClient:
    """
    HTTP 请求客户端。

    统一处理：
    1. 基础地址；
    2. 超时时间；
    3. requests.Session；
    4. 禁止读取 Clash 等系统代理。
    """

    def __init__(self, base_url: str, timeout: int | float = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.session = requests.Session()

        # 防止 localhost 请求经过 Clash 或系统代理
        self.session.trust_env = False

    def build_url(self, path: str) -> str:
        if path.startswith(("http://", "https://")):
            return path

        return f"{self.base_url}/{path.lstrip('/')}"

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        data: dict | None = None,
        json: dict | None = None,
        files: dict | None = None,
        headers: dict | None = None,
        timeout: int | float | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        url = self.build_url(path)
        request_timeout = timeout if timeout is not None else self.timeout

        request_info = {
            "method": method.upper(),
            "url": url,
            "params": params,
            "data": data,
            "json": json,
            "headers": mask_sensitive(headers or {}),
            "has_files": bool(files),
            "timeout": request_timeout,
        }
        logger.info("发送接口请求：%s", mask_sensitive(request_info))

        with allure_step(f"{method.upper()} {path}"):
            attach_json("request", mask_sensitive(request_info))

            try:
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    data=data,
                    json=json,
                    files=files,
                    headers=headers,
                    timeout=request_timeout,
                    **kwargs,
                )
            except requests.Timeout as exc:
                timeout_info = {
                    "method": method.upper(),
                    "url": url,
                    "timeout": request_timeout,
                    "exception": repr(exc),
                }
                logger.error("Request timeout: %s", mask_sensitive(timeout_info))
                attach_json("timeout", mask_sensitive(timeout_info))
                raise

            response_body = _response_body_for_report(response)
            response_info = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response_body,
            }
            logger.info("接口响应：%s", mask_sensitive(response_info))
            attach_text("response", mask_sensitive(response_body))

            return response

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("DELETE", path, **kwargs)

    def close(self) -> None:
        self.session.close()
