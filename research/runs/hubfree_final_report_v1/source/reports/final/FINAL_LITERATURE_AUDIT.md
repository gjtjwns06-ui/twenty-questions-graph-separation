# 기존 결과와의 최종 대조: 문헌 감사

조사일: 2026-11-25 (Asia/Seoul). 이전 `reports/followup/LITERATURE_AUDIT.md`를 보존하고, 검색어를 넓힌 후 핵심 정리·구성·버전 기록을 다시 대조했다. 이 문서의 “최종”은 이번 작업의 감사 결과를 뜻한다. 전체 문헌의 부재 증명이나 최초성 인증을 뜻하지 않는다. 검색 후보는 일반 검색으로 찾되 판정 근거는 저자 원고, 공식 학회 원문, 출판사 서지와 버전 기록으로 제한했다.

## 판정

**검토한 1차 자료에서는 현재의 전체 조건을 결합한 동일 정리를 찾지 못했다. 최초성은 아직 확인되지 않았다.** 반면 이전 감사보다 훨씬 가까운 정량적 선행례 두 개를 추가로 확인했다. **같은 모든 CUT 값 아래 최적화 값이 선형으로 달라지는 현상 자체는 기존 결과다.** 따라서 논문의 기여를 그 넓은 문장으로 표현하면 안 된다.

현재 구별 가능한 기여 후보는 다음처럼 좁다.

> 균등한 숨은 대상, 고정된 이진 단위 비용 질문, 서로 다른 행, 행 차수 3이라는 조건에서, 전체 질문 Gram이 같은 명시적 두 응답표의 실제 적응형 식별 비용과 정보이득 탐욕 regret가 정량적으로 분리되는 사례 및 증폭 가족.

연결성, 최대 질문 차수의 상수 제한, 질문 절단점 부재, 모든 동점 규칙에 대한 분리는 별개의 추가 조건이다. 기존 허브 연결 가족에서 증명한 결과를 이 조건들까지 만족한다고 쓰면 안 된다. 이번 문헌 조사에서는 이 조건을 모두 갖춘 동일 식별 정리도 발견하지 못했다. 새로운 탐색의 유한 검산과 무한 가족 정리는 구분해야 한다.

## 동일성을 판정한 수학적 조건

응답표를 \(M\in\{0,1\}^{N\times m}\)라 하고, 숨은 행은 균등하게 고른다. 알고리즘은 표 전체를 알고 열 하나의 숨은 행 값을 질문하며, 서로 다른 모든 행을 식별해야 한다. \(C^*\)는 최적 평균 질문 수, \(C_G\)는 매 상태에서 가장 균형 잡힌 열을 고르는 실제 탐욕 완성 비용, \(R=C_G-C^*\)이다. 이진 균등 조건에서는 정보이득 최대화와 균형 분할이 같다. 현재 증폭 정리의 탐욕은 균등 무작위 동점을 사용한다.

| 조건 | 동일 결과로 판단하려면 필요한 내용 |
|---|---|
| 제약 | 같은 \(N,m\), 서로 다른 행, 모든 행의 1의 수가 3 |
| 통제 | 열의 이름을 고정한 전체 \(M_A^\top M_A=M_B^\top M_B\) |
| 관측 | 알려진 세계의 숨은 한 행에 대한 단일 열 이진 응답 |
| 목적 | 평균 완전 식별 비용 또는 실제 탐욕 regret |
| 정량성 | \(\lvert R(A_N)-R(B_N)\rvert=\Omega(N)\) 같은 명시적 증폭 |
| 정책 | 균등 동점인지, 특정 동점인지, 모든 동점인지 명시 |
| 연결 확장 | 어떤 그래프의 연결성인지, 허브·절단점·최대 차수 제한을 명시 |

CUT 논문의 미지수는 하이퍼그래프 전체이고 관측은 여러 간선의 집계값이다. 현재 문제의 미지수는 이미 알려진 표의 한 행이다. 이 둘은 서로 다른 질의 모델이다.

## 가장 가까운 정량적 선행례: 이번에 추가 확인

### Chen–Khanna–Nagda, ICALP 2021

[공식 학회 원문](https://drops.dagstuhl.de/storage/00lipics/lipics-vol198-icalp2021/LIPIcs.ICALP.2021.53/LIPIcs.ICALP.2021.53.pdf), [저자 전체 원고 §3 Example 2와 §6.1](https://arxiv.org/html/2106.10386v1).

§3 Example 2는 \(K_4\)와 네 점의 모든 삼중항으로 이루어진 하이퍼그래프가 같은 CUT profile을 갖는다고 설명한다. 적절한 유도 부분그래프의 cut 값은 1 대 0이며, 복사본을 취해 0 대 \(\Omega(n)\) 차이로 증폭한다. §6.1 Lemma 6.1은 같은 CUT 응답을 갖는 두 세계와 vertex-neighbor sampling을 사용한 구별 불가능성을 분석한다. 공식판에서는 예제 번호가 다를 수 있어 저자판의 위치를 함께 고정했다.

**현재 결과와의 차이:** rank 2 세계와 rank 3 세계를 대조한다. 동일한 단순 3-uniform 행 집합 크기·전체 Gram·균등 숨은 행 식별·정보이득 탐욕 regret 조건을 모두 충족하는 정리가 아니다. 하지만 “동일 CUT profile + 복사본 + 선형 최적화 차이”라는 조합 자체의 선행례이므로 반드시 인용해야 한다.

### Aksoy–Friedman–Veldt–Young, 2026-10-13 v1

[원고와 제출 기록](https://arxiv.org/abs/2610.17581), [전체 원문 §4.1, 그림 1, 정리 4.1–4.2](https://arxiv.org/html/2610.17581v1).

§4.1은 삼각형의 세 2-간선과 중복도 2인 3-간선의 CUT 동등성을 이용한다. 여러 삼각형을 공통 간선에 겹쳐 만든 \(F^2,F^3\)는 같은 CUT profile이지만 최대 density가 선형 인자로 다르다. 정리 4.1은 CUT만으로 Densest Subhypergraph를 상수 성공확률로 \(o(\sqrt n)\)-근사할 수 없음을 보인다. 정리 4.2는 고정 크기 목적의 더 강한 불가능성을 준다.

**현재 결과와의 차이:** multihypergraph와 rank 2/3 대조이며 목적은 density다. 한 간선을 찾는 최적 질문 트리나 그 정보이득 탐욕 regret를 분석하지 않는다. 이 원고는 조사 기준일 전 한 달에 공개된 최신 선행례이므로, 오래된 감사만으로는 놓칠 수 있는 중요 중복 위험이다. “같은 집계 통계이지만 최적화가 매우 다름”이라는 넓은 신규성 문구를 피해야 한다.

## 탐욕 식별과 min-sum 계열의 직접 대조

### Li–Liang–Mussmann, SODA 2020

[공식 DOI](https://doi.org/10.1137/1.9781611975994.7), [저자 원문 v2, 정리 3.1·명제 3.3·부록 C.1·§6.6](https://arxiv.org/html/1906.11385v2).

정리 3.1의 균등 분포 특수화는 \(C_G/C^*=O(\log N/\log C^*)\)이며 임의의 탐욕 동점 트리에 적용된다. 명제 3.3과 부록 C.1은 균등 이진 질문에서도 탐욕의 나쁜 가족을 준다. §6.6은 불균형 경로를 Min Sum Set Cover로 분석한다. 따라서 탐욕 실패, 균등 목표의 최악 사례, 첫 yes 전 경로와 MSSC의 관계는 기존 내용이다.

**직접 대조:** 인용한 상·하한의 가정에는 행 차수 3 및 같은 전체 Gram을 갖는 동반 세계가 없다. 이 정리만으로 현재 통제 쌍의 선형 regret 차이가 바로 나오지는 않는다. 반대로 현재의 additive 차이는 이 기존 ratio 상한과 모순되지 않는다. 특히 고정 행 차수에서 무한히 커지는 ratio를 보였다고 표현하면 안 된다.

### Feige–Lovász–Tetali, APPROX 2002 / Algorithmica 2004

[기관 저자 원문 MSR-TR-2003-21](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-2003-21.pdf), 확인 위치: §1.1, 정리 10, 정리 13 및 그 증명.

목적은 각 원소가 처음 덮이는 위치의 합이다. §1.1은 분리된 인스턴스의 최적값이 단순 가산적이지 않음을 지적한다. 정리 10의 \(2r/(r+1)\) 탐욕 근사 보장은 r-uniform과 d-regular를 함께 가정한다. 정리 13의 증명은 복사본과 원소 중복으로 균일 하이퍼그래프의 hardness gap을 증폭한다.

**직접 대조:** r-uniform은 현재 행 차수 r에 대응하고, d-regular는 질문 빈도가 모두 같다는 추가 조건이다. 현재의 불균일 열 차수에 정리 10을 그대로 적용할 수 없다. 처음 덮이는 시점은 완전 식별 비용과 다르며, 중복 원소를 그대로 숨은 행으로 바꾸면 서로 다른 행 가정도 깨질 수 있다. 스케줄·복사본 증폭 기법의 신규성을 주장하지 말고, 통계 보존과 실제 식별 비용으로 이어지는 단계만 별도로 증명해야 한다.

## 같은 Gram을 만드는 조합론은 기존 내용

### Pasch trade와 twin Steiner triple systems

[Grannell–Lovegrove 2016 공식판](https://ajc.maths.uq.edu.au/pdf/66/ajc_v66_p130.pdf), [열람 가능한 저자판: 도입부·정리 2.3–2.4](https://grannell.net/Papers/twins.pdf), [Grannell–Griggs–Murphy 1997 출판사 서지·초록](https://www.sciencedirect.com/science/article/pii/S0012365X96002397).

2016 원문은 여섯 점의 네 삼중항을 교환하는 Pasch switch와 twin의 정의를 명시하고, 정리 2.3–2.4로 무한 가족을 구성한다. “identical twins”는 두 시스템이 동형이라는 뜻이다. 이 원문은 단순 동일 쌍 출현 통계와 교환, 복사·재귀 확장이 오래된 구성임을 직접 뒷받침한다.

**현재 적용의 한계:** 동일 쌍 출현은 off-diagonal Gram 보존이고 3-uniform에서는 대각도 결정된다. 그러나 동형인 두 표는 균등 목표와 순열에 대해 공변하는 균등 동점 정책의 비용이 같다. 따라서 identical twin을 이름만 바꾸어 현재 비용 차이 반례로 쓸 수 없다. 비동형 trade는 탐색 재료이며, trade 자체는 식별 regret 정리가 아니다. 1997 자료는 서지·초록까지 확인했으며 전문의 모든 정리를 검토했다고 주장하지 않는다.

### Chakrabarty–Liao, ESA 2026

[공식 전체 원문: 관찰 31, 부록 A 정리 32](https://drops.dagstuhl.de/storage/00lipics/lipics-vol388-esa2026/html/LIPIcs.ESA.2026.150/LIPIcs.ESA.2026.150.html), [저자 PDF](https://arxiv.org/pdf/2607.01216).

관찰 31은 삼중 간선을 삼각형으로 바꾸는 CUT 동등성을 사용한다. 정리 32는 홀수 k에 대해 같은 CUT profile을 갖는 서로 다른 k-uniform 하이퍼그래프를 구성한다. k=3의 세 점쌍에서 하나씩 고르는 짝수/홀수 패리티 구성은 Pasch 쌍이다. 논문은 미지 하이퍼그래프의 연결성·복원을 다루며 현재의 숨은 단일 행 식별 비용을 분석하지 않는다.

다음은 그 문맥을 현재 표에 적용한 초등 계산이다. 모든 행이 삼중항이고 \(G=M^\top M\)이면

\[
\operatorname{CUT}_H(S)=\tfrac12\sum_{i\in S,j\notin S}G_{ij},\qquad
G_{ij}=\operatorname{CUT}(\{i\})+\operatorname{CUT}(\{j\})-\operatorname{CUT}(\{i,j\})\quad(i\ne j).
\]

또한 \(G_{ii}=\operatorname{CUT}(\{i\})\)이다. 따라서 현재 조건의 전체 Gram과 전체 CUT profile은 동등하다. 이 환원을 새 독립 결과로 과장하지 않는다. 전체 비조건부 CUT 값이 같아도 답을 조건으로 제한한 남은 행들의 통계는 달라질 수 있으며, 그 적응형 차이를 증명하는 것이 현재 연구의 좁은 질문이다.

## 제한된 yes 수와 최근 원고의 버전 확인

[Dolev–Korach–Yukelson 2001 출판사 서지·초록](https://www.sciencedirect.com/science/article/abs/pii/S0743731500917179)은 시간과 에너지의 제약을 가진 guessing game을 다룬다. 원문 전문은 이번 도구에서 접근되지 않았으므로 세부 정리를 재검증했다고 쓰지 않는다. [Bruno–De Prisco–Vaccaro 2025 v3 도입부와 참고문헌](https://arxiv.org/html/2501.11129v3)은 이를 경로의 한쪽 응답 횟수 제한과 평균 깊이 문제의 선행 계보로 명시한다.

행에 1이 최대 r개면 비반복 식별 경로의 yes도 최대 r개다. 경로 계수로 얻는 \(C^*=\Omega_r(N^{1/r})\)와 기존 탐욕 상한을 결합한 고정 r의 \(O(r)\) ratio는 이 오래된 bounded-ones coding/search 계열의 초등 따름결과로 다루는 편이 타당하다. 현재의 고정 질문표는 임의의 membership 질문을 새로 설계하는 coding 문제보다 제약이 강하므로 두 최적값을 동일시하지 않는다.

| 자료 | 2026-11-25 확인 상태 | 원고에 반영할 점 |
|---|---|---|
| [Bruno–De Prisco–Vaccaro arXiv:2501.11129v3](https://arxiv.org/abs/2501.11129v3) | 2025-12-02 v3 코멘트가 정리 2의 주장을 증명 결함으로 철회했다고 명시 | 철회된 정리 2 또는 그 Kraft 조건을 증명 근거로 사용하지 않음 |
| [Szyfelbein arXiv:2604.12036 현재 v4](https://arxiv.org/abs/2604.12036) | v1의 constant-factor 제목 이후 v2 철회, 2026-10-19 v4는 logarithmic approximation으로 변경 | 옛 상수 근사 주장을 유효한 최신 결과로 인용하지 않음 |
| Szyfelbein v4의 현재 알고리즘 | separating subfamily를 탐욕적으로 고르며 평균 비용 보장은 \(7.3\log_2 n\) 미만 | 현재 연구의 단일 질문 정보이득 greedy와 동일 알고리즘으로 쓰지 않음 |

## 주장별 최종 분류

| 주장 | 이 감사의 판정 |
|---|---|
| 균등 이진 정보이득 탐욕의 비최적성·나쁜 ratio 가족 | 이미 알려짐 |
| 첫 yes 전 경로를 MSSC로 보는 기법 | 이미 알려짐 |
| min-sum 목적을 복사본으로 증폭 | 이미 알려짐 |
| Pasch로 같은 쌍 출현 통계를 갖는 삼중계 구성 | 이미 알려짐 |
| 서로 다른 홀수 균일 하이퍼그래프의 동일 CUT profile | 이미 알려짐 |
| 동일 CUT profile 아래 선형 최적화 값 차이 | 2021 induced-cut 및 2026 density 선행례 확인 |
| 동일 단순 3-uniform/동일 Gram의 균등 숨은 행 식별 regret에 대한 현재 명시적 선형 대비 | 검토한 정리에서 동일 명제 미발견; 신규성 미확인 |
| 중심 질문 없는 연결·상수 질문 차수·질문 절단점 없는 가족에서 같은 식별 대비 | 동일 선행 정리 미발견; 현재 증명 여부는 별도 결과를 따라야 함 |

논문에 사용할 수 있는 절제된 문구는 “질문 쌍 통계를 보존하는 명시적 희소 응답표 쌍에서 실제 적응형 정보이득 탐욕의 regret 분리를 분석한다”이다. “이런 통계 보존 세계에서 최적화 차이가 처음 발견되었다” 또는 “기존 탐욕 최악 사례를 처음 제시한다”는 문구는 이번 확인과 맞지 않는다.

## 검색 기록과 남은 범위

같은 날짜에 이전 감사의 검색군을 재확인하고 다음 검색어를 추가했다. 아래 검색군은 실제 수행 기록을 묶은 것이며 결과 개수나 전 세계 문헌의 완전성을 뜻하지 않는다.

| 순서 | 추가 검색식 | 확인·제외 내용 |
|---|---|---|
| 1 | `"decision tree" "same" "pairwise" "greedy"`; `"min sum set cover" "same" "intersection"`; `"cut equivalent" hypergraph "decision tree"`; `"hidden edge" "vertex queries" greedy` | 직접 조건 조합 탐색; 동일 전체 정리 미발견 |
| 2 | `"hypergraph" "hidden edge" "vertex" search decision`; `"hypergraphs" "same 2-section" "cover"`; `"decision tree" "pairwise independent" optimal`; `"min-sum" "trade" hypergraph` | graph-learning oracle, 불리언 함수 평가, 숨은 대상 식별을 구분 |
| 3 | `"min-sum set cover" "frequency" greedy 3 uniform`; `"greedy" "same" "cut profile" hypergraph`; `"decision trees" "pairwise correlations"`; `"decision tree" "intersection matrix"` | FLT의 uniform/regular 가정 재검토; 교차행렬 용어의 무관한 결과 제외 |
| 4 | `"minimum sum set cover" "co-degree"`; `"set cover" "same incidence" "greedy"`; `"hypergraph search" "average" vertex`; `"decision tree" "bounded frequency"` | 빈도 제한과 코드 경로 제약 확인; 직접 쌍 정리 미발견 |
| 5 | `"min sum set cover" "reverse"`; `"cut-equivalent" "ordering" hypergraph`; `"hypergraph" "same cut" "minimum sum"`; `"set cover" "pairwise intersections" "ordering"` | ordering/arrangement 대체 용어 점검; 정리의 동일성 근거로 채택한 새 결과 없음 |
| 6 | `Chen Khanna Nagda "hypergraph" "cut queries" 2021`; `"Identical Twin Steiner Triple Systems" pdf`; `"Guessing Games" "Yukelson" 2001` | 2026 CUT 원고의 인용망을 거슬러 2021 정량 선행례와 Pasch 저자판 확보 |
| 7 | `"hidden edge" "vertex queries" identification`; `"hypergraph search" "membership" "decision tree"`; `"searching" "hyperedge" "vertex" "average"`; `"decision tree" "same pairwise intersections"` | 단일 열 membership 모델의 대체 명칭 점검; 동일 전체 정리 미발견 |

인용망 점검은 Li–Liang–Mussmann의 MSSC 연결, Feige–Lovász–Tetali의 균일·정규 및 복사본 증명, Chakrabarty–Liao의 parity 구성, Aksoy 외의 2026 원고가 인용한 Chen 외의 2021 원고, bounded-ones 원고가 인용한 2001 계보를 중심으로 했다. Online MSSC, 일반 set cover, hypergraph reconstruction/group testing, classification 학습 및 pairwise independent percolation decision trees는 목적과 oracle이 달라 직접 동일 정리로 채택하지 않았다.

Scopus/Web of Science의 전체 전후방 인용망, 접근하지 못한 모든 유료 전문, 모든 언어의 학위논문을 완전 검토하지 않았다. 따라서 최종 결론은 **“검토한 원문에서 동일 결합 정리 미발견”**이며 **“동일 결과가 존재하지 않는다”**가 아니다. 새로운 hub-free 가족이 증명되면 그 정확한 가정과 계수를 기준으로 다시 대조할 필요가 있다.
