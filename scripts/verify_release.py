"""Check public research bytes, gzip contents, frozen manifests, and README links."""
import gzip
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def digest(path, compressed=False):
    h = hashlib.sha256()
    opener = gzip.open if compressed else open
    with opener(path,'rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    manifest = json.loads((ROOT/'publication-manifest.json').read_text(encoding='utf-8'))
    for name, record in manifest['files'].items():
        path = ROOT/record['storage']
        assert path.is_file(), record['storage']
        assert digest(path) == record['stored_sha256'], record['storage']
        assert digest(path, record['encoding']=='gzip') == record['sha256'], name
        restored = ROOT/name
        if restored.exists():
            assert digest(restored) == record['sha256'], name
    checked = missing = 0
    manifests = [('runs/main/ARTIFACT_MANIFEST.json','runs/main/'),
                 ('EXTREMAL_ARTIFACT_MANIFEST.json',''),('FOLLOWUP_ARTIFACT_MANIFEST.json',''),
                 ('FINAL_RESEARCH_ARTIFACT_MANIFEST.json',''),('NOVELTY_ARTIFACT_MANIFEST.json',''),
                 ('PAPER_ARTIFACT_MANIFEST.json','')]
    for filename, base in manifests:
        frozen = json.loads((ROOT/'research'/filename).read_text(encoding='utf-8'))
        for name, expected in frozen['files'].items():
            key = 'research/'+base+name.replace('\\','/')
            if key in manifest['files']:
                assert manifest['files'][key]['sha256'] == expected, key
                checked += 1
            else:
                assert key in manifest['omitted'], key
                assert manifest['omitted'][key]['sha256'] == expected, key
                missing += 1
    broken = []
    for file in [ROOT/'README.md', *sorted((ROOT/'docs').glob('*.md'))]:
        for target in re.findall(r'!?\[[^\]]*\]\(([^)\s]+)\)',file.read_text(encoding='utf-8')):
            if target.startswith(('http://','https://','#','mailto:')):
                continue
            clean = target.split('#')[0]
            if clean and not (file.parent/clean).exists():
                broken.append(f'{file.relative_to(ROOT)} -> {target}')
    assert not broken, broken
    result = dict(passed=True,research_files=len(manifest['files']),
                  archived_manifest_entries_verified=checked,
                  declared_external_or_local_receipts_omitted=missing,
                  compressed_files=sum(r['encoding']=='gzip' for r in manifest['files'].values()),
                  broken_readme_links=0)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
