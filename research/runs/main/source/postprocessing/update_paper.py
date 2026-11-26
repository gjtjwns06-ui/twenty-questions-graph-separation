#!/usr/bin/env python3
"""Regenerate the paper's measured sections from the preserved raw study tables."""
import argparse
import csv
import json
from pathlib import Path
import re


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def update(run, output):
    run, output = Path(run), Path(output)
    report = run / "report"
    summary = read_json(run / "summary.json")
    audit = read_json(run / "audit.json")
    assert audit["passed"], "Only audited results may update the paper"
    selection = read_json(run / "comparison/selection.json")
    config = read_json(run / "config.json")
    occurrences = read_csv(report / "occurrence.csv")
    policies = read_csv(report / "policy_summary.csv")
    comparisons = read_csv(report / "paired_comparisons.csv")
    timing = read_json(report / "timing.json")
    splits = read_json(run / "splits.json")
    primary = selection["primary_model"]
    seed = str(config["model_seeds"][0])
    test = next(r for r in policies if r["split"] == "test" and r["method"] == primary and r["seed"] == seed)
    la = next(r for r in policies if r["split"] == "test" and r["method"] == "lookahead3")
    comparison = next(r for r in comparisons if r["split"] == "test" and r["baseline"] == "lookahead3" and r["seed"] == seed)
    difference, low, high = map(float, [comparison["mean_difference"], comparison["ci_low"], comparison["ci_high"]])
    conclusion = ("깊이 3 탐색보다 낮은 초과 비용을 보였으며 고정 모델의 부모 재표집 구간도 0 아래였다" if high < 0 else
                  "깊이 3 탐색보다 수치상 낮았으나 차이 구간이 0을 포함하여 개선을 확정하지 못했다" if difference < 0 else
                  "깊이 3 탐색보다 개선되지 않았다")
    english = ("The selected model improved over depth-3 lookahead in the fixed-model parent bootstrap comparison" if high < 0 else
               "The selected model had a lower point estimate than depth-3 lookahead, but its difference interval included zero" if difference < 0 else
               "The selected model did not improve over depth-3 lookahead")
    original = Path("archive/Twenty_Questions_Paper_Draft_v0.1.md").read_text(encoding="utf-8")
    text = original.replace("본실험 전 연구 초안 · 2026년 11월 25일 · 버전 0.1",
        "합성 본실험 1회 완료 연구 초안 · 2026년 11월 25일 · 버전 0.2\n\n"
        "> 기존 14×8 검산·증명과 새로 실행한 합성 실험을 구분한다. PDF·DOCX는 버전 0.1 스냅샷이며, 최신 측정과 상태는 이 Markdown 및 원시 결과표를 기준으로 한다.")
    abstract = ("스무고개에서 현재 후보를 고르게 나누는 질문과 이후에 구별하기 쉬운 후보 집합을 남기는 질문은 다를 수 있다. "
        "본 연구는 대상–질문 행렬의 대상별 차수와 질문 공동 출현 행렬을 동일하게 유지한 채 Pasch 교환으로 고차 연결을 바꾼다. "
        "기존에 검산한 14×8 구성의 최적 평균 비용은 54/14와 55/14이고 최적 첫 질문 집합은 서로소이다. "
        f"이 예시와 분리하여 사용자 PC의 시간·메모리 예비 측정 후 설계를 고정하고 {summary['parents']:,}번의 독립 부모 생성을 시도했다. "
        f"유효 교환 {summary['pairs']:,}쌍, {summary['worlds']:,}세계 중 {summary['completed_worlds']:,}세계의 정확 계산을 완료했다. "
        f"Gram 동형 그룹을 분리한 주 시험 {test['parents']}부모에서 검증 선택 모델 `{primary}`의 첫 질문 초과 비용은 {float(test['first_regret']):.6f}, "
        f"깊이 3 탐색은 {float(la['first_regret']):.6f}회였다. 선택 모델은 {conclusion}. "
        "교환 효과가 없는 사례와 불리한 학습 결과도 보존했다. 이 결과는 지정한 합성 분포와 완료 사례에 관한 것으로, 일반적인 학습 우월성·현실 대화 성능·새로운 구조 정리를 뜻하지 않는다.")
    text = re.sub(r"(?<=## 초록\n\n).*?(?=\n\n\*\*핵심어)", lambda _: abstract, text, flags=re.S)
    english_abstract = ("We study binary object–attribute graphs with identical per-object degrees and question Gram matrices, using Pasch trades and exact adaptive identification costs. "
        "The previously verified 14-object, 8-question witness has optimal mean costs 54/14 and 55/14 with disjoint optimal first-question sets. "
        f"Separately, after timing and memory pilots on the user's PC, we froze a synthetic study with {summary['parents']:,} independent parent-generation attempts, "
        f"{summary['pairs']:,} valid controlled pairs, and {summary['completed_worlds']:,}/{summary['worlds']:,} completed exact world labels. "
        f"Exact Gram-isomorphism groups define the data split. On the main held-out set of {test['parents']} paired parents, "
        f"the validation-selected model's mean first-question regret was {float(test['first_regret']):.6f}, versus {float(la['first_regret']):.6f} for depth-3 lookahead. "
        f"{english}; the paired difference was {difference:.6f} with a 95% parent-bootstrap interval [{low:.6f}, {high:.6f}]. "
        "Null interventions and unsuccessful learning comparisons are retained. Full sequential learned policies, real-world data, and a new general structural theorem remain untested or unestablished.")
    text = re.sub(r"(?<=## Abstract\n\n).*?(?=\n\n## 1 서론)", lambda _: english_abstract, text, flags=re.S)
    text = text.replace("세 번째 부분의 결과는 아직 없다.", "세 번째 부분의 첫 합성 실행 결과는 8절에 제시하며, 전체 학습 정책과 일반 정리는 미완료다.")
    text = text.replace("향후 학습 성능과 반복 구조에 관한 기여는 실제 결과가 나온 뒤 추가해야 한다.",
                        "이번 합성 실행에서 측정한 학습 비교와 효과 없는 대조는 8절에 추가했다. 반복 구조의 일반 정리는 아직 확립하지 않았다.")
    text = text.replace("## 6 본실험 설계", "## 6 본실험 설계와 구현\n\n"
        "이 절의 프로토콜을 `configs/main.json`과 `reports/EXPERIMENT_DESIGN.md`로 본실험 전에 고정했다. "
        "고정 시각과 코드·입력 해시는 `configs/main.frozen.json`, 예비 근거는 `reports/PILOT_REPORT.md`에 있다. "
        "주 설정은 균등 목표·차수 3·정확 이진 응답이다. 도달 가능한 후보 집합의 정수 DP를 구현하여 기존 예시 및 작은 전체 부분집합 DP와 대조했다. "
        "이하의 방법 정의와 앞으로의 확장 제안을 구분하며, 실제 완료 상태는 8절을 기준으로 한다.")
    text = text.replace("본실험의 생성기와 학습 파이프라인은 후속 구현 대상이다.",
        "생성기·교환 열거·정확 계산·분할·Ridge/부스팅·보고·감사는 `tq/`와 `experiment.py`에 구현했다. "
        "실행법과 저장 형식은 `README.md`에 있으며 원시 파일에서 표와 그림을 다시 생성할 수 있다.")
    section = ["## 8 실행 결과와 완료 상태", "",
        "### 8.1 예비 측정과 고정 설계", "",
        "사용자 PC는 Intel Core Ultra 5 226V, 논리 CPU 8개, RAM 15.54GiB이며 Python 3.13.5와 CPU 연산을 사용했다. "
        "BLAS 스레드는 1개다. 예비실험의 36×12 정확 계산 p95는 가족별 약 0.019초, 48×14는 약 0.063–0.071초였다. "
        "64×16은 완료됐지만 정책 열거 시간이 커졌고, 96×20은 두 세계 모두 250,000상태 제한으로 미완결이었다. "
        "이 기록을 삭제하거나 근사 정답으로 대체하지 않았다. 셀별 새 프로세스의 OS peak는 약 34–55MiB였으며 5ms RSS 표본의 한계도 기록했다.", "",
        "주 크기 14×8·24×10·36×12에서 natural(균등 삼중항)과 planted(Pasch 삽입+균등 배경)를 각 180부모 시도했다. "
        "외삽은 48×14 두 가족 각 80부모와, 모듈 내부 삼중항의 가중치를 6으로 둔 modular 36×12 160부모다. "
        "유효 교환 중 하나를 비용 확인 전에 균등 선택했다. 교환이 없는 부모를 다른 부모로 채우지 않았다. "
        "본실험 정확 계산 한도는 세계당 10초·500,000상태·RSS 1,024MiB다.", "",
        "### 8.2 교환과 정확 비용", "",
        f"총 {summary['parents']:,}부모 시도 중 {summary['pairs']:,}부모에서 하나씩 유효 쌍을 얻었다. "
        f"{summary['worlds']:,}세계 전부에 대해 {summary['completed_worlds']:,}개 정확 계산이 완료됐다. "
        "아래 변화율은 선택된 유효 교환과 정확 계산 완료에 조건부이며, 자연 표집과 삽입 표집을 합친 모집단 발생률로 해석하지 않는다.", "",
        "표 5 생성 가족별 교환 결과", "",
        "| 가족 | 크기 | 시도 부모 | 유효 쌍 | 평균 |ΔC*| | 서로소 argmin 쌍 | 비용차 0 쌍 |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    # Escape the absolute-value bars in Markdown table headers.
    section[-2] = "| 가족 | 크기 | 시도 부모 | 유효 쌍 | 평균 절대 ΔC* | 서로소 argmin 쌍 | 비용차 0 쌍 |"
    for r in occurrences:
        section.append(f'| {r["family"]} | {r["n"]}×{r["m"]} | {r["attempted_parents"]} | {r["complete_pairs"]} | {float(r["absolute_delta"]):.6f} | {r["disjoint_count"]} ({float(r["disjoint_rate"]):.2%}) | {r["zero_cost_effect_count"]} |')
    section += ["", "### 8.3 첫 질문 학습과 전체 비학습 정책", "",
        "질문 이름 순열까지 고려한 정확 Gram 동형 그룹을 크기별 60/20/20%로 분할했다. "
        "개발·검산 자료와 같은 Gram 그룹을 시험에서 제외했다. 같은 부모의 두 세계는 항상 같은 분할이다. "
        f"주 시험은 {test['parents']}부모·{test['worlds']}세계다. 첫 질문 초과 비용을 부모 안에서 평균한 뒤 부모에 같은 가중치를 부여했다. "
        "동점은 균등 무작위 기대값이며 비학습 전체 정책은 모든 동점 분기를 유리수로 평균했다.", "",
        "표 6 주 시험 결과(학습 시드 41; 전체 정책 비용과 첫 질문 비용을 분리)", "",
        "| 방법/특징 | 첫 질문 초과 비용 | 최적집합 선택 확률 | 전체 정책 평균 비용 |", "|---|---:|---:|---:|"]
    for r in policies:
        if r["split"] == "test" and r["seed"] in ("fixed", seed):
            actual = f'{float(r["full_policy_mean"]):.6f}' if r["full_policy_mean"] else "미평가"
            section.append(f'| {r["method"]} | {float(r["first_regret"]):.6f} | {float(r["optimal_probability"]):.3%} | {actual} |')
    section += ["", f"검증 자료에서 선택한 주 모델 `{primary}`는 {conclusion}. "
        f"주 모델 − 깊이 3 탐색의 차이는 {difference:.6f}, 부모 단위 paired bootstrap 5,000회의 95% 구간은 [{low:.6f}, {high:.6f}]이다. "
        "구간은 학습된 모델 하나를 고정한 시험 불확실성이다. 모델 시드 73·107의 결과와 모든 특징 제거 비교도 원시 표에 남겼다. "
        "부스팅은 이 설정에서 시드에 따른 변동이 없을 수도 있으며, 시드 반복이 학습 자료 재표집을 대신하지 않는다.", "",
        "표 7 동일 모델의 외삽 첫 질문 평가", "",
        "| 시험 | 부모 | ML 초과 비용 | 깊이 3 초과 비용 | 차이의 95% 구간 |", "|---|---:|---:|---:|---:|"]
    for partition in ("test_size", "test_family"):
        ml = next(r for r in policies if r["split"] == partition and r["method"] == primary and r["seed"] == seed)
        baseline = next(r for r in policies if r["split"] == partition and r["method"] == "lookahead3")
        ci = next(r for r in comparisons if r["split"] == partition and r["baseline"] == "lookahead3" and r["seed"] == seed)
        section.append(f'| {partition} | {ml["parents"]} | {float(ml["first_regret"]):.6f} | {float(baseline["first_regret"]):.6f} | [{float(ci["ci_low"]):.6f}, {float(ci["ci_high"]):.6f}] |')
    section += ["", f"오프라인 정확 라벨 생성 시간은 {timing['exact_label_seconds']:.3f}초, 특징 추출은 {timing['feature_seconds']:.3f}초다. " +
        "첫 선택 시간은 특징 추출·벡터 구성·추론을 포함해 `policy_summary.csv`에, 모든 대상의 종료 비용 검산 시간은 별도로 저장했다. "
        "H_d 자체를 완료 질문 수로 보고하지 않는다. ML에는 전체 특징 추출 시간을 보수적으로 붙였으므로 부분 특징 전용 구현의 속도 우월성을 주장하지 않는다.", "",
        "### 8.4 구조 분석과 미완료 항목", "",
        "학습 부모에서 조건부 특징 L1 차이의 중앙값을 정해 시험에도 적용하는 기술 분석을 수행했다. "
        "효과 사례와 비용 변화가 없는 안전한 대조를 함께 저장했다. 같은 국소 Pasch 모양이라는 사실만으로 비용 효과의 크기나 첫 질문 충돌을 단정하지 않는다. "
        "이 분석은 조건부 구조의 연관성에 관한 것으로, 특정 요약의 인과 효과나 구조적 충분조건을 증명하지 않는다.", "",
        "| 항목 | 상태 | 범위 |", "|---|---|---|",
        "| 기존 14×8 유한 예시 | 재검산 완료 | 원본 JSON의 모든 필드 일치 |",
        "| 초기 요약 정책 하한 | 기존 증명 유지 | 해당 두 세계의 유한 하한 |",
        "| 통제 생성·교환·정확 비용 | 이번 실행 완료 | 위 합성 분포, 교환 없는 부모 포함 |",
        "| 초기 상태 ML·특징 제거·외삽 | 이번 실행 완료 | 불리한 결과도 보존 |",
        "| 비학습 전체 순차 정책 | 이번 실행 완료 | 실제 종료 비용의 정확 기대값 |",
        "| ML 전체 순차 정책 | 미실행 | 후속 상태 학습·검증 필요 |",
        "| 공통 구조의 일반 정리 | 미확립 | 기술 분석을 충분조건으로 해석하지 않음 |",
        "| 외부 데이터·응답 오류·불균등 목표 | 미실행 | 현실 일반화 주장 없음 |", "",
        f"계보·통제·모든 최적 트리·특징 라벨과 순열 감사를 통과했다(`{run.as_posix()}/audit.json`). "
        "결과 원본은 `occurrence.csv`, `policy_summary.csv`, `paired_comparisons.csv`, `model_seed_variation.csv`, `policy_subgroups.csv`, `structure_pairs.csv`이며 전체 검증 후보·모델·예측도 저장했다. "
        "그림은 아래와 같이 같은 원시 기록에서 생성한다.", "",
        f"![독립 시험 첫 질문 초과 비용]({report.as_posix()}/first_regret.png)", "",
        f"![변화 없는 쌍을 포함한 가족별 교환 효과]({report.as_posix()}/trade_effects.png)", ""]
    text = re.sub(r"## 8 결과 상태와 향후 결과표.*?(?=## 9 한계와 논의)", lambda _: "\n".join(section) + "\n", text, flags=re.S)
    text = text.replace("학습 효과가 없으면 구조 분석과 비학습 방법의 결과를 중심으로 결론을 수정한다.",
                        "이번 학습 비교는 8절의 모든 특징 제거·외삽 결과를 포함해 해석하며, 일반적인 ML 우월성으로 확대하지 않는다.")
    conclusion_text = ("## 10 결론\n\n"
        "기존의 14×8 유한 예시는 대상별 차수와 전체 질문 쌍 통계만으로 최적 첫 질문이 정해지지 않음을 보여준다. "
        "이번에는 이 검산과 별도로 PC의 실행 시간·메모리 예비 측정에 따라 합성 본실험을 고정하고 실행했다. "
        f"{summary['parents']:,}번의 부모 생성 시도와 {summary['pairs']:,}통제 쌍의 결과, 교환이 없는 부모와 비용 변화가 없는 사례를 모두 보존했다. "
        f"주 시험에서 선택 모델은 {conclusion}. "
        "이 사실은 실패한 학습 비교를 지우거나 새 특징으로 시험을 다시 맞추는 근거가 아니다.\n\n"
        "현재 결과는 지정한 합성 생성·교환 분포, 균등 목표와 정확 이진 응답에 한정된다. "
        "ML의 전체 순차 정책, 현실 자료의 효과, 고차 구조의 일반 정리는 아직 주장하지 않는다. "
        "통제 쌍과 정확 비용을 공개하여 조건부 구조가 유용한 범위와 단순 선행 탐색의 경쟁력을 후속 연구에서 검증할 수 있게 한다.\n\n")
    text = re.sub(r"## 10 결론.*?(?=## 참고문헌)", lambda _: conclusion_text, text, flags=re.S)
    text = text.replace("본실험의 생성기와 학습 파이프라인은 후속 구현 대상이다.", "본실험 구현과 실행 결과는 8절과 README를 참고한다.")
    output.write_text(text, encoding="utf-8")
    print(json.dumps(dict(paper=str(output), primary_model=primary, completed_pairs=summary["pairs"],
                          main_comparison=difference), ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", default="runs/main")
    parser.add_argument("--output", default="Twenty_Questions_Paper_Draft.md")
    args = parser.parse_args()
    update(args.run, args.output)
