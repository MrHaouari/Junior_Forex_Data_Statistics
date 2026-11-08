"""
lot_size_calculator_view.py — Professional Lot Size Calculator (Fully Generic)
"""

import threading
import customtkinter as ctk

from data_manager import DataManager

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


class LotSizeCalculatorView(ctk.CTkFrame):
    """Professional Lot Size Calculator interface (Fully Generic for any pair)."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Load all pairs from specs
        self.all_pairs = list(DataManager.INSTRUMENT_SPECS.keys())
        if not self.all_pairs:
            self.all_pairs = ["EURUSD=X"] # Fallback

        self._build_ui()

    def _build_ui(self):
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=THEME_BG, border_width=1, border_color=BORDER_COLOR, corner_radius=8)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title & Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=15, pady=(15, 10))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="Lot Size Calculator",
            font=ctk.CTkFont(family="SF Mono", size=16, weight="bold"),
            text_color=TEXT_COLOR
        )
        title_lbl.pack(side="left")
        
        self.status_lbl = ctk.CTkLabel(
            header_frame,
            text="Ready",
            font=ctk.CTkFont(family="SF Mono", size=12),
            text_color=LABEL_COLOR
        )
        self.status_lbl.pack(side="right")

        # Scrollable area
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=5)

        # ─── INPUT SECTION ──────────────────────────────────────────────
        input_section = ctk.CTkFrame(scroll_frame, fg_color=INPUT_BG, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
        input_section.pack(fill="x", pady=(0, 20))

        section_title = ctk.CTkLabel(
            input_section,
            text="Trade Parameters",
            font=ctk.CTkFont(family="SF Mono", size=14, weight="bold"),
            text_color=TEXT_COLOR
        )
        section_title.pack(padx=15, pady=(15, 10), anchor="w")

        input_grid = ctk.CTkFrame(input_section, fg_color="transparent")
        input_grid.pack(fill="x", padx=15, pady=(0, 15))
        input_grid.grid_columnconfigure(1, weight=1)
        input_grid.grid_columnconfigure(3, weight=1)

        # Row 0: Instrument & Trade Direction
        self._add_label(input_grid, "Instrument:", 0, 0)
        self._instrument_var = ctk.StringVar(value=self.all_pairs[0])
        self._instrument_combo = ctk.CTkComboBox(
            input_grid, values=self.all_pairs, variable=self._instrument_var, **self._input_kwargs()
        )
        self._instrument_combo.grid(row=0, column=1, sticky="w", pady=10, padx=(0, 20))
        # Update dynamic labels when instrument changes
        self._instrument_var.trace_add("write", lambda *args: self._update_dynamic_labels())

        self._add_label(input_grid, "Trade Direction:", 0, 2)
        self._direction_var = ctk.StringVar(value="Buy")
        self._direction_combo = ctk.CTkComboBox(
            input_grid, values=["Buy", "Sell"], variable=self._direction_var, **self._input_kwargs()
        )
        self._direction_combo.grid(row=0, column=3, sticky="w", pady=10)

        # Row 1: Account Currency & Account Balance
        self._add_label(input_grid, "Account Currency:", 1, 0)
        self._add_label(input_grid, "USD", 1, 1, color=TEXT_COLOR)

        self._add_label(input_grid, "Account Balance:", 1, 2)
        self._balance_var = ctk.StringVar(value="10000")
        self._balance_entry = ctk.CTkEntry(input_grid, textvariable=self._balance_var, **self._entry_kwargs())
        self._balance_entry.grid(row=1, column=3, sticky="w", pady=10)

        # Row 2: Risk % & Entry Price
        self._add_label(input_grid, "Risk (%):", 2, 0)
        self._risk_var = ctk.StringVar(value="1.0")
        self._risk_entry = ctk.CTkEntry(input_grid, textvariable=self._risk_var, **self._entry_kwargs())
        self._risk_entry.grid(row=2, column=1, sticky="w", pady=10, padx=(0, 20))

        self._add_label(input_grid, "Entry Price:", 2, 2)
        self._entry_var = ctk.StringVar(value="")
        self._entry_entry = ctk.CTkEntry(input_grid, textvariable=self._entry_var, placeholder_text="e.g. 1.10500", **self._entry_kwargs())
        self._entry_entry.grid(row=2, column=3, sticky="w", pady=10)

        # Row 3: Stop Loss Price
        self._add_label(input_grid, "Stop Loss Price:", 3, 0)
        self._sl_var = ctk.StringVar(value="")
        self._sl_entry = ctk.CTkEntry(input_grid, textvariable=self._sl_var, placeholder_text="e.g. 1.10000", **self._entry_kwargs())
        self._sl_entry.grid(row=3, column=1, sticky="w", pady=10, padx=(0, 20))

        # Calculate Button
        btn_frame = ctk.CTkFrame(input_section, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self._calc_btn = ctk.CTkButton(
            btn_frame,
            text="Calculate Lot Size",
            font=ctk.CTkFont(family="SF Mono", size=14, weight="bold"),
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            corner_radius=6,
            height=40,
            command=self._on_calculate
        )
        self._calc_btn.pack(side="right")

        # Bind enter key to calculate
        self._balance_entry.bind("<Return>", lambda e: self._on_calculate())
        self._risk_entry.bind("<Return>", lambda e: self._on_calculate())
        self._entry_entry.bind("<Return>", lambda e: self._on_calculate())
        self._sl_entry.bind("<Return>", lambda e: self._on_calculate())

        # ─── RESULTS SECTION ───────────────────────────────────────────
        results_section = ctk.CTkFrame(scroll_frame, fg_color=INPUT_BG, corner_radius=8, border_width=1, border_color=BORDER_COLOR)
        results_section.pack(fill="x", pady=0)

        res_title = ctk.CTkLabel(
            results_section,
            text="Calculation Results",
            font=ctk.CTkFont(family="SF Mono", size=14, weight="bold"),
            text_color=TEXT_COLOR
        )
        res_title.pack(padx=15, pady=(15, 10), anchor="w")

        res_grid = ctk.CTkFrame(results_section, fg_color="transparent")
        res_grid.pack(fill="x", padx=15, pady=(0, 15))
        res_grid.grid_columnconfigure(1, weight=1)
        res_grid.grid_columnconfigure(3, weight=1)

        # Row 0: Risk Amount / Pip Size
        self._add_label(res_grid, "Risk Amount:", 0, 0)
        self._res_risk_amt = self._add_result_label(res_grid, "--", 0, 1)

        self._lbl_pip_size = self._add_label(res_grid, "Pip Size:", 0, 2)
        self._res_pip_size = self._add_result_label(res_grid, "--", 0, 3)

        # Row 1: SL Distance (Price) / SL Distance (Pips)
        self._add_label(res_grid, "SL Distance (Price):", 1, 0)
        self._res_sl_price_dist = self._add_result_label(res_grid, "--", 1, 1)

        self._lbl_sl_pips_dist = self._add_label(res_grid, "SL Distance (Pips):", 1, 2)
        self._res_sl_pips_dist = self._add_result_label(res_grid, "--", 1, 3)

        # Row 2: Pip Value / Lot Size
        self._lbl_pip_value = self._add_label(res_grid, "Pip Value (1 Lot):", 2, 0)
        self._res_pip_value = self._add_result_label(res_grid, "--", 2, 1)

        self._add_label(res_grid, "Lot Size:", 2, 2)
        self._res_lot_size = self._add_result_label(res_grid, "--", 2, 3, font_size=16, color=SUCCESS_COLOR)

        # Row 3: Position Size
        self._add_label(res_grid, "Position Size (Units):", 3, 0)
        self._res_pos_size = self._add_result_label(res_grid, "--", 3, 1)

        # Initialize labels correctly
        self._update_dynamic_labels()

    # ─── UI Helpers ──────────────────────────────────────────────────
    def _add_label(self, parent, text, row, col, color=LABEL_COLOR):
        lbl = ctk.CTkLabel(
            parent, text=text, font=ctk.CTkFont(family="SF Mono", size=12), text_color=color
        )
        lbl.grid(row=row, column=col, sticky="w", padx=(0, 10), pady=10)
        return lbl

    def _add_result_label(self, parent, text, row, col, font_size=13, color=TEXT_COLOR):
        lbl = ctk.CTkLabel(
            parent, text=text, font=ctk.CTkFont(family="SF Mono", size=font_size, weight="bold"), text_color=color
        )
        lbl.grid(row=row, column=col, sticky="w", padx=(0, 20), pady=10)
        return lbl

    def _input_kwargs(self):
        return {
            "font": ctk.CTkFont(family="SF Mono", size=12),
            "width": 160,
            "fg_color": HEADER_BG,
            "border_color": BORDER_COLOR,
            "text_color": TEXT_COLOR,
            "button_color": ACCENT_COLOR,
            "button_hover_color": ACCENT_HOVER,
            "dropdown_fg_color": HEADER_BG,
            "dropdown_hover_color": INPUT_BG,
            "corner_radius": 6,
            "state": "readonly"
        }

    def _entry_kwargs(self):
        return {
            "font": ctk.CTkFont(family="SF Mono", size=12),
            "width": 160,
            "fg_color": HEADER_BG,
            "border_color": BORDER_COLOR,
            "text_color": TEXT_COLOR,
            "corner_radius": 6
        }

    def _update_dynamic_labels(self):
        instrument = self._instrument_var.get()
        spec = DataManager.INSTRUMENT_SPECS.get(instrument)
        if spec and spec.get("type") == "forex":
            self._lbl_pip_size.configure(text="Pip Size:")
            self._lbl_sl_pips_dist.configure(text="SL Distance (Pips):")
            self._lbl_pip_value.configure(text="Pip Value (1 Lot):")
        else:
            self._lbl_pip_size.configure(text="Tick Size:")
            self._lbl_sl_pips_dist.configure(text="SL Distance (Ticks):")
            self._lbl_pip_value.configure(text="Tick Value (1 Lot):")

    # ─── Calculation Logic ───────────────────────────────────────────
    def _on_calculate(self):
        # Reset results
        for lbl in [self._res_risk_amt, self._res_pip_size, self._res_sl_price_dist, 
                    self._res_sl_pips_dist, self._res_pip_value, self._res_lot_size, self._res_pos_size]:
            lbl.configure(text="--")

        try:
            balance = float(self._balance_var.get())
            risk_pct = float(self._risk_var.get())
            entry_price = float(self._entry_var.get())
            sl_price = float(self._sl_var.get())
            instrument = self._instrument_var.get()
        except ValueError:
            self.status_lbl.configure(text="Error: Invalid numeric input.", text_color=ALERT_COLOR)
            return

        if balance <= 0 or risk_pct <= 0 or entry_price <= 0 or sl_price <= 0:
            self.status_lbl.configure(text="Error: Values must be > 0.", text_color=ALERT_COLOR)
            return

        spec = DataManager.INSTRUMENT_SPECS.get(instrument)
        if not spec:
            self.status_lbl.configure(text=f"Error: Spec not found for {instrument}", text_color=ALERT_COLOR)
            return

        # Basic calculations
        risk_amount = balance * (risk_pct / 100.0)
        sl_dist_price = abs(entry_price - sl_price)
        
        if sl_dist_price == 0:
            self.status_lbl.configure(text="Error: Entry and SL cannot be same.", text_color=ALERT_COLOR)
            return

        tick_size = spec.get("tick_size", spec.get("pip_size"))
        sl_dist_pips = sl_dist_price / tick_size

        self._res_risk_amt.configure(text=f"${risk_amount:,.2f}")
        self._res_pip_size.configure(text=f"{tick_size}")
        self._res_sl_price_dist.configure(text=f"{sl_dist_price:.5f}")
        self._res_sl_pips_dist.configure(text=f"{sl_dist_pips:.1f}")

        self.status_lbl.configure(text="Fetching live market data...", text_color=LABEL_COLOR)
        self._calc_btn.configure(state="disabled")
        
        # Dispatch background thread for generic network fetching
        threading.Thread(
            target=self._fetch_market_data,
            args=(instrument, spec, risk_amount, sl_dist_pips, tick_size),
            daemon=True
        ).start()

    def _fetch_market_data(self, instrument, spec, risk_amount, sl_dist_pips, tick_size):
        # 1. Fetch current price of the instrument
        current_price = DataManager.get_current_price(instrument)
        
        # 2. Fetch conversion rate from quote currency to USD (account currency)
        quote_currency = spec["quote"]
        conversion_rate = DataManager.get_conversion_rate(quote_currency, "USD")
        
        # Switch back to UI thread
        self.after(0, self._on_market_data_fetched, current_price, conversion_rate, spec, risk_amount, sl_dist_pips, tick_size)

    def _on_market_data_fetched(self, current_price, conversion_rate, spec, risk_amount, sl_dist_pips, tick_size):
        self._calc_btn.configure(state="normal")
        
        if conversion_rate is None or conversion_rate <= 0:
            self.status_lbl.configure(text=f"Error: Could not fetch conversion rate for {spec['quote']}->USD.", text_color=ALERT_COLOR)
            return
            
        contract_size = spec["contract_size"]
        
        # Value in quote currency = tick_size * contract_size
        # Value in USD = (Value in quote currency) * conversion_rate
        pip_value = (tick_size * contract_size) * conversion_rate
        
        self._finalize_calculation(pip_value, risk_amount, sl_dist_pips, contract_size, current_price, spec["quote"], conversion_rate)

    def _finalize_calculation(self, pip_value, risk_amount, sl_dist_pips, contract_size, current_price, quote_curr, conversion_rate):
        lot_size = risk_amount / (sl_dist_pips * pip_value)
        position_size = lot_size * contract_size
        
        self._res_pip_value.configure(text=f"${pip_value:,.2f}")
        self._res_lot_size.configure(text=f"{lot_size:.3f}")
        self._res_pos_size.configure(text=f"{position_size:,.0f}")
        
        # Format informative status message
        status_msg = "Success."
        if current_price:
            status_msg += f" (Live Price: {current_price:.5f})"
        if quote_curr != "USD":
            status_msg += f" (Conv {quote_curr}->USD: {conversion_rate:.5f})"
            
        self.status_lbl.configure(text=status_msg, text_color=SUCCESS_COLOR)
