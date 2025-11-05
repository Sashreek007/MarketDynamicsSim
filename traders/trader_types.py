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
        if sim_time < 2.0 and random.random() < 0.2:
            # Random initial position building (reduced to 20% chance)
            max_capital_to_use = self.cash * random.uniform(0.03, 0.05)  # Smaller orders
            quantity = int(max_capital_to_use / current_price)
            if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                return (ticker, 'buy', quantity, 0.0)  # Market order

        current_holdings = self.holdings.get(ticker, 0)

        # AGGRESSIVE MOMENTUM STRATEGY: Ride winners, cut losers fast

        # Check current position P&L
        if current_holdings > 0 and ticker in self.cost_basis:
            pnl_pct = (current_price - self.cost_basis[ticker]) / self.cost_basis[ticker]

            # CUT LOSERS FAST (stop loss at -3%)
            if pnl_pct < -0.03:
                # Get out of losing positions quickly
                quantity = int(current_holdings * random.uniform(0.7, 1.0))  # Sell most/all
                if quantity > 0:
                    return (ticker, 'sell', quantity, 0.0)

            # TAKE BIG PROFITS on winners (let winners run to 10%+, then take profits)
            elif pnl_pct > 0.10:  # Up 10%+
                # Take some profits but keep riding
                quantity = int(current_holdings * random.uniform(0.3, 0.5))  # Sell 30-50%
                if quantity > 0:
                    return (ticker, 'sell', quantity, 0.0)

        # BUY on STRONG upward momentum (ride the trend)
        if price_change > 0.005 or volume_ratio > 1.3:  # Strong momentum
            if self.cash > current_price * 10:
                # Aggressive sizing on strong signals
                max_capital_to_use = self.cash * random.uniform(0.06, 0.12)
                quantity = int(max_capital_to_use / current_price)

                if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                    return (ticker, 'buy', quantity, 0.0)

        # SELL on downward momentum (trend reversal)
        if current_holdings > 0:
            if price_change < -0.005:  # Strong downward move
                quantity = int(current_holdings * random.uniform(0.4, 0.6))
                if quantity > 0:
                    return (ticker, 'sell', quantity, 0.0)

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
        sim_time = market_data.get('sim_time', 0)

        # Calculate value metrics
        price_vs_initial = (current_price - initial_price) / initial_price
        current_holdings = self.holdings.get(ticker, 0)

        # Conservative traders should slowly build positions
        # More relaxed conditions - trade more frequently

        # Buy on ANY dips or just for diversification (if we have lots of cash)
        cash_ratio = self.cash / self.initial_capital
        if cash_ratio > 0.7:  # Have >70% cash, should be investing
            # Any slight dip or just random opportunity
            if price_change < 0 or random.random() < 0.15:
                if self.cash > current_price * 10:
                    # Conservative position sizing (2-4% of capital)
                    max_capital_to_use = self.cash * random.uniform(0.02, 0.04)
                    quantity = int(max_capital_to_use / current_price)

                    if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                        # Use market order for guaranteed execution
                        return (ticker, 'buy', quantity, 0.0)

        # Buy on dips (value opportunity) - more relaxed
        elif price_change < -0.002 or price_vs_initial < -0.01:  # Much more sensitive
            if self.cash > current_price * 10:
                max_capital_to_use = self.cash * random.uniform(0.02, 0.05)
                quantity = int(max_capital_to_use / current_price)

                if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                    return (ticker, 'buy', quantity, 0.0)  # Market order

        # Sell to lock in gains (more active)
        if current_holdings > 0:
            # Sell on any profit or to rebalance
            if ticker in self.cost_basis:
                gain_pct = (current_price - self.cost_basis[ticker]) / self.cost_basis[ticker]
                if gain_pct > 0.02 or random.random() < 0.08:  # 2% gain or random
                    quantity = int(current_holdings * random.uniform(0.1, 0.25))
                    if quantity > 0:
                        return (ticker, 'sell', quantity, 0.0)  # Market order

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

        current_holdings = self.holdings.get(ticker, 0)

        # Check position P&L for bad decisions
        if current_holdings > 0 and ticker in self.cost_basis:
            loss_pct = (current_price - self.cost_basis[ticker]) / self.cost_basis[ticker]

            # BAD DECISION: Sell winners IMMEDIATELY at tiny gains
            if loss_pct > 0.005:  # Just 0.5% gain - sell NOW!
                quantity = int(current_holdings * random.uniform(0.7, 1.0))  # Sell ALL
                if quantity > 0:
                    return (ticker, 'sell', quantity, 0.0)

            # BAD DECISION: HOLD LOSERS (never sell losing positions)
            # They just hold forever hoping it recovers - this costs them money
            # No selling of losers = losses accumulate

        # BAD DECISION 1: Buy HIGH (FOMO after big gains)
        if price_change > 0.002:  # Buy when rising (terrible timing!)
            if self.cash > current_price * 10:
                # Buy BIG at the TOP
                max_capital_to_use = self.cash * random.uniform(0.10, 0.20)  # Huge orders!
                quantity = int(max_capital_to_use / current_price)

                if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                    return (ticker, 'buy', quantity, 0.0)  # Market order - pays TOP

        # BAD DECISION 2: Panic sell LOW (on any dip)
        if price_change < -0.002:  # Panic on tiny drops!
            if current_holdings > 0:
                # Panic dump EVERYTHING
                quantity = int(current_holdings * random.uniform(0.8, 1.0))  # Sell ALL
                if quantity > 0:
                    return (ticker, 'sell', quantity, 0.0)  # Market order - sells at BOTTOM

        # BAD DECISION 3: Impulsive random bad trades
        if random.random() < 0.15:  # 15% chance of random bad trade
            if self.cash > current_price * 10 and random.random() < 0.5:
                # Impulsive buy at bad time
                max_capital_to_use = self.cash * random.uniform(0.05, 0.15)
                quantity = int(max_capital_to_use / current_price)
                if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                    return (ticker, 'buy', quantity, 0.0)
            elif current_holdings > 0:
                # Impulsive sell
                quantity = int(current_holdings * random.uniform(0.4, 0.7))
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

        # SIMPLIFIED LONG-TERM STRATEGY: Gradual accumulation
        # LongTerm traders should build positions over time

        # If we have lots of cash, we should be buying
        cash_ratio = self.cash / self.initial_capital

        # ACCUMULATION: Buy when we have cash and it's a decent time
        if cash_ratio > 0.5:  # Have >50% cash
            # Buy on any dip, or just randomly to accumulate
            if price_change < 0 or random.random() < 0.25:  # 25% chance
                if self.cash > current_price * 10:
                    # Larger position sizing for long term (5-12% of capital)
                    max_capital_to_use = self.cash * random.uniform(0.05, 0.12)
                    quantity = int(max_capital_to_use / current_price)

                    if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                        # Use market order for guaranteed execution
                        self.last_trade_time[ticker] = sim_time
                        return (ticker, 'buy', quantity, 0.0)

        # ACCUMULATION when allocation is low
        if current_allocation < target:
            # More active buying - don't be too picky
            if random.random() < 0.4 or price_change < -0.005:  # 40% chance or dip
                if self.cash > current_price * 10:
                    max_capital_to_use = self.cash * random.uniform(0.05, 0.15)
                    quantity = int(max_capital_to_use / current_price)

                    if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                        self.last_trade_time[ticker] = sim_time
                        return (ticker, 'buy', quantity, 0.0)  # Market order

        # REBALANCING: Sell if allocation gets too high (rarely)
        elif current_allocation > target * 1.8:  # 80% over target
            if current_holdings > 0:
                quantity = int(current_holdings * 0.15)  # Sell 15%
                if quantity > 0:
                    return (ticker, 'sell', quantity, 0.0)

        # OPPORTUNISTIC BUYING: Any dip is opportunity
        price_vs_initial = (current_price - initial_price) / initial_price
        if price_vs_initial < -0.05:  # Down 5% from initial (less strict)
            if self.cash > current_price * 10:
                max_capital_to_use = self.cash * random.uniform(0.05, 0.10)
                quantity = int(max_capital_to_use / current_price)

                if quantity > 0 and self.can_afford(ticker, quantity, current_price):
                    return (ticker, 'buy', quantity, 0.0)  # Market order

        # Generally don't sell - buy and hold philosophy
        # Only sell for rebalancing (handled above)

        return None
