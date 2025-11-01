import warnings

warnings.filterwarnings("ignore", category=FutureWarning, module="pandera")

from datetime import datetime, timedelta
from order_matching.order_book import OrderBook
from order_matching.matching_engine import MatchingEngine
from order_matching.side import Side
from order_matching.order import Order
from order_matching.orders import Orders
from order_matching.order import LimitOrder
from order_matching.order import MarketOrder
from order_matching.trade import Trade
import numpy as np
from typing import Dict, List, Tuple, Optional
from pprint import pp
import random
import time


class Exchange:
    def __init__(self, tickers: List[str], initial_prices: Dict[str, float]):
        self.tickers = tickers
        self.matching_engines = {}
        self.order_books = {}
        self.last_prices = initial_prices.copy()
        self.trade_history = []
        self.orders = {}
        self.order_counter = 0
        self.timestamp = datetime.now()
        self.buy_volume = {ticker: 0 for ticker in tickers}
        self.sell_volume = {ticker: 0 for ticker in tickers}

        for ticker in tickers:
            self.matching_engines[ticker] = MatchingEngine(seed=42)
            self.orders[ticker] = Orders()

        print(f"Exchange initialized with {len(tickers)} stocks")
        for ticker, price in initial_prices.items():
            print(f"{ticker}: ${price:.2f}")

    def place_order(
        self,
        ticker: str,
        trader_id: str,
        side: str,  # buy or sell
        quantity: float,
        order_type: str = "market",
        price: float = 0.0,
    ):
        self.order_counter += 1
        order_id = f"{trader_id}_{ticker}_{self.order_counter}"

        if ticker not in self.matching_engines:
            return {"success": False, "error": f"Unkown ticker: {ticker}"}
        if quantity <= 0:
            return {"success": False, "error": "Quanity must be positive"}
        if side.lower() == "buy":
            order_side = Side.BUY
        elif side.lower() == "sell":
            order_side = Side.SELL
        else:
            return "Either Sell or Buy"

        if order_type.lower() == "limit":
            if price <= 0:
                return
            order = LimitOrder(
                side=order_side,
                price=price,
                size=quantity,
                timestamp=self.timestamp,
                order_id=order_id,
                trader_id=trader_id,
            )
        elif order_type.lower() == "market":
            order = MarketOrder(
                side=order_side,
                size=quantity,
                timestamp=self.timestamp,
                order_id=order_id,
                trader_id=trader_id,
            )
        else:
            return
        orders_wrapper = Orders([order])
        try:
            # Execute matching
            executed_trades = self.matching_engines[ticker].match(
                timestamp=self.timestamp, orders=orders_wrapper
            )

            # Process the trades
            trades = executed_trades.trades

        #send them to a csv later 





if __name__ == "__main__":
    tickers = ["AAPL", "GOOGL"]
    initial_prices = {"AAPL": 180.0, "GOOGL": 140.0}

    exchange = Exchange(tickers, initial_prices)

    print(
        exchange.place_order("AAPL", "hi", "sell", 1, order_type="limit", price=180.0)
    )
    print(exchange.place_order("AAPL", "hdi", "buy", 1, order_type="market"))
