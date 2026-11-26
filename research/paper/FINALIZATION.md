# 최종 LaTeX 원고와 검증 기록

2026-11-25, 한국어 본문과 영문 제목·초록, 18쪽, 표 15개, 그림 3개, 참고문헌 20개.

## 전달본

- `main.tex`: 표·벡터 그림·참고문헌을 내장한 기준 원고.
- `Twenty_Questions_Final.tex`: 같은 내용의 Overleaf 업로드 파일.
- `../output/pdf/Twenty_Questions_Paper_Final.pdf`: Overleaf에서 실제 내려받은 최종 PDF.
- `Twenty_Questions_LaTeX.zip`: 새 프로젝트에 올릴 수 있는 패키지. ZIP 안의 `main.tex`는 완성 원고이며, 기존 온라인 프로젝트의 짧은 원래 `main.tex`와 다르다.
- `evidence.json`: 원고 생성에 읽은 31개 입력의 해시 및 핵심 수치.
- `verification.json`: 보존 자료, 상호 참조, 온라인 소스 및 PDF 대조 결과.

## Overleaf 반영

프로젝트: https://www.overleaf.com/project/6b06bd27056e299464631d9c

`Twenty_Questions_Final.tex`를 main document로 지정하고 XeLaTeX / TeX Live 2026으로 컴파일했다. 최종 UI는 `Compile finished`, Errors 0, Warnings 0, 전체 18쪽을 표시했다. 참고문헌의 Underfull hbox 한 건은 typesetting 정보로 남으며 육안 검사에서 잘림이나 겹침은 없었다.

온라인 소스를 ZIP으로 다시 내려받아 로컬 기준 원고와 대조했다. Overleaf가 CRLF를 LF로 바꾼 차이만 있으며 내용은 같다. 원래 온라인 `main.tex`는 작업 전 다운로드와 바이트 단위로 같다. 온라인 PDF와 로컬 컴파일 PDF의 페이지별 추출 텍스트도 18쪽 모두 같다. 공유 권한이나 초대 설정은 변경하지 않았다.

## 원고에 반영한 연구

주 결과는 동일한 전체 질문 Gram, 서로 다른 차수 3 행, 최대 질문 차수 10, 단절점 없는 연결성 및 양의 팽창이 함께 성립하는 구성이다. 매 상태의 탐욕 동점을 균등하게 처리할 때 regret 대비는 `N/578+O(1)`이다. 모든 동점 규칙에 대한 결과나 발산하는 근사비로 주장하지 않는다.

본문과 부록에는 원래 14×8 첫 질문 충돌, 극값 탐색, 18×9와 38×18 유한 반례, 직접합·허브 연결의 이전 결과, 허브 없는 강화 구성과 아홉 골격의 정확 팽창 인증을 반영했다. 큰 구성의 증명상 경계를 실제 전체 DP 측정으로 표현하지 않았다.

기존 합성 본실험 1,400부모 시도, 1,223완료 쌍·2,446세계와 예비 시간·메모리, 분할, 특징, 사전 선택 모델 및 13개 방법/ablation의 결과를 포함한다. ML은 첫 질문만 평가했으며 전체 ML 정책 비용을 채우지 않았다. 주 비교의 paired 구간이 0을 포함한다는 결과를 유지했다. 비용 효과가 없는 1,114쌍, 개선되지 않은 탐색, 작은 크기의 대비 0과 상태·시간 한도 미완결도 남겼다.

문헌 감사의 범위와 인접한 결과를 구분했다. 최초성이나 선행연구 부재를 인증하지 않으며, 외부 동료 심사 또는 형식 증명 인증을 받았다고 표현하지 않았다.

## 검증과 재생성

`python paper_work/verify_manuscript.py`는 31개 원고 입력 해시와 기존 다섯 manifest의 351개 등재 항목을 확인한다. 이전 실험, 문헌 감사, Markdown 원고의 동결 자료는 수정하지 않았다. 이 단계에서는 실험 생성·학습·모델 선택을 새로 하지 않았다.

원고 재생성은 `.venv/Scripts/python.exe paper_work/build_manuscript.py`, 로컬 PDF 컴파일은 `.tools/tectonic/tectonic.exe -X compile paper/main.tex --outdir output/pdf --keep-logs`다. PDF 검수용 18쪽 렌더링은 `tmp/pdfs/final_overleaf/`에 있다. 로컬 휴대용 컴파일러는 공식 Tectonic 배포에서 취득했으며 영수증은 `.tools/tectonic/acquisition.json`에 있다.
