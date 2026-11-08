"""
atr_stop_loss_v2_view.py — ATR Stop Loss Calculator V2
"""

import customtkinter as ctk

# Theme colors
THEME_BG = "#0b0e1a"
HEADER_BG = "#1a1a2e"
INPUT_BG = "#16213e"
TEXT_COLOR = "#e0e0ff"
LABEL_COLOR = "#a0a0c0"
ACCENT_COLOR = "#7f5af0"
ACCENT_HOVER = "#6b46d6"
BORDER_COLOR = "#2a2a4a"
SUCCESS_COLOR = "#00d084"
ALERT_COLOR = "#ff3d71"


class ATRStopLossV2View(ctk.CTkFrame):
    """Interactive ATR-based Stop Loss calculator V2."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=THEME_BG, border_width=1, border_color=BORDER_COLOR, corner_radius=8)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title_lbl = ctk.CTkLabel(
            main_frame,
            text="ATR Stop Loss Calculator V2",
            font=ctk.CTkFont(family="SF Mono", size=14, weight="bold"),
            text_color=TEXT_COLOR
        )
        title_lbl.pack(fill="x", padx=15, pady=(15, 20))

        # Create scrollable frame for inputs
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # ─── INPUT SECTION ──────────────────────────────────────────────
        input_section = ctk.CTkFrame(scroll_frame, fg_color=INPUT_BG, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
        input_section.pack(fill="x", pady=(0, 20))

        section_title = ctk.CTkLabel(
            input_section,
            text="Configuration",
            font=ctk.CTkFont(family="SF Mono", size=12, weight="bold"),
            text_color=TEXT_COLOR
        )
        section_title.pack(padx=15, pady=(12, 12), anchor="w")

        # Grid for inputs
        grid_frame = ctk.CTkFrame(input_section, fg_color="transparent")
        grid_frame.pack(fill="x", padx=15, pady=15)
        grid_frame.grid_columnconfigure(1, weight=1)

        # Trade Direction
        direction_label = ctk.CTkLabel(
            grid_frame,
            text="Trade Direction:",
            font=ctk.CTkFont(family="SF Mono", size=11),
            text_color=LABEL_COLOR
        )
        direction_label.grid(row=0, column=0, sticky="w", padx=(0, 15), pady=10)

        self._direction_var = ctk.StringVar(value="Buy")
        self._direction_combo = ctk.CTkComboBox(
            grid_frame,
            values=["Buy", "Sell"],
            variable=self._direction_var,
            font=ctk.CTkFont(family="SF Mono", size=10),
            dropdown_font=ctk.CTkFont(family="SF Mono", size=9),
            width=150,
            fg_color=HEADER_BG,
            border_color=BORDER_COLOR,
            button_color=ACCENT_COLOR,
            button_hover_color=ACCENT_HOVER,
            dropdown_fg_color=HEADER_BG,
            dropdown_hover_color=INPUT_BG,
            corner_radius=6,
            state="readonly",
            command=self._on_input_changed
        )
        self._direction_combo.grid(row=0, column=1, sticky="w", pady=10)

        # Entry Price
        entry_price_label = ctk.CTkLabel(
            grid_frame,
            text="Entry Price:",
            font=ctk.CTkFont(family="SF Mono", size=11),
            text_color=LABEL_COLOR
        )
        entry_price_label.grid(row=1, column=0, sticky="w", padx=(0, 15), pady=10)

        self._entry_price_var = ctk.StringVar(value="")
        self._entry_price_entry = ctk.CTkEntry(
            grid_frame,
            textvariable=self._entry_price_var,
            font=ctk.CTkFont(family="SF Mono", size=10),
            width=150,
            fg_color=HEADER_BG,
            border_color=BORDER_COLOR,
            text_color=TEXT_COLOR,
            placeholder_text="e.g., 1.10500",
            corner_radius=6
        )
        self._entry_price_entry.grid(row=1, column=1, sticky="w", pady=10)
        self._entry_price_var.trace_add("write", lambda *args: self._on_input_changed())

        # ATR Value
        atr_value_label = ctk.CTkLabel(
            grid_frame,
            text="ATR Value:",
            font=ctk.CTkFont(family="SF Mono", size=11),
            text_color=LABEL_COLOR
        )
        atr_value_label.grid(row=2, column=0, sticky="w", padx=(0, 15), pady=10)

        self._atr_value_var = ctk.StringVar(value="")
        self._atr_value_entry = ctk.CTkEntry(
            grid_frame,
            textvariable=self._atr_value_var,
            font=ctk.CTkFont(family="SF Mono", size=10),
            width=150,
            fg_color=HEADER_BG,
            border_color=BORDER_COLOR,
            text_color=TEXT_COLOR,
            placeholder_text="e.g., 0.00200",
            corner_radius=6
        )
        self._atr_value_entry.grid(row=2, column=1, sticky="w", pady=10)
        self._atr_value_var.trace_add("write", lambda *args: self._on_input_changed())

        # ATR Multiple
        atr_multiple_label = ctk.CTkLabel(
            grid_frame,
            text="ATR Multiple:",
            font=ctk.CTkFont(family="SF Mono", size=11),
            text_color=LABEL_COLOR
        )
        atr_multiple_label.grid(row=3, column=0, sticky="w", padx=(0, 15), pady=10)

        self._atr_multiple_var = ctk.StringVar(value="2.0")
        self._atr_multiple_entry = ctk.CTkEntry(
            grid_frame,
            textvariable=self._atr_multiple_var,
            font=ctk.CTkFont(family="SF Mono", size=10),
            width=150,
            fg_color=HEADER_BG,
            border_color=BORDER_COLOR,
            text_color=TEXT_COLOR,
            placeholder_text="e.g., 2.0",
            corner_radius=6
        )
        self._atr_multiple_entry.grid(row=3, column=1, sticky="w", pady=10)
        self._atr_multiple_var.trace_add("write", lambda *args: self._on_input_changed())

        # ─── RESULTS SECTION ───────────────────────────────────────────
        results_section = ctk.CTkFrame(scroll_frame, fg_color=INPUT_BG, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
        results_section.pack(fill="x", pady=20)

        results_title = ctk.CTkLabel(
            results_section,
            text="Result",
            font=ctk.CTkFont(family="SF Mono", size=12, weight="bold"),
            text_color=TEXT_COLOR
        )
        results_title.pack(padx=15, pady=(12, 15), anchor="w")

        # Results grid
        results_grid = ctk.CTkFrame(results_section, fg_color="transparent")
        results_grid.pack(fill="x", padx=15, pady=15)
        results_grid.grid_columnconfigure(1, weight=1)

        # Stop Loss Price
        stop_loss_label = ctk.CTkLabel(
            results_grid,
            text="Stop Loss Price:",
            font=ctk.CTkFont(family="SF Mono", size=11, weight="bold"),
            text_color=SUCCESS_COLOR
        )
        stop_loss_label.grid(row=0, column=0, sticky="w", padx=(0, 15), pady=10)

        self._stop_loss_display = ctk.CTkLabel(
            results_grid,
            text="--",
            font=ctk.CTkFont(family="SF Mono", size=14, weight="bold"),
            text_color=SUCCESS_COLOR
        )
        self._stop_loss_display.grid(row=0, column=1, sticky="w", pady=10)

        # ─── INFO SECTION ──────────────────────────────────────────────
        info_section = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        info_section.pack(fill="x", pady=20)

        info_title = ctk.CTkLabel(
            info_section,
            text="Formula Reference",
            font=ctk.CTkFont(family="SF Mono", size=11, weight="bold"),
            text_color=LABEL_COLOR
        )
        info_title.pack(anchor="w", pady=(0, 8))

        buy_formula = ctk.CTkLabel(
            info_section,
            text="Buy:  Stop Loss = Entry Price − (ATR × Multiple)",
            font=ctk.CTkFont(family="SF Mono", size=10),
            text_color="#888888"
        )
        buy_formula.pack(anchor="w", pady=4)

        sell_formula = ctk.CTkLabel(
            info_section,
            text="Sell: Stop Loss = Entry Price + (ATR × Multiple)",
            font=ctk.CTkFont(family="SF Mono", size=10),
            text_color="#888888"
        )
        sell_formula.pack(anchor="w", pady=4)

    def _on_input_changed(self, *args) -> None:
        """Calculate stop loss instantly on any input change."""
        try:
            entry_str = self._entry_price_var.get().strip()
            atr_str = self._atr_value_var.get().strip()
            multiple_str = self._atr_multiple_var.get().strip()

            if not entry_str or not atr_str or not multiple_str:
                self._stop_loss_display.configure(text="--")
                return

            entry_price = float(entry_str)
            atr_value = float(atr_str)
            multiple = float(multiple_str)

            if entry_price < 0 or atr_value < 0 or multiple < 0:
                self._stop_loss_display.configure(text="--")
                return

            direction = self._direction_var.get()

            if direction == "Buy":
                sl_price = entry_price - (atr_value * multiple)
            else:
                sl_price = entry_price + (atr_value * multiple)

            # Prevent negative SL if buy drops below 0
            if sl_price < 0:
                self._stop_loss_display.configure(text="--")
                return

            self._stop_loss_display.configure(text=f"{sl_price:.5f}")

        except ValueError:
            self._stop_loss_display.configure(text="--")
