"""
resume_view.py — Dynamic Statistic Resume Table.
"""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import pandas as pd

# Theme constants
HEADER_BG = "#1a1a2e"
HEADER_FG = "#e0e0ff"
ROW_EVEN_BG = "#16213e"
ROW_ODD_BG = "#0f3460"
ROW_FG = "#d4d4dc"
BG_COLOR = "#0b0e1a"

class ResumeView(ctk.CTkFrame):
    """Statistic Resume Panel showing dynamic comparative insights."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        self._tree = None

    def _setup_tree(self, columns):
        container = tk.Frame(self, bg=BG_COLOR)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        self._tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            style="Dark.Treeview",
            selectmode="browse"
        )

        vsb = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self._tree.yview,
            style="Dark.Vertical.TScrollbar",
        )
        self._tree.configure(yscrollcommand=vsb.set)

        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Column widths
        widths = {
            "Analysis Metric": 220,
            "Status / Result": 350,
            "Current Value (Yesterday)": 180,
            "Comparison Benchmark": 250
        }

        for col in columns:
            self._tree.heading(col, text=col, anchor="center")
            w = widths.get(col, 150)
            self._tree.column(col, anchor="center", minwidth=100, width=w)

    def load_data(self, df: pd.DataFrame):
        if df.empty:
            if self._tree:
                self._tree.delete(*self._tree.get_children())
            return
            
        columns = list(df.columns)
        if not self._tree:
            self._setup_tree(columns)
            
        self._tree.delete(*self._tree.get_children())
        for idx, row in df.iterrows():
            tag = "even" if idx % 2 == 0 else "odd"
            values = [row[col] for col in columns]
            self._tree.insert("", "end", values=values, tags=(tag,))
