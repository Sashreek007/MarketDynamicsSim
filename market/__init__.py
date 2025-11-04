"""
Market module for market simulation.

This module provides market/exchange functionality with dynamic pricing
and market cap updates, plus market effects system.
"""

from .market import Market, Stock
from .market_effects import (
    MarketEffectsEngine,
    MarketEffect,
    EventType,
    apply_effect_to_market
)

__all__ = [
    'Market',
    'Stock',
    'MarketEffectsEngine',
    'MarketEffect',
    'EventType',
    'apply_effect_to_market'
]
