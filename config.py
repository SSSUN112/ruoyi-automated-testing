import os
from pathlib import Path

from dotenv import load_dotenv


# api_automation 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 测试数据目录
API_TESTS_DIR = BASE_DIR / "api_tests"
UI_TESTS_DIR = BASE_DIR / "ui_tests"
PERF_TESTS_DIR = BASE_DIR / "perf_tests"

API_DATA_DIR = API_TESTS_DIR / "data"
UI_DATA_DIR = UI_TESTS_DIR / "data"
PERF_DATA_DIR = PERF_TESTS_DIR / "data"

# Keep old API test imports working while the project is split by test type.
DATA_DIR = API_DATA_DIR

# 加载 .env，并覆盖同名系统环境变量
load_dotenv(BASE_DIR / ".env", override=False)

TEST_ENV = os.getenv("TEST_ENV", "test").strip().lower()
ENV_FILE = BASE_DIR / f".env.{TEST_ENV}"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE, override=True)
elif TEST_ENV != "test":
    raise FileNotFoundError(f"Missing environment config file: {ENV_FILE}")
else:
    load_dotenv(BASE_DIR / ".env", override=True)


BASE_URL = os.getenv(
    "RUOYI_BASE_URL",
    "http://127.0.0.1:19099",
).rstrip("/")

USERNAME = os.getenv("RUOYI_USERNAME", "admin")
PASSWORD = os.getenv("RUOYI_PASSWORD", "admin123")

REQUEST_TIMEOUT = int(
    os.getenv("REQUEST_TIMEOUT", "30")
)

FRONTEND_URL = os.getenv(
    "RUOYI_FRONTEND_URL",
    "http://127.0.0.1:12580",
).rstrip("/")

UI_HEADLESS = os.getenv("UI_HEADLESS", "true").lower() in {"1", "true", "yes", "on"}
UI_BROWSER = os.getenv("UI_BROWSER", "chromium")
UI_SLOW_MO = int(os.getenv("UI_SLOW_MO", "0"))
UI_TIMEOUT = int(os.getenv("UI_TIMEOUT", "10000"))
UI_VIEWPORT_WIDTH = int(os.getenv("UI_VIEWPORT_WIDTH", "1366"))
UI_VIEWPORT_HEIGHT = int(os.getenv("UI_VIEWPORT_HEIGHT", "768"))


DB_HOST = os.getenv("RUOYI_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("RUOYI_DB_PORT", "13306"))
DB_USER = os.getenv("RUOYI_DB_USER", "root")
DB_PASSWORD = os.getenv("RUOYI_DB_PASSWORD", "root")
DB_NAME = os.getenv("RUOYI_DB_NAME", "ruoyi-fastapi")

REDIS_HOST = os.getenv("RUOYI_REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("RUOYI_REDIS_PORT", "16379"))
REDIS_PASSWORD = os.getenv("RUOYI_REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("RUOYI_REDIS_DB", "2"))
