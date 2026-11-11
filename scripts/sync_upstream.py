"""Sync the complete icon set and generated mappings from an official VSIX release.

Only Python's standard library is used. No upstream extension code is executed.
Use --tag v13.0.0 to reproduce a release, or omit it to resolve latest.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = 'vscode-icons/vscode-icons'
MAX_DOWNLOAD = 32 * 1024 * 1024


def download(url):
    headers = {'User-Agent': 'dsh-icons-upstream-sync', 'Accept': 'application/vnd.github+json'}
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token and url.startswith('https://api.github.com/'):
        headers['Authorization'] = 'Bearer ' + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=90) as response:
        data = response.read(MAX_DOWNLOAD + 1)
    if len(data) > MAX_DOWNLOAD:
        raise ValueError('Upstream download exceeds 32 MiB')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', help='Official release tag; default: latest')
    args = parser.parse_args()
    endpoint = 'tags/' + args.tag if args.tag else 'latest'
    release = json.loads(download('https://api.github.com/repos/' + REPO + '/releases/' + endpoint))
    tag = release['tag_name']
    if not re.fullmatch(r'v?\d+\.\d+\.\d+(?:[-.][\w.-]+)?', tag):
        raise ValueError('Unexpected release tag')
    asset = next(a for a in release['assets'] if a['name'].endswith('.vsix'))
    url = asset['browser_download_url']
    if not url.startswith('https://github.com/' + REPO + '/releases/download/'):
        raise ValueError('Unexpected release asset URL')
    data = download(url)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if sum(info.file_size for info in archive.infolist()) > 128 * 1024 * 1024:
            raise ValueError('Unpacked release exceeds 128 MiB')
        theme = archive.read('extension/dist/src/vsicons-icon-theme.json')
        json.loads(theme)  # fail before touching the checkout on a malformed manifest
        license_text = archive.read('extension/LICENSE.txt')
        icons = {}
        for name in archive.namelist():
            if not name.startswith('extension/icons/') or not name.endswith('.svg'):
                continue
            basename = name.removeprefix('extension/icons/')
            if '/' in basename or not re.fullmatch(r'[\w.-]+\.svg', basename):
                raise ValueError('Unexpected icon path: ' + name)
            icons[basename] = archive.read(name)
    if not icons:
        raise ValueError('Release contains no SVG icons')
    asset_dir = ROOT / 'assets'
    asset_dir.mkdir(exist_ok=True)
    # Only delete stale SVGs directly under this verified, fixed project asset folder.
    assert asset_dir.resolve() == ROOT.resolve() / 'assets'
    for file in asset_dir.glob('*.svg'):
        if file.name not in icons:
            file.unlink()
    for name, content in icons.items():
        (asset_dir / name).write_bytes(content)
    vendor = ROOT / 'vendor'
    vendor.mkdir(exist_ok=True)
    (vendor / 'vsicons-icon-theme.json').write_bytes(theme)
    (vendor / 'LICENSE.vscode-icons.txt').write_bytes(license_text)
    (vendor / 'upstream.json').write_text(json.dumps({
        'repository': 'https://github.com/' + REPO,
        'tag': tag,
        'release': release['html_url'],
        'asset': url,
        'sha256': hashlib.sha256(data).hexdigest(),
    }, indent=2) + '\n')
    print('Synced', len(icons), 'icons from', tag)


if __name__ == '__main__':
    main()
