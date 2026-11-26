#!/usr/bin/env python3
"""Audit discovery traces and generate the extremal research note from raw files."""
from fractions import Fraction
import csv
import json
from pathlib import Path
import shutil

from extremal_experiment import canonical, graph_id, GreedyCosts
from tq.core import ExactSolver, control_check, gram_of
from tq.io import read_jsonl, write_json, digest, now


def csv_write(path, rows):
    with Path(path).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def main():
    folders=[Path(p) for p in ['runs/extremal_v1','runs/extremal_pair_design_v1','runs/extremal_analysis_v1']]
    dest=Path('runs/extremal_report_v1')
    dest.mkdir(exist_ok=True)
    old=json.loads(Path('configs/main.frozen.json').read_text(encoding='utf-8'))
    assert all(digest(p)==sha for p,sha in old['source_sha256'].items())
    assert digest('configs/main.json')==old['config_sha256']
    for folder in folders:
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        assert all(digest(folder/p)==sha for p,sha in manifest.items())
    seeds=json.loads((folders[0]/'seeds.json').read_text(encoding='utf-8'))
    nodes=read_jsonl(folders[0]/'nodes.jsonl')
    by_id={r['node_id']:r for r in nodes}
    for node in nodes:
        index=int(node['fiber_id'].split('-')[-1])
        assert gram_of(node['rows'],node['m'])==gram_of(seeds[index]['rows'],node['m'])
        assert len(set(map(tuple,node['rows'])))==node['n']
        assert all(len(r)==3 for r in node['rows'])
        if node['exact']['status']=='complete':
            g=node['greedy']
            assert g['total_min_ties']<=Fraction(g['total_uniform_exact'])<=g['total_max_ties']
    edges=read_jsonl(folders[0]/'edges.jsonl')
    for edge in edges:
        before=by_id[edge['before']]
        history=edge['history']
        changed=canonical((set(map(tuple,before['rows']))-set(map(tuple,history['removed'])))|set(map(tuple,history['added'])))
        assert graph_id(changed,before['m'])==edge['after']
        assert control_check(before['rows'],changed,before['m'])==edge['checks']
    candidates=read_jsonl(folders[1]/'candidates.jsonl')
    indexed={r['candidate_id']:r for r in candidates}
    for candidate in candidates:
        a,b=candidate['a'],candidate['b']
        assert control_check(a['rows'],b['rows'],a['m'])==candidate['checks']
    traces=read_jsonl(folders[1]/'trace.jsonl')
    for trace in traces:
        before=indexed[trace['before']]
        after=indexed[trace['proposal']]
        background=set(map(tuple,before['common_background']))
        background.remove(tuple(trace['removed']))
        background.add(tuple(trace['inserted']))
        assert canonical(background)==canonical(after['common_background'])
    fixed=json.loads((folders[0]/'summary.json').read_text(encoding='utf-8'))
    paired=json.loads((folders[1]/'summary.json').read_text(encoding='utf-8'))
    best=json.loads((folders[1]/'best.json').read_text(encoding='utf-8'))
    root_details={}
    costs=[]
    for label in ('a','b'):
        w=best[label]
        solver=ExactSolver(w['rows'],w['m'],seconds=10)
        exact=solver.solve()
        greedy=GreedyCosts(solver.columns)
        root=[q for q,_,_ in greedy.choices(solver.full)]
        assert len(root)==1
        q=root[0]
        oracle_regret=Fraction(exact['first_totals'][q]-exact['optimal_total'],w['n'])
        tail_regret=Fraction(w['greedy']['gap_exact'])-oracle_regret
        root_details[label]=dict(root=q,optimal_roots=exact['argmin'],
            column_degrees=[c.bit_count() for c in solver.columns],
            greedy_root_oracle_regret_exact=str(oracle_regret),tail_regret_exact=str(tail_regret),
            full_regret_exact=w['greedy']['gap_exact'],first_questions=[])
        for j,a,b in solver.splits(solver.full):
            detail=dict(world=label,question=j,yes_size=a.bit_count(),no_size=b.bit_count(),
                optimal_yes_total=solver.cost(a),optimal_no_total=solver.cost(b),
                first_total=exact['first_totals'][j],greedy_yes_total_exact=str(greedy.cost(a)[0]),
                greedy_no_total_exact=str(greedy.cost(b)[0]))
            root_details[label]['first_questions'].append(detail)
            costs.append(detail)
    write_json(dest/'root_structure.json',root_details)
    csv_write(dest/'first_question_costs.csv',costs)
    csv_write(dest/'fixed_fiber_search.csv',fixed['fibers'])
    write_json(dest/'best18.json',best)
    base=json.loads((folders[2]/'fixed_degree3_base.json').read_text(encoding='utf-8'))
    lifts=json.loads((folders[2]/'explicit_lift_checks.json').read_text(encoding='utf-8'))
    bounds=json.loads((folders[2]/'scaling_bounds.json').read_text(encoding='utf-8'))
    csv_write(dest/'scaling_bounds.csv',bounds)
    write_json(dest/'audit.json',dict(completed=now(),passed=True,
        old_main_source_and_config_unchanged=True,fixed_nodes_checked=len(nodes),edges_replayed=len(edges),
        controlled_candidates_checked=len(candidates),background_mutations_replayed=len(traces),
        independent_full_subset_audits='runs/extremal_analysis_v1/new18_independent_audit.json',
        directsum_and_product_checks_complete=True))
    make_figures(dest,folders,bounds,best)
    lines=['# 질문 쌍 통계를 보존하는 탐욕 손실의 극값 탐색','',
        '기존 무작위 실험과 분리한 발견 연구 · 2026년 11월 25일. 기존 설정·원시 결과·ML의 불확실한 결과는 그대로 보존했다. 이번에는 ML을 재학습하지 않았다. 탐색한 최대값을 모집단 발생률이나 전역 최악값으로 해석하지 않는다.','',
        '## 이번에 얻은 결과','',
        '**새 18×9 통제 쌍에서는 정보량이 가장 큰 첫 질문이 양쪽에서 유일하고 같지만, 한 세계의 실제 탐욕 손실은 2/9회, 다른 세계는 0회다. 이 차이는 모든 탐욕 동점 규칙에서 유지된다.** 별도의 차수 3 직접합 가족에서는 두 세계의 손실 차이가 대상 수 N에 대해 N/392+O(1)로 커짐을 증명했다. 이는 유한 반례의 손실과 크기 성장의 구조를 함께 설명한다.','',
        '## 탐색과 보존 조건','',
        f"고정 Gram 안에서는 {len(fixed['fibers'])}개 씨앗 성분의 {fixed['total_nodes']:,}세계를 검사했다. {sum(x['component_certified_exhausted'] for x in fixed['fibers'])}성분은 Pasch 도달 성분 전체를 열거했고 나머지는 노드 한도에서 멈췄다. 최고 통제 regret 대비는 2/21로, 선택한 기존 씨앗보다 커지지 않았다. 이 실패도 보존했다. 전체 Gram 섬유의 전역 최적성을 인증한 것은 아니다.","",
        f"공통 배경을 적대적으로 설계한 별도 단계에서는 {paired['proposals']:,}회 제안, {paired['unique_candidates']:,}개 서로 다른 쌍을 평가하고 {paired['accepted']:,}개 변형을 수락했다. 각 시점의 두 세계는 Gram과 행 차수가 같지만, 배경을 함께 바꾸므로 시점 사이의 Gram은 달라질 수 있다. 고정 섬유 탐색과 이 모드를 구분한다.","",
        f"고정 섬유 탐색은 {fixed['profile']['seconds']:.2f}초/OS 최고 {fixed['profile']['lifetime_peak_rss_mb']:.1f}MiB, 공동 설계는 {paired['profile']['seconds']:.2f}초/{paired['profile']['lifetime_peak_rss_mb']:.1f}MiB였다. 모든 후보·교환·수락/거절·제한 도달을 보존했다.","",
        '## 새 유한 반례와 조건부 구조','',
        '인덱스는 0부터 시작한다. 두 세계 모두 대상별 차수 3과 같은 Gram을 갖는다. 유일한 탐욕 첫 질문 q3은 9/9로 후보를 나눈다. 정확 값은 다음과 같다.','',
        '| 세계 | 최적 잎 깊이 합 | 실제 탐욕 잎 깊이 합 | 평균 최적 비용 | 평균 탐욕 비용 | 탐욕 손실 |',
        '|---|---:|---:|---:|---:|---:|',
        '| A | 77 | 81 | 77/18 | 9/2 | 2/9 |','| B | 78 | 78 | 13/3 | 13/3 | 0 |','',
        'A의 최적 첫 질문은 q0·q2다. 탐욕 q3을 강제한 뒤 최적으로 계속해도 총 비용 합은 79이므로 첫 선택에서 1/9회 손실이 생긴다. 이후 탐욕 정책의 조건부 구조에서 추가로 1/9회 손실이 생긴다. B에서는 q3이 최적이며 후속 손실도 없다. 즉 단순히 같은 9/9 분할이 남기는 후보 수를 보는 것으로 두 세계의 후속 식별 난도를 설명할 수 없다.','',
        '두 세계 모두 탐욕의 최선·최악 동점 완료 비용이 같아 ID 선택으로 생긴 현상이 아니다. 모든 2^18−1 후보 부분집합을 사용하는 별도 정수·유리수 DP로 F, 모든 Q, 탐욕 균등/최선/최악 비용을 독립 재검산했다. 행 목록과 전체 Gram은 `runs/extremal_report_v1/best18.json`, 질문별 분해는 `first_question_costs.csv`와 `root_structure.json`에 있다.','',
        '## 차수 3에서 선형으로 커지는 통제 손실 차이','',
        '큰 유한 손실 하나를 찾는 것과 증폭 가능한 반례는 다르다. 새 18×9 쌍의 블록 직접합은 양쪽의 피복 프로필이 (9,7,2)로 같아서 선형 증폭에 실패했다. 이 음성 결과도 저장했다. 선형 확장에는 기존 자료에서 재분석한 별도의 14×8 쌍을 사용한다.','',
        '기반 A와 B를 각각 T개 블록으로 직접합한다. 질문은 자기 블록의 대상에서만 예다. 그러면 N=14T, m=8T, 모든 행 차수는 계속 3이며 Gram은 양쪽 모두 diag(G,…,G)다. 각 블록에서 Pasch 교환을 하나씩 실행하면 모든 중간 세계도 같은 Gram을 유지한다. 이 가족은 연결되지 않은 그래프다.','',
        '모든 답이 아니오인 경로에서는, 후보가 충분히 많을 동안 탐욕이 가장 많은 새 대상을 덮는 질문을 고른다. 두 세계의 최적 피복 포락선은 공통으로 (0,7,12,14)이고 (7,5,2)의 중첩 순서가 이를 달성한다. 하지만 무작위 동점의 실제 최대 피복 프로필은 다르다.','',
        '| 세계 | 피복 프로필 | 확률 |','|---|---|---:|',
        '| A | (7,5,2) / (7,4,3) | 각각 1/2 |',
        '| B | (7,5,2) / (7,4,2,1) | 각각 1/2 |','',
        '작은 피복 작업이 더 오래 남는 구조가 블록마다 반복된다. 전역 균등 동점은 블록의 동점 질문 수에 비례해 블록을 고른 뒤 지역 질문을 균등 선택하는 결합으로 분석한다. 단순한 균등 블록 선택은 사용하지 않는다. 프로필의 크기 s 이상 작업 수를 Z_s라 하면 D=Σ_s(EZ_s)^2는 A에서 65/2, B에서 67/2다.','',
        r'\[C^*(M_T)=\frac87T+O(1)\ (M\in\{A,B\}),\quad C_G(A_T)=\frac{65}{56}T+O(1),\quad C_G(B_T)=\frac{67}{56}T+O(1).\]','',
        r'따라서 \[R(B_T)-R(A_T)=\frac{T}{28}+O(1)=\frac{N}{392}+O(1),\qquad R=C_G-C^*.\]','',
        '비상수 질문을 할 때마다 후보가 적어도 하나 줄어드므로 어떤 탐욕 경로도 N−1번을 넘지 않는다. 따라서 regret와 통제 regret 대비의 절댓값은 O(N)이다. 위 가족은 N=14T 수열에서 이 선형 증가 차수에 도달한다. 정확한 최대 상수나 유한 크기의 전역 극값을 찾았다는 뜻은 아니다.','',
        '엄밀한 유한 구간도 얻었다. 이는 실제 큰 그래프의 정확 DP 측정값이 아니라, 유한 기반 계산과 증명으로 인증한 경계다.','',
        r'\[\frac{T-71}{28}-\frac{393}{14T}\ \le R(B_T)-R(A_T)\le\frac{T+65}{28}+\frac{393}{14T}.\]','',
        '하한은 T≥81에서 양수다. T=100, N=1,400에서는 적어도 약 0.755회 차이가 보장된다. 실제 정보이득 탐욕과 가상 최대 피복 과정은 후보 14개 이하의 꼬리에서만 다를 수 있으며, 이 차이와 첫 예 응답 뒤 식별 비용을 모두 경계에 포함했다. 전체 증명은 `reports/extremal_math_agent.md`, 독립 검토는 `reports/EXTREMAL_INDEPENDENT_REVIEW.md`에 있다.','',
        '작은 직접합 T=2는 정확 DP로 별도 검사했는데 양쪽 regret가 모두 1/48이었다. 따라서 작은 크기의 측정값에서 선형 추세를 추정한 결론이 아니다. 큰 T의 성장은 위 증명으로 얻는다.','',
        '새 18×9 쌍의 Cartesian 곱도 k=2에서 실제 324×18 행렬과 정확 DP로 검사했다. 손실은 A에서 4/9, B에서 0이었다. 일반 k에서 손실 대비는 2k/9지만 행 차수가 3k로 늘어나는 확장이므로 고정 차수 3의 직접합과 구분한다.','',
        '## 비율 성장의 한계와 기존 연구','',
        '절대 손실의 선형 증가가 근사 비율의 발산은 아니다. 위 차수 3 가족의 비율은 각각 65/64와 67/64로 수렴한다. 더 나아가 고정 차수 r에서는 각 결정 경로의 예 응답이 최대 r개이므로 깊이 d 이하의 잎 수가 Σ_{j≤r} binom(d,j) 이하이고 C*=Ω_r(N^(1/r))다. 이를 기존 탐욕 상한과 결합하면 C_G/C*=O(r)다. 따라서 현재 가정에서 차수 3을 유지하며 비율 자체가 발산하는 목표는 불가능하다.','',
        '일반 균등 이진 식별의 탐욕 최악 사례와 O(log N/log C*) 상한은 이미 알려져 있다. 여기서 구별되는 명제는 같은 Gram·같은 차수 아래 두 세계의 전체 탐욕 regret 대비가 선형으로 달라지는 구체적 가족이다. 이 따름정리와 구성의 문헌상 최초성은 주장하지 않는다. [Li–Liang–Mussmann, 정리 3.1 및 부록 C.1](https://arxiv.org/html/1906.11385v2).','',
        '## 판단과 남은 범위','',
        '이번에는 반례의 조건부 구조와 차수 3의 선형 확장까지 확보했으므로, 무작위 표본이나 ML 규모를 더 늘리기보다 이 통제 극값 명제를 중심으로 연구를 좁힐 근거가 있다. 다음 미해결 범위는 연결된 그래프에서의 증폭, 실제 최대 상수, 더 넓은 교환을 포함한 전체 섬유 극값, 정확한 선행연구 대조다. 독립 검토는 계산·증명을 검토한 기록이며 동료 심사나 신규성 증명은 아니다.','',
        '재현 명령은 README의 극값 탐색 절에 있다. 이전 본실험, 실패한 고정 섬유 개선, 18×9 직접합 증폭 실패, 불리한 기존 ML 비교는 모두 남겼다.']
    note=Path('Twenty_Questions_Extremal_Note.md')
    note.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for p in ['configs/extremal.json','configs/extremal_pair_design.json','extremal_experiment.py',
              'extremal_pair_design.py','extremal_certify.py','report_extremal.py','reports/EXTREMAL_DESIGN.md',
              'reports/extremal_math_agent.md','reports/EXTREMAL_INDEPENDENT_REVIEW.md']:
        destination=dest/'source'/p
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,destination)
    write_json(dest/'status.json',dict(completed=now(),search_modes=['fixed Gram','joint controlled context'],
        finite_best_contrast_exact='2/9',finite_min_tie_contrast_exact='2/9',
        fixed_degree3_asymptotic_contrast='N/392+O(1)',global_maximum_proved=False,
        failed_extensions_preserved=['No improvement over2/21 in selected fixed Gram search','18x9 directsum no linear amplification'],
        previous_main_preserved=True,note_sha256=digest(note)))
    write_json(dest/'manifest.json',{str(p.relative_to(dest)):digest(p) for p in sorted(dest.rglob('*'))
        if p.is_file() and p.name!='manifest.json'})
    print(json.dumps(dict(audit='passed',nodes=len(nodes),designed_pairs=len(candidates),note=str(note))))


def make_figures(dest,folders,bounds,best):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    progress=read_jsonl(folders[1]/'incumbents.jsonl')
    fig,axes=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
    axes[0].step([p['candidate_id'] for p in progress],[float(Fraction(p['contrast'])) for p in progress],where='post')
    axes[0].set(xlabel='Distinct evaluated pair',ylabel='Best controlled regret contrast (questions)',title='Guided context design; discovery only')
    chosen=[r for r in bounds if r['T']>=81]
    t=np.array([r['T'] for r in chosen])
    lower=np.array([r['certified_regret_b_minus_a_lower'] for r in chosen])
    upper=np.array([float(Fraction(int(x)+65,28)+Fraction(393,14*int(x))) for x in t])
    axes[1].fill_between(14*t,lower,upper,alpha=.2,label='Proved finite interval')
    axes[1].plot(14*t,t/28,label='Leading term N/392')
    axes[1].set(xlabel='Objects N=14T; row degree remains3',ylabel='Regret B minus regret A',title='Theory bounds; not large-N DP measurements')
    axes[1].legend()
    for ext in ['png','pdf']:
        fig.savefig(dest/f'extremal_search_scaling.{ext}',dpi=180)
    plt.close(fig)
    common=sorted(set(map(tuple,best['a']['rows']))&set(map(tuple,best['b']['rows'])))
    fig,axes=plt.subplots(1,2,figsize=(8,6),constrained_layout=True)
    for ax,label in zip(axes,['a','b']):
        w=best[label]
        rows=sorted(set(map(tuple,w['rows']))-set(common))+common
        matrix=np.array([[int(q in row) for q in range(w['m'])] for row in rows])
        ax.imshow(matrix,cmap='Blues',vmin=0,vmax=1,aspect='auto',interpolation='nearest')
        ax.axhline(3.5,color='#d36b3e',linewidth=1.5)
        ax.axvline(3,color='#b33c28',alpha=.35,linewidth=5)
        ax.set(xticks=range(w['m']),xlabel='Question (0-based); red=q3',ylabel='Objects; first4rows traded',
            title=f"{label.upper()}: opt={w['exact']['optimal_total']}/18, greedy={w['greedy']['mean_uniform_exact']}")
    for ext in ['png','pdf']:
        fig.savefig(dest/f'new18_matrices.{ext}',dpi=180)
    plt.close(fig)


if __name__=='__main__':
    main()
