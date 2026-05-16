# Notebook 07 — Executive Decision

Source notebook: [07-blockchain-case-study-decision.ipynb](../../../apps/fhs/notebooks/07-blockchain-case-study-decision.ipynb)
Overview: [Product Owner Case Study - Notebook 07](../PRODUCT-OWNER-CASE-STUDY.md#notebook-07---executive-decision)

This guide transfers Notebook 07 — the synthesis. It explains how the five evidence layers from Notebooks 02–06 collapse into one traffic-light verdict, why the CONDITIONAL GO recommendation is defensible, what the robustness check tells you, and what to do depending on the verdict.

## The Question

One notebook. All dimensions. One recommendation. Five separate evidence layers (Business Value, Financial Return, Portfolio Optimisation, Risk Profile, Deployment Cost Risk) get reduced to a single GO / CONDITIONAL GO / REVIEW signal and a concrete action playbook.

The value of Notebook 07 is **not** another calculation. Its value is **traceability**: every recommendation can be walked back to one earlier evidence layer.

## Five Dimensions, One Decision

The synthesis combines five questions, each answered by one source notebook:

| # | Dimension | Source | Question answered |
|:-:|---|---|---|
| 1 | Business Value | [Notebook 02](02-business-value-evidence.md) | How much can each feature deliver? |
| 2 | Financial Return | [Notebook 03](03-financial-return-evidence.md) | Is the investment worthwhile? (NPV, IRR) |
| 3 | Portfolio Optimisation | [Notebook 04](04-portfolio-and-budget-evidence.md) | Which features should we build at this budget? |
| 4 | Risk Profile | [Notebook 05](05-risk-resilience-evidence.md) | What can go wrong and how much value is at risk? |
| 5 | Deployment Cost Risk | [Notebook 06](06-development-cost-risk-evidence.md) | Will deployment stay within budget if sprints run late? |

For each dimension, Notebook 07 emits one **traffic-light signal**:

- **GO** — the dimension supports execution.
- **CONDITIONAL GO** — execution is possible, but only with a specific control or gate.
- **REVIEW** — the case is too weak to proceed without mitigation.

## The Combination Rule

Five signals roll up into one overall verdict using a deliberately simple rule:

| Overall verdict | Rule |
|---|---|
| **GO** | All five dimensions are GO. |
| **REVIEW** | Two or more dimensions are REVIEW. |
| **CONDITIONAL GO** | Every other combination. |

This rule is **easy to audit**:

- One weak dimension creates a condition (CONDITIONAL GO).
- Two weak dimensions stop the decision and force review.

The mechanical simplicity is the point. A more elaborate scoring formula would be impossible to defend in a steering meeting; the five-dimension rule is something a board member can verify on the back of a napkin.

## What This Case Study Shows

For the H2 + H3 portfolio in the blockchain case study, the five dimensions resolve as follows (the Overview captures the result):

| Dimension | Main message | Signal |
|---|---|---|
| Business Value | H2 is the value anchor; H3 is useful; H1 is too weak for its cost. | GO for H2 + H3 / REVIEW for H1 |
| Financial Return | Installment funding improves the case, but H1 still misses the threshold. | GO for H2 + H3 / REVIEW for H1 |
| Portfolio And Budget | H2 + H3 is the best use of budget; keeping reserve is better than spending everything. | GO |
| Risk Resilience | Development risk dominates the downside story. | CONDITIONAL GO |
| Deployment Cost Risk | H2 needs release-window control; H3 needs an early scope gate because the current ceiling prevents late cancellation. | CONDITIONAL GO |

Overall verdict: **CONDITIONAL GO** — proceed with H2 + H3 with active development-risk control.

The concrete recommendation:

- **Fund H2 Traceability** as the value anchor.
- **Test H3 Expiration Alerts** behind a tight development gate.
- **Defer H1 Simplified UI** until the business value case improves.
- **Keep EUR 89,491 as reserve** instead of spending the full budget.

## What A Product Owner Can Say In The Meeting

The message is short enough to fit in one breath:

> We should not fund the full roadmap now. The evidence supports H2 and a controlled H3 test. H1 should wait. The main risk is not market demand; it is development confidence. We should keep reserve and pass the next gate only when development risk improves.

That statement is the essence of the notebook. It connects backlog priority, budget discipline, and development-risk management in one decision.

## Visual Evidence Set

Notebook 07 collects four charts and reads them as one summary set. The four roles together:

| Chart | Source | What it shows |
|---|---|---|
| Budget-level portfolio selection | NB 04 | H2 + H3 is the strongest funded bundle; H1 waits; reserve stays available. |
| Risk resilience matrix | NB 05 | Where the portfolio keeps a profit buffer; where harder development/market conditions push it toward review. |
| Sprint overrun distribution | NB 06 | Why H2 must stay inside a controlled release window and H3 needs an early scope gate before the sprint ceiling is reached. |
| Portfolio expected business value decay across risk layers | NB 07 synthesis | Portfolio expected BV after each risk layer is applied. |

### The Value-Decay Numbers

The portfolio expected business value through the four risk layers:

| Step | Portfolio expected BV |
|---|---:|
| Base, no risk applied | EUR 139k |
| After development risk | EUR 54k |
| After market risk | EUR 52k |
| After component risk | EUR 51k |
| After global risk | EUR 50k |

Reading the table: **about EUR 85k of the EUR 89k total decay happens at the development step alone.** Market, component, and global combined remove ~EUR 4k.

This is the structural argument for the **CONDITIONAL GO**: the portfolio is attractive (Base EUR 139k vs. budget commitments), but the development risk is the dominant value-loss mechanism. Until development confidence improves, the headline figure cannot be defended in a steering meeting.

> For a Product Owner, the leverage point is clear: smaller scope, tighter estimates, and explicit development gates recover more decision quality than broad risk mitigation alone.

## Robustness Check — Does The Verdict Survive Easier And Harder Conditions?

The notebook then asks: does the recommendation hold under different conditions?

| Scenario | Development factor | Market shock probability | What it tests |
|---|---:|---:|---|
| Optimistic | 0.5× | 10% | How much value better development confidence would unlock. |
| Base case | 1.0× | 20% | The current planning assumption and headline verdict. |
| Stressed | 1.5× | 30% | Whether the portfolio still works when development gets harder. |

Two interpretation rules:

- **If the verdict improves mainly when development risk is halved**, the highest-leverage action is **development-risk reduction** — exactly the conclusion the Overview hands to steering.
- **A recommendation that only works in the optimistic row is fragile.** A recommendation that remains acceptable in the stressed row is durable.

In this case study, the recommendation moves from CONDITIONAL GO (base) toward GO under the optimistic row and toward REVIEW under the stressed row — confirming that the verdict is **decision-leverage-sensitive**, not robust enough to ignore development quality.

## The Action Playbook

Each verdict maps to a concrete action:

| Verdict | Product Owner action |
|---|---|
| **GO** | Confirm the funding structure, set development milestones, and rerun the analysis quarterly. |
| **CONDITIONAL GO** | Fund only the data-backed bundle, work the conditional dimensions first, and keep reserve until the next gate. |
| **REVIEW** | Do not proceed before mitigation; fix the highest-impact red dimension and rerun the scenario configuration. |

For this case study, the action is **CONDITIONAL GO**: fund H2, test H3 behind an early scope gate, defer H1, keep EUR 89,491 as reserve, and make development confidence the next management focus.

### What To Do Next — Role-Specific

**If the recommendation is GO:**

1. Confirm financing option — use installment (Option B from [NB 03](03-financial-return-evidence.md)) to reduce Year-1 cash outflow.
2. Set development milestones using the NB 06 sprint plan as baseline for review gates.
3. Monitor risk — rerun the synthesis notebook quarterly with updated development probabilities.

**If the recommendation is CONDITIONAL GO** (this case study):

1. Check which dimensions need attention — see the dimension table in the Overview.
2. Reduce development risk first — it is usually the biggest lever (see the sensitivity heatmap in NB 05).
3. Consider phasing — start with features that pass all checks, add others later.

**If the recommendation is REVIEW:**

1. Do not proceed without mitigation — two or more dimensions show risk.
2. Prioritise the red dimensions — fix the highest-impact issue first.
3. Rerun after changes — adjust `blockchain.yaml` and rerun the notebook to see if the recommendation improves.

## The Phase-Rollout Idea

The notebook closes with a board-summary view: how the recommendation translates into phased rollout.

For this case study:

- **Phase 1 (now):** Fund H2 Traceability inside one controlled release window. Test H3 Expiration Alerts behind an early scope gate. Keep EUR 89,491 as reserve.
- **Phase 2 (next gate, e.g. next quarter):** Re-evaluate H3 — if development confidence holds, scale; if it does not, cancel cleanly using the gate rule. Re-evaluate H1 — if growth assumptions improve, fund from reserve.
- **Phase 3 (after development confidence improves):** Convert any remaining CONDITIONAL GO components to GO. Set the next round of investment based on observed velocity, not estimated.

Phasing turns CONDITIONAL GO into a **decision rhythm**, not a single yes/no. The reserve is what makes the rhythm possible — without it, the next decision is constrained before the new evidence arrives.

## What A Product Owner Should Walk Away With

- **Five layers in, one signal out.** The combination rule is simple enough to defend in a meeting.
- **CONDITIONAL GO is not weak.** It is a defensible "proceed with controls" — far better than "yes" without evidence or "no" without analysis.
- **Development is the leverage point.** ~EUR 85k of EUR 89k decay happens at development — the management action with the highest return is development quality, not market hedging.
- **Reserve is part of the decision**, not "leftover budget". Spending it on the wrong feature would worsen the verdict.
- **The verdict must survive the stressed row** to be durable. If it only works under optimistic development, treat it as fragile and act first.

## Three Passes For The Steering Meeting

A defensible three-pass reading order:

1. **Recommendation block** (Overview): one paragraph + four bullets. Use this to start the meeting.
2. **Decision Dimensions table** (Overview): show that the verdict is traceable — one row per dimension, one main message each.
3. **Robustness Check + Action Playbook** (Overview): explain what must change before the next gate.

The earlier notebooks build the evidence. This notebook turns that evidence into an executive roadmap decision.

## Glossary

| Term | Definition |
|---|---|
| **GO / CONDITIONAL GO / REVIEW** | Traffic-light signals per dimension and overall. |
| **Combination rule** | All five GO = GO; ≥ 2 REVIEW = REVIEW; everything else = CONDITIONAL GO. |
| **Five dimensions** | Business Value, Financial Return, Portfolio Optimisation, Risk Profile, Deployment Cost Risk. |
| **Robustness check** | Three named scenarios (Optimistic / Base / Stressed) that vary development and market parameters. |
| **Action Playbook** | Verdict-to-action mapping that turns the signal into a concrete next step. |
| **Reserve** | Unspent budget held for the next decision gate or mitigation. EUR 89,491 in this case study. |
| **Phase rollout** | Treating CONDITIONAL GO as a decision rhythm — fund Phase 1, re-evaluate at the next gate, scale or cancel based on new evidence. |
| **Traceability** | Each recommendation can be walked back to one source notebook and one piece of evidence. The point of Notebook 07. |

## End Of The Reading Path

This is the last notebook in the case-study sequence. The role-specific reading and the executive verdict are now complete; the next steps depend on the verdict and the action playbook. For deeper portfolio analysis (10-feature portfolios, three solvers, concentration risk), see the advanced notebooks:

- [A01 — Portfolio Advisor](../../../apps/fhs/notebooks/advanced/01-portfolio-advisor.ipynb)
- [A02 — Portfolio Risk Dashboard](../../../apps/fhs/notebooks/advanced/02-portfolio-risk-dashboard.ipynb)
