# Notebook 05 — Risk Resilience

Source notebook: [05-blockchain-case-study-risk.ipynb](../../../apps/fhs/notebooks/05-blockchain-case-study-risk.ipynb)
Overview: [Product Owner Case Study - Notebook 05](../PRODUCT-OWNER-CASE-STUDY.md#notebook-05---risk-resilience)

This guide transfers Notebook 05 — the risk dashboard. It defines the four risk dimensions (Development, Market, Component, Global) with their formulas and parameters, walks the risk waterfall, compares the four ranking strategies (`var_floor`, `risk_ratio`, `rorac`, `risk_adjusted_roi`), explains the sensitivity heatmap, and ends with role-specific decision briefs and industry benchmarks.

## The Question

What can go wrong with the feature portfolio (H2 + H3 from [Notebook 04](04-portfolio-and-budget-evidence.md)), and how much business value is at risk after all sources of failure are applied? The Notebook 04 decision says "fund this bundle". Notebook 05 tests whether the bundle is **resilient enough to survive realistic setbacks**.

## The Four Risk Dimensions

The notebook applies four risk layers sequentially. Each scenario passes through all four gates in order: Development → Market → Component → Global.

| Risk | What happens to business value | Probability |
|---|---|---|
| **Development** | Feature not completed → business value drops to zero | Per feature (LLP from config) |
| **Market** | Market shock → business value × 0.85 | 20% of scenarios |
| **Component** | Shared platform fails → business value × cluster factor | Per dependency cluster |
| **Global** | Severe crisis (regulation, pandemic) → business value × 0.60 | 5% of scenarios |

These are sequential **multiplicative shocks** applied per scenario. The full formal model:

### Development Risk — Per Feature

Each scenario draws a random number for each feature. If the draw falls below the feature's LLP, the feature is not delivered and produces zero business value:

$$\text{BV after Development} = \begin{cases} \text{Simulated BV} & \text{if completed} \\ 0 & \text{if not completed} \end{cases}$$

$$P(\text{not completed}) = \text{LLP (per feature, from config)}$$

For the case study features: H1 LLP = 20%, H2 LLP = 50%, H3 LLP = 80%. H3's LLP is the highest by far — 80% of simulated scenarios produce zero BV for H3 at the development gate alone.

### Market Risk — Portfolio-Wide

One random draw per scenario. If a market shock occurs, all surviving feature values are multiplied by the market factor:

$$\text{BV after Market} = \text{BV after Development} \times \begin{cases} m_{\text{market}} & \text{if market shock} \\ 1.0 & \text{otherwise} \end{cases}$$

$$P(\text{market shock}) = p_{\text{market}}, \quad m_{\text{market}} = 0.85$$

The base-case parameters in this case study: 20% probability, 0.85 factor (i.e. 15% loss in the shock case).

### Component Risk — Per Cluster

Features sharing a `dependency_cluster` experience the **same** failure draw. If the cluster fails in a scenario, all features in that cluster are reduced by the cluster factor:

$$\text{BV after Component} = \text{BV after Market} \times \begin{cases} m_{\text{comp}} & \text{if platform outage} \\ 1.0 & \text{otherwise} \end{cases}$$

$$P(\text{outage}), \; m_{\text{comp}} \text{ — per cluster, from risk model config}$$

In the case study, H2 and H3 share the *Traceability Platform* cluster — if that platform fails, both lose value together. H1 sits on the *Customer Experience Platform* cluster, isolated from H2/H3.

### Global Risk — Portfolio-Wide

One random draw per scenario. If a global crisis occurs, all remaining values are reduced:

$$\text{BV after Global} = \text{BV after Component} \times \begin{cases} m_{\text{global}} & \text{if global crisis} \\ 1.0 & \text{otherwise} \end{cases}$$

$$P(\text{global crisis}) = p_{\text{global}} = 0.05, \quad m_{\text{global}} = 0.60$$

Global crisis is low probability (5%) but high impact (40% loss across the portfolio). Think regulatory shock, pandemic-scale disruption, or systemic supply-chain failure.

### Business Value Floor And CVaR After All Layers

After all four risk gates are applied, the same metrics from [Notebook 02](02-business-value-evidence.md) are recomputed on the **risk-adjusted** distribution:

$$\text{Business Value Floor} = \text{5th percentile of } N \text{ risk-adjusted scenarios}$$

$$\text{CVaR 95\%} = \text{average of scenarios} \leq \text{Business Value Floor}$$

> ⚠️ **The floor can be EUR 0 for features with high LLP.** When `LLP > 5%`, more than 5% of scenarios produce zero business value (feature not completed). The 5th percentile of that distribution is EUR 0 — by design, not a bug. For H2 (LLP 50%) and H3 (LLP 80%) the floor *is* EUR 0 unless development risk is mitigated. Use **expected business value** and **retention %** as primary metrics for these features.

## Feature Risk Profiles — Retention Rate

For each feature, the notebook reports the expected business value remaining after each gate:

| Gate | What it does |
|---|---|
| **Base** | Full simulated business value — no risk applied yet |
| **After Development** | Features with high LLP lose most value here |
| **After Market** | All surviving values × market factor (probability-weighted) |
| **After Component** | Cluster-correlated outage applied |
| **After Global** | Remaining value × global crisis factor (probability-weighted) |

The **retention rate** is the simple ratio:

$$\text{Retention} = \frac{\text{BV after Global}}{\text{Base BV}}$$

Reading rule:

- **High retention (>70%)** — feature is resilient; risk layers do not erode much value.
- **Medium retention (40–70%)** — meaningful risk; check which layer causes the biggest drop.
- **Low retention (<40%)** — most value lost to risk; the feature needs de-risking before investment.

> **When values are almost only positive:** if a feature's simulated BV distribution shows little to no downside (gains dominate), retention will naturally exceed 90%. **Do not over-interpret this as "risk-free"** — it usually reflects optimistic input assumptions (narrow spread, no negative tail). Cross-check **Assumption Quality** and the input ranges before treating high retention as a green light.

The decay chart shows business value shrinking left to right through each risk layer. **A steep drop at "After Development" means development failure dominates the risk** — that is the case for H2 and H3 in this study.

## Portfolio Risk Waterfall — Where Value Is Lost

The waterfall traces the **combined** portfolio value through all four risk layers. Each step reports the expected business value *after* that risk has been applied.

For the H2 + H3 bundle in this case study, the layer-by-layer numbers (matching the Overview value-decay table):

| Step | Portfolio expected BV |
|---|---:|
| Base, no risk applied | EUR 139k |
| After Development risk | EUR 54k |
| After Market risk | EUR 52k |
| After Component risk | EUR 51k |
| After Global risk | EUR 50k |

About **EUR 85k of the EUR 89k total decay happens at the Development step alone**. Market, Component, and Global together remove ~EUR 4k — roughly 5% of what Development removes.

The erosion chart visualises the same numbers as bars. The tallest drop is the risk that matters most — and it is Development, by an order of magnitude. The reason is structural: Development failure sets BV to zero (multiplied by 0), while Market and Global multiply by 0.85 / 0.60 — they reduce, they do not annihilate.

> **Key insight:** reducing development risk (LLP) typically has more impact than hedging against market or global crisis — because development failure sets business value to zero, while market/global only reduce it by a fraction.

The **profitability check** at the bottom of the section compares risk-adjusted business value against the total investment. Positive net = the portfolio pays for itself after all risks. Negative net = risk is eating more value than the investment generates.

## Ranking Strategies Compared

The portfolio selection from [Notebook 04](04-portfolio-and-budget-evidence.md) used `var_floor` as the ranking strategy. Notebook 05 also compares it with three alternatives:

| Strategy | Maximises | When to use |
|---|---|---|
| `var_floor` | VaR 95% floor minus development cost | Absolute downside protection — contractual / obligation logic |
| `risk_ratio` | Lowest relative drawdown | Conservative prioritisation — minimise volatility |
| `rorac` | Return on Risk-Adjusted Capital | Standard risk-adjusted return metric |
| `risk_adjusted_roi` | Best floor per euro invested | CFO capital-budgeting view |

Formally, the `var_floor` score per feature:

$$S_{\text{var}} = \mathrm{VaR}_{95} - C$$

The four strategies **are not equivalent** and can produce different top features:

- `var_floor` selects features with the strongest worst-case floor. Right for non-negotiable downside protection.
- `risk_ratio` (also called Coefficient of Variation) selects the feature with the smallest spread relative to its mean. Right when predictability matters more than absolute return.
- `rorac` divides expected return by economic capital (or by a risk-derived denominator like VaR). It is the banking-style return-per-risk metric.
- `risk_adjusted_roi` divides the risk-floor by the upfront cost — answers "how much downside protection per euro spent".

When the top ranks differ across strategies, the decision **depends strongly on the chosen risk perspective**. The recommendation in this case study is robust because H2 and H3 dominate the top under multiple strategies — but a single strategy is not enough evidence for a strong claim.

## Sensitivity — What If The World Changes?

The "what-if" check varies the two largest risk drivers and looks for break-even points.

Three named scenarios:

| Scenario | Market shock probability | Global crisis probability | Meaning |
|---|---:|---:|---|
| **Low Risk** (Optimistic) | 10% | 2.5% | Things go better than planned |
| **Base Case** (Expected) | 20% | 5.0% | Central assumption |
| **High Risk** (Stress) | 30% | 7.5% | Things go worse — stress test |

Reading rule: if the **High Risk** column still produces a portfolio value above the investment line, the portfolio pays off even under stress. If it dips below, **risk mitigation becomes urgent**.

### Development × Market Heatmap

The sensitivity heatmap tests the two largest risk dimensions against each other:

- **Development Risk (vertical axis):** all feature LLP rates scaled uniformly — halved, unchanged, or increased by 50%.
- **Market Risk (horizontal axis):** market shock probability at 10%, 20%, or 30%.

Each cell shows expected portfolio value after all four risk layers (Component and Global stay at their base rates).

| Row | Scenario | What causes it |
|---|---|---|
| **Better development** (top) | All LLP rates halved | Better testing, smaller scope, experienced team |
| **Base case** (middle) | Current LLP rates | Planning assumption |
| **Worse development** (bottom) | All LLP rates +50% | New technology, team turnover, scope creep |

Colour rule: green = profitable; red = loss. The colour flips at the break-even line (portfolio value = investment). The white dashed border marks the base case.

**The structural insight:** moving *up one row* (improving development) gains more EUR than moving *left one column* (lower market risk). Development risk is the highest-leverage lever because it is both the largest risk **and** the one within team control. Market risk is mostly external.

What to do with the heatmap:

| If you see... | It means... | Action |
|---|---|---|
| Top row all green | Development quality makes the portfolio robust | Prioritise testing, team stability, smaller scope |
| Middle row mixed | Base case is marginal — buffer is thin | Reduce development risk before committing full budget |
| Bottom row mostly red | If development worsens, the portfolio fails | Do not proceed without development de-risking |

## Decision Brief — Role-Specific Reading

### For The Product Owner

1. **Check feature retention** (Section 3 in the notebook). If any feature retains less than 50% of its base value, de-risk development before further investment.
2. **Find the biggest risk** (Section 4). The "Business Value Loss by Risk Dimension" table tells you which risk to tackle first — usually Development.
3. **Set risk tolerance** (Section 5). Use the sensitivity range to decide how much risk swing is acceptable for the budget.

### For The Risk Manager

1. **Quantify total risk exposure** (Section 4). Compare "Total expected risk loss" with the portfolio investment. If loss approaches investment, raise a flag.
2. **Stress-test assumptions** (Section 5). The high-risk column shows business value under stressed probabilities — use for board reporting.
3. **Identify concentration risk** (Section 3). Features with low retention and high cost create disproportionate risk.

### For The Board

| Question | Answer (from this notebook) |
|---|---|
| Does the portfolio pay off after risks? | Section 4 → Profitability Check card |
| What is the single biggest risk? | Section 4 → Business Value Loss table (top row) |
| How bad can it get? | Section 5 → Sensitivity high column |
| What should we mitigate first? | Section 4 → Largest loss dimension = first mitigation target |

## Industry Benchmarks

The metrics in this notebook have equivalents in financial-industry practice. Use them as **reference points, not rules** — every organisation has its own thresholds depending on sector, risk appetite, and regulatory context:

| Metric | Benchmark | Source / convention |
|---|---|---|
| **HHI (concentration)** | HHI > 0.25 = highly concentrated | EU/US competition authorities use this threshold for market dominance |
| **IRR vs. hurdle** | IRR > WACC + 3% = typically investable | Standard corporate-finance buffer for estimation uncertainty |
| **Risk Ratio** | < 0.3 low · 0.3–0.5 moderate · > 0.5 high | Coefficient of variation thresholds used in project risk management |
| **CVaR / floor spread** | CVaR < 5× floor = well-behaved tail | Common risk calibration norm (also used in Swiss/EU banking governance) |
| **Retention rate** | > 70% resilient · 40–70% moderate · < 40% fragile | Derived from stress-testing practice in operational risk |

A tech startup and a regulated utility will judge the same HHI very differently.

## What A Product Owner Should Walk Away With

- **Development risk dominates the case study** — about EUR 85k of EUR 89k decay happens at the Development layer.
- **H2 + H3 remains the right portfolio**, but it is not ready for uncontrolled execution.
- **Market, Component, and Global combined remove ~EUR 4k.** Hedging them is a small lever compared to development confidence.
- **The risk perspective changes the ranking.** Use multiple strategies for cross-checking; do not over-fit to one metric.
- **Retention < 50% is a red flag.** Combine it with the EUR delta per layer to find the highest-impact mitigation.

In Scrum language: this notebook turns a positive value story into a realistic execution story. The Product Owner can defend "we need development gates before scaling" with three numbers (Base BV, BV after Development, retention rate) instead of opinion.

## Glossary

| Term | Definition |
|---|---|
| **LLP** | Likelihood of non-completion — `likelihood_of_non_delivery` in config. Probability the feature never reaches production. |
| **Risk Waterfall** | Sequential layers Development → Market → Component → Global. Each layer multiplies surviving BV by a (probabilistic) factor. |
| **Retention Rate** | `BV after all layers / Base BV`. Fraction of base value surviving. |
| **Business Value Floor 95** | 5th percentile of the simulation. 95% of scenarios exceed this floor. Can equal EUR 0 when LLP > 5%. |
| **CVaR 95%** | Average of the worst 5% of scenarios. More conservative than the floor alone. |
| **Market Risk** | Portfolio-wide shock — one draw per scenario, all features × factor. |
| **Global Risk** | Severe portfolio-wide crisis. Low probability, high impact. |
| **Component Risk** | Cluster-level risk — features sharing a `dependency_cluster` fail together. |
| **Sensitivity** | Testing how results change when a risk parameter is increased or decreased. |
| **Heatmap** | Two-dimensional sensitivity grid (here: Development × Market). Cells colour-coded around the break-even line. |
| **HHI** | Herfindahl-Hirschman Index — concentration measure. HHI > 0.25 = highly concentrated. |
| **RORAC** | Return on Risk-Adjusted Capital. Standard banking metric. |

## Next

Risk Resilience showed *that* development dominates the downside. The next question is *how much* deployment cost overruns can add to the bill, and which cancellation rule applies if a feature runs late: [Notebook 06 — Deployment Cost Risk Evidence](06-development-cost-risk-evidence.md).
