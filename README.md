# Brian's Market Charts

Auto-updating Bollinger Band charts (20-period SMA, ±1/2/3 SD) on 10-minute, 1-hour and daily timeframes for Nasdaq, FTSE 100, S&P 500, Dow Jones, NYSE Composite, Philadelphia Semiconductor, PHLX Gold/Silver and KOSPI.

A GitHub Action rebuilds `site/data.json` from free, delayed Yahoo Finance data about every 5–15 minutes on weekdays and publishes to GitHub Pages. The page re-checks for new data every 60 seconds. Mechanical band levels only.
