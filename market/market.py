import pandas as pd
import random
import json
import math
from assets import Assets


class Stock:
    def __init__(
        self,
        name,
        ticker,
        shares,
        price,
        history,
        currency="USD",
        tags=None,
        volatility=0.02,
        drift=0.0003,
    ):
        self.name = name
        self.ticker = ticker
        self.tags = tags
        self.currency = currency
        self.price = float(price)
        self.shares = int(shares)
        self.available_shares = shares
        self.volatility = volatility
        self.drift = drift
        self.impact = 15 * self.volatility * (8000000000 / max(self.market_cap, 1000000)) ** 0.25

        self.history = history

        self.base_price = self.price

        if isinstance(history, pd.Series):
            self.history = history.ffill().bfill().tolist()
        else:
            self.history = list(history)

        self.bought = 0
        self.sold = 0

    # Acheter
    def buy(self, qty):
        self.bought += qty
        self.available_shares = max(0, self.available_shares - qty)

    # Vendre
    def sell(self, qty):
        self.sold += qty
        self.available_shares = min(self.shares, self.available_shares + qty)

    # Calculer le nouveau prix de l'action
    def update(self):
        capped_drift = max(-0.0008, min(0.0008, self.drift))
        gbm_shock = (capped_drift - 0.5 * (self.volatility ** 2)) + random.gauss(0, self.volatility)
        daily_growth = 1.10 ** (1 / 365)
        self.base_price = max(0.01, self.base_price * math.exp(gbm_shock) * daily_growth)

        net_demand = (self.bought - self.sold) / self.shares
        raw_impact = self.impact * net_demand
        max_daily_impact = max(0.08, 6.0 * self.volatility)
        damped_impact = max_daily_impact * math.tanh(raw_impact / max_daily_impact)

        reversion_speed = 0.05
        log_mispricing = math.log(self.base_price / max(self.price, 0.01))
        mean_reversion = reversion_speed * log_mispricing

        raw_total_return = gbm_shock + damped_impact + mean_reversion
        max_total_move = max(0.15, 10.0 * self.volatility)
        final_return = max_total_move * math.tanh(raw_total_return / max_total_move)

        self.price = max(0.01, self.price * (1.0 + final_return))
        self.history.append(self.price)
        self.bought = self.sold = 0

    # Retourner la capitalisation
    @property
    def market_cap(self):
        return self.price * self.shares

    # Pour des tests
    def __repr__(self):
        return f"Stock(name={self.name}, price={self.price} {self.currency}, shares={self.shares}, market_cap={self.market_cap})"


class Market:
    def __init__(self, size):
        self.size = size
        self.assets = Assets("market")
        self.stocks = self.create_stocks(self.size)  # Dictionnaire des actions

    # Les actions sont créées à partir de vraies données. Ces données incluent :
    # S&P500, TSX60, NASDAQ100, et 10 cryptomonnaies.
    def create_stocks(self, size):
        with open(self.assets.getAssetPath("stocks.json"), "r") as f:
            stocks = json.load(f)
        with open(self.assets.getAssetPath("prices.csv")) as f:
            prices = pd.read_csv(f)

        iter = random.sample(stocks, k=size)

        data = {}

        for i in iter:
            data[i["ticker"]] = Stock(
                i["name"],
                i["ticker"],
                i["shares"],
                i["price"],
                prices[i["ticker"]],
                i["currency"],
                i["tags"],
                i["volatility"],
                i["drift"],
            )

        return data

    # Mettre tout le market à jour
    def update(self):
        for stock in self.stocks.values():
            stock.update()

    # Définir les prix pour la database
    def setPrices(self, prices):
        if not prices:
            return

        for t, price in prices.items():
            self.stocks[t].price = price

    # Pour synchroniser les historiques
    def addHist(self, lastHist):
        if not lastHist:
            return

        for t, price in lastHist.items():
            self.stocks[t].history.append(price)

    # Prendre une copie du marché à cet instant
    def snapshot(self):
        return {
            t: {
                "name": s.name,
                "shares": s.shares,
                "currency": s.currency,
                "tags": s.tags,
                "volatility": s.volatility,
                "drift": s.drift,
                "impact": s.impact,
                "price": s.price,
                "history": [round(p, 4) for p in s.history],
            }
            for t, s in self.stocks.items()
        }

    # Charger une copie d'un marché
    def load_snapshot(self, stocks):
        self.stocks = {
            t: Stock(
                d["name"],
                t,
                d["shares"],
                d["price"],
                d["history"],
                d["currency"],
                d["tags"],
                d["volatility"],
                d["drift"],
            )
            for t, d in stocks.items()
        }

    # Faire avancer le marché d'une itération
    def apply_tick(self, prices):
        for t, price in prices.items():
            stock = self.stocks.get(t)
            if stock:
                stock.price = price
                stock.history.append(price)

    # Pour des tests
    def __repr__(self):
        return str(self.stocks)

    # Retourne les tickers (ex.: AAPL)
    def get_tickers(self):
        return sorted(list(self.stocks.keys()))

    # Retourne tous les noms des stocks du marché
    def get_names(self):
        return sorted([stock.name for stock in self.stocks.values()])

    # Trouver un stock avec son ticker
    def get_stock_by_ticker(self, ticker):
        return self.stocks.get(ticker, None)

    # Dans market view, les noms sont stockés sous la forme [nom] ([ticker]).
    # Cette méthode permet de chercher un stock avec ce format de nom
    def find_stock_by_long_name(self, name):
        # Format : A (A)

        index = name.find("(")
        ticker = name[index + 1 : -1]

        return self.get_stock_by_ticker(ticker)
