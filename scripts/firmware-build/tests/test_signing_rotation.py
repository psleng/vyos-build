"""Exercise signature preservation using real OpenSSL CMS signatures."""
import hashlib
import json
import sys
from unittest.mock import patch

import importlib.machinery
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('firmware_signer', str(ROOT/'wwan-firmware-sign'))
spec = importlib.util.spec_from_loader(loader.name, loader)
signer = importlib.util.module_from_spec(spec)
loader.exec_module(signer)


class TestSigningRotation(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.archive = self.root/'firmware.tar'
        self.archive.write_bytes(b'original firmware')
        self.crl = self.root/'current.crl'
        self.crl.write_bytes(b'old revocation data')
        self.old = self.identity('old')
        self.new = self.identity('new')
        signer.sign(self.archive, self.old, b'')

    def identity(self, name):
        key, cert = self.root/(name+'.key'), self.root/(name+'.pem')
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
            '-keyout', str(key), '-out', str(cert), '-days', '1',
            '-subj', '/CN='+name,
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return SimpleNamespace(key=key, cert=cert, crl=self.crl)

    def sidecar(self, suffix):
        return Path(str(self.archive)+suffix)

    def test_rotation_preserves_signature_and_certificate_refreshes_crl(self):
        before = {suffix: self.sidecar(suffix).read_bytes() for suffix in ('.sig', '.pem')}
        self.crl.write_bytes(b'new revocation data')
        self.assertTrue(signer.preserve_archive_signature(self.archive, self.new))
        for suffix, data in before.items():
            self.assertEqual(self.sidecar(suffix).read_bytes(), data)
        self.assertEqual(self.sidecar('.crl').read_bytes(), b'new revocation data')

    def test_changed_archive_requires_fresh_signature(self):
        self.archive.write_bytes(b'changed firmware')
        self.assertFalse(signer.preserve_archive_signature(self.archive, self.new))
        signer.sign(self.archive, self.new, b'')
        self.assertEqual(self.sidecar('.pem').read_bytes(), self.new.cert.read_bytes())
        self.assertTrue(signer.preserve_archive_signature(self.archive, self.new))

    def test_wrong_saved_certificate_cannot_preserve_signature(self):
        self.sidecar('.pem').write_bytes(self.new.cert.read_bytes())
        self.assertFalse(signer.preserve_archive_signature(self.archive, self.new))

    def test_missing_or_corrupt_signature_requires_signing(self):
        self.sidecar('.sig').write_bytes(b'corrupt')
        self.assertFalse(signer.preserve_archive_signature(self.archive, self.new))
        self.sidecar('.sig').unlink()
        self.assertFalse(signer.preserve_archive_signature(self.archive, self.new))

    def test_release_rotation_signs_only_catalog(self):
        catalog = self.root/'modem-firmware.json'
        catalog.write_text(json.dumps({
            'schema': 1, 'cellular-firmware': [{'revisions': [{'firmware': [{
                'url': 'https://fw.test/firmware.tar',
                'archive_sha256': hashlib.sha256(self.archive.read_bytes()).hexdigest(),
            }]}]}],
        }))
        argv = ['wwan-firmware-sign', 'release', '--catalog', str(catalog),
                '--archive-root', str(self.root), '--base-url', 'https://fw.test',
                '--key', str(self.new.key), '--cert', str(self.new.cert),
                '--crl', str(self.crl)]
        before = self.sidecar('.sig').read_bytes()
        with patch.object(sys, 'argv', argv), patch.object(signer, 'sign', wraps=signer.sign) as sign:
            self.assertEqual(signer.main(), 0)
        self.assertEqual([call.args[0] for call in sign.call_args_list], [catalog])
        self.assertEqual(self.sidecar('.sig').read_bytes(), before)
        self.assertEqual(Path(str(catalog)+'.pem').read_bytes(), self.new.cert.read_bytes())
