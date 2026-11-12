# part A's last 28 days (13 oct to 9 nov 2026). the archived inputs had no neighbour prices or dk1 weather for them,
# so the github run skipped them; here they come from the price repo's live inputs, which match the archive exactly
# on the 104 days both cover. python live_days.py DAILY_WITH_LIVE.csv SHARD SHARDS
import sys
import pandas as pd
sys.path.insert(0, "..")
from common import load
from level import PARTS, forecast

D = load(sys.argv[1]); shard, shards = int(sys.argv[2]), int(sys.argv[3])
_, hi, groups, variants = PARTS["A"]
t = D["dates"]
rows = []
for d in [i for i in range(len(t)) if "2026-10-13" <= str(t[i]) <= hi][shard::shards]:
    for v in variants:
        f = forecast(D, d, v, groups)
        rows += [dict(part="A", date=t[d], hour=h, variant=v, forecast=round(f[h], 2), actual=D["P"][d, h]) for h in range(24)]
    print(t[d], flush=True)
pd.DataFrame(rows).to_csv(f"live_{shard}.csv", index=False)
