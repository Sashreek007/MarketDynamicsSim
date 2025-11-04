"""
Traders module for market simulation.

This module provides trader classes with different trading strategies and behaviors.
"""

from .base_trader import BaseTrader
from .trader_types import (
    AggressiveTrader,
    ConservativeTrader,
    LossMakerTrader,
    LongTermTrader
)

__all__ = [
    'BaseTrader',
    'AggressiveTrader',
    'ConservativeTrader',
    'LossMakerTrader',
    'LongTermTrader'
]
