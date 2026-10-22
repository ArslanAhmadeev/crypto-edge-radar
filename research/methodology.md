# TGE Polymarket pilot backtest methodology

## Research question

Can information available before a public token sale closes identify sales whose post-TGE fully diluted valuation (FDV) and investor return are attractive?

The intended signal is the ratio between a point-in-time Polymarket-implied post-TGE valuation and the public-sale FDV. A larger positive ratio would support entering the sale if it is known before the participation deadline.

This pilot is descriptive. Ten projects cannot establish a production trading rule, and the current dataset does not contain exact historical Polymarket probabilities for any project.

## Decision timestamp and sample groups

The decision timestamp is the public-sale close time.

- `actionable`: the Polymarket market opened before the sale closed. Only this group can provide evidence about a sale-participation strategy.
- `predictive_only`: the Polymarket market opened after the sale closed but before TGE. These projects can be used to study prediction quality, but never as evidence that an investor could have acted on the signal.

The groups are always reported separately. A combined table may be shown for completeness, but combined statistics are not treated as strategy results.

## Features

### Entry valuation

- `sale_price_usd`: public-sale token price.
- `sale_fdv_usd`: valuation paid by the public-sale investor.

### Polymarket signal

The preferred inputs are an exact snapshot timestamp and threshold probabilities observed no later than the relevant decision timestamp. The conceptual feature is:

`Polymarket expected post-TGE FDV / sale FDV`

The current pilot lacks exact historical snapshots and probabilities. Search-indexed probability strings with unknown timestamps are retained as proxy evidence only. A transparent threshold summary may be calculated from them, but it is never promoted to an exact signal or used to claim an actionable backtest.

`pm_total_volume_usd` is reported as a market-quality indicator. It is not converted into a fitted weight.

Final Polymarket resolution brackets are outcomes. They are never used as pre-TGE features.

### Token mechanics

- `tge_unlock_pct`
- `vesting`

These fields are controls for interpreting results. No fitted adjustment is applied in the pilot.

### Social and benchmark features

Current TwitterScore and follower counts are excluded because they are not point-in-time pre-TGE observations. Historical social features remain unavailable.

BTC and ETH returns are included only if reliable horizon-matched historical values exist. The current CSV leaves all benchmark fields empty, so benchmark and excess-return analysis remains an enrichment task rather than a blocker.

## Outcomes

The primary outcome is the return from the public-sale price to the exact TGE+1 day price:

`ROI = outcome price / sale price - 1`

The stored CSV expresses ROI as percentage points, so the implementation multiplies the ratio by 100 when producing `*_pct` columns.

Secondary outcomes are exact TGE+7, TGE+30 and TGE+90 day returns where prices exist. FDV at each horizon is:

`FDV = outcome price * total supply`

Exact day-1 outcomes and proxy day-1 outcomes remain in separate columns. A combined exact-then-proxy value may be displayed only in an explicitly labeled sensitivity analysis and carries an `outcome_quality` field.

## Look-ahead prevention

1. Apply the sale-close timestamp as the actionable decision cutoff.
2. Exclude `predictive_only` rows from strategy evidence.
3. Require an observed historical snapshot timestamp before treating probabilities as exact.
4. Never use resolved FDV brackets as features.
5. Never use current social values as historical predictors.
6. Keep timestamp-unknown Polymarket probabilities and non-close price observations in proxy-only sensitivity sections.
7. Report individual projects and missing observations so that unavailable values cannot silently become zeros.

## Evaluation

The hypothesis would merit a larger backtest if stronger point-in-time valuation gaps are directionally associated with higher exact TGE+1 returns among actionable projects, and the relationship remains visible after excluding proxies, obvious outliers and weak-liquidity markets. Unlock and vesting should offer plausible explanations for exceptions rather than being optimized into a score.

The pilot conclusion uses:

- `GO`: usable point-in-time coverage and a robust directional pattern justify expanding the test.
- `MAYBE`: the idea is economically interesting, but missing signal data or the small sample prevents a credible strategy conclusion.
- `NO-GO`: usable evidence shows no meaningful directional relationship or an economically unattractive result.

No conclusion is based on an optimized threshold or fitted weight.

## Current limitations

- Only ten projects are available.
- Exact historical Polymarket snapshot times and probabilities are missing for every row.
- Several outcome prices are missing or available only as intraday/day-high proxies.
- Later-horizon outcomes are sparse.
- Historical social metrics and BTC/ETH benchmark returns are absent.
- Sale and TGE timestamp quality varies across projects.
- The sample may contain selection bias because it is not a complete universe of public sales with Polymarket markets.

## Pilot result

The current conclusion is `MAYBE`.

Among the seven actionable projects, four have exact day-1 closing prices. Three of those four returns are positive, with a median of `+66.25%`. The mean of `+607.70%` is dominated by Plasma at `+2,329.2%`; excluding Plasma leaves only three exact observations, with a mean of `+33.86%`.

Adding two explicitly labeled proxy outcomes produces six observed actionable projects, four positive, with a median return of `+48.08%`. This shows that the opportunity set has interesting outcomes, but it does not validate the Polymarket valuation-gap signal. There are zero actionable rows with exact point-in-time probabilities, and only one row combines an actionable proxy signal with any day-1 outcome, which is itself a proxy.

The pilot therefore supports further data collection, not an ENTER/WATCH/SKIP investment rule.

## Next data-collection priorities

1. Capture exact Polymarket CLOB threshold probabilities immediately before each public-sale close.
2. Store snapshot timestamps, market identifiers and the applicable decision cutoff.
3. Expand to a systematic universe that includes failed and unattractive sales.
4. Collect exact horizon-aligned day-1 closing prices separately from intraday highs.
5. Complete unlock and vesting data at TGE.
6. Add BTC and ETH horizon returns for excess-return analysis.
7. Add historical social metrics only after the core valuation signal and outcomes are reliable.
