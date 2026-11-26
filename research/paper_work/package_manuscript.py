"""Package the verified, self-contained paper without changing research data."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT/'paper'


def main():
    verification = json.loads((PAPER/'verification.json').read_text(encoding='utf-8'))
    assert verification['passed']
    assert verification['overleaf']['errors'] == verification['overleaf']['warnings'] == 0
    qa = dict(renderer='PyMuPDF 1.3x, page PNGs and contact sheet',
              pdf='output/pdf/Twenty_Questions_Paper_Final.pdf', pages_rendered=18,
              contact_sheet='tmp/pdfs/final_overleaf/contact.png',
              inspected='All-page contact sheet; full-size title, theorem, ML table, witness tables and references',
              clipping_or_overlaps_found=False, missing_glyphs_found=False,
              bibliography_orphan_page_removed=True)
    (PAPER/'visual_qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
    readme = '''# 완성 논문 LaTeX 패키지

main.tex를 XeLaTeX, TeX Live 2025 이상으로 컴파일하세요.
Overleaf에서 실제 확인한 환경은 XeLaTeX / TeX Live 2026입니다.
그림 3개, 표 15개와 참고문헌 20개가 소스 안에 있어 외부 그림이나 BibTeX가 필요 없습니다.
Twenty_Questions_Paper_Final.pdf는 온라인에서 내려받은 실제 18쪽 PDF입니다.

evidence.json은 원고에 사용한 원시 입력의 경로와 해시,
verification.json은 보존 검사와 온라인 대조,
visual_qa.json은 PDF 렌더 검수 기록입니다.
이 ZIP은 독립 컴파일용이며 원시 실험 전체와 학습 모델 파일은 포함하지 않습니다.
기존 연구 작업 폴더의 runs/, final_work/, novelty_work/에 자료가 보존되어 있습니다.

온라인 프로젝트의 main document는 Twenty_Questions_Final.tex입니다.
이 ZIP의 main.tex는 같은 완성 원고이고, 온라인에 보존한 원래 main.tex와 다릅니다.

핵심 결과는 균등 탐욕 동점에 대한 선형 regret 대비입니다.
ML 개선 미확정, 실패한 증폭, 미완결 계산을 원고에 유지했습니다.
최초성·외부 동료 심사·형식 증명 인증을 주장하지 않습니다.
'''
    with zipfile.ZipFile(PAPER/'Twenty_Questions_LaTeX.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(PAPER/'main.tex','main.tex')
        archive.write(ROOT/'output/pdf/Twenty_Questions_Paper_Final.pdf','Twenty_Questions_Paper_Final.pdf')
        for name in ('evidence.json','verification.json','visual_qa.json'):
            archive.write(PAPER/name,name)
        archive.writestr('README.md',readme)
    with zipfile.ZipFile(PAPER/'Twenty_Questions_LaTeX.zip') as archive:
        assert archive.testzip() is None
        assert archive.read('main.tex') == (PAPER/'main.tex').read_bytes()
    status = dict(completed_at=datetime.now(timezone(timedelta(hours=9))).isoformat(),
                  status='completed', manuscript='paper/main.tex', language='Korean, English title/abstract',
                  pdf='output/pdf/Twenty_Questions_Paper_Final.pdf', pages=18, figures=3, tables=15, references=20,
                  package='paper/Twenty_Questions_LaTeX.zip',
                  overleaf=verification['overleaf'], verification='paper/verification.json',
                  finalization_record='paper/FINALIZATION.md', prior_research_preserved=True,
                  ml_improvement_claim=False, novelty_priority_certified=False)
    (ROOT/'PAPER_STATUS.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
    paths = [p for p in PAPER.rglob('*') if p.is_file()]
    paths += [p for p in (ROOT/'paper_work').rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    paths += [ROOT/'output/pdf/Twenty_Questions_Paper_Final.pdf',ROOT/'output/pdf/main.log',ROOT/'PAPER_STATUS.json']
    manifest = dict(created=status['completed_at'],scope='Completed manuscript and local/Overleaf evidence, preserving prior frozen packages',
                    files={p.relative_to(ROOT).as_posix():sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))})
    (ROOT/'PAPER_ARTIFACT_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(passed=True,package=str(PAPER/'Twenty_Questions_LaTeX.zip'),files=len(paths),pages=18)))


if __name__ == '__main__':
    main()
