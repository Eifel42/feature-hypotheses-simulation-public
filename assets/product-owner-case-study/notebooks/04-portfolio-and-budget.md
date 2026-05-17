# Notebook 04 — Portfolio And Budget

Source notebook: [04-blockchain-case-study-advisor.ipynb](../../../apps/fhs/notebooks/04-blockchain-case-study-advisor.ipynb)
Overview: [Product Owner Case Study - Notebook 04](../product-owner-case-study.md#notebook-04---portfolio-and-budget)

This guide transfers Notebook 04 — the move from "which feature creates value" to "which bundle of features should we build". It walks the ILP optimiser, the three objective formulas, the decision-governance thresholds (who actually approves the spend), and the role-specific reading.

## The Question Changes

Notebooks 02 and 03 evaluated each feature on its own. Notebook 04 changes the question: at a given budget, **which combination of features creates the most value?** The decision is no longer "build H1 or not" — it is "given EUR 155,000, which subset of {H1, H2, H3} should we fund?"

| Horizon | What it answers | Use |
|---|---|---|
| **3 Years (primary)** | Does the feature create value over its planned investment period? | Roadmap budget decision |
| **Year 1 (payback check)** | Does the feature pay back within one year? | Conservative cross-check |

The two horizons can disagree. When they do, the disagreement carries information: a feature with negative Year-1 NPV but positive 3-year NPV is a **growth bet** — acceptable if the business can wait, risky if cash is tight.

> The optimiser uses Option A (upfront investment) from [Notebook 03](03-financial-return.md). All development cost is paid in Year 0; operating costs are deducted from business value each year. ILP (linear) optimisation only — no installment spreading.

## The ILP Solver

The selection problem is solved as **Integer Linear Programming (ILP)**. Each feature is either selected (variable = 1) or not (= 0). The solver finds the subset of features that:

- **Maximises** the chosen score (NPV at 3 years, NPV at Year 1, or VaR floor — see below).
- **Subject to** the constraint that the sum of `development_cost` over selected features is at most the budget.

ILP is the right tool here for two reasons:

- It guarantees the **optimal** combination within the budget — not a greedy approximation.
- All three score functions (below) are **linear and additive** per feature — exactly the form ILP solves efficiently.

For three features the ILP problem is small enough to enumerate by hand (`2³ = 8` subsets). The solver still runs because the same algorithm scales to 10, 50, or 200 features in the advanced notebooks ([A01](../../../apps/fhs/notebooks/advanced/01-portfolio-advisor.ipynb)).

## The Three Objective Formulas

The notebook compares three score formulas under the same ILP framework:

| Objective | Idea | Best for |
|---|---|---|
| `var_floor` | VaR 95% floor minus development cost | Risk-first: protect against worst-case losses |
| `npv_year1` | Discounted Year-1 net cash flow minus cost | Fast payback: does it pay back within one year? |
| `npv_3year` | Sum of 3-year discounted net cash flows minus cost | Growth: does it create value over the full horizon? |

The exact score per feature for each objective (C = development cost, r = discount rate, g = annual growth rate):

**`var_floor` score:**

$$S_{\text{var}} = \mathrm{VaR}_{95} - C$$

**`npv_year1` score:**

$$S_{\text{Y1}} = \frac{BV_1 - OpEx_1}{1+r} - C$$

**`npv_3year` score:**

$$S_{\text{3Y}} = \sum_{t=1}^{3} \frac{BV_t \cdot (1+g)^{t-1} - OpEx_t}{(1+r)^t} - C$$

Reading the formulas:

- **`var_floor`** uses the *simulated* VaR 95% floor from [Notebook 02](02-business-value.md) minus the upfront cost. This selects the bundle with the strongest downside protection. Use it when you cannot afford a worst-case shortfall.
- **`npv_year1`** is the simplest form of NPV: one year of business value minus one year of opex, discounted once, minus the upfront cost. A feature passes this gate only if Year-1 cash flow alone covers a significant share of the investment.
- **`npv_3year`** is the standard NPV formula across three years, with the per-feature `annual_growth_rate` (config) compounding the business value year over year. A feature with negative `annual_growth_rate` decays; one with positive growth strengthens over time.

All three score functions are **per-feature additive** — the portfolio score is the sum of per-feature scores. That is what makes the ILP solver applicable: no cross-feature interaction terms.

## Budget Sweeps

The notebook runs the same optimiser at three budget levels: 25%, 50%, and 100% of EUR 155,000. The result is a small table:

- **At low budget**: only one feature fits — the optimiser picks the one with the best NPV per euro (effectively PI ranking).
- **At medium budget**: a different combination emerges depending on the horizon.
- **At full budget**: H2 + H3 is the strongest bundle by both NPV objectives; the leftover is held as reserve. Spending the remaining capital on H1 would *reduce* the total NPV because H1's NPV is negative.

This is the central insight the Overview captures: **the best decision is not always to spend the full budget.** Budget discipline means spending where the roadmap gets the best risk-adjusted result, not maximising spend.

> When 3-year NPV and Year-1 NPV agree on the bundle → high confidence. When they disagree → the feature needs growth to pay off (acceptable when the business can wait, risky when cash is tight).

## What The Table Reveals

Four patterns recur across budget levels:

- **Budget drives the decision.** The same optimiser picks different features at different budgets. There is no single "right" portfolio — only the optimal one for a given budget.
- **Time horizon matters.** A feature with negative Year-1 NPV can have positive 3-year NPV if growth kicks in over time. The 3-year view may include features the Year-1 view skips.
- **One table, two perspectives.** The Product Owner picks the row matching the planning horizon. No separate ROI, IRR, or multi-year tables needed.
- **Upfront investment model.** Development cost is paid at Year 0; operating costs accrue each year. Installment financing is a separate analysis in [Notebook 03](03-financial-return.md).

## Decision Governance — Who Approves?

The optimiser tells you **which** features to build. It does **not** tell you who in the organisation is allowed to approve them. The notebook proposes three escalation tiers based on the risk profile of the selection:

| Condition | Decision Level | Why |
|---|---|---|
| Business Value Floor > investment cost | **Product team** decides autonomously | Conservative floor exceeds cost — low risk |
| Business Value Floor < 0, but Expected Value > cost | **Department head** approval required | Positive average, but real downside — needs oversight |
| CVaR 95% < −1× investment | **CFO / executive board** review | Worst-case losses exceed the entire investment — strategic decision |

These thresholds are examples; every organisation has its own risk appetite. A tech startup may accept higher risk autonomously; a regulated company may require board approval earlier.

> **Why this matters for Product Owners:** without clear escalation rules, every feature decision becomes a political discussion. With these thresholds, the Product Owner can say *"our business value floor is above cost — the data supports autonomous approval"* or *"CVaR exceeds investment — this needs the CFO"* and reach the decision without a power struggle.

## Why Reserve Beats Maximum Spend

The headline reserve in this case study is **EUR 89,491**. The arithmetic:

- Budget: EUR 155,000.
- Selected bundle (H2 + H3): `55,000 + 10,509 = EUR 65,509`.
- Reserve: `155,000 − 65,509 = EUR 89,491`.

The reserve has a concrete purpose: it stays available for the next decision gate. If [Notebook 05](05-risk-resilience.md) or [Notebook 06](06-development-cost-risk.md) surfaces a tail risk that needs mitigation budget, the reserve covers it. If H1's value case strengthens later (better growth data, lower development risk), the reserve can fund a re-evaluated H1.

Spending the reserve on H1 *today* would worsen the portfolio NPV — that is the optimiser's answer. The Overview row "Defer H1 — until the business value case improves" is the direct consequence.

## What A Product Owner Should Walk Away With

- **The best decision is not always to spend the full budget.** Sometimes the optimal answer is a smaller bundle plus reserve.
- **Two features beat one feature beat zero features only when the math says so.** ILP picks the math, not the politics.
- **Budget level changes the bundle.** Run the optimiser when the budget changes — do not assume the same bundle holds.
- **Horizon agreement is a confidence signal.** When 3-year and Year-1 NPV agree, the bundle is robust. When they disagree, scrutinise the growth assumptions.
- **Decision governance prevents political debate.** Tie approval level to the risk profile, not to seniority or volume.

Three Scrum-language uses:

| Backlog question | What this notebook gives you |
|---|---|
| Why fund this slice now and hold the rest? | The optimiser picks the highest-NPV subset that fits the budget. |
| Why keep reserve when there is budget left? | Spending it on the wrong feature reduces total NPV. |
| Why does this decision not need the CFO? | BV Floor > Investment Cost — the governance threshold supports autonomous approval. |

## Glossary

| Term | Definition |
|---|---|
| **ILP** | Integer Linear Programming — exact solver that guarantees the optimal feature combination within a budget constraint. |
| **Objective function** | The score the solver maximises. Here: `var_floor`, `npv_year1`, or `npv_3year`. |
| **NPV** | Net Present Value — sum of discounted future cash flows minus upfront investment. NPV > 0 = value-creating. |
| **PI** | Profitability Index — NPV per euro of invested capital. Ranks features by capital efficiency. |
| **Discount rate** | Minimum annual return required on an investment. The case study uses 12%. |
| **Upfront investment** | All development cost paid in Year 0 (Option A from [Notebook 03](03-financial-return.md)). No installment spreading. |
| **Business Value Floor 95** | The 5th percentile of the simulation. 95% of scenarios produce a result above this floor. |
| **Annual growth rate** | Per-feature multiplier applied to business value year over year. Config parameter `annual_growth_rate`. Negative = decay; positive = growth. |
| **Reserve** | Unspent budget held for the next decision gate or mitigation. Not "money left over" — money kept for a future decision. |

## Next

The portfolio choice (H2 + H3) is the input to the risk-resilience stress test in [Notebook 05 — Risk Resilience](05-risk-resilience.md), where the bundle is subjected to development, market, component, and global shocks.
