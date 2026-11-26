"""Generate the complete self-contained manuscript from preserved measurements.

No experimental regeneration, fitting, data-split changes, or label edits.
"""
import csv
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import re
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'paper'
INPUTS = {}


def read(path):
    p = ROOT / path
    INPUTS[path] = sha256(p.read_bytes()).hexdigest()
    return json.loads(p.read_text(encoding='utf-8'))


def csvrows(path):
    p = ROOT / path
    INPUTS[path] = sha256(p.read_bytes()).hexdigest()
    with p.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def esc(text):
    return str(text).replace('_', r'\_').replace('%', r'\%').replace('&', r'\&')


def table(caption, label, fmt, header, rows, foot=''):
    return ('\\begin{table}[htbp]\n\\centering\\small\n'
            f'\\caption{{{caption}}}\\label{{{label}}}\n'
            f'\\begin{{tabular}}{{{fmt}}}\\toprule\n' + header + r'\\\midrule' + '\n' +
            '\n'.join(' & '.join(str(c) for c in row) + r'\\' for row in rows) +
            '\n\\bottomrule\\end{tabular}\n' + foot + '\n\\end{table}')


def witness_table(a, b, caption, label, original=False):
    assert len(a) == len(b)
    half = (len(a)+1)//2
    def rowtext(row):
        if isinstance(row, str):
            return r'$\{' + ','.join(row) + r'\}$'
        return r'$\{' + ','.join(map(str,row)) + r'\}$'
    rows=[]
    for i in range(half):
        left=[i+1,rowtext(a[i]),rowtext(b[i])]
        j=i+half
        right=[j+1,rowtext(a[j]),rowtext(b[j])] if j<len(a) else ['','','']
        rows.append(left+right)
    return table(caption,label,'rllrll',r'대상 & A & B & 대상 & A & B',rows)


def main():
    OUT.mkdir(exist_ok=True)
    occurrence=csvrows('runs/main/report/occurrence.csv')
    policies=csvrows('runs/main/report/policy_summary.csv')
    comparisons=csvrows('runs/main/report/paired_comparisons.csv')
    selection=read('runs/main/comparison/selection.json')
    splits=read('runs/main/splits.json')
    main_summary=read('runs/main/summary.json')
    timing=read('runs/main/report/timing.json')
    best38=read('runs/hubfree_search_v1/best.json')
    best18=read('runs/extremal_report_v1/best18.json')
    original=read('verification.json')
    expander=read('runs/hubfree_expander_cert_v1/summary.json')
    fiber=read('runs/extremal_v1/summary.json')
    pair=read('runs/extremal_pair_design_v1/summary.json')
    hub=read('runs/hubfree_search_v1/summary.json')
    independent=read('runs/final_independent_certificate_v1/summary.json')
    connected=read('followup_work/connected_glue_results/summary.json')
    root_connected=read('runs/followup_connected_v1/summary.json')
    root_gluing=read('runs/followup_root_gluing_v1/summary.json')
    pilot=read('runs/pilot_v2/summary.json')
    pilot_config=read('runs/pilot_v2/config.json')
    substitutions={}
    substitutions['SEARCH_TABLE']=table('적응적 발견 단계의 실제 계산량과 자원. OS peak는 프로세스 수명 값이다.',
        'tab:search','lrrrr','단계 & 패턴/성분 & 정확 평가 & 시간(s) & OS peak(MiB)',[
        ['고정 Gram',10,fiber['total_nodes'],f"{fiber['profile']['seconds']:.2f}",f"{fiber['profile']['lifetime_peak_rss_mb']:.2f}"],
        ['공통 배경',pair['proposals'],pair['unique_candidates'],f"{pair['profile']['seconds']:.2f}",f"{pair['profile']['lifetime_peak_rss_mb']:.2f}"],
        ['중심 질문 없음',hub['patterns'],hub['complete_worlds'],f"{hub['profile']['seconds']:.2f}",f"{hub['profile']['lifetime_peak_rss_mb']:.2f}"]])
    substitutions['EXPANDER_TABLE']=table('아홉 유한 골격의 구조·유리수 팽창 인증. 비용 열은 증명 경계이며 정확 DP 값이 아니다.',
        'tab:expanders','lrrrll','골격 & T & N & m & 대비 하한 & 대비 상한',[
        [esc(c['name'].replace('cubic-','').replace('-seed', '/s')),c['T'],c['n'],8*c['T'],
         '$'+c['regret_lower']+'$','$'+c['regret_upper']+'$'] for c in expander['cases']])
    pilot_rows=[]
    for i,(c,s) in enumerate(zip(pilot_config['cells'],pilot['cells'])):
        p=ROOT/f'runs/pilot_v2/cell-{i:02d}/worlds.jsonl'
        INPUTS[p.relative_to(ROOT).as_posix()]=sha256(p.read_bytes()).hexdigest()
        worlds=[json.loads(line) for line in p.read_text(encoding='utf-8').splitlines()]
        exact=[w['solver_profile']['seconds'] for w in worlds]
        baselines=[w['baseline_profile']['seconds'] for w in worlds if w.get('baseline_profile')]
        pilot_rows.append([c['family'],f"${c['n']}\\times{c['m']}$",f"{s['completed_worlds']}/{s['worlds']}",
            f'{np.quantile(exact,.95):.4f}',f'{np.quantile(baselines,.95):.4f}' if baselines else '--',
            f"{s['profile']['lifetime_peak_rss_mb']:.1f}"])
    substitutions['PILOT_TABLE']=table('예비 실행의 크기별 계산 비용. 미완결 세계의 시간도 한도 도달 시간으로 포함한다.',
        'tab:pilot','lrrrrr','가족 & 크기 & 완료 세계 & 정확 p95(s) & 정책 검산 p95(s) & OS peak(MiB)',pilot_rows)
    substitutions['OCCURRENCE_TABLE']=table('사전 고정 합성 실험의 교환 결과. 충돌은 두 최적 첫 질문 집합이 서로소인 경우다.',
        'tab:occurrence','lrrrrrr',r'가족 & 크기 & 시도 & 완료 쌍 & 평균 $|\Delta\Opt|$ & 충돌 쌍 & 비용차 0',[
        [r['family'],f"${r['n']}\\times{r['m']}$",r['attempted_parents'],r['complete_pairs'],
         f"{float(r['absolute_delta']):.6f}",r['disjoint_count'],r['zero_cost_effect_count']] for r in occurrence])
    substitutions['ZERO_PAIRS']=str(sum(int(r['zero_cost_effect_count']) for r in occurrence))
    aliases={'random':'무작위','information_gain':'정보이득','lookahead2':'깊이 2','lookahead3':'깊이 3','oracle':'정확 최적'}
    method_order=['random','information_gain','lookahead2','lookahead3','oracle','boosting_base',
        'boosting_base_conditional','boosting_base_search','boosting_all','ridge_base','ridge_base_conditional','ridge_base_search','ridge_all']
    by_method={r['method']:r for r in policies if r['split']=='test' and r['seed'] in ('fixed','41')}
    def model_label(m):
        if m in aliases:return aliases[m]
        family,block=m.split('_',1)
        name=('Boost' if family=='boosting' else 'Ridge')+' / '+{'base':'base','base_conditional':'+cond','base_search':'+search','all':'all'}[block]
        return r'\textbf{'+name+'}' if m==selection['primary_model'] else name
    prows=[]
    for method in method_order:
        r=by_method[method]
        prows.append([model_label(method),f"{float(r['first_regret']):.6f}",f"{100*float(r['optimal_probability']):.3f}\\%",
            f"{float(r['full_policy_mean']):.6f}" if r['full_policy_mean'] else '미평가',f"{1000*float(r['root_seconds_mean']):.3f}"])
    substitutions['POLICY_TABLE']=table('주 시험 179부모·358세계의 결과. 굵은 모델은 시험 전에 검증으로 선택했다. ML 전체 정책은 미평가다.',
        'tab:policy','lrrrr',r'방법/특징 & 첫 질문 regret & argmin 확률 & 전체 평균 비용 & 첫 선택(ms)',prows)
    ood=[]
    for split,label in [('test','주 시험'),('test_size','크기 외삽'),('test_family','가족 외삽')]:
        r=next(x for x in comparisons if x['split']==split and x['seed']=='41' and x['baseline']=='lookahead3')
        a=next(x for x in policies if x['split']==split and x['method']=='boosting_all' and x['seed']=='41')
        l=next(x for x in policies if x['split']==split and x['method']=='lookahead3')
        ood.append([label,r['parents'],f"{float(a['first_regret']):.6f}",f"{float(l['first_regret']):.6f}",
            f"{float(r['mean_difference']):.6f}",'$['+f"{float(r['ci_low']):.6f},{float(r['ci_high']):.6f}"+']$'])
    substitutions['OOD_TABLE']=table('선택 모델과 깊이 3의 사전 지정 비교. 차이는 ML 빼기 깊이 3이며 음수가 ML에 유리하다.',
        'tab:ood','lrrrrl',r'분할 & 부모 & ML regret & 깊이 3 & 차이 & paired 95\% 구간',ood)
    substitutions['BOUND_POINTS']=''.join(f"({c['n']},{float(Fraction(c['regret_lower'])):.12f})" for c in expander['cases'] if Fraction(c['regret_lower'])>0)
    plot_methods=['information_gain','lookahead2','lookahead3','boosting_all','ridge_all']
    points=[]
    for i,m in enumerate(plot_methods):
        r=by_method[m]; y=float(r['first_regret']); low=float(r['first_regret_ci_low']); high=float(r['first_regret_ci_high'])
        points.append(f'({i},{y:.12f}) += (0,{high-y:.12f}) -= (0,{y-low:.12f})')
    substitutions['ML_FIGURE']=r'''\begin{figure}[htbp]\centering
\begin{tikzpicture}\begin{axis}[width=.9\linewidth,height=5.9cm,ymin=0,ymax=.011,
ylabel={Initial-question regret},xtick={0,1,2,3,4},
xticklabels={IG,Depth 2,Depth 3,Boost/all,Ridge/all},grid=major]
\addplot[only marks,mark=*,blue!70!black,error bars/.cd,y dir=both,y explicit] coordinates {
'''+ '\n'.join(points)+r'''
};\end{axis}\end{tikzpicture}
\caption{주 시험의 첫 질문 regret와 부모 재표집 95\% 구간. 이 그림의 개별 평균 구간 중첩으로 주 비교를 판정하지 않고, 표~\ref{tab:ood}의 paired 차이 구간을 사용한다. 무작위 정책과 모든 ablation은 표~\ref{tab:policy}에 남겼다.}\label{fig:ml}
\end{figure}'''
    substitutions['ORIGINAL_WITNESS_TABLE']=witness_table(original['A']['rows'],original['B']['rows'],
        '원래 검산 예시의 전체 행. 질문 인덱스는 1부터 시작한다.','tab:original')
    substitutions['WITNESS18_TABLE']=witness_table(best18['a']['rows'],best18['b']['rows'],
        '선택한 18×9 쌍의 전체 행. 양쪽 최초 greedy 질문은 유일한 $q_3$다.','tab:witness18')
    substitutions['WITNESS38_TABLE']=witness_table(best38['bad']['graph']['rows'],best38['good']['graph']['rows'],
        '선택한 38×18 쌍의 전체 행. A는 손실 세계, B는 대조 세계다.','tab:witness38')
    substitutions['REPRO_TABLE']=r'''\begin{table}[htbp]\centering\footnotesize
\caption{보존 자료의 경로와 재현 범위.}\label{tab:repro}
\begin{tabularx}{\linewidth}{lY}\toprule
경로&내용\\\midrule
\code{verification.json}&원래 14×8의 정확 비용·트리·통제 검사\\
\code{runs/main/}&모든 부모·세계·교환·모델·예측·분할·감사\\
\code{runs/pilot_v2/}&규모 결정용 예비 시간·메모리·미완결\\
\code{runs/extremal_v1/}&고정 Gram 탐색의 모든 방문·교환 간선\\
\code{runs/extremal_pair_design_v1/}&공통 배경 제안과 수락·거절\\
\code{runs/extremal_analysis_v1/}&18×9 독립 DP와 14×8 증폭 기반\\
\code{followup_work/connected_glue_results/}&49개 포트·전체 행렬 DP 완료/미완결\\
\code{runs/followup_root_gluing_v1/}&공유 질문 구성과 512 CUT 독립 대조\\
\code{runs/hubfree_search_v1/}&포트 패턴·720세계·38×18 선택 반례\\
\code{runs/hubfree_expander_cert_v1/}&아홉 골격·전체 행렬·유리수 인증\\
\code{runs/final_independent_certificate_v1/}&독립 DP·정점 삭제·민감도·정수 인증\\
\code{final_work/hubfree_agent_proven_results/}&장식 기반의 상수와 작은 음성 사례\\
\code{runs/novelty_audit_v1/}&문헌 스냅샷·검색·직접 환원 검사\\\bottomrule
\end{tabularx}\end{table}'''
    template_path=ROOT/'paper_work/manuscript.tex.in'
    INPUTS[template_path.relative_to(ROOT).as_posix()]=sha256(template_path.read_bytes()).hexdigest()
    template=template_path.read_text(encoding='utf-8')
    for key,value in substitutions.items():
        marker='@@'+key+'@@'; assert template.count(marker)==1,marker
        template=template.replace(marker,value)
    assert not re.findall(r'@@\w+@@',template)
    template=re.sub(r'\\emph\{([^{}]*[가-힣][^{}]*)\}',lambda m:r'\textbf{'+m.group(1)+'}',template)
    # Sanity checks against scientific records, not only against rendered text.
    assert main_summary['parents']==1400 and main_summary['pairs']==1223 and main_summary['completed_worlds']==2446
    assert sum(int(r['complete_pairs']) for r in occurrence)==1223
    assert best38['summary']['contrast_exact']=='13/76' and best38['summary']['robust_exact']=='3/19'
    assert best18['contrast_exact']=='2/9'
    assert independent['positive_single_deletion_contrast_count']==18
    assert sum(x['component_certified_exhausted'] for x in fiber['fibers'])==8
    assert connected['all_port_cases']==49
    assert sum(r['status']=='complete' for r in connected['finite_statuses'])==8
    assert root_connected['structural_graphs_checked']==14 and root_gluing['all_cut_subsets_checked']==512
    assert by_method['boosting_all']['parents']=='179'
    assert selection['primary_model']=='boosting_all'
    refs=set(re.findall(r'\\bibitem\{([^}]+)\}',template))
    cited={k for group in re.findall(r'\\cite\{([^}]+)\}',template) for k in group.split(',')}
    assert cited <= refs, cited-refs
    (OUT/'main.tex').write_text(template,encoding='utf-8')
    evidence=dict(version='1.0',language='Korean with English title and abstract',
        parents=1400,pairs=1223,worlds=2446,zero_cost_pairs=int(substitutions['ZERO_PAIRS']),
        primary_model=selection['primary_model'],main_parents=179,extremal_worlds=2534,hubfree_worlds=720,
        selected18_regret_contrast='2/9',selected38_regret_contrast='13/76',
        selected38_min_tie_contrast='3/19',cubic_asymptotic_regret_contrast='N/578+O(1)',
        theorem_scope='uniform greedy ties, not arbitrary ties',large_dp_claim=False,
        main_paired_difference=next(r for r in comparisons if r['split']=='test' and r['seed']=='41' and r['baseline']=='lookahead3'),
        expander_cases=expander['cases'],references=sorted(refs),input_sha256=INPUTS,
        latex_sha256=sha256((OUT/'main.tex').read_bytes()).hexdigest())
    (OUT/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'README.md').write_text('''# 완성 연구 원고

`main.tex`는 그림·표·참고문헌을 모두 포함하는 자체 완결 LaTeX 원고다.
Overleaf에서는 XeLaTeX와 TeX Live 2025 이상을 선택한다. 그림 외부 파일이나 BibTeX 실행은 필요 없다.

본문은 한국어이며 영문 제목과 초록을 포함한다. 실제 측정과 정확 유리수 값, 수학적 경계, 미실행 항목을 구분한다.
`evidence.json`은 표·그림 좌표에 사용한 원시 파일의 해시를 보존한다.

로컬 재생성: `.venv/Scripts/python.exe paper_work/build_manuscript.py`
로컬 컴파일: `.tools/tectonic/tectonic.exe -X compile paper/main.tex --outdir output/pdf --keep-logs`

기존 v0.3 Markdown·옛 PDF·DOCX와 실험 기록은 보존한다. 새 완성본의 기준은 이 LaTeX와 새 PDF다.
''',encoding='utf-8')
    print(json.dumps(dict(latex=str(OUT/'main.tex'),characters=len(template),
        input_files=len(INPUTS),zero_cost_pairs=int(substitutions['ZERO_PAIRS']),references=len(refs)),ensure_ascii=False))


if __name__=='__main__':
    main()
