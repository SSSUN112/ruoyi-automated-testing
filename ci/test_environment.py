import unittest
from types import SimpleNamespace
from check_environment import targets


class EnvironmentTests(unittest.TestCase):
    def test_suite_dependencies_and_configured_ports(self):
        config=SimpleNamespace(BASE_URL='https://example.test/api',
            FRONTEND_URL='http://example.test:12580',DB_HOST='db',DB_PORT=3307,
            REDIS_HOST='redis',REDIS_PORT=6380)
        for suite in ('api','smoke'):
            found=targets(config,suite)
            self.assertEqual([x[0] for x in found],['Backend','MySQL','Redis'])
            self.assertEqual(found[0][2],443)
            self.assertEqual(found[1][2],3307)
        for suite in ('ui','full'):
            self.assertEqual(targets(config,suite)[-1],('Frontend','example.test',12580))

    def test_invalid_url(self):
        with self.assertRaises(ValueError):
            targets(SimpleNamespace(BASE_URL='not-a-url'),'api')
