"""
Specific Trader Type Implementations

This module implements four distinct trader types:
1. AggressiveTrader - High frequency, momentum-based, large orders
2. ConservativeTrader - Low frequency, value-based, small orders
3. LossMakerTrader - Poor timing, buys high/sells low
4. LongTermTrader - Buy and hold, patient, infrequent large positions
"""

import random
from typing import Dict, Optional, Tuple
from .base_trader import BaseTrader


class AggressiveTrader(BaseTrader):
    """
    Aggressive Trader - High risk, high frequency momentum trader.

    Characteristics:
    - Trades frequently (70% probability)
    - Larger order sizes (up to 10% of capital)
    - Momentum-based: buys when price is rising, sells when falling
    - Uses limit orders strategically
    - Higher risk tolerance
    """

    def decide_trade(self, ticker: str, current_price: float,
                    market_data: Dict) -> Optional[Tuple[str, str, float, float]]:
        """
        Aggressive trading strategy: momentum-based with large orders.

        Buys when detecting upward momentum, sells when detecting downward momentum.
        """
        if not self.should_trade():
            return None

        # Validate price - skip if invalid
        if not (0 < current_price < float('inf')):
            return None

        # Get market data
        price_change = market_data.get('price_change_pct', 0.0)
        volatility = market_data.get('volatility', 0.02)
        buy_volume = market_data.get('buy_volume', 0)
        sell_volume = market_data.get('sell_volume', 0)
        sim_time = market_data.get('sim_time', 0)

        # Calculate momentum signal
        volume_ratio = (buy_volume / (sell_volume + 1))  # Avoid division by zero

        # Early in simulation, establish positions with some random trading
        if sim_time < 1.0 and random.random() < 0.3:
            # Random initial position building
            max_capital_to_use = self.cash * random.uniform(0.05, 0.10)
            quantity = int(max_capital_to_use / current_price)
            if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                return (ticker, 'buy', quantity, 0.0)  # Market order

        # Aggressive momentum following
        # Buy on upward momentum
        if price_change > 0.005 or volume_ratio > 1.2:
            # Calculate aggressive order size (5-10% of capital)
            max_capital_to_use = self.cash * random.uniform(0.05, 0.10)
            quantity = int(max_capital_to_use / current_price)

            if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                # Use limit order slightly above current price (aggressive)
                limit_price = current_price * 1.001  # 0.1% above market
                return (ticker, 'buy', quantity, limit_price)

        # Sell on downward momentum or to take profits
        elif price_change < -0.003 or volume_ratio < 0.8:
            current_holdings = self.holdings.get(ticker, 0)
            if current_holdings > 0:
                # Sell a significant portion (30-60%)
                quantity = int(current_holdings * random.uniform(0.3, 0.6))
                if quantity > 0:
                    # Use limit order slightly below current price
                    limit_price = current_price * 0.999  # 0.1% below market
                    return (ticker, 'sell', quantity, limit_price)

        # Also consider profit taking
        if ticker in self.cost_basis:
            unrealized_gain = (current_price - self.cost_basis[ticker]) / self.cost_basis[ticker]
            # Take profits if up 5% or more
            if unrealized_gain > 0.05 and random.random() < 0.3:
                current_holdings = self.holdings.get(ticker, 0)
                if current_holdings > 0:
                    quantity = int(current_holdings * random.uniform(0.2, 0.4))
                    if quantity > 0:
                        return (ticker, 'sell', quantity, 0.0)  # Market order

        return None


class ConservativeTrader(BaseTrader):
    """
    Conservative Trader - Low risk, value-focused, patient trader.

    Characteristics:
    - Trades infrequently (30% probability)
    - Smaller order sizes (2-5% of capital)
    - Value-based: buys on dips, sells on highs
    - Uses limit orders for better prices
    - Lower risk tolerance
    - Maintains diversified portfolio
    """

    def decide_trade(self, ticker: str, current_price: float,
                    market_data: Dict) -> Optional[Tuple[str, str, float, float]]:
        """
        Conservative trading strategy: value-based with small orders.

        Buys on dips (potential value), sells on peaks (risk management).
        """
        if not self.should_trade():
            return None

        # Validate price - skip if invalid
        if not (0 < current_price < float('inf')):
            return None

        # Get market data
        price_change = market_data.get('price_change_pct', 0.0)
        volatility = market_data.get('volatility', 0.02)
        initial_price = market_data.get('initial_price', current_price)

        # Calculate value metrics
        price_vs_initial = (current_price - initial_price) / initial_price

        # Buy on significant dips (value opportunity)
        if price_change < -0.01 or price_vs_initial < -0.03:
            # Conservative position sizing (2-5% of capital)
            max_capital_to_use = self.cash * random.uniform(0.02, 0.05)
            quantity = int(max_capital_to_use / current_price)

            if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                # Use limit order below current price (patient)
                limit_price = current_price * 0.998  # 0.2% below market
                return (ticker, 'buy', quantity, limit_price)

        # Sell on high valuations or to reduce risk
        elif price_vs_initial > 0.05:  # Up 5% from initial
            current_holdings = self.holdings.get(ticker, 0)
            if current_holdings > 0:
                # Sell small portion to lock in gains (10-25%)
                quantity = int(current_holdings * random.uniform(0.1, 0.25))
                if quantity > 0:
                    # Use limit order above current price (patient)
                    limit_price = current_price * 1.002  # 0.2% above market
                    return (ticker, 'sell', quantity, limit_price)

        # Risk management: sell if position has grown too large
        portfolio_value = self.get_portfolio_value({ticker: current_price})
        if portfolio_value > 0:
            position_size = (self.holdings.get(ticker, 0) * current_price) / portfolio_value
            if position_size > 0.3:  # More than 30% in one stock
                current_holdings = self.holdings.get(ticker, 0)
                quantity = int(current_holdings * 0.2)  # Reduce by 20%
                if quantity > 0:
                    return (ticker, 'sell', quantity, 0.0)  # Market order

        return None


class LossMakerTrader(BaseTrader):
    """
    LossMaker Trader - Poor timing, bad decisions, buys high/sells low.

    Characteristics:
    - Trades very frequently (80% probability)
    - Poor timing: buys after rallies, sells after drops
    - Panic sells on volatility
    - FOMO buys (fear of missing out)
    - Doesn't use stop losses effectively
    - Chases performance
    """

    def decide_trade(self, ticker: str, current_price: float,
                    market_data: Dict) -> Optional[Tuple[str, str, float, float]]:
        """
        LossMaker strategy: consistently bad timing and decisions.

        This trader does the opposite of what they should do.
        """
        if not self.should_trade():
            return None

        # Validate price - skip if invalid
        if not (0 < current_price < float('inf')):
            return None

        # Get market data
        price_change = market_data.get('price_change_pct', 0.0)
        volatility = market_data.get('volatility', 0.02)
        sim_time = market_data.get('sim_time', 0)

        # Impulsive random trades (LossMaker is impulsive!)
        if random.random() < 0.2:
            max_capital_to_use = self.cash * random.uniform(0.05, 0.15)
            quantity = int(max_capital_to_use / current_price)
            if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                return (ticker, 'buy', quantity, 0.0)  # Market order

        # BAD DECISION 1: Buy after price has already gone up (FOMO)
        if price_change > 0.01:  # Buy high
            max_capital_to_use = self.cash * random.uniform(0.05, 0.15)
            quantity = int(max_capital_to_use / current_price)

            if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                # Pay even more (market order that executes at ask)
                return (ticker, 'buy', quantity, 0.0)  # Market order

        # BAD DECISION 2: Panic sell after price drops
        elif price_change < -0.008:  # Sell low
            current_holdings = self.holdings.get(ticker, 0)
            if current_holdings > 0:
                # Panic sell large portion
                quantity = int(current_holdings * random.uniform(0.4, 0.7))
                if quantity > 0:
                    # Sell at market (accepting lower price)
                    return (ticker, 'sell', quantity, 0.0)  # Market order

        # BAD DECISION 3: Sell winners too early, hold losers
        if ticker in self.cost_basis:
            unrealized_gain_pct = (current_price - self.cost_basis[ticker]) / self.cost_basis[ticker]

            # Sell winning positions too early (small gain)
            if 0.02 < unrealized_gain_pct < 0.04 and random.random() < 0.4:
                current_holdings = self.holdings.get(ticker, 0)
                if current_holdings > 0:
                    # Sell most of position
                    quantity = int(current_holdings * random.uniform(0.5, 0.8))
                    if quantity > 0:
                        return (ticker, 'sell', quantity, 0.0)

            # Hold losing positions (hope they recover)
            # This is modeled by NOT selling when down

        # BAD DECISION 4: Random impulsive trades on high volatility
        if volatility > 0.03 and random.random() < 0.3:
            if random.random() < 0.5:  # Random buy
                max_capital_to_use = self.cash * random.uniform(0.03, 0.08)
                quantity = int(max_capital_to_use / current_price)
                if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                    return (ticker, 'buy', quantity, 0.0)
            else:  # Random sell
                current_holdings = self.holdings.get(ticker, 0)
                if current_holdings > 0:
                    quantity = int(current_holdings * random.uniform(0.2, 0.5))
                    if quantity > 0:
                        return (ticker, 'sell', quantity, 0.0)

        return None


class LongTermTrader(BaseTrader):
    """
    Long-Term Trader - Buy and hold, patient, strategic investor.

    Characteristics:
    - Trades very infrequently (20% probability)
    - Larger positions when they do trade (8-15% of capital)
    - Focuses on accumulation over time
    - Rarely sells (only for rebalancing)
    - Holds through volatility
    - Strategic, not reactive
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Track target allocation per stock
        self.target_allocation: Dict[str, float] = {}
        self.last_trade_time: Dict[str, float] = {}

    def decide_trade(self, ticker: str, current_price: float,
                    market_data: Dict) -> Optional[Tuple[str, str, float, float]]:
        """
        Long-term strategy: buy and hold with strategic accumulation.

        Focuses on building positions over time and holding through volatility.
        """
        if not self.should_trade():
            return None

        # Validate price - skip if invalid
        if not (0 < current_price < float('inf')):
            return None

        # Get market data
        sim_time = market_data.get('sim_time', 0)
        price_change = market_data.get('price_change_pct', 0.0)
        initial_price = market_data.get('initial_price', current_price)

        # Calculate current position
        current_holdings = self.holdings.get(ticker, 0)
        holdings_value = current_holdings * current_price
        portfolio_value = self.get_portfolio_value({ticker: current_price})

        # Initialize target allocation if not set (aim for 20-25% per stock)
        if ticker not in self.target_allocation:
            self.target_allocation[ticker] = random.uniform(0.20, 0.25)

        current_allocation = holdings_value / portfolio_value if portfolio_value > 0 else 0
        target = self.target_allocation[ticker]

        # ACCUMULATION STRATEGY: Slowly build to target allocation
        if current_allocation < target:
            # Buy on any weakness (patient accumulation)
            if price_change <= 0 or random.random() < 0.3:
                # Calculate how much to buy to move toward target
                target_value = portfolio_value * target
                needed_value = target_value - holdings_value
                max_buy = self.cash * 0.15  # Max 15% of cash at once

                capital_to_use = min(needed_value, max_buy)
                quantity = int(capital_to_use / current_price)

                if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                    # Use limit order to get good price
                    limit_price = current_price * 0.997  # 0.3% below market
                    self.last_trade_time[ticker] = sim_time
                    return (ticker, 'buy', quantity, limit_price)

        # REBALANCING: Sell if allocation gets too high
        elif current_allocation > target * 1.5:  # 50% over target
            # Trim position back to target
            target_value = portfolio_value * target
            excess_value = holdings_value - target_value
            quantity = int(excess_value / current_price)

            if quantity > 0:
                # Use limit order to get good price
                limit_price = current_price * 1.003  # 0.3% above market
                return (ticker, 'sell', quantity, limit_price)

        # OPPORTUNISTIC BUYING: Major dips are buying opportunities
        price_vs_initial = (current_price - initial_price) / initial_price
        if price_vs_initial < -0.10:  # Down 10% from initial
            # This is a buying opportunity regardless of allocation
            max_capital_to_use = self.cash * random.uniform(0.08, 0.12)
            quantity = int(max_capital_to_use / current_price)

            if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                limit_price = current_price * 0.995  # 0.5% below market
                return (ticker, 'buy', quantity, limit_price)

        # Generally don't sell - buy and hold philosophy
        # Only sell for rebalancing (handled above)

        return None
