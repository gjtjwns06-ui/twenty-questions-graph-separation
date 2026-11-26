from __future__ import annotations
from collections import defaultdict
import csv
import json
from pathlib import Path
import numpy as np
from .features import flatten
from .io import read_jsonl, write_json, now, digest


def write_csv(path, rows):
    if not rows:
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with Path(path).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def bootstrap(values, count, seed):
    a = np.asarray(values, dtype=float)
    if not len(a):
        return [None, None]
    rng = np.random.default_rng(seed)
    # Batched draws bound memory while preserving every parent, including zeros.
    draws = np.concatenate([a[rng.integers(len(a), size=(min(250, count - k), len(a)))].mean(axis=1)
                            for k in range(0, count, 250)])
    return [float(x) for x in np.quantile(draws, [.025, .975])]


def aggregate_parents(rows, field):
    grouped = defaultdict(list)
    for row in rows:
        if row.get(field) is not None:
            grouped[row["parent_id"]].append(row[field])
    return {parent: float(np.mean(values)) for parent, values in grouped.items()}


def report(out, config):
    out = Path(out)
    dest = out / "report"
    dest.mkdir(parents=True, exist_ok=True)
    worlds = read_jsonl(out / "worlds.jsonl")
    world_map = {w["world_id"]: w for w in worlds}
    parents = read_jsonl(out / "parents.jsonl")
    pairs = read_jsonl(out / "pairs.jsonl")
    split = json.loads((out / "splits.json").read_text(encoding="utf-8"))["parents"]
    selection = json.loads((out / "comparison" / "selection.json").read_text(encoding="utf-8"))
    predictions = read_jsonl(out / "comparison" / "predictions.jsonl")
    count, seed = config["bootstrap_replicates"], config["bootstrap_seed"]
    occurrences = []
    conditions = sorted({(p["family"], p["n"], p["m"], p["cohort"]) for p in parents})
    for family, n, m, cohort in conditions:
        ps = [p for p in parents if (p["family"], p["n"], p["m"], p["cohort"]) == (family, n, m, cohort)]
        ids = {p["parent_id"] for p in ps}
        selected = [p for p in pairs if p["parent_id"] in ids]
        complete = [p for p in selected if p["complete"]]
        values = aggregate_parents(complete, "argmin_disjoint")
        ci = bootstrap(list(values.values()), count, seed)
        candidates = sum(p["candidate_count"] for p in ps)
        valid = sum(p["valid_candidate_count"] for p in ps)
        occurrences.append(dict(family=family, n=n, m=m, cohort=cohort, attempted_parents=len(ps),
            parents_with_pasch=sum(p["candidate_count"] > 0 for p in ps),
            parents_with_valid_trade=sum(p["selected_count"] > 0 for p in ps),
            candidates=candidates, valid_candidates=valid, candidate_acceptance=valid / candidates if candidates else None,
            pairs=len(selected), complete_pairs=len(complete),
            complete_parents=len(values), signed_delta=np.mean([p["delta_optimal"] for p in complete]) if complete else None,
            absolute_delta=np.mean([p["abs_delta_optimal"] for p in complete]) if complete else None,
            disjoint_count=sum(p["argmin_disjoint"] for p in complete),
            disjoint_rate=float(np.mean(list(values.values()))) if values else None,
            disjoint_ci_low=ci[0], disjoint_ci_high=ci[1],
            changed_count=sum(p["argmin_changed"] for p in complete),
            zero_cost_effect_count=sum(p["abs_delta_optimal"] == 0 for p in complete)))
    write_csv(dest / "occurrence.csv", occurrences)
    rows = []
    for world in worlds:
        if world["exact"]["status"] != "complete":
            continue
        partition = split[world["parent_id"]]["split"]
        if not (partition.startswith("test") or partition == "validation"):
            continue
        common = dict(world_id=world["world_id"], parent_id=world["parent_id"], split=partition,
                      family=world["family"], n=world["n"], m=world["m"])
        for method, metric in world["baselines"].items():
            rows.append(dict(**common, method=method, seed="fixed", **metric,
                             total_root_seconds=metric["root_seconds"]))
        rows.append(dict(**common, method="oracle", seed="fixed", first_regret=0., optimal_probability=1.,
                         policy_mean=world["exact"]["optimal_mean"], policy_regret=0.,
                         total_root_seconds=world["solver_profile"]["seconds"]))
    for p in predictions:
        w = world_map[p["world_id"]]
        rows.append(dict(p, method=p["model"], family=w["family"], n=w["n"], m=w["m"],
                         total_root_seconds=p["root_seconds_with_features"]))
    write_csv(dest / "policy_world_metrics.csv", [{k: v for k, v in r.items() if k not in
              ("predicted_regrets", "root_questions")} for r in rows])
    summaries = []
    for partition in sorted({r["split"] for r in rows}):
        for method, model_seed in sorted({(r["method"], str(r["seed"])) for r in rows if r["split"] == partition}):
            chosen = [r for r in rows if r["split"] == partition and r["method"] == method and str(r["seed"]) == model_seed]
            regret = aggregate_parents(chosen, "first_regret")
            hit = aggregate_parents(chosen, "optimal_probability")
            policy = aggregate_parents(chosen, "policy_mean")
            ci = bootstrap(list(regret.values()), count, seed)
            summaries.append(dict(split=partition, method=method, seed=model_seed, parents=len(regret),
                worlds=len(chosen), first_regret=float(np.mean(list(regret.values()))),
                first_regret_ci_low=ci[0], first_regret_ci_high=ci[1],
                optimal_probability=float(np.mean(list(hit.values()))),
                full_policy_mean=float(np.mean(list(policy.values()))) if policy else None,
                root_seconds_mean=float(np.mean([r["total_root_seconds"] for r in chosen])),
                root_seconds_p95=float(np.quantile([r["total_root_seconds"] for r in chosen], .95))))
    write_csv(dest / "policy_summary.csv", summaries)
    # Paired uncertainty for the preselected ML, keeping the trained model fixed.
    comparisons = []
    for partition in sorted({r["split"] for r in rows if r["split"].startswith("test")}):
        for model_seed in config["model_seeds"]:
            ml_rows = [r for r in rows if r["split"] == partition and r["method"] == selection["primary_model"]
                       and r["seed"] == model_seed]
            ml = aggregate_parents(ml_rows, "first_regret")
            for baseline in ("information_gain", "lookahead2", "lookahead3"):
                base = aggregate_parents([r for r in rows if r["split"] == partition and r["method"] == baseline], "first_regret")
                ids = sorted(set(ml) & set(base))
                difference = [ml[p] - base[p] for p in ids]
                ci = bootstrap(difference, count, seed)
                comparisons.append(dict(split=partition, model=selection["primary_model"], seed=model_seed,
                    baseline=baseline, parents=len(ids), mean_difference=float(np.mean(difference)),
                    ci_low=ci[0], ci_high=ci[1], direction="Negative favors ML"))
    write_csv(dest / "paired_comparisons.csv", comparisons)
    # Training-seed variation is reported separately from fixed-model bootstrap CIs.
    seed_rows = []
    for partition, method in sorted({(r["split"], r["method"]) for r in summaries if r["seed"] != "fixed"}):
        values = [r["first_regret"] for r in summaries if r["split"] == partition and r["method"] == method]
        seed_rows.append(dict(split=partition, method=method, seeds=len(values), mean=float(np.mean(values)),
                              standard_deviation=float(np.std(values)), min=float(min(values)), max=float(max(values))))
    write_csv(dest / "model_seed_variation.csv", seed_rows)
    subgroups = []
    for partition, family, n, method, s in sorted({(r["split"], r["family"], r["n"], r["method"], str(r["seed"])) for r in rows}):
        chosen = [r for r in rows if (r["split"], r["family"], r["n"], r["method"], str(r["seed"])) == (partition, family, n, method, s)]
        values = aggregate_parents(chosen, "first_regret")
        subgroups.append(dict(split=partition, family=family, n=n, method=method, seed=s, parents=len(values),
                              first_regret=float(np.mean(list(values.values())))))
    write_csv(dest / "policy_subgroups.csv", subgroups)
    structure = structure_analysis(out, pairs, split, config)
    figures(dest, summaries, occurrences, config)
    failures = [dict(world_id=w["world_id"], parent_id=w["parent_id"], family=w["family"], n=w["n"], m=w["m"],
                     **w["exact"]) for w in worlds if w["exact"]["status"] != "complete"]
    write_json(dest / "incomplete_worlds.json", failures)
    timing = dict(exact_label_seconds=sum(w["solver_profile"]["seconds"] for w in worlds),
                  feature_seconds=sum(w.get("feature_profile", {}).get("seconds", 0) for w in worlds),
                  all_target_baseline_evaluation_seconds=sum(w.get("baseline_profile", {}).get("seconds", 0) for w in worlds),
                  memory_sampling="5 ms sampled phase RSS; may miss short spikes. OS peak is process lifetime.",
                  full_ml_policy="Not performed; root models have no successor-state training.")
    write_json(dest / "timing.json", timing)
    make_report(out, dest, config, occurrences, summaries, comparisons, parents, worlds, pairs, failures, selection, timing, structure)
    write_json(dest / "manifest.json", {p.name: digest(p) for p in sorted(dest.iterdir()) if p.is_file() and p.name != "manifest.json"})


def structure_analysis(out, pairs, split, config):
    data = read_jsonl(out / "features.jsonl")
    by_world = defaultdict(dict)
    for r in data:
        by_world[r["world_id"]][r["feature"]["question"]] = r["feature"]
    records = []
    for pair in pairs:
        if not pair["complete"]:
            continue
        a, b = by_world[pair["a"]], by_world[pair["b"]]
        distance = max(sum(abs(x - y) for x, y in zip(a[q]["conditional"].values(), b[q]["conditional"].values())) for q in a)
        search_distance = max(abs(a[q]["search"]["H3"] - b[q]["search"]["H3"]) for q in a)
        records.append(dict(parent_id=pair["parent_id"], pair_id=pair["pair_id"], split=split[pair["parent_id"]]["split"],
                            conditional_l1=distance, h3_max_difference=search_distance,
                            zero_cost_effect=pair["abs_delta_optimal"] == 0, **{k: pair[k] for k in
                            ("family", "n", "m", "abs_delta_optimal", "argmin_disjoint", "argmin_changed")}))
    discovery = [r for r in records if r["split"] == "train"]
    threshold = float(np.median([r["conditional_l1"] for r in discovery]))
    groups = []
    for partition in sorted({r["split"] for r in records}):
        for high in (False, True):
            chosen = [r for r in records if r["split"] == partition and (r["conditional_l1"] > threshold) == high]
            groups.append(dict(split=partition, above_train_median=high, pairs=len(chosen),
                               mean_abs_delta=float(np.mean([r["abs_delta_optimal"] for r in chosen])) if chosen else None,
                               disjoint_rate=float(np.mean([r["argmin_disjoint"] for r in chosen])) if chosen else None,
                               zero_cost_effect_count=sum(r["zero_cost_effect"] for r in chosen)))
    # Effect and null examples selected by ID order, not by effect magnitude.
    examples = {}
    for name, condition in [("cost_effect", lambda r: not r["zero_cost_effect"]),
                             ("no_cost_effect", lambda r: r["zero_cost_effect"]),
                             ("disjoint", lambda r: r["argmin_disjoint"]),
                             ("overlapping_optima", lambda r: not r["argmin_disjoint"])]:
        examples[name] = next((r for r in sorted(records, key=lambda r: r["pair_id"])
                               if r["split"] == "train" and condition(r)), None)
    result = dict(train_median_conditional_l1=threshold, groups=groups, discovery_examples=examples,
                   interpretation="Descriptive association only; no new sufficient structural theorem established.")
    write_json(out / "report" / "structure.json", result)
    write_csv(out / "report" / "structure_pairs.csv", records)
    return result


def figures(dest, summaries, occurrences, config):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    seed = str(config["model_seeds"][0])
    chosen = [r for r in summaries if r["split"] == "test" and r["seed"] in ("fixed", seed) and r["method"] != "oracle"]
    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    ax.barh([r["method"] for r in chosen], [r["first_regret"] for r in chosen], color="#3a6c9e")
    ax.set_xlabel("Mean first-question regret (questions); equal parent weights")
    ax.set_title("Held-out initial states; uniform tie handling")
    for ext in ("png", "pdf"):
        fig.savefig(dest / f"first_regret.{ext}", dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    for family in sorted({r["family"] for r in occurrences}):
        chosen = [r for r in occurrences if r["family"] == family]
        axes[0].plot([r["n"] for r in chosen], [r["absolute_delta"] for r in chosen], "o-", label=family)
        axes[1].plot([r["n"] for r in chosen], [r["disjoint_rate"] for r in chosen], "o-", label=family)
    axes[0].set_ylabel("Mean absolute optimal-cost change")
    axes[1].set_ylabel("Disjoint optimal-root sets / complete pairs")
    for ax in axes:
        ax.set_xlabel("Objects")
        ax.set_ylim(bottom=0)
        ax.legend()
    for ext in ("png", "pdf"):
        fig.savefig(dest / f"trade_effects.{ext}", dpi=180)
    plt.close(fig)


def make_report(out, dest, config, occurrences, summaries, comparisons, parents, worlds, pairs, failures, selection, timing, structure):
    seed = config["model_seeds"][0]
    primary = selection["primary_model"]
    test = next(r for r in summaries if r["split"] == "test" and r["method"] == primary and r["seed"] == str(seed))
    comparison = next(r for r in comparisons if r["split"] == "test" and r["seed"] == seed and r["baseline"] == "lookahead3")
    evidence = ("개선 방향이며 고정 모델의 paired bootstrap 구간이 0 아래이다." if comparison["ci_high"] < 0 else
                "수치상 개선 방향이지만 구간이 0을 포함한다." if comparison["mean_difference"] < 0 else
                "개선되지 않았다. 이 결과와 모든 비교를 그대로 보존했다.")
    lines = ["# 본실험 실행 보고서", "", f"생성 시각: {now()}. 설정: `configs/main.json`. 원시 자료: `{out.as_posix()}`.", "",
        "## 완료 범위", "", "기존 논문의 14×8 예시를 재검산했으며 `verification_recomputed.json`은 동봉 파일과 모든 필드가 일치했다. 이 예시는 학습·빈도 계산에 넣지 않았다.", "",
        f"이번 본실험에서 독립 생성 시도 {len(parents)}부모, 교환 쌍 {len(pairs)}개, 세계 {len(worlds)}개를 보존했다. 정확 계산 미완결은 {len(failures)}세계다. 교환이 없는 부모도 분모와 원시 기록에 남겼다.", "",
        "## 통제 교환", "", "자연 표집과 교환 삽입 표집의 발생률을 합치지 않는다. 아래 충돌률은 유효한 교환을 균등하게 하나 선택하고 정확 계산이 완료된 쌍에 조건부인 비율이다.", "",
        "| 가족 | 대상×질문 | 시도 부모 | 유효 교환 부모 | 완료 쌍 | 평균 절대 비용차 | 서로소 최적집합 | 비용차 0인 쌍 |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in occurrences:
        lines.append(f'| {r["family"]} | {r["n"]}×{r["m"]} | {r["attempted_parents"]} | {r["parents_with_valid_trade"]} | {r["complete_pairs"]} | {r["absolute_delta"]:.6f} | {r["disjoint_count"]} ({r["disjoint_rate"]:.2%}) | {r["zero_cost_effect_count"]} |')
    lines += ["", "## 독립 시험과 모델 비교", "", f"검증 자료에서 선택한 주 모델은 `{primary}`다. 시험에는 {test['parents']}부모/{test['worlds']}세계가 있다. 주 지표는 부모 안에서 세계를 평균한 첫 질문 초과 비용이며, 동점은 균등 무작위 기대값이다.", "",
        "| 방법 | 첫 질문 초과 비용 | 최적집합 선택 확률 | 전체 정책 평균 비용 | 첫 선택 시간(ms) |", "|---|---:|---:|---:|---:|"]
    for r in summaries:
        if r["split"] == "test" and r["seed"] in ("fixed", str(seed)):
            policy = f'{r["full_policy_mean"]:.6f}' if r["full_policy_mean"] is not None else "미평가"
            lines.append(f'| {r["method"]} | {r["first_regret"]:.6f} | {r["optimal_probability"]:.3%} | {policy} | {r["root_seconds_mean"] * 1000:.3f} |')
    lines += ["", f"주 모델 − 깊이 3 탐색의 첫 질문 초과 비용 차이는 {comparison['mean_difference']:.6f}, 부모 paired bootstrap 95% 구간은 [{comparison['ci_low']:.6f}, {comparison['ci_high']:.6f}]이다. {evidence}", "",
        "이 구간은 학습된 모델 하나를 고정한 시험 부모 재표집의 불확실성이다. 재학습 시드 변동은 `model_seed_variation.csv`에 따로 기록했다. 모든 특징 제거 결과, 후보 검증 결과, 모델 시드, 예측과 손실을 보존했다. 여러 비교에 대한 유의성 탐색으로 해석하지 않는다.", "",
        "## 비용·누출 점검", "", f"오프라인 정확 라벨 계산은 총 {timing['exact_label_seconds']:.3f}초, 특징 추출은 {timing['feature_seconds']:.3f}초였다. ML 시간은 벡터 구성·추론과 전체 특징 추출을 포함한다. 기준선은 방법마다 빈 탐색 캐시에서 시작한다. 전체 정책 비용은 선행 탐색 점수가 아니라 매 상태에서 같은 정책을 다시 선택한 실제 완료 비용의 정확 기대값이다.", "",
        "정확한 weighted Gram 동형 검사로 질문 이름 순열까지 묶어 분할했다. WL 해시는 후보 묶음에만 사용했다. 이분 그래프가 동형이면 Gram도 동형이므로 이 규칙은 전체 세계 동형의 분할 누출도 막는다. 예비실험과 같은 Gram 그룹은 시험에서 제외했다. 행·열 순열과 통제 불변량은 별도 감사에서 확인한다.", "",
        "## 구조 분석과 남은 일", "", f"학습 부모에서 조건부 특징 L1 차이의 중앙값 {structure['train_median_conditional_l1']:.6f}를 정하고 같은 규칙을 시험에 적용했다. 결과는 `structure.json`과 `structure_pairs.csv`에 있다. 비용 변화가 없는 대조도 포함했다. 특징 차이와 비용 차이의 연관성은 충분조건이나 인과 증명이 아니다.", "",
        "초기 상태만 학습한 ML의 전체 순차 정책, 새로운 일반 정리, 외부 사실 데이터, 불균등 목표·응답 오류는 미실행 또는 미확립이다. 큰 규모 정확 계산의 완료 편향, 작은 예비 표본에 근거한 규모 결정, 제한된 합성 분포도 해석에 포함한다.", "",
        "그림은 `first_regret.png/pdf`, `trade_effects.png/pdf`, 표 원본은 이 폴더의 CSV이다. `python experiment.py report --config configs/main.json --out runs/main`으로 원시 기록에서 다시 생성할 수 있다."]
    (dest / "MAIN_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
