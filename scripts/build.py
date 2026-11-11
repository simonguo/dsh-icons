"""Generate a dependency-free DSH Client from the pinned vscode-icons theme."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def build():
    theme = json.loads((ROOT / 'vendor/vsicons-icon-theme.json').read_text())
    pin = json.loads((ROOT / 'vendor/upstream.json').read_text())
    used = set()

    def image(key):
        path = theme['iconDefinitions'][key].get('iconPath')
        if not path:
            fallback = {'_file_light': '_file', '_folder_light': '_folder',
                        '_folder_light_open': '_folder_open'}.get(key, '_file')
            path = theme['iconDefinitions'][fallback]['iconPath']
        name = Path(path).name
        assert (ROOT / 'assets' / name).is_file(), name
        used.add(name)
        return 'url("__ASSET__' + name + '__")'

    def row(kind, condition=''):
        # Match ONLY the semantic row, never every descendant button/span.
        return 'li[data-files-entry="' + kind + '"]' + condition

    def names(kind, name):
        return ':is(' + row(kind, '[data-files-path$=' + json.dumps('/' + name) + ' i]') + ',' + row(kind, '[data-files-path=' + json.dumps(name) + ' i]') + ')'

    css = [
        'li[data-files-entry="file"]{' + '--dsh-icons-image:' + image(theme['file']) + '}',
        'li[data-files-entry="directory"]{' + '--dsh-icons-image:' + image(theme['folder']) + ';--dsh-icons-open:' + image(theme['folderExpanded']) + '}',
    ]
    # VS Code supplies language IDs for common extensions (e.g. .ts, .md).
    # DSH has filenames only: bridge those IDs without editing upstream data.
    extensions = {}
    bridge = json.loads((ROOT / 'src/language-extensions.json').read_text())
    for language, suffixes in bridge.items():
        if language in theme['languageIds']:
            for suffix in suffixes:
                extensions[suffix] = theme['languageIds'][language]
    extensions.update(theme['fileExtensions'])
    # :where gives every association equal specificity: later, longer suffixes win.
    for ext, key in sorted(extensions.items(), key=lambda kv: (len(kv[0]), kv[0])):
        css.append(':where(' + row('file', '[data-files-path$=' + json.dumps('.' + ext) + ' i]') + '){--dsh-icons-image:' + image(key) + '}')
    # Default row selectors must not outrank zero-specificity associations.
    css[0] = ':where(li[data-files-entry="file"]){--dsh-icons-image:' + image(theme['file']) + '}'
    css[1] = ':where(li[data-files-entry="directory"]){--dsh-icons-image:' + image(theme['folder']) + ';--dsh-icons-open:' + image(theme['folderExpanded']) + '}'
    for name, key in theme['fileNames'].items():
        css.append(':where(' + names('file', name) + '){--dsh-icons-image:' + image(key) + '}')
    for name, key in theme['folderNames'].items():
        opened = theme['folderNamesExpanded'].get(name, theme['folderExpanded'])
        css.append(':where(' + names('directory', name) + '){--dsh-icons-image:' + image(key) + ';--dsh-icons-open:' + image(opened) + '}')
    # Only TWO structural selectors touch descendants; all associations live on li.
    css.extend([
        'li[data-files-entry][data-files-path]>div>:is(button,span):first-child>svg:first-child{display:none!important}',
        'li[data-files-entry][data-files-path]>div>:is(button,span):first-child::before{content:"";display:block;width:16px;height:16px;flex:0 0 16px;background:var(--dsh-icons-image) center/contain no-repeat;pointer-events:none}',
        'li[data-files-entry="directory"]>div>button[aria-expanded="true"]::before{background-image:var(--dsh-icons-open)}',
    ])
    text = '\n'.join(css)
    # Resolve each unique asset ONCE, not once for each filename association.
    assets = sorted(used)
    indexes = {name: i for i, name in enumerate(assets)}
    expression = []
    last = 0
    for match in re.finditer(r'__ASSET__(.*?)__', text):
        expression.extend([json.dumps(text[last:match.start()]), 'urls[' + str(indexes[match.group(1)]) + ']'])
        last = match.end()
    expression.append(json.dumps(text[last:]))
    template = (ROOT / 'src/client.template.js').read_text()
    result = template.replace('__ASSET_NAMES__', json.dumps(assets)).replace('__CSS__', '+'.join(expression)).replace('__UPSTREAM__', pin['tag'])
    (ROOT / 'client.js').write_text(result)
    stats = dict(upstream=pin['tag'], icons=len(list((ROOT / 'assets').glob('*.svg'))),
                 fileNames=len(theme['fileNames']), fileExtensions=len(theme['fileExtensions']),
                 folderNames=len(theme['folderNames']), referencedAssets=len(used),
                 cssRules=len(css), cssBytes=len(text.encode()), clientBytes=len(result.encode()))
    (ROOT / 'icon-stats.json').write_text(json.dumps(stats, indent=2) + '\n')
    print(json.dumps(stats, indent=2))


if __name__ == '__main__':
    build()
