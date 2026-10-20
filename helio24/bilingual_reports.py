"""Publish paired report documents without modifying frozen experiment artifacts."""
from hashlib import sha256
from html import escape, unescape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


def tables(text):
    return re.findall(r'(?:^\|.*\n)+', text, re.M)


def numeric_cells(table):
    """Keep cell positions; allow translated prose to reorder numbers within a cell."""
    return [[sorted(re.findall(r'[-+]?\d+(?:[.,]\d+)*(?:e[+-]?\d+)?', cell))
             for cell in row.split('|')[1:-1]]
            for row in table.splitlines()[2:]]


def validate_catalog(root):
    docs = root / 'docs'
    catalog = json.loads((docs / 'reports.json').read_text())
    ids = set()
    for entry in catalog:
        if entry['id'] in ids or not re.fullmatch(r'[a-z0-9-]+', entry['id']):
            raise ValueError('Invalid or duplicate report ID')
        ids.add(entry['id'])
        if entry['source_language'] not in {'en', 'tr'}:
            raise ValueError('Unsupported source language')
        texts = {}
        for lang in ['en', 'tr']:
            name = entry[lang]
            if Path(name).name != name or not name.endswith('.md'):
                raise ValueError('Report sources must be local Markdown files')
            texts[lang] = (docs / name).read_text()
            if '{{TABLE_' in texts[lang] or '{{REFERENCES}}' in texts[lang]:
                raise ValueError('Unresolved translation placeholder')
        source = docs / entry[entry['source_language']]
        if sha256(source.read_bytes()).hexdigest() != entry['source_sha256']:
            raise ValueError(f"Source changed; review both translations: {entry['id']}")
        left, right = tables(texts['en']), tables(texts['tr'])
        if len(left) != len(right) or any(numeric_cells(a) != numeric_cells(b) for a, b in zip(left, right)):
            raise ValueError(f"Numeric tables differ between languages: {entry['id']}")
    return catalog


def render_markdown(text, resolve_link=lambda url: url):
    """Render the headings, tables, lists, links and code used by report documents."""
    references = dict(re.findall(r'^\[([^]]+)\]:\s+(\S+)\s*$', text, re.M))
    text = re.sub(r'^\[([^]]+)\]:\s+\S+\s*$', '', text, flags=re.M)
    text = re.sub(r'\[([^]]+)\]\[([^]]+)\]',
                  lambda m: '['+m[1]+']('+references[m[2]]+')' if m[2] in references else m[0], text)

    def inline(value):
        # Escape text first; only explicitly supported markup becomes HTML.
        value = escape(value)
        def link(match):
            url = unescape(match[2])
            if urlsplit(url).scheme not in {'', 'http', 'https', 'mailto'}:
                return match[1]
            return '<a href="'+escape(resolve_link(url), quote=True)+'">'+match[1]+'</a>'
        value = re.sub(r'\[([^]]+)\]\(([^)]+)\)', link, value)
        value = re.sub(r'`([^`]+)`', r'<code>\1</code>', value)
        return re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', value)

    lines = text.splitlines()
    output, paragraph = [], []
    def flush():
        if paragraph:
            output.append('<p>'+inline(' '.join(paragraph))+'</p>')
            paragraph.clear()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('```'):
            flush()
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code.append(lines[i])
                i += 1
            output.append('<pre><code>'+escape('\n'.join(code))+'</code></pre>')
        elif line.startswith('|'):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                row = lines[i]
                if not re.fullmatch(r'[\s|:\-]+', row):
                    rows.append([cell.strip() for cell in row.strip('|').split('|')])
                i += 1
            output.append('<div class="table"><table><thead><tr>'+
                          ''.join('<th scope="col">'+inline(c)+'</th>' for c in rows[0])+
                          '</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in r)+'</tr>'
                                                       for r in rows[1:])+'</tbody></table></div>')
            continue
        elif re.match(r'^#{1,6} ', line):
            flush()
            level = len(line)-len(line.lstrip('#'))
            output.append(f'<h{level}>'+inline(line[level+1:])+f'</h{level}>')
        elif line.startswith(('- ', '* ')):
            flush()
            output.append('<ul>')
            while i < len(lines) and lines[i].startswith(('- ', '* ')):
                item = [lines[i][2:]]
                i += 1
                while i < len(lines) and lines[i].startswith('  '):
                    item.append(lines[i].strip())
                    i += 1
                output.append('<li>'+inline(' '.join(item))+'</li>')
            output.append('</ul>')
            continue
        elif not line.strip():
            flush()
        else:
            paragraph.append(line.strip())
        i += 1
    flush()
    return '\n'.join(output)


def publish(root, output):
    catalog = validate_catalog(root)
    output.mkdir(parents=True, exist_ok=False)
    by_file = {entry[lang]: entry['id']+'.'+lang+'.html' for entry in catalog for lang in ['en', 'tr']}

    def resolve(url):
        if urlsplit(url).scheme or url.startswith('#'):
            return url
        path, separator, fragment = url.partition('#')
        if path in by_file:
            return by_file[path]+separator+fragment
        # Preserve links to protocols and other local context in the shared workspace.
        import os
        return Path(os.path.relpath(root / 'docs' / path, output)).as_posix()+separator+fragment

    style = '<style>body{font:16px/1.6 system-ui;margin:32px auto;padding:0 24px;max-width:1200px;color:#172b3a}nav{margin:20px 0}table{border-collapse:collapse;font-size:14px}td,th{padding:8px;border:1px solid #ccd5dd;text-align:left}.table{overflow:auto}pre{white-space:pre-wrap;background:#f3f5f7;padding:16px}a{color:#075e9c}</style>'
    sources, index = {}, []
    for entry in catalog:
        links = ' · '.join(f'<a lang="{lang}" href="{entry["id"]}.{lang}.html">{label}</a>'
                           for lang, label in [('tr', 'Türkçe'), ('en', 'English')])
        index.append('<li>'+escape(entry['id'])+' — '+links+'</li>')
        for lang in ['en', 'tr']:
            source = root / 'docs' / entry[lang]
            text = source.read_text()
            sources[str(source.relative_to(root))] = sha256(source.read_bytes()).hexdigest()
            title = text.splitlines()[0].lstrip('# ')
            page = ('<!doctype html><html lang="'+lang+'"><head><meta charset="utf-8">'
                    '<meta name="viewport" content="width=device-width, initial-scale=1">'
                    '<title>'+escape(title)+'</title>'+style+'</head><body><nav>'
                    '<a href="index.html">Raporlar / Reports</a> · '+links+
                    '</nav><main>'+render_markdown(text, resolve)+'</main></body></html>')
            (output / (entry['id']+'.'+lang+'.html')).write_text(page)
    (output / 'index.html').write_text('<!doctype html><html lang="tr"><meta charset="utf-8">'
                                      '<title>Helio24 — Raporlar / Reports</title>'+style+
                                      '<body><h1>Helio24 — Raporlar / Reports</h1><ul>'+
                                      ''.join(index)+'</ul></body></html>')
    manifest = dict(scope='Bilingual document editions; original experiment artifacts unchanged',
                    sources=sources, catalog_sha256=sha256((root / 'docs/reports.json').read_bytes()).hexdigest(),
                    renderer_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                    artifacts={p.name: sha256(p.read_bytes()).hexdigest() for p in sorted(output.glob('*.html'))})
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest
