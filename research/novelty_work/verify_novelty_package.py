"""Check editorial provenance, exact claim constants, and preserved research.

This is an evidence/integrity check, not a mechanical certification of novelty
or a formal verification of an infinite mathematical theorem.
"""
import argparse
from datetime import datetime, timezone, timedelta
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'runs/novelty_audit_v1'
MANIFEST = ROOT / 'NOVELTY_ARTIFACT_MANIFEST.json'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def extract(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0].strip()


def check():
    prior = []
    for filename, base in [('runs/main/ARTIFACT_MANIFEST.json', ROOT/'runs/main'),
                           ('EXTREMAL_ARTIFACT_MANIFEST.json', ROOT),
                           ('FOLLOWUP_ARTIFACT_MANIFEST.json', ROOT),
                           ('FINAL_RESEARCH_ARTIFACT_MANIFEST.json', ROOT)]:
        manifest = read(ROOT / filename)
        for name, expected in manifest['files'].items():
            path = base / name
            assert path.is_file(), path
            assert digest(path) == expected, path
        prior.append(dict(manifest=filename, files_checked=len(manifest['files']), passed=True))
    final = read(ROOT/'FINAL_RESEARCH_ARTIFACT_MANIFEST.json')
    assert digest(ROOT/'FINAL_RESEARCH_STATUS.json') == final['status_sha256']
    assert digest(ROOT/'Twenty_Questions_Hubfree_Final_Review.md') == final['note_sha256']
    assert digest(ROOT/'archive/README_hubfree_final_v1.md') == final['current_readme_sha256']
    old = (ROOT/'archive/Twenty_Questions_Paper_Draft_v0.2.md').read_text(encoding='utf-8')
    new = (ROOT/'Twenty_Questions_Paper_Draft.md').read_text(encoding='utf-8')
    assert extract(old, '### 8.1 ', '### 8.4 ') == extract(new, '### 8.1 ', '### 8.4 ')
    assert extract(old, '### 5.1 ', '## 6 ') == extract(new, '### 5.1 ', '### 5.5 ')
    reproduced = OUT / 'paper_reproduced.md'
    assert reproduced.is_file() and digest(reproduced) == digest(ROOT/'Twenty_Questions_Paper_Draft.md')
    refs = re.findall(r'^\[(\d+)\] ', new, flags=re.M)
    assert list(map(int, refs)) == list(range(1,22)), refs
    missing = []
    for target in re.findall(r'\]\(([^)\s]+)\)', new):
        if target.startswith(('https:', 'http:', '#')):
            continue
        if not (ROOT/target.split('#')[0]).exists():
            missing.append(target)
    assert not missing, missing
    assert '균등' in new and 'N/578' in new and '71/70' in new and '73/70' in new
    assert '-0.000485' in new and '-0.001144' in new and '0.000116' in new
    assert 'O(1)' in new and '모든 가능한 환원을 배제한 것은 아니다' in new
    log = read(OUT/'search_log.json')
    assert sum(len(b['queries']) for b in log['batches']) == 50
    assert len(log['batches']) == 13
    receipts = list((OUT/'web_receipts').glob('*.json'))
    assert len(receipts) == 24
    for path in receipts:
        r = read(path)
        if r.get('status') == 'fulfilled':
            r = r['value']
        assert not r.get('isError'), path
        assert r.get('content'), path
    sources = read(OUT/'source_manifest.json')
    downloaded = [r for r in sources if r['status'] == 'downloaded']
    assert len(sources) == 22 and len(downloaded) == 21
    for r in downloaded:
        assert digest(ROOT/r['path']) == r['sha256']
        assert digest(ROOT/r['text_path']) == r['text_sha256']
    # Derive the theorem's leading constants from the exact saved profiles.
    decorated = read(ROOT/'final_work/hubfree_agent_proven_results/decorated_certificates.json')['3']
    coefficients = {}
    for world, expected_D, expected_slope in [('a', Fraction(71,2), Fraction(71,68)),
                                             ('b', Fraction(73,2), Fraction(73,68))]:
        certificate = decorated['worlds'][world]['certificate']
        profiles = certificate['profiles']
        ps = [Fraction(p['probability_exact']) for p in profiles]
        means = [sum(p*sum(g >= s for g in prof['gains']) for p, prof in zip(ps,profiles))
                 for s in range(1,11)]
        D = sum(z*z for z in means)
        assert D == expected_D == Fraction(certificate['D_exact'])
        assert D/34 == expected_slope == Fraction(certificate['virtual_cover_slope_exact'])
        coefficients[world] = expected_slope
    assert coefficients['b']-coefficients['a'] == Fraction(1,34)
    assert (coefficients['b']-coefficients['a'])/17 == Fraction(1,578)
    assert coefficients['a']/Fraction(35,34) == Fraction(71,70)
    assert coefficients['b']/Fraction(35,34) == Fraction(73,70)
    assert 2*Fraction(1,20)/(25*(7+2*Fraction(1,20))) == Fraction(1,1775)
    assert Fraction(100-69,34)-Fraction(235,1700) == Fraction(263,340)
    finite = read(ROOT/'runs/hubfree_search_v1/best.json')
    assert finite['summary']['contrast_exact'] == '13/76'
    assert finite['summary']['robust_exact'] == '3/19'
    reduced = read(OUT/'natural_reduction_checks.json')
    assert len(reduced['checks']) == 3
    assert all(r['target_indicator_tables_identical'] and not r['onehot_gram_equal'] for r in reduced['checks'])
    assert [(r['mismatch']['fast'],r['mismatch']['slow']) for r in reduced['checks']] == [(4,6),(8,14),(16,30)]
    assert reduced['bare_pasch']['a'] == reduced['bare_pasch']['b'] == dict(optimal_mean='2',greedy_mean='2')
    assert reduced['chen_k4']['cut_profile_equal'] and not reduced['chen_k4']['gram_equal']
    assert reduced['script_sha256'] == digest(ROOT/'novelty_work/check_prior_reductions.py')
    status = read(ROOT/'NOVELTY_STATUS.json')
    assert status['status'] == 'completed_with_scoped_claim' and not status['priority_certified']
    assert not status['all_possible_reductions_ruled_out'] and not status['ml_improvement_claim']
    return dict(passed=True, prior_manifests=prior, prior_listed_files_checked=sum(r['files_checked'] for r in prior),
        paper_measured_sections_preserved=True, original_finite_witness_section_preserved=True,
        deterministic_editorial_reproduction=True, bibliography_entries=len(refs),
        local_paper_links_valid=True, web_receipts=len(receipts), sources_downloaded=len(downloaded),
        source_hashes_valid=True, theorem_leading_constants_consistent=True,
        preserved_finite_costs_consistent=True, natural_reduction_checks_consistent=True,
        priority_certification=False, infinite_formal_proof_certification=False,
        python=sys.version.split()[0])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true')
    args = parser.parse_args()
    result = check()
    if args.freeze:
        assert not MANIFEST.exists(), 'Use a new audit version instead of overwriting a frozen package'
        (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        paths = [p for p in OUT.rglob('*') if p.is_file()]
        paths += [p for p in (ROOT/'novelty_work').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
        paths += [ROOT/'reports/novelty/NOVELTY_DECISION.md', ROOT/'NOVELTY_STATUS.json',
                  ROOT/'Twenty_Questions_Paper_Draft.md', ROOT/'README.md',
                  ROOT/'archive/Twenty_Questions_Paper_Draft_v0.2.md',
                  ROOT/'archive/README_hubfree_final_v1.md']
        manifest = dict(created=datetime.now(timezone(timedelta(hours=9))).isoformat(),
            scope='Novelty claim review, source receipts and editorial revision; not a proof of literature absence',
            superseded_mutable_documents={'README.md': 'archive/README_hubfree_final_v1.md',
                'Twenty_Questions_Paper_Draft.md': 'archive/Twenty_Questions_Paper_Draft_v0.2.md'},
            files={p.relative_to(ROOT).as_posix():digest(p) for p in sorted(set(paths))})
        MANIFEST.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    if MANIFEST.exists():
        manifest = read(MANIFEST)
        for name, expected in manifest['files'].items():
            assert digest(ROOT/name) == expected, name
        result['new_manifest_files_checked'] = len(manifest['files'])
    print(json.dumps(result,ensure_ascii=False))


if __name__ == '__main__':
    main()
