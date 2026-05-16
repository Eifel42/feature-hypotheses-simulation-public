# Notebook 03 — Financial Return

Source notebook: [03-blockchain-case-study-capital-budgeting.ipynb](../../../apps/fhs/notebooks/03-blockchain-case-study-capital-budgeting.ipynb)
Overview: [Product Owner Case Study - Notebook 03](../PRODUCT-OWNER-CASE-STUDY.md#notebook-03---financial-return)

This guide transfers Notebook 03 — the finance view on top of the business-value evidence. It walks the central question (upfront vs. installment financing), defines NPV, IRR, and PI in product-owner language, explains the hurdle rate, and proves why Option B (installments) produces a higher IRR than Option A (upfront).

## The Central Question

Should the team pay the full development investment upfront, or spread it over annual installments? Both options carry the same total spend; the difference is **when** the money leaves the bank account.

| | Option A — Upfront | Option B — Installment |
|---|---|---|
| Development cost | Paid in full at Year 0 | Equal annual payments over `installment_years` |
| Operating cost (OpEx) | Every year | Every year (identical) |
| Time-value effect | None — full PV of investment | Favourable — later payments discounted |
| Year-1 cash outflow | Maximum | Minimum |

The notebook makes the cash flows explicit — year by year, hypothesis by hypothesis — so the NPV advantage of installment financing is **visible**, not just asserted.

## The Hurdle Rate (Discount Rate)

The discount rate is the company's **minimum return expectation**. Any investment must earn at least this rate to be worth doing. It reflects the cost of capital — the return that the same money could earn somewhere else.

Typical industry ranges:

| Industry | Typical hurdle rate |
|---|---|
| Regulated utility (energy, water) | 5–8% |
| Industrial company | 8–12% |
| Retail / commercial bank | 10–15% |
| Technology startup | 15–25% |

The case study scenario uses `discount_rate: 0.12` — 12%, the upper end of the industrial-company range. If a team does not know its own rate, the finance partner does. The exact number matters: a higher rate makes future cash flows less valuable, so a stricter rate makes it harder for features to clear the gate.

> **Simple rule:** the discount rate answers *"what annual return could we get by investing this money somewhere else instead?"* A feature must beat that alternative.

## Year 1 — What Each Feature Earns And Costs

The notebook's starting table puts expected business value next to Year-1 cost exposure under each financing structure:

- **Option A Net Year 1** = `Expected BV − Full Development Cost − Annual OpEx`. A negative number is normal for multi-year programmes — you front-load the investment.
- **Option B Net Year 1** = `Expected BV − (Development Cost / installment_years) − Annual OpEx`. A positive number means the feature is P&L-neutral from Year 1 onward.

For this scenario (`installment_years`: 3 for H1/H2, 2 for H3):

| Feature | Dev cost | Installment / yr | Annual OpEx |
|---|---:|---:|---:|
| H1 | EUR 75,000 | EUR 25,000 | EUR 25,000 |
| H2 | EUR 55,000 | EUR 18,333 | EUR 40,000 |
| H3 | EUR 10,509 | EUR 5,254 | EUR 3,000 |

H3 has the lightest Year-1 commitment under both options because both the development cost and the annual operating cost are small. H2 has the heaviest opex (EUR 40,000/yr) — that puts pressure on the Year-1 net even under installments.

## NPV — Net Present Value

NPV sums every future net cash flow, discounted to today, then subtracts the upfront investment. The standard formula for a project running over `T` years at discount rate `r`:

$$\text{NPV} = \sum_{t=1}^{T} \frac{CF_t}{(1 + r)^t} - C_0$$

where `CF_t` is the net cash flow in year `t` and `C_0` is the Year-0 investment.

Read this in two parts:

- Each future year's net cash flow is **discounted** — a euro received in Year 3 is worth less than a euro received in Year 1.
- The sum of discounted future cash flows must **exceed** the Year-0 investment for NPV to be positive.

**Positive NPV → value-creating.** **Negative NPV → value-destroying** at the chosen hurdle rate.

For the case study, the per-feature 3-year NPV with `annual_growth_rate` applied year over year (and the chosen financing option) is what makes the recommendation in [Notebook 04](04-portfolio-and-budget-evidence.md) defensible. The simulated business value is the input to `CF_t`; the discount rate is fixed at 12%; the growth rate per feature comes from config (H1 −20%, H2 −10%, H3 +15%).

## IRR — Internal Rate Of Return

IRR is the discount rate at which NPV equals zero — the **annualised yield** the project earns on its invested capital. The decision rule:

- IRR **above** the hurdle rate → feature creates value.
- IRR **below** the hurdle rate → feature destroys value at the chosen hurdle.

Both Option A and Option B start with a negative Year-0 cashflow, so both always produce a finite IRR. The gap comes from the **size of the Year-0 outflow**.

| | Year 0 | Years 1 – (n−1) | Year n onward |
|---|---|---|---|
| **Option A — Upfront** | −Full Investment | +BV − OpEx | +BV − OpEx |
| **Option B — Installment** | −1st Installment | +BV − Installment − OpEx | +BV − OpEx |

Option B's Year-0 outflow is a fraction of Option A's. A smaller capital commitment must be recovered for NPV to reach zero, so the **break-even discount rate (the IRR) is higher**.

> Less capital at risk early means a higher yield on that capital.

The notebook's NPV-vs-rate curve makes the difference visible: both curves cross zero (their IRR), but Option B crosses at a higher rate.

For the case study: H2 improves clearly under installment financing because its larger development cost benefits more from staging. H1 stays below the hurdle even under Option B — the value case is weak independent of the financing structure. H3 stays attractive regardless of financing because the initial capital need is already small.

## PI — Profitability Index

PI normalises NPV by the upfront capital:

$$\text{PI} = \frac{\text{NPV}}{\text{Investment}}$$

In this project's convention, `PI > 0` means value creation; some finance textbooks use `PI > 1` with a different formula (NPV / Investment + 1). Same intuition, different threshold.

PI is the right metric when **budget is scarce**. Two features can both have positive NPV; PI tells you which one creates more value **per euro invested**. The portfolio optimiser in [Notebook 04](04-portfolio-and-budget-evidence.md) uses this implicitly when choosing the bundle that maximises total NPV within the budget constraint.

## Visual Comparison

The notebook shows two charts:

- **Cash-flow timeline (left):** net cash flow year by year per option. The red bar at Year 0 for Option A is the full investment outflow. Option B has no Year-0 bar — instead, every year shows the same installment slice as a small negative.
- **NPV side-by-side (right):** NPV under each option, with the VaR 95% floor as a red marker, and the PI written above each bar.

The visual purpose: a non-finance reader can see, without reading a table, that Option B's bars are uniformly less extreme — the investment is smoothed across years.

## What A Product Owner Should Walk Away With

- **H1 stays below the funding threshold under both financing options.** The financial case is not rescued by smarter financing — the value case is the problem.
- **H2 improves clearly with installment financing.** The 3-year horizon plus staged investment moves it cleanly above the hurdle.
- **H3 stays attractive under both options** because the initial capital need is small. Financing structure barely changes its case.

The practical lesson:

> The same feature can look more or less attractive depending on how the investment is funded over time. Choose the financing option that matches the company's cash position **and** the feature's value profile.

This notebook is also the briefing material when a roadmap discussion turns into a funding discussion with finance partners or steering. It gives the Product Owner a clear, defensible answer beyond "we think it is worth it".

## Glossary

| Term | Definition |
|---|---|
| **NPV** | Net Present Value — sum of discounted future cash flows minus the upfront investment. Positive = value-creating. |
| **IRR** | Internal Rate of Return — the discount rate at which NPV = 0. Higher IRR = faster capital recovery. |
| **PI** | Profitability Index — NPV per euro of invested capital. Higher PI = better use of scarce capital. |
| **Hurdle Rate** | Minimum required return (= discount rate). Projects must clear this to create shareholder value. |
| **Option A (Upfront)** | Full development cost paid at Year 0. Maximum Year-1 cash outflow, no time-value advantage. |
| **Option B (Installment)** | Development cost spread over `installment_years`. Smaller Year-0 outflow, time-value benefit. |
| **OpEx** | Annual operating cost — recurring expense deducted from business value every year. |
| **Business Value Floor 95** | 5th percentile of the Monte Carlo simulation. 95% of scenarios produce a value above the floor. |
| **P95** | 95th percentile — the ceiling. Only 5% of scenarios exceed this value. |
| **Monte Carlo** | Simulation technique — runs the configured number of random scenarios per feature to build a probability distribution of outcomes. |

## Next

NPV and IRR tell you whether a single feature pays back. The next question is **which bundle** to fund within the budget — and whether to keep reserve instead of spending everything: [Notebook 04 — Portfolio And Budget Evidence](04-portfolio-and-budget-evidence.md).
