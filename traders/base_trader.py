"""
Base Trader Class

This module defines the base trader class that all specific trader types inherit from.
Each trader has their own portfolio, trading strategy, and behavior patterns.
"""

import random
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod


class BaseTrader(ABC):
    """
    Abstract base class for all trader types.

    All traders must implement the decide_trade method which determines
    their trading behavior based on market conditions.
    """

    def __init__(self, trader_id: str, initial_capital: float,
                 trade_probability: float, config: Optional[Dict] = None):
        """
        Initialize a trader.

        Args:
            trader_id: Unique identifier for the trader
            initial_capital: Starting cash balance
            trade_probability: Probability of trading when given opportunity (0-1)
            config: Additional configuration parameters
        """
        self.trader_id = trader_id
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.holdings: Dict[str, float] = {}  # ticker -> quantity
        self.trade_probability = trade_probability
        self.config = config or {}

        # Trading history for performance tracking
        self.trades_executed = 0
        self.total_buy_volume = 0.0
        self.total_sell_volume = 0.0
        self.realized_pnl = 0.0
        self.cost_basis: Dict[str, float] = {}  # ticker -> average cost

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio value (cash + holdings).

        Args:
            current_prices: Dictionary of ticker -> current price

        Returns:
            Total portfolio value
        """
        holdings_value = sum(
            qty * current_prices.get(ticker, 0.0)
            for ticker, qty in self.holdings.items()
        )
        return self.cash + holdings_value

    def get_holdings_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate value of all stock holdings."""
        return sum(
            qty * current_prices.get(ticker, 0.0)
            for ticker, qty in self.holdings.items()
        )

    def can_afford(self, ticker: str, quantity: float, price: float) -> bool:
        """Check if trader can afford a purchase."""
        # Safety checks for invalid prices or quantities
        if price <= 0 or not (0 < price < float('inf')):
            return False
        if quantity <= 0 or not (0 < quantity < float('inf')):
            return False

        total_cost = quantity * price
        return self.cash >= total_cost and total_cost < float('inf')

    def has_shares(self, ticker: str, quantity: float) -> bool:
        """Check if trader has enough shares to sell."""
        return self.holdings.get(ticker, 0.0) >= quantity

    def execute_buy(self, ticker: str, quantity: float, price: float) -> bool:
        """
        Execute a buy order (update portfolio).

        Args:
            ticker: Stock ticker
            quantity: Number of shares
            price: Price per share

        Returns:
            True if successful, False otherwise
        """
        total_cost = quantity * price

        # Validate total_cost
        if not (0 < total_cost < float('inf')):
            return False

        if not self.can_afford(ticker, quantity, price):
            return False

        # Update cash
        self.cash -= total_cost

        # Ensure cash stays valid (should always be >= 0 after buy)
        if self.cash < 0 or not (self.cash < float('inf')):
            self.cash = 0
            return False

        # Update holdings
        current_qty = self.holdings.get(ticker, 0.0)
        current_cost_basis = self.cost_basis.get(ticker, 0.0)

        # Calculate new average cost basis
        if current_qty > 0:
            total_cost_basis = (current_qty * current_cost_basis) + total_cost
            new_qty = current_qty + quantity
            self.cost_basis[ticker] = total_cost_basis / new_qty
        else:
            self.cost_basis[ticker] = price

        self.holdings[ticker] = current_qty + quantity

        # Update statistics
        self.trades_executed += 1
        self.total_buy_volume += total_cost

        return True

    def execute_sell(self, ticker: str, quantity: float, price: float) -> bool:
        """
        Execute a sell order (update portfolio).

        Args:
            ticker: Stock ticker
            quantity: Number of shares
            price: Price per share

        Returns:
            True if successful, False otherwise
        """
        if not self.has_shares(ticker, quantity):
            return False

        total_proceeds = quantity * price

        # Validate total_proceeds
        if not (0 < total_proceeds < float('inf')):
            return False

        # Update cash
        self.cash += total_proceeds

        # Ensure cash stays valid
        if not (0 <= self.cash < float('inf')):
            self.cash = self.initial_capital  # Reset to initial if corrupted
            return False

        # Update holdings
        current_qty = self.holdings.get(ticker, 0.0)
        self.holdings[ticker] = current_qty - quantity

        # Calculate realized P&L
        cost_basis = self.cost_basis.get(ticker, price)
        pnl = (price - cost_basis) * quantity
        self.realized_pnl += pnl

        # Remove from holdings if quantity is zero
        if self.holdings[ticker] == 0:
            del self.holdings[ticker]
            if ticker in self.cost_basis:
                del self.cost_basis[ticker]

        # Update statistics
        self.trades_executed += 1
        self.total_sell_volume += total_proceeds

        return True

    def should_trade(self) -> bool:
        """
        Determine if trader should attempt to trade based on probability.

        Returns:
            True if trader should trade, False otherwise
        """
        return random.random() < self.trade_probability

    @abstractmethod
    def decide_trade(self, ticker: str, current_price: float,
                    market_data: Dict) -> Optional[Tuple[str, str, float, float]]:
        """
        Decide whether to trade and what to trade (must be implemented by subclasses).

        Args:
            ticker: Stock ticker to consider
            current_price: Current price of the stock
            market_data: Additional market information (volatility, volume, etc.)

        Returns:
            Tuple of (ticker, side, quantity, price) if trading, None otherwise
            - side: 'buy' or 'sell'
            - quantity: number of shares
            - price: limit price (0 for market order)
        """
        pass

    def get_unrealized_pnl(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate unrealized profit/loss on current holdings.

        Args:
            current_prices: Dictionary of ticker -> current price

        Returns:
            Total unrealized P&L
        """
        unrealized = 0.0
        for ticker, qty in self.holdings.items():
            if qty > 0:
                cost_basis = self.cost_basis.get(ticker, 0.0)
                current_price = current_prices.get(ticker, 0.0)
                unrealized += (current_price - cost_basis) * qty
        return unrealized

    def get_total_pnl(self, current_prices: Dict[str, float]) -> float:
        """Get total P&L (realized + unrealized)."""
        return self.realized_pnl + self.get_unrealized_pnl(current_prices)

    def get_return(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total return as a percentage.

        Returns:
            Return as decimal (0.10 = 10% gain)
        """
        total_value = self.get_portfolio_value(current_prices)
        return (total_value - self.initial_capital) / self.initial_capital

    def __repr__(self) -> str:
        """String representation of trader."""
        return (f"{self.__class__.__name__}(id={self.trader_id}, "
                f"cash=${self.cash:,.2f}, holdings={len(self.holdings)})")
