# scores parts D and E of RULES.md: lear-x on prices relative to last month's gas price (gasm).
#   part E: gasm against now and gas on part A's 405 days. passes if it keeps at least half of gas's gain over now
#   part D: gasm against part B's now on 1 jul 2021 - 31 dec 2022. passes if it beats now, newey-west p < 0.05
# python score_gasm.py   (from level/, after forecasts_D.csv and forecasts_E.csv). writes scores_gasm.csv
from math import erf, sqrt

import numpy as np
import pandas as pd


def dm(d, lags=7):
    """mean of a daily loss difference, its newey-west t and two-sided p (as in evaluate.py)"""
    d = np.asarray(d, float); n = len(d); m = d.mean(); e = d - m
    v = e @ e / n + 2 * sum((1 - k / (lags + 1)) * (e[k:] @ e[:-k]) / n for k in range(1, lags + 1))
    t = m / np.sqrt(v / n)
    return m, t, 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2))))


def daily(files, variants):
    f = pd.concat([pd.read_csv(x) for x in files])
    f = f[f.variant.isin(variants)]
    full = f.groupby(["date", "variant"]).hour.count().unstack()
    days = full.index[(full.reindex(columns=variants) == 24).all(axis=1)]
    f = f[f.date.isin(days)].assign(ae=lambda x: (x.actual - x.forecast).abs(), e=lambda x: x.actual - x.forecast)
    g = f.groupby(["variant", "date"])[["ae", "e"]].mean().unstack(0)
    return g["ae"], g["e"]


rows = []
ae, e = daily(["forecasts_A.csv", "forecasts_E.csv"], ["now", "gas", "gasm"])
gain_gas = (ae["now"] - ae["gas"]).mean()
m, t, p = dm(ae["now"] - ae["gasm"])
for v in ["now", "gas", "gasm"]:
    rows.append({"part": "E", "variant": v, "days": len(ae), "mae": ae[v].mean(), "bias": e[v].mean()})
rows[-1].update(gain_vs_now=m, dm_t=t, p=p, share_of_gas_gain=m / gain_gas, passes=bool(m >= gain_gas / 2))
pass_e = rows[-1]["passes"]

ae, e = daily(["forecasts_B.csv", "forecasts_D.csv"], ["now", "gasm"])
m, t, p = dm(ae["now"] - ae["gasm"])
for v in ["now", "gasm"]:
    rows.append({"part": "D", "variant": v, "days": len(ae), "mae": ae[v].mean(), "bias": e[v].mean()})
rows[-1].update(gain_vs_now=m, dm_t=t, p=p, passes=bool(m > 0 and p < 0.05))
pass_d = rows[-1]["passes"]

S = pd.DataFrame(rows).round(3)
S.to_csv("scores_gasm.csv", index=False)
print(S.to_string(index=False))
verdict = ("confirmed on 2021-22" if pass_e and pass_d else
           "not confirmed: gasm keeps enough of the gain but doesn't beat now on 2021-22" if pass_e else
           "says little: gasm doesn't keep half of gas's gain, so the monthly stand-in isn't good enough")
print("\nverdict:", verdict)
open("verdict_gasm.txt", "w").write(verdict + "\n")
