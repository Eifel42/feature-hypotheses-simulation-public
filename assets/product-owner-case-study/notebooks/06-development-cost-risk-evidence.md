# Notebook 06 — Deployment Cost Risk

Source notebook: [06-blockchain-case-study-development-risk.ipynb](../../../apps/fhs/notebooks/06-blockchain-case-study-development-risk.ipynb)
Overview: [Product Owner Case Study - Notebook 06](../PRODUCT-OWNER-CASE-STUDY.md#notebook-06---development-cost-risk)

This guide transfers Notebook 06 — the pure development cost-and-schedule risk view. It defines the planned vs. actual sprint model (lognormal moment-matched), explains the cancellation rule and sunk cost, defines CaR 95% and CVaR 95% with the distinction between them, walks the budget-pressure metric, and ends with the cost-risk feature selection.

## The Question

Will this feature stay within budget if the team runs late? Notebook 06 is **pure development cost and schedule risk** — business value is not modelled here (it lives in [Notebook 02](02-business-value-evidence.md)) and risk to value lives in [Notebook 05](05-risk-resilience-evidence.md). The output of this notebook is one set of numbers:

- How often development runs over the planned sprint count.
- How much more it costs in a bad case.
- Which features are most likely to blow the budget.

## How The Simulation Works

Each feature has a planned number of sprints based on its estimated development weeks. The simulation runs thousands of scenarios — in each scenario, the actual sprint count is drawn from a **truncated lognormal distribution** moment-matched to the plan. Most scenarios finish close to plan; a small number run significantly late.

### Planned Sprints

$$S_{\text{plan}} = \left\lceil \frac{W}{L} \right\rceil$$

where `W` = `development_weeks` (from config) and `L` = `sprint_length` (default 2 weeks). The ceiling means a feature estimated at 5 weeks needs 3 sprints — even though 2.5 sprints "would do" in continuous time, sprints are discrete units.

For the case study features (sprint length 2 weeks):

| Feature | `development_weeks` | `S_plan` |
|---|---:|---:|
| H1 Simplified UI | 5 | 3 |
| H2 Traceability | 5 | 3 |
| H3 Expiration Alerts | 3 | 2 |

### Actual Sprints — Lognormal Moment-Matched

The actual sprint count follows a **truncated lognormal distribution**, moment-matched so that:

- The **expected value** equals the planned sprint count.
- The **standard deviation** equals planned sprints × the configured uncertainty.

Formally:

$$E[X] = S_{\text{plan}}, \qquad \text{Std}[X] = S_{\text{plan}} \cdot \sigma_{\text{delay}}$$

The distribution is **truncated at** `S_plan × c_ceil` — the sprint ceiling from config. The draw is then rounded **up** to a whole sprint number.

Log-space parameters (derived by moment-matching):

$$\sigma_{\mathrm{log}} = \sqrt{\ln(1 + \sigma_{\text{delay}}^2)}, \qquad \mu_{\mathrm{log}} = \ln(S_{\text{plan}}) - \tfrac{1}{2}\,\sigma_{\mathrm{log}}^2$$

The lognormal shape is the right choice because it captures the empirical pattern: **most projects finish close to plan, but a small fraction run significantly late**. The distribution has a long right tail — exactly what real teams experience. Rare on-time-early, common slightly-late, occasional very-late.

### Why Lognormal — Empirical Evidence

The lognormal shape is not arbitrary. IT-project research consistently finds right-skewed delay distributions:

- **Standish Group CHAOS Reports** show ~30% of IT projects finish on time and on budget; the distribution of overruns is right-skewed.
- **McKinsey/Oxford research** on large IT projects: 45% run over budget, 7% run over time, with cost overruns averaging 45% of the planned budget.

The specific parameters (sprint uncertainty, sprint ceiling, cancellation thresholds) are **configurable estimates**, not universal truths. A team with two quarters of recorded velocity data should override `sprint_uncertainty` with values from its own history.

> **Calibrate with your own data.** Two sprints of team data are more valuable than any industry benchmark.

### Development Cost Per Scenario

$$C_{\text{actual}} = S_{\text{actual}} \times L \times \frac{C_{\text{dev}}}{W}$$

where `C_dev` is the planned development cost, `W` is the planned weeks, and `S_actual × L` is the actual development duration in weeks. The factor `C_dev / W` is the implicit **weekly burn rate** — the cost per week the team consumes.

More sprints → more team-weeks → more cost. The burn rate is held constant: only sprint count varies.

### The Cancellation Rule

A cancellation check fires when the simulated sprint count exceeds `S_plan + max_sprints_over_plan`:

- If the check fires, cancellation occurs with probability `cancellation_probability` (configured at 80% in this case study).
- When a feature is cancelled, **business value is zero** — the feature is not delivered.
- The cost is the spend **already accrued up to the trigger point** (`S_plan + Δ_max` sprints). This is the **sunk cost** — money already spent that cannot be recovered.

For the case study (`max_sprints_over_plan` = 2, `cancellation_probability` = 80%):

| Feature | `S_plan` | Cancellation trigger sprint | Sprint ceiling (1.5x `S_plan`, rounded up) |
|---|---:|---:|---:|
| H1 | 3 | 5 | 5 |
| H2 | 3 | 5 | 5 |
| H3 | 2 | 4 | 3 |

With the current 1.5x sprint ceiling, the cancellation trigger is at or above the maximum possible sprint draw. H1 and H2 can reach the trigger boundary at 5 sprints, but the cancellation rule fires only when actual sprints exceed the trigger. H3 cannot reach its 4-sprint trigger because the ceiling caps it at 3 sprints. The main H3 risk is therefore early schedule pressure, not cancellation frequency.

> Sunk costs are money already spent and not recoverable. Track them to set review gates — if cancelling after Sprint 4 costs 120k, consider a decision point at Sprint 3.

## Development Setup In This Case Study

The Overview lists the configured parameters in one table. All values come from the `deployment_risk:` block in [blockchain.yaml](../../../apps/fhs/notebooks/config/blockchain.yaml) — the notebook reads them directly; nothing is hard-coded.

| Parameter | YAML key | Value | Meaning |
|---|---|---|---|
| Sprint length | `sprint_length_weeks` | 2 weeks | Six sprints fit in one quarter |
| Quarterly capacity | `quarterly_capacity_sprints` | 6 sprints | Development capacity per quarter |
| Sprint uncertainty | `delay_model.sprint_uncertainty` | 30 (approx. +/-30%) | Around 68% of sprints finish within +/-30% of plan |
| Sprint ceiling | `delay_model.sprint_ceiling` | 1.5 | No scenario assumes worse than 1.5 times the planned duration |
| Cancellation threshold | `cancellation.max_sprints_over_plan` / `cancellation_probability` | 2 / 0.8 | At more than two sprints over plan there is an 80% chance the feature is cancelled |

To adjust any of these in a what-if analysis, edit `blockchain.yaml` and re-run the notebook. The Pydantic schema (`fhs.core.model.config.DeliveryRiskConfig`) is the single source of truth for validation.

## Capacity Check — Sprint Plan

Before running the simulation, the notebook checks whether the planned features even fit one quarter. Add up the per-feature `S_plan` values and compare to `quarterly_capacity`.

For the case study: `3 + 3 + 2 = 8 planned sprints`. Quarterly capacity is `6 sprints`. **The portfolio is over capacity on paper** — before any uncertainty is added.

What this means:

- **Fits:** the team can deliver everything within the quarter on plan.
- **Over capacity:** the team is overloaded before any delays occur. The cost-risk numbers in the next sections are computed independently of capacity — if the team forces all three features into one quarter, **realised risk is worse than the simulated numbers** because the simulation assumes each feature has its own runway.

The two roles read this differently:

- **Product Owner:** descope or split releases before sprint start.
- **Risk Manager:** capacity overrun = schedule pressure exists even before uncertainty.

## Delay Analysis — How Far From Plan?

For each feature, the notebook reports the actual sprint count at three percentiles plus a cancellation rate:

| Column | Meaning |
|---|---|
| **Planned sprints** | `S_plan = ceil(W / L)` — from config |
| **P50 actual** | Half of scenarios finish within this many sprints |
| **P75 actual** | 75% finish within this |
| **P95 actual** | 95% finish within this; 5% go beyond |
| **P50 / P75 / P95 overrun** | Extra sprints beyond plan at each percentile |
| **Cancelled %** | Share of scenarios where the feature was cancelled |

The chart shows the full sprint-count distribution per feature — how spread out development estimates are around the plan. With the current 1.5x ceiling, H1 and H2 are capped at 5 actual sprints, while H3 is capped at 3 actual sprints.

## Cost Risk — CaR 95% vs. CVaR 95%

The simulation produces a distribution of development costs per feature. The notebook reports three headline numbers:

- **Expected cost** — average across all scenarios. Slightly above plan because overruns are more common than finishing early.
- **CaR 95% (Cost at Risk)** — the cost level exceeded in only 5% of scenarios. A *point estimate* of the worst-case boundary.
- **CVaR 95% (Conditional Value at Risk, Expected Shortfall)** — the **average** cost across the worst 5% of scenarios.

The distinction matters:

> **CaR answers:** *How bad can it get within the 95% confidence window?*
> **CVaR answers:** *When it breaks that limit, how bad is it on average?*

Two feature subsets can have **identical CaR 95% but very different tail behaviour** beyond that point. CVaR captures the full severity of the tail — making it the right criterion when you want to minimise what development actually costs when things go wrong, not just where the cliff is.

There is a second technical reason CVaR beats CaR in this model: sprint-based costs are **step functions** — each extra sprint adds a fixed cost block. The 95th percentile often lands on the same sprint count for every feature, making CaR-based ranking meaningless. CVaR averages across the full tail and produces continuous, differentiating values.

### Three Reading Rules

The Overview captures the three usage rules — they are worth restating in PO language:

- **Expected development cost** → size the **planning reserve** in the release plan.
- **CaR 95% (Loss at Risk 95%)** → use as the **upper guardrail in steering** — the budget level that should not be exceeded outside of rare scenarios.
- **CVaR 95%** → use in the **funding-gate decision** — it answers *"how bad does it get on average when it goes wrong, and can we still cover it?"*

> The business value floor measures the floor of business value; LaR / CaR measures the ceiling of potential loss. They look at the same distribution from opposite sides.

## Budget Fit — Cost Risk Selection

The final section ranks features by budget pressure and selects the best subset under the budget constraint.

### Budget Pressure Per Feature

$$\text{Budget pressure} = \frac{\mathrm{CVaR}_{95}}{C_{\text{plan}}} - 1$$

This is a **proportional** metric: "by how much does the worst-case expected cost exceed what was planned for this feature?" It is comparable across features regardless of absolute EUR size.

The ranking table columns:

| Column | Meaning |
|---|---|
| **Priority** | 1 = lowest budget pressure — safest to schedule first |
| **Planned investment** | `C_plan` — approved budget for this feature |
| **CVaR 95%** | Average development cost in the worst 5% of sprint scenarios |
| **Budget pressure** | `(CVaR_95% / C_plan) − 1` |

For the case study with the current 1.5x sprint ceiling, the individual feature CVaR values hit the configured ceiling. That makes the feature-level budget pressure similar across H1, H2, and H3. The practical difference is therefore not the individual pressure percentage alone: H2 dominates absolute EUR exposure, while H3 still needs scope control because its short planned duration leaves little room before the ceiling is reached.

### Why Normalise By Total Planned Cost

A combination of three short, cheap features will always have a lower **absolute** CVaR than a combination of three longer, more expensive features — simply because the total cost is smaller. That is not a risk difference; it is a scale difference. Normalising removes the scale effect:

$$\text{Portfolio budget pressure} = \frac{\text{Portfolio CVaR}_{95}}{\sum_{i \in S} C_{\text{plan}, i}} - 1$$

This is the right metric for **comparing combinations of different sizes** under one budget.

### Cost Risk Selection Algorithm

The two-step algorithm:

1. **Maximise feature count** — find the largest number of features whose planned costs fit within the scenario budget.
2. **Minimise portfolio budget pressure** — among all combinations of that count, pick the one with the lowest `CVaR_95% / total planned cost − 1`.

In formula form, the portfolio CVaR is the conditional expectation of the per-scenario cost sum, given that this sum is at or above its 95th percentile `Q₀․₉₅`:

$$\text{Portfolio CVaR}_{95} = E\left[ T \mid T \geq Q_{0.95} \right] \quad \text{where } T = \sum_{i \in S} C_{\text{actual}, i}$$

`Q₀․₉₅` is computed on the **portfolio** cost distribution (sum per scenario, then take the percentile of the sum — not the sum of per-feature percentiles).

The algorithm output:

| Output | Meaning |
|---|---|
| **Selected features** | Largest subset fitting the budget, with the lowest normalised worst-case cost |
| **Total planned cost** | Sum of `development_cost` for selected features |
| **Budget remaining** | Unallocated scenario budget after selection |
| **Budget pressure** | `CVaR_95% / total planned cost − 1` |
| **Expected development cost** | Mean portfolio development cost across all scenarios |
| **Portfolio CaR 95%** | 95th percentile of portfolio development cost |
| **Portfolio CVaR 95%** | Average portfolio cost in the worst 5% — the minimised metric |

## What A Product Owner Should Walk Away With

- **A low planned investment does not mean low development risk.** H3 is the cheapest feature on paper, but its short planned duration leaves little room before the ceiling is reached.
- **A cancelled feature still costs money.** Every sprint up to the cancellation trigger is sunk cost without business value.
- **The portfolio can fit the planned budget and still become uncomfortable in the development tail** — especially when the planned sprint count exceeds quarterly capacity.
- **CaR is a point on the cliff; CVaR is the average fall.** Use CVaR for ranking and funding decisions, CaR only as a guardrail.
- **Normalise across feature combinations.** Absolute CVaR favours small bundles automatically; that is a scale artefact, not better risk.

Combined with the portfolio choice from [Notebook 04](04-portfolio-and-budget-evidence.md) (H2 + H3), the implication is direct:

- Hold **H2 inside one release window** because its absolute cost dominates the development risk.
- Apply a **tight scope gate to H3** because its relative cost range is widest even though the current sprint ceiling prevents the cancellation rule from firing.

Three Scrum-language uses:

| Backlog question | What this notebook gives you |
|---|---|
| Why reduce H3 scope before sprint commitment? | Shortest schedule buffer; current ceiling prevents cancellation, so scope must be controlled earlier. |
| Why is H2's release window critical? | Absolute CVaR dominates the portfolio development cost — one release window keeps it contained. |
| Why book reserve for the development tail? | Expected cost is above plan; LaR/CaR sits well above the planned investment. |

## Glossary

| Term | Definition |
|---|---|
| **Sprint overrun** | When actual sprint count exceeds the planned sprint count for a feature. |
| **Sunk cost at cancellation** | Development cost already accrued up to the cancellation trigger point (`S_plan + Δ_max` sprints). Remaining work is abandoned. |
| **Development risk** | Probability that schedule overruns, cost variability, or cancellation causes development cost to exceed the planned investment. |
| **VaR / CaR 95%** | Cost threshold not exceeded in 95% of scenarios — a point estimate of worst-case cost. |
| **CVaR 95% (Expected Shortfall)** | Average development cost across the worst 5% of scenarios. Always ≥ CaR 95%. Coherent risk measure — captures full tail severity, not just the boundary. |
| **Feature budget pressure** | `(CVaR_95% / C_plan) − 1` — how far a feature's worst-case development cost exceeds its planned investment. |
| **Portfolio budget pressure** | `Portfolio CVaR_95% / total planned cost − 1` — same metric on the bundle. |
| **Portfolio CVaR 95%** | CVaR 95% of the per-scenario sum of development costs across selected features. The metric the selection algorithm minimises. |
| **Lognormal distribution** | Distribution used to draw sprint delay factors. Long right tail: most scenarios finish near plan, a small fraction run significantly late. |
| **Moment matching** | Setting the lognormal parameters `μ_log`, `σ_log` so that the resulting distribution has the prescribed expected value and standard deviation. |
| **Sprint ceiling** | Upper truncation of the actual-sprint draw — `S_plan × c_ceil`. No scenario assumes worse than this many sprints. |
| **Cancellation trigger** | `S_plan + Δ_max` — sprint count at which the cancellation rule begins to fire. |

## Next

Deployment cost is the last evidence layer. The synthesis — turning all five dimensions (Business Value, Financial Return, Portfolio Choice, Risk Resilience, Deployment Cost Risk) into one executive recommendation with a traffic-light verdict — is [Notebook 07 — Executive Decision Evidence](07-executive-decision-evidence.md).
