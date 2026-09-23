import pathlib
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts/bootstrap"

class BootstrapTest(unittest.TestCase):
    def test_private_files_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            target = pathlib.Path(temp) / "runtime"
            first = subprocess.run(["python3", str(SCRIPT), str(target)], capture_output=True)
            self.assertEqual(first.returncode, 0, first.stderr.decode())
            files = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
            self.assertIn(pathlib.Path("rustfs.env"), list(files))
            self.assertNotIn(pathlib.Path("garage.env"), list(files))
            admin = dict(line.split("=", 1) for line in files[pathlib.Path("rustfs.env")].decode().splitlines())
            app = dict(line.split("=", 1) for line in files[pathlib.Path("loki.env")].decode().splitlines())
            self.assertNotEqual(admin["RUSTFS_ACCESS_KEY"], app["S3_ACCESS_KEY"])
            self.assertNotEqual(admin["RUSTFS_SECRET_KEY"], app["S3_SECRET_KEY"])
            self.assertNotEqual(admin["RUSTFS_RPC_SECRET"], admin["RUSTFS_SECRET_KEY"])
            self.assertEqual(app["S3_REGION"], "us-east-1")
            self.assertEqual(app["S3_ENDPOINT"], "10.20.0.1:19000")
            self.assertIn(pathlib.Path("agents/fujiserver.env"), list(files))
            for p in target.rglob("*"):
                if p.is_file():
                    self.assertEqual(p.stat().st_mode & 0o077, 0)
            second = subprocess.run(["python3", str(SCRIPT), str(target)], capture_output=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertTrue(files == {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}, "Bootstrap changed existing secrets")
            for data in files.values():
                self.assertNotIn(b"GENERATED_", data)

if __name__ == "__main__":
    unittest.main()
