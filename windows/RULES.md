# Training window for LEAR-X

Written 11 Nov 2026, before this run. An earlier look at the test days suggested that a longer history helps
LEAR-X. That look used the test days, so it decides nothing. This is the test that decides.

Variants, all trained on the complete days in the last 730 (the weather inputs start in March 2024, so before
2026 that is every day there is). They differ in how much history the price scaling (median and spread) uses:

| Name | Scaling over |
|---|---|
| scale_1y | last 365 days |
| now | last 730 days (the live model) |
| scale_3y | last 1095 days |
| scale_4y | last 1460 days |
| scale_all | everything since 2019 |

Days: every 7th day from 1 Oct 2024 to 30 Sep 2025, the network bake-off's tuning days, keeping only days with at least
10% more complete training days than inputs (the lasso's BIC needs that). The test days are not used.

More training days can't be tested here, because there are none before March 2024 with the weather inputs. That needs
older weather forecasts.

Decision: the variant with the lowest error wins if it beats `now` with Diebold-Mariano p < 0.05. Days are a week
apart, so one lag. A winner runs live as a challenger next to the forecast, not shown, judged on 1 Mar 2027 with the
others. The test-day numbers are reported afterwards, and don't change the choice.
