# Results and claim boundaries

[Overview](../README.md) · [Reproducibility](REPRODUCIBILITY.md) · [한국어](README.ko.md)

## Model and control condition

An unknown row of a binary response table is drawn uniformly. A query asks one of the fixed columns, returns a noiseless bit and costs one unit. Rows are distinct, each with exactly three ones. Within each compared pair, dimensions and the full indexed matrix $M^\top M$ agree. Thus question marginals and every two-question response distribution agree.

The control also fixes the question projection, the full bipartite adjacency/Laplacian/normalized spectra, and total simple four- and six-cycle counts. Conditional structures after answers may differ. Initial pairwise indistinguishability does not imply a limitation on every adaptive conditional method.

## First-question cost and full policy cost

The first-question regret of `q` allows optimal continuation after that question. The full greedy regret instead asks greedy to choose again after every answer. These are separate metrics throughout the paper and results.

The main ML study evaluates first actions. Its full learned sequential policy is unmeasured. The 38×18 witness has zero first-action regret for every initial greedy choice, while subsequent greedy decisions produce positive full-policy regret in world A.

## Finite computations

| Artifact | Verified result | Evidence |
|---|---|---|
| Original 14×8 pair | Different optimal first-question sets; optimal means 54/14 and 55/14 | [Original verification](../research/verification.json) |
| Selected 18×9 pair | Full greedy regret contrast 2/9; unique shared first greedy query | [Saved pair](../research/runs/extremal_report_v1/best18.json) |
| Selected 38×18 pair | Contrast 13/76; minimum-over-greedy-ties contrast 3/19 | [Saved pair](../research/runs/hubfree_search_v1/best.json) |
| Independent finite audit | Separate DP representation, vertex deletion and query-deletion sensitivity checks | [Certificate](../research/runs/final_independent_certificate_v1/summary.json) |
| Nine finite expander skeletons | Exact rational/integer spectral and structural certificates | [Expander summary](../research/runs/hubfree_expander_cert_v1/summary.json) |

Selected extremal witnesses are search results, not random-prevalence estimates or proofs of global extremality.

## Asymptotic theorem

The final family uses a different 14×8 base from the original first-question example. For infinitely many cubic-expander skeleton sizes `T`, the lift has `N=17T` objects, `8T` questions, maximum question degree 10, no articulation vertex, distinct degree-three rows, the same indexed Gram, and uniform positive incidence expansion.

Under uniform tie selection at every greedy state, the regret contrast is `N/578+O(1)`. The two greedy-to-optimal ratios tend to `71/70` and `73/70`. The result separates additive costs. Arbitrary tie priorities can remove the linear contrast; that stronger claim is not made.

For cubic skeletons, the proved finite contrast interval is

$$\frac{T-69}{34}-\frac{235}{17T}\ \leq\ R(B_T)-R(A_T)\ \leq\ \frac{T+63}{34}+\frac{235}{17T}.$$

The lower bound is `31/1292` at `T=76` and `263/340` at `T=100`. These values are **proved bounds**, not full DP measurements at 1,292 or 1,700 objects. See [the manuscript](../research/paper/main.tex) for the coverage-envelope, profile and expansion arguments.

Earlier disconnected and hub-based constructions remain in [the follow-up review](../research/Twenty_Questions_Followup_Review.md). The final result strengthens their connectivity/degree structure. It does not erase cases in which a proposed extension failed.

## Synthetic study and ML

The frozen main study contains 1,400 parent attempts and 1,223 completed pairs (2,446 worlds), across natural, planted and modular generators. Of those pairs, 1,114 have zero optimal-cost difference and remain included. Related worlds and weighted-Gram isomorphism groups stay in the same split; the selected primary model was fixed using validation data before independent test evaluation.

| Comparison | ML minus depth-3 first regret | Paired 95% interval |
|---|---:|---:|
| Main held-out test, 179 parents | −0.000484947 | [−0.001144475, +0.000116387] |
| Size extrapolation, 160 parents | −0.000954861 | [−0.002365451, +0.000455729] |
| Family extrapolation, 153 parents | −0.000226943 | [−0.001346526, +0.000816993] |

All three intervals include zero. The bootstrap resamples parents with the fitted model fixed. Three recorded refitting seeds gave the same point estimates; that does not remove model uncertainty. Ridge variants with lower test point estimates were not substituted for the validation-selected primary model. All method/ablation rows remain in [policy_summary.csv](../research/runs/main/report/policy_summary.csv).

On the recorded PC, feature-inclusive ML first-action selection took about 34 ms versus 1.55 ms for depth-3 lookahead. These resource measurements are environment dependent. See [the timing record](../research/runs/main/report/timing.json), [pilot report](../research/reports/PILOT_REPORT.md), and [frozen design](../research/reports/EXPERIMENT_DESIGN.md).

## Unsuccessful or incomplete outcomes

- The fixed-Gram search did not improve its seed: the largest visited contrast was 2/21.
- Direct sums of the selected 18×9 pair have the same `(9,7,2)` coverage profile and do not give linear amplification.
- Some small direct-sum/cycle cases have zero contrast despite asymptotic separation in their families.
- Sharing a root query in the 18-object construction separated optimal cost, without giving the desired linear regret contrast.
- Deleting both initial greedy roots in the 38-object witness removes its contrast. Individual-query deletion robustness does not imply arbitrary deletion robustness.
- State/time limits, including both 96×20 pilot worlds, are recorded as incomplete. No approximate answer is substituted for an exact label.

The [manuscript appendices](../research/paper/main.tex), [extremal note](../research/Twenty_Questions_Extremal_Note.md), [follow-up review](../research/Twenty_Questions_Followup_Review.md), and [final hub-free review](../research/Twenty_Questions_Hubfree_Final_Review.md) retain the details and original denominators.

## Relation to earlier work

Greedy worst cases, min-sum set cover, trades preserving pairwise statistics, loss in graph projections, and expander constructions already have literature. The scoped contribution is their simultaneous constrained realization with the stated actual adaptive-cost coefficients.

The literature audit did not find the identical conjunction among reviewed sources, but does not certify priority, rule out every possible reduction, or replace external peer review. Source URLs, an authored claim matrix and direct reduction checks are retained in [the novelty audit](../research/runs/novelty_audit_v1/claim_matrix.csv) and [decision report](../research/reports/novelty/NOVELTY_DECISION.md). Downloaded third-party full texts and raw page excerpts are not redistributed here.
