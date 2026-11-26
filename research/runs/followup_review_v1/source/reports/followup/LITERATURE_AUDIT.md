# 선행연구 중복 감사

조사 기준일: 2026년 11월 25일(Asia/Seoul). 이 문서는 기존 실행 결과와 코드를 바꾸지 않는 문헌 감사다. 일반 웹 검색으로 후보를 찾은 뒤 저자 원고·arXiv 버전 기록·공식 학회/출판사 원문을 확인했다. Scopus·Web of Science 전체 인용망을 완전 검색한 결과는 아니며, 검색에서 발견하지 못한 문헌의 부재를 증명하지 않는다.

## 판정

**현재 확인한 1차 자료에서는 다음 조건을 모두 결합한 동일 정리를 찾지 못했다.** 균등 목표·고정 이진 질문·단위 비용 아래, 행 차수가 3이고 전체 Gram이 같은 두 세계의 균등 동점 탐욕 regret 차이가 대상 수에 선형으로 증가한다는 정리다. 그러나 이 결론을 구성하는 중요한 부분은 이미 알려져 있다. 최초성 주장은 보류해야 한다.

새 기여 후보는 단순한 탐욕 실패, Pasch 교환, 같은 저차 통계로 서로 다른 세계를 만드는 것, 복사본으로 비용 차이를 키우는 것 각각이 아니다. 후보는 **이 알려진 재료들을 같은 Gram 제약 아래의 실제 적응형 식별 비용 차이로 정량적으로 연결한 명시적 쌍과 증명**이다.

## 조건별 비교

| 1차 연구 | 이미 알려진 부분 | 현재 정리와 같지 않은 부분 |
|---|---|---|
| Li–Liang–Mussmann, SODA 2020 | 균등 이진 식별의 탐욕 상한·하한, 임의 동점 규칙, MSSC와의 연결 | 같은 Gram·같은 차수인 동반 세계의 regret 대비를 요구하지 않음 |
| Feige–Lovász–Tetali, APPROX 2002/Algorithmica 2004 | 최초 피복 비용, 최대 미피복 greedy, 복사본을 이용한 gap amplification, 균일 하이퍼그래프 | 알려진 응답표의 숨은 대상 완전 식별과 다름; 같은 Gram 쌍의 regret를 분석하지 않음 |
| Grannell–Lovegrove, 2016 및 Grannell–Griggs–Murphy, 1997 | Pasch 스위치·동일한 쌍 출현을 갖는 삼중계의 무한 가족 | 질문 전략이나 식별 비용을 분석하지 않음 |
| Chakrabarty–Liao, ESA 2026 | 같은 모든 CUT 값을 갖는 서로 다른 홀수 균일 하이퍼그래프; k=3의 패리티 쌍은 Pasch 형태 | CUT로 미지 하이퍼그래프를 복원하는 문제이며, 알려진 하이퍼그래프의 숨은 한 간선을 질문으로 찾는 비용은 분석하지 않음 |
| Dolev–Korach–Yukelson, 2001 | 경로의 한쪽 응답 횟수 제한 아래 평균 깊이 최소화 | 같은 Gram, 고정 질문표, 정보이득 greedy 대비가 없음 |
| Bruno–De Prisco–Vaccaro, 2025 | codeword당 1의 수가 제한된 prefix/search tree 문제와 선행 계보 | 고정 차수의 경로 계수법은 이 오래된 문제 계열에 속함; 동일 Gram 대비는 없음. 일부 정리는 철회 주의 |

## 1. 일반 탐욕 최악 사례와 MSSC 연결은 기존 결과다

Li–Liang–Mussmann의 정리 3.1은 균등 목표에서 \(C_G/C^*=O(\log N/\log C^*)\)를 주고, 명제 3.3·부록 C.1은 나쁜 균등 이진 사례를 구성한다. 상한은 임의의 탐욕 동점 트리에 적용된다. 6.6절은 min-sum set cover를 통해 비균형 경로를 분석한다. 따라서 탐욕과 MSSC를 연결한 사실 자체를 새 기여로 쓰면 안 된다. 이 논문의 가정에는 동일 Gram 쌍이나 행 차수 3이 포함되지 않는다. [저자 원문, 정리 3.1·명제 3.3·6.6절](https://arxiv.org/html/1906.11385v2)

Feige–Lovász–Tetali의 원문은 최초 피복 위치 합이 \(\sum_i i|X_i|=\sum_i R_i\)임을 쓰며 최대 피복 greedy의 4 근사를 다룬다. 1.1절은 분리된 인스턴스를 합쳐도 최적 순서를 단순히 합칠 수 없음을 명시하고, 정리 13은 여러 복사본으로 gap을 증폭한다. 현재 증명의 포락선·스케줄 분석은 이 선행 계열과 비교해야 한다. 그들의 정리 10은 r-uniform과 d-regular를 모두 요구하므로, 질문 빈도가 불균일한 현재 기반 쌍에 그 특별 상한을 바로 적용할 수 없다. [저자/기관 원문, MSR-TR-2003-21](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-2003-21.pdf)

## 2. 같은 Gram의 구성과 더 강한 CUT 동등성도 선행 맥락이 있다

Grannell–Lovegrove는 twin Steiner triple systems와 Pasch 교환을 명시한다. 행을 삼중 블록, 열을 점으로 보면 같은 쌍 출현 수는 현재의 off-diagonal Gram 보존이다. 특히 논문이 주로 구성하는 **identical twins는 동형**이므로, 이름 순열에 따라 움직이는 균등 동점 정책의 비용이 같아야 한다. 그 종류의 쌍 자체가 현재 비용 차이 반례인 것은 아니다. 비동형 twin 계열은 더 가까운 조합적 배경이지만 그 원문에서 식별 비용 정리는 확인하지 못했다. [공식 2016 원문](https://ajc.maths.uq.edu.au/pdf/66/ajc_v66_p130.pdf), [1997 논문 초록·서지](https://www.sciencedirect.com/science/article/pii/S0012365X96002397)

Chakrabarty–Liao의 ESA 2026 논문 부록 A 정리 32는 같은 CUT profile의 홀수 k-uniform 쌍을 준다. k=3에서는 여섯 점의 세 쌍에서 하나씩 고른 짝수/홀수 패리티 네 삼중항으로, Pasch 쌍과 같다. 관찰 31은 삼중 간선을 반가중 삼각형으로 바꾼 CUT 동등성을 쓴다. 이것은 단순한 쌍 통계보다 강해 보이지만, 3-uniform에서는 다음 계산에 의해 Gram과 모든 CUT 값이 사실상 동등하다. 다만 해당 원문에는 greedy 식별 regret 대비 정리가 없다. [공식 원문, 관찰 31·정리 32](https://drops.dagstuhl.de/storage/00lipics/lipics-vol388-esa2026/html/LIPIcs.ESA.2026.150/LIPIcs.ESA.2026.150.html)

질문 집합 S가 나누는 삼중 간선마다 crossing 질문 쌍은 정확히 두 개이므로

\[
\operatorname{CUT}_H(S)=\frac12\sum_{i\in S,j\notin S}G_{ij}.
\]

반대로 \(d_i=\operatorname{CUT}(\{i\})\), \(G_{ij}=d_i+d_j-\operatorname{CUT}(\{i,j\})\)이고 대각은 \(G_{ii}=d_i\)다. 따라서 차수 3 결과는 **모든 비조건부 CUT 응답까지 같은 세계에서 실제 적응형 식별 비용이 다르다**고 표현할 수도 있다. 이 문장의 Gram↔CUT 환원은 위 관찰의 간단한 특수화이며 독립된 새 정리라고 주장하지 않는다. CUT oracle은 미지 세계의 모든 간선 수를 집계하며, 현재 게임의 질문은 주어진 한 열에 대한 숨은 대상의 이진 응답이다. 두 oracle 모델을 혼동하면 안 된다.

## 3. 고정 차수의 O(r) 비율은 새 주요 정리로 삼기 어렵다

행마다 1이 최대 r개이면 비반복 결정 경로의 yes도 최대 r개다. 짧은 잎 경로를 0으로 채우는 단사와 이항계수 합으로 \(C^*=\Omega_r(N^{1/r})\)를 얻고, Li–Liang–Mussmann의 기존 상한을 결합하면 고정 r에서 비율은 O(r)다. 이 결합은 타당한 따름결과 후보지만, 경로의 1 제한은 오래된 coding/search 문제다.

Dolev–Korach–Yukelson의 2001년 원문 초록은 시간·에너지 제한 아래 guessing game의 최적 트리 DP를 제시한다. 더 최근 원문은 이 연구를 한쪽 간선 횟수 제한 평균 깊이 문제의 선행연구로 명시한다. [출판사 원문 서지·초록, DOI 10.1006/jpdc.2000.1717](https://www.sciencedirect.com/science/article/abs/pii/S0743731500917179)

Bruno–De Prisco–Vaccaro는 1의 수가 제한된 codeword와 prefix tree를 직접 다룬다. 도입부는 2001년 연구와 binary search/code 대응을 설명한다. **현재 v3의 저자 코멘트는 정리 2의 주장을 증명 결함으로 철회했다고 명시한다.** 해당 정리를 현재 증명에 쓰지 않는다. 이 논문은 문제 계보의 근거로만 인용하고, 현재의 계수법은 독립적으로 증명한다. [현재 버전 기록](https://arxiv.org/abs/2501.11129v3), [원문 도입부·참고문헌](https://arxiv.org/html/2501.11129v3)

## 4. 동일 수학적 결과 여부의 현재 결론

| 주장 | 판정 |
|---|---|
| 정보이득 greedy는 비최적일 수 있다 | 기존 결과 |
| 균등 대상에서도 greedy 비율의 나쁜 가족이 있다 | 기존 결과 |
| Pasch로 같은 쌍 출현을 갖는 서로 다른 삼중계가 생긴다 | 기존 결과 |
| 서로 다른 3-uniform 세계가 모든 CUT 값까지 같을 수 있다 | 기존 결과 |
| 첫 yes 전 경로를 MSSC로 분석한다 | 기존 기법과 밀접하며 LLM 2020이 이미 연결 |
| 복사본/스케줄로 min-sum gap을 증폭한다 | 기존 기법 |
| 현재 명시적 같은-Gram 쌍에서 \(R(B_T)-R(A_T)=N/392+O(1)\) | 조사한 원문에서 동일 명제 미발견; 신규성 미확인 |
| 고정 차수 3에서 선형 additive 차이를 구성하는 동시에 비율 발산은 배제 | 현재 구성+기존 이론의 결합; 개별 도구를 새 결과로 표현하면 안 됨 |
| 연결된 같은-Gram 쌍의 동일 증폭 | 이번 문헌 검색에서 동일 명제 미발견; 구성·증명은 별도 검토 필요 |

가능한 논문 기여 문구는 '새 탐욕 최악 사례를 최초 제시한다'가 아니라 '명시적 동일 Gram의 희소 응답표 쌍에서 실제 균등 동점 식별 regret의 정량적 분리를 보이고, 그 분리가 선형으로 증폭되는 가족을 구성한다' 정도로 좁히는 것이 맞다. 이 표현도 원고 제출 전 해당 분야 연구자의 확인과 더 넓은 인용망 점검이 필요하다.

## 5. 검색 기록과 범위

같은 날 다음 검색군을 사용했다. 각 군에서 약 네 검색어를 병행했으며, 무관한 분류 학습·의학·일반 set cover 결과는 일치 근거로 쓰지 않았다.

| 검색군 | 대표 검색식 | 결과 |
|---|---|---|
| 직접 문구 | `decision tree same pairwise marginals`, `decision tree pairwise statistics`, `decision tree Gram`, `decision tree Pasch` | 같은 전체 조건의 명제 미발견 |
| set system 동등성 | `set systems same pairwise intersections`, `set cover intersection matrix`, `set cover identical Gram` | 일반 교차·기하 cover와 혼재; 직접 동치 결과 미발견 |
| 극값과 MSSC | `min-sum set cover greedy frequency`, `min-sum set cover trade`, 저자+논문명 | FLT 원문, 균일/정규 특수 조건과 복사본 증폭 확인 |
| 희소 경로 | `prefix code bounded Hamming weight average length`, `decision tree bounded frequency` | 2025 bounded-ones 원문 및 2001 선행연구 확인 |
| 하이퍼그래프 식별 | `hypergraph unknown edge queries`, `Steiner triple system decision tree`, `hidden edge vertex queries` | 임의 집합 group testing과 현재 단일 열 질의를 구분 |
| CUT profile | `cut-equivalent decision tree`, `hypergraph same cut greedy` 및 2026 원문 인용 추적 | 3-uniform Pasch와 같은 CUT profile의 직접 선행 맥락 확인 |

검색으로 발견하지 못한 결과도 있을 수 있다. 특히 용어가 'decision tree' 대신 hypergraph search, restricted membership query, bounded-ones prefix code, trade, indistinguishability로 쓰이는 문헌을 더 찾을 여지가 있다. 현재 자료로 '선행연구에 동일한 결과가 없다'고 단정하지 않는다.
