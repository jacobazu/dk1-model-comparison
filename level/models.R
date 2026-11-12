# part C: the three live models (lear-x, bmt-x, xgboost-x), as they are and on prices relative to gas, on part A's days.
# run from a checkout of jacobazu/dk1-price-forecasting, whose model code it uses unchanged:
#   Rscript ../level/models.R ../level/daily_with_live.csv SHARD SHARDS OUT.csv
suppressMessages({
  library(readr)
  source("R/lear.R"); source("R/bmt.R"); source("R/exog.R"); source("R/xmodels.R"); source("R/xgb.R"); source("R/inputs.R")
})
a <- commandArgs(trailingOnly = TRUE)
tab <- read_csv(a[1], show_col_types = FALSE)
shard <- as.integer(a[2]); shards <- as.integer(a[3])

P <- as.matrix(tab[, paste0("p_h", 0:23)]); colnames(P) <- paste0("h", 0:23)
features <- make_features(bind_cols(tibble(date = tab$date), as_tibble(P)))
exog <- lapply(setNames(nm = c("nb", "hol", "wx", "wxde", "fuel")), \(g) {
  m <- as.matrix(tab[, startsWith(names(tab), paste0(g, ":"))]); colnames(m) <- sub("^[a-z]+:", "", colnames(m)); m
})
rel <- gas_relative(features, exog)
tun <- read_csv("results/xgb_tuning.csv", show_col_types = FALSE) |> filter(model == "xgbx", chosen)
groups <- forecast_groups   # nb, hol, wx, wxde: the live inputs

run <- function(f, e, d, scale = 1) {
  xgb <- \() xgb_forecast_day(f, d, exog = e[groups], params = modifyList(xgb_params, list(max_depth = tun$max_depth)),
                              rounds = tun$rounds, seed = as.integer(tab$date[d]))
  list(learx = scale * learx_forecast_day(f, e, d, groups), bmtx = scale * bmtx_forecast_day(f, e, d, groups), xgbx = scale * xgb())
}
days <- which(tab$date >= as_date("2025-10-01") & tab$date <= as_date("2026-11-09"))
days <- days[seq_along(days) %% shards == shard]
out <- list()
for (d in days) {
  r <- list(now = run(features, exog, d), gas = run(rel$features, rel$exog, d, rel$gas[d]))
  for (v in names(r)) for (m in names(r[[v]]))
    out[[length(out) + 1]] <- tibble(date = tab$date[d], hour = 0:23, model = m, variant = v,
                                     forecast = round(r[[v]][[m]], 2), actual = features$P[d, ])
  message(tab$date[d])
}
write_csv(bind_rows(out), a[4])
