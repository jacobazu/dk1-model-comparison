# scores the level test as RULES.md says. python evaluate.py   (from level/, after forecasts_A.csv and forecasts_B.csv)
import sys
from math import erf, sqrt
import numpy as np, pandas as pd
sys.path.insert(0, "..")
from common import load


def dm(d, lags=7):
    """mean of a daily loss difference, its newey-west t and two-sided p"""
    d = np.asarray(d, float); n = len(d); m = d.mean(); e = d - m
    v = e @ e / n + 2 * sum((1 - k / (lags + 1)) * (e[k:] @ e[:-k]) / n for k in range(1, lags + 1))
    t = m / np.sqrt(v / n)
    return m, t, 2 * (1 - 0.5 * (1 + erf(abs(t) / sqrt(2))))


def holm(p):
    p = np.asarray(p); o = np.argsort(p); out = np.empty(len(p)); run = 0
    for i, j in enumerate(o):
        run = max(run, min(1, (len(p) - i) * p[j])); out[j] = run
    return out


D = load("../inputs/daily.csv")
day = pd.Series(np.nanmean(D["P"], axis=1), index=pd.to_datetime(D["dates"]))
# normal day: yesterday's average at most 1.5 times the average of the two years before
normal = (day.shift(1) / day.shift(1).rolling(730, min_periods=600).mean().shift(1) <= 1.5)

scores, daily_out = [], []
for part in "AB":
    f = pd.read_csv(f"forecasts_{part}.csv", parse_dates=["date"])
    f["ae"], f["e"] = (f.actual - f.forecast).abs(), f.actual - f.forecast
    full = f.groupby(["date", "variant"]).hour.count().unstack()
    days = full.index[(full == 24).all(axis=1)]            # days every variant forecast
    g = f[f.date.isin(days)].groupby(["variant", "date"])[["ae", "e"]].mean().unstack(0)
    ae, e = g["ae"], g["e"]
    nm = normal.reindex(ae.index).to_numpy()
    cand = [v for v in ae.columns if v != "now"]
    tests = {v: dm(ae["now"] - ae[v]) for v in cand}
    ph = dict(zip(cand, holm([tests[v][2] for v in cand])))
    for v in ae.columns:
        scores.append({"part": part, "variant": v, "days": len(ae), "mae": ae[v].mean(), "bias": e[v].mean(),
                       "mae_normal": ae[v][nm].mean(), "bias_normal": e[v][nm].mean(), "days_normal": int(nm.sum()),
                       "mae_high": ae[v][~nm].mean(), "bias_high": e[v][~nm].mean(), "days_high": int((~nm).sum()),
                       "gain_vs_now": tests[v][0] if v in tests else np.nan, "dm_t": tests[v][1] if v in tests else np.nan,
                       "p": tests[v][2] if v in tests else np.nan, "p_holm": ph.get(v, np.nan)})
    daily_out.append(pd.concat({"ae": ae, "e": e}, axis=1).assign(part=part, normal=nm))
S = pd.DataFrame(scores)
now = S[S.variant == "now"].set_index("part")
S["passes"] = [r.variant != "now" and r.p_holm < 0.05 and r.gain_vs_now > 0 and
               (r.part == "B" or r.mae_normal <= 1.03 * now.loc[r.part, "mae_normal"]) for r in S.itertuples()]
S.round(3).to_csv("scores.csv", index=False)
pd.concat(daily_out).round(2).to_csv("daily.csv")

A = S[(S.part == "A") & S.passes].sort_values("mae")
winner = None
for v in A.variant:
    if v.startswith("level") and not S[(S.part == "B") & (S.variant == v)].passes.any():
        continue
    winner = v; break
print(S.round(2).to_string(index=False))
print("\nwinner:", winner)
open("winner.txt", "w").write(str(winner) + "\n")
