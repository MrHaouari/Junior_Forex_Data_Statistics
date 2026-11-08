"""
app.py — Main application window for Forex Data Statistics.
"""

from __future__ import annotations

import threading

import customtkinter as ctk

from data_manager import DataManager
from table_view import TableView
from stats_view import StatsView
from atr_timeframes_view import ATRTimeframesView
from candlestick_view import CandlestickView
from atr_stop_loss_v2_view import ATRStopLossV2View
from lot_size_calculator_view import LotSizeCalculatorView
from profit_loss_view import ProfitLossView
from freq_views import OOFreqView, HLFreqView
from resume_view import ResumeView

# ---------------------------------------------------------------------------
# Theme constants
# ---------------------------------------------------------------------------
WINDOW_BG = "#0b0e1a"
ACCENT = "#7f5af0"
ACCENT_HOVER = "#6b46d6"
STATUS_FG = "#a0a0c0"
TITLE_FG = "#e0e0ff"


class ForexApp(ctk.CTk):
    """Root window for the Forex Data Statistics desktop app."""

    def __init__(self) -> None:
        super().__init__()

        # Window setup -------------------------------------------------------
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Forex Data Statistics")
        self.geometry("1200x800")
        self.minsize(900, 600)
        self.configure(fg_color=WINDOW_BG)

        self._data_mgr = DataManager()
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ── Top bar ───────────────────────────────────────────────────
        top_bar = ctk.CTkFrame(self, fg_color="#12152a", corner_radius=0, height=60)
        top_bar.pack(fill="x", padx=0, pady=0)
        top_bar.pack_propagate(False)

        title_lbl = ctk.CTkLabel(
            top_bar,
            text="📊  Forex Data Statistics",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TITLE_FG,
        )
        title_lbl.pack(side="left", padx=20)

        # Fetch button
        self._fetch_btn = ctk.CTkButton(
            top_bar,
            text="Fetch Data",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            corner_radius=8,
            width=120,
            command=self._on_fetch,
        )
        self._fetch_btn.pack(side="right", padx=20, pady=12)

        # Timeframe selector
        self._timeframe_var = ctk.StringVar(value="1d")
        self._timeframe_combo = ctk.CTkComboBox(
            top_bar,
            values=DataManager.TIMEFRAMES,
            variable=self._timeframe_var,
            font=ctk.CTkFont(size=14),
            dropdown_font=ctk.CTkFont(size=13),
            width=100,
            fg_color="#1a1a2e",
            border_color="#2a2a4a",
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color="#1a1a2e",
            dropdown_hover_color="#2a2a4a",
            corner_radius=8,
            state="readonly",
            command=lambda _: self.update_dashboard(),
        )
        self._timeframe_combo.pack(side="right", padx=(0, 10), pady=12)

        timeframe_label = ctk.CTkLabel(
            top_bar,
            text="Timeframe:",
            font=ctk.CTkFont(size=14),
            text_color=STATUS_FG,
        )
        timeframe_label.pack(side="right", padx=(0, 4), pady=12)

        # Pair selector
        self._pair_var = ctk.StringVar(value=DataManager.PAIRS[0])
        self._pair_combo = ctk.CTkComboBox(
            top_bar,
            values=DataManager.PAIRS,
            variable=self._pair_var,
            font=ctk.CTkFont(size=14),
            dropdown_font=ctk.CTkFont(size=13),
            width=180,
            fg_color="#1a1a2e",
            border_color="#2a2a4a",
            button_color=ACCENT,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color="#1a1a2e",
            dropdown_hover_color="#2a2a4a",
            corner_radius=8,
            state="readonly",
            command=lambda _: self.update_dashboard(),
        )
        self._pair_combo.pack(side="right", padx=(0, 10), pady=12)

        pair_label = ctk.CTkLabel(
            top_bar,
            text="Pair:",
            font=ctk.CTkFont(size=14),
            text_color=STATUS_FG,
        )
        pair_label.pack(side="right", padx=(0, 4), pady=12)

        # ── Status bar ────────────────────────────────────────────────
        status_bar = ctk.CTkFrame(self, fg_color="#10132a", corner_radius=0, height=30)
        status_bar.pack(fill="x", side="bottom", padx=0, pady=0)
        status_bar.pack_propagate(False)

        self._status_lbl = ctk.CTkLabel(
            status_bar,
            text="Ready — select a pair and click Fetch Data",
            font=ctk.CTkFont(size=12),
            text_color=STATUS_FG,
            anchor="w",
        )
        self._status_lbl.pack(side="left", padx=16, pady=4)

        self._row_count_lbl = ctk.CTkLabel(
            status_bar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=STATUS_FG,
            anchor="e",
        )
        self._row_count_lbl.pack(side="right", padx=16, pady=4)

        # ── Tabs ──────────────────────────────────────────────────────
        self._tabview = ctk.CTkTabview(
            self,
            fg_color="#12152a",
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color=ACCENT_HOVER
        )
        self._tabview.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        self._tab_data = self._tabview.add("Data Table")
        self._tab_stats = self._tabview.add("Summary Statistics")
        self._tab_atr_timeframes = self._tabview.add("ATR Timeframes")
        self._tab_chart = self._tabview.add("Price Chart")
        self._tab_stop_loss_v2 = self._tabview.add("ATR Stop Loss V2")
        self._tab_lot_size = self._tabview.add("Lot Size Calculator")
        self._tab_oo_freq = self._tabview.add("O-O Distribution")
        self._tab_hl_freq = self._tabview.add("H-L Distribution")
        self._tab_resume = self._tabview.add("Statistic Resume")
        self._tab_profit_loss = self._tabview.add("P/L Target Calculator")

        # ── Table ─────────────────────────────────────────────────────
        self._table = TableView(self._tab_data)
        self._table.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Stats ─────────────────────────────────────────────────────
        self._stats_view = StatsView(self._tab_stats)
        self._stats_view.pack(fill="both", expand=True, padx=0, pady=0)

        # ── ATR Timeframes ─────────────────────────────────────────────
        self._atr_timeframes_view = ATRTimeframesView(self._tab_atr_timeframes)
        self._atr_timeframes_view.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Candlestick Chart ──────────────────────────────────────────
        self._candlestick_view = CandlestickView(self._tab_chart)
        self._candlestick_view.pack(fill="both", expand=True, padx=0, pady=0)

        # ── ATR Stop Loss Calculator V2 ─────────────────────────────────
        self._stop_loss_v2_view = ATRStopLossV2View(self._tab_stop_loss_v2)
        self._stop_loss_v2_view.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Lot Size Calculator ───────────────────────────────────────────
        self._lot_size_view = LotSizeCalculatorView(self._tab_lot_size)
        self._lot_size_view.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Profit/Loss Target Calculator ───────────────────────────────
        self._profit_loss_view = ProfitLossView(self._tab_profit_loss)
        self._profit_loss_view.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Frequency Views ───────────────────────────────────────────
        self._oo_freq_view = OOFreqView(self._tab_oo_freq)
        self._oo_freq_view.pack(fill="both", expand=True, padx=0, pady=0)

        self._hl_freq_view = HLFreqView(self._tab_hl_freq)
        self._hl_freq_view.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Resume View ───────────────────────────────────────────────
        self._resume_view = ResumeView(self._tab_resume)
        self._resume_view.pack(fill="both", expand=True, padx=0, pady=0)

    # ------------------------------------------------------------------
    # Data fetching (threaded)
    # ------------------------------------------------------------------

    def _on_fetch(self) -> None:
        """Start a background thread to download data for current pair and timeframe."""
        self.update_dashboard()

    def update_dashboard(self) -> None:
        """Unified function to update the entire dashboard with current pair and timeframe."""
        ticker = self._pair_var.get()
        timeframe = self._timeframe_var.get()
        self._set_status(f"Downloading {ticker} ({timeframe}) …")
        self._fetch_btn.configure(state="disabled")
        threading.Thread(target=self._fetch_worker, args=(ticker, timeframe), daemon=True).start()

    def _fetch_worker(self, ticker: str, timeframe: str) -> None:
        """Run in background thread — downloads data then schedules UI update."""
        try:
            df, stats, oo_freq, hl_freq, oo_cond, oo_bands, resume_df, atr_timeframes, ohlc_raw = DataManager.fetch(ticker, timeframe)
            self.after(0, self._on_fetch_done, ticker, timeframe, df, stats, oo_freq, hl_freq, oo_cond, oo_bands, resume_df, atr_timeframes, ohlc_raw, None)
        except Exception as exc:  # noqa: BLE001
            self.after(0, self._on_fetch_done, ticker, timeframe, None, None, None, None, None, None, None, None, None, exc)

    def _on_fetch_done(self, ticker: str, timeframe: str, df, stats, oo_freq, hl_freq, oo_cond, oo_bands, resume_df, atr_timeframes, ohlc_raw, error) -> None:
        """Called on the main thread after the download completes."""
        self._fetch_btn.configure(state="normal")

        if error is not None:
            self._set_status(f"Error fetching {ticker}: {error}")
            return

        if df is None or df.empty:
            self._set_status(f"No data returned for {ticker} ({timeframe})")
            return

        self._table.load_dataframe(df)
        if stats:
            self._stats_view.load_stats(stats)

        if atr_timeframes:
            self._atr_timeframes_view.load_data(atr_timeframes)

        if ohlc_raw is not None and not ohlc_raw.empty:
            self._candlestick_view.load_data(ohlc_raw)
            # Get latest close price (last complete candle)
            latest_close = float(ohlc_raw.iloc[-2]["Close"]) if len(ohlc_raw) > 1 else float(ohlc_raw.iloc[-1]["Close"])
            self._resume_view.load_data(resume_df)

        if oo_freq is not None:
            self._oo_freq_view.load_data(oo_freq, oo_cond, oo_bands)
        if hl_freq is not None:
            self._hl_freq_view.load_data(hl_freq)

        self._set_status(f"Loaded {ticker} ({timeframe}) — {len(df)} rows")
        self._row_count_lbl.configure(text=f"{len(df):,} rows")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_status(self, msg: str) -> None:
        self._status_lbl.configure(text=msg)
