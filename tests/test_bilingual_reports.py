import json
from pathlib import Path
import shutil

import pytest
from helio24.bilingual_reports import publish, render_markdown, validate_catalog

ROOT = Path(__file__).resolve().parents[1]


def test_every_result_report_has_both_languages_and_identical_numeric_tables():
    catalog = validate_catalog(ROOT)
    registered = {entry[lang] for entry in catalog for lang in ['en', 'tr']}
    context = {'data-contract.md', 'next-evaluation-plan.md', 'reports.md'}
    reports = {p.name for p in (ROOT / 'docs').glob('*.md')
               if not p.name.endswith('-protocol.md') and p.name not in context}
    assert reports == registered


def test_translation_drift_blocks_publication(tmp_path):
    shutil.copytree(ROOT / 'docs', tmp_path / 'docs')
    path = tmp_path / 'docs/first-experiment.tr.md'
    path.write_text(path.read_text().replace('528', '529'))
    with pytest.raises(ValueError, match='Numeric tables differ'):
        validate_catalog(tmp_path)
    shutil.copy(ROOT / 'docs/first-experiment.tr.md', path)
    source = tmp_path / 'docs/first-experiment.md'
    source.write_text(source.read_text()+'\nNew finding.\n')
    with pytest.raises(ValueError, match='Source changed'):
        validate_catalog(tmp_path)


def test_publish_keeps_sources_and_has_language_navigation(tmp_path):
    before = {p: p.read_bytes() for p in (ROOT / 'docs').glob('*') if p.is_file()}
    output = tmp_path / 'editions'
    manifest = publish(ROOT, output)
    assert len(manifest['artifacts']) == 21
    for entry in validate_catalog(ROOT):
        for lang in ['tr', 'en']:
            page = (output / f'{entry["id"]}.{lang}.html').read_text()
            assert f'<html lang="{lang}">' in page
            assert f'{entry["id"]}.en.html' in page
            assert f'{entry["id"]}.tr.html' in page
            assert '{{TABLE_' not in page
    assert before == {p: p.read_bytes() for p in before}
    assert json.loads((output / 'manifest.json').read_text()) == manifest
    with pytest.raises(FileExistsError):
        publish(ROOT, output)


def test_rendering_preserves_unicode_tables_links_and_escapes_html():
    text = '# Ölçüm\n\n**Sonuç** [kaynak](https://example.org/?a=1&b=2)\n\n| A | B |\n| --- | --- |\n| %95 | 1,076 |\n\n<script>alert(1)</script>\n\n[bad](javascript:alert)\n\n```sh\npython example.py\n```\n'
    page = render_markdown(text)
    assert '<h1>Ölçüm</h1>' in page
    assert '<td>%95</td><td>1,076</td>' in page
    assert 'href="https://example.org/?a=1&amp;b=2"' in page
    assert '<script>' not in page and 'href="javascript:' not in page
    assert '<pre><code>python example.py</code></pre>' in page
