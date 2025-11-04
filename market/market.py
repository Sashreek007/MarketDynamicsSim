"""
Market Class with Dynamic Pricing and Market Cap

This module implements the market/exchange that:
- Manages order books for each stock using order-matching library
- Dynamically updates prices based on supply/demand
- Dynamically updates market cap (price × shares)
- Tracks volume, volatility, and market metrics
- Logs all activity to database
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import random
import numpy as np

from order_matching.matching_engine import MatchingEngine
from order_matching.order import LimitOrder, MarketOrder
from order_matching.orders import Orders
from order_matching.side import Side

from database.db_manager import DatabaseManager


class Stock:
    """Represents a single stock with its market data."""

    def __init__(self, ticker: str, initial_price: float,
                 total_shares: float, market_cap: float):
        """
        Initialize a stock.

        Args:
            ticker: Stock ticker symbol
            initial_price: Starting price
            total_shares: Total shares outstanding
            market_cap: Initial market capitalization
        """
        self.ticker = ticker
        self.initial_price = initial_price
        self.current_price = initial_price
        self.total_shares = total_shares
        self.market_cap = market_cap

        # Price history for volatility calculation
        self.price_history: List[float] = [initial_price]

        # Volume tracking
        self.buy_volume = 0.0
        self.sell_volume = 0.0
        self.daily_volume = 0.0

        # Volatility
        self.volatility = 0.02  # Start with 2% volatility

        # Price change tracking
        self.last_price = initial_price
        self.price_change_pct = 0.0

    def update_price(self, new_price: float):
        """
        Update stock price and recalculate market cap.

        Args:
            new_price: New price for the stock
        """
        self.last_price = self.current_price
        self.current_price = new_price

        # Update market cap dynamically
        self.market_cap = self.current_price * self.total_shares

        # Update price change percentage
        self.price_change_pct = (self.current_price - self.last_price) / self.last_price

        # Add to price history
        self.price_history.append(new_price)

        # Keep only last 20 prices for volatility calculation
        if len(self.price_history) > 20:
            self.price_history = self.price_history[-20:]

        # Recalculate volatility
        self._calculate_volatility()

    def _calculate_volatility(self):
        """Calculate volatility from recent price history."""
        if len(self.price_history) < 2:
            return

        # Calculate returns
        returns = []
        for i in range(1, len(self.price_history)):
            ret = (self.price_history[i] - self.price_history[i-1]) / self.price_history[i-1]
            returns.append(ret)

        # Volatility is standard deviation of returns
        if returns:
            self.volatility = np.std(returns)

    def add_volume(self, side: str, quantity: float):
        """Track trading volume."""
        if side.lower() == 'buy':
            self.buy_volume += quantity
        else:
            self.sell_volume += quantity
        self.daily_volume += quantity

    def get_market_data(self) -> Dict:
        """Get current market data for this stock."""
        return {
            'ticker': self.ticker,
            'price': self.current_price,
            'initial_price': self.initial_price,
            'market_cap': self.market_cap,
            'total_shares': self.total_shares,
            'buy_volume': self.buy_volume,
            'sell_volume': self.sell_volume,
            'volatility': self.volatility,
            'price_change_pct': self.price_change_pct,
        }


class Market:
    """
    Market/Exchange with dynamic pricing and order matching.

    Uses order-matching library for realistic order execution and
    implements dynamic price discovery and market cap updates.
    """

    def __init__(self, stocks_config: Dict[str, Dict], db_manager: DatabaseManager,
                 price_impact_factor: float = 0.1, base_volatility: float = 0.02):
        """
        Initialize the market.

        Args:
            stocks_config: Dict of ticker -> {price, market_cap, total_shares}
            db_manager: Database manager for logging
            price_impact_factor: How much trades impact price
            base_volatility: Base market volatility
        """
        self.db_manager = db_manager
        self.price_impact_factor = price_impact_factor
        self.base_volatility = base_volatility

        # Initialize stocks
        self.stocks: Dict[str, Stock] = {}
        for ticker, config in stocks_config.items():
            self.stocks[ticker] = Stock(
                ticker=ticker,
                initial_price=config['price'],
                total_shares=config['total_shares'],
                market_cap=config['market_cap']
            )

        # Initialize matching engines (one per stock)
        self.matching_engines: Dict[str, MatchingEngine] = {}
        for ticker in self.stocks.keys():
            self.matching_engines[ticker] = MatchingEngine(seed=42)

        # Market timestamp
        self.timestamp = datetime.now()
        self.order_counter = 0

        # Market-wide effects
        self.market_sentiment = 0.0  # -1 to 1
        self.circuit_breaker_active = False

    def place_order(self, ticker: str, trader_id: str, side: str,
                   quantity: float, order_type: str = 'market',
                   price: float = 0.0, sim_time: float = 0.0) -> Dict:
        """
        Place an order on the market.

        Args:
            ticker: Stock ticker
            trader_id: ID of trader placing order
            side: 'buy' or 'sell'
            quantity: Number of shares
            order_type: 'market' or 'limit'
            price: Limit price (ignored for market orders)
            sim_time: Current simulation time

        Returns:
            Dict with execution results
        """
        # Check circuit breaker
        if self.circuit_breaker_active:
            return {
                'success': False,
                'error': 'Circuit breaker active - trading halted'
            }

        # Validate inputs
        if ticker not in self.stocks:
            return {'success': False, 'error': f'Unknown ticker: {ticker}'}

        if quantity <= 0:
            return {'success': False, 'error': 'Quantity must be positive'}

        # Create order
        self.order_counter += 1
        order_id = f"{trader_id}_{ticker}_{self.order_counter}"

        order_side = Side.BUY if side.lower() == 'buy' else Side.SELL

        if order_type.lower() == 'limit':
            if price <= 0:
                return {'success': False, 'error': 'Limit price must be positive'}
            order = LimitOrder(
                side=order_side,
                price=price,
                size=quantity,
                timestamp=self.timestamp,
                order_id=order_id,
                trader_id=trader_id
            )
        else:  # market order
            order = MarketOrder(
                side=order_side,
                size=quantity,
                timestamp=self.timestamp,
                order_id=order_id,
                trader_id=trader_id
            )

        # Execute order through matching engine
        try:
            orders_wrapper = Orders([order])
            executed_trades = self.matching_engines[ticker].match(
                timestamp=self.timestamp,
                orders=orders_wrapper
            )

            trades = executed_trades.trades

            if trades:
                # Process executed trades
                total_quantity = sum(trade.size for trade in trades)
                total_value = sum(trade.price * trade.size for trade in trades)
                average_price = total_value / total_quantity if total_quantity > 0 else 0

                # Update stock price based on trade
                self._update_price_from_trade(ticker, side, total_quantity, average_price)

                # Track volume
                self.stocks[ticker].add_volume(side, total_quantity)

                # Log to database
                self.db_manager.log_trade(
                    timestamp=self.timestamp.timestamp(),
                    sim_time=sim_time,
                    ticker=ticker,
                    trader_id=trader_id,
                    side=side,
                    quantity=total_quantity,
                    price=average_price,
                    order_type=order_type,
                    execution_type=trades[0].execution.name if trades else None
                )

                return {
                    'success': True,
                    'executed': True,
                    'quantity_filled': total_quantity,
                    'average_price': average_price,
                    'num_trades': len(trades),
                    'total_value': total_value
                }
            else:
                # Order placed but not executed (limit order in book)
                return {
                    'success': True,
                    'executed': False,
                    'message': 'Order placed in book but not filled'
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _update_price_from_trade(self, ticker: str, side: str,
                                 quantity: float, trade_price: float):
        """
        Update stock price based on executed trade using supply/demand dynamics.

        Price impact is based on:
        - Trade size relative to typical volume
        - Direction (buy pushes up, sell pushes down)
        - Current volatility
        - Market sentiment
        """
        stock = self.stocks[ticker]

        # Calculate price impact
        # Larger trades have more impact
        typical_volume = 1000  # Base volume for comparison
        volume_ratio = quantity / typical_volume

        # Direction: buy = positive, sell = negative
        direction = 1 if side.lower() == 'buy' else -1

        # Base price impact
        base_impact = self.price_impact_factor * volume_ratio * direction

        # Adjust for volatility (more volatile = more price movement)
        volatility_multiplier = 1 + (stock.volatility / self.base_volatility)

        # Adjust for market sentiment
        sentiment_adjustment = self.market_sentiment * 0.1 * direction

        # Calculate total price change
        price_change_pct = (base_impact * volatility_multiplier) + sentiment_adjustment

        # Apply change to current price
        new_price = stock.current_price * (1 + price_change_pct)

        # Ensure price doesn't go negative, zero, or infinity
        if not (0 < new_price < float('inf')):
            new_price = stock.current_price  # Keep current price if invalid

        # Limit price movements to prevent extreme changes
        max_increase = stock.current_price * 1.10  # Max 10% increase at once
        min_decrease = stock.current_price * 0.90  # Max 10% decrease at once

        new_price = max(min_decrease, min(new_price, max_increase))

        # Absolute minimum price floor
        new_price = max(1.0, new_price)

        # Update the stock price (this also updates market cap)
        stock.update_price(new_price)

        # Check for circuit breaker conditions
        self._check_circuit_breaker(ticker)

    def _check_circuit_breaker(self, ticker: str):
        """
        Check if circuit breaker should be triggered.

        Halts trading if price moves >20% in a short period.
        """
        stock = self.stocks[ticker]

        # Check price change from initial
        price_change = (stock.current_price - stock.initial_price) / stock.initial_price

        if abs(price_change) > 0.20:  # 20% circuit breaker
            self.circuit_breaker_active = True

    def apply_market_wide_shock(self, magnitude: float, sim_time: float):
        """
        Apply a market-wide price shock (e.g., news event).

        Args:
            magnitude: Price change as decimal (-0.05 = -5% shock)
            sim_time: Current simulation time
        """
        for ticker, stock in self.stocks.items():
            new_price = stock.current_price * (1 + magnitude)
            new_price = max(0.01, new_price)  # Prevent negative prices
            stock.update_price(new_price)

        # Log market event
        self.db_manager.log_market_event(
            timestamp=self.timestamp.timestamp(),
            sim_time=sim_time,
            event_type='market_shock',
            description=f'Market-wide shock: {magnitude:+.1%}',
            affected_tickers=list(self.stocks.keys()),
            impact_magnitude=magnitude
        )

    def apply_stock_specific_news(self, ticker: str, magnitude: float, sim_time: float):
        """
        Apply a stock-specific news event.

        Args:
            ticker: Stock ticker
            magnitude: Price impact as decimal
            sim_time: Current simulation time
        """
        if ticker in self.stocks:
            stock = self.stocks[ticker]
            new_price = stock.current_price * (1 + magnitude)
            new_price = max(0.01, new_price)
            stock.update_price(new_price)

            # Log event
            self.db_manager.log_market_event(
                timestamp=self.timestamp.timestamp(),
                sim_time=sim_time,
                event_type='stock_news',
                description=f'{ticker} news event: {magnitude:+.1%}',
                affected_tickers=[ticker],
                impact_magnitude=magnitude
            )

    def update_market_sentiment(self, new_sentiment: float, sim_time: float):
        """
        Update overall market sentiment.

        Args:
            new_sentiment: New sentiment value (-1 to 1)
            sim_time: Current simulation time
        """
        old_sentiment = self.market_sentiment
        self.market_sentiment = max(-1.0, min(1.0, new_sentiment))

        self.db_manager.log_market_event(
            timestamp=self.timestamp.timestamp(),
            sim_time=sim_time,
            event_type='sentiment_change',
            description=f'Market sentiment: {old_sentiment:.2f} -> {self.market_sentiment:.2f}',
            impact_magnitude=self.market_sentiment
        )

    def reset_circuit_breaker(self):
        """Reset circuit breaker to resume trading."""
        self.circuit_breaker_active = False

    def get_current_price(self, ticker: str) -> float:
        """Get current price for a stock."""
        return self.stocks[ticker].current_price if ticker in self.stocks else 0.0

    def get_current_prices(self) -> Dict[str, float]:
        """Get current prices for all stocks."""
        return {ticker: stock.current_price for ticker, stock in self.stocks.items()}

    def get_market_data(self, ticker: str) -> Dict:
        """Get comprehensive market data for a stock."""
        if ticker in self.stocks:
            data = self.stocks[ticker].get_market_data()
            data['market_sentiment'] = self.market_sentiment
            data['circuit_breaker_active'] = self.circuit_breaker_active
            data['sim_time'] = 0  # Will be updated by simulation
            return data
        return {}

    def get_all_market_data(self) -> Dict[str, Dict]:
        """Get market data for all stocks."""
        return {ticker: self.get_market_data(ticker) for ticker in self.stocks.keys()}

    def log_market_metrics(self, sim_time: float):
        """Log current market metrics to database."""
        for ticker, stock in self.stocks.items():
            self.db_manager.log_stock_metrics(
                timestamp=self.timestamp.timestamp(),
                sim_time=sim_time,
                ticker=ticker,
                price=stock.current_price,
                market_cap=stock.market_cap,
                total_shares=stock.total_shares,
                buy_volume=stock.buy_volume,
                sell_volume=stock.sell_volume,
                volatility=stock.volatility
            )

    def advance_time(self, hours: float = 1.0):
        """Advance market timestamp."""
        self.timestamp += timedelta(hours=hours)

    def get_market_summary(self) -> str:
        """Get a human-readable market summary."""
        summary_lines = ["=" * 70, "MARKET SUMMARY", "=" * 70]

        for ticker, stock in self.stocks.items():
            price_change = ((stock.current_price - stock.initial_price) /
                          stock.initial_price * 100)
            summary_lines.append(
                f"{ticker}: ${stock.current_price:.2f} ({price_change:+.2f}%) "
                f"| MCap: ${stock.market_cap/1e9:.2f}B | Vol: {stock.volatility:.2%}"
            )

        summary_lines.append("=" * 70)
        return "\n".join(summary_lines)
