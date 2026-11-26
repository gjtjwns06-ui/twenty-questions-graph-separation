"""Reproduce the v0.3 editorial revision from the archived measured v0.2 paper.

Scientific tables are preserved verbatim; new theory/literature sections come
from the adjacent Markdown fragments. This does not rerun or retune ML.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
ARCHIVE = ROOT / 'archive/Twenty_Questions_Paper_Draft_v0.2.md'
DEFAULT = ROOT / 'Twenty_Questions_Paper_Draft.md'


def replace_once(s, old, new):
    assert s.count(old) == 1, old[:100]
    return s.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=DEFAULT)
    args = parser.parse_args()
    if not ARCHIVE.exists():
        original_bytes = DEFAULT.read_bytes()
        assert '버전 0.2' in original_bytes.decode('utf-8')
        ARCHIVE.write_bytes(original_bytes)
    text = ARCHIVE.read_text(encoding='utf-8')
    text = replace_once(text,
        '# 같은 질문 쌍 통계를 가진 스무고개 지식그래프의 최적 질문 선택\n\nTwenty Questions with Identical Pairwise Statistics and Different Optimal First Questions',
        '# 질문 쌍 통계를 보존하는 희소 식별 문제에서 정보이득 탐욕 손실의 선형 분리\n\nLinear Separation of Information-Gain Greedy Regret under Identical Pairwise Statistics')
    text = replace_once(text, '합성 본실험 1회 완료 연구 초안 · 2026년 11월 25일 · 버전 0.2',
        '구성 정리·신규성 범위 반영 연구 초안 · 2026년 11월 25일 · 버전 0.3')
    text = replace_once(text,
        '> 기존 14×8 검산·증명과 새로 실행한 합성 실험을 구분한다. PDF·DOCX는 버전 0.1 스냅샷이며, 최신 측정과 상태는 이 Markdown 및 원시 결과표를 기준으로 한다.',
        '> 원래 14×8 검산, 합성 본실험, 선택된 극값 반례와 무한 구성 정리를 구분한다. 신규성 주장은 2026-11-25에 확인한 문헌 범위에 한정한다. PDF·DOCX는 버전 0.1 스냅샷이며, 최신 결과는 이 Markdown과 연결한 원시 인증을 기준으로 한다.')
    ko = r'''균등한 숨은 대상을 주어진 이진 단위 비용 질문으로 식별할 때, 전체 질문 쌍 통계가 같아도 정보이득 탐욕의 실제 손실은 선형으로 달라질 수 있다. 서로 다른 degree-3 행만 갖고 같은 indexed Gram 행렬을 보존하는 응답표 쌍을 구성한다. 질문 최대 차수는 10이고 전체 이분 그래프에는 단절점이 없으며, 기존 cubic expander를 골격으로 사용하면 양의 균일 팽창을 유지한다. 매 상태 탐욕 동점을 균등 처리할 때 대상 수 $N=17T$에 대해 두 세계의 최적 평균 비용은 모두 $35T/34+O(1)$, 탐욕 비용은 각각 $71T/68+O(1)$와 $73T/68+O(1)$이다. 따라서 regret 차이는 $N/578+O(1)$이며, 비용 비율은 상수로 수렴한다. 별도 38×18 유한 쌍에서는 양쪽의 모든 최초 greedy 질문이 최적임에도 후속 greedy 손실이 $13/76$ 대 0이고 최선 greedy 동점에서도 손실이 남는다. 최초성은 단정하지 않으며, 기존의 탐욕 최악 사례·투영 정보 손실·같은 CUT의 최적화 분리와 차이를 명시한다. 이전 합성 본실험의 1,223쌍·2,446세계와 학습 비교도 보존한다. 주 시험에서 선택 모델은 깊이 3 탐색보다 낮은 점추정치를 보였지만 차이 구간이 0을 포함하여 ML 개선을 확정하지 못했다.'''
    en = r'''We construct pairs of sparse binary identification tables with identical indexed question Gram matrices but linearly separated regret of information-gain greedy. The hidden row is uniform, tests are fixed binary columns of unit cost, and greedy ties are resolved uniformly at every state. All rows are distinct and have weight three. For infinitely many even T, the tables have N=17T objects and 8T questions, maximum question degree ten, and incidence graphs with no articulation vertex. Using an established family of cubic expanders as skeletons also yields uniform positive incidence expansion. Both optimal mean costs are 35T/34+O(1), whereas the greedy costs are 71T/68+O(1) and 73T/68+O(1). Their regret difference is N/578+O(1); the approximation ratios converge to constants. A separate exact 38-object, 18-question pair has greedy regret 13/76 versus zero even though every initial greedy question is optimal in both worlds; its inefficient world remains suboptimal under every greedy tie resolution. We distinguish these results from known greedy lower bounds, projection information loss, and cut-equivalent optimization separations, without claiming certified priority. The preserved synthetic study contains 1,223 pairs and 2,446 completed exact world labels. Its selected learning model did not establish improvement over depth-three lookahead: the paired first-question regret difference was -0.000485 with a 95% parent-bootstrap interval [-0.001144, 0.000116].'''
    text, n = re.subn(r'(?<=## 초록\n\n).*?(?=\n\n\*\*핵심어)', lambda _: ko, text, count=1, flags=re.S)
    assert n == 1
    text, n = re.subn(r'(?<=## Abstract\n\n).*?(?=\n\n## 1 서론)', lambda _: en, text, count=1, flags=re.S)
    assert n == 1
    text = replace_once(text,
        '이 초안은 세 부분을 구분한다. 첫째, 주어진 통계가 같지만 최적 첫 질문 집합이 서로소인 작은 예시를 구성하고 정확하게 검산했다. 둘째, 그 예시에서 얻는 초기 요약 표현의 한계와 통제 과정에서 자동으로 고정되는 그래프 특징을 설명한다. 셋째, 여러 그래프에서 현상을 조사하고 ML의 실질적인 추가 가치를 검증할 본실험을 설계한다. 세 번째 부분의 첫 합성 실행 결과는 8절에 제시하며, 전체 학습 정책과 일반 정리는 미완료다.',
        '이 초안은 유한 첫 질문 충돌 예시, 중심 질문 없는 선형 탐욕 손실 분리 정리, 합성 본실험과 학습 비교를 구분한다. 핵심 정리는 5.5절과 부록 C에 제시한다. 5.6절의 유한 보강은 모든 greedy 동점에서의 실패를 보이지만, 무한 가족의 정리는 균등 동점에 한정된다. 8절의 이전 합성 실행과 ML 미개선 결과는 그대로 보존하며 전체 학습 정책은 미실행이다.')
    text = replace_once(text,
        '이 설계가 선행연구와 구별되는 유용한 기여인지는 본실험 및 추가 문헌 검토를 통해 판단해야 한다.',
        '기여의 중심은 같은 통계 아래 실제 적응형 탐욕 손실을 분리하면서 연결성과 유계 차수·팽창을 함께 유지하는 정리다. 이 결합 결과와 기존 도구의 경계는 2.4–2.5절에서 밝힌다.')
    related = (HERE / 'paper_related_work.md').read_text(encoding='utf-8').rstrip() + '\n\n'
    text, n = re.subn(r'### 2.4 현재 제안하는 기여\n.*?(?=## 3 문제 정의)', lambda _: related, text, count=1, flags=re.S)
    assert n == 1
    theory = (HERE / 'paper_theory.md').read_text(encoding='utf-8').rstrip() + '\n\n'
    text = replace_once(text, '## 6 본실험 설계와 구현', theory + '## 6 본실험 설계와 구현')
    text = replace_once(text, '## 5 검산한 유한 예시', '## 5 유한 검산과 구성 정리')
    text = replace_once(text,
        '| 공통 구조의 일반 정리 | 미확립 | 기술 분석을 충분조건으로 해석하지 않음 |',
        '| 본실험 분포 전체의 구조적 충분조건 | 미확립 | 기술 분석을 충분조건으로 해석하지 않음 |\n'
        '| 별도 설계한 무한 구성 정리 | 증명·유한 인증 완료 | 5.5절, 균등 탐욕 동점·유계 차수·연결 팽창 |\n'
        '| 38×18 후속 탐욕 실패 | 독립 정확 검산 완료 | 5.6절, 모든 greedy 동점에서의 유한 보강 |')
    text = replace_once(text,
        '첫째, 검산한 예시는 현상의 존재를 보여주는 선택된 작은 구성이다. 평균 최적 비용 차이는 작고 표본 분포에 대한 대표성이 없다. 더 작은 반례가 가능한지, 같은 구조가 큰 그래프에서도 유의미한 비용 차이를 만드는지, 실용적인 질문 시간 절감으로 이어지는지는 미해결이다.',
        '첫째, 검산한 예시와 극값 탐색의 최선 예시는 선택된 구성이며 모집단의 대표성이나 전역 극값을 보이지 않는다. 정리 1은 절대 손실 차이의 선형 증가를 보이지만, 최적 비용 자체도 선형이고 비율은 상수로 수렴한다. 더 작은 반례, 날카로운 계수, 실용적 질문 시간 절감은 별도 문제다.\n\n'
        '정리 1의 균등 동점 가정은 필수다. 특정 우선순위 동점에서는 양쪽 regret가 O(1)이 된다. 유한 38×18의 모든 동점 강건성을 무한 정리로 확대하지 않는다. 큰 그래프의 비용 경계와 작은 표의 정확 DP 결과도 구분한다. 신규성 검토에서는 동일 결합 정리를 찾지 못했으나, 최초성·외부 심사·형식 검증은 인증하지 않았다.')
    text = replace_once(text,
        'ML의 전체 순차 정책, 현실 자료의 효과, 고차 구조의 일반 정리는 아직 주장하지 않는다.',
        'ML의 전체 순차 정책과 현실 자료의 효과는 미실행이다. 별도 구성 정리 1은 균등 동점 아래 전체 Gram을 보존하는 연결·유계 차수·팽창 가족에서 선형 탐욕 손실 차이를 보인다. 이 정리는 모든 동점 규칙이나 무작위 생성 분포 전체의 구조적 충분조건을 보장하지 않는다.')
    text = replace_once(text,
        '현재 결과는 지정한 합성 생성·교환 분포, 균등 목표와 정확 이진 응답에 한정된다.',
        '8절의 경험적 결과는 지정한 합성 생성·교환 분포, 균등 목표와 정확 이진 응답에 한정된다.')
    text = replace_once(text, '## 10 결론\n\n',
        '## 10 결론\n\n'
        '같은 질문 쌍 통계를 갖는 희소 응답표에서 실제 정보이득 탐욕 손실이 선형으로 달라지는 가족을 구성했다. 최대 질문 차수 10과 단절점 없는 연결성을 유지하고, 기존 expander 골격을 이용해 균일 팽창도 확보한다. 이 결합 구성과 비용 계수를 중심 기여로 삼으며 Pasch trade·투영 정보 손실·탐욕 비최적성 자체의 신규성은 주장하지 않는다.\n\n')
    references = r'''[11] Ray Li, Percy Liang, and Stephen Mussmann. A Tight Analysis of Greedy Yields Subexponential Time Approximation for Uniform Decision Tree. *SODA 2020*. [저자 원문 v2](https://arxiv.org/html/1906.11385v2).

[12] Uriel Feige, László Lovász, and Prasad Tetali. Approximating Min Sum Set Cover. *Algorithmica*, 40:219–234, 2004; preliminary version APPROX 2002. [기관 저자 원문 MSR-TR-2003-21](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-2003-21.pdf).

[13] Steve Kirkland. Two-mode networks exhibiting data loss. *Journal of Complex Networks*, 6(2):297–316, 2018. [DOI 10.1093/comnet/cnx039](https://doi.org/10.1093/comnet/cnx039). [저자 원문](https://server.math.umanitoba.ca/~kirkland/actor_event_paper_revised.pdf).

[14] Yu Chen, Sanjeev Khanna, and Ansh Nagda. Sublinear Time Hypergraph Sparsification via Cut and Edge Sampling Queries. *ICALP 2021*, LIPIcs 198, Article 53. [저자 원문 §3](https://arxiv.org/html/2106.10386v1).

[15] Deeparnab Chakrabarty and Hang Liao. Query Complexity of Hypergraph Connectivity and Learnability Using CUT Oracles. *ESA 2026*, LIPIcs 388, Article 150. [공식 원문](https://drops.dagstuhl.de/storage/00lipics/lipics-vol388-esa2026/html/LIPIcs.ESA.2026.150/LIPIcs.ESA.2026.150.html).

[16] Sinan G. Aksoy, Eli Friedman, Nate Veldt, and Stephen J. Young. Query Complexity of Densest Sub(hyper)graph Problems. *arXiv:2610.17581v1*, 2026-10-13. [원문](https://arxiv.org/html/2610.17581v1).

[17] Yunjae Hwang and Byoungjin Seok. What Response Marginals Miss: Adaptive Query Complexity of Functional Backdoor Recovery. *arXiv:2610.07771v1*, 2026-10-06. [원문](https://arxiv.org/html/2610.07771v1).

[18] Zhongyi Zhang and Yixin Cao. Minimum Sum Set Cover: Structures and Algorithm. *arXiv:2605.21920v1*, 2026-05-21. [원문](https://arxiv.org/html/2605.21920v1).

[19] Shuchi Chawla, Evangelia Gergatsouli, Jeremy McMahan, and Christos Tzamos. Approximating Pandora’s Box with Correlations. *arXiv:2108.12976v4*, 2023-07-21. [원문](https://arxiv.org/html/2108.12976v4).

[20] Joel Friedman. A Proof of Alon's Second Eigenvalue Conjecture and Related Problems. *Memoirs of the AMS*, 195(910), 2008; arXiv:cs/0405020. [저자 공개본](https://arxiv.org/abs/cs/0405020).

[21] Sanjoy Dasgupta. Analysis of a Greedy Active Learning Strategy. *Advances in Neural Information Processing Systems 17*, 2004; extended author manuscript 2005. [저자 원문](https://cseweb.ucsd.edu/~dasgupta/papers/greedy.pdf).

'''
    text = replace_once(text, '## 부록 A 통제 조건의 수학적 귀결', references + '## 부록 A 통제 조건의 수학적 귀결')
    text += '\n' + (HERE / 'paper_appendix_c.md').read_text(encoding='utf-8').rstrip() + '\n'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding='utf-8')
    receipt = dict(input_archive=str(ARCHIVE.relative_to(ROOT)),
        archived_sha256=sha256(ARCHIVE.read_bytes()).hexdigest(),
        output=str(args.output), output_sha256=sha256(args.output.read_bytes()).hexdigest(),
        version='0.3', measured_tables_preserved=True)
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
