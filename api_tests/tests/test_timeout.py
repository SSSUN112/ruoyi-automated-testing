import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import requests

from common.allure_util import allure_step, set_case_metadata
from common.request_util import RequestClient


TIMEOUT_FEATURE = "超时异常"


class SlowResponseHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.3)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        try:
            self.wfile.write(b'{"code": 200, "msg": "ok"}')
        except OSError:
            pass

    def log_message(self, format, *args):
        return


@pytest.fixture()
def slow_http_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), SlowResponseHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


def test_request_timeout_is_logged_and_raised(slow_http_server, caplog):
    set_case_metadata(
        {"id": "TIMEOUT-001", "title": "请求超时应记录日志并抛出异常"},
        feature=TIMEOUT_FEATURE,
        story="读取超时",
    )

    caplog.set_level(logging.ERROR, logger="common.request_util")
    client = RequestClient(base_url=slow_http_server, timeout=1)

    try:
        with allure_step("使用短超时时间请求慢接口"):
            with pytest.raises(requests.Timeout) as exc_info:
                client.get("/slow", timeout=0.05)

        with allure_step("校验超时异常和日志"):
            assert "timed out" in str(exc_info.value).lower(), exc_info.value
            assert any("Request timeout" in record.message for record in caplog.records), [
                record.message for record in caplog.records
            ]
    finally:
        client.close()
