from __future__ import annotations

from common.allure_util import allure_step
from common.assert_util import assert_api_response
from common.redis_util import RedisClient


def get_captcha_payload(auth_api, redis_client: RedisClient) -> tuple[dict, dict]:
    with allure_step("获取图片验证码"):
        captcha_response = auth_api.get_captcha_image()
        captcha_result = assert_api_response(
            captcha_response,
            {
                "http_status": 200,
                "code": 200,
                "required_fields": ["registerEnabled", "captchaEnabled", "uuid"],
            },
        )

    if not captcha_result["captchaEnabled"]:
        return captcha_result, {}

    uuid = captcha_result["uuid"]
    redis_key = f"captcha_codes:{uuid}"

    with allure_step("从 Redis 读取验证码答案"):
        code = redis_client.get(redis_key)

    assert code is not None, f"Redis 中未找到验证码：{redis_key}"
    return captcha_result, {"uuid": uuid, "code": str(code)}
