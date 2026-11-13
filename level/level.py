# lear-x with each day's prices taken relative to a moving level, RULES.md. python level.py DAILY.csv A|B SHARD SHARDS
import sys, warnings
import numpy as np, pandas as pd
from sklearn.linear_model import LassoLarsIC
from sklearn.preprocessing import StandardScaler
sys.path.insert(0, "..")
from common import load, mad
warnings.filterwarnings("ignore")

PARTS = {"A": ("2025-10-01", "2026-11-09", ("nb", "hol", "wx", "wxde"), ("now", "level7", "level28", "gas")),
         "B": ("2021-07-01", "2022-12-31", ("nb", "hol"), ("now", "level7", "level28")),
         "D": ("2021-07-01", "2022-12-31", ("nb", "hol"), ("gasm",)),
         "E": ("2025-10-01", "2026-11-09", ("nb", "hol", "wx", "wxde"), ("gasm",))}


def monthly_gas(dates):
    """last month's neutral gas price, €/MWh, for each day: a month's price is only known after it"""
    from pathlib import Path
    m = pd.read_csv(Path(__file__).with_name("gas_monthly_raw.csv"), header=None, names=["month", "dkk_kwh"])
    m = pd.Series(m.dkk_kwh.to_numpy() * 1000 / 7.44, index=pd.to_datetime(m.month).dt.to_period("M"))
    prev = pd.to_datetime(pd.Series(dates).astype(str)).dt.to_period("M") - 1
    return prev.map(m).to_numpy(dtype=float)


def base(D, variant):
    """per day: what is taken off (a) and divided by (b) before the model sees a price"""
    n = len(D["P"]); day = np.nanmean(D["P"], axis=1)
    a, b = np.zeros(n), np.ones(n)
    if variant.startswith("level"):
        k = int(variant[5:])
        a = np.array([np.mean(day[i - k:i]) if i >= k else np.nan for i in range(n)])   # the k days before, all known
    elif variant == "gas":
        b = D["ex"]["fuel"][:, 0]   # gas price two days before, known in the morning
    elif variant == "gasm":
        b = monthly_gas(D["dates"])
    return a, b


def forecast(D, d, variant, groups, window=730):
    a, b = base(D, variant)
    rel = lambda M: (M - a[:, None]) / b[:, None]
    tr = np.arange(d - window, d)
    P = rel(D["P"])
    med, s = np.nanmedian(P[tr]), mad(P[tr].ravel())
    blocks = [np.arcsinh((rel(D["lags"]) - med) / s)]
    for g in groups:
        X = D["ex"][g].copy()
        if g == "nb":
            X = rel(X)
        if g != "hol":
            series = np.array(D["names"][g])
            for name in np.unique(series):
                j = series == name
                t = X[tr][:, j].ravel()
                if g == "nb":
                    sd = mad(t)
                    sd = sd if np.isfinite(sd) and sd > 0 else np.nanstd(t, ddof=1)
                    X[:, j] = np.arcsinh((X[:, j] - np.nanmedian(t)) / sd)
                else:
                    X[:, j] = (X[:, j] - np.nanmean(t)) / np.nanstd(t, ddof=1)
        blocks.append(X)
    X = np.hstack(blocks + [D["dow"]])
    if not np.isfinite(X[d]).all():
        raise ValueError("missing inputs")
    keep = tr[np.isfinite(X[tr]).all(1) & np.isfinite(P[tr]).all(1)]
    Xtr, Y, xd = X[keep], np.arcsinh((P[keep] - med) / s), X[d:d + 1]
    sc = StandardScaler().fit(Xtr); k = sc.scale_ > 1e-9
    Xtr, xd = sc.transform(Xtr)[:, k], sc.transform(xd)[:, k]
    z = np.array([LassoLarsIC(criterion="bic").fit(Xtr, Y[:, h]).predict(xd)[0] for h in range(24)])
    return a[d] + b[d] * (med + s * np.sinh(z))


if __name__ == "__main__":
    D = load(sys.argv[1]); part, shard, shards = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    lo, hi, groups, variants = PARTS[part]
    t = D["dates"]
    days = [i for i in range(len(t)) if lo <= str(t[i]) <= hi][shard::shards]
    rows = []
    for d in days:
        for v in variants:
            try:
                f = forecast(D, d, v, groups)
            except ValueError as e:
                print(t[d], v, e, flush=True); continue
            rows += [dict(part=part, date=t[d], hour=h, variant=v, forecast=round(f[h], 2), actual=D["P"][d, h]) for h in range(24)]
        print(t[d], flush=True)
    pd.DataFrame(rows).to_csv(f"part{part}_{shard}.csv", index=False)
