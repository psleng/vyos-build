#!/usr/bin/env python3
# Copyright (C) 2026 Perle Systems Limited
# SPDX-License-Identifier: GPL-2.0-or-later
"""Validate firmware releases and build reproducible archives in dist/."""

import argparse
import fcntl
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from contextlib import ExitStack, contextmanager
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urlsplit
from urllib.request import urlopen

import tomllib

def firmware_base_url():
    # Read the tracked flavor directly from GitHub; no local or URL overrides.
    source = ("https://raw.githubusercontent.com/psleng/vyos-build/"
              "psl-master/data/build-flavors/igos-am64x-all.toml")
    with urlopen(source, timeout=30) as response:
        config = tomllib.loads(response.read(1024 * 1024).decode("utf-8"))
    url = config["wwan_firmware_map_url"]
    parsed = urlsplit(url)
    if (parsed.scheme not in ("http", "https") or not parsed.netloc
            or parsed.query or parsed.fragment or parsed.username or parsed.password
            or not parsed.path.endswith("/modem-firmware.json")):
        raise ValueError("wwan_firmware_map_url must be an HTTP(S) modem-firmware.json URL")
    return url.rsplit("/", 1)[0]


FORMAT_VERSION = 2
VERSION_FIELDS = ("telit_version", "telit_package_version", "payload_entry")


MAX_ARCHIVE = 4 * 1024 ** 3
MAX_MEMBERS = 10000


def component(value):
    """Validate an identifier before using it in a filesystem path."""
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*', value):
        raise ValueError(f'Invalid firmware identifier: {value!r}')
    return value


def native_version(value):
    """Accept the opaque revision reported by ModemManager, including build dates."""
    if (not isinstance(value, str) or not value.strip() or len(value) > 512
            or value in ('.', '..') or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise ValueError('Invalid native firmware revision')
    return value


def revision_rank(pattern, revision):
    """Rank a hardware match: exact, longest prefix, then catch-all."""
    if pattern == '*':
        return 0
    if not isinstance(pattern, str) or not re.fullmatch(r'\d+(?:\.\d+)*(?:\.\*)?', pattern):
        raise ValueError(f'Invalid hardware revision pattern: {pattern!r}')
    if pattern.endswith('.*'):
        return len(pattern.split('.')) if revision.startswith(pattern[:-1]) else -1
    return 10000 if pattern == revision else -1


def version_key(version):
    """Compare numeric igOS labels, treating 1.0 and 1.0.0 as equal."""
    if not isinstance(version, str) or not re.fullmatch(r'\d+(?:\.\d+)*', version):
        raise ValueError(f'Invalid igOS version: {version!r}')
    parts = tuple(map(int, version.split('.')))
    while len(parts) > 1 and parts[-1] == 0:
        parts = parts[:-1]
    return parts


def parse_catalog(data):
    """Validate a schema-1 catalog and return its model/revision tracks."""
    if not isinstance(data, dict) or type(data.get('schema')) is not int or data['schema'] != 1:
        raise ValueError('Archive installation requires a schema-1 firmware catalog')
    models = data.get('cellular-firmware')
    if not isinstance(models, list):
        raise TypeError('Missing cellular-firmware list')
    entries, seen = [], set()
    for model in models:
        manufacturer = model['manufacturer']
        if not isinstance(manufacturer, str) or not manufacturer.strip():
            raise ValueError('Missing manufacturer')
        component(model['model'])
        if model['installer'] not in ('uxfp', 'tfl'):
            raise ValueError('Unsupported firmware installer')
        for track in model['revisions']:
            pattern = track['hardware_revision']
            revision_rank(pattern, '0')
            key = (manufacturer, model['model'], pattern)
            if key in seen:
                raise ValueError('Duplicate model/revision block')
            seen.add(key)
            versions, labels, native = {}, set(), set()
            for release in track['firmware']:
                label = release['igos_version']
                order = version_key(label)
                native_version(release['telit_version'])
                if order in labels or release['telit_version'] in native:
                    raise ValueError('Duplicate firmware version in revision track')
                labels.add(order)
                native.add(release['telit_version'])
                url = urlsplit(release['url'])
                if url.scheme not in ('http', 'https') or not url.netloc or url.username or url.password:
                    raise ValueError('Firmware URL must be absolute HTTP(S) without credentials')
                if not re.fullmatch(r'[0-9a-fA-F]{64}', release['archive_sha256']):
                    raise ValueError('archive_sha256 must contain 64 hexadecimal characters')
                versions[label] = release
            if not versions:
                raise ValueError('Empty firmware track')
            entries.append({**model, 'hardware_revision': pattern, 'releases': versions})
    return entries


def safe_path(name):
    """Reject archive paths that could escape the extraction directory."""
    path = PurePosixPath(name)
    if (
        not name
        or path.is_absolute()
        or '..' in path.parts
        or '\\' in name
        or re.match(r'^[A-Za-z]:', name)
        or not path.parts
    ):
        raise ValueError(f'Unsafe archive path: {name!r}')
    return path


def digest(path):
    """Calculate a file hash without loading the firmware into memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def atomic_json(path, data):
    """Write the complete file before replacing the previous version."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=path.parent) as temporary:
        candidate = Path(temporary) / path.name
        with candidate.open("w") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        candidate.chmod(0o644)
        candidate.replace(path)


def add_archive_file(archive, name, stream, size):
    # Fixed permissions and timestamps keep identical builds byte-for-byte equal.
    info = tarfile.TarInfo(name)
    info.size, info.mode, info.mtime = size, 0o644, 0
    info.uid = info.gid = 0
    archive.addfile(info, stream)


def validate_tfl_zip(selected):
    """Check the vendor ZIP before embedding it in a release archive."""
    with zipfile.ZipFile(selected) as archive:
        members = archive.infolist()
        if len(members) > MAX_MEMBERS or sum(m.file_size for m in members) > MAX_ARCHIVE:
            raise ValueError("TFL ZIP exceeds device extraction limits")
        names = set()
        for member in members:
            name = safe_path(member.filename)
            if name in names or stat.S_IFMT(member.external_attr >> 16) not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError("Unsafe/duplicate TFL ZIP entry")
            names.add(name)
        if (
            archive.testzip() is not None
            or len([n for n in archive.namelist() if n.rsplit("/", 1)[-1] == "contents.xml"]) != 1
        ):
            raise ValueError("Invalid TFL ZIP: expected one contents.xml and valid CRCs")


def payloads(directory, installer, entry):
    """Collect safe payload files and check the flashing tool entry point."""
    files = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError(f"Unsafe payload: {path}")
        if path.is_file():
            name = path.relative_to(directory).as_posix()
            safe_path(name)
            if name == "firmware.json" or path.name == ".DS_Store":
                raise ValueError(f"Unexpected payload file: {path}")
            files.append((name, path, digest(path)))
    if not files:
        raise ValueError(f"Missing payload files: {directory}")
    safe_path(entry)
    selected = directory / entry
    if installer == "uxfp" and not selected.is_file():
        raise ValueError("uxfp payload_entry must select a stream file")
    if installer == "tfl":
        if selected.suffix.lower() == ".zip":
            validate_tfl_zip(selected)
        elif selected.name != "contents.xml" or not selected.is_file():
            raise ValueError("tfl payload_entry must select vendor ZIP or contents.xml")
    return files


@contextmanager
def release_payloads(directory, installer, entry):
    """Unpack a source ZIP only when uxfp needs the binary stored inside it."""
    safe_path(entry)
    if installer != "uxfp" or (directory / entry).is_file():
        yield payloads(directory, installer, entry)
        return
    sources = list(directory.glob("*.zip"))
    if len(sources) != 1 or sources[0].is_symlink():
        raise ValueError(f"Expected one source ZIP containing {entry} in {directory}")
    with zipfile.ZipFile(sources[0]) as archive, tempfile.TemporaryDirectory(prefix="firmware-payload-") as temporary:
        members = archive.infolist()
        if len(members) > MAX_MEMBERS:
            raise ValueError("Too many source ZIP entries")
        matches = []
        for member in members:
            path = safe_path(member.filename)
            if (not member.is_dir() and path.name == Path(entry).name
                    and not member.filename.startswith("__MACOSX/")):
                matches.append(member)
        if len(matches) != 1:
            raise ValueError(f"Expected exactly one {entry} in {sources[0]}")
        member = matches[0]
        mode = stat.S_IFMT(member.external_attr >> 16)
        if mode not in (0, stat.S_IFREG) or member.file_size > MAX_ARCHIVE:
            raise ValueError("Unsafe or oversized firmware ZIP entry")
        target = Path(temporary) / entry
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(member) as incoming, target.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing, 1024 * 1024)
        yield [(entry, target, digest(target))]


def create_archive(target, manifest_bytes, files):
    """Write to a temporary tar, verify its contents, then replace the output."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temporary:
        candidate = Path(temporary) / "release.tar"
        with tarfile.open(candidate, "w", format=tarfile.USTAR_FORMAT) as archive:
            add_archive_file(archive, "firmware.json", io.BytesIO(manifest_bytes), len(manifest_bytes))
            for name, path, _ in files:
                with path.open("rb") as stream:
                    add_archive_file(archive, name, stream, path.stat().st_size)
        # Verify the archived bytes, which also detects payload changes during the build.
        with tarfile.open(candidate, "r:") as archive:
            if archive.extractfile("firmware.json").read() != manifest_bytes:
                raise ValueError("Manifest round-trip failed")
            for name, _, expected in files:
                if hashlib.file_digest(archive.extractfile(name), "sha256").hexdigest() != expected:
                    raise ValueError("Payload round-trip failed")
        checksum = digest(candidate)
        candidate.replace(target)
    return checksum


def add_catalog_release(models, manifest, relative, checksum, base_url):
    """Group a release under its model and hardware revision in the catalog."""
    manufacturer = manifest["manufacturer"]
    model = manifest["model"]
    installer = manifest["installer"]
    revision = manifest["hardware_revision"]
    release = {
        key: value
        for key, value in manifest.items()
        if key not in ("manufacturer", "model", "hardware_revision", "installer")
    }
    release.update(url=base_url.rstrip("/") + "/" + quote(relative.as_posix(), safe="/"), archive_sha256=checksum)
    model_key = (manufacturer, model)
    entry = models.setdefault(
        model_key, {"manufacturer": manufacturer, "model": model, "installer": installer, "revisions": []}
    )
    if entry["installer"] != installer:
        raise ValueError("Conflicting installers for model")
    block = next((b for b in entry["revisions"] if b["hardware_revision"] == revision), None)
    if block is None:
        block = {"hardware_revision": revision, "firmware": []}
        entry["revisions"].append(block)
    block["firmware"].append(release)


def signing_config(root):
    """Use the local signing tool and fetched key repository."""
    directory = os.environ.get('FIRMWARE_SIGNING_DIR')
    if not directory:
        if os.environ.get('FIRMWARE_REQUIRE_SIGNING', '').lower() in ('1', 'true', 'yes'):
            raise ValueError('Signing is required but FIRMWARE_SIGNING_DIR is missing')
        return None
    directory = Path(directory)
    result = {
        'tool': root/'wwan-firmware-sign',
        'key': directory/'igos-firmware-leaf.key',
        'cert': directory/'igos-firmware-leaf.pem',
        'crl': directory/'igos-firmware-root-ca.crl',
        'password_file': Path(os.environ.get('FIRMWARE_SIGNING_PASSWORD_FILE',
                                           '/run/leaf.passphrase')),
    }
    for name, path in result.items():
        if not path.is_file():
            raise ValueError(f'Missing signing input: {name}')
    return result


def sign_release(output, base_url, config):
    command = [sys.executable, str(config['tool']), 'release',
               '--catalog', str(output/'modem-firmware.json'),
               '--archive-root', str(output), '--base-url', base_url]
    for name in ('key', 'cert', 'crl', 'password_file'):
        if name in config:
            command.extend(['--'+name.replace('_', '-'), str(config[name])])
    # Hold the generator lock until signing completes. A failure
    # is a failed build; the transfer job must never publish failed output.
    result = subprocess.run(command, check=False)
    if result.returncode:
        raise ValueError(f'Firmware signing failed (exit {result.returncode}); do not publish this build')


def build(source, output, base_url, signing=None):
    """Build changed releases and regenerate the catalog from source metadata."""
    base = urlsplit(base_url)
    if (
        base.scheme not in ("http", "https")
        or not base.netloc
        or base.query
        or base.fragment
        or base.username
        or base.password
    ):
        raise ValueError("base-url must be an absolute HTTP(S) directory URL")
    output.mkdir(parents=True, exist_ok=True)
    # Serialize generators sharing a persistent CI workspace.
    with (output / ".build.lock").open("a") as lock, ExitStack() as workspace:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state_path = output / ".build-state.json"
        state = json.loads(state_path.read_text()) if state_path.exists() else {}
        build_datetime = datetime.now().strftime("%Y%m%d%H%M%S") + "00"
        new_state = {}
        models = {}
        counts = {"built": 0, "reused": 0}
        targets = set()
        metadata_files = sorted(source.glob("*/*/*/*/meta.toml"))
        if not metadata_files:
            raise ValueError("No vendor/model/revision/igos_version/meta.toml releases found")
        for metadata in metadata_files:
            if metadata.is_symlink():
                raise ValueError("Symlink metadata is not allowed")
            vendor, model, track, label = metadata.parent.relative_to(source).parts
            for value in (vendor, model, label):
                component(value)
            version_key(label)
            meta = tomllib.loads(metadata.read_text())
            installer = meta["installer"]
            if installer not in ("uxfp", "tfl"):
                raise ValueError("Unsupported installer")
            native_version(meta["telit_version"])
            version_directory = component(meta["telit_version"])
            component(meta["telit_package_version"])
            manufacturer = meta["manufacturer"]
            payload_directory = metadata.parent / "payload"
            if payload_directory.is_symlink():
                raise ValueError("Symlink payload directory is not allowed")
            files = workspace.enter_context(release_payloads(payload_directory, installer, meta["payload_entry"]))
            revisions = meta.get("revisions", [track])
            if not isinstance(revisions, list) or not revisions or len(set(revisions)) != len(revisions):
                raise ValueError("revisions must be a nonempty unique list")
            for revision in revisions:
                revision_rank(revision, "0")
                slug = revision.replace("*", "all")
                manifest = {
                    "manufacturer": manufacturer,
                    "model": model,
                    "hardware_revision": revision,
                    "igos_version": label,
                    "installer": installer,
                    **{key: meta[key] for key in VERSION_FIELDS},
                }
                if meta.get("release_date"):
                    manifest["release_date"] = meta["release_date"]
                serialized = (json.dumps(manifest, indent=2) + "\n").encode()
                fingerprint = hashlib.sha256(
                    json.dumps(
                        [FORMAT_VERSION, manifest, meta, [(name, checksum) for name, _, checksum in files]],
                        sort_keys=True,
                    ).encode()
                ).hexdigest()
                relative = (
                    Path(vendor)
                    / model
                    / slug
                    / version_directory
                    / f"{model}-{slug}-{version_directory}.tar"
                )
                key = relative.as_posix()
                if key in targets:
                    raise ValueError(f"Multiple releases target the same archive: {key}")
                targets.add(key)
                previous = state.get(key, {})
                stem = relative.stem
                previous_name = previous.get("archive_name", "")
                reusable_name = isinstance(previous_name, str) and re.fullmatch(
                    re.escape(stem) + r"-\d{14}00\.tar", previous_name
                )
                archive_name = previous_name if reusable_name else f"{stem}-{build_datetime}.tar"
                relative = relative.with_name(archive_name)
                target = output / relative
                if (
                    reusable_name
                    and previous.get("fingerprint") == fingerprint
                    and target.is_file()
                    and digest(target) == previous.get("archive_sha256")
                ):
                    checksum = previous["archive_sha256"]
                    counts["reused"] += 1
                else:
                    relative = relative.with_name(f"{stem}-{build_datetime}.tar")
                    target = output / relative
                    checksum = create_archive(target, serialized, files)
                    counts["built"] += 1
                new_state[key] = {"fingerprint": fingerprint, "archive_sha256": checksum,
                                  "archive_name": relative.name}
                add_catalog_release(models, manifest, relative, checksum, base_url)
        document = {"schema": 1, "cellular-firmware": list(models.values())}
        # An invalid release must never replace the last usable catalog.
        parse_catalog(document)
        atomic_json(state_path, new_state)
        atomic_json(output / "modem-firmware.json", document)
        if signing is not None:
            sign_release(output, base_url, signing)
        print(f"Build complete: {counts['built']} archives created, {counts['reused']} reused.")
        print('Release signing completed.' if signing is not None else 'Unsigned build: no signing configuration supplied.')
        return counts


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path.cwd(), help="Firmware payload and metadata checkout")
    parser.add_argument("--output", type=Path, help="Artifact output directory (default: SOURCE/dist)")
    args = parser.parse_args()
    try:
        signing = signing_config(root)
        build(args.source.resolve(), (args.output or args.source / "dist").resolve(), firmware_base_url(), signing=signing)
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError, zipfile.BadZipFile) as error:
        sys.exit(f"Build failed: {error}")


if __name__ == "__main__":
    main()
