# Result (12 Nov 2026)

Short version: the live challenger is the ensemble with LEAR-X and XGBoost-X on prices relative to gas and BMT-X as it
is (Part C, at the end). Parts A and B came first and are kept as they were written.

Scored by `evaluate.py`, which was committed before the forecasts were in. Numbers are €/MWh; bias is actual minus
forecast.

## Part A: 1 Oct 2025 to 9 Nov 2026, 405 days

| | Error | Bias | Bias on normal days (285) | Bias on high days (120) | Against `now`, Holm p |
|---|---|---|---|---|---|
| now | 19.46 | +8.8 | +6.0 | +15.5 | |
| **gas** | **17.94** | +2.6 | +3.2 | +1.2 | 0.03 |
| level7 | 18.10 | +1.6 | +0.8 | +3.3 | 0.01 |
| level28 | 18.22 | +3.1 | +1.1 | +8.0 | 0.00 |

All three pass Part A. On the 28 live days alone (13 Oct to 9 Nov): now 34.7 with bias +25.7, gas 25.2 with bias −6.5.

## Part B: 1 Jul 2021 to 31 Dec 2022, 549 days, never used before

| | Error | Bias | Against `now` |
|---|---|---|---|
| now | 40.59 | +10.4 | |
| level7 | 41.30 | +1.7 | worse, p = 0.32 |
| level28 | 42.39 | +3.9 | worse, p = 0.05 |

The level variants take the bias away here too, but their error is not lower. They fail Part B, so by the rule they
are out.

## Winner: gas

Prices relative to the gas price is the passing candidate with the lowest error in Part A. It runs live from the
forecast for 14 Nov 2026 as the challenger `ensemble_gasrel` in jacobazu/dk1-price-forecasting: the ensemble with
LEAR-X replaced by this version.

## What this does and doesn't show

- It would have worked: 8% lower error over the 405 days, 27% lower on the live days, and the bias mostly gone.
- It is not proof. The idea came from these days, and without the 28 live days `gas` is ahead but not significantly
  (17.4 against 18.3, p = 0.09). There are no gas prices here before June 2023, so it has no untouched period like
  Part B. The live record from 14 Nov is the proof.
- It overshoots on the live days (bias −6.5): with gas at twice its usual level the ratio is being stretched.
- Only LEAR-X was tested. BMT-X and XGBoost-X run the same way live and are saved, with no rule until they are tested.

## One thing that went differently from the rules

The archived inputs had no neighbour prices or DK1 weather after 12 Oct 2026, so the GitHub run skipped Part A's last
28 days. They were run afterwards with the price repo's live inputs (`live_days.py`), which match the archive exactly
on the 104 days both cover. The scores above include them, as the rules say.

# Part C: all three live models (12 Nov 2026, evening)

Scored by `evaluate_models.py`, committed before the run. The live R code, 405 days.

## Each model, relative to gas against as it is

| | Error as it is | Relative to gas | Bias as it is | Relative to gas | Holm p |
|---|---|---|---|---|---|
| LEAR-X | 19.64 | 17.95 | +9.0 | +2.6 | 0.03 |
| BMT-X | 19.22 | 19.00 | +7.0 | +2.3 | 0.69 |
| XGBoost-X | 19.16 | 17.47 | +4.8 | +1.9 | 0.00 |

The bias falls for all three. The error falls for LEAR-X and XGBoost-X, not for BMT-X.

## The ensemble: which models to switch

`now`, the average of the three as they are: error 17.93, bias +7.0.

| Switched to gas | Error | Bias | Bias on high days | Holm p |
|---|---|---|---|---|
| LEAR-X | 16.79 | +4.8 | +6.9 | 0.00 |
| BMT-X | 16.95 | +5.4 | +7.8 | 0.00 |
| XGBoost-X | 17.00 | +6.0 | +9.1 | 0.00 |
| LEAR-X, BMT-X | 16.83 | +3.2 | +2.9 | 0.02 |
| **LEAR-X, XGBoost-X** | **16.28** | +3.8 | +4.2 | 0.00 |
| BMT-X, XGBoost-X | 16.35 | +4.4 | +5.1 | 0.00 |
| all three | 16.77 | +2.3 | +0.2 | 0.03 |

All seven pass. The winner by the rule is LEAR-X and XGBoost-X switched, BMT-X as it is: 9% lower error.

Split by period, error (bias): the 377 backtest days, now 17.0 (+6.0), winner 15.8 (+3.9); the 28 live days, now
30.7 (+19.6), winner 22.8 (+3.0). Switching all three removes more bias but overshoots on the live days (−6.4) and
has a higher error.

## Live

`ensemble_gasrel` in jacobazu/dk1-price-forecasting is now this winner, from the forecast for 14 Nov 2026, changed
before the earlier LEAR-X-only version had a live day. Early check 15 Dec 2026, otherwise 1 Mar 2027.

The caveats from above stand: the idea came from these days, and gas has no untouched period. Seven candidates were
compared and the best one picked, so its 16.28 is a little flattering; the live record decides.

One thing that went differently: `evaluate_models.py` imported two functions from the wrong file and stopped. The
same two functions were copied into it; nothing in the scoring changed.
