"""Builds site/data.json: 8 indices x 3 timeframes with SMA20 and Bollinger Bands (1/2/3 SD).
Free Yahoo Finance data via yfinance (delayed). No invented prices: failures are recorded as gaps."""
import json, math, os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import pandas as pd
import yfinance as yf

LON = ZoneInfo("Europe/London")
INDICES = [
    ("nasdaq", "^IXIC", "Nasdaq Composite", "about 15 min"),
    ("ftse", "^FTSE", "FTSE 100", "about 15 min"),
    ("sp500", "^GSPC", "S&P 500", "about 15 min"),
    ("dow", "^DJI", "Dow Jones", "about 15 min"),
    ("nyse", "^NYA", "NYSE Composite", "about 15 min"),
    ("sox", "^SOX", "Philadelphia Semiconductor", "about 15 min"),
    ("xau", "^XAU", "PHLX Gold/Silver", "about 15 min"),
    ("kospi", "^KS11", "KOSPI (South Korea)", "about 20 min; trades overnight UK time"),
]
TF = {"10m": ("5d", "5m", "10min", 120), "1h": ("1mo", "60m", None, 120), "1d": ("6mo", "1d", None, 130)}

def clean(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 2)

def fetch(sym, tf):
    period, interval, resample, keep = TF[tf]
    df = yf.download(sym, period=period, interval=interval, progress=False, auto_adjust=False)
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close"]].dropna()
    if resample:
        df = df.resample(resample, label="left", closed="left").agg(
            {"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()
    c = df["Close"]; sma = c.rolling(20).mean(); sd = c.rolling(20).std(ddof=0)
    df = df.assign(sma=sma, **{f"u{k}": sma + k * sd for k in (1, 2, 3)}, **{f"l{k}": sma - k * sd for k in (1, 2, 3)})
    df = df.tail(keep)
    idx = df.index
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    if tf == "1d":
        t = [d.strftime("%Y-%m-%d") for d in idx]
    else:
        t = [d.tz_convert(LON).strftime("%Y-%m-%d %H:%M") for d in idx]
    out = {"t": t}
    for col, key in [("Open", "o"), ("High", "h"), ("Low", "l"), ("Close", "c"), ("sma", "sma"),
                     ("u1", "u1"), ("u2", "u2"), ("u3", "u3"), ("l1", "l1"), ("l2", "l2"), ("l3", "l3")]:
        out[key] = [clean(v) for v in df[col]]
    last = df.iloc[-1]
    p = last["Close"]
    if any(math.isnan(last[k]) for k in ("sma", "u3", "l3")):
        status = "not enough bars for bands"
    elif p >= last["u3"]: status = "above +3 SD (extreme)"
    elif p >= last["u2"]: status = "between +2 and +3 SD (sell zone)"
    elif p >= last["u1"]: status = "between +1 and +2 SD"
    elif p >= last["sma"]: status = "between SMA20 and +1 SD"
    elif p >= last["l1"]: status = "between −1 SD and SMA20"
    elif p >= last["l2"]: status = "between −2 and −1 SD"
    elif p >= last["l3"]: status = "between −3 and −2 SD (buy zone)"
    else: status = "below −3 SD (stop level)"
    out["last"] = {"price": clean(p), "time": t[-1], "status": status,
                   **{k: clean(last[k]) for k in ("sma", "u1", "u2", "u3", "l1", "l2", "l3")}}
    return out

def main():
    data = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "generated_london": datetime.now(LON).strftime("%d %b %Y, %H:%M"), "indices": []}
    for slug, sym, name, delay in INDICES:
        item = {"slug": slug, "symbol": sym, "name": name, "delay": delay, "tf": {}, "gaps": []}
        for tf in TF:
            try:
                r = fetch(sym, tf)
                if r: item["tf"][tf] = r
                else: item["gaps"].append(tf)
            except Exception as e:
                item["gaps"].append(f"{tf} ({type(e).__name__})")
        data["indices"].append(item)
    os.makedirs("site", exist_ok=True)
    with open("site/data.json", "w") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
    print("built", data["generated_london"], [(i["slug"], list(i["tf"]), i["gaps"]) for i in data["indices"]])

if __name__ == "__main__":
    main()
