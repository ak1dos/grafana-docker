from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/prepare-env'

class PrepareEnvTest(unittest.TestCase):
    def test_preserves_existing_settings_and_fills_missing_images(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / '.env.example').write_text('MONITORING_BIND_IP=default\nALLOY_IMAGE=default:1\nLOKI_IMAGE=default:2\n')
            (root / '.env').write_text('ALLOY_IMAGE=custom:3\n')
            target = root / 'installed.env'
            target.write_text('MONITORING_BIND_IP=private\nLOKI_IMAGE=installed:4\n')
            subprocess.run(['sh', str(SCRIPT), str(root), str(target)], check=True)
            values = dict(line.split('=', 1) for line in target.read_text().splitlines())
            self.assertEqual(values, {'MONITORING_BIND_IP': 'private', 'ALLOY_IMAGE': 'custom:3', 'LOKI_IMAGE': 'installed:4'})
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            previous = target.read_bytes()
            subprocess.run(['sh', str(SCRIPT), str(root), str(target)], check=True)
            self.assertEqual(target.read_bytes(), previous)

    def test_fresh_install_uses_source_overrides(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / '.env.example').write_text('ALLOY_IMAGE=default:1\n')
            (root / '.env').write_text('ALLOY_IMAGE=custom:2\n')
            target = root / 'installed.env'
            subprocess.run(['sh', str(SCRIPT), str(root), str(target)], check=True)
            self.assertEqual(target.read_text(), 'ALLOY_IMAGE=custom:2\n')

    def test_in_place_migration_does_not_duplicate_existing_lines(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / '.env.example').write_text('ALLOY_IMAGE=default:1\n')
            target = root / '.env'
            target.write_text('COMPOSE_FILE=agents/compose.yaml\n')
            subprocess.run(['sh', str(SCRIPT), str(root), str(target)], check=True)
            self.assertEqual(target.read_text(), 'COMPOSE_FILE=agents/compose.yaml\nALLOY_IMAGE=default:1\n')
