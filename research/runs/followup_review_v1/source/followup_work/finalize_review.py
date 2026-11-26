#!/usr/bin/env python3
"""Verify follow-up certificates and generate the current research review."""
from __future__ import annotations
from fractions import Fraction
from pathlib import Path
import argparse
import csv
import json
import shutil
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tq.core import ExactSolver,columns_of
from tq.io import digest,write_json,now


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def table(path,rows):
    with Path(path).open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def check_post_certificate():
    base=load('runs/extremal_analysis_v1/fixed_degree3_base.json')
    certificate=load('followup_work/proof_audit_certificates.json')
    checked={}
    for label in ['a','b']:
        rows=base[label]['rows']
        cols=columns_of(rows,8)
        solver=ExactSolver(rows,8,seconds=30)
        states=certificate['minimum_post'][label]['states']
        for mask_text,record in states.items():
            mask=int(mask_text)
            choices=[]
            for col in cols:
                yes=mask&col
                if yes:
                    no=mask^yes
                    tail=states[str(no)]['value'] if no else 0
                    choices.append(solver.cost(yes)+tail)
            assert record['value']==min(choices)
            yes=mask&cols[record['question']]
            assert record['yes_mask']==yes and record['no_mask']==mask^yes
            assert record['yes_cost']==solver.cost(yes)
        assert states[str((1<<14)-1)]['value']==19
        checked[label]=dict(states_checked=len(states),minimum_post=19,
                            method='All Bellman alternatives checked with independent reachable-state F')
    tail=[]
    for s in range(1,14):
        h=s.bit_length()-1
        lmin=s*h+2*(s-(1<<h))
        lmax=(s*s+s-2)//2
        tail.append(lmax+min(s,7)-lmin)
    assert max(tail)==48
    assert Fraction(38-33,28)-Fraction(97,14*38)<=0<Fraction(39-33,28)-Fraction(97,14*39)
    assert Fraction(64-62,29)-Fraction(97,29*32)<=0<Fraction(66-62,29)-Fraction(97,29*33)
    return dict(post=checked,max_tail_leafsum_difference=48,
        disconnected_sufficient_T=39,connected_bridge_sufficient_S=33)


def main(out_path):
    out=Path(out_path)
    out.mkdir(parents=True,exist_ok=False)
    # The original experiments are immutable; check every original stored artifact.
    old_main=load('runs/main/ARTIFACT_MANIFEST.json')
    assert all(digest(Path('runs/main')/p)==sha for p,sha in old_main['files'].items())
    assert digest('Twenty_Questions_Paper_Draft.md')==old_main['paper_sha256']
    old_extreme=load('EXTREMAL_ARTIFACT_MANIFEST.json')
    assert all(digest(p)==sha for p,sha in old_extreme['files'].items())
    assert digest('Twenty_Questions_Extremal_Note.md')==old_extreme['note_sha256']
    old_sources=load('configs/main.frozen.json')['source_sha256']
    assert all(digest(p)==sha for p,sha in old_sources.items())
    reviewed=check_post_certificate()
    root_bridge=load('runs/followup_connected_v1/summary.json')
    root_glue=load('runs/followup_root_gluing_v1/summary.json')
    assert root_bridge['connected_same_gram_degree3'] and root_glue['passed']
    finite=load('followup_work/connected_glue_results/finite_connected_checks.json')
    incomplete=[]
    finite_rows=[]
    for r in finite:
        result=r['result']
        exact=result['exact']
        if exact['status']!='complete':
            assert exact['optimal_total'] is None and exact['first_totals'] is None
            incomplete.append(dict(base=r['base'],copies=r['copies'],world=r['label'],status=exact['status']))
        finite_rows.append(dict(base=r['base'],copies=r['copies'],world=r['label'],n=r['n'],m=r['m'],
            status=exact['status'],optimal_mean_exact=str(Fraction(exact['optimal_total'],r['n'])) if exact['status']=='complete' else '',
            greedy_mean_exact=result.get('greedy',{}).get('mean_uniform_exact',''),
            regret_exact=result.get('greedy',{}).get('gap_exact','')))
    table(out/'finite_connected_costs.csv',finite_rows)
    bounds=[]
    for t in [1,2,20,38,39,54,60,81,100,128,256]:
        bounds.append(dict(family='disconnected14',copies=t,N=14*t,
            lower_exact=str(Fraction(t-33,28)-Fraction(97,14*t)),
            upper_exact=str(Fraction(t+27,28)+Fraction(97,14*t)),
            kind='proved regret contrast; not measured exact cost'))
    for s in [9,20,32,33,54,100,128,256]:
        bounds.append(dict(family='paired_connector',copies=s,N=29*s,
            lower_exact=str(Fraction(2*s-62,29)-Fraction(97,29*s)),
            upper_exact=str(Fraction(2*s+56,29)+Fraction(97,29*s)),
            kind='proved regret contrast; not measured exact cost'))
    for t in [1,2,30,59,60,100,128,256]:
        bounds.append(dict(family='shared18_port3',copies=t,N=18*t,
            lower_exact=str(Fraction(t-59,18)-Fraction(1,9*t)),
            upper_exact=str(Fraction(t+59,18)+Fraction(1,9*t)),
            kind='proved OPTIMAL COST contrast, NOT regret contrast'))
    table(out/'proved_finite_bounds.csv',bounds)
    write_json(out/'incomplete_cases.json',incomplete)
    write_json(out/'certificate_review.json',dict(completed=now(),old_artifacts_unchanged=True,
        original_main_files_verified=len(old_main['files']),original_extremal_files_verified=len(old_extreme['files']),
        strengthened_bounds=reviewed,root_bridge=root_bridge,root_gluing=root_glue,
        agent_finite_completed=len(finite)-len(incomplete),agent_finite_incomplete=len(incomplete),
        formal_proof_assistant_used=False,method='Direct mathematical audit plus independently implemented finite certificate checks'))
    make_plot(out)
    write_note(out)
    # Preserve the old README checksum before adding the new current-work pointer.
    archive=Path('archive/README_extremal_v1.md')
    if not archive.exists():
        assert digest('README.md')==old_extreme['readme_sha256']
        shutil.copy2('README.md',archive)
    assert digest(archive)==old_extreme['readme_sha256']
    readme=Path('README.md')
    text=readme.read_text(encoding='utf-8')
    marker='현재 후속 검토는 [선행연구·연결 확장·증명 감사](Twenty_Questions_Followup_Review.md)에 정리했다.'
    if marker not in text:
        text=text.replace('# Twenty Questions 통제 그래프 실험\n','# Twenty Questions 통제 그래프 실험\n\n'+marker+'\n',1)
        text+='\n## 후속 연결성·증명 재현\n\n새 연결 그래프 인증은 `.\\.venv\\Scripts\\python.exe followup_work/root_connected_certificate.py --out runs/new_connected_check`로 새 폴더에 생성한다. `root_gluing_review.py`는 독립된 행 집합 열거와 모든 512개 기반 CUT 검사를 수행하며 기본 결과 폴더가 있으면 중단한다. 기존 기록은 삭제하지 않는다. 세부 실행·실패한 강화 시도와 모든 원시 인증은 `followup_work/`와 후속 노트에서 연결한다.\n'
        readme.write_text(text,encoding='utf-8')
    sources=list(Path('reports/followup').glob('*'))+[p for p in Path('followup_work').glob('*.py')]
    sources+=[Path('Twenty_Questions_Followup_Review.md'),Path('README.md')]
    for p in sources:
        if not p.is_file():continue
        destination=out/'source'/p
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,destination)
    status=dict(completed=now(),literature='No identical full theorem found in reviewed primary sources; novelty unconfirmed',
        connected_degree3_same_gram=True,regret_contrast_connected='2N/841+O(1)',
        additional_connected_no_new_objects_regret='N/784+O(1), other world regretO(1)',
        connected_optimal_cost_contrast='N/324+O(1), cost ratio tends17/16; NOT regretcontrast',
        proof_audit='No fatal flaw found; stronger finite bounds independently checked',
        sufficient_positive_size_disconnected_N=546,sufficient_positive_size_bridge_N=957,
        all_tie_linear_claim=False,linear_regret_scope='Uniform random tie handling is essential for these families',
        unresolved=['Literature novelty','Bounded question degree','2-connected families','Sharp constants','All-tie robust linear separation at degree3'],
        previous_results_preserved=True,new_incomplete_cases=len(incomplete))
    write_json('FOLLOWUP_STATUS.json',status)
    roots=[Path('runs/followup_connected_v1'),Path('runs/followup_root_gluing_v1'),out,
           Path('followup_work/connected_glue_results')]
    files={str(p):digest(p) for root in roots for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in str(p)}
    for p in sorted(Path('followup_work').glob('*')):
        if p.is_file():files[str(p)]=digest(p)
    for p in sorted(Path('reports/followup').glob('*')):
        if p.is_file():files[str(p)]=digest(p)
    write_json('FOLLOWUP_ARTIFACT_MANIFEST.json',dict(created=now(),files=files,
        review_sha256=digest('Twenty_Questions_Followup_Review.md'),status_sha256=digest('FOLLOWUP_STATUS.json'),
        current_readme_sha256=digest('README.md'),prior_readme_preserved_as=str(archive)))
    print(json.dumps(dict(completed=True,files=len(files),old_artifacts_preserved=True,certificate_checks=reviewed)))


def write_note(out):
    text=r'''# 동일 통계 식별 그래프: 선행연구·연결 확장·증명 직접 검토

검토일: 2026년 11월 25일. 기존 무작위 실험·극값 탐색·논문 및 원시 기록을 바꾸지 않은 후속 연구다. 목표는 균등, 답은 정확한 이진값, 질문 비용은 1이다. R=C_G−C*는 실제 종료까지의 탐욕 초과 비용이다. 아래 선형 regret 명제의 동점은 **매 상태의 균등 무작위**다.

## 결론

1. 조사한 1차 문헌에서 동일한 전체 정리는 찾지 못했다. 다만 Pasch, 같은 CUT/Gram의 구별 불가능성, 피복 지연·복사본 증폭, 제한된 yes 경로는 선행 맥락이다. 최초성은 아직 미확인이다.
2. 연결성·행 차수 3·같은 전체 Gram을 동시에 유지하면서 선형 regret 대비를 얻었다. 새 대상을 추가하지 않는 구성도 있고, 소수의 연결 대상을 넣어 대비 계수를 높인 구성도 있다.
3. 기존 증명을 직접 검토하고 유한 인증을 독립 확인했다. 결론을 무너뜨리는 오류는 찾지 못했으며, 보수적인 꼬리와 후속 비용 경계를 강화했다. 하지만 모든 동점 규칙에 통하는 선형 regret 명제로 확대할 수는 없다.

## 1. 무엇이 이미 알려졌는가

| 기존 연구 | 겹치는 수학적 부분 | 이번 정리와 구별할 부분 |
|---|---|---|
| Li–Liang–Mussmann, SODA 2020 | 균등 이진 식별의 탐욕 상한·하한, MSSC 연결 | 같은 Gram 쌍의 정량적 regret 대비를 요구하지 않음 |
| Feige–Lovász–Tetali | 최초 피복 지연, greedy 분석, 복사본을 이용한 증폭 | 완전 식별의 같은 Gram 쌍을 분석하지 않음 |
| 조합 설계의 Pasch/twin triple systems | 같은 쌍 출현을 갖는 서로 다른 삼중계 | 적응형 식별 비용을 분석하지 않음 |
| Chakrabarty–Liao, ESA 2026 | 같은 모든 CUT 값을 갖는 홀수 균일 하이퍼그래프; 3-uniform에서는 Pasch 쌍 | 알려진 세계의 숨은 간선을 찾는 greedy regret와 다른 oracle 문제 |
| bounded-ones prefix/search codes | 한 경로의 yes 수 제한과 평균 깊이 | 같은 Gram에서의 식별 regret 대비는 아님 |

차수 3 행을 하이퍼간선으로 보면


\[
\operatorname{CUT}_M(S)=\frac12\sum_{i\in S,j\notin S}G_{ij},\qquad
G_{ij}=d_i+d_j-\operatorname{CUT}_M(\{i,j\}),\quad d_i=\operatorname{CUT}_M(\{i\}).
\]

즉 이 조건에서는 **같은 Gram과 같은 모든 CUT profile이 동치**다. 따라서 단순한 복원 불가능성을 새 기여로 내세우면 안 된다. [ESA 2026 공식 원문, 관찰 31·정리 32](https://drops.dagstuhl.de/storage/00lipics/lipics-vol388-esa2026/html/LIPIcs.ESA.2026.150/LIPIcs.ESA.2026.150.html).

현재의 기여 후보는 이 알려진 동등성 제약 안에서 **실제 적응형 식별 regret와 최적 비용의 정량적 분리**를 보이는 명시적 연결 가족이다. 검색 범위와 정확한 조건별 대조는 `reports/followup/LITERATURE_AUDIT.md`에 있다. 문헌상 부재나 최초성을 증명한 것은 아니다. 철회된 정리를 사용하지 않았다.

## 2. 기존 증명 직접 검토와 강화

기존 직접합의 포락선·프로필·균등 동점 스케줄러·곱 가법성·prefix-free 하한을 다시 확인했다. 전역 균등 동점은 블록별 동점 질문 수에 비례해 블록을 선택하는 결합이어야 한다. 단순한 균등 블록 선택은 다른 정책이다. 가상 최대 피복 비용과 실제 식별 비용도 같다고 놓지 않았다.

### 2.1 국소 후속 비용의 양의 하한

기반 블록의 정확 잎 깊이 합을 F(S)라 하고

\[
U(\varnothing)=0,\qquad
U(S)=\min_{q:S\cap M_q\ne\varnothing}
\left[F(S\cap M_q)+U(S\setminus M_q)\right]
\]

을 계산하면 두 세계 모두 U(V)=19다. 이는 질문 비용을 제외하고 첫 yes 이후의 후속 비용만 센 값이다. 독립 정수 DP와 모든 Bellman 대안 검사를 통과했다. 따라서

\[
V_{\min}(T)+\frac{19}{14}-\frac1{14T}
\le C^*(M_T)\le V_{\min}(T)+\frac{34}{14}
\]

로 기존 최적 비용 하한을 높였다.

### 2.2 꼬리 잎 깊이 합 오차

후보가 14개 이상이면 최대 yes 수 7 이하인 질문의 entropy 순서는 신규 피복 수 순서와 같다. 다른 것은 13개 이하의 꼬리뿐이다. s개 잎을 갖는 proper 이진 트리의 깊이 합은

\[
L_{\min}(s)=s\lfloor\log_2s\rfloor+2(s-2^{\lfloor\log_2s\rfloor}),\qquad
L_{\max}(s)=\frac{s^2+s-2}{2}
\]

사이다. 가상 피복에는 최대 한 개의 상수 yes 노드가 있고 그 아래 대상은 min(s,7)개 이하다. 따라서 꼬리 깊이 합 차이는 최대

\[
\max_{1\le s\le13}[L_{\max}(s)+\min(s,7)-L_{\min}(s)]=48.
\]

기존의 세계당 14/T 오차를 48/(14T)로 줄였다. 이 두 개선을 합치면

\[
\boxed{\frac{T-33}{28}-\frac{97}{14T}
\le R(B_T)-R(A_T)
\le\frac{T+27}{28}+\frac{97}{14T}.}
\]

양의 대비가 보장되는 충분 조건은 **T≥81에서 T≥39**, 대상 수로는 1,134에서 **546**으로 개선된다. 이것은 현상이 처음 나타나는 크기나 정확 비용 공식이 아니다.

### 2.3 강화하지 못한 부분

모든 T에서 두 정확 최적 비용이 같다는 강화를 검토했으나, 국소 제어 서명과 가능한 피복 언어가 일치하지 않아 그 인증 방법은 실패했다. 이것만으로 정확 최적 비용이 다르다는 반증도 되지 않는다. 실패 기록은 남겼다.

더 중요하게, 이 직접합 가족에서 q0→q2→q6 피복 순서를 우선하는 탐욕 동점 규칙은 양쪽에 최적 포락선 (7,5,2)을 만들며, 두 regret를 모두 O(1)로 만든다. 따라서 **기존 선형 명제는 모든 동점 규칙으로 강화할 수 없다**. 유한 18×9 반례의 모든 동점 규칙 성질과 이 점근 명제는 서로 다르다.

직접 검토와 독립 유한 인증이지 Lean/Isabelle 같은 형식 증명 검사기로 확인한 결과는 아니다. 상세 논증과 실패한 강화는 `reports/followup/PROOF_AUDIT.md`를 참고한다.

## 3. 연결 구성 A: 대상 추가 없이 한 질문을 공유

14×8 기반 쌍의 q3을 T개 블록 전체에서 하나의 질문으로 합친다. 다른 열은 블록별로 둔다. 한 행이 합치는 열 중 최대 하나만 포함하므로 결과는 이진이고 행 차수는 계속 3이다. N=14T, m=7T+1이다. 기준 그래프가 연결되어 있고 공유 질문이 비어 있지 않아 전체가 연결된다.

열 식별 행렬을 P라 하면 양쪽 Gram은 모두

\[
P^\top\operatorname{diag}(G,\ldots,G)P
\]

다. q3은 T≥3에서 유일한 탐욕 첫 질문이다. 답 이후에는 11개/3개 기준 후보 블록들의 직접합이 남는다. 아니오 가지에서 A의 최대 피복 프로필은 (6,3,2)/(6,4,1) 각각 1/2지만 B는 (6,4,1) 하나다. 예 가지는 양쪽 모두 (1,1,1)이다. 두 조건부 최적 포락선은 공통이다.

\[
C^*(M_T)=\frac87T+O(1)\quad(M=A,B),\qquad
C_G(A_T)=\frac{65}{56}T+O(1),\quad C_G(B_T)=\frac87T+O(1).
\]

따라서 연결성·차수 3·같은 Gram 아래

\[
\boxed{R(A_T)-R(B_T)=\frac{N}{784}+O(1),\quad R(A_T)=\Theta(N),\quad R(B_T)=O(1).}
\]

이는 한쪽 탐욕은 점근적으로 최적이고 다른 쪽은 선형 손실을 내는 연결 쌍이다. 비율은 A에서 65/64, B에서 1로 수렴한다. 균등 동점 가정은 유지된다.

## 4. 연결 구성 B: 연결 대상을 넣어 대비 계수 개선

기존 14×8 블록 2S개를 두 개씩 묶는다. 공통 질문 h와 S개의 새 대상을 추가하고, j번째 새 행을

\[
\{h,q_{2j,0},q_{2j+1,0}\}
\]

로 둔다. 그러면 N=29S, m=16S+1, 모든 행 차수는 3이다. 추가 행은 양쪽에서 같으므로 전체 Gram이 같으며, h를 통해 모든 블록이 연결된다. 모든 질문은 비상수이고, 허브의 차수는 S로 증가한다. 최대 질문 차수까지 고정한 구성은 아니다.

S≥9에서는 h의 yes 수 S가 다른 질문의 최대 yes 수 8보다 커서 유일한 탐욕 첫 질문이다. h=0 클래스는 기존 2S개 블록, h=1 클래스는 S개의 one-hot 연결 대상이다. 후자는 최적과 탐욕 비용 모두

\[
c(S)=\frac{S+1}{2}-\frac1S
\]

다. 임의 정책을 두 클래스에 제한하고 상수 질문을 지우면 조건부 최적 비용의 가중합이 하한이고, h를 먼저 묻는 정책은 그 값+1을 달성한다. 따라서 p=28/29에 대해

\[
C^*_{\rm conn,M}=pC^*(M_{2S})+(1-p)c(S)+e_M,\quad0\le e_M\le1,
\]

\[
C_{G,\rm conn,M}=1+pC_G(M_{2S})+(1-p)c(S).
\]

즉 연결화가 두 세계의 regret 대비를 p배한 값에서 최대 1만 바꾼다. 그 결과

\[
\boxed{R_{\rm conn}(B)-R_{\rm conn}(A)=\frac{2N}{841}+O(1).}
\]

강화된 유한 경계도 전달된다.

\[
\boxed{\frac{2S-62}{29}-\frac{97}{29S}
\le\Delta R_{\rm conn}
\le\frac{2S+56}{29}+\frac{97}{29S}.}
\]

**S≥33, N≥957**에서 양의 차이를 보장한다. 처음의 보수적인 연결 보증 N≥1,566보다 작다. 선도항은 최적 129S/58, 탐욕 A 131S/58, B 135S/58이고 비용 비율은 131/129와 45/43이다. 기저 블록 크기가 고정이므로 그래프 지름도 유계지만 h는 단절점이며 차수가 커진다. 2연결성이나 모든 질문 차수 유계는 주장하지 않는다.

## 5. 별도 강화: 연결된 세계의 최적 비용 자체가 선형으로 다름

18×9 반례의 q3을 블록 전체에서 공유하면 N=18T, m=8T+1인 연결된 차수 3 쌍을 얻는다. q3은 모든 T≥1에서 유일하게 9T/9T를 만든다. 조건부 블록들의 피복 포락선과 중첩 최적 증가량은 다음과 같다.

| 세계/답 | 피복 증가량 | D |
|---|---|---:|
| A,아니오 | (7,2) | 13 |
| B,아니오 | (7,2) | 13 |
| A,예 | (5,3,1) | 19 |
| B,예 | (5,2,2) | 21 |

각 증가량이 조건부 최적 포락선과 탐욕 최대 피복을 함께 달성한다. 조건부 정확 비용의 가중합을 하한으로, 공유 질문을 실제로 묻는 비용+1을 상한으로 사용하면

\[
C^*(A_T)=\frac89T+O(1),\quad C^*(B_T)=\frac{17}{18}T+O(1),
\]

\[
\boxed{C^*(B_T)-C^*(A_T)=\frac{N}{324}+O(1),\qquad C^*(B_T)/C^*(A_T)\to17/16.}
\]

유한 경계는

\[
\frac{T-59}{18}-\frac1{9T}\le C^*(B_T)-C^*(A_T)
\le\frac{T+59}{18}+\frac1{9T}
\]

이며 T≥60, N≥1,080에서 하한이 양수다. **이것은 최적 비용 차이이며 탐욕 regret 차이가 아니다.** 이 가족에서는 양쪽 regret가 O(1)이고 모든 9개 단일 질문 공유 방식에서 선형 regret 대비가 나오지 않았다는 음성 결과도 보존했다.

## 6. 실제 계산과 증명 경계의 구분

| 항목 | 수행·보존한 내용 |
|---|---|
| 연결 질문 공유 탐색 | 49개 포트 조건의 모든 조건부 포락선·유리수 프로필 |
| 실제 전체 행렬 DP | 10세계 중 8완료, 14×8 기반 T=3 두 세계는 상태 한도 미완결 |
| 루트 자체의 연결 구성 검산 | 14개 허브 구성의 Gram·차수·연결성, 작은 2세계 정확 계산, 8개 시드 정책의 전체 대상 재실행 |
| 별도 독립 행 집합 검토 | 24개 질문 공유 그래프, 4개 조건부 프로필, 기반 18×9의 모든 512 CUT 값 |
| 강화 증명 인증 | 모든 Bellman 대안과 최소 후속 값 19, 꼬리 잎 깊이 합 48, 양의 하한 충분 크기 |

큰 N의 비용은 정확 DP 값으로 채우지 않았다. 표·그림의 큰 N 경계는 수학적으로 증명한 구간이다. 시드별 정책의 비용은 해당 트리의 정확 실행 비용이며, 균등 동점 전체 기대값이나 최적 라벨이라고 부르지 않았다. 미완결 사례와 실패한 정확 동일성 강화, 선형 regret 증폭에 실패한 질문 공유는 모두 보존했다.

## 7. 논문의 기여와 남은 한계

연결성 부족 때문에 주제를 접을 필요는 없어졌다. 논문은 '새로운 일반 탐욕 최악 사례' 대신 **같은 Gram, 동치인 모든 CUT 통계, 같은 대상 차수 3 아래의 적응형 식별 비용·regret 분리**에 집중하는 것이 타당하다. 선형 대비는 O(N)의 자명한 전역 상한과 같은 증가 차수지만 정확한 최대 상수는 미해결이다.

신규성, 모든 질문 차수 유계, 2연결 그래프, 모든 동점 규칙에 강건한 고정 차수 3 선형 regret 가족은 아직 확보하지 않았다. 기존 단순 직접합/허브 전이 가족의 모든 동점 규칙 버전은 실제로 성립하지 않는다는 점까지 확인했다. 최초성 판단은 제한된 문헌 검색과 구분하고, 지금의 증명 검토 역시 외부 동료 심사를 대신한다고 쓰지 않는다.

상세 자료: `reports/followup/LITERATURE_AUDIT.md`, `PROOF_AUDIT.md`, `CONNECTED_AGENT.md`. 재현 코드와 원시 인증은 `followup_work/`, `runs/followup_connected_v1`, `runs/followup_root_gluing_v1`에 있다. 이전 두 연구 노트와 모든 원시 실험 파일은 별도 보존했다.
'''
    # Raw source uses double backslashes for easy literal math; Markdown needs one.
    text=text.replace('\\\\','\\')
    Path('Twenty_Questions_Followup_Review.md').write_text(text,encoding='utf-8')


def make_plot(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    t=np.arange(20,121,dtype=float)
    fig,axes=plt.subplots(1,2,figsize=(11,4),constrained_layout=True)
    axes[0].plot(t,(t-71)/28-393/(14*t),label='Prior bound')
    axes[0].plot(t,(t-33)/28-97/(14*t),label='Audited stronger bound')
    axes[0].axhline(0,color='black',linewidth=.7)
    axes[0].set(xlabel='Copies T (N=14T)',ylabel='Certified lower regret contrast',title='Disconnected family; proof bounds only')
    axes[0].legend()
    axes[1].plot(t,(2*t-100)/29-393/(29*t),label='Conservative transfer')
    axes[1].plot(t,(2*t-62)/29-97/(29*t),label='Strengthened transfer')
    axes[1].axhline(0,color='black',linewidth=.7)
    axes[1].set(xlabel='Connector objects S (N=29S)',ylabel='Certified lower regret contrast',title='Connected same-Gram degree3 family')
    axes[1].legend()
    for ext in ['png','pdf']:
        fig.savefig(out/f'bound_improvements.{ext}',dpi=180)
    plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default='runs/followup_review_v1')
    main(parser.parse_args().out)
