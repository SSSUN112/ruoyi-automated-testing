"""按套件检查连接；不打印配置值、密码或连接异常正文。"""
import argparse
import socket
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def targets(config, suite):
    def endpoint(name, url):
        parsed = urlsplit(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname:
            raise ValueError('Invalid service URL: ' + name)
        return name, parsed.hostname, parsed.port or (443 if parsed.scheme=='https' else 80)
    result = [endpoint('Backend', config.BASE_URL),
              ('MySQL', config.DB_HOST, config.DB_PORT),
              ('Redis', config.REDIS_HOST, config.REDIS_PORT)]
    if suite in ('ui', 'full'):
        result.append(endpoint('Frontend', config.FRONTEND_URL))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=['smoke','api','ui','full'], required=True)
    args = parser.parse_args()
    import config
    pending = targets(config, args.suite)
    # 有限等待，避免单个未启动服务使流水线长期阻塞。
    for attempt in range(1, 4):
        failed=[]
        for name, host, port in pending:
            try:
                with socket.create_connection((host, port), timeout=3):
                    print(name + ': TCP reachable', flush=True)
            except OSError:
                failed.append((name,host,port))
                print(f'{name}: not reachable (attempt {attempt}/3)',flush=True)
        if not failed:
            print('Connectivity check passed; application readiness/authentication is checked by tests.')
            return 0
        pending=failed
        if attempt<3:time.sleep(2)
    print('Start required services or check TEST_ENV configuration. Failed: '+', '.join(t[0] for t in pending))
    return 1


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (ValueError, FileNotFoundError) as exc:
        print('Invalid or missing environment configuration: '+type(exc).__name__)
        raise SystemExit(2)
