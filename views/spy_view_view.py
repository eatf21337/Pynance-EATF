import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from PIL import Image, ImageTk
import tkinter.font as tkfont

import pandas as pd
import numpy as np

from assets import Assets

# user topographical depicter

"""
Roadmap :

Changer la logique de refresh des boutons pour éviter de les delete à chaque fois
Add les players à data
Faire les filters
Picker entre market et userbase
Ajouter une search bar
Ajouter un systeme de pages
Ajouter la right view
    Users:
    Nom
    Holdings
    Statut
    Portfolio
    Concentration
    Win rate
    Trading style
    Niveau
    Volatility
    Percentile
    Historique de transactions
Ajouter les graphes pour user/userbase/stock/market
Fix money displaying through app

"""



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

        self.user_options = ["Portfolio", "Portfolio (Graphique)"]
        self.userbase_options = ["aaaaaaaaaa", "bbbbbbbbbbb"]

        self.button_style = {
            "text": "",
            "width": 40,
            "height": 40,
            "corner_radius": 8,
            "fg_color": "transparent",
            "hover_color": "#2a2d2e",
        }

        self.tier_illustrater = {
            0: "Gestionnaire d'actifs",
            1: "Personnalité publique",
            2: "Corporation",
            3: "Civil",
            4: "Joueur"
        }

        self.page_len = 30
        self.page = 0
        self.sort_col = "Holdings"
        self.sort_asc = False
        self.row_buttons = []

        self.mover_buttons = []

        self.previous_data = None

        self.data = self.dataframe_doer()
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

        self.username_btn = ctk.CTkButton(                
                filter_btn_area,
                text=f"Nom d'utilisateur",
                anchor="w",
                height=30,
                fg_color="transparent",
                hover_color="#545A6D",
                font=("Consolas", 11),
                corner_radius=0,
                command=lambda: self.data_sorter("Nom d'utilisateur"),
                )
        self.username_btn.grid(row=0, column=0, sticky="nsew", padx=(5, 0))

        self.holdings_btn = ctk.CTkButton(                
                filter_btn_area,
                text=f"Actifs",
                height=30,
                fg_color="transparent",
                hover_color="#545A6D",
                font=("Consolas", 11),
                corner_radius=0,
                anchor="center",
                command=lambda: self.data_sorter("Holdings"),
                )
        self.holdings_btn.grid(row=0, column=1, sticky="nsew", padx=(0, 0))

        self.status_btn = ctk.CTkButton(                
                filter_btn_area,
                text=f"Statut",
                height=30,
                fg_color="transparent",
                hover_color="#545A6D",
                font=("Consolas", 11),
                corner_radius=0,
                anchor="e",
                command=lambda: self.data_sorter("Statut")
                )
        self.status_btn.grid(row=0, column=2, sticky="nsew", padx=(0, 5))

        # Vue
        self.page = 0
        self.sort_col = "Holdings"
        self.sort_asc = False
        self.mover_buttons = []

        for _ in range(self.page_len):
            btn = ctk.CTkButton(
                self.card1,
                text="",
                anchor="w",
                height=30,
                corner_radius=6,
                fg_color="transparent",
                hover_color="#545A6D",
                font=("Consolas", 11),
                border_width=0.3,
            )
            btn.pack(fill="x", padx=5, pady=2)
            self.mover_buttons.append(btn)

        # Trouver les dimensions
        self.text_maker = ("▼ ", "▸ ", "▲ ")
        self.colorizer = ("#f6465d", "#848e9c", "#0ba367")
        names = [self.data.iloc[_]["Nom d'utilisateur"] for _ in range(len(self.data))]
        holding = [f"{self.text_maker[row['Change']]}{row['Holdings']:,.2f} $" for _, row in self.data.iterrows()]
        status = [self.data.iloc[_]["Statut"] for _ in range(len(self.data))]
        self.max_name = max(len(h) for h in names)
        self.max_hold = max(len(h) for h in holding)
        self.max_stat = max(len(h) for h in status)

        self.leaderboarder()

        # Pages
        nav = ctk.CTkFrame(panel, fg_color="transparent")
        nav.pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(nav, text="< Précédent", width=90, command=lambda: self.page_change_doer(-1)).pack(side="left")
        self.page_label = ctk.CTkLabel(nav, text="Page 1")
        self.page_label.pack(side="left", expand=True)
        ctk.CTkButton(nav, text="Suivant >", width=90, command=lambda: self.page_change_doer(1)).pack(side="right")

        # Vue
        self.userbase_slot_1 = DataSlot(panel, self.userbase_options, self.data_architect_renderer)
        self.userbase_slot_1.pack(fill="both", expand=True, padx=12, pady=6)

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

        # Nom
        self.user_label = ctk.CTkLabel(
            self.card,
            text=self.data.iloc[self.current_user_index]["Nom d'utilisateur"],
            text_color="#eaecef",
            font=("Arial", 22, "bold"),
        )
        self.user_label.pack(anchor="nw", padx=14, pady=(14, 8))

        # Description générée par "IA"
        desc = self.descriptor()
        ai = ctk.CTkLabel(
            self.card,
            text="✨ SpyView pense que ...",
            text_color="#eaecef",
            font=("Arial", 14, "bold"),
        )
        ai.pack(anchor="nw", padx=14, pady=(14, 8))

        self.ai_desc = ctk.CTkLabel(
            self.card,
            text=desc,
            text_color="#eaecef",
            font=("Arial", 12),
            anchor="w",
            justify="left",
        )
        self.ai_desc.pack(anchor="nw", fill="x", padx=14)

        def update_wrap(event):
            if not self.ai_desc.winfo_exists():
                return
            
            scaling = ctk.ScalingTracker.get_widget_scaling(self.ai_desc)
            usable_width = (event.width / scaling) - 4
            new_wrap = max(10, int(usable_width))
        
            if self.ai_desc.cget("wraplength") != new_wrap:
                self.ai_desc.configure(wraplength=new_wrap)

        self.ai_desc.bind("<Configure>", update_wrap)

        # Les 2 views
        slots = ctk.CTkFrame(self.card, fg_color="transparent")
        slots.pack(fill="both", expand=True, padx=8, pady=6)

        slots.grid_columnconfigure(0, weight=1)
        for row in range(2):
            slots.grid_rowconfigure(row, weight=1, uniform="user_slots")

        self.user_slot_1 = DataSlot(slots, self.user_options, self.data_architect_renderer)
        self.user_slot_1.grid(row=0, column=0, sticky="nsew", padx=8, pady=6)
        self.user_slot_1.on_change(self.user_options[0])

        self.user_slot_2 = DataSlot(slots, self.user_options, self.data_architect_renderer)
        self.user_slot_2.grid(row=1, column=0, sticky="nsew", padx=8, pady=6)
        self.user_slot_2.on_change(self.user_options[1])

    def dataframe_doer(self):
        df = pd.DataFrame()
        holdings = [round(data.holdings, 2) for data in self.engine.userbase.userbase]

        # Données de base
        df["Portfolio"] = [data.wallet for data in self.engine.userbase.userbase]
        df["Liquidités"] = [data.liquidity for data in self.engine.userbase.userbase]
        df["Nom d'utilisateur"] = [data.nom for data in self.engine.userbase.userbase]
        df["Holdings"] = holdings
        df["Statut"] = [self.tier_illustrater[data.tier] for data in self.engine.userbase.userbase]
        df["Niveau"] = [data.lvl for data in self.engine.userbase.userbase]
        df["Données de départ"] = [data.initial_data for data in self.engine.userbase.userbase]

        # Données calculées
        df["G/P"] = abs((df["Holdings"] - df["Données de départ"])/df["Données de départ"] * 100)

        if self.previous_data is not None:
            df["Change"] = np.select((df["Holdings"] > self.previous_data["Holdings"], df["Holdings"] < self.previous_data["Holdings"]), (2, 0), default=1)
        else:
            df["Change"] = 1

        return df

    def export(self):
        print("aaaaaaaa")

    def leaderboarder(self):
        sorted_df = self.data.sort_values(by=self.sort_col, ascending=self.sort_asc)
        start = self.page * self.page_len
        page_df = sorted_df.iloc[start : start + self.page_len]

        names = page_df["Nom d'utilisateur"].tolist()
        holdings = [f"{self.text_maker[r['Change']]}{r['Holdings']:,.2f} $" for _, r in page_df.iterrows()]
        statuses = page_df["Statut"].tolist()

        for i, btn in enumerate(self.mover_buttons):
            if i < len(page_df):
                row = page_df.iloc[i]
                real_idx = row.name  # Index réel de l'utilisateur dans self.data
                color = self.colorizer[row["Change"]]

                btn.configure(
                    text=f"{names[i]:<{self.max_name}}     {holdings[i]:>{self.max_hold}}     {statuses[i]:>{self.max_stat}}",
                    fg_color="#545A6D" if real_idx == self.current_user_index else "transparent",
                    border_color=color,
                    command=lambda idx=real_idx: self.open_card(idx),
                )
                btn.pack(fill="x", padx=5, pady=2)
            else:
                btn.pack_forget()

    def open_card(self, index):
        self.current_user_index = index
        self.leaderboarder()  # Met à jour la couleur du bouton
        self.user_carder()

    def data_sorter(self, col_name):
        if self.sort_col == col_name:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_col = col_name
            self.sort_asc = True

        self.page = 0

        # Ajouter la genre de flèche 
        if col_name == "Holdings":
            self.holdings_btn.configure(text=f"{"▼" if not self.sort_asc else "▲"} Actifs")
            self.status_btn.configure(text=f"Statut")
            self.username_btn.configure(text=f"Nom d'utilisateur")
        elif col_name == "Statut":
            self.holdings_btn.configure(text=f"Actifs")
            self.status_btn.configure(text=f"{"▼" if not self.sort_asc else "▲"} Statut")
            self.username_btn.configure(text=f"Nom d'utilisateur")
        elif col_name == "Nom d'utilisateur":
            self.holdings_btn.configure(text=f"Actifs")
            self.status_btn.configure(text=f"Statut")
            self.username_btn.configure(text=f"Nom d'utilisateur {"▼" if not self.sort_asc else "▲"}")
        

        self.leaderboarder()

    def page_change_doer(self, delta):
        max_page = max(0, (len(self.data) - 1) // self.page_len)
        self.page = max(0, min(self.page + delta, max_page))
        self.page_label.configure(text=f"Page {self.page+1}")
        self.leaderboarder()

    def descriptor(self):
        # Tier, Niveau, Holdings, Liquidités, Concentration, Win rate, Trading style, Volatility, Percentile
        tier = self.data.iloc[self.current_user_index]["Statut"] 
        niveau = self.data.iloc[self.current_user_index]["Niveau"]
        holdings = self.data.iloc[self.current_user_index]["Holdings"]
        liquidites = self.data.iloc[self.current_user_index]["Liquidités"]
        percentile = 0
        concentration = ""
        trading_style = "a"
        volatility = 0
        win_rate = 0


        descriptions = {
            "Gestionnaire d'actifs": (
                f"Une banque, un fonds d'investissement ou un gestionnaire d'actifs institutionnel"
                f"(Niveau {niveau}), se classant dans le {percentile}e percentile des acteurs du marché. "
                f"Avec un portefeuille évalué à {holdings} et {liquidites} de liquidités disponibles, cette entité "
                f"maintient une concentration d'actifs de {concentration}. Son approche repose sur un style de trading "
                f"{trading_style}, affichant une volatilité de {volatility} et un taux de réussite (win rate) de {win_rate}."
            ),
            "Personnalité publique": (
                f"Une personnalité publique ou figure influente du milieu financier classée {tier} (Niveau {niveau}), "
                f"positionnée au {percentile}e percentile. Disposant de {holdings} en actifs sous gestion et d'une réserve "
                f"de {liquidites} en liquidités, son capital présente une concentration de {concentration}. "
                f"Connue pour un style de trading {trading_style}, son portefeuille enregistre une volatilité de {volatility} "
                f"et un win rate de {win_rate}."
            ),
            "Corporation": (
                f"Une corporation ou entreprise commerciale de catégorie {tier} (Niveau {niveau}), figurant dans le "
                f"{percentile}e percentile de sa classe. Sa trésorerie et ses investissements totalisent {holdings}, "
                f"dont {liquidites} en liquidités immédiates, avec un indice de concentration de {concentration}. "
                f"Sa gestion financière adopte un profil {trading_style}, générant une volatilité de {volatility} "
                f"pour un win rate global de {win_rate}."
            ),
            "Civil": (
                f"Un investisseur particulier de statut {tier} (Niveau {niveau}), surpassant ses pairs au {percentile}e percentile. "
                f"Son patrimoine investi s'élève à {holdings}, appuyé par {liquidites} de liquidités et un taux de "
                f"concentration de {concentration}. Il opère selon un style de trading {trading_style}, avec une "
                f"volatilité mesurée à {volatility} et un win rate de {win_rate}."
            ),
            "Joueur": (
                "Un joueur actif, classé dans le {percentile}e percentile du classement. "
                "Son capital en jeu atteint {holdings}, incluant {liquidites} de liquidités prêtes à être déployées, "
                "avec une concentration de {concentration}. Son style de trading {trading_style} se traduit par "
                "une volatilité de {volatility} et un win rate de {win_rate}."
            )
        }

        return descriptions[tier]

    def data_architect_renderer(self, choice, container):
        user_row = self.data.iloc[self.current_user_index]
        portfolio = user_row["Portfolio"]  # Dictionnaire {ticker: quantité}

        if choice == "Portfolio":
            scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
            scroll.pack(fill="both", expand=True)

            columns = 3
            for col in range(columns):
                scroll.grid_columnconfigure(col, weight=1)

            for idx, (stock, qty) in enumerate(portfolio.items()):
                row = idx // columns
                col = idx % columns
                
                ctk.CTkLabel(
                    scroll,
                    text=f"{stock:<8} : {qty} actions",
                    text_color="#eaecef",
                    font=("Consolas", 12),
                    justify="left"
                ).grid(row=row, column=col, sticky="w", padx=14, pady=4)

        elif choice == "Portfolio (Graphique)":
            fig, ax = plt.subplots(figsize=(4, 2.5), facecolor="#121418")
            ax.set_facecolor("#121418")

            tickers = list(portfolio.keys())
            quantities = list(portfolio.values())

            wedges, texts, autotexts = ax.pie(
                quantities,
                labels=tickers,
                autopct="%1.1f%%",
                startangle=90,
                textprops={"color": "#eaecef", "fontsize": 9},
                wedgeprops={"edgecolor": "#121418", "linewidth": 1.5},
            )

            for autotext in autotexts:
                autotext.set_color("#121418")
                autotext.set_weight("bold")
                autotext.set_fontsize(8)

            ax.axis("equal")
            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
            plt.close(fig)

    def refresh(self):
        self.previous_data = None

        self.data = self.dataframe_doer()
        self.current_user_index = None

        self.user_carder()
        self.leaderboarder()

    def refresher(self):
        self.previous_data = self.data
        self.data = self.dataframe_doer()
        self.user_slot_1.on_change()
        self.user_slot_2.on_change()
        self.userbase_slot_1.on_change()
        desc = self.descriptor()
        self.ai_desc.configure(text=desc)

        self.leaderboarder()


class DataSlot(ctk.CTkFrame):
    def __init__(self, master, options, render_callback):
        super().__init__(master, fg_color="transparent")
        self.render_callback = render_callback

        self.menu = ctk.CTkOptionMenu(
            self,
            values=options,
            command=self.on_change,
            fg_color="#2b313a",
            button_color="#363c4e",
        )
        self.menu.pack(anchor="nw", pady=(6, 6))

        self.content = ctk.CTkFrame(self, fg_color="#121418", corner_radius=8)
        self.content.pack(fill="both", expand=True)

    def on_change(self, choice=None):
        if choice is None:
            choice = self.menu.get()
        else:
            self.menu.set(choice)
        for w in self.content.winfo_children():
            w.destroy()
        self.render_callback(self.menu.get(), self.content)