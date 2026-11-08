"""
data_manager.py — Forex data acquisition and derived-column calculations.
"""

import pandas as pd
import yfinance as yf
import numpy as np
from typing import Optional


class DataManager:
    """Downloads Forex history from Yahoo Finance and computes statistics for multiple timeframes."""

    PAIRS = [
        "EURUSD=X", "GBPUSD=X", "AUDUSD=X", "NZDUSD=X", "USDJPY=X", "USDCAD=X", "USDCHF=X",
        "EURGBP=X", "EURJPY=X", "EURCHF=X", "EURAUD=X", "EURNZD=X",
        "GBPAUD=X", "GBPJPY=X", "GBPCHF=X", "GBPCAD=X", "GBPNZD=X",
        "AUDJPY=X", "AUDCAD=X", "AUDCHF=X", "AUDNZD=X",
        "NZDJPY=X", "NZDCAD=X", "NZDCHF=X",
        "CADJPY=X", "CADCHF=X",
        "CHFJPY=X",
        "GC=F", "XAGUSD=X", "CL=F", "BTC-USD"
    ]

    INSTRUMENT_SPECS = {
        "EURUSD=X": {"type": "forex", "base": "EUR", "quote": "USD", "tick_size": 0.0001, "contract_size": 100000},
        "GBPUSD=X": {"type": "forex", "base": "GBP", "quote": "USD", "tick_size": 0.0001, "contract_size": 100000},
        "AUDUSD=X": {"type": "forex", "base": "AUD", "quote": "USD", "tick_size": 0.0001, "contract_size": 100000},
        "NZDUSD=X": {"type": "forex", "base": "NZD", "quote": "USD", "tick_size": 0.0001, "contract_size": 100000},
        "USDJPY=X": {"type": "forex", "base": "USD", "quote": "JPY", "tick_size": 0.01, "contract_size": 100000},
        "USDCAD=X": {"type": "forex", "base": "USD", "quote": "CAD", "tick_size": 0.0001, "contract_size": 100000},
        "USDCHF=X": {"type": "forex", "base": "USD", "quote": "CHF", "tick_size": 0.0001, "contract_size": 100000},

        "EURGBP=X": {"type": "forex", "base": "EUR", "quote": "GBP", "tick_size": 0.0001, "contract_size": 100000},
        "EURJPY=X": {"type": "forex", "base": "EUR", "quote": "JPY", "tick_size": 0.01, "contract_size": 100000},
        "EURCHF=X": {"type": "forex", "base": "EUR", "quote": "CHF", "tick_size": 0.0001, "contract_size": 100000},
        "EURAUD=X": {"type": "forex", "base": "EUR", "quote": "AUD", "tick_size": 0.0001, "contract_size": 100000},
        "EURNZD=X": {"type": "forex", "base": "EUR", "quote": "NZD", "tick_size": 0.0001, "contract_size": 100000},

        "GBPAUD=X": {"type": "forex", "base": "GBP", "quote": "AUD", "tick_size": 0.0001, "contract_size": 100000},
        "GBPJPY=X": {"type": "forex", "base": "GBP", "quote": "JPY", "tick_size": 0.01, "contract_size": 100000},
        "GBPCHF=X": {"type": "forex", "base": "GBP", "quote": "CHF", "tick_size": 0.0001, "contract_size": 100000},
        "GBPCAD=X": {"type": "forex", "base": "GBP", "quote": "CAD", "tick_size": 0.0001, "contract_size": 100000},
        "GBPNZD=X": {"type": "forex", "base": "GBP", "quote": "NZD", "tick_size": 0.0001, "contract_size": 100000},

        "AUDJPY=X": {"type": "forex", "base": "AUD", "quote": "JPY", "tick_size": 0.01, "contract_size": 100000},
        "AUDCAD=X": {"type": "forex", "base": "AUD", "quote": "CAD", "tick_size": 0.0001, "contract_size": 100000},
        "AUDCHF=X": {"type": "forex", "base": "AUD", "quote": "CHF", "tick_size": 0.0001, "contract_size": 100000},
        "AUDNZD=X": {"type": "forex", "base": "AUD", "quote": "NZD", "tick_size": 0.0001, "contract_size": 100000},

        "NZDJPY=X": {"type": "forex", "base": "NZD", "quote": "JPY", "tick_size": 0.01, "contract_size": 100000},
        "NZDCAD=X": {"type": "forex", "base": "NZD", "quote": "CAD", "tick_size": 0.0001, "contract_size": 100000},
        "NZDCHF=X": {"type": "forex", "base": "NZD", "quote": "CHF", "tick_size": 0.0001, "contract_size": 100000},

        "CADJPY=X": {"type": "forex", "base": "CAD", "quote": "JPY", "tick_size": 0.01, "contract_size": 100000},
        "CADCHF=X": {"type": "forex", "base": "CAD", "quote": "CHF", "tick_size": 0.0001, "contract_size": 100000},
        "CHFJPY=X": {"type": "forex", "base": "CHF", "quote": "JPY", "tick_size": 0.01, "contract_size": 100000},

        "XAGUSD=X": {"type": "metal", "base": "XAG", "quote": "USD", "tick_size": 0.01, "contract_size": 5000},
        "GC=F": {"type": "metal", "base": "XAU", "quote": "USD", "tick_size": 0.1, "contract_size": 100},
        "CL=F": {"type": "energy", "base": "WTI", "quote": "USD", "tick_size": 0.01, "contract_size": 1000},
        "BTC-USD": {"type": "crypto", "base": "BTC", "quote": "USD", "tick_size": 0.01, "contract_size": 1},
    }

    TIMEFRAMES = [
        "1m",
        "5m",
        "15m",
        "30m",
        "1h",
        "4h",
        "1d",
        "1wk",
        "1mo"
    ]

    TIMEFRAME_CONFIG = {
        "1m": {"interval": "1m", "period": "7d", "resample": None},
        "5m": {"interval": "5m", "period": "60d", "resample": None},
        "15m": {"interval": "15m", "period": "60d", "resample": None},
        "30m": {"interval": "30m", "period": "60d", "resample": None},
        "1h": {"interval": "1h", "period": "730d", "resample": None},
        "4h": {"interval": "1h", "period": "730d", "resample": "4h"},
        "1d": {"interval": "1d", "period": "max", "resample": None},
        "1wk": {"interval": "1wk", "period": "max", "resample": None},
        "1mo": {"interval": "1mo", "period": "max", "resample": None},
    }

    @staticmethod
    def fetch(ticker: str, timeframe: str = "1d") -> tuple[pd.DataFrame, dict, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict, pd.DataFrame]:
        """
        Download history for *ticker* and *timeframe*, then return a tuple:
        (DataFrame, dict of summary statistics, oo_freq_df, hl_freq_df, oo_cond_df, oo_bands_df, resume_df, atr_timeframes, ohlc_raw_df)
        """
        config = DataManager.TIMEFRAME_CONFIG.get(timeframe, DataManager.TIMEFRAME_CONFIG["1d"])
        raw = yf.download(ticker, period=config["period"], interval=config["interval"], progress=False)

        if raw.empty:
            return pd.DataFrame(), {}, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}, pd.DataFrame()

        # Resample if needed (for 4h)
        if config["resample"] is not None:
            # Resample OHLC data
            raw = raw.resample(config["resample"]).agg({
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum"
            })

        # yfinance may return MultiIndex columns when a single ticker is
        # passed; flatten to simple column names.
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)

        df = raw[["Open", "High", "Low", "Close"]].copy()

        # Include Volume if available
        if "Volume" in raw.columns:
            df["Volume"] = raw["Volume"]
        else:
            df["Volume"] = 0

        df.dropna(inplace=True)

        # Derived columns --------------------------------------------------
        hl = (df["High"] - df["Low"]) / df["Low"]
        oo = (df["Open"] - df["Open"].shift(1)) / df["Open"].shift(1)

        hl_pct = hl * 100
        oo_pct = oo * 100

        # ── True Range (J. Welles Wilder) ──────────────────────────────────
        # TR = max(High − Low, |High − Prev Close|, |Low − Prev Close|)
        prev_close = df["Close"].shift(1)
        tr = pd.concat([
            df["High"] - df["Low"],
            (df["High"] - prev_close).abs(),
            (df["Low"]  - prev_close).abs(),
        ], axis=1).max(axis=1)

        # ATR as % of previous close (comparable to the old dailyatr_pct scale)
        dailyatr_pct = (tr / prev_close) * 100

        # Calculate stats on vector data excluding the last row (incomplete current candle)
        stats = {}
        for col_name, series in [("H-L", hl_pct), ("O-O", oo_pct), ("Daily ATR", dailyatr_pct)]:
            if len(series) > 1:
                hist = series.iloc[:-1].dropna() # yesterday and older
                stats[col_name] = {
                    "Count": hist.count(),
                    "Average / Mean": hist.mean(),
                    "Standard Error (sem)": hist.sem(),
                    "Median": hist.median(),
                    "Mode": hist.mode().iloc[0] if not hist.mode().empty else float('nan'),
                    "Standard Deviation": hist.std(),
                    "Sample Variance": hist.var(),
                    "Kurtosis": hist.kurt(),
                    "Skewness": hist.skew(),
                    "Range": hist.max() - hist.min() if not hist.empty else float('nan'),
                    "Minimum": hist.min(),
                    "Maximum": hist.max(),
                    "Sum": hist.sum()
                }
            else:
                stats[col_name] = {}

        df["H-L"] = hl_pct
        df["O-O"] = oo_pct
        df["dailyatr"] = dailyatr_pct

        # Preserve raw OHLC + Volume for chart rendering (before formatting for display)
        ohlc_raw = df[["Open", "High", "Low", "Close", "Volume"]].copy()

        # Round OHLC to 5 decimals
        for col in ["Open", "High", "Low", "Close"]:
            df[col] = df[col].round(5)

        # Format percentage columns: 3 decimal places + % suffix
        for col in ["H-L", "O-O", "dailyatr"]:
            df[col] = df[col].round(3).apply(lambda x: f"{x:.3f}%" if pd.notna(x) else "")

        # Move index (Date) into a regular column
        df.reset_index(inplace=True)
        df.rename(columns={"index": "Date"}, inplace=True)

        # Ensure Date column name is "Date" regardless of index name
        if "Date" not in df.columns:
            df.rename(columns={df.columns[0]: "Date"}, inplace=True)

        # Format Date as string for display (include time for intraday timeframes
        dt_col = pd.to_datetime(df["Date"])
        # Check if timeframe is intraday
        if timeframe in ["1m", "5m", "15m", "30m", "1h", "4h"]:
            df["Date"] = dt_col.dt.strftime("%Y-%m-%d %H:%M")
        else:
            df["Date"] = dt_col.dt.strftime("%Y-%m-%d")

        # Frequency Distributions
        if len(oo_pct) > 1 and len(hl_pct) > 1:
            oo_freq = DataManager._calc_oo_freq(oo_pct.iloc[:-1].dropna())
            hl_freq = DataManager._calc_hl_freq(hl_pct.iloc[:-1].dropna())
            oo_cond = DataManager._calc_oo_cond(oo_pct.iloc[:-1].dropna())
            oo_bands = DataManager._calc_oo_bands(stats)
            resume_df = DataManager._calc_resume(oo_pct, hl_pct, oo_cond, oo_bands)
            atr_timeframes = DataManager._calc_atr_timeframes(dailyatr_pct)
        else:
            oo_freq, hl_freq, oo_cond, oo_bands, resume_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            atr_timeframes = {}

        return df, stats, oo_freq, hl_freq, oo_cond, oo_bands, resume_df, atr_timeframes, ohlc_raw

    @staticmethod
    def _calc_resume(series_oo: pd.Series, series_hl: pd.Series, oo_cond: pd.DataFrame, oo_bands: pd.DataFrame) -> pd.DataFrame:
        if len(series_oo) < 6:
            return pd.DataFrame()

        hist_oo = series_oo.iloc[:-1]
        hist_hl = series_hl.iloc[:-1]

        last_oo = hist_oo.iloc[-1]
        last_hl = hist_hl.iloc[-1]

        oo_weekly_avg = hist_oo.rolling(5).mean().iloc[-1]
        hl_weekly_avg = hist_hl.rolling(5).mean().iloc[-1]

        hist_before_yesterday = hist_oo.iloc[:-1]
        if not hist_before_yesterday.empty:
            oo_100_max = hist_before_yesterday.tail(100).max()
            oo_100_min = hist_before_yesterday.tail(100).min()
        else:
            oo_100_max = float('nan')
            oo_100_min = float('nan')

        avg_pos = oo_cond[oo_cond["Segment"] == "Average Pos'"]["proba% (Average)"].values[0] if not oo_cond.empty else 0.0
        avg_neg = oo_cond[oo_cond["Segment"] == "Average Neg'"]["proba% (Average)"].values[0] if not oo_cond.empty else 0.0

        if not oo_bands.empty:
            upper1 = oo_bands[oo_bands["Std Dev"] == "Upper"]["1"].values[0]
            lower1 = oo_bands[oo_bands["Std Dev"] == "Lower"]["1"].values[0]
            upper2 = oo_bands[oo_bands["Std Dev"] == "Upper"]["2"].values[0]
            lower2 = oo_bands[oo_bands["Std Dev"] == "Lower"]["2"].values[0]
            upper3 = oo_bands[oo_bands["Std Dev"] == "Upper"]["3"].values[0]
            lower3 = oo_bands[oo_bands["Std Dev"] == "Lower"]["3"].values[0]
        else:
            upper1 = lower1 = upper2 = lower2 = upper3 = lower3 = 0.0

        vol_label = "DAILY VOLATILITY : Volatile FX" if last_hl > hl_weekly_avg else "DAILY VOLATILITY : LESS VOLATILE FX"
        ret_label = "DAILY RETURN : UPSIDE RETURN" if last_oo > oo_weekly_avg else "DAILY RETURN : DOWNSIDE RETURN"
        max_100_label = "Biggest Return in the last 100 days" if last_oo > oo_100_max else "Still under its Max Last-100-days"
        min_100_label = "Biggest Negative Return in the last 100 days" if last_oo < oo_100_min else "Still above its Min Last-100-days"

        if last_oo > avg_pos:
            pos_neg_label = "Above Positive Daily Average"
        elif last_oo < avg_neg:
            pos_neg_label = "Below Negative Daily Average"
        else:
            pos_neg_label = "Normal Distributed Return"

        if last_oo > upper1:
            sd1_label = "Above 1 Std dev :Positivly Volatile"
        elif last_oo < lower1:
            sd1_label = "Below 1 Std dev : Negativly Volatile"
        else:
            sd1_label = "Normal STD DEV 1"

        if last_oo > upper2:
            sd2_label = "Above 2 Std dev :Positivly Volatile"
        elif last_oo < lower2:
            sd2_label = "Below 2 Std dev : Negativly Volatile"
        else:
            sd2_label = "Normal STD DEV 2"

        if last_oo > upper3:
            sd3_label = "Above 3 Std dev :Extremly Positivly Volatile"
        elif last_oo < lower3:
            sd3_label = "Below 3 Std dev : Extremly Negativly Volatile"
        else:
            sd3_label = "Normal STD DEV 3"

        metrics = [
            "Daily Volatility vs Weekly Avg",
            "Daily Return vs Weekly Avg",
            "100-Day Max Breakdown",
            "100-Day Min Breakdown",
            "Pos/Neg Segmentation Check",
            "1 Standard Deviation Check",
            "2 Standard Deviation Check",
            "3 Standard Deviation Check"
        ]

        labels = [vol_label, ret_label, max_100_label, min_100_label, pos_neg_label, sd1_label, sd2_label, sd3_label]
        cur_vals = [last_hl, last_oo, last_oo, last_oo, last_oo, last_oo, last_oo, last_oo]

        bench_strs = [
            f"{hl_weekly_avg:.4f}%",
            f"{oo_weekly_avg:.4f}%",
            f"{oo_100_max:.4f}%",
            f"{oo_100_min:.4f}%",
            f"Pos: {avg_pos:.4f}% | Neg: {avg_neg:.4f}%",
            f"Up: {upper1:.4f}% | Dn: {lower1:.4f}%",
            f"Up: {upper2:.4f}% | Dn: {lower2:.4f}%",
            f"Up: {upper3:.4f}% | Dn: {lower3:.4f}%"
        ]

        cur_strs = [f"{v:.4f}%" for v in cur_vals]

        return pd.DataFrame({
            "Analysis Metric": metrics,
            "Status / Result": labels,
            "Current Value (Yesterday)": cur_strs,
            "Comparison Benchmark": bench_strs
        })

    @staticmethod
    def _calc_oo_bands(stats: dict) -> pd.DataFrame:
        oo_stats = stats.get("O-O", {})
        if not oo_stats:
            return pd.DataFrame()

        mean = oo_stats.get("Average / Mean", 0.0)
        std = oo_stats.get("Standard Deviation", 0.0)

        return pd.DataFrame({
            "Std Dev": ["Upper", "Lower"],
            "1": [mean + std, mean - std],
            "2": [mean + 2 * std, mean - 2 * std],
            "3": [mean + 3 * std, mean - 3 * std]
        })

    @staticmethod
    def _calc_oo_cond(series: pd.Series) -> pd.DataFrame:
        if series.empty:
            return pd.DataFrame()

        total = len(series)
        pos_series = series[series > 0]
        neg_series = series[series < 0]
        zero_series = series[series == 0]

        avg_pos = pos_series.mean() if not pos_series.empty else 0.0
        avg_neg = neg_series.mean() if not neg_series.empty else 0.0
        avg_zero = 0.0

        cnt_pos = len(pos_series)
        cnt_neg = len(neg_series)
        cnt_zero = len(zero_series)

        freq_pct_pos = cnt_pos / total if total > 0 else 0.0
        freq_pct_neg = cnt_neg / total if total > 0 else 0.0
        freq_pct_zero = cnt_zero / total if total > 0 else 0.0

        return pd.DataFrame({
            "Segment": ["Average Pos'", "Average Neg'", "Zero"],
            "proba% (Average)": [avg_pos, avg_neg, avg_zero],
            "Freq' (Count)": [cnt_pos, cnt_neg, cnt_zero],
            "Freq %": [freq_pct_pos, freq_pct_neg, freq_pct_zero],
            "Prob' Adjust % Change": [avg_pos * freq_pct_pos, avg_neg * freq_pct_neg, 0.0]
        })

    @staticmethod
    def _calc_oo_freq(series: pd.Series) -> pd.DataFrame:
        if series.empty:
            return pd.DataFrame()
        edges = [-np.inf] + list(np.round(np.arange(-3.0, 3.001, 0.3), 2)) + [np.inf]
        labels = ['< -3.0%'] + [f"{edges[i]:.1f}% to {edges[i+1]:.1f}%" for i in range(1, len(edges)-2)] + ['> 3.0%']

        cats = pd.cut(series, bins=edges, right=False)
        counts = cats.value_counts(sort=False).reindex(cats.cat.categories, fill_value=0)
        counts = counts.astype(int)
        df = pd.DataFrame({"Interval": labels, "Frequency": counts.values})
        total = df["Frequency"].sum()
        df["Probability"] = df["Frequency"] / total if total > 0 else 0.0
        df["Cumulative Probability"] = df["Probability"].cumsum()
        return df

    @staticmethod
    def _calc_hl_freq(series: pd.Series) -> pd.DataFrame:
        if series.empty:
            return pd.DataFrame()
        edges = [-np.inf] + list(np.round(np.arange(0.15, 3.151, 0.15), 2)) + [np.inf]
        labels = ['< 0.15%'] + [f"{edges[i]:.2f}% to {edges[i+1]:.2f}%" for i in range(1, len(edges)-2)] + ['> 3.15%']

        cats = pd.cut(series, bins=edges, right=False)
        counts = cats.value_counts(sort=False).reindex(cats.cat.categories, fill_value=0)
        counts = counts.astype(int)
        df = pd.DataFrame({"Interval": labels, "Frequency": counts.values})
        total = df["Frequency"].sum()
        df["Probability"] = df["Frequency"] / total if total > 0 else 0.0
        return df

    @staticmethod
    def _calc_atr_timeframes(series: pd.Series) -> dict:
        """Calculate the Wilder ATR for specific trading timeframes (excluding today).

        Uses J. Welles Wilder's original smoothing method (identical to TradingView
        and MetaTrader):
          - First ATR  = SMA(TR, n)  over the first n periods
          - Subsequent = ((prev_ATR × (n − 1)) + TR_current) / n

        The *series* passed in is ``dailyatr_pct`` which already encodes
        ``(TR / prev_close) × 100``, so the Wilder-smoothed result is returned
        in the same percentage unit.

        Timeframes (n periods):
        - 1 WEEK    =   5 trading days
        - 1 MONTH   =  21 trading days
        - 3 MONTHS  =  63 trading days
        - 1 YEAR    = 252 trading days
        - 2 YEARS   = 504 trading days

        Returns dict with timeframe labels as keys and Wilder-ATR values as values.
        """
        if len(series) < 2:
            return {}

        # Exclude today's incomplete candle (last row)
        hist = series.iloc[:-1].dropna().reset_index(drop=True)

        timeframes = {
            "1 WEEK":    5,
            "1 MONTH":  21,
            "3 MONTHS": 63,
            "1 YEAR":  252,
            "2 YEARS": 504,
        }

        result = {}
        for name, n in timeframes.items():
            if len(hist) < n:
                result[name] = float('nan')
                continue

            # ── Wilder smoothing over the full available history ────────────
            # Seed: simple average of the first n values
            atr = hist.iloc[:n].mean()

            # Apply Wilder's EMA-like smoothing for all subsequent bars
            for tr_val in hist.iloc[n:]:
                atr = (atr * (n - 1) + tr_val) / n

            result[name] = atr

        return result

    @staticmethod
    def get_conversion_rate(from_currency: str, to_currency: str = "USD") -> Optional[float]:
        """Get the latest conversion rate from one currency to another.

        Args:
            from_currency: Currency to convert from (e.g., "CAD", "EUR")
            to_currency: Currency to convert to (default "USD")

        Returns:
            Conversion rate or None if not available
        """
        if from_currency == to_currency:
            return 1.0

        # Try direct pair first
        ticker1 = f"{from_currency}{to_currency}=X"
        try:
            data = yf.download(ticker1, period="1d", interval="1d", progress=False)
            if not data.empty and "Close" in data.columns:
                return float(data["Close"].iloc[-1])
        except Exception:
            pass

        # Try reversed pair
        ticker2 = f"{to_currency}{from_currency}=X"
        try:
            data = yf.download(ticker2, period="1d", interval="1d", progress=False)
            if not data.empty and "Close" in data.columns:
                rate = float(data["Close"].iloc[-1])
                if rate > 0:
                    return 1.0 / rate
        except Exception:
            pass

        return None

    @staticmethod
    def get_current_price(ticker: str) -> Optional[float]:
        """Fetch the latest live price for the given ticker using yfinance.

        Args:
            ticker: The instrument symbol (e.g., "USDJPY=X").
            
        Returns:
            The latest close price, or None if unavailable.
        """
        try:
            # fast_info is typically faster for grabbing current price without downloading a df
            ticker_obj = yf.Ticker(ticker)
            price = ticker_obj.fast_info.get('lastPrice')
            
            if price is not None and not np.isnan(price):
                return float(price)
            
            # Fallback to download if fast_info fails
            data = yf.download(ticker, period="1d", interval="1m", progress=False)
            if not data.empty and "Close" in data.columns:
                return float(data["Close"].iloc[-1])
        except Exception:
            pass
        
        return None
