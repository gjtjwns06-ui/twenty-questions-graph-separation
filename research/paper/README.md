# 완성 연구 원고

`main.tex`는 그림·표·참고문헌을 모두 포함하는 자체 완결 LaTeX 원고다.
Overleaf에서는 XeLaTeX와 TeX Live 2025 이상을 선택한다. 그림 외부 파일이나 BibTeX 실행은 필요 없다.

본문은 한국어이며 영문 제목과 초록을 포함한다. 실제 측정과 정확 유리수 값, 수학적 경계, 미실행 항목을 구분한다.
`evidence.json`은 표·그림 좌표에 사용한 원시 파일의 해시를 보존한다.

로컬 재생성: `.venv/Scripts/python.exe paper_work/build_manuscript.py`
로컬 컴파일: `.tools/tectonic/tectonic.exe -X compile paper/main.tex --outdir output/pdf --keep-logs`

기존 v0.3 Markdown·옛 PDF·DOCX와 실험 기록은 보존한다. 새 완성본의 기준은 이 LaTeX와 새 PDF다.
