"""Acquire a portable official Tectonic release without changing the study venv."""
from hashlib import sha256
import io
import json
from pathlib import Path
import requests
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.tools' / 'tectonic'
OUT.mkdir(parents=True, exist_ok=True)
r = requests.get('https://api.github.com/repos/tectonic-typesetting/tectonic/releases/latest', timeout=30)
r.raise_for_status()
j = r.json()
a = next(a for a in j['assets'] if a['name'].endswith('x86_64-pc-windows-msvc.zip'))
r = requests.get(a['browser_download_url'], timeout=90)
r.raise_for_status()
digest = sha256(r.content).hexdigest()
if a.get('digest', '').startswith('sha256:'):
    assert a['digest'] == 'sha256:' + digest
with ZipFile(io.BytesIO(r.content)) as archive:
    for member in archive.infolist():
        path = (OUT / member.filename).resolve()
        assert path.is_relative_to(OUT.resolve())
    archive.extractall(OUT)
(OUT / 'acquisition.json').write_text(json.dumps(dict(tag=j['tag_name'],
    url=a['browser_download_url'], sha256=digest, bytes=len(r.content)), indent=2), encoding='utf-8')
print(json.dumps(dict(release=j['tag_name'], sha256=digest, bytes=len(r.content))))
