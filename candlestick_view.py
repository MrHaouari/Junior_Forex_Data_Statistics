"""
candlestick_view.py — Professional candlestick chart using mplfinance with CustomTkinter.
"""

import customtkinter as ctk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Theme colors
THEME_BG = "#0b0e1a"
THEME_GRID = "#1a1a2e"
TEXT_COLOR = "#e0e0ff"
ACCENT_COLOR = "#7f5af0"
ACCENT_HOVER = "#6b46d6"
COLOR_BULLISH = "#00d084"  # Green for bullish
COLOR_BEARISH = "#ff3d71"  # Red for bearish


class CandlestickView(ctk.CTkFrame):
    """Displays professional candlestick chart with volume and moving averages."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="#0b0e1a", border_width=1, border_color="#2a2a4a", corner_radius=8)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header with title and controls
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="Price Action — Professional Chart (OHLC + MA20/50/200)",
            font=ctk.CTkFont(family="SF Mono", size=14, weight="bold"),
            text_color=TEXT_COLOR
        )
        title_lbl.pack(side="left", padx=0)

        # Time range selector
        range_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        range_frame.pack(side="right", padx=0)

        range_label = ctk.CTkLabel(
            range_frame,
            text="View:",
            font=ctk.CTkFont(family="SF Mono", size=11),
            text_color="#a0a0c0"
        )
        range_label.pack(side="left", padx=(0, 8))

        self._range_var = ctk.StringVar(value="100")
        self._range_combo = ctk.CTkComboBox(
            range_frame,
            values=["30", "50", "100", "250", "500", "All"],
            variable=self._range_var,
            font=ctk.CTkFont(family="SF Mono", size=10),
            dropdown_font=ctk.CTkFont(family="SF Mono", size=9),
            width=70,
            fg_color="#1a1a2e",
            border_color="#2a2a4a",
            button_color=ACCENT_COLOR,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color="#1a1a2e",
            dropdown_hover_color="#2a2a4a",
            corner_radius=6,
            state="readonly",
            command=self._on_range_changed
        )
        self._range_combo.pack(side="left", padx=0)

        range_unit = ctk.CTkLabel(
            range_frame,
            text="days",
            font=ctk.CTkFont(family="SF Mono", size=10),
            text_color="#a0a0c0"
        )
        range_unit.pack(side="left", padx=(4, 0))

        # Canvas frame for matplotlib
        self._canvas_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self._canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self._figure = None
        self._canvas = None
        self._ohlc_data = None  # Store full data

    def load_data(self, ohlc_df: pd.DataFrame) -> None:
        """Load OHLC data and render professional chart.

        Args:
            ohlc_df: DataFrame with 'Open', 'High', 'Low', 'Close' columns
        """
        if ohlc_df is None or ohlc_df.empty:
            return

        # Store full data (excluding today's incomplete candle)
        self._ohlc_data = ohlc_df.iloc[:-1].copy()

        if self._ohlc_data.empty:
            return

        # Render chart with current range selection
        self._render_chart()

    def _on_range_changed(self, selection: str) -> None:
        """Handle range dropdown selection change."""
        if self._ohlc_data is not None:
            self._render_chart()

    def _render_chart(self) -> None:
        """Render professional candlestick chart with moving averages."""
        if self._ohlc_data is None or self._ohlc_data.empty:
            return

        # Get selected range
        range_str = self._range_var.get()
        if range_str == "All":
            df = self._ohlc_data.copy()
        else:
            days = int(range_str)
            df = self._ohlc_data.tail(days).copy()

        if df.empty:
            return

        # Calculate moving averages
        df["MA20"] = df["Close"].rolling(window=20, min_periods=1).mean()
        df["MA50"] = df["Close"].rolling(window=50, min_periods=1).mean()
        df["MA200"] = df["Close"].rolling(window=200, min_periods=1).mean()

        # Clear previous canvas
        if self._canvas is not None:
            self._canvas.get_tk_widget().destroy()

        # Create figure with single subplot for candlesticks
        self._figure = Figure(figsize=(16, 9), dpi=80, facecolor=THEME_BG, edgecolor="none")

        ax_candles = self._figure.add_subplot(1, 1, 1)

        # Plot candlesticks and moving averages
        self._plot_candlesticks(ax_candles, df)
        self._plot_moving_averages(ax_candles, df)

        # Style axes
        ax_candles.set_facecolor(THEME_BG)
        ax_candles.grid(True, color=THEME_GRID, alpha=0.3, linestyle="--", linewidth=0.5)
        ax_candles.tick_params(colors=TEXT_COLOR, labelsize=9)
        ax_candles.spines["bottom"].set_color(THEME_GRID)
        ax_candles.spines["left"].set_color(THEME_GRID)
        ax_candles.spines["top"].set_visible(False)
        ax_candles.spines["right"].set_visible(False)

        # Labels
        ax_candles.set_ylabel("Price", color=TEXT_COLOR, fontsize=10)
        ax_candles.set_xlabel("Date", color=TEXT_COLOR, fontsize=10)

        # Legend
        ax_candles.legend(
            ["MA20 (Orange)", "MA50 (Blue)", "MA200 (Purple)"],
            loc="upper left",
            fontsize=8,
            labelcolor=TEXT_COLOR,
            facecolor=THEME_BG,
            edgecolor=THEME_GRID
        )

        # Date labels
        self._set_date_labels(ax_candles, df)
        self._figure.tight_layout()

        # Embed canvas
        self._canvas = FigureCanvasTkAgg(self._figure, master=self._canvas_frame)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

    def _plot_candlesticks(self, ax, df: pd.DataFrame) -> None:
        """Draw candlesticks with professional styling."""
        for i, (idx, row) in enumerate(df.iterrows()):
            open_price = float(row["Open"])
            high_price = float(row["High"])
            low_price = float(row["Low"])
            close_price = float(row["Close"])

            # Color based on direction
            color = COLOR_BULLISH if close_price >= open_price else COLOR_BEARISH

            # Wick (high-low line)
            ax.plot([i, i], [low_price, high_price], color=color, linewidth=1.2, alpha=0.9)

            # Body (open-close rectangle)
            body_top = max(open_price, close_price)
            body_bottom = min(open_price, close_price)
            body_height = body_top - body_bottom if body_top != body_bottom else 0.0001

            rect = patches.Rectangle(
                (i - 0.35, body_bottom),
                0.7,
                body_height,
                linewidth=0.8,
                edgecolor=color,
                facecolor=color,
                alpha=0.9
            )
            ax.add_patch(rect)

        # Axis limits with padding
        ax.set_xlim(-1, len(df))
        all_prices = df[["Open", "High", "Low", "Close"]].astype(float)
        price_min = all_prices.min().min()
        price_max = all_prices.max().max()
        price_range = price_max - price_min
        padding = price_range * 0.1
        ax.set_ylim(price_min - padding, price_max + padding)

    def _plot_moving_averages(self, ax, df: pd.DataFrame) -> None:
        """Draw moving averages on the chart."""
        x = range(len(df))
        ax.plot(x, df["MA20"], color="#ff9800", linewidth=1.8, alpha=0.8, label="MA20")
        ax.plot(x, df["MA50"], color="#2196f3", linewidth=1.8, alpha=0.8, label="MA50")
        ax.plot(x, df["MA200"], color="#9c27b0", linewidth=1.8, alpha=0.8, label="MA200")

    def _set_date_labels(self, ax, df: pd.DataFrame) -> None:
        """Format x-axis date labels."""
        step = max(1, len(df) // 10)
        x_ticks = list(range(0, len(df), step))

        date_labels = []
        for idx in x_ticks:
            date = df.index[idx]
            if hasattr(date, "strftime"):
                date_labels.append(date.strftime("%Y-%m-%d"))
            else:
                date_labels.append(str(date)[:10])

        ax.set_xticks(x_ticks)
        ax.set_xticklabels(date_labels, rotation=45, ha="right", fontsize=9, color=TEXT_COLOR)
