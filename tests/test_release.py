"""Integrity of the installed release and its inherited scientific source."""
from pathlib import Path
from importlib.metadata import version
import hashlib
import json
import tomllib

from h2pipebench import __version__ as SOLVER_VERSION
from h2web import __version__ as WEB_VERSION

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / 'vendor/h2pipebench'


def test_installed_release_versions_agree():
    metadata = tomllib.loads((VENDOR / 'pyproject.toml').read_text())
    source = json.loads((VENDOR / 'SOURCE_HASHES.json').read_text())
    manifest = json.loads((ROOT / 'RELEASE_MANIFEST.json').read_text())
    assert SOLVER_VERSION == WEB_VERSION == version('h2pipebench') == metadata['project']['version'] == source['version'] == '0.1.0'
    assert manifest['release'] == 'H2PipeBench 0.1.0'


def test_scientific_source_inherited_except_version_string():
    provenance = json.loads((VENDOR / 'SOURCE_HASHES.json').read_text())
    for relative, digest in provenance['inherited_sha256'].items():
        data = (VENDOR / relative).read_bytes()
        if relative == 'src/h2pipebench/__init__.py':
            assert data.count(b'__version__ = "0.1.0"') == 1
            data = data.replace(b'__version__ = "0.1.0"', b'__version__ = "0.1.0rc1"')
        assert hashlib.sha256(data).hexdigest() == digest, relative
