# A fix for forecasts that run too low when prices change level

Written 12 Nov 2026, before any of this was run.

## The problem

Since the live forecasts started (13 Oct 2026) they have been about 20 €/MWh too low, all three models. Prices
are about twice their two-year average, and gas is too. The models have learned that prices far above that average
fall back, which held when high prices were spikes. Each morning they forecast a drop that doesn't come.

## The idea

Let the model see each day's prices relative to a level that follows the market, so that "200 €/MWh for the third
week running" looks normal and only today's deviation from it is expected to fall back.

## Variants, on LEAR-X (lasso per hour, 730 days, the live inputs)

| Name | Each day's prices (the target, its own earlier prices, the neighbours' prices) are |
|---|---|
| now | used as they are (the live model) |
| level7 | minus the average DK1 price of the 7 days before |
| level28 | minus the average DK1 price of the 28 days before |
| gas | divided by the gas price known that morning |

Everything else is the same: the scaling, the lasso, the other inputs. The forecast is turned back by adding the
average or multiplying by the gas price. Nothing is tuned.

## Days

- Part A, the period with the problem: 1 Oct 2025 to 9 Nov 2026, every day (the backtest's test days and the live
  days so far). The idea came from looking at these days, so they can show that it would have worked, not prove it.
- Part B, an untouched period: 1 Jul 2021 to 31 Dec 2022, the last time prices changed level. Never used in this
  project. No weather forecasts or gas prices exist that far back here, so all variants run on prices, neighbour
  prices, holidays and weekdays only, and `gas` can't be run.

## Decision

- Score: mean absolute error per day. Test against `now`: Diebold-Mariano with Newey-West (7 lags), Holm over the
  candidates in each part.
- A candidate passes Part A if it beats `now` with p < 0.05 and, on days where yesterday's average price was at most
  1.5 times the two-year average (normal days), its error is not more than 3% above `now`'s.
- The winner is the passing candidate with the lowest error in Part A. If it is a level variant it must also beat
  `now` in Part B with p < 0.05.
- Reported with it: the bias (actual minus forecast) on normal days and on the others, both parts.
- A winner runs live as a challenger from the next morning, saved before the auction and not shown, and is judged
  with the other challengers (early check 15 Dec 2026, otherwise 1 Mar 2027). Only that live record is proof.
- If nothing passes, that is the result.

# Part C: all three live models, and which of them to switch (added 12 Nov 2026, before it was run)

Part A picked prices relative to gas, on LEAR-X only. The live forecast is the average of three models, so:

- Models: LEAR-X, BMT-X and XGBoost-X, the live R code unchanged (jacobazu/dk1-price-forecasting at a fixed commit,
  packages from its lock file), each as it is and on prices relative to gas. Part A's 405 days.
- Per model, reported: error and bias, relative to gas against as it is, Diebold-Mariano with Newey-West (7 lags),
  Holm over the three.
- The decision is about the ensemble. `now` is the average of the three as they are. The candidates are the seven ways
  to switch one, two or all three of them to gas.
- A candidate passes if it beats `now` with Holm p < 0.05 over the seven, and its error on normal days is not more
  than 3% above `now`'s. The winner is the passing candidate with the lowest error.
- The winner becomes the live challenger `ensemble_gasrel`, in place of the LEAR-X-only version set earlier today,
  before that has had a live day. If none passes, there is no ensemble challenger; the three gas versions are still
  saved each day.
- Not tested: the networks, Chronos-2, Timestral and TabPFN. On the backtest's high-price days Chronos-2 and Timestral
  have no bias (+0.1 and +2.9) and the networks about +4 to +5, against +7 to +11 for these three.
- The same caveat as Part A: the idea came from these days. The live record decides.
