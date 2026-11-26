"""Freeze the study only after observed PC measurements exist."""
import argparse
import json
from pathlib import Path
import numpy as np
from .io import read_jsonl, write_json, digest, now


def freeze(pilot, destination):
    pilot, destination = Path(pilot), Path(destination)
    if destination.exists() or Path("configs/main.frozen.json").exists():
        raise FileExistsError("Study settings have already been frozen")
    measurements = []
    for folder in sorted(pilot.glob("cell-*")):
        cell = json.loads((folder / "config.json").read_text(encoding="utf-8"))["cells"][0]
        summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
        worlds = read_jsonl(folder / "worlds.jsonl") if (folder / "worlds.jsonl").exists() else []
        def p95(field):
            values = [w[field]["seconds"] for w in worlds if field in w]
            return float(np.quantile(values, .95)) if values else None
        measurements.append(dict(**cell, paired=summary["parents_with_valid_trade"],
            candidates=summary["candidates"], valid_candidates=summary["valid_candidates"],
            worlds=summary["worlds"], complete_worlds=summary["completed_worlds"],
            exact_p95=p95("solver_profile"), baseline_p95=p95("baseline_profile"), feature_p95=p95("feature_profile"),
            process_peak_mb=summary["profile"]["lifetime_peak_rss_mb"],
            phase_seconds=summary["profile"]["seconds"],
            incomplete_statuses=[w["exact"]["status"] for w in worlds if w["exact"]["status"] != "complete"]))
    cells = [dict(n=n, m=m, family=family, parents=180, cohort="id")
             for n, m in [(14, 8), (24, 10), (36, 12)] for family in ("natural", "planted")]
    cells += [dict(n=48, m=14, family=family, parents=80, cohort="size") for family in ("natural", "planted")]
    cells += [dict(n=36, m=12, family="modular", parents=160, cohort="family")]
    estimate = sum(c["parents"] * 2 * sum(next(r for r in measurements if
                    (r["n"], r["m"], r["family"]) == (c["n"], c["m"], c["family"] if c["family"] != "modular" else "planted"))[key]
                    for key in ("exact_p95", "baseline_p95", "feature_p95")) for c in cells)
    config = dict(name="main", seed=2026112501, cells=cells, trades_per_parent=1,
        solver=dict(seconds=10.0, max_states=500000, max_rss_mb=1024),
        tie_tolerance=1e-10, selection_tolerance=1e-12, baselines=True, features=True,
        split_seed=2741125, train_fraction=.6, validation_fraction=.2,
        pilot_directories=[str(p) for p in sorted(pilot.glob("cell-*"))] + ["runs/smoke"],
        reserved_witness="verification_recomputed.json",
        model_seeds=[41, 73, 107],
        model_grid=dict(ridge=[dict(alpha=a) for a in (.1, 1.0, 10.0)],
                        boosting=[dict(max_iter=120, max_leaf_nodes=k) for k in (7, 15)]),
        bootstrap_replicates=5000, bootstrap_seed=129417,
        freeze_receipt="configs/main.frozen.json",
        primary_metric="Parent-mean expected initial-question regret under uniform tie handling",
        primary_comparison="Validation-selected ML versus lookahead3; fixed seed 41 primary, other seeds sensitivity",
        model_fit_scope="Train only, all hyperparameters selected on validation; no successor-state training",
        selection_order=["base", "base_conditional", "base_search", "all"],
        generation_estimate_seconds_p95_sum=estimate,
        post_pilot_numerics="Features clamp abs<=1e-10 and round to 12 decimals to suppress eigensolver permutation noise.")
    write_json(destination, config)
    paths = [Path("experiment.py"), Path("run_study.py")] + sorted(Path("tq").glob("*.py")) + sorted(Path("tests").glob("*.py"))
    receipt = dict(frozen=now(), config_sha256=digest(destination),
                   source_sha256={str(p): digest(p) for p in paths},
                   inputs_sha256={str(p): digest(p) for p in map(Path, ["AGENT_START.md", "Twenty_Questions_Paper_Draft.md", "verification.json", "verification_recomputed.json"])},
                   pilot_summary_sha256=digest(pilot / "summary.json"),
                   development_audit_sha256=digest("runs/smoke/audit.json"),
                   pilot_measurements=measurements,
                   rationale="Measured exact/runtime/memory and completion, never selected by ML improvement or effect magnitude.")
    write_json("configs/main.frozen.json", receipt)
    Path("reports").mkdir(exist_ok=True)
    env = json.loads((pilot / "environment.json").read_text(encoding="utf-8"))
    lines = ["# 예비실험 보고서", "", f"측정 환경: {env['cpu']}, 논리 CPU {env['logical_cpus']}개, RAM {env['physical_memory_mb']/1024:.2f} GiB, Windows, Python 3.13.5. 측정: `{pilot.as_posix()}`. 모든 수치는 사용자 PC의 실제 실행 기록이다.", "",
             "첫 예비 실행(`runs/pilot`) 후, 방법별 빈 캐시로 첫 질문 시간을 재측정한 실행(`runs/pilot_v2`)을 규모 결정에 사용했다. 같은 시드의 반복이므로 두 실행을 독립 표본으로 합치지 않는다.", "",
             "| 가족 | 크기 | 시도/유효 부모 | 후보/수락 | 완료 세계 | 정확 p95(s) | 기준선 전체 p95(s) | 특징 p95(s) | OS peak(MiB) |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in measurements:
        fmt = lambda x: f"{x:.4f}" if x is not None else "미실행"
        lines.append(f'| {r["family"]} | {r["n"]}×{r["m"]} | {r["parents"]}/{r["paired"]} | {r["candidates"]}/{r["valid_candidates"]} | {r["complete_worlds"]}/{r["worlds"]} | {fmt(r["exact_p95"])} | {fmt(r["baseline_p95"])} | {fmt(r["feature_p95"])} | {r["process_peak_mb"]:.1f} |')
    lines += ["", "p95는 2–10세계로 계산한 작은 예비 표본의 기술통계이며 보장된 상한이 아니다. RSS는 5ms 간격 표본과 Windows 프로세스 수명 peak를 함께 기록했다. 짧은 단계의 순간 최고값은 표본 사이에서 놓칠 수 있다. 셀마다 새 프로세스를 사용해 이전 셀의 high-water memory와 분리했다.", "",
        f"96×20은 {measurements[-1]['incomplete_statuses']}로 미완결이었다. 이 두 세계에는 정확 라벨을 넣지 않았다. 64×16도 가능했지만 전체 정책 열거 비용이 커져 주 크기에서 제외했다. 본실험은 14×8·24×10·36×12에 부모 180개씩 두 가족, 크기 외삽 48×14 두 가족 각 80개, 가족 외삽 modular 36×12 160개로 총 1,400번 생성한다.", "",
        f"각 크기·가족의 정확 계산/모든 기준선/전체 특징 p95를 더해 모든 부모가 교환된다고 가정한 보수적 생성 시간 추정은 {estimate:.1f}초다. 모델 학습·동형 검사·파일 I/O 등은 별도다. modular는 같은 크기의 planted 비용으로 근사했으므로 그 가족의 비용 보장이 아니다. 한 번에 한 부모를 처리하고 BLAS 스레드를 1개로 제한한다.", "",
        "설정은 `configs/main.json`, 코드·문서·설정 해시와 고정 시각은 `configs/main.frozen.json`에 남겼다. 본실험의 교환 효과나 시험 손실을 보기 전에 고정했다. 변경이 필요하면 기존 결과를 덮어쓰지 않고 변경 사유와 별도 실행을 남긴다."]
    Path("reports/PILOT_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    design = f"""# 본실험 사전 설계

고정 시각: {receipt['frozen']}. 설정 SHA-256: `{receipt['config_sha256']}`.

## 모집단과 계산 규모

대상은 균등 분포, 질문 비용 1, 응답은 오류 없는 0/1이다. 모든 행은 서로 다른 3원소 질문 집합이다. 주 크기는 14×8, 24×10, 36×12이며 각 크기에서 natural과 planted 가족을 각각 180부모 시도한다. 48×14의 natural/planted 각 80부모는 test_size, 36×12 modular 160부모는 test_family로만 사용한다. 예비 시간·메모리 근거는 PILOT_REPORT.md에 기록했다.

natural은 모든 가능한 삼중항 중 n개를 균등 비복원 표집한다. planted는 임의 여섯 질문의 Pasch 네 행을 삽입하고 나머지 배경을 균등 비복원 표집한다. 배경에서 교환 반대편 행을 인위적으로 금지하지 않는다. modular는 무작위로 나눈 두 질문 모듈 안의 삼중항에 가중치 6, 나머지 1로 순차 비복원 표집한 삽입 가족이다. 이 셋의 교환 존재율·수락률을 분리 보고한다.

존재하는 모든 Pasch 네 행을 열거하고 중복 행이 생기는 교환은 이유와 함께 제외한다. 유효 교환 중 균등하게 하나를 결과 확인 전에 선택한다. 없으면 부모 기록을 보존하고 다른 부모로 채우지 않는다. 효과가 큰 교환만 채택하지 않는다. 전 과정은 균등한 통계 섬유 표집 또는 섬유의 연결성을 보장하지 않는다.

## 정확 라벨과 자원 제한

도달 가능한 후보 비트집합에 정수 DP를 적용한다. 각 세계에 F(V), 비상수 질문 모두의 Q(q), argmin 전체, 최적 트리, 모든 대상의 재실행 깊이를 저장한다. 시간 10초, 완료 캐시 500,000상태, RSS 1,024MiB를 한 세계의 계산 한도로 둔다. 128개 새 상태마다 검사하므로 약간 넘을 수 있다. 시간·상태·메모리 한도에 닿으면 미완결로 표시하고 근사 라벨을 넣지 않는다. 미완결은 조건별 별도 분모로 보고한다. RSS 한도는 정확 계산 프로세스에 관한 것이고 모델 학습 전체의 메모리 상한은 아니다.

## 분할과 누출 통제

부모와 모든 파생 세계·이름 순열·후속 상태는 같은 분할에 둔다. 질문 정점의 대각 차수와 모든 간선의 Gram 가중치를 갖는 완전 그래프를 만든다. WL 해시로 후보만 묶고 NetworkX의 정확 가중 그래프 동형 검사로 Gram 동형 그룹을 확정한다. 주 크기의 그룹을 크기별로 고정 시드 정렬하여 60/20/20% 학습·검증·시험으로 나눈다. 같은 그룹은 하나의 분할에만 둔다. 전체 이분 세계의 동형은 Gram 동형을 함의하므로 이 규칙이 전체 세계 동형 누출도 막는다. 예비 자료와 같은 Gram 그룹 및 ID/OOD가 겹치는 그룹은 excluded_overlap으로 남긴다. 외삽 자료를 튜닝하지 않는다.

## 지표와 동점

주 ML 지표는 첫 질문을 고정한 뒤 최적 후속 행동을 허용하는 평균 초과 비용 R(q)다. 먼저 세계의 질문 동점을 평균하고, 부모 내 세계를 평균한 다음 부모 사이를 평균한다. 최적 argmin 선택 확률을 보조 지표로 둔다. 주 비교는 검증 자료에서 선택한 한 ML 모델(시드 41)과 깊이 3 탐색의 부모별 차이다. 음수는 ML에 유리하다. 시험 부모 5,000회 paired cluster bootstrap으로 고정 모델의 95% 구간을 계산한다. 시드 73·107의 재학습 변동은 따로 보고한다. 파생 세계와 질문 행을 독립 표본으로 세지 않는다. 이 규모는 검출력을 보장한 표본 수가 아니라 PC 자원으로 정한 첫 연구 규모다.

모든 비학습 동점은 균등 무작위로 처리하고 기대 완료 비용을 Fraction으로 정확 평균한다. float 탐색·예측 점수의 동점 허용 오차는 1e-10이다. IG는 정수 불균형을 최소화한다. 최적 라벨은 동점 허용 오차 없이 정수로 판정한다. 행·열 순열에서 특징·예측·라벨이 따라가는지 감사한다. 최적 트리의 재실행용 ID 동점 선택은 주 정책 비교와 별개다.

교환 지표는 signed/absolute ΔC*, argmin 변화율, 서로소 argmin 비율이다. 유효 선택 교환과 정확 계산 완료에 조건부인 지표임을 표시한다. 변화 없는 쌍을 포함한다. 자연 표집의 부모 교환 존재율과 삽입 표집을 합치지 않는다.

## 모델과 특징

비학습 비교는 무작위 질문, 최대 정보이득, 논문 정의 H_d의 깊이 2·3 재계산 정책, 정확 최적이다. H_d는 선택 점수이며 실제 비용으로 보고하지 않는다. 각 정책을 매 후보 상태에서 다시 선택하여 종료까지의 실제 기대 질문 수를 별도 표로 계산한다. 초기만 학습하는 ML의 전체 순차 실행은 수행하지 않는다.

특징은 base, base+conditional, base+search, all의 네 묶음이다. base는 n,m,질문 빈도/엔트로피, Gram 전체·주변 겹침과 첫 응답 뒤 단일 질문 분할의 평균/표준편차/최소/최대/25·75분위/0비율이다. conditional은 각 답 뒤 활성 질문의 Gram 겹침·고유값 요약·연결 성분 크기와 개수다. 상수 질문을 제외하고 빈 가지 요약은 0으로 정의한다. search는 H1,H2,H3와 각 최솟값과의 차이다. 코드의 이름 목록을 모델 메타데이터에 보존한다. 고유값 수치오차를 막기 위해 절댓값 1e-10 이하를 0, 나머지는 소수 12자리로 고정한다. 객체·질문 ID, 정확 비용, 최적 트리 깊이, 시험 라벨은 입력에 없다. 전체 삼중 텐서를 입력하지 않는다. base와 H2가 쌍에서 같은지도 검증한다.

Ridge의 alpha 후보는 0.1/1/10, 표준화는 학습 자료로만 적합한다. 부스팅은 HistGradientBoostingRegressor, max_iter=120, learning_rate=0.05, l2=1, max_leaf_nodes=7/15, early_stopping=False다. 각 묶음·가족의 하이퍼파라미터를 검증 부모 평균 첫 질문 regret으로 정한다. 1e-12 이내의 선택 동점은 위 묶음 순서, Ridge 우선, 설정의 후보 순서를 따른다. 모델은 학습 분할만으로 적합하고 질문 행의 가중치는 부모마다 합이 같도록 정한다. 검증 선택 영수증을 시험 예측 전에 쓴다. 예측 regret을 0으로 잘라내지 않는다. 모든 ablation과 불리한 결과를 보존한다.

특징 추출·벡터 구성·추론 시간을 포함해 보고한다. 모든 ML 변형에 전체 특징 계산 시간을 붙여 보수적으로 비교하며 부분 특징 전용 구현의 속도 개선을 주장하지 않는다. 기준선 첫 선택은 방법마다 빈 캐시를 쓴다. 전체 정책을 모든 대상과 동점에 걸쳐 검산하는 오프라인 시간은 단일 게임 지연과 구분한다. 정확 라벨 생성 시간은 별도로 기록한다.

## 구조 분석과 주장 범위

구조 분석은 쌍 사이 조건부 특징 L1 차이의 학습 중앙값으로 양분하는 기술 분석을 사전에 정한다. 같은 임계값으로 시험과 외삽에 적용하고 효과 없는 대조를 보존한다. 효과/무효/서로소/공통최적의 첫 학습 ID 사례를 저장한다. 이는 구조적 충분조건이나 새로운 일반 정리의 증명이 아니다. 표와 그림은 원시 JSONL/CSV에서 다시 만든다.

기존 논문의 검산/증명, 이번 합성 본실험, 아직 미실행인 ML 전체 정책·외부 데이터·새 일반 정리를 구분한다. ML이 깊이 3보다 낫지 않거나 차이가 불확실해도 그대로 기록하고 논문의 초록·결론을 실제 결과에 맞춘다. 어떤 결과도 예상값으로 채우지 않는다.
"""
    Path("reports/EXPERIMENT_DESIGN.md").write_text(design, encoding="utf-8")
    print(json.dumps(dict(config=str(destination), frozen=receipt["frozen"], parents=sum(c["parents"] for c in cells), estimated_generation_seconds=estimate)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot", required=True)
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    freeze(args.pilot, args.config)
