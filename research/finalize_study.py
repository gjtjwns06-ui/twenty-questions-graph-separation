#!/usr/bin/env python3
"""Verify immutable artifacts and record the completed scope; no model refitting."""
from datetime import datetime
import json
from pathlib import Path
import shutil
from tq.io import digest, read_jsonl, write_json, now


def main():
    out = Path("runs/main")
    config = json.loads((out / "config.json").read_text(encoding="utf-8"))
    frozen = json.loads(Path(config["freeze_receipt"]).read_text(encoding="utf-8"))
    assert digest("configs/main.json") == frozen["config_sha256"]
    assert digest(out / "config.json") == frozen["config_sha256"]
    assert all(digest(path) == value for path, value in frozen["source_sha256"].items())
    assert digest("archive/Twenty_Questions_Paper_Draft_v0.1.md") == frozen["inputs_sha256"]["Twenty_Questions_Paper_Draft.md"]
    original = json.loads(Path("verification.json").read_text(encoding="utf-8"))
    recomputed = json.loads(Path("verification_recomputed.json").read_text(encoding="utf-8"))
    assert original == recomputed
    for folder in [out, out / "report"]:
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        assert all(digest(folder / path) == value for path, value in manifest.items())
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    audit = json.loads((out / "audit.json").read_text(encoding="utf-8"))
    selection = json.loads((out / "comparison/selection.json").read_text(encoding="utf-8"))
    models = json.loads((out / "comparison/status.json").read_text(encoding="utf-8"))
    assert audit["passed"]
    assert all(digest(out / "comparison" / path) == value for path, value in models["model_files_sha256"].items())
    assert datetime.fromisoformat(frozen["frozen"]) < datetime.fromisoformat(summary["started"])
    assert datetime.fromisoformat(selection["frozen"]) < datetime.fromisoformat(models["completed"])
    worlds = read_jsonl(out / "worlds.jsonl")
    parents = read_jsonl(out / "parents.jsonl")
    pairs = read_jsonl(out / "pairs.jsonl")
    for world in worlds:
        assert world["matrix"] == [[int(q in row) for q in range(world["m"])] for row in world["rows"]]
    assert len(parents) == summary["parents"] == 1400
    assert len(pairs) == summary["pairs"] == 1223
    assert len(worlds) == summary["worlds"] == 2446
    completed = datetime.fromisoformat(audit["completed"])
    start = datetime.fromisoformat(summary["started"])
    resource = dict(generation=summary["profile"], candidate_training=selection["training_profile"],
        generation_to_final_audit_seconds=(completed - start).total_seconds(),
        note="Candidate training includes 20 candidates and validation. Additional-seed fits and test inference follow separately.")
    write_json(out / "resources.json", resource)
    status = dict(finalized=now(), witness="Recomputed; all scientific JSON fields identical",
        pilot="Completed; original and cold-cache repeat preserved, not pooled",
        frozen_before_main=True, source_and_config_unchanged=True,
        main=dict(parent_attempts=len(parents), controlled_pairs=len(pairs), worlds=len(worlds),
            exact_completed=summary["completed_worlds"], incomplete=summary["worlds"] - summary["completed_worlds"],
            zero_cost_change_pairs=sum(p["abs_delta_optimal"] == 0 for p in pairs),
            audit_passed=True, feature_labels_checked=audit["feature_labels_checked"]),
        model_selection="Validation only; boosting_all retained despite lower test point estimates for some other models",
        primary_result="Difference from lookahead3 includes zero in the 95% parent bootstrap interval; no confirmed advantage",
        not_performed=["Full sequential learned policy", "External factual data", "Nonuniform targets or noisy answers"],
        not_established=["A new general structural theorem", "Population-uniform sampling of a Gram fiber", "General ML superiority"],
        paper="Twenty_Questions_Paper_Draft.md version 0.2; original Markdown archived, original PDF/DOCX remain version 0.1")
    write_json("EXPERIMENT_STATUS.json", status)
    log = f"""# 실행 기록과 해석

`AGENT_START.md`와 기존 논문 초안을 읽고 별도 Python 환경에서 작업했다. 기존 예시는 재검산한 JSON의 모든 필드가 일치했다. 원본의 줄바꿈·인코딩 차이 때문에 파일 해시 일치와 JSON 값 일치를 구분한다.

설계 고정: {frozen['frozen']}. 본실험 생성 시작: {summary['started']}. 생성 종료: {summary['finished']}. 검증 모델 선택 고정: {selection['frozen']}. 시험 예측 종료: {models['completed']}. 최종 감사 종료: {audit['completed']}.

본실험 전 7개 단위 검사와 전체 개발 실행 감사를 통과했다. 본실험에서 1,400번의 독립 부모 생성 시도, 1,223쌍, 2,446세계의 정확 계산을 완료했다. 교환 없는 부모 177개와 최적 비용 변화가 없는 쌍 1,114개를 포함해 모두 보존했다. 최종 감사는 1,223쌍·2,446최적 트리·26,916질문 특징 라벨을 점검했고, 9개 크기·가족 층의 이름 순열 및 모든 선택 모델 예측 검사도 통과했다.

본실험 생성·정확 계산·기준선·특징·원시 저장 단계의 실제 시간은 {summary['profile']['seconds']:.3f}초, OS 최고 RSS는 {summary['profile']['lifetime_peak_rss_mb']:.3f}MiB다. 예비 p95 합 추정 316.049초보다 약 42% 길었으며, 이 추정은 작은 예비 표본이고 파일 I/O·동형 검사·학습 등을 별도로 둔 값이다. 표본 수를 줄이거나 미완결을 숨기지 않았다.

20개 후보 적합과 검증 단계는 {selection['training_profile']['seconds']:.3f}초, 이 프로세스 수명 중 OS 최고 RSS는 {selection['training_profile']['lifetime_peak_rss_mb']:.3f}MiB다. 후자는 약 522.8MiB의 자료 로딩·라이브러리 기초 메모리를 포함한다. 추가 시드 적합과 시험 추론 시간은 별도 예측 기록에 있다. 생성 시작부터 최종 감사까지 약 {(completed-start).total_seconds():.1f}초이며 설치·구현·예비 실행은 포함하지 않는다.

주 시험의 ML 선택은 boosting_all이며 179부모/358세계다. 첫 질문 regret은 0.001435 대 깊이 3의 0.001920, 차이 -0.000485의 부모 paired bootstrap 95% 구간은 [-0.001144, 0.000116]으로 0을 포함한다. 주·외삽 시험 모두 깊이 3 대비 구간이 0을 포함한다. 선택 모델의 특징 포함 평균 첫 선택 시간은 약 34.0ms, 깊이 3은 약 1.55ms였다. 이 구현에서 계산 시간의 이점은 없었다.

Ridge base→base_conditional 및 base_search→all처럼 시험 손실이 증가한 비교도 보존했다. 일부 미선택 Ridge가 시험 점추정에서 더 낮았어도 시험을 보고 주 모델을 바꾸지 않았다. 세 학습 시드의 예측은 이 결정적 설정에서 같았으며, 기계 오차 수준의 표준편차를 재학습 불확실성 증거로 해석하지 않는다. 학습 자료 재표집에 따른 변동은 이번에 측정하지 않았다.

교환 충돌률이 0인 조건에서 단순 bootstrap 구간이 0으로 퇴화할 수 있다. 이는 모집단 충돌 확률이 0이라는 증거가 아니며, 보편적 부재를 주장하지 않는다. 구조 분석은 사전 지정한 기술적 연관성 분석이며 충분조건·인과 효과·새 일반 정리는 미확립이다.

기존 PDF·DOCX는 본실험 전 스냅샷으로 남겼다. Markdown의 초록·결과·결론은 `update_paper.py`로 실제 표에서 갱신했고 미실행 항목도 명시했다. 통제·학습·집계 소스와 설정은 고정 영수증의 해시 그대로다. 논문 갱신·최종 산출물 정리는 결과 후처리이며 학습이나 시험 지표를 변경하지 않는다.
"""
    Path("reports/EXECUTION_LOG.md").write_text(log, encoding="utf-8")
    for path in [Path("update_paper.py"), Path("finalize_study.py"), Path("README.md"),
                 Path("reports/PILOT_REPORT.md"), Path("reports/EXPERIMENT_DESIGN.md"),
                 Path("reports/EXECUTION_LOG.md"), Path("reports/VALIDATION.md")]:
        dest = out / "source/postprocessing" / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
    manifest = {str(p.relative_to(out)): digest(p) for p in sorted(out.rglob("*"))
                if p.is_file() and p.name != "ARTIFACT_MANIFEST.json"}
    write_json(out / "ARTIFACT_MANIFEST.json", dict(created=now(), files=manifest,
        paper_sha256=digest("Twenty_Questions_Paper_Draft.md"),
        status_sha256=digest("EXPERIMENT_STATUS.json"),
        paper_updater_sha256=digest("update_paper.py")))
    print(json.dumps(dict(finalized=True, files=len(manifest), main_audit=audit["passed"])))


if __name__ == "__main__":
    main()
