import pandas as pd

import random as rd
import json
import math
import csv
from assets import Assets
from collections import defaultdict
import statistics


class User:
    def __init__(self, nom, lvl, starting_cash, tier):
        self.nom = nom
        self.lvl = lvl
        self.wallet = {}
        self.liquidity = starting_cash
        self.tier = tier
        self.initial_data = starting_cash
        self.transaction_history = []
        self.holdings_history = [starting_cash]
        self.avg_cost = defaultdict(list)

    def get_holdings(self, market):
        stock_value = sum(
            qty * market.stocks[ticker].price
            for ticker, qty in self.wallet.items()
            if ticker in market.stocks
        )
        return stock_value + self.liquidity

    # Définir comment les utilisateurs simulés prennent des décisions
    def make_decision(self, market, good_stocks):
        all_tickers = list(market.stocks.keys())
        if not all_tickers:
            return

        # 1. Probabilité d'agir et nombre d'actions observées selon le niveau / tier
        # Les gros acteurs (lvl >= 8 ou tier en haut de la hiérarchie) regardent 100 % du marché
        if self.lvl >= 8.0 or self.tier in (0, 1):
            activity_chance = 1.0
            sample_tickers = all_tickers
        else:
            # Tiers inférieurs / particuliers : action ponctuelle et attention limitée
            activity_chance = min(0.65, 0.15 + 0.08 * self.lvl)
            nb_seen = max(1, min(len(all_tickers), int(3 + self.lvl * 2)))
            sample_tickers = rd.sample(all_tickers, nb_seen)

        if rd.random() > activity_chance:
            return

        # 2. Précision d'analyse : les meilleurs bots ont presque zéro bruit
        skill_factor = max(0.0, (10.0 - min(10.0, self.lvl)) / 10.0)
        noise_std = 0.06 * skill_factor

        # 3. Achat sur la meilleure opportunité perçue
        best_ticker = None
        best_score = -999.0

        for ticker in sample_tickers:
            perceived = good_stocks.get(ticker, 0.0) + rd.gauss(0, noise_std)
            if perceived > best_score:
                best_score = perceived
                best_ticker = ticker

        if best_ticker and best_score > 0.002:
            stock = market.stocks[best_ticker]
            # Les bots forts investissent plus franchement quand le signal est bon
            alloc_min = 0.10 if self.lvl >= 7 else 0.05
            alloc_max = 0.35 if self.lvl >= 7 else 0.15
            budget = self.liquidity * rd.uniform(alloc_min, alloc_max)

            qty = int(budget // stock.price)
            if qty > 0:
                self.buy_stock(stock, qty)

        # 4. Vente seulement si le signal est nettement négatif (évite de vendre sur un simple bruit)
        sell_threshold = -0.025 if self.lvl >= 7 else -0.015
        for ticker, owned_qty in list(self.wallet.items()):
            if owned_qty <= 0:
                continue
            perceived = good_stocks.get(ticker, 0.0) + rd.gauss(0, noise_std)
            if perceived < sell_threshold:
                stock = market.stocks[ticker]
                sell_ratio = rd.uniform(0.15, 0.45) if self.lvl >= 7 else rd.uniform(0.30, 0.80)
                sell_qty = max(1, int(owned_qty * sell_ratio))
                self.sell_stock(stock, sell_qty)

    def buy_stock(self, stock, qty):
        already_owned = self.wallet.get(stock.ticker, 0)
        max_allowed = int(stock.shares * 0.05) - already_owned
        qty = min(qty, stock.available_shares, max(0, max_allowed))


        cost = stock.price * qty
        if self.liquidity >= cost and qty > 0:
            self.avg_cost[stock.ticker].append(stock.price)            
            self.liquidity -= cost
            self.wallet[stock.ticker] = already_owned + qty
            stock.buy(qty)
            self.transaction_history.append(
                {
                    "Action": "BUY",
                    "Ticker": stock.ticker,
                    "Amount_Shares": qty,
                    "Amount_Cash": round(-cost, 2),
                    "Share_Price": round(stock.price, 2),
                    "Profit": None
                }
            )

    def sell_stock(self, stock, qty):
        owned = self.wallet.get(stock.ticker, 0)
        qty = min(qty, owned)
        if qty > 0:
            self.liquidity += stock.price * qty
            self.wallet[stock.ticker] -= qty
            if self.wallet[stock.ticker] <= 0:
                del self.wallet[stock.ticker]
            stock.sell(qty)

            self.transaction_history.append(
                {
                    "Action": "SELL",
                    "Ticker": stock.ticker,
                    "Amount_Shares": -qty,
                    "Amount_Cash": round(stock.price * qty, 2),
                    "Share_Price": round(stock.price, 2),
                    "Profit": (stock.price - statistics.mean(self.avg_cost[stock.ticker])) / statistics.mean(self.avg_cost[stock.ticker]) * 100
                }
            )

    def wallet_setter(self, wallet):
        self.wallet = wallet.copy()

    def cash_setter(self, qty):
        self.liquidity = qty

    def __gt__(self, other):
        return self.name > other.name

    def __lt__(self, other):
        return self.name < other.name

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name

    def __ge__(self, other):
        return self.name >= other.name

    def __le__(self, other):
        return self.name <= other.name

    def __repr__(self):
        return f"{self.nom} (holding ${self.liquidity})"


class Userbase:
    def __init__(self, nb, difficulty_multiplier):
        self.userbase = []
        self.size = nb
        self.difficulty_multiplier = difficulty_multiplier
        self.random_proportions = self.randomize_odds()
        self.assets = Assets("Users")

    # Définir quelles proportions de chaque catégorie de users
    def randomize_odds(self):
        x, y, z, t = 0, 0, 0, 0
        for i in range(self.size):
            temp = rd.randint(1, self.size)
            if temp % 50 == 0 and x < 19:
                x += 1
            elif temp % 20 == 0 and y < 19:
                y += 1
            elif temp % 10 == 0 and z < 259:
                z += 1
            else:
                t += 1
        return [x, y, z, t]

    # T1 users : vraies compagnies d'investissements
    # Vraies données
    def build_T1s(self):
        with open(self.assets.getAssetPath("predefined_users.json"), "r") as f:
            t1_names = json.load(f)[0]
        users = []
        for i in range(self.random_proportions[0]):
            obj = rd.choice(list(t1_names.keys()))
            users.append(
                User(
                    obj,
                    10 * self.difficulty_multiplier**2,
                    math.ceil(t1_names[obj] * self.difficulty_multiplier**2),
                    0,
                )
            )
            t1_names.pop(obj)
        self.userbase.extend(users)

    # T2 users : vraies personnes célèbres en rapport avec la "finance"
    # Vraies données
    def build_T2s(self):
        with open(self.assets.getAssetPath("predefined_users.json"), "r") as f:
            t2_names = json.load(f)[1]
        users = []
        for i in range(self.random_proportions[1]):
            obj = rd.choice(list(t2_names.keys()))
            users.append(
                User(
                    obj,
                    rd.uniform(7, 9.5) * self.difficulty_multiplier**2,
                    math.ceil(t2_names[obj] * self.difficulty_multiplier**2),
                    1,
                )
            )
            t2_names.pop(obj)
        self.userbase.extend(users)

    # Fausses compagnies
    # 10% chances "The" + Adjectif + suffixe
    # Entre 1 et 10 B de fonds
    def build_T3s(self):
        with open(self.assets.getAssetPath("adjectives.json"), "r") as f:
            data = json.load(f)

        temp = []

        with open(self.assets.getAssetPath("terminology.csv"), "r") as f:
            terminology = list(csv.reader(f, delimiter=","))[0]

        for i in range(self.random_proportions[2]):
            name = ""
            if rd.randint(1, 100) % 10 == 0:
                name += "The "
            obj = rd.choice(data)
            name += obj
            data.remove(obj)
            name += " "
            name += rd.choice(terminology)
            temp.append(
                User(
                    name,
                    rd.uniform(4, 8) * self.difficulty_multiplier**2,
                    math.ceil(
                        rd.uniform(
                            1000000000 * self.difficulty_multiplier**2,
                            10000000000 * self.difficulty_multiplier**2,
                        )
                    ),
                    2,
                )
            )

        self.userbase.extend(temp)

    # T4 users : fausses personnes
    # Prénom + nom
    # Entre 100$ et 10000000 $ de fonds
    def build_T4s(self):
        with open(self.assets.getAssetPath("names.json"), "r") as f:
            first_names = json.load(f)
        with open(self.assets.getAssetPath("last.names.json"), "r") as f:
            last_names = json.load(f)

        users = []
        for i in range(self.random_proportions[3]):
            users.append(
                User(
                    (rd.choice(first_names) + " " + rd.choice(last_names)),
                    rd.uniform(0, 3),
                    math.ceil(
                        rd.uniform(
                            100 * self.difficulty_multiplier**2,
                            10000000 * self.difficulty_multiplier**2,
                        )
                    ),
                    3,
                )
            )
        self.userbase.extend(users)

    # Essentiellement, trouve, pour chaque action, quelle est sa "vraie valeur",
    # en fonction de l'action elle-même et des événements aléatoires.
    # Les deux paramètres sont donc le momentum et le mouvement des événements (event_impact)
    def good_stock_finder(self, market, active_event=None, eventer=None):
        scores = {}

        event_targets = {}
        event_impact = 0.0
        if active_event and eventer:
            affected_stocks = eventer.resolve_targets(active_event, market)
            event_targets = {s.ticker for s in affected_stocks}
            event_impact = active_event.get("impact", 0.0)

        for ticker, stock in market.stocks.items():
            if len(stock.history) >= 5 and stock.history[-5] > 0:
                momentum = (stock.price - stock.history[-5]) / stock.history[-5]
            else:
                momentum = 0.0

            score = (momentum * 0.1) + (stock.drift * 10)

            if ticker in event_targets:
                score += event_impact

            scores[ticker] = score

        return scores

    # Relier les users et le marché évalué
    def update(self, market, active_event=None, eventer=None):
        good_stocks = self.good_stock_finder(market, active_event, eventer)
        for bot in self.userbase:
            bot.make_decision(market, good_stocks)
            bot.holdings_history.append(round(bot.get_holdings(market), 2))


    def populate_wallets(self, market):
        all_stocks = list(market.stocks.values())
        filter = market.get_stock_by_ticker("SHIB-USD")
        if filter in all_stocks:
            all_stocks.remove(filter)
        if not all_stocks:
            return

        bot_tier_doer_of_magic = {
            0: (586, 586),
            1: (10, 50),
            2: (250, 587),
            3: (1, 20)
        }

        for bot in self.userbase:
            invest_ratio = rd.uniform(0.60, 0.85) if bot.tier in (0, 1) else rd.uniform(0.10, 0.60)
            budget_to_invest = bot.liquidity * invest_ratio
            remaining_cash = bot.liquidity - budget_to_invest

            nb_stocks = min(len(all_stocks), rd.randint(bot_tier_doer_of_magic[bot.tier][0], bot_tier_doer_of_magic[bot.tier][1]))
            chosen_stocks = rd.sample(all_stocks, nb_stocks)

            wallet = {}
            budget_per_stock = budget_to_invest / nb_stocks

            for stock in chosen_stocks:
                max_by_cash = int(budget_per_stock // stock.price)
                max_by_cap = int(stock.shares * 0.20)  # Plafond de 20 % par acteur

                qty = min(max_by_cash, stock.available_shares, max_by_cap)

                if qty > 0:
                    wallet[stock.ticker] = qty
                    stock.available_shares -= qty
                    remaining_cash += budget_per_stock - (qty * stock.price)
                else:
                    remaining_cash += budget_per_stock

                bot.avg_cost[stock.ticker].append(stock.price)  

            bot.wallet_setter(wallet)
            bot.cash_setter(round(remaining_cash, 2))