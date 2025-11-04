"""
Market Effects System

This module provides various market effects that can be applied to the simulation:
- News events (positive/negative shocks)
- Volatility changes
- Sector correlations
- Dividend payments
- Market sentiment shifts

Effects can be triggered randomly or manually by the user.
"""

import random
from typing import Dict, List, Optional
from enum import Enum


class EventType(Enum):
    """Types of market events."""
    POSITIVE_NEWS = "positive_news"
    NEGATIVE_NEWS = "negative_news"
    VOLATILITY_SPIKE = "volatility_spike"
    VOLATILITY_CALM = "volatility_calm"
    MARKET_RALLY = "market_rally"
    MARKET_CRASH = "market_crash"
    DIVIDEND_PAYMENT = "dividend_payment"
    SECTOR_ROTATION = "sector_rotation"
    SENTIMENT_SHIFT = "sentiment_shift"
    CORRELATION_EVENT = "correlation_event"


class MarketEffect:
    """Base class for market effects."""

    def __init__(self, event_type: EventType, description: str):
        self.event_type = event_type
        self.description = description

    def __repr__(self):
        return f"MarketEffect({self.event_type.value}: {self.description})"


class MarketEffectsEngine:
    """
    Engine for generating and applying market effects.

    Can generate random events or allow manual triggering.
    """

    def __init__(self, tickers: List[str], random_event_probability: float = 0.05):
        """
        Initialize the market effects engine.

        Args:
            tickers: List of stock tickers in the market
            random_event_probability: Probability of random event per time step
        """
        self.tickers = tickers
        self.random_event_probability = random_event_probability

        # Event history
        self.event_history: List[MarketEffect] = []

    def should_generate_event(self) -> bool:
        """Determine if a random event should occur."""
        return random.random() < self.random_event_probability

    def generate_random_event(self) -> Optional[MarketEffect]:
        """
        Generate a random market event.

        Returns:
            MarketEffect or None
        """
        if not self.should_generate_event():
            return None

        # Randomly select an event type
        event_type = random.choice(list(EventType))

        return self.create_event(event_type)

    def create_event(self, event_type: EventType,
                    custom_params: Optional[Dict] = None) -> MarketEffect:
        """
        Create a specific market event.

        Args:
            event_type: Type of event to create
            custom_params: Custom parameters for the event

        Returns:
            MarketEffect instance
        """
        if event_type == EventType.POSITIVE_NEWS:
            return self._create_positive_news(custom_params)
        elif event_type == EventType.NEGATIVE_NEWS:
            return self._create_negative_news(custom_params)
        elif event_type == EventType.VOLATILITY_SPIKE:
            return self._create_volatility_spike(custom_params)
        elif event_type == EventType.VOLATILITY_CALM:
            return self._create_volatility_calm(custom_params)
        elif event_type == EventType.MARKET_RALLY:
            return self._create_market_rally(custom_params)
        elif event_type == EventType.MARKET_CRASH:
            return self._create_market_crash(custom_params)
        elif event_type == EventType.DIVIDEND_PAYMENT:
            return self._create_dividend_payment(custom_params)
        elif event_type == EventType.SECTOR_ROTATION:
            return self._create_sector_rotation(custom_params)
        elif event_type == EventType.SENTIMENT_SHIFT:
            return self._create_sentiment_shift(custom_params)
        elif event_type == EventType.CORRELATION_EVENT:
            return self._create_correlation_event(custom_params)
        else:
            return MarketEffect(event_type, "Unknown event")

    def _create_positive_news(self, params: Optional[Dict]) -> 'PositiveNewsEffect':
        """Create a positive news event for a random stock."""
        ticker = params.get('ticker') if params else random.choice(self.tickers)
        magnitude = params.get('magnitude') if params else random.uniform(0.02, 0.08)

        news_items = [
            f"{ticker} announces strong earnings beat",
            f"{ticker} wins major contract",
            f"{ticker} launches innovative new product",
            f"{ticker} announces share buyback program",
            f"{ticker} upgrades guidance for next quarter"
        ]

        description = params.get('description') if params else random.choice(news_items)

        return PositiveNewsEffect(ticker, magnitude, description)

    def _create_negative_news(self, params: Optional[Dict]) -> 'NegativeNewsEffect':
        """Create a negative news event for a random stock."""
        ticker = params.get('ticker') if params else random.choice(self.tickers)
        magnitude = params.get('magnitude') if params else random.uniform(-0.08, -0.02)

        news_items = [
            f"{ticker} misses earnings expectations",
            f"{ticker} faces regulatory investigation",
            f"{ticker} announces product recall",
            f"{ticker} lowers guidance",
            f"{ticker} CEO resignation announced"
        ]

        description = params.get('description') if params else random.choice(news_items)

        return NegativeNewsEffect(ticker, magnitude, description)

    def _create_volatility_spike(self, params: Optional[Dict]) -> 'VolatilityEffect':
        """Create a volatility spike event."""
        new_volatility = params.get('volatility') if params else random.uniform(0.05, 0.10)
        description = "Market volatility spikes due to uncertainty"
        return VolatilityEffect(new_volatility, description)

    def _create_volatility_calm(self, params: Optional[Dict]) -> 'VolatilityEffect':
        """Create a volatility calming event."""
        new_volatility = params.get('volatility') if params else random.uniform(0.005, 0.015)
        description = "Market volatility decreases as calm returns"
        return VolatilityEffect(new_volatility, description)

    def _create_market_rally(self, params: Optional[Dict]) -> 'MarketWideEffect':
        """Create a market-wide rally."""
        magnitude = params.get('magnitude') if params else random.uniform(0.03, 0.07)
        description = params.get('description') if params else "Market rallies on positive economic data"
        return MarketWideEffect(magnitude, description, EventType.MARKET_RALLY)

    def _create_market_crash(self, params: Optional[Dict]) -> 'MarketWideEffect':
        """Create a market-wide crash."""
        magnitude = params.get('magnitude') if params else random.uniform(-0.10, -0.03)
        description = params.get('description') if params else "Market drops on economic concerns"
        return MarketWideEffect(magnitude, description, EventType.MARKET_CRASH)

    def _create_dividend_payment(self, params: Optional[Dict]) -> 'DividendEffect':
        """Create a dividend payment event."""
        ticker = params.get('ticker') if params else random.choice(self.tickers)
        dividend_pct = params.get('dividend_pct') if params else random.uniform(0.01, 0.03)
        description = f"{ticker} pays dividend ({dividend_pct:.1%} yield)"
        return DividendEffect(ticker, dividend_pct, description)

    def _create_sector_rotation(self, params: Optional[Dict]) -> 'SectorRotationEffect':
        """Create a sector rotation event."""
        # Randomly pick winners and losers
        num_winners = random.randint(1, len(self.tickers) // 2)
        winners = random.sample(self.tickers, num_winners)
        losers = [t for t in self.tickers if t not in winners]

        magnitude = params.get('magnitude') if params else random.uniform(0.02, 0.05)
        description = "Sector rotation: capital flows from growth to value"

        return SectorRotationEffect(winners, losers, magnitude, description)

    def _create_sentiment_shift(self, params: Optional[Dict]) -> 'SentimentEffect':
        """Create a market sentiment shift."""
        new_sentiment = params.get('sentiment') if params else random.uniform(-0.5, 0.5)

        if new_sentiment > 0.3:
            description = "Market sentiment turns bullish"
        elif new_sentiment < -0.3:
            description = "Market sentiment turns bearish"
        else:
            description = "Market sentiment becomes neutral"

        return SentimentEffect(new_sentiment, description)

    def _create_correlation_event(self, params: Optional[Dict]) -> 'CorrelationEffect':
        """Create a correlation event (stocks move together)."""
        # Randomly select correlated stocks
        num_stocks = random.randint(2, len(self.tickers))
        correlated_tickers = random.sample(self.tickers, num_stocks)

        magnitude = params.get('magnitude') if params else random.uniform(-0.05, 0.05)
        description = f"Correlated movement in {', '.join(correlated_tickers)}"

        return CorrelationEffect(correlated_tickers, magnitude, description)


# Specific effect classes

class PositiveNewsEffect(MarketEffect):
    """Positive news for a specific stock."""

    def __init__(self, ticker: str, magnitude: float, description: str):
        super().__init__(EventType.POSITIVE_NEWS, description)
        self.ticker = ticker
        self.magnitude = magnitude  # Positive price impact


class NegativeNewsEffect(MarketEffect):
    """Negative news for a specific stock."""

    def __init__(self, ticker: str, magnitude: float, description: str):
        super().__init__(EventType.NEGATIVE_NEWS, description)
        self.ticker = ticker
        self.magnitude = magnitude  # Negative price impact


class VolatilityEffect(MarketEffect):
    """Change in market volatility."""

    def __init__(self, new_volatility: float, description: str):
        event_type = (EventType.VOLATILITY_SPIKE if new_volatility > 0.03
                     else EventType.VOLATILITY_CALM)
        super().__init__(event_type, description)
        self.new_volatility = new_volatility


class MarketWideEffect(MarketEffect):
    """Market-wide price movement."""

    def __init__(self, magnitude: float, description: str, event_type: EventType):
        super().__init__(event_type, description)
        self.magnitude = magnitude


class DividendEffect(MarketEffect):
    """Dividend payment for a stock."""

    def __init__(self, ticker: str, dividend_pct: float, description: str):
        super().__init__(EventType.DIVIDEND_PAYMENT, description)
        self.ticker = ticker
        self.dividend_pct = dividend_pct


class SectorRotationEffect(MarketEffect):
    """Sector rotation: some stocks up, others down."""

    def __init__(self, winners: List[str], losers: List[str],
                magnitude: float, description: str):
        super().__init__(EventType.SECTOR_ROTATION, description)
        self.winners = winners
        self.losers = losers
        self.magnitude = magnitude


class SentimentEffect(MarketEffect):
    """Market sentiment shift."""

    def __init__(self, new_sentiment: float, description: str):
        super().__init__(EventType.SENTIMENT_SHIFT, description)
        self.new_sentiment = new_sentiment  # -1 to 1


class CorrelationEffect(MarketEffect):
    """Correlated price movement across multiple stocks."""

    def __init__(self, tickers: List[str], magnitude: float, description: str):
        super().__init__(EventType.CORRELATION_EVENT, description)
        self.tickers = tickers
        self.magnitude = magnitude


# Helper function to apply effects to the market

def apply_effect_to_market(effect: MarketEffect, market, sim_time: float):
    """
    Apply a market effect to the market.

    Args:
        effect: MarketEffect instance
        market: Market instance
        sim_time: Current simulation time
    """
    if isinstance(effect, PositiveNewsEffect):
        market.apply_stock_specific_news(effect.ticker, effect.magnitude, sim_time)
        print(f"[EVENT] {effect.description} (+{effect.magnitude:.1%})")

    elif isinstance(effect, NegativeNewsEffect):
        market.apply_stock_specific_news(effect.ticker, effect.magnitude, sim_time)
        print(f"[EVENT] {effect.description} ({effect.magnitude:.1%})")

    elif isinstance(effect, MarketWideEffect):
        market.apply_market_wide_shock(effect.magnitude, sim_time)
        print(f"[EVENT] {effect.description} ({effect.magnitude:+.1%})")

    elif isinstance(effect, SentimentEffect):
        market.update_market_sentiment(effect.new_sentiment, sim_time)
        print(f"[EVENT] {effect.description} (sentiment: {effect.new_sentiment:+.2f})")

    elif isinstance(effect, SectorRotationEffect):
        # Apply positive impact to winners
        for ticker in effect.winners:
            market.apply_stock_specific_news(ticker, effect.magnitude, sim_time)

        # Apply negative impact to losers
        for ticker in effect.losers:
            market.apply_stock_specific_news(ticker, -effect.magnitude, sim_time)

        print(f"[EVENT] {effect.description}")

    elif isinstance(effect, CorrelationEffect):
        # Apply same movement to all correlated stocks
        for ticker in effect.tickers:
            market.apply_stock_specific_news(ticker, effect.magnitude, sim_time)

        print(f"[EVENT] {effect.description} ({effect.magnitude:+.1%})")

    elif isinstance(effect, VolatilityEffect):
        # Volatility effects are handled at the stock level
        # This would need to be integrated into the market class
        print(f"[EVENT] {effect.description} (volatility: {effect.new_volatility:.2%})")

    elif isinstance(effect, DividendEffect):
        # Dividend payments give cash to holders
        # This would need trader integration
        print(f"[EVENT] {effect.description}")

    else:
        print(f"[EVENT] Unknown effect type: {effect}")


if __name__ == "__main__":
    """Test the market effects engine."""
    print("=" * 70)
    print("MARKET EFFECTS ENGINE TEST")
    print("=" * 70)

    tickers = ["AAPL", "GOOGL", "AMZN", "NVDA"]
    engine = MarketEffectsEngine(tickers, random_event_probability=0.5)

    print("\n🎲 Generating 10 random events:")
    print("-" * 70)

    for i in range(10):
        event = engine.generate_random_event()
        if event:
            print(f"{i+1}. {event}")

    print("\n📋 Creating specific events:")
    print("-" * 70)

    # Positive news
    event1 = engine.create_event(
        EventType.POSITIVE_NEWS,
        {'ticker': 'AAPL', 'magnitude': 0.05}
    )
    print(f"1. {event1}")

    # Market crash
    event2 = engine.create_event(
        EventType.MARKET_CRASH,
        {'magnitude': -0.08, 'description': 'Flash crash triggered by algo trading'}
    )
    print(f"2. {event2}")

    # Sentiment shift
    event3 = engine.create_event(
        EventType.SENTIMENT_SHIFT,
        {'sentiment': 0.7}
    )
    print(f"3. {event3}")

    print("\n" + "=" * 70)
    print("✅ Market effects test complete!")
    print("=" * 70)
