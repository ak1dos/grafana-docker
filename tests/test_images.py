"""Exercise Compose image overrides without loading deployment credentials."""
import json
import os
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
VARIABLES = {'prometheus': 'PROMETHEUS_IMAGE', 'alertmanager': 'ALERTMANAGER_IMAGE',
             'loki': 'LOKI_IMAGE', 'grafana': 'GRAFANA_IMAGE', 'gateway': 'NGINX_IMAGE',
             'rustfs': 'RUSTFS_IMAGE', 'init': 'MC_IMAGE', 'alloy': 'ALLOY_IMAGE'}

class ImageConfigurationTest(unittest.TestCase):
    def test_overrides_reach_both_compose_manifests(self):
        env = os.environ.copy()
        env.update({variable: 'example.invalid/test/' + service + ':test'
                    for service, variable in VARIABLES.items()})
        for manifest, services in [('docker-compose.yaml', VARIABLES),
                                   ('agents/compose.yaml', {'alloy': 'ALLOY_IMAGE'})]:
            with self.subTest(manifest=manifest):
                result = subprocess.run(['docker', 'compose', '--env-file', str(ROOT / '.env.example'),
                                         '-f', str(ROOT / manifest), '--profile', 'bootstrap',
                                         'config', '--no-env-resolution', '--format', 'json'],
                                        env=env, capture_output=True, text=True, check=True)
                config = json.loads(result.stdout)
                for service, variable in services.items():
                    self.assertEqual(config['services'][service]['image'], env[variable])

if __name__ == '__main__':
    unittest.main()
