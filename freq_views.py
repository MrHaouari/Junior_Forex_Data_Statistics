"""
freq_views.py — Frequency distribution tables and charts.
"""

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk
import pandas as pd

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Dark-theme color palette matching the app
BG_COLOR = "#0b0e1a"
FG_COLOR = "#d4d4dc"
BAR_COLOR = "#7f5af0"
LINE_COLOR = "#00e5ff"

class BaseFreqView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.columnconfigure(0, weight=1, uniform="col")
        self.columnconfigure(1, weight=1, uniform="col")
        
        # Left side: Treeview
        self._table_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._table_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Right side: Chart
        self._chart_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        self._chart_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self._tree = None

    def _setup_tree(self, columns: list[str]):
        container = tk.Frame(self._table_frame, bg=BG_COLOR)
        container.pack(fill="both", expand=True)

        self._tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            style="Dark.Treeview",
            selectmode="browse",
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

        for col in columns:
            self._tree.heading(col, text=col, anchor="center")
            self._tree.column(col, anchor="center", minwidth=60, width=120)

    def _populate_tree(self, df: pd.DataFrame):
        self._tree.delete(*self._tree.get_children())
        for idx, row in df.iterrows():
            tag = "even" if idx % 2 == 0 else "odd"
            values = []
            for col in self._tree["columns"]:
                val = row[col]
                if "Probability" in col:
                    values.append(f"{val*100:.2f}%")
                else:
                    values.append(str(val))
            self._tree.insert("", "end", values=values, tags=(tag,))

    def clear(self):
        if self._tree:
            self._tree.delete(*self._tree.get_children())
        for widget in self._chart_frame.winfo_children():
            widget.destroy()


class OOFreqView(BaseFreqView):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # New frame for conditional stats
        self._cond_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._cond_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 5))
        self.rowconfigure(1, weight=0)
        
        # New frame for bands stats
        self._bands_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._bands_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        self.rowconfigure(2, weight=0)
        
        self._cond_tree = None
        self._bands_tree = None

    def _setup_cond_tree(self):
        columns = ["Segment Name", "proba% (Average Value)", "Freq' (Count)", "Freq %", "Prob' Adjust % Change"]
        
        container = tk.Frame(self._cond_frame, bg=BG_COLOR)
        container.pack(fill="x", expand=True)

        self._cond_tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            style="Dark.Treeview",
            selectmode="browse",
            height=3
        )
        self._cond_tree.pack(fill="x", expand=True)

        for col in columns:
            self._cond_tree.heading(col, text=col, anchor="center")
            self._cond_tree.column(col, anchor="center")

    def _setup_bands_tree(self):
        columns = ["Std Dev", "1", "2", "3"]
        
        container = tk.Frame(self._bands_frame, bg=BG_COLOR)
        container.pack(fill="x", expand=True)

        self._bands_tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            style="Dark.Treeview",
            selectmode="browse",
            height=2
        )
        self._bands_tree.pack(fill="x", expand=True)

        for col in columns:
            self._bands_tree.heading(col, text=col, anchor="center")
            self._bands_tree.column(col, anchor="center")

    def load_data(self, df: pd.DataFrame, cond_df: pd.DataFrame = None, bands_df: pd.DataFrame = None):
        if df.empty:
            self.clear()
            if self._cond_tree:
                self._cond_tree.delete(*self._cond_tree.get_children())
            if self._bands_tree:
                self._bands_tree.delete(*self._bands_tree.get_children())
            return
            
        columns = ["Interval", "Frequency", "Probability", "Cumulative Probability"]
        if not self._tree:
            self._setup_tree(columns)
            
        self._populate_tree(df)
        self._draw_chart(df)

        # Populate conditional table
        if cond_df is not None and not cond_df.empty:
            if not self._cond_tree:
                self._setup_cond_tree()
                
            self._cond_tree.delete(*self._cond_tree.get_children())
            for idx, row in cond_df.iterrows():
                tag = "even" if idx % 2 == 0 else "odd"
                values = [
                    row["Segment"],
                    f"{row['proba% (Average)']:.4f}%",
                    str(int(row["Freq' (Count)"])),
                    f"{row['Freq %'] * 100:.4f}%",
                    f"{row['Prob\' Adjust % Change']:.4f}%"
                ]
                self._cond_tree.insert("", "end", values=values, tags=(tag,))

        # Populate bands table
        if bands_df is not None and not bands_df.empty:
            if not self._bands_tree:
                self._setup_bands_tree()
                
            self._bands_tree.delete(*self._bands_tree.get_children())
            for idx, row in bands_df.iterrows():
                tag = "even" if idx % 2 == 0 else "odd"
                values = [
                    row["Std Dev"],
                    f"{row['1']:.4f}%",
                    f"{row['2']:.4f}%",
                    f"{row['3']:.4f}%"
                ]
                self._bands_tree.insert("", "end", values=values, tags=(tag,))

        
    def _draw_chart(self, df: pd.DataFrame):
        for widget in self._chart_frame.winfo_children():
            widget.destroy()
            
        # Dark style for matplotlib
        plt.style.use("dark_background")
        fig = Figure(figsize=(5, 4), dpi=100, facecolor=BG_COLOR)
        ax1 = fig.add_subplot(111)
        ax1.set_facecolor(BG_COLOR)
        
        x = range(len(df))
        ax1.bar(x, df["Probability"] * 100, color=BAR_COLOR, alpha=0.8, label="Prob (%)")
        ax1.set_ylabel("Probability (%)", color=FG_COLOR)
        ax1.tick_params(axis='y', colors=FG_COLOR)
        
        ax2 = ax1.twinx()
        ax2.plot(x, df["Cumulative Probability"] * 100, color=LINE_COLOR, marker="o", linewidth=2, label="Cumul (%)")
        ax2.set_ylabel("Cumulative (%)", color=LINE_COLOR)
        ax2.tick_params(axis='y', colors=LINE_COLOR)
        
        ax1.set_xticks(x)
        labels = [lbl if i % 2 == 0 else "" for i, lbl in enumerate(df["Interval"])]
        ax1.set_xticklabels(labels, rotation=45, ha="right", color=FG_COLOR, fontsize=8)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self._chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

class HLFreqView(BaseFreqView):
    def load_data(self, df: pd.DataFrame):
        if df.empty:
            self.clear()
            return
            
        columns = ["Interval", "Frequency", "Probability"]
        if not self._tree:
            self._setup_tree(columns)
            
        self._populate_tree(df)
        self._draw_chart(df)
        
    def _draw_chart(self, df: pd.DataFrame):
        for widget in self._chart_frame.winfo_children():
            widget.destroy()
            
        plt.style.use("dark_background")
        fig = Figure(figsize=(5, 4), dpi=100, facecolor=BG_COLOR)
        ax = fig.add_subplot(111)
        ax.set_facecolor(BG_COLOR)
        
        x = range(len(df))
        ax.bar(x, df["Probability"] * 100, color=BAR_COLOR, alpha=0.8)
        ax.set_ylabel("Probability (%)", color=FG_COLOR)
        ax.tick_params(axis='y', colors=FG_COLOR)
        
        ax.set_xticks(x)
        labels = [lbl if i % 2 == 0 else "" for i, lbl in enumerate(df["Interval"])]
        ax.set_xticklabels(labels, rotation=45, ha="right", color=FG_COLOR, fontsize=8)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self._chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
