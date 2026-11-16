import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

# Exercise CLI subprocesses without depending on GitHub availability.
TEST_RUNNER = """
import io, runpy, sys
from unittest.mock import patch
sys.argv = sys.argv[1:]
with patch('urllib.request.urlopen', return_value=io.BytesIO(
        b'wwan_firmware_map_url = "https://fw.test/modem-firmware.json"')):
    runpy.run_path(sys.argv[0], run_name='__main__')
"""

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('firmware_build', ROOT/'build.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
class TestGenerator(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root/'source'
        self.output = self.root/'build'
        self.release = self.source/'telit/TEST/1.20/1.0'
        (self.release/'payload').mkdir(parents=True)
        (self.release/'payload/stream.bin').write_bytes(b'firmware')
        self.meta = self.release/'meta.toml'
        self.meta.write_text('manufacturer = "Telit"\ninstaller = "uxfp"\ntelit_version = "M0L.001004"\ntelit_package_version = "40.00.004"\npayload_entry = "stream.bin"\n')

    def build(self):
        return g.build(self.source, self.output, 'https://fw.test/cellular-firmware')

    def test_flavor_url_from_git(self):
        with patch.dict('os.environ', {'FIRMWARE_BASE_URL': 'https://ignored.test',
                                       'FIRMWARE_BUILD_FLAVOR': '/does/not/exist'}, clear=True), \
                patch.object(g, 'urlopen') as fetch:
            fetch.return_value.__enter__.return_value.read.return_value = (
                b'wwan_firmware_map_url = "https://git.test/modem-firmware/modem-firmware.json"')
            self.assertEqual(g.firmware_base_url(), 'https://git.test/modem-firmware')
            self.assertIn('/psleng/vyos-build/psl-master/', fetch.call_args.args[0])
            fetch.return_value.__enter__.return_value.read.return_value = b'invalid toml!'
            with self.assertRaises(ValueError):
                g.firmware_base_url()

    def test_no_arguments_builds_dist_without_publishing(self):
        with patch.object(g, 'build') as build, patch.object(sys, 'argv', ['build.py', '--source', str(ROOT)]), \
                patch.object(g, 'signing_config', return_value=None), \
                patch.object(g, 'firmware_base_url', return_value='https://fw.test'):
            g.main()
        self.assertEqual(build.call_args.args[:2], (ROOT, ROOT/'dist'))

    def test_cli_uses_separate_source_and_output(self):
        import os
        env = {key: value for key, value in os.environ.items()
               if not key.startswith('FIRMWARE_SIGNING_') and key != 'FIRMWARE_REQUIRE_SIGNING'}
        result = subprocess.run(
            [sys.executable, '-c', TEST_RUNNER, str(ROOT/'build.py'),
             '--source', str(self.source), '--output', str(self.output)],
            cwd=self.root, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.output/'modem-firmware.json').is_file())
        self.assertFalse((self.source/'dist').exists())

    def test_reproducible_incremental_and_corrupt_rebuild(self):
        self.assertEqual(self.build(), {'built': 1, 'reused': 0})
        self.assertFalse((self.output/'inventory.json').exists())
        path = next(self.output.rglob('*.tar'))
        checksum = g.digest(path)
        mtime = path.stat().st_mtime_ns
        self.assertEqual(self.build(), {'built': 0, 'reused': 1})
        self.assertEqual(path.stat().st_mtime_ns, mtime)
        path.write_bytes(b'corrupt')
        self.assertEqual(self.build(), {'built': 1, 'reused': 0})
        catalog = json.loads((self.output/"modem-firmware.json").read_text())
        name = catalog["cellular-firmware"][0]["revisions"][0]["firmware"][0]["url"].rsplit("/", 1)[-1]
        self.assertEqual(g.digest(path.with_name(name)), checksum)

    def test_build_from_isolated_checkout(self):
        checkout = self.root/'independent'
        shutil.copytree(self.source, checkout)
        import os
        env = {key: value for key, value in os.environ.items() if not key.startswith('FIRMWARE_SIGNING_') and key != 'FIRMWARE_REQUIRE_SIGNING'}
        result = subprocess.run([sys.executable, '-c', TEST_RUNNER, str(ROOT/'build.py'), '--source', str(checkout), '--output', str(checkout/'dist')],
                                cwd=checkout, env=env, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((checkout/'dist/modem-firmware.json').is_file())

    def test_source_zip_builds_same_archive_as_binary(self):
        self.build()
        target = next(self.output.rglob('*.tar'))
        expected = g.digest(target)
        binary = self.release/'payload/stream.bin'
        with zipfile.ZipFile(binary.parent/'source.zip', 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(binary, arcname=binary.name)
        binary.unlink()
        self.assertEqual(self.build()['reused'], 1)
        self.assertEqual(g.digest(target), expected)
        self.assertFalse(binary.exists())

    def test_source_zip_rejects_unsafe_paths(self):
        binary = self.release/'payload/stream.bin'
        with zipfile.ZipFile(binary.parent/'source.zip', 'w') as archive:
            archive.writestr('../stream.bin', b'firmware')
        binary.unlink()
        with self.assertRaisesRegex(ValueError, 'Unsafe archive path'):
            self.build()

    def test_archive_path_uses_telit_version(self):
        with patch.object(g, "datetime") as clock:
            clock.now.return_value.strftime.return_value = "20261101064712"
            self.build()
        expected = self.output/'telit/TEST/1.20/M0L.001004/TEST-1.20-M0L.001004-2026110106471200.tar'
        self.assertTrue(expected.is_file())
        catalog = json.loads((self.output/'modem-firmware.json').read_text())
        release = catalog['cellular-firmware'][0]['revisions'][0]['firmware'][0]
        self.assertEqual(release['url'],
                         'https://fw.test/cellular-firmware/telit/TEST/1.20/M0L.001004/TEST-1.20-M0L.001004-2026110106471200.tar')
        self.assertEqual(release['telit_package_version'], '40.00.004')

    def test_unsafe_telit_version_cannot_be_archive_directory(self):
        self.meta.write_text(self.meta.read_text().replace('M0L.001004', '../escape'))
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse((self.output/'modem-firmware.json').exists())

    def test_changed_payload_rebuilds(self):
        self.build()
        (self.release/'payload/stream.bin').write_bytes(b'new firmware')
        self.assertEqual(self.build(), {'built': 1, 'reused': 0})

    def test_catalog_rejects_bad_version(self):
        (self.release.parent/'bad').mkdir()
        shutil.copytree(self.release/'payload', self.release.parent/'bad/payload')
        (self.release.parent/'bad/meta.toml').write_bytes(self.meta.read_bytes())
        with self.assertRaises(ValueError):
            self.build()
        self.assertFalse((self.output/'modem-firmware.json').exists())

    def test_grouped_revisions(self):
        self.meta.write_text(self.meta.read_text()+'revisions = ["1.10", "1.20"]\n')
        self.assertEqual(self.build()['built'], 2)
        data=json.loads((self.output/'modem-firmware.json').read_text())
        self.assertEqual(len(data['cellular-firmware'][0]['revisions']), 2)

    def test_symlink_payload_refused(self):
        (self.release/'payload/link').symlink_to(self.meta)
        with self.assertRaises(ValueError):
            self.build()



class TestAutomaticSigning(unittest.TestCase):
    setUp = TestGenerator.setUp

    def checkout(self):
        checkout = self.root/'checkout'
        shutil.copytree(self.source, checkout)
        shutil.copyfile(ROOT/'build.py', checkout/'build.py')
        return checkout

    def configure(self, checkout):
        tool = checkout/'signer.py'
        tool.write_text('''import argparse,fcntl,hashlib
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('command');p.add_argument('--catalog');p.add_argument('--archive-root')
a,_=p.parse_known_args()
assert a.command=='release'
root=Path(a.archive_root)
# The build lock must still be held by the parent while signing runs.
with (root/'.build.lock').open('a') as lock:
    try:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        pass
    else:
        raise SystemExit('Build lock released before signing')
for item in [Path(a.catalog),*root.rglob('*.tar')]:
    Path(str(item)+'.sig').write_text(hashlib.sha256(item.read_bytes()).hexdigest())
''')
        signing=checkout/'signing'
        tool.rename(checkout/'wwan-firmware-sign')
        signing.mkdir()
        for name in ('igos-firmware-leaf.key',
                     'igos-firmware-leaf.pem',
                     'igos-firmware-root-ca.crl', 'leaf.passphrase'):
            path=signing/name
            path.parent.mkdir(exist_ok=True)
            path.touch()
        return checkout/'wwan-firmware-sign', signing

    def run_checkout(self, checkout, env=None):
        import os
        clean={key:value for key,value in os.environ.items()
               if not key.startswith('FIRMWARE_SIGNING_') and key!='FIRMWARE_REQUIRE_SIGNING'}
        signing=checkout/'signing'
        if signing.is_dir():
            clean.update(FIRMWARE_SIGNING_DIR=str(signing),
                         FIRMWARE_SIGNING_PASSWORD_FILE=str(signing/'leaf.passphrase'))
        clean.update(env or {})
        return subprocess.run([sys.executable, '-c', TEST_RUNNER, str(checkout/'build.py'), '--source', str(checkout), '--output', str(checkout/'dist')],
                              cwd=self.root,env=clean,capture_output=True,text=True)

    def test_build_signs_and_rebuilds_from_repository_layout(self):
        checkout=self.checkout()
        self.configure(checkout)
        result=self.run_checkout(checkout)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('Release signing completed.',result.stdout)
        archive=next((checkout/'dist').rglob('*.tar'))
        first=Path(str(archive)+'.sig').read_text()
        (checkout/'telit/TEST/1.20/1.0/payload/stream.bin').write_bytes(b'changed payload')
        result=self.run_checkout(checkout)
        self.assertEqual(result.returncode,0,result.stderr)
        catalog=json.loads((checkout/'dist/modem-firmware.json').read_text())
        name=catalog['cellular-firmware'][0]['revisions'][0]['firmware'][0]['url'].rsplit('/',1)[-1]
        archive=archive.with_name(name)
        self.assertNotEqual(Path(str(archive)+'.sig').read_text(),first)

    def test_signing_failure_fails_build_without_success_message(self):
        checkout=self.checkout()
        tool,_=self.configure(checkout)
        tool.write_text('raise SystemExit(7)\n')
        result=self.run_checkout(checkout)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Firmware signing failed',result.stderr)
        self.assertNotIn('Build complete:',result.stdout)
        self.assertFalse((checkout/'dist/modem-firmware.json.sig').exists())

    def test_missing_signing_key_fails_before_build(self):
        checkout=self.checkout()
        _,signing=self.configure(checkout)
        (signing/'igos-firmware-leaf.key').unlink()
        result=self.run_checkout(checkout)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Missing signing input: key',result.stderr)
        self.assertFalse((checkout/'dist').exists())

    def test_required_signing_never_falls_back_to_unsigned(self):
        checkout=self.checkout()
        result=self.run_checkout(checkout,env={'FIRMWARE_REQUIRE_SIGNING':'1'})
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Signing is required',result.stderr)
        self.assertFalse((checkout/'dist').exists())



if __name__ == '__main__':
    unittest.main()
