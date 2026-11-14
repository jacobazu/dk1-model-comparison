# DK1 model comparison

Neural networks and pretrained forecasting models (Chronos-2, TabPFN, Timestral) against the models that make my live DK1 day-ahead price forecast. Same 377 test days (1 Oct 2025 to 12 Oct 2026), same inputs, same scoring. The rules were set before any test run.

Results: [jacobazu.github.io/models](https://jacobazu.github.io/models/)

## What it found

| | Mean absolute error, €/MWh |
|---|---|
| Today's live forecast (average of BMT-X, LEAR-X, XGBoost-X) | 16.65 |
| Best single new model, Chronos-2 | 15.56 |
| Best mix, PyTorch distribution network + Chronos-2 | 14.69 |
| Timestral (Mistral, released 11 Nov 2026) | 14.41 |

- All 511 mixes of the nine candidate models were scored. 247 of them can't be told apart from the best at the 90% level (model confidence set), so the ranking at the top is noise. Beating today's forecast is not.
- Timestral came out after the test days, so it may have seen them in training. It is shown but kept out of the mixes, and only its live record counts.
- Winners don't replace the live forecast on a backtest. Chronos-2 with today's models, Chronos-2 with the PyTorch network, and Timestral with today's models run live as challengers from 13 Nov 2026, saved before each auction. They get one early check on 15 Dec 2026 (p < 0.01), otherwise they are judged on 1 Mar 2027.
- Gas fix tested on 2021-22 as well, with a monthly gas price (`level/RESULT.md`, Parts D and E): it removes the bias there too, but the error doesn't fall, so it is not confirmed outside 2025-26. It stays a live challenger.

TabPFN is too slow for a laptop over a full year, so its days were split over parallel GitHub jobs here.

## License

Code: [MIT](LICENSE).

Data: prices, neighbour prices and gas from Energi Data Service (Energinet), not covered by the MIT License or endorsed by Energinet; weather forecasts from Open-Meteo.com (CC BY 4.0).
