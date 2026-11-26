# Twenty Questions 통제 그래프 실험

현재 후속 검토는 [선행연구·연결 확장·증명 감사](Twenty_Questions_Followup_Review.md)에 정리했다.

`AGENT_START.md`와 논문 초안의 조건을 구현한 로컬 실험이다. LLM API와 API 키는 사용하지 않는다. Python 3.13.5의 별도 `.venv`에서 실행했으며 패키지 버전은 `requirements-lock.txt`에 고정했다.

현재 연구 방향은 **질문 쌍 통계를 보존하는 극값 탐색**이다. 새 결과는 [극값 연구 노트](Twenty_Questions_Extremal_Note.md), [사전 설계](reports/EXTREMAL_DESIGN.md), [성장 증명](reports/extremal_math_agent.md), [독립 검토](reports/EXTREMAL_INDEPENDENT_REVIEW.md)에 있다. 아래의 이전 무작위 본실험·ML 결과는 그대로 보존한다.

먼저 [예비실험 보고서](reports/PILOT_REPORT.md), [본실험 사전 설계](reports/EXPERIMENT_DESIGN.md), [본실험 결과](runs/main/report/MAIN_REPORT.md)를 읽으면 된다. 실제 사용한 설정은 [main.json](configs/main.json), 실행 전 설정·코드·입력 해시와 시각은 [main.frozen.json](configs/main.frozen.json)에 있다.

## 설치와 실행

PowerShell에서 작업 폴더를 현재 디렉터리로 둔다.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe verify_witness.py --output verification_recomputed.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`verification.json`은 기존 14×8 예시의 검산 결과다. `verification_recomputed.json`은 이번에 재실행한 결과이며 모든 JSON 필드가 일치한다. 이 예시와 예비·개발 데이터는 본실험 빈도나 학습 표본으로 삽입하지 않았다.

이미 고정한 설계의 본실험을 재실행하려면 새 출력 폴더를 사용한다. 이전 측정 파일은 덮어쓰지 않는다.

```powershell
.\.venv\Scripts\python.exe run_study.py --config configs/main.json --out runs/reproduction
```

설정이나 코드가 고정 영수증의 해시와 다르면 생성 단계가 중단된다. 연구 설정을 바꿀 때에는 원래 설정과 영수증을 보존하고 새 설정·근거·해시를 별도로 기록해야 한다. 정확 라벨과 예측은 결정적 재현 대상이며 실행 시각과 시간·메모리 측정값은 실행마다 달라질 수 있다. 원래 예비·개발 폴더도 분할 중복 검사를 위해 유지한다.

단계별 실행과 표·그림 재생성도 가능하다.

```powershell
.\.venv\Scripts\python.exe experiment.py generate --config configs/main.json --out runs/new_main
.\.venv\Scripts\python.exe experiment.py split --config configs/main.json --out runs/new_main
.\.venv\Scripts\python.exe experiment.py compare --config configs/main.json --out runs/new_main
.\.venv\Scripts\python.exe experiment.py report --config configs/main.json --out runs/new_main
.\.venv\Scripts\python.exe experiment.py audit --config configs/main.json --out runs/new_main
```

감사를 통과한 결과로 Markdown 논문을 다시 생성할 수도 있다. 원본 초안은 `archive/Twenty_Questions_Paper_Draft_v0.1.md`에 보존한다.

```powershell
.\.venv\Scripts\python.exe update_paper.py --run runs/main --output Twenty_Questions_Paper_Draft.md
```

`generate`, `split`, `compare`는 기존 산출물이 있으면 중단한다. `report`와 `audit`는 같은 원시 자료로 산출물을 다시 만들 수 있다. 중간에 실행이 중단되면 불완전한 원시 기록을 보존하고 새 폴더에서 다시 실행한다. 이어 붙여 표본 수를 변경하지 않는다.

## 예비실험

```powershell
.\.venv\Scripts\python.exe experiment.py pilot --config configs/pilot.json --out runs/new_pilot
```

`runs/pilot`은 최초 연결 실험, `runs/pilot_v2`는 기준선마다 독립된 빈 탐색 캐시로 다시 측정한 예비실험이다. 같은 시드의 반복이므로 독립 표본으로 합치지 않는다. `runs/smoke`는 분할·학습·보고·감사 전체 경로를 확인한 개발 데이터다. 본실험의 시험 자료와 Gram 동형 중복을 점검한다. 96×20의 상태 수 제한 미완결 기록도 그대로 남아 있다.

## 저장 형식과 분석 범위

`runs/main`에 다음 기록을 보존한다.

본실험 원시 JSON의 대상·질문 인덱스는 0부터 시작한다. 기존 검산 스크립트와 논문 표 1–3은 원래의 1부터 시작하는 표기를 유지한다.

| 파일 | 내용 |
|---|---|
| `parents.jsonl` | 모든 생성 시도, 독립 부모 ID/시드/가족, 교환 없는 부모, 교환 후보와 제외 사유 |
| `worlds.jsonl` | 전체 응답 행렬, 부모와 교환 이력, 정확 계산 상태, 모든 첫 질문 비용, argmin 집합, 최적 트리와 대상별 깊이, 정책 결과와 단계별 자원 측정 |
| `pairs.jsonl` | 원본·파생 세계 ID, 행 차수/Gram/C4/C6 통제 검사, 교환 방향, 효과 0을 포함한 모든 결과 |
| `features.jsonl` | 질문별 세 특징 묶음과 별도로 저장한 정확 회귀 목표 |
| `splits.json` | 정확 Gram 동형 그룹, 부모 단위 학습·검증·시험 및 외삽 분할, 예비 중복 제외 |
| `environment.json`, `manifest.json` | PC/패키지/스레드/소스 해시와 원시 파일 무결성 해시 |
| `comparison/` | 모든 검증 후보, 시험 전에 고정한 모델 선택, 모델 파일, 시드별 예측과 시간 |
| `report/` | 원시 표 CSV, 부모 bootstrap 구간, 모델 시드 변동, 특징 제거·외삽 결과, 구조 분석, PNG/PDF 그림 |
| `audit.json` | 통제 조건, 계보 재실행, 모든 최적 트리, Gram 그룹, 특징 라벨, 행·열 순열 검사 |

주 학습 평가는 첫 질문 선택이다. 첫 질문의 초과 비용에는 최적 후속 행동을 허용한다. 비학습 정책의 전체 실행 비용은 매 후속 상태에서 정책을 다시 선택한 종료 비용이며 따로 보고한다. 초기 상태만 학습한 ML의 전체 순차 정책은 미평가다.

동점은 균등 무작위 기대값을 사용한다. 비학습 전체 정책은 `Fraction`으로 모든 동점 경로를 정확 평균한다. 정확 DP의 시간/상태/메모리 한도 초과는 미완결로 표시하며 근사 정답을 만들지 않는다. 같은 부모의 세계와 질문 행을 독립 표본으로 세지 않는다. 효과 없는 쌍과 ML이 개선되지 않는 비교를 삭제하지 않는다.

## 구현

| 모듈 | 역할 |
|---|---|
| `tq/core.py` | 부모 생성, Pasch 열거·교환, 통제 검사, 도달 상태 정수 DP, 깊이 1–3 탐색과 실제 정책 비용 |
| `tq/features.py` | ID를 쓰지 않는 불변/조건부/탐색 특징 |
| `tq/data.py`, `tq/io.py` | 원시 계보 저장, 시간과 5ms RSS 측정, 환경과 해시 |
| `tq/splits.py` | WL 후보 묶음 뒤 정확한 weighted Gram 동형 그룹과 분할 |
| `tq/models.py` | 부모 가중 Ridge/부스팅, 검증 선택, 독립 시험, 모델 저장 |
| `tq/reporting.py`, `tq/audit.py` | 원시 자료에서 표·그림 재생성, 구조 대조와 재검산 |
| `tq/planning.py` | 예비 측정에서 본실험 규모·설정·설계 고정 |

`tests/test_research.py`는 작은 전체 부분집합 DP와 독립 대조, Pasch 완전 열거 대조, 기존 예시의 무작위 동점 비용, 시간 제한 라벨 부재, 이름 순열, Gram 그룹, 가중 표준화를 검사한다.

원래 PDF·DOCX는 본실험 전 버전 0.1의 스냅샷이다. 위 무작위 본실험의 수치는 Markdown 논문과 결과 보고서·CSV를 기준으로 한다. 그 단계에서는 외부 데이터, 일반 구조 정리, ML 전체 정책 및 불균등·오류 응답 확장을 수행하지 않았다. 후속 극값 연구의 명제와 성장 증명은 별도 노트에 있다.

## 극값 탐색과 구조 인증

고정 Gram 안의 Pasch 이동과, 매 시점 통제 쌍을 유지하며 공통 배경을 함께 설계하는 두 모드를 구분한다. 두 번째 모드에서는 시점 사이의 Gram이 달라질 수 있다. 새로운 최초성·전역 최대값이나 발생률을 주장하지 않는다.

```powershell
.\.venv\Scripts\python.exe extremal_experiment.py --config configs/extremal.json --out runs/extremal_reproduction
.\.venv\Scripts\python.exe extremal_pair_design.py --config configs/extremal_pair_design.json --out runs/pair_design_reproduction
.\.venv\Scripts\python.exe extremal_certify.py --pair-run runs/pair_design_reproduction --out runs/extremal_audit_reproduction
```

새 실행에는 새 출력 폴더를 쓴다. 공통 배경 설계의 기본 설정은 보존된 고정 섬유 씨앗을 입력으로 사용한다. 다른 고정 섬유 실행을 연결할 때에는 새 설정 파일의 `seed_pair`를 그 실행의 `fiber-00-extrema.json`으로 지정하고 변경 근거를 남긴다. 시간 제한에 의해 방문 수가 달라질 수 있으므로 재현의 대상은 저장된 그래프의 비용과 증명 인증이며 종료 시각·시간·메모리는 달라질 수 있다.

보존된 원시 기록에서 표·그림·새 연구 노트를 다시 생성한다.

```powershell
.\.venv\Scripts\python.exe report_extremal.py
```

| 폴더 | 내용 |
|---|---|
| `runs/extremal_v1` | 10개 고정 Gram 성분, 2,534세계, 모든 Pasch 간선·도달 극값·중단 이유 |
| `runs/extremal_pair_design_v1` | 6,000회 제안, 5,728쌍, 수락/거절 경로, 최고 18×9 반례 |
| `runs/extremal_analysis_v1` | 18×9 전 부분집합 독립 DP, 피복 포락선·프로필·정확 유리수 인증, 직접합/곱 유한 검산, 증명 경계 |
| `runs/extremal_report_v1` | 전체 계보 감사, 질문별 비용표, 행렬 그림, 탐색 곡선과 성장 경계 그림, 소스 사본 |

새 18×9 반례의 직접합은 선형 증폭에 실패했다. 선형 증명은 별도의 14×8 기반 쌍을 사용한다. 큰 N의 값은 DP 측정 대신 증명 하한/상한으로 표시한다. 차수 3과 같은 Gram 아래 regret 대비는 `N/392+O(1)`인 비연결 가족을 구성했으며, 고정 차수의 비용 비율은 발산하지 않는다. 실행 당시 인증 소스는 `runs/extremal_analysis_v1/source_executed`에 보존했다. 이후 추가한 출력 폴더 CLI는 계산식을 바꾸지 않는다.

## 후속 연결성·증명 재현

새 연결 그래프 인증은 `.\.venv\Scripts\python.exe followup_work/root_connected_certificate.py --out runs/new_connected_check`로 새 폴더에 생성한다. `root_gluing_review.py`는 독립된 행 집합 열거와 모든 512개 기반 CUT 검사를 수행하며 기본 결과 폴더가 있으면 중단한다. 기존 기록은 삭제하지 않는다. 세부 실행·실패한 강화 시도와 모든 원시 인증은 `followup_work/`와 후속 노트에서 연결한다.
