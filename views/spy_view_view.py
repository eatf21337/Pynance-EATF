import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import filedialog
from PIL import Image

import pandas as pd
import numpy as np

from assets import Assets

"""
Résumé du projet :

1. Changements à market.update()
La logique précédente avait une croissance exponentielle, et était très exploitable
car se basait sur la valeur du drift. La nouvelle logique fait varier l'action autour
d'une droite fixe de (1 + 0.1/365)x + b, soit + 10 % par année. 

2. Changements à users
Améliorer le processur pour prendre des décisions. Remplir les portefeuilles par défaut.

3. Added spy_view_view
Barre du haut : possibilité d'exporter la userbase, le market, et chacune des trois vues
affichées + rafraîchir.

Panneau de gauche : 
Boutons pour sélectionner un utilisateur, système de pages, filtres.
Quatre vues : Top rendements, Richesse par statut, Actions populaires, Statistiques globales

Panneau de droite : 
Une description comme si c'était une "AI overview" (parce que c'est drôle),
deux vues identiques et customisables.
Quatre options : Portfolio, Portfolio (Graphique), Historique de transactions, Évolution des actifs

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

        self.user_options = [
            "Portfolio",
            "Portfolio (Graphique)",
            "Historique de transactions",
            "Évolution des actifs",
        ]
        self.userbase_options = [
            "Top rendements",
            "Richesse par statut",
            "Actions populaires",
            "Statistiques globales",
        ]
        # Pour conserver les options sélectionnées
        self.active_options = [0, 0, 1]

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
            4: "Joueur",
        }

        # Congig par défaut
        self.page_len = 30
        self.page = 0
        self.sort_col = "Holdings"
        self.sort_asc = False
        self.row_buttons = []

        # Boutons d'utilisateurs
        self.mover_buttons = []

        # Pour permettre des comparaisons
        self.previous_data = None

        self.data = self.dataframe_doer()
        self.current_user_index = None

        # Pour définir quelles sont les vues à exporter
        self.slot_exports = {0: None, 1: None, 2: None}

        self.top_bar_builder_yet_again()
        self.user_carder()
        self.left_view_builder()

    def top_bar_builder_yet_again(self):
        bar = ctk.CTkFrame(self, fg_color="#181a20", height=48, corner_radius=0)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=(0, 4))

        # Icône
        self.icon = ctk.CTkLabel(bar, text="👁", font=("Arial", 30, "bold"))
        self.icon.pack(side="left", padx=12, pady=8)

        # Titre
        self.name = ctk.CTkLabel(bar, text="SpyView™", font=("Arial", 20, "bold"))
        self.name.pack(side="left", padx=12, pady=8)

        # Bouton pour rafraîchir
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

        # Bouton pour exporter
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

    # Panneau de gauche
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

        # Filtre (recherche)
        self.selector = ctk.CTkEntry(
            panel,
            width=180,
            height=36,
            placeholder_text="Filtrer par ...",
            show=None,
            state="normal",
            border_color="#181a20",
            fg_color="#121418",
        )
        self.selector.pack(anchor="w", padx=12, pady=(12, 6))

        self.selector.bind("<KeyRelease>", self.button_filter_doer)

        # Carte

        self.card1 = ctk.CTkScrollableFrame(panel, fg_color="#121418", corner_radius=8)
        self.card1.pack(fill="x", padx=12, pady=(6, 12))

        # Trier par catégorie
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
            command=lambda: self.data_sorter("Statut"),
        )
        self.status_btn.grid(row=0, column=2, sticky="nsew", padx=(0, 5))

        # Créer les boutons pour choisir un utilisateur
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
        self.text_maker = ("▼ ", "▶ ", "▲ ")
        self.colorizer = ("#f6465d", "#848e9c", "#0ba367")
        names = [self.data.iloc[_]["Nom d'utilisateur"] for _ in range(len(self.data))]
        holding = [
            f"{self.text_maker[row['Change']]}{row['Holdings']:,.2f} $"
            for _, row in self.data.iterrows()
        ]
        status = [self.data.iloc[_]["Statut"] for _ in range(len(self.data))]
        self.max_name = max(len(h) for h in names if h is not None)
        self.max_hold = max(len(h) for h in holding if h is not None)
        self.max_stat = max(len(h) for h in status if h is not None)

        self.leaderboarder(
            self.data[
                self.data["Nom d'utilisateur"].str.contains(
                    self.selector.get(), case=False, na=False, regex=False
                )
            ]
        )

        # Pages
        nav = ctk.CTkFrame(panel, fg_color="transparent")
        nav.pack(fill="x", padx=12, pady=4)
        ctk.CTkButton(
            nav,
            text="< Précédent",
            width=90,
            border_color="#848e9c",
            fg_color="#121418",
            command=lambda: self.page_change_doer(-1),
        ).pack(side="left")
        self.page_label = ctk.CTkLabel(nav, text="Page 1")
        self.page_label.pack(side="left", expand=True)
        ctk.CTkButton(
            nav,
            text="Suivant >",
            width=90,
            border_color="#848e9c",
            fg_color="#121418",
            command=lambda: self.page_change_doer(1),
        ).pack(side="right")

        # Vue
        self.userbase_slot_1 = DataSlot(
            panel,
            0,
            self.userbase_options,
            self.data_architect_renderer_but_for_userbase,
        )
        self.userbase_slot_1.pack(fill="both", expand=True, padx=12, pady=6)
        self.after(
            200,
            lambda: self.userbase_slot_1.on_change(
                0, self.userbase_options[self.active_options[0]]
            ),
        )

    # Panneau de droite
    def user_carder(self):
        # Pour reconstruire la carte après un nouveau choix
        if not hasattr(self, "card"):
            self.card = ctk.CTkFrame(self, fg_color="#181a20", corner_radius=6)
            self.card.grid(row=1, column=1, sticky="nsew", padx=(6, 12), pady=3)
            self.card.grid_propagate(False)

        for widget in self.card.winfo_children():
            widget.destroy()

        # Tant qu'il n'y a pas eu de choix
        if self.current_user_index is None:
            self.slot_exports[1] = None
            self.slot_exports[2] = None
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
        ai.pack(anchor="nw", padx=14, pady=6)
        self.ai_desc = ctk.CTkLabel(
            self.card,
            text=desc,
            text_color="#eaecef",
            font=("Arial", 12),
            anchor="w",
            justify="left",
        )

        self.ai_desc.pack(anchor="nw", fill="x", padx=14, pady=6)

        # Pour permettre au texte de changer de ligne tout seul
        def update_wrap(event):
            if not self.ai_desc.winfo_exists():
                return

            scaling = ctk.ScalingTracker.get_widget_scaling(self.ai_desc)
            new_wrap = max(100, int((event.width / scaling) - 35))
            current_wrap = self.ai_desc.cget("wraplength")

            if abs(current_wrap - new_wrap) > 10:
                self.ai_desc.configure(wraplength=new_wrap)

        self.card.bind("<Configure>", update_wrap)

        # Les 2 views
        slots = ctk.CTkFrame(self.card, fg_color="transparent")
        slots.pack(fill="both", expand=True, padx=8, pady=6)

        slots.grid_columnconfigure(0, weight=1)
        for row in range(2):
            slots.grid_rowconfigure(row, weight=1, uniform="user_slots")

        self.user_slot_1 = DataSlot(
            slots, 1, self.user_options, self.data_architect_renderer
        )
        self.user_slot_1.grid(row=0, column=0, sticky="nsew", padx=8, pady=6)
        self.user_slot_1.on_change(1, self.user_options[self.active_options[1]])

        self.user_slot_2 = DataSlot(
            slots, 2, self.user_options, self.data_architect_renderer
        )
        self.user_slot_2.grid(row=1, column=0, sticky="nsew", padx=8, pady=6)
        self.user_slot_2.on_change(2, self.user_options[self.active_options[2]])

    # Créer le dataframe des données
    def dataframe_doer(self):
        df = pd.DataFrame()

        playerlist = self.engine.database.get("playerlist") or []
        cash_map = self.engine.database.get("cash") or {}
        portfolios = self.engine.database.get("portfolios") or {}
        starting_cash = (
            self.engine.database.get("starting_cash")
            or self.engine.config["starting_cash"]
        )

        # Données de base
        df["Nom d'utilisateur"] = [
            data.nom for data in self.engine.userbase.userbase
        ] + list(playerlist)

        df["Portfolio"] = [data.wallet for data in self.engine.userbase.userbase] + [
            portfolios.get(player, {}) for player in playerlist
        ]

        df["Liquidités"] = [
            data.liquidity for data in self.engine.userbase.userbase
        ] + [cash_map.get(player, 0) for player in playerlist]

        df["Statut"] = [
            self.tier_illustrater[data.tier] for data in self.engine.userbase.userbase
        ] + [self.tier_illustrater[4]] * len(playerlist)

        df["Niveau"] = [data.lvl for data in self.engine.userbase.userbase] + [0] * len(
            playerlist
        )

        df["Données de départ"] = [
            data.initial_data for data in self.engine.userbase.userbase
        ] + [starting_cash] * len(playerlist)

        # Données calculées
        df["Holdings"] = [
            sum(
                qty * self.engine.market.stocks[ticker].price
                for ticker, qty in portfolio.items()
                if ticker in self.engine.market.stocks
            )
            + liquidity
            for portfolio, liquidity in zip(df["Portfolio"], df["Liquidités"])
        ]

        df["G/P"] = (
            (df["Holdings"] - df["Données de départ"]) / df["Données de départ"] * 100
        )

        if self.previous_data is not None and len(self.previous_data) == len(df):
            df["Change"] = np.select(
                (
                    df["Holdings"] > self.previous_data["Holdings"],
                    df["Holdings"] < self.previous_data["Holdings"],
                ),
                (2, 0),
                default=1,
            )
        else:
            df["Change"] = 1

        df["Percentile (Argent)"] = df["Holdings"].rank(pct=True) * 100
        df["Percentile (Rendement)"] = df["G/P"].rank(pct=True) * 100

        return df

    # Exporter les données
    def export(self):
        # 1. Userbase
        path = filedialog.asksaveasfilename(
            title="Exporter Userbase",
            initialfile="userbase.csv",
            defaultextension=".csv",
            filetypes=[("Fichier CSV", "*.csv")],
        )
        if path:
            self.data.to_csv(path, index=False, encoding="utf-8-sig")

        # 2. Market
        path = filedialog.asksaveasfilename(
            title="Exporter Market",
            initialfile="market.csv",
            defaultextension=".csv",
            filetypes=[("Fichier CSV", "*.csv")],
        )
        if path:
            market_df = pd.DataFrame(
                [
                    {
                        "Ticker": s.ticker,
                        "Nom": s.name,
                        "Prix": round(s.price, 4),
                        "Devise": s.currency,
                        "Actions totales": s.shares,
                        "Actions disponibles": s.available_shares,
                        "Capitalisation": round(s.market_cap, 2),
                        "Volatilité": s.volatility,
                        "Drift": s.drift,
                    }
                    for s in self.engine.market.stocks.values()
                ]
            )
            market_df.to_csv(path, index=False, encoding="utf-8-sig")

        # 3. Les 3 vues
        slot_names = [
            f"Vue Userbase - {self.userbase_options[self.active_options[0]]}",
            f"Vue Utilisateur 1 - {self.user_options[self.active_options[1]]}",
            f"Vue Utilisateur 2 - {self.user_options[self.active_options[2]]}",
        ]

        for i in range(3):
            item = self.slot_exports.get(i)
            if item is None:
                continue
            # Deux possiblités de données : graphique ou csv
            if isinstance(item, Figure):
                path = filedialog.asksaveasfilename(
                    title=f"Exporter {slot_names[i]}",
                    initialfile=f"vue_{i + 1}.png",
                    defaultextension=".png",
                    filetypes=[("Image PNG", "*.png")],
                )
                if path:
                    item.savefig(path, facecolor=item.get_facecolor(), dpi=150)

            elif isinstance(item, pd.DataFrame):
                path = filedialog.asksaveasfilename(
                    title=f"Exporter {slot_names[i]}",
                    initialfile=f"vue_{i + 1}.csv",
                    defaultextension=".csv",
                    filetypes=[("Fichier CSV", "*.csv")],
                )
                if path:
                    item.to_csv(path, index=False, encoding="utf-8-sig")

    # Configurer les boutons en fonction des données fournies
    def leaderboarder(self, data):
        sorted_df = data.sort_values(by=self.sort_col, ascending=self.sort_asc)
        start = self.page * self.page_len
        page_df = sorted_df.iloc[start : start + self.page_len]

        names = page_df["Nom d'utilisateur"].tolist()
        holdings = [
            f"{self.text_maker[r['Change']]}{r['Holdings']:,.2f} $"
            for _, r in page_df.iterrows()
        ]
        statuses = page_df["Statut"].tolist()

        for i, btn in enumerate(self.mover_buttons):
            if i < len(page_df):
                row = page_df.iloc[i]
                real_idx = row.name  # Index réel de l'utilisateur dans self.data
                color = self.colorizer[row["Change"]]

                btn.configure(
                    text=f"{names[i]:<{self.max_name}}     {holdings[i]:>{self.max_hold}}     {statuses[i]:>{self.max_stat}}",
                    fg_color=(
                        "#545A6D"
                        if real_idx == self.current_user_index
                        else "transparent"
                    ),
                    border_color=color,
                    command=lambda idx=real_idx: self.open_card(idx),
                )
                btn.pack(fill="x", padx=5, pady=2)
            else:
                btn.pack_forget()

    # Ouvrir la carte de l'utilisateur sélectionné
    def open_card(self, index):
        self.current_user_index = index
        self.leaderboarder(
            self.data[
                self.data["Nom d'utilisateur"].str.contains(
                    self.selector.get(), case=False, na=False, regex=False
                )
            ]
        )  # Met à jour la couleur du bouton pour que le bouton de l'utilisateur sélectionné soit en surbrillance
        self.user_carder()

    # Trier les boutons par la colonne sélectionnée
    def data_sorter(self, col_name):
        if self.sort_col == col_name:
            self.sort_asc = not self.sort_asc
        else:
            self.sort_col = col_name
            self.sort_asc = True

        self.page = 0

        # Ajouter la genre de flèche
        if col_name == "Holdings":
            self.holdings_btn.configure(
                text=f"{"▼" if not self.sort_asc else "▲"} Actifs"
            )
            self.status_btn.configure(text=f"Statut")
            self.username_btn.configure(text=f"Nom d'utilisateur")
        elif col_name == "Statut":
            self.holdings_btn.configure(text=f"Actifs")
            self.status_btn.configure(
                text=f"{"▼" if not self.sort_asc else "▲"} Statut"
            )
            self.username_btn.configure(text=f"Nom d'utilisateur")
        elif col_name == "Nom d'utilisateur":
            self.holdings_btn.configure(text=f"Actifs")
            self.status_btn.configure(text=f"Statut")
            self.username_btn.configure(
                text=f"Nom d'utilisateur {"▼" if not self.sort_asc else "▲"}"
            )

        self.leaderboarder(
            self.data[
                self.data["Nom d'utilisateur"].str.contains(
                    self.selector.get(), case=False, na=False, regex=False
                )
            ]
        )

    # Re-configure les boutons en fonction de la page
    def page_change_doer(self, delta):
        max_page = max(0, (len(self.data) - 1) // self.page_len)
        self.page = max(0, min(self.page + delta, max_page))
        self.page_label.configure(text=f"Page {self.page+1}")
        self.leaderboarder(
            self.data[
                self.data["Nom d'utilisateur"].str.contains(
                    self.selector.get(), case=False, na=False, regex=False
                )
            ]
        )

    # Retourne les descriptions générées par "IA"
    def descriptor(self):
        # Au cas où, les descriptions ne sont pas vraiment générées par IA.
        if self.current_user_index >= len(self.engine.userbase.userbase):
            df_history = pd.DataFrame(self._get_user_history())
        else:
            df_history = pd.DataFrame(
                self.engine.userbase.userbase[
                    self.current_user_index
                ].transaction_history
            )

        self.trading_styles_dict_er = {}
        tier = self.data.iloc[self.current_user_index]["Statut"]
        niveau = self.data.iloc[self.current_user_index]["Niveau"]
        holdings = self.data.iloc[self.current_user_index]["Holdings"]
        liquidites = self.data.iloc[self.current_user_index]["Liquidités"]
        percentile_rend = self.data.iloc[self.current_user_index][
            "Percentile (Rendement)"
        ]
        percentile_hold = self.data.iloc[self.current_user_index]["Percentile (Argent)"]
        concentration = (
            max(0.0, min(100.0, (1 - liquidites / holdings) * 100))
            if holdings > 0
            else 0.0
        )

        if not df_history.empty and "Profit" in df_history.columns:
            sells = df_history["Profit"].dropna()
            win_rate = (sells > 0).mean() * 100 if len(sells) > 0 else 0.0
        else:
            win_rate = 0.0

        descriptions = {
            "Gestionnaire d'actifs": (
                f"Fonds institutionnel de niveau {niveau:.2f} gérant {holdings:,.2f} $ d'actifs "
                f"(top {max(0.1, 100 - percentile_hold):.1f} % des plus gros portefeuilles) avec {liquidites:,.2f} $ en réserve. "
                f"Son capital est investi à {concentration:.1f} %, affichant un taux de réussite de {win_rate:.1f} % "
                f"et un rendement supérieur à {percentile_rend:.1f} % du marché."
            ),
            "Personnalité publique": (
                f"Investisseur influent de niveau {niveau:.2f} détenant {holdings:,.2f} $ d'actifs totaux "
                f"et {liquidites:,.2f} $ de liquidités (percentile richesse : {percentile_hold:.1f} %). "
                f"Avec une exposition au marché de {concentration:.1f} % et un win rate de {win_rate:.1f} %, "
                f"ses performances le placent au {percentile_rend:.1f}e percentile."
            ),
            "Corporation": (
                f"Entité corporative de niveau {niveau:.2f} disposant d'un portefeuille de {holdings:,.2f} $ "
                f"(percentile {percentile_hold:.1f} %) et de {liquidites:,.2f} $ disponibles. "
                f"Engagée à {concentration:.1f} % sur les marchés, elle maintient {win_rate:.1f} % de positions gagnantes "
                f"pour un indice de rendement de {percentile_rend:.1f} %."
            ),
            "Civil": (
                f"Investisseur particulier (bot niveau {niveau:.2f}) avec {holdings:,.2f} $ d'actifs totaux et {liquidites:,.2f} $ en cash. "
                f"Son portefeuille, investi à {concentration:.1f} %, le classe au {percentile_hold:.1f}e percentile de richesse "
                f"et au {percentile_rend:.1f}e percentile de rendement ({win_rate:.1f} % de trades gagnants)."
            ),
            "Joueur": (
                f"Profil joueur totalisant {holdings:,.2f} $ d'actifs (top {max(0.1, 100 - percentile_hold):.1f} % des participants) "
                f"et {liquidites:,.2f} $ de liquidités. Actuellement investi à {concentration:.1f} %, "
                f"il affiche un taux de succès de {win_rate:.1f} % et surpasse {percentile_rend:.1f} % des investisseurs en rendement."
            ),
        }

        return descriptions[tier]

    # Créer les vues de userbase
    def data_architect_renderer(self, choice, container, index):
        if self.current_user_index is None:
            return
        user_row = self.data.iloc[self.current_user_index]
        portfolio = user_row["Portfolio"]  # Dictionnaire {ticker: quantité}

        if choice == "Portfolio":
            self.active_options[index] = 0
            scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
            scroll.pack(fill="both", expand=True)

            columns = 2
            for col in range(columns):
                scroll.grid_columnconfigure(col, weight=1, uniform="group1")

            for idx, (stock, qty) in enumerate(portfolio.items()):
                r = idx // columns
                c = idx % columns
                temp = self.engine.market.get_stock_by_ticker(stock)
                label_str = f"{temp.name} ({temp.ticker})" if temp else stock
                if len(label_str) > 30:
                    label_str = label_str[:27] + "..."

                ctk.CTkLabel(
                    scroll,
                    text=f"{label_str:<30} : {qty:>10,}",
                    text_color="#eaecef",
                    font=("Consolas", 12),
                    anchor="w",
                ).grid(row=r, column=c, sticky="ew", padx=14, pady=3)

            self.slot_exports[index] = pd.DataFrame(
                [
                    {
                        "Ticker": stock,
                        "Nom": (
                            self.engine.market.get_stock_by_ticker(stock).name
                            if self.engine.market.get_stock_by_ticker(stock)
                            else stock
                        ),
                        "Quantité": qty,
                        "Prix": (
                            self.engine.market.stocks[stock].price
                            if stock in self.engine.market.stocks
                            else 0
                        ),
                    }
                    for stock, qty in portfolio.items()
                ]
            )

        elif choice == "Portfolio (Graphique)":
            self.active_options[index] = 1
            fig = Figure(
                figsize=(4, 2.5), dpi=100, facecolor="#121418", layout="constrained"
            )
            ax = fig.add_subplot(111)
            ax.set_facecolor("#121418")

            tickers = list(portfolio.keys())
            quantities = [
                a * self.engine.market.stocks[b].price
                for a, b in zip(list(portfolio.values()), tickers)
            ]

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

            canvas = FigureCanvasTkAgg(fig, master=container)
            canvas.draw()
            widget = canvas.get_tk_widget()
            widget.configure(bg="#121418", highlightthickness=0)
            widget.pack(fill="both", expand=True, padx=6, pady=6)
            self.slot_exports[index] = fig

        elif choice == "Historique de transactions":
            self.active_options[index] = 2
            if self.current_user_index >= len(self.engine.userbase.userbase):
                df_history = pd.DataFrame(self._get_user_history())[-200:]
            else:
                df_history = pd.DataFrame(
                    self.engine.userbase.userbase[
                        self.current_user_index
                    ].transaction_history
                )[-200:]

            self.slot_exports[index] = df_history

            header_frame = ctk.CTkFrame(container, fg_color="#1e2329", corner_radius=6)
            header_frame.pack(fill="x", padx=5, pady=(5, 2))

            header_text = (
                f"{'#':<5} "
                f"{'Stock':<10} "
                f"{'Ticker':<8} "
                f"{'Actions':<16} "
                f"{'Fonds':<20} "
                f"{"Prix d'achat":<16} "
                f"{'Profit (%)':<6}"
            )

            ctk.CTkLabel(
                header_frame,
                text=header_text,
                text_color="#848e9c",
                font=("Consolas", 12, "bold"),
                anchor="w",
            ).pack(fill="x", padx=10, pady=6)

            scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
            scroll.pack(fill="both", expand=True)

            rows = []
            for idx, row in df_history.iloc[::-1].iterrows():
                shares = f"{int(row['Amount_Shares']):,}"
                cash = f"${abs(row['Amount_Cash']):,.2f}"
                price = f"${row['Share_Price']:,.2f}"
                val = row.get("Profit")
                if val is None or pd.isna(val):
                    profit = "-"
                else:
                    profit = f"{float(val):+,.1f} %"

                line = (
                    f"{idx:<5} "
                    f"{row['Action']:<10} "
                    f"{row['Ticker']:<8} "
                    f"{shares:<16} "
                    f"{cash:<20} "
                    f"{price:<16} "
                    f"{profit:<6}"
                )
                rows.append(line)

            ctk.CTkLabel(
                scroll,
                text="\n\n".join(rows),
                text_color="#eaecef",
                font=("Consolas", 12),
                justify="left",
                anchor="w",
            ).pack(fill="x", padx=10, pady=4)

        elif choice == "Évolution des actifs":
            self.active_options[index] = 3
            history = self._get_user_holdings_history()
            if not history:
                ctk.CTkLabel(
                    container, text="En attente de données...", text_color="#848e9c"
                ).pack(pady=20)
                self.slot_exports[index] = None
                return
            color = "#0ecb81" if history[-1] >= history[0] else "#f6465d"

            fig = Figure(
                figsize=(4, 2.5), dpi=100, facecolor="#121418", layout="constrained"
            )
            ax = fig.add_subplot(111)
            ax.set_facecolor("#121418")

            ax.plot(history, color=color, linewidth=1.8)
            ax.fill_between(
                range(len(history)), history, min(history), color=color, alpha=0.12
            )
            ax.grid(True, color="#2b313a", linestyle="--", linewidth=0.5)
            ax.tick_params(colors="#848e9c", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#2b313a")

            canvas = FigureCanvasTkAgg(fig, master=container)
            canvas.draw()
            widget = canvas.get_tk_widget()
            widget.configure(bg="#121418", highlightthickness=0)
            widget.pack(fill="both", expand=True, padx=6, pady=6)

            self.slot_exports[index] = fig

    # Créer les vues de userbase
    def data_architect_renderer_but_for_userbase(self, choice, container, index):
        self.active_options[index] = self.userbase_options.index(choice)

        if choice == "Richesse par statut":
            grouped = self.data.groupby("Statut")["Holdings"].sum().sort_values()

            fig = Figure(
                figsize=(4, 2.2), dpi=100, facecolor="#121418", layout="constrained"
            )
            ax = fig.add_subplot(111)
            ax.set_facecolor("#121418")

            ax.barh(grouped.index, grouped.values, color="#0ecb81")
            ax.tick_params(colors="#eaecef", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#2b313a")

            canvas = FigureCanvasTkAgg(fig, master=container)
            canvas.draw()
            widget = canvas.get_tk_widget()
            widget.configure(bg="#121418", highlightthickness=0)
            widget.pack(fill="both", expand=True, padx=6, pady=6)

            self.slot_exports[index] = fig

        elif choice == "Actions populaires":
            counts = {}
            for portfolio in self.data["Portfolio"]:
                for ticker in portfolio:
                    counts[ticker] = counts.get(ticker, 0) + 1

            if not counts:
                ctk.CTkLabel(
                    container, text="Aucune action détenue.", text_color="#848e9c"
                ).pack(pady=20)
                self.slot_exports[index] = None
                return

            top10 = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5][::-1]
            tickers = [t[0] for t in top10]
            nb_holders = [t[1] for t in top10]

            fig = Figure(
                figsize=(4, 2.2), dpi=100, facecolor="#121418", layout="constrained"
            )
            ax = fig.add_subplot(111)
            ax.set_facecolor("#121418")

            ax.barh(tickers, nb_holders, color="#3b8ed0")
            ax.set_xlabel("Nombre de détenteurs", color="#848e9c", fontsize=8)
            ax.tick_params(colors="#eaecef", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#2b313a")

            canvas = FigureCanvasTkAgg(fig, master=container)
            canvas.draw()
            widget = canvas.get_tk_widget()
            widget.configure(bg="#121418", highlightthickness=0)
            widget.pack(fill="both", expand=True, padx=6, pady=6)

            self.slot_exports[index] = fig

        elif choice == "Top rendements":
            temp = self.data.copy()
            temp["Perf"] = (
                (temp["Holdings"] - temp["Données de départ"])
                / temp["Données de départ"]
                * 100
            )
            top = temp.sort_values(by="Perf", ascending=False).head(10)

            self.slot_exports[index] = top[
                ["Nom d'utilisateur", "Statut", "Holdings", "Perf"]
            ]

            lines = []
            for i, (_, row) in enumerate(top.iterrows(), start=1):
                name = row["Nom d'utilisateur"][:24]
                lines.append(
                    f"{i}. {name:<24} {row['Perf']:>+8.2f} %   ({row['Statut']})"
                )

            ctk.CTkLabel(
                container,
                text="\n\n".join(lines),
                text_color="#0ecb81",
                font=("Consolas", 12),
                justify="left",
                anchor="nw",
            ).pack(fill="both", expand=True, padx=14, pady=12)

        # 4. Résumé chiffré global (NumPy)
        elif choice == "Statistiques globales":
            holdings = self.data["Holdings"].to_numpy()
            liquidites = self.data["Liquidités"].to_numpy()
            total = np.sum(holdings)
            pct_cash = (np.sum(liquidites) / total * 100) if total > 0 else 0

            stats_text = (
                f"Nombre d'acteurs      : {len(self.data)}\n\n"
                f"Richesse totale       : {total:,.2f} $\n\n"
                f"Richesse moyenne      : {np.mean(holdings):,.2f} $\n\n"
                f"Richesse médiane      : {np.median(holdings):,.2f} $\n\n"
                f"Part en liquidités    : {pct_cash:.1f} %"
            )

            ctk.CTkLabel(
                container,
                text=stats_text,
                text_color="#eaecef",
                font=("Consolas", 12),
                justify="left",
                anchor="nw",
            ).pack(fill="both", expand=True, padx=14, pady=12)

            self.slot_exports[index] = pd.DataFrame(
                [
                    {"Statistique": "Nombre d'acteurs", "Valeur": len(self.data)},
                    {"Statistique": "Richesse totale ($)", "Valeur": round(total, 2)},
                    {
                        "Statistique": "Richesse moyenne ($)",
                        "Valeur": round(np.mean(holdings), 2),
                    },
                    {
                        "Statistique": "Richesse médiane ($)",
                        "Valeur": round(np.median(holdings), 2),
                    },
                    {
                        "Statistique": "Part en liquidités (%)",
                        "Valeur": round(pct_cash, 1),
                    },
                ]
            )

    # Re-configurer les boutons en fonction du filte
    def button_filter_doer(self, nothing=None):
        self.leaderboarder(
            self.data[
                self.data["Nom d'utilisateur"].str.contains(
                    self.selector.get(), case=False, na=False, regex=False
                )
            ]
        )
        self.selector.configure()

    # Pour la database
    def _get_user_history(self):
        if self.current_user_index >= len(self.engine.userbase.userbase):
            username = self.data.iloc[self.current_user_index]["Nom d'utilisateur"]
            return self.engine.database.getPath(f"player_history:{username}") or []
        return self.engine.userbase.userbase[
            self.current_user_index
        ].transaction_history

    # Pour la database
    def _get_user_holdings_history(self):
        if self.current_user_index >= len(self.engine.userbase.userbase):
            username = self.data.iloc[self.current_user_index]["Nom d'utilisateur"]
            return (
                self.engine.database.getPath(f"player_holdings_history:{username}")
                or []
            )
        return self.engine.userbase.userbase[self.current_user_index].holdings_history

    # Quand la simulation est réinitialisée
    def refresh(self):
        self.previous_data = None

        self.active_options = [0, 0, 1]

        self.data = self.dataframe_doer()
        self.current_user_index = None

        self.user_carder()
        self.leaderboarder(
            self.data[
                self.data["Nom d'utilisateur"].str.contains(
                    self.selector.get(), case=False, na=False, regex=False
                )
            ]
        )

    # Pour le bouton rafraîchir
    def refresher(self):
        self.previous_data = self.data
        self.data = self.dataframe_doer()
        self.userbase_slot_1.on_change(0, self.userbase_options[self.active_options[0]])

        if self.current_user_index is not None:
            self.user_slot_1.on_change(1, self.user_options[self.active_options[1]])
            self.user_slot_2.on_change(2, self.user_options[self.active_options[2]])
            self.ai_desc.configure(text=self.descriptor())

        self.leaderboarder(
            self.data[
                self.data["Nom d'utilisateur"].str.contains(
                    self.selector.get(), case=False, na=False, regex=False
                )
            ]
        )


# Vu que les vues répètent toujours les mêmes structures :


class DataSlot(ctk.CTkFrame):
    def __init__(self, master, index, options, render_callback):
        super().__init__(master, fg_color="transparent")
        self.render_callback = render_callback

        self.menu = ctk.CTkOptionMenu(
            self,
            values=options,
            command=lambda choice: self.on_change(index, choice),
            fg_color="#2b313a",
            button_color="#363c4e",
        )
        self.menu.pack(anchor="nw", pady=(6, 6))

        self.content = ctk.CTkFrame(self, fg_color="#121418", corner_radius=8)
        self.content.pack(fill="both", expand=True)

    def on_change(self, index, choice=None):
        if choice is None:
            choice = self.menu.get()
        else:
            self.menu.set(choice)
        for w in self.content.winfo_children():
            w.destroy()
        self.render_callback(self.menu.get(), self.content, index)
