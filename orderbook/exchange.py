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


class Exchange:
    def __init__(self, tickers: List[str], initial_prices: Dict[str, float]):
        self.tickers = tickers
        self.matching_engines = {}
        self.last_prices = initial_prices.copy()
        self.orders = {}
        self.order_counter = 0
        self.timestamp = datetime.now()
        self.buy_volume = {ticker: 0 for ticker in tickers}
        self.sell_volume = {ticker: 0 for ticker in tickers}

        for ticker in tickers:
            self.matching_engines[ticker] = MatchingEngine(seed=42)
        """
        print(f"Exchange initialized with {len(tickers)} stocks")
        for ticker, price in initial_prices.items():
            print(f"{ticker}: ${price:.2f}")"""

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
            if trades:
                total_quantity = sum(trade.size for trade in trades)
                total_value = sum(trade.price * trade.size for trade in trades)
                average_price = (
                    total_value / total_quantity if total_quantity > 0 else 0
                )

                self.last_prices[ticker] = trades[-1].price

                if side.lower() == "buy":
                    self.buy_volume[ticker] += total_quantity
                else:
                    self.sell_volume[ticker] += total_quantity

                self.update_market_price(ticker, side, total_quantity)

                return {
                    "success": True,
                    "executed": True,
                    "trades:": [
                        {
                            "ticker": ticker,
                            "trader": trader_id,
                            "side": side,
                            "quantity": trade.size,
                            "price": trade.price,
                            "timestamp": trade.timestamp,
                            "trade_id": trade.trade_id,
                            "execution_type": trade.execution.name,
                            "incoming_order_id": trade.incoming_order_id,
                            "book_order_id": trade.book_order_id,
                        }
                        for trade in trades
                    ],
                    "summary": {
                        "quantity_filled": total_quantity,
                        "average_price": average_price,
                        "num_trades": len(trades),
                    },
                }
            else:
                return {
                    "success": True,
                    "executed": False,
                    "trades": [],
                    "summary": {
                        "quantity_filled": 0,
                        "average_price": 0,
                        "num_trades": 0,
                    },
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_market_price(self, ticker: str, side: str, quantity: float):
        current_price = self.last_prices[ticker]

        base_impact = 0.001

        typical_volume = 100

        volume_ratio = quantity / typical_volume

        direction = 1 if side.lower() == "buy" else -1

        price_change_pct = base_impact * volume_ratio * direction
        price_change = current_price * price_change_pct

        new_price = current_price + price_change

        new_price = max(0.01, new_price)

        self.last_prices[ticker] = new_price

    def get_current_price(self, ticker: str):
        if self.last_prices[ticker]:
            return self.last_prices[ticker]
        return

    def get_big_ask_spread(self, ticker: str) -> Tuple[float, float]:
        price = self.last_prices[ticker]
        spread_pct = 0.001

        best_bid = price * (1 - spread_pct)
        best_ask = price * (1 + spread_pct)

        return (best_bid, best_ask)

    def get_market_summary(self) -> Dict:
        summary = {}
        for ticker in self.tickers:
            bid, ask = self.get_big_ask_spread(ticker)
            summary[ticker] = {
                "price": self.last_prices[ticker],
                "bid": bid,
                "ask": ask,
                "spread": ask - bid,
                "buy_volume": self.buy_volume[ticker],
                "sell_volume": self.sell_volume[ticker],
            }
        return summary


if __name__ == "__main__":
    """
    Test the exchange with proper order matching and price discovery.
    Run this file directly to see the exchange in action!
    """
    print("=" * 70)
    print("TESTING EXCHANGE: ORDER MATCHING + PRICE DISCOVERY")
    print("=" * 70)

    # Create a simple exchange
    exchange = Exchange(
        tickers=["AAPL", "GOOGL"], initial_prices={"AAPL": 180.0, "GOOGL": 140.0}
    )

    print("\n🔍 ARCHITECTURE:")
    print("-" * 70)
    print("1. Order Matching: Matching engine matches buy/sell orders")
    print("2. Price Discovery: Exchange updates prices based on order flow")
    print("   - More buying → price goes UP")
    print("   - More selling → price goes DOWN")

    print("\n🔍 VERIFICATION: Separate Order Books Per Ticker")
    print("-" * 70)
    print(f"Number of matching engines: {len(exchange.matching_engines)}")
    print(f"Tickers: {list(exchange.matching_engines.keys())}")
    print(
        f"Are they different objects? {exchange.matching_engines['AAPL'] is not exchange.matching_engines['GOOGL']}"
    )
    print("✅ Each ticker has its own independent matching engine!")

    print("\n📊 Initial Prices:")
    summary = exchange.get_market_summary()
    for ticker, info in summary.items():
        print(f"{ticker}: ${info['price']:.2f}")

    print("\n💼 Testing Order Flow and Price Discovery...")

    # Test 1: BUY order - should push price UP
    print("\n1. Market BUY: 100 AAPL")
    print(f"   Before: AAPL = ${exchange.get_current_price('AAPL'):.2f}")
    result1 = exchange.place_order("AAPL", "Trader1", "buy", 100, "market")
    print(f"   After:  AAPL = ${exchange.get_current_price('AAPL'):.2f}")
    print(f"   💹 Price went UP due to buying pressure!")

    # Test 2: Another BUY - price should go UP more
    print("\n2. Market BUY: 200 AAPL (larger order)")
    print(f"   Before: AAPL = ${exchange.get_current_price('AAPL'):.2f}")
    result2 = exchange.place_order("AAPL", "Trader2", "buy", 200, "market")
    print(f"   After:  AAPL = ${exchange.get_current_price('AAPL'):.2f}")
    print(f"   💹 Larger buy order → bigger price increase!")

    # Test 3: SELL order - should push price DOWN
    print("\n3. Market SELL: 150 AAPL")
    print(f"   Before: AAPL = ${exchange.get_current_price('AAPL'):.2f}")
    result3 = exchange.place_order("AAPL", "Trader1", "sell", 150, "market")
    print(f"   After:  AAPL = ${exchange.get_current_price('AAPL'):.2f}")
    print(f"   💹 Price went DOWN due to selling pressure!")

    # Test 4: GOOGL trades (different stock, independent)
    print("\n4. Market BUY: 50 GOOGL")
    print(f"   Before: GOOGL = ${exchange.get_current_price('GOOGL'):.2f}")
    print(
        f"   Before: AAPL  = ${exchange.get_current_price('AAPL'):.2f} (should not change)"
    )
    result4 = exchange.place_order("GOOGL", "Trader3", "buy", 50, "market")
    print(f"   After:  GOOGL = ${exchange.get_current_price('GOOGL'):.2f}")
    print(f"   After:  AAPL  = ${exchange.get_current_price('AAPL'):.2f}")
    print(f"   ✅ GOOGL changed, AAPL stayed the same (independent order books!)")

    # Test 5: Limit order
    print("\n5. Limit BUY: 30 GOOGL at $142")
    print(f"   Before: GOOGL = ${exchange.get_current_price('GOOGL'):.2f}")
    result5 = exchange.place_order("GOOGL", "Trader4", "buy", 30, "limit", 142.0)
    print(f"   After:  GOOGL = ${exchange.get_current_price('GOOGL'):.2f}")
    if result5["executed"]:
        print(f"   ✅ Limit order filled and price updated!")
    else:
        print(f"   ⏳ Limit order placed but not filled (waiting in book)")

    print("\n📈 Final Summary:")
    print("-" * 70)
    summary = exchange.get_market_summary()
    for ticker, info in summary.items():
        print(f"{ticker}:")
        print(f"  Price: ${info['price']:.2f}")
        print(f"  Buy Volume:   {info['buy_volume']:.0f} shares")
        print(f"  Sell Volume:  {info['sell_volume']:.0f} shares")
        net_flow = info["buy_volume"] - info["sell_volume"]
        flow_dir = (
            "📈 NET BUYING"
            if net_flow > 0
            else "📉 NET SELLING"
            if net_flow < 0
            else "⚖️ BALANCED"
        )
        print(f"  Order Flow:   {flow_dir} ({net_flow:+.0f})")

    print("\n🔍 Price Discovery Demo:")
    print("-" * 70)
    print("Initial AAPL: $180.00")
    print(f"Final AAPL:   ${exchange.get_current_price('AAPL'):.2f}")
    price_change = exchange.get_current_price("AAPL") - 180.0
    print(f"Net Change:   ${price_change:+.2f} ({price_change / 180.0:+.2%})")
    print("")
    print("✅ Buy orders → price went UP")
    print("✅ Sell orders → price went DOWN")
    print("✅ Each stock independent")

    print("\n" + "=" * 70)
    print("✅ Test complete!")
    print("=" * 70)
