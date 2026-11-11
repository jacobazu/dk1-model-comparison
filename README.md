# DK1 model comparison

Pretrained forecasting models (TabPFN, Chronos-2) against my own models for DK1 day-ahead prices. Same test days (1 Oct 2025 to 9 Nov 2026), same inputs and the same scoring as the neural networks in [dk1-price-forecasting](https://github.com/jacobazu/dk1-price-forecasting/tree/master/bakeoff). The rules were set before any test run.

TabPFN is too slow for a laptop over a full year, so the days are split over parallel GitHub jobs here.

Data: prices, neighbour prices and gas from Energi Data Service (Energinet); weather forecasts from Open-Meteo.com (CC BY 4.0).
