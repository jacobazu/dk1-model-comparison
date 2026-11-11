# every model and every equal-weight combination of them, on the days all of them have
# results/models.csv, combos.csv, monthly.csv. diebold-mariano against today's ensemble (newey-west, 7 lags),
# and a model confidence set (hansen, lunde & nason 2011, block bootstrap) so the best of 511 isn't taken at face value
from itertools import combinations
import numpy as np
import pandas as pd
from scipy import stats

MODELS = ["bmtx", "learx", "xgbx", "r_net", "torch_plain", "torch_warm", "torch_dist", "chronos2", "tabpfn"]
TODAY = ["bmtx", "learx", "xgbx"]
CHECKS = ["chronos2_prices_only"]   # shown, not part of any combination


def dm(d, lag=7):
    n, u = len(d), d - d.mean()
    v = (u @ u) / n + 2 * sum((1 - k / (lag + 1)) * (u[k:] @ u[:-k]) / n for k in range(1, lag + 1))
    t = d.mean() / np.sqrt(v / n) * np.sqrt((n - 1) / n)
    return 2 * stats.t.cdf(-abs(t), n - 1)


def mcs(L, B=2000, block=7, seed=1):
    """p-values of the model confidence set (max t statistic) for a days x models loss matrix"""
    n, m = L.shape
    rng = np.random.default_rng(seed)
    W = np.zeros((B, n))
    for b in range(B):   # moving blocks, circular
        starts = rng.integers(0, n, size=int(np.ceil(n / block)))
        idx = ((starts[:, None] + np.arange(block)) % n).ravel()[:n]
        np.add.at(W[b], idx, 1)
    W /= n
    mu, Lb = L.mean(0), W @ L
    alive, p = list(range(m)), np.zeros(m)
    pmax = 0.0
    while len(alive) > 1:
        a = np.array(alive)
        d = mu[a] - mu[a].mean()
        db = Lb[:, a] - Lb[:, a].mean(1, keepdims=True)
        se = np.sqrt(((db - d) ** 2).mean(0))
        t = d / se
        tb = ((db - d) / se).max(1)
        pv = (tb >= t.max()).mean()
        pmax = max(pmax, pv)
        worst = a[np.argmax(t)]
        p[worst] = pmax
        alive.remove(worst)
    p[alive[0]] = 1.0
    return p


fc = pd.read_csv("results/forecasts.csv", parse_dates=["date"])
wide = fc.pivot_table(index=["date", "hour"], columns="model", values="forecast")
actual = fc.groupby(["date", "hour"]).actual.first().reindex(wide.index)
ok = wide.notna().groupby(level=0).all()
base_all = (actual - wide[TODAY].mean(axis=1)).abs().groupby(level=0).mean()
# a model still running (fewer days than today's ensemble) is scored on its own days but kept out of the combinations
full = ok[TODAY].all(axis=1)
models = [m for m in MODELS if m in wide and ok.loc[full, m].all()]
partial = [m for m in MODELS if m in wide and m not in models]

rows = []
for m in models + partial + [c for c in CHECKS if c in wide]:
    have = ok.index[ok[m] & full]
    d = (actual - wide[m]).abs().groupby(level=0).mean().loc[have]
    e = (actual - wide[m]).loc[have]
    rows.append(dict(model=m, days=len(have), mae=d.mean(), today_same_days=base_all.loc[have].mean(),
                     rmse=np.sqrt((e ** 2).mean()), bias=e.mean(), p_vs_today=dm((d - base_all.loc[have]).to_numpy()),
                     group="today" if m in TODAY else "check" if m in CHECKS else "partial" if m in partial else "new"))
single = pd.DataFrame(rows)

days = ok.index[ok[models].all(axis=1)]
wide, actual = wide.loc[days], actual.loc[days]
dloss = lambda f: (actual - f).abs().groupby(level=0).mean()
base = dloss(wide[TODAY].mean(axis=1))

combos, losses = [], []
for k in range(1, len(models) + 1):
    for c in combinations(models, k):
        d = dloss(wide[list(c)].mean(axis=1))
        combos.append(dict(members="+".join(c), size=k, mae=d.mean(), p_vs_today=dm((d - base).to_numpy()) if set(c) != set(TODAY) else np.nan))
        losses.append(d.to_numpy())
combos = pd.DataFrame(combos)
combos["mcs_p"] = mcs(np.column_stack(losses))
combos["in_mcs90"] = combos.mcs_p >= 0.10
combos = combos.sort_values("mae").reset_index(drop=True)
single = single.merge(combos[combos["size"] == 1][["members", "mcs_p", "in_mcs90"]].rename(columns={"members": "model"}), on="model", how="left")

month = wide[models].sub(actual, axis=0).abs().groupby(lambda i: i[0].strftime("%Y-%m")).mean()
best = combos.members[0].split("+")
month["today"] = (actual - wide[TODAY].mean(axis=1)).abs().groupby(lambda i: i[0].strftime("%Y-%m")).mean()
month["best_combo"] = (actual - wide[best].mean(axis=1)).abs().groupby(lambda i: i[0].strftime("%Y-%m")).mean()

single.round(4).to_csv("results/models.csv", index=False)
combos.round(4).to_csv("results/combos.csv", index=False)
month.round(3).rename_axis("month").to_csv("results/monthly.csv")
pd.Series({"days": len(days), "first": str(days.min().date()), "last": str(days.max().date()), "today_mae": round(base.mean(), 4)}).to_csv("results/summary.csv", header=False)
pd.Series(models, name="model").to_csv("results/combined_models.csv", index=False)
print(single.to_string(index=False)); print(combos.head(12).to_string(index=False)); print(combos.in_mcs90.sum(), "combinations in the 90% set")
