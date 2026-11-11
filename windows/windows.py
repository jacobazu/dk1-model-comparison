# lear-x with the training windows in RULES.md, on the tuning days. python windows.py DAILY.csv PART PARTS
import sys, numpy as np, pandas as pd, warnings
from sklearn.linear_model import LassoLarsIC
from sklearn.preprocessing import StandardScaler
sys.path.insert(0, "..")
from common import load, mad
warnings.filterwarnings("ignore")


def inputs(D, d, scale_from, train_from, groups=("nb", "hol", "wx", "wxde", "fuel")):
    sc_rows, tr = np.arange(scale_from, d), np.arange(train_from, d)
    P = D["P"]
    med, s = np.nanmedian(P[sc_rows]), mad(P[sc_rows].ravel())
    blocks = [np.arcsinh((D["lags"] - med) / s)]
    for g in groups:
        X = D["ex"][g].copy()
        if g != "hol":
            series = np.array(D["names"][g])
            for name in np.unique(series):
                j = series == name
                t = X[sc_rows][:, j].ravel()
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
    return X[keep], np.arcsinh((P[keep] - med) / s), X[d:d + 1], lambda z: med + s * np.sinh(z)


def lear(D, d, scale_from, train_from):
    Xtr, Y, xd, back = inputs(D, d, scale_from, train_from)
    sc = StandardScaler().fit(Xtr); k = sc.scale_ > 1e-9
    Xtr, xd = sc.transform(Xtr)[:, k], sc.transform(xd)[:, k]
    return back(np.array([LassoLarsIC(criterion="bic").fit(Xtr, Y[:, h]).predict(xd)[0] for h in range(24)]))


D = load(sys.argv[1])
part, parts = int(sys.argv[2]), int(sys.argv[3])
t = D["dates"]
days = [i for i in range(len(t)) if "2024-10-01" <= str(t[i]) <= "2025-09-30"][::7]
days = [d for d in days if len(inputs(D, d, d - 730, d - 730)[0]) >= 1.1 * inputs(D, d, d - 730, d - 730)[0].shape[1]][part::parts]
first = 8   # the first rows have no lagged prices
# training always on the complete days in the last 730 (before 2026 that is every day since march 2024 anyway);
# what changes is how many days of history the price scaling is taken over
V = {"scale_1y": lambda d: (d - 365, d - 730), "now": lambda d: (d - 730, d - 730), "scale_3y": lambda d: (d - 1095, d - 730),
     "scale_4y": lambda d: (d - 1460, d - 730), "scale_all": lambda d: (first, d - 730)}
rows = []
for d in days:
    for v, f in V.items():
        fc = lear(D, d, *f(d))
        rows += [dict(date=t[d], hour=h, variant=v, forecast=round(fc[h], 2), actual=D["P"][d, h]) for h in range(24)]
    print(t[d], flush=True)
pd.DataFrame(rows).to_csv(f"part{part}.csv", index=False)
