"""Restore losslessly compressed experiment files; never replace changed data."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    manifest = json.loads((ROOT/'publication-manifest.json').read_text(encoding='utf-8'))
    restored = 0
    for name, record in manifest['files'].items():
        if record['encoding'] != 'gzip':
            continue
        target = (ROOT/name).resolve()
        assert target.is_relative_to(ROOT), name
        if target.exists():
            assert sha(target) == record['sha256'], f'Refusing to replace modified file: {name}'
            continue
        archive = ROOT/record['storage']
        assert sha(archive) == record['stored_sha256'], record['storage']
        target.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent,delete=False) as out:
                temp_path = Path(out.name)
                with gzip.open(archive,'rb') as src:
                    for chunk in iter(lambda: src.read(1024*1024), b''):
                        out.write(chunk)
            assert temp_path.stat().st_size == record['bytes'] and sha(temp_path) == record['sha256'], name
            os.replace(temp_path,target)
            restored += 1
        finally:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()
    print(f'Restored {restored} files. All archive contents match the preserved SHA-256 hashes.')


if __name__ == '__main__':
    main()
