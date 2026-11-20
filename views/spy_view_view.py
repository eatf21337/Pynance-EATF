import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
import tkinter.font as tkfont

import pandas as pd
import numpy as np

from assets import Assets

# user topographical dpicter


class SpyViewView(ctk.CTkFrame):
    def __init__(self, master, controller, engine):
        super().__init__(master, fg_color="#0b0e11")
        self.controller = controller

        self.engine = engine

        # Configuration de la grille
        self.grid_columnconfigure(0, weight=4, uniform="panels")
        self.grid_columnconfigure(1, weight=5, uniform="panels")
        self.grid_rowconfigure(1, weight=1)

        self.assets = Assets("Assets")

        self.button_style = {
            "text": "",
            "width": 40,
            "height": 40,
            "corner_radius": 8,
            "fg_color": "transparent",
            "hover_color": "#2a2d2e",
        }

        self.tier_illustrater = {
            0: "Gestionnaire d'actif",
            1: "Personnalité publique",
            2: "Corporation",
            3: "Civil",
        }

        self.mover_buttons = []

        self.previous_data = None

        self.data = self.dataframer()
        self.current_user_index = None

        self.top_bar_builder_yet_again()
        self.user_carder()
        self.left_view_builder()

    def top_bar_builder_yet_again(self):
        bar = ctk.CTkFrame(self, fg_color="#181a20", height=48, corner_radius=0)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=(0, 4))

        self.icon = ctk.CTkLabel(bar, text="👁", font=("Arial", 30, "bold"))
        self.icon.pack(side="left", padx=12, pady=8)

        # Titre
        self.name = ctk.CTkLabel(bar, text="SpyView™", font=("Arial", 20, "bold"))
        self.name.pack(side="left", padx=12, pady=8)

        refresh = ctk.CTkImage(
            dark_image=Image.open(self.assets.getAssetPath("refresh.png")),
            size=(24, 24),
        )

        self.btn_refresh = ctk.CTkButton(
            bar,
            image=refresh,
            command=self.refresher,
            **self.button_style,
        )
        self.btn_refresh.pack(side="right", padx=10)

        export = ctk.CTkImage(
            dark_image=Image.open(self.assets.getAssetPath("file-export.png")),
            size=(24, 24),
        )

        self.btn_export = ctk.CTkButton(
            bar,
            image=export,
            command=self.export,
            **self.button_style,
        )
        self.btn_export.pack(side="right", padx=10)



    def left_view_builder(self):
        panel = ctk.CTkFrame(self, fg_color="#181a20", corner_radius=6)
        panel.grid(row=1, column=0, sticky="nsew", padx=(12, 6), pady=3)

        # Titre
        title = ctk.CTkLabel(
            panel,
            text="Données",
            font=("Arial", 22, "bold"),
            justify="left",
            )
        title.pack(anchor="w", padx=12, pady=(12, 0))

        # 2 Selections
        """
        self.name_select = ctk.CTkComboBox(
            panel,
            values=(""),
            command=self.switch_data,
            fg_color="#2b313a",
            button_color="#363c4e",
            border_width=0,
            width=180,
        )
        self.name_select.pack(side="left", padx=12, pady=8)
"""
        # Premier panneau

        self.card1 = ctk.CTkScrollableFrame(panel, fg_color="#121418", scrollbar_button_color="red", corner_radius=8)
        self.card1.pack(fill="x", padx=12, pady=12)


        # Filtres
        filter_btn_area = ctk.CTkFrame(self.card1, fg_color="#121418")
        filter_btn_area.pack(fill="x")

        filter_btn_area.columnconfigure((0, 1, 2), weight=1, uniform="header_cols")

        username_btn = ctk.CTkButton(                
                filter_btn_area,
                text=f"Nom d'utilisateur",
                anchor="w",
                height=30,
                fg_color="transparent",
                hover_color="#545A6D",
                font=("Consolas", 11),
                corner_radius=0,
                #command=lambda: self.open_card(_)
                )
        username_btn.grid(row=0, column=0, sticky="nsew", padx=(5, 0))

        holdings_btn = ctk.CTkButton(                
                filter_btn_area,
                text=f"Actifs",
                height=30,
                fg_color="transparent",
                hover_color="#545A6D",
                font=("Consolas", 11),
                corner_radius=0,
                anchor="center",
                #command=lambda: self.open_card(_)
                )
        holdings_btn.grid(row=0, column=1, sticky="nsew", padx=(0, 0))

        status_btn = ctk.CTkButton(                
                filter_btn_area,
                text=f"Statut",
                height=30,
                fg_color="transparent",
                hover_color="#545A6D",
                font=("Consolas", 11),
                corner_radius=0,
                anchor="e",
                #command=lambda: self.open_card(_)
                )
        status_btn.grid(row=0, column=2, sticky="nsew", padx=(0, 5))

        # Vue
        self.leaderboarder()

        # Titre

        # Deuxième panneau

    def user_carder(self):
        if not hasattr(self, "card"):
            self.card = ctk.CTkFrame(self, fg_color="#181a20", corner_radius=6)
            self.card.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=3)

        for widget in self.card.winfo_children():
            widget.destroy()

        if self.current_user_index is None:
            self.placeholder = ctk.CTkLabel(
                self.card,
                text="Sélectionnez un utilisateur dans le panneau de gauche pour commencer.",
                text_color="#6c748a",
                font=("Arial", 13),
                justify="center",
            )
            self.placeholder.place(relx=0.5, rely=0.5, anchor="center")
            return

        self.user_label = ctk.CTkLabel(
            self.card,
            text=self.data.iloc[self.current_user_index]["Nom d'utilisateur"],
            text_color="#eaecef",
            font=("Arial", 22, "bold"),
        )
        self.user_label.pack(anchor="nw", padx=14, pady=(14, 8))


    def dataframer(self):
        holdings = [round(data.holdings, 2) for data in self.engine.userbase.userbase]
        #  wallet =
        # funds =
        df = pd.DataFrame()
        df["Nom d'utilisateur"] = [data.nom for data in self.engine.userbase.userbase]
        #    df["Fonds"] =
        df["Holdings"] = holdings
        df["Statut"] = [self.tier_illustrater[data.tier] for data in self.engine.userbase.userbase]
        if self.previous_data is not None:
            df["Change"] = np.select((df["Holdings"] > self.previous_data["Holdings"], df["Holdings"] < self.previous_data["Holdings"]), (2, 0), default=1)
        else:
            df["Change"] = 1

        return df

    def export(self):
        print("aaaaaaaa")

    def leaderboarder(self):
        for btn in self.mover_buttons:
            btn.destroy()

        self.mover_buttons = []

        text_maker = ("▼ ", "▸ ", "▲ ")
        colorizer = ("#f6465d", "#848e9c", "#0ba367")
        names = [self.data.iloc[_]["Nom d'utilisateur"] for _ in range(len(self.data))]
        holding = [f"{text_maker[row['Change']]}{row['Holdings']:,} $" for _, row in self.data.iterrows()]
        status = [self.data.iloc[_]["Statut"] for _ in range(len(self.data))]
        max_name = max(len(h) for h in names)
        max_hold = max(len(h) for h in holding)
        max_stat = max(len(h) for h in status)

        for _ in range(min(50, len(self.data))):
            index = self.data.iloc[_]["Change"]
            color = colorizer[index]

            button = ctk.CTkButton(
                self.card1,
                text=f"{names[_]:<{max_name}}     {holding[_]:>{max_hold}}     {status[_]:>{max_stat}}",
                anchor="w",
                height=30,
                corner_radius=6,
                fg_color=("#545A6D" if _ == self.current_user_index else "transparent"),
                hover_color="#545A6D",
                font=("Consolas", 11),
                border_color=color,
                border_width=0.3,
                command=lambda idx=_: self.open_card(idx)            
                )
            button.pack(fill="x", padx=5, pady=2)
            self.mover_buttons.append(button)

    def open_card(self, index):
        if self.current_user_index is not None:
            self.mover_buttons[self.current_user_index].configure(fg_color="#181a20")

        self.current_user_index = index
        self.mover_buttons[index].configure(fg_color="#545A6D")

        self.user_carder()

    def data_sorter(self):
        pass

    def refresh(self):
        self.previous_data = None

        self.data = self.dataframer()
        self.current_user_index = None

        self.user_carder()
        self.leaderboarder()

    def refresher(self):
        self.previous_data = self.data
        self.data = self.dataframer()

        self.leaderboarder()