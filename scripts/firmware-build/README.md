# Modem firmware build tools

Nexus-build orchestrates Docker, source/key checkout, cleanup, and staging.
These tools generate firmware archives/catalogs and perform X.509/CMS signing.
Firmware payloads and metadata live in igos-modem-firmwares.
The container definition lives in `docker/firmware/Dockerfile` in vyos-build.

Run tests from this directory:

```sh
python3 -m unittest discover -s tests -v
```

Build from a separate source checkout (Python 3.11+ and OpenSSL required):

```sh
python3 build.py --source /path/to/igos-modem-firmwares --output /path/to/dist
```

Source defaults to the current directory; output defaults to SOURCE/dist.
Set FIRMWARE_SIGNING_DIR, FIRMWARE_SIGNING_PASSWORD_FILE, and
FIRMWARE_REQUIRE_SIGNING=1 for required signed builds. The signing tool is
resolved beside build.py, independently of the source checkout. ISO signing
and firmware X.509/CMS signing remain separate.
