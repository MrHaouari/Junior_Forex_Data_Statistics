"""
atr_timeframes_view.py — Time-based average Daily ATR table display.
"""

import customtkinter as ctk

# Theme constants
HEADER_BG = "#1a1a2e"
HEADER_FG = "#e0e0ff"
ROW_EVEN_BG = "#16213e"
ROW_ODD_BG = "#0f3460"
ROW_FG = "#d4d4dc"
FONT_FAMILY = "SF Mono"


class ATRTimeframesView(ctk.CTkFrame):
    """Displays time-based rolling averages for Daily ATR."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Main container frame
        main_frame = ctk.CTkFrame(self, fg_color="#0b0e1a", border_width=1, border_color="#2a2a4a", corner_radius=8)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_lbl = ctk.CTkLabel(
            main_frame,
            text="Daily ATR — Trading Timeframe Averages (Excl. Today)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=HEADER_FG
        )
        title_lbl.pack(pady=(15, 10))

        # Table frame
        self._table_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self._table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self._table_frame.columnconfigure(0, weight=1, uniform="col")
        self._table_frame.columnconfigure(1, weight=1, uniform="col")

    def load_data(self, timeframes_data: dict) -> None:
        """Populate the table with trailing average data.

        Args:
            timeframes_data: Dictionary with keys like "1 WEEK", "1 MONTH", etc.
        """
        # Clear previous table entries
        for w in self._table_frame.winfo_children():
            w.destroy()

        # Define column headers
        self._table_frame.columnconfigure(0, weight=1, uniform="col")
        self._table_frame.columnconfigure(1, weight=1, uniform="col")

        # Header row
        header_bg = HEADER_BG
        header_labels = ["Timeframe", "Average Daily ATR"]

        for col_idx, header_text in enumerate(header_labels):
            header_lbl = ctk.CTkLabel(
                self._table_frame,
                text=header_text,
                font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                fg_color=header_bg,
                text_color=HEADER_FG,
                anchor="center"
            )
            header_lbl.grid(row=0, column=col_idx, sticky="nsew", padx=0, pady=1, ipady=6, ipadx=10)

        # Data rows (maintain order: 1 WEEK, 1 MONTH, 3 MONTHS, 1 YEAR, 2 YEARS)
        row_order = ["1 WEEK", "1 MONTH", "3 MONTHS", "1 YEAR", "2 YEARS"]

        for row_idx, timeframe in enumerate(row_order, start=1):
            bg = ROW_EVEN_BG if row_idx % 2 == 0 else ROW_ODD_BG

            value = timeframes_data.get(timeframe, float('nan'))
            if isinstance(value, float):
                v_str = f"{value:.5f}%" if not pd.isna(value) else "N/A"
            else:
                v_str = str(value)

            # Timeframe label
            tf_lbl = ctk.CTkLabel(
                self._table_frame,
                text=timeframe,
                font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                fg_color=bg,
                text_color=ROW_FG,
                anchor="w"
            )
            tf_lbl.grid(row=row_idx, column=0, sticky="nsew", padx=0, pady=1, ipady=6, ipadx=10)

            # Value label
            val_lbl = ctk.CTkLabel(
                self._table_frame,
                text=v_str,
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                fg_color=bg,
                text_color=ROW_FG,
                anchor="e"
            )
            val_lbl.grid(row=row_idx, column=1, sticky="nsew", padx=0, pady=1, ipady=6, ipadx=10)


# Import pandas after class definition to avoid circular imports
import pandas as pd
