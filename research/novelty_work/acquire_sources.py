"""Snapshot the primary sources used in the scoped novelty review.

Uses the host Python's requests/pypdf only for research-document acquisition.
It does not change the experiment environment or any scientific result.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from html.parser import HTMLParser
import argparse
import json
from pathlib import Path
import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs' / 'novelty_audit_v1'
SOURCES = [
    ('kirkland2018', 'https://server.math.umanitoba.ca/~kirkland/actor_event_paper_revised.pdf'),
    ('dasgupta2004', 'https://cseweb.ucsd.edu/~dasgupta/papers/greedy.pdf'),
    ('flt2003', 'https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-2003-21.pdf'),
    ('llm2019v2', 'https://arxiv.org/html/1906.11385v2'),
    ('chen2021v1', 'https://arxiv.org/html/2106.10386v1'),
    ('chakrabarty2026', 'https://drops.dagstuhl.de/storage/00lipics/lipics-vol388-esa2026/html/LIPIcs.ESA.2026.150/LIPIcs.ESA.2026.150.html'),
    ('aksoy2026v1', 'https://arxiv.org/html/2610.17581v1'),
    ('zhangcao2026v1', 'https://arxiv.org/html/2605.21920v1'),
    ('grannell2016', 'https://ajc.maths.uq.edu.au/pdf/66/ajc_v66_p130.pdf'),
    ('friedman2004', 'https://arxiv.org/abs/cs/0405020'),
    ('szyfelbein2026_versions', 'https://arxiv.org/abs/2604.12036'),
    ('bruno2025_versions', 'https://arxiv.org/abs/2501.11129'),
    ('hiddenedge2022', 'https://arxiv.org/abs/2207.02344'),
    ('kirkland2018_metadata', 'https://doi.org/10.1093/comnet/cnx039'),
    ('hwangseok2026v1', 'https://arxiv.org/html/2610.07771v1'),
    ('hwangseok2026_versions', 'https://arxiv.org/abs/2610.07771'),
    ('pandora2021_versions', 'https://arxiv.org/abs/2108.12976'),
    ('pandora2021v2', 'https://arxiv.org/html/2108.12976v2'),
    ('pandora2023v4', 'https://arxiv.org/html/2108.12976v4'),
    ('zhangcao2026_versions', 'https://arxiv.org/abs/2605.21920'),
    ('llm2019_versions', 'https://arxiv.org/abs/1906.11385'),
    ('aksoy2026_versions', 'https://arxiv.org/abs/2610.17581'),
]


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        if tag in ('p', 'div', 'section', 'li', 'h1', 'h2', 'h3', 'h4', 'tr'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def acquire(item):
    key, url = item
    record = dict(id=key, requested_url=url,
                  checked_at=datetime.now(timezone(timedelta(hours=9))).isoformat())
    try:
        r = requests.get(url, timeout=(15, 45), headers={'User-Agent': 'Research source verification'})
        record.update(status_code=r.status_code, final_url=r.url,
                      content_type=r.headers.get('content-type', ''))
        if r.status_code != 200:
            record['status'] = 'unavailable'
            return record
        pdf = r.content.startswith(b'%PDF')
        path = OUT / 'sources' / (key + ('.pdf' if pdf else '.html'))
        path.write_bytes(r.content)
        record.update(status='downloaded', path=str(path.relative_to(ROOT)),
                      bytes=len(r.content), sha256=sha256(r.content).hexdigest())
        if pdf:
            reader = PdfReader(path)
            extracted = '\n\n'.join(f'--- PDF PAGE {i+1} ---\n{p.extract_text()}'
                                     for i, p in enumerate(reader.pages))
            record['pages'] = len(reader.pages)
        else:
            parser = Text()
            parser.feed(r.text)
            extracted = ''.join(parser.parts)
        txt = path.with_suffix('.txt')
        txt.write_text(extracted, encoding='utf-8')
        record.update(text_path=str(txt.relative_to(ROOT)),
                      text_sha256=sha256(txt.read_bytes()).hexdigest())
    except Exception as exc:
        record.update(status='error', error=f'{type(exc).__name__}: {exc}')
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--append', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(exist_ok=args.append)
    (OUT / 'sources').mkdir(exist_ok=args.append)
    manifest = OUT / 'source_manifest.json'
    existing = json.loads(manifest.read_text(encoding='utf-8')) if args.append and manifest.exists() else []
    known = {r['id'] for r in existing}
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(acquire, (s for s in SOURCES if s[0] not in known)))
    manifest.write_text(json.dumps(existing + records, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps([dict(id=r['id'], status=r['status'], pages=r.get('pages')) for r in records]))


if __name__ == '__main__':
    main()
