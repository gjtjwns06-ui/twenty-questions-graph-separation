"""Verify delivered manuscript evidence and the source downloaded from Overleaf.

Does not rerun experiments, alter splits, fit models, or certify mathematical novelty.
Run with the host Python (PyMuPDF); raw research remains frozen.
"""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone, timedelta
import json
import re
import zipfile
import fitz

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def entries(path):
    with zipfile.ZipFile(path) as archive:
        return {n: archive.read(n) for n in archive.namelist() if not n.endswith('/')}


def normalized(data):
    return data.replace(b'\r\n', b'\n')


def main():
    paper = ROOT / 'paper'
    evidence = read(paper / 'evidence.json')
    for name, expected in evidence['input_sha256'].items():
        assert digest(ROOT / name) == expected, name
    assert digest(paper / 'main.tex') == evidence['latex_sha256']
    assert (paper / 'Twenty_Questions_Final.tex').read_bytes() == (paper / 'main.tex').read_bytes()
    preserved = []
    for name, base in [('runs/main/ARTIFACT_MANIFEST.json', ROOT/'runs/main'),
                       ('EXTREMAL_ARTIFACT_MANIFEST.json', ROOT),
                       ('FOLLOWUP_ARTIFACT_MANIFEST.json', ROOT),
                       ('FINAL_RESEARCH_ARTIFACT_MANIFEST.json', ROOT),
                       ('NOVELTY_ARTIFACT_MANIFEST.json', ROOT)]:
        manifest = read(ROOT/name)
        for filename, expected in manifest['files'].items():
            assert digest(base/filename) == expected, filename
        preserved.append({'manifest': name, 'listed_entries': len(manifest['files'])})
    tex = (paper/'main.tex').read_text(encoding='utf-8')
    labels = re.findall(r'\\label\{([^}]+)\}', tex)
    assert len(labels) == len(set(labels))
    refs = re.findall(r'\\(?:eqref|ref)\{([^}]+)\}', tex)
    assert set(refs) <= set(labels)
    bib = set(re.findall(r'\\bibitem\{([^}]+)\}', tex))
    cites = {k for group in re.findall(r'\\cite\{([^}]+)\}', tex) for k in group.split(',')}
    assert cites <= bib and len(bib) == 20
    assert not re.search(r'@@\w+@@|TODO|PLACEHOLDER', tex)
    assert evidence['parents'] == 1400 and evidence['pairs'] == 1223 and evidence['worlds'] == 2446
    assert evidence['zero_cost_pairs'] == 1114
    assert evidence['selected38_regret_contrast'] == '13/76'
    assert evidence['cubic_asymptotic_regret_contrast'] == 'N/578+O(1)'
    comparison = evidence['main_paired_difference']
    assert float(comparison['ci_low']) < 0 < float(comparison['ci_high'])
    assert evidence['primary_model'] == 'boosting_all' and not evidence['large_dp_claim']
    receipt_dir = ROOT/'paper_work/overleaf_verification'
    original = entries(receipt_dir/'original_project.zip')
    completed = entries(receipt_dir/'completed_project.zip')
    assert original['main.tex'] == completed['main.tex']
    assert normalized(completed['Twenty_Questions_Final.tex']) == normalized((paper/'main.tex').read_bytes())
    local = fitz.open(ROOT/'output/pdf/main.pdf')
    online = fitz.open(receipt_dir/'overleaf_compiled.pdf')
    local_text = [p.get_text() for p in local]
    online_text = [p.get_text() for p in online]
    assert local_text == online_text and len(online) == 18
    assert not any('\ufffd' in t or '??' in t for t in online_text)
    log = (ROOT/'output/pdf/main.log').read_text(encoding='utf-8')
    assert 'Overfull' not in log and 'LaTeX Font Warning' not in log and 'undefined references' not in log
    result = {
        'checked_at': datetime.now(timezone(timedelta(hours=9))).isoformat(),
        'passed': True, 'raw_input_hashes_checked': len(evidence['input_sha256']),
        'preserved_manifests': preserved,
        'preserved_listed_entries': sum(p['listed_entries'] for p in preserved),
        'references': len(bib), 'labels': len(labels), 'pages': len(online),
        'source_matches_overleaf_after_line_ending_normalization': True,
        'original_overleaf_main_preserved_byte_for_byte': True,
        'pdf_text_matches_overleaf_on_all_pages': True,
        'pdf_replacement_glyphs': 0, 'unresolved_references': 0,
        'ml_null_and_failed_constructions_retained': True,
        'new_experiments_or_retraining_performed_in_manuscript_stage': False,
        'priority_or_formal_proof_certification': False,
        'overleaf': read(receipt_dir/'verification.json'),
    }
    (paper/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=True))


if __name__ == '__main__':
    main()
