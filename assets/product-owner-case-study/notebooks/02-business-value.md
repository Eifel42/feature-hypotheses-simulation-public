# Notebook 02 — Business Value

Source notebook: [02-blockchain-case-study.ipynb](../../../apps/fhs/notebooks/02-blockchain-case-study.ipynb)
Overview: [Product Owner Case Study - Notebook 02](../product-owner-case-study.md#notebook-02---business-value)

This guide transfers the content of Notebook 02 in full so a reader who does not run Jupyter can still follow the method, the parameters, and the result. It walks the four-step simulation, explains every metric (Expected, VaR 95%, CVaR 95%, P95), shows the cost variants and the portfolio aggregation rule, and closes with the two board questions (budget check, rollout order).

## The Business Question

A regional farm business is choosing between three blockchain features. The exact parameters come from [blockchain.yaml](../../../apps/fhs/notebooks/config/blockchain.yaml).

| Hypothesis | Feature | What it aims to improve |
|:--:|---|---|
| **H1** | Simplified user interface | Retention and conversion through lower UX friction |
| **H2** | Complete traceability | New business value and trust through provenance |
| **H3** | Automatic expiration alerts | Waste reduction and operational efficiency |

The decision must replace opinions with a simple risk/return view that shows what value each feature produces and how low the floor can go.

> **Regulatory features** are built to meet legal or compliance requirements and are prioritised regardless of immediate financial return. None of H1/H2/H3 is regulatory here, so the financial gate applies to all three.

## Measuring Business Value: Customer-Facing vs. Internal Systems

Business value is **not one number**. It depends on what the feature is trying to improve and which type of information system it lives in. This case study uses the **customer-facing conversion model** because the three feature hypotheses target customer-facing behaviour. The simulation framework, however, is the same regardless of system type — only the **input units** change.

### The Two System Types

| | Customer-facing system | Internal system |
|---|---|---|
| **Examples** | Customer portal, e-commerce, marketing app, public API | Employee portal, internal tooling, compliance system, decision-support dashboard |
| **Who benefits** | External customers | Internal staff or organisational processes |
| **Adoption uncertainty** | High — depends on user behaviour, marketing, competition | Low — usage is mandated or strongly incentivised |
| **Value driver** | Revenue, conversion, retention | Time saved, errors avoided, decisions improved, compliance enforced |

### Concrete Measurement Models

The same `Users × Rate × Unit value` shape fits both system types — but the meaning of each factor changes:

| Model | Users | Rate | Unit value | Where it fits |
|---|---|---|---|---|
| **Customer-facing — conversion** | Visitors / month | Conversion rate | EUR per converted user | Customer portal, e-commerce, app store |
| **Internal — productivity** | Employees using the tool | Tasks per period | EUR saved per task (time × labour rate) | Internal tools, employee portals |
| **Internal — error reduction** | Events per period | Failure rate reduction | EUR avoided per failure | Compliance system, validation tool, monitoring |
| **Internal — decision support** | Decisions per period | Decision-quality lift | EUR per better decision | Analytics dashboard, alert system, BI tool |
| **Customer-facing — pricing** | Customers in segment | Adoption rate | EUR premium per adopter | Premium tier, paid feature, certification |

The Monte Carlo simulation in this case study runs **the same way** for any of these models. Only the YAML config values (`expected_users`, `conversion_rate`, `business_value_per_conversion`) change their interpretation. For an internal productivity case, `expected_users` becomes "tasks per quarter", `conversion_rate` becomes "share of tasks where the tool is used", `business_value_per_conversion` becomes "EUR saved per task".

### Why The Distinction Matters

- **Customer-facing value is highly uncertain.** It depends on user adoption, marketing, competition. The Monte Carlo spread is **wide** — VaR and CVaR diverge.
- **Internal value is more predictable.** Labour costs and task volumes are known. The spread is **narrower**, but the absolute value can be much larger because adoption is near 100%.
- **A risk-adjusted comparison only makes sense within one system type.** Mixing customer-facing-conversion features and internal-productivity features in the same portfolio requires careful **unit calibration** — they have the same dimension (EUR/period) but very different uncertainty profiles.
- **The case-study recommendation language ("CONDITIONAL GO", "development risk dominates") translates cleanly across system types** — only the absolute EUR numbers and the relative spread change.

The case study works as a **showcase**: it demonstrates the method on three customer-facing features. To use the same method for an internal portfolio, swap the YAML config and rerun — the entire decision chain (Notebooks 02–07) produces a directly comparable answer.

## Feature Inputs (Live From Config)

These values come directly from `blockchain.yaml`:

| Parameter | H1 Simplified UI | H2 Traceability | H3 Expiration Alerts |
|---|---:|---:|---:|
| Expected users | 10,000 | 15,000 | 80,000 |
| Conversion rate | 22% | 18% | 12% |
| Business value per conversion | EUR 14.00 | EUR 32.00 | EUR 5.50 |
| Uncertainty | 30% | 25% | 35% |
| Development cost | EUR 75,000 | EUR 55,000 | EUR 10,509 |
| Annual operating cost | EUR 25,000 | EUR 40,000 | EUR 3,000 |
| Annual growth rate | −20% | −10% | +15% |
| Installment years | 3 | 3 | 2 |
| Development weeks | 5 | 5 | 3 |
| Likelihood of non-completion (LLP) | 20% | 50% | 80% |
| Dependency cluster | Customer Experience Platform | Traceability Platform | Traceability Platform |
| Acceptance model | binomial | binomial | binomial |
| Planned release | R2 | R2 | R2 |

Scenario-wide: budget **EUR 155,000**, seed **73**, **100,000 scenarios**, discount rate **12%**.

### Year-1 Development Risk

The notebook surfaces a simple planning number per feature, independent of the Monte Carlo:

$$\text{Year-1 Development Risk} = \text{Expected BV} \times p_{\text{non-completion}}$$

- For the Product Owner: how much business value is at risk if this feature is not completed.
- For the Risk Manager: the expected business value exposure from development failure in Year 1.

This is **not** the Monte Carlo VaR 95% floor introduced below — it is planning context for prioritisation, not a percentile of the simulated distribution.

### Team Dependencies

`dependency_cluster` groups features that share a team or platform. H2 and H3 sit on the same cluster (Traceability Platform), which means they can fail together — relevant for portfolio risk, modelled explicitly in [Notebook 05](05-risk-resilience.md). Notebook 02 keeps feature calculations independent for readability.

## How The Simulation Works — Four Steps

The notebook walks through one example feature (H1) end to end. Every other feature follows the same procedure.

### Step 1 — Deterministic Formula

Without uncertainty, the tool computes one expected number:

$$\text{Expected Business Value} = \text{Users} \times \text{Conversion Rate} \times \text{Value per Conversion}$$

For H1: `10,000 × 0.22 × 14.00 = EUR 30,800`. This is the "spreadsheet answer" — one point, no spread.

### Step 2 — Add Uncertainty

The conversion rate is not fixed; it is drawn fresh for every scenario. The simulator selects the distribution by the `uncertainty` value:

- **Uncertainty below 30%** → symmetric bell curve (Normal distribution).
- **Uncertainty 30% or higher** → right-skewed curve (Lognormal distribution).

In this case study:
- H1 (uncertainty 30%) → Lognormal (the rule uses ≥30%, H1 sits exactly at the boundary).
- H2 (uncertainty 25%) → Normal.
- H3 (uncertainty 35%) → Lognormal.

A Lognormal draw means the long tail points to the high side — most scenarios near plan, a few significantly above, fewer significantly below.

### Step 3 — Acceptance Model

With `acceptance_model: binomial`, each simulated user independently converts (or not) — the simulator draws from `Binomial(n_users, conversion_rate)`. This produces realistic whole-number conversion counts instead of a single averaged percentage. The alternative (Bernoulli per user with averaged rate) is faster but loses the integer granularity that matters for small user populations.

### Step 4 — Run All Scenarios

100,000 scenarios are drawn (the configured `scenarios` value). Each scenario produces one Business Value number. Collected together, they form a full distribution with four key readings:

| Number | Definition | Use |
|---|---|---|
| **Expected** | Mean across all scenarios | Planning baseline |
| **VaR 95% (business value floor)** | 5th percentile of the distribution | Worst-case budget guardrail |
| **CVaR 95% (tail)** | Average of all scenarios at or below the floor | Defending downside in steering |
| **P95 (ceiling)** | 95th percentile | Optimistic case — do not plan with it |

The deterministic number from Step 1 and the simulation mean from Step 4 are close. The added value of the simulation is the **spread** — the floor and the ceiling that a single-point estimate cannot show.

## Year 1 At A Glance — Business Value vs. Costs

The notebook produces one table that puts all Year-1 numbers side by side per feature, plus a portfolio row:

| Column group | What it shows |
|---|---|
| **(a) Business Value** | Expected, VaR 95% floor, CVaR 95% tail — straight from the Monte Carlo |
| **(b) Variant 1 — Full Investment** | Expected BV minus the full development cost and Year-1 opex |
| **(c) Variant 2 — Year-1 P&L** | Expected BV minus the annual installment charge and Year-1 opex |

Reading rules:

- **Net Year 1 (V1)** = `Expected − development_cost − annual_operating_cost`.
- **Net Year 1 (V2)** = `Expected − development_cost / installment_years − annual_operating_cost`.
- A **green +** means the feature covers its costs in Year 1. A **red −** means it does not — which may still be acceptable over a multi-year horizon (see [Notebook 03](03-financial-return.md)).

### Variant 2 — Proportional Installment View

Variant 2 replaces the full one-time investment charge with the annual installment slice:

$$
\text{Net}_{\text{V2}} = BV - \frac{C_{\text{dev}}}{n_{\text{years}}} - C_{\text{opex Y1}}
$$

This is the **P&L / accounting perspective**: the income statement sees only the installment slice each year, not the full cash outlay on day one. For H1 over 3 years that means the investment charge per year is `75,000 / 3 = EUR 25,000` instead of the full EUR 75,000.

### Why Portfolio VaR Is Not A Sum

The portfolio row comes from the **combined Monte Carlo** — every scenario sums the three feature draws, then the percentiles are computed on the combined distribution. The portfolio VaR 95% is therefore **not the sum of the three feature VaRs**. Diversification matters: bad outcomes in one feature can be offset by good outcomes in another, so the floor of the sum is higher than the sum of the floors. The combined simulation captures this automatically.

## Comparing The Downside Across Features

The notebook overlays the three feature distributions on a common x-axis. Two patterns become visible:

- **Features with higher `uncertainty` produce wider distributions.** H3 (35%) is wider than H1 (30%) which is wider than H2 (25%).
- **Features with `uncertainty` ≥ 30% are right-skewed.** Their downside is *narrower* than the upside — most bad scenarios stay close to plan, the worst tail extends further.

The bar comparison shows two bars per feature: solid bar for Expected, faded bar for VaR 95% floor. The **gap between them is the downside exposure** — the business value you could lose compared to plan in a bad scenario. The Product Owner question:

> Is this gap acceptable, or should we invest in user research to reduce uncertainty?

Lowering uncertainty narrows the distribution and shrinks the gap. The tutorial [T01 — Distribution Guide](../../../apps/fhs/notebooks/tutorial/01-distribution-guide.ipynb) explains the mechanics.

## VaR vs. CVaR — Reading The Tail

VaR 95% answers "where is the floor?" CVaR 95% answers "what happens *below* the floor?"

CVaR (Conditional Value at Risk, also called Expected Shortfall) is the **average** of all scenarios that fall at or below the VaR 95% threshold. Two examples make the difference concrete:

- VaR 95% = EUR 200k and CVaR = EUR 190k → the bad scenarios stay close to the floor. **Low tail risk.**
- VaR 95% = EUR 200k and CVaR = EUR 50k → some bad scenarios are much worse than the floor. **High tail risk.**

**The smaller the gap between VaR and CVaR, the more predictable the worst case.** This is why VaR alone is misleading: it tells you where the cliff is, not how steep the drop is.

In this case study, the combined reading points to H2 first (strong expected value AND strong floor), H3 as a low-capital test (good value-to-cost, but wide spread), and H1 as too weak for its planned investment.

## Combined Portfolio View

The notebook builds the combined view by adding the per-feature business value draws scenario by scenario. The combined distribution is smoother than the single-feature charts because of diversification.

The contribution breakdown shows which feature dominates the portfolio and which features mainly add incremental value or improve resilience.

The portfolio KPI card carries:

- Expected portfolio Business Value
- Portfolio VaR 95% (combined floor)
- Portfolio CVaR 95% (combined tail)
- Portfolio volatility (standard deviation of the combined distribution)

### Cost Deduction At Portfolio Level

The same Variant 1 / Variant 2 rule applies on the portfolio:

| View | Deducted | When to use |
|---|---|---|
| **Variant 1 (cash-flow)** | Sum of development investments + sum of Year-1 opex | Comparing against annual budget ceiling |
| **Variant 2 (P&L)** | Sum of Year-1 installments + sum of Year-1 opex | Finance team capitalises development spend |

Four statistics are reported (Expected, VaR 95%, CVaR 95%, P95) so the picture is visible at every point of the distribution, not only at the mean.

## Annual Operating Cost — Inflation Simulation

Building a feature is a one-time investment. Running it is a recurring cost. The notebook simulates annual opex with a **uniform inflation factor** drawn between 0% and the configured maximum (default 25%). One factor is drawn per scenario and applied uniformly to all features — the assumption is that infrastructure cost drivers (hosting, energy, licences) move together.

The opex table per feature:

| Column | Meaning |
|---|---|
| **Base (EUR/yr)** | Configured annual operating cost, no inflation |
| **Expected** | Mean simulated cost across all scenarios |
| **Worst Case** | Cost at the maximum inflation rate |
| **Inflation Impact** | Worst Case − Base — the additional spend in the stressed case |

For the three features:

| Feature | Base | Worst Case at +25% |
|---|---:|---:|
| H1 | EUR 25,000 | EUR 31,250 |
| H2 | EUR 40,000 | EUR 50,000 |
| H3 | EUR 3,000 | EUR 3,750 |

## Two Board Questions

### Question 01 — Initiative Budget Check

The simplest possible check:

$$C_{\text{total}} = \sum_i C_{\text{feature},i}, \qquad B_{\text{remaining}} = B_{\text{budget}} - C_{\text{total}}$$

Decision rule:

- `B_remaining ≥ 0` → all features fit the budget.
- `B_remaining < 0` → portfolio is over budget.

For the case study: development costs sum to `75,000 + 55,000 + 10,509 = EUR 140,509`. Budget is EUR 155,000. `B_remaining = EUR 14,491` — all three features fit the development budget on paper. (Year-1 opex of `25,000 + 40,000 + 3,000 = EUR 68,000` is *not* deducted at this gate. It is the next gate, and it is what makes the full-build case fail in [Notebook 04](04-portfolio-and-budget.md).)

### Question 02 — Rollout Ordering

> Which feature should go live first to maximise early business value return?

The notebook ranks the features by simulated expected Business Value (highest first = Phase 1). This is the simulated number, not the deterministic one — it already includes uncertainty.

Read the Overview for the final rollout outcome and the GO / CONDITIONAL GO / REVIEW recommendation that the steering board sees.

## What A Product Owner Should Walk Away With

- **H2 is the strongest value anchor** — highest expected BV and strongest floor in the simulation.
- **H3 is attractive on low capital** — small development cost, useful value, but wide relative spread because of the high `uncertainty` and high LLP.
- **H1 is too weak for its planned investment** — the expected value does not justify the cost over the planned horizon.

Three Scrum-language uses for the same decision basis:

| Backlog question | What this notebook gives you |
|---|---|
| Why move H2 up? | Strongest expected value AND strongest floor — both numbers point the same way. |
| Why test H3 first instead of funding it fully? | Useful value at low capital, but the spread is wide → de-risk by running it as a test. |
| Why hold H1? | Expected value below the planned investment — and the floor confirms the bad cases are not flukes. |

## Glossary

| Term | Definition |
|---|---|
| **Expected Business Value** | Mean of all simulated Business Value scenarios for a feature. |
| **VaR 95% (Business Value Floor)** | 5th percentile of the simulated distribution. 95 out of 100 scenarios produce a value above the floor. |
| **CVaR 95% (Tail)** | Average of all scenarios at or below the VaR 95% floor — the expected shortfall. |
| **P95** | 95th percentile of the simulated distribution — the upper-side counterpart of VaR. Not for planning. |
| **Year-1 Development Risk** | Expected BV × probability of non-completion. Planning context, not a simulation percentile. |
| **LLP** | Likelihood of non-completion — config parameter `likelihood_of_non_delivery`. |
| **Binomial acceptance** | Each user converts independently with the configured rate — produces integer conversion counts. |
| **Diversification effect** | Reason portfolio VaR is higher than the sum of feature VaRs — bad outcomes do not all hit simultaneously. |
| **Variant 1 / Variant 2** | Cash-flow vs. P&L cost view. V1 deducts full development cost in Year 1, V2 deducts the annual installment slice. |

## Next

Once business value is sized, the next question is whether the investment pays back over time after discounting and financing decisions: [Notebook 03 — Financial Return](03-financial-return.md).
