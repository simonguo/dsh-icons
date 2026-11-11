"""Validate redistributable resources and generated theme contracts."""
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build import build

before = (ROOT / 'client.js').read_bytes()
build()
assert before == (ROOT / 'client.js').read_bytes(), 'client.js is stale; run scripts/build.py'
package = json.loads((ROOT / 'package.json').read_text())
assert package['name'] == 'dsh-icons'
assert package['exports']['./assets/*'] == './assets/*'
for file in (ROOT / 'assets').glob('*.svg'):
    root = ET.parse(file).getroot()
    assert root.tag.endswith('svg'), file
manifest = json.loads((ROOT / 'vendor/vsicons-icon-theme.json').read_text())
for key, definition in manifest['iconDefinitions'].items():
    if definition.get('iconPath'):
        assert (ROOT / 'assets' / Path(definition['iconPath']).name).exists(), key
# Critical precedence and folder-open coverage in the pinned upstream manifest.
for name in ('package.json', '.gitignore'):
    assert name in manifest['fileNames']
assert manifest['languageIds']['typescript']
assert 'ts' in json.loads((ROOT / 'src/language-extensions.json').read_text())['typescript']
assert 'src' in manifest['folderNamesExpanded']
assert (ROOT / 'vendor/LICENSE.vscode-icons.txt').stat().st_size > 500
assert (ROOT / 'LICENSE').is_file()
print('Resource, mapping, license and reproducibility checks passed.')
