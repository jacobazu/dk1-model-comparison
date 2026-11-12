# scores part C as RULES.md says. python evaluate_models.py   (from level/, after forecasts_C.csv)
import sys
from itertools import combinations
import numpy as np, pandas as pd
sys.path.insert(0, "..")
from common import load
from evaluate import dm, holm

D = load("daily_with_live.csv")
day = pd.Series(np.nanmean(D["P"], axis=1), index=pd.to_datetime(D["dates"]))
normal = (day.shift(1) / day.shift(1).rolling(730, min_periods=600).mean().shift(1) <= 1.5)

f = pd.read_csv("forecasts_C.csv", parse_dates=["date"])
w = f.pivot_table(index=["date", "hour"], columns=["model", "variant"], values="forecast")
act = f.groupby(["date", "hour"]).actual.first()
ok = w.notna().all(axis=1).groupby("date").sum() == 24          # days every model and variant forecast
w, act = w[w.index.get_level_values(0).isin(ok.index[ok])], act[act.index.get_level_values(0).isin(ok.index[ok])]
models = ["learx", "bmtx", "xgbx"]
daily = lambda fc: pd.DataFrame({"ae": (act - fc).abs(), "e": act - fc}).groupby("date").mean()
nm = normal.reindex(daily(w[("learx", "now")]).index).to_numpy()


def row(name, fc, base):
    d, b = daily(fc), daily(base)
    g, t, p = dm(b.ae - d.ae)
    return {"name": name, "days": len(d), "mae": d.ae.mean(), "bias": d.e.mean(), "mae_normal": d.ae[nm].mean(),
            "bias_normal": d.e[nm].mean(), "mae_high": d.ae[~nm].mean(), "bias_high": d.e[~nm].mean(),
            "gain": g, "dm_t": t, "p": p, "base_mae": b.ae.mean(), "base_mae_normal": b.ae[nm].mean(), "base_bias": b.e.mean()}


per = pd.DataFrame([row(m, w[(m, "gas")], w[(m, "now")]) for m in models])
per["p_holm"] = holm(per.p)
ens_now = sum(w[(m, "now")] for m in models) / 3
cands = [c for k in (1, 2, 3) for c in combinations(models, k)]
ens = pd.DataFrame([row("+".join(c), sum(w[(m, "gas" if m in c else "now")] for m in models) / 3, ens_now) for c in cands])
ens["p_holm"] = holm(ens.p)
ens["passes"] = (ens.p_holm < 0.05) & (ens.gain > 0) & (ens.mae_normal <= 1.03 * ens.base_mae_normal)
per.round(3).to_csv("scores_models.csv", index=False)
ens.round(3).to_csv("scores_ensembles.csv", index=False)
cols = ["name", "days", "base_mae", "mae", "base_bias", "bias", "bias_normal", "bias_high", "gain", "p_holm"]
print(per[cols].round(2).to_string(index=False)); print()
print(ens[cols + ["mae_normal", "base_mae_normal", "passes"]].round(2).to_string(index=False))
won = ens[ens.passes].sort_values("mae")
winner = won.name.iloc[0] if len(won) else None
print("\nwinner:", winner)
open("winner_ensemble.txt", "w").write(str(winner) + "\n")
