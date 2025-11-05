"""
This file defines how the simluations runs:
- How many trading days to simulate
- How many times to run the siluation (Monte Carlo runs)
- Timestep definitions
- Other simluation settings
"""

# SIMULATION DURATION
# each timestep = 1 trading day
TIMESTEPS = 100

# defines how many times to run the entire simluation
MONTE_CARLO_RUNS = 1


# TRADING PARAMS


# defining how many trimes per day does each trader get a chance to trade
TRADES_PER_TIMESTEP = 4

# Minimum order size (number of shares)

MIN_ORDER_SIZE = 1


# Max order size as percentage of avalible capital
MAX_ORDER_SIZE_PCT = 0.1

# ORDER BOOK PARAMS

# spread is bascially the difference between buy and sell prices
# smaller spread = more liquid market, easier to trade
INITIAL_SPREAD_PCT = 0.001

# Order boook depth is how many price levels to maintian
# more depth means more realistitc order book, but slower execution
ORDER_BOOK_DEPTH = 5

# Using a seed gives the same random results
RANDOM_SEED = 42

# Probability that a trader will trader in any given opportunity
# NOT ALL TRADERS TRADE CONSTANTLY
TRADE_PROBABILITY = {
    "Aggressive": 0.7,
    "Conservative": 0.3,
    "LossMaker": 0.9,  # Increased to 90% - they trade MORE (making more bad decisions = more losses)
    "LongTerm": 0.2,
}


# PRICE MOVEMENT PARAMS

# base volatility means how much prices naturally fluctuate
# this is the standard deviation of price changes
# higher means more volatility

BASE_VOLATILITY = 0.02  # 2% per day


# price impact is how much a trade affects the stock price
# Larger trades should move the price more
# price change = PRICE_IMPACT_FACTOR x (order_size/total_shares)

PRICE_IMPACT_FACTOR = 0.1

# Mean reversion strength means tendency for prices to return to fundmental value
# 1 means instant reversion (prices snap back immediately)
# 0 means no mean reversion (random walk)

MEAN_REVERSION = 0.05

# Verbosity level for simulation output
# 0 = silent
# 1 = basic
# 2 show all trades

VERBOSITY = 1

# Save simulation data to csv
SAVE_RESULTS = True
OUTPUT_DIR = "simulation_results"


def get_simulation_params():
    """
    Returns a dictionary with all simulation parameters.

    This is used by the cadCAD model configuration.

    Returns:
        dict: Complete simulation parameters
    """
    return {
        "timesteps": TIMESTEPS,
        "monte_carlo_runs": MONTE_CARLO_RUNS,
        "trades_per_timestep": TRADES_PER_TIMESTEP,
        "min_order_size": MIN_ORDER_SIZE,
        "max_order_size_pct": MAX_ORDER_SIZE_PCT,
        "initial_spread_pct": INITIAL_SPREAD_PCT,
        "order_book_depth": ORDER_BOOK_DEPTH,
        "random_seed": RANDOM_SEED,
        "trade_probability": TRADE_PROBABILITY,
        "base_volatility": BASE_VOLATILITY,
        "price_impact_factor": PRICE_IMPACT_FACTOR,
        "mean_reversion": MEAN_REVERSION,
        "verbosity": VERBOSITY,
        "save_results": SAVE_RESULTS,
        "output_dir": OUTPUT_DIR,
    }


if __name__ == "__main__":
    """
    If you run this file directly, it will print all parameters.
    """
    print("=" * 70)
    print("MARKET SIMULATION - PARAMETERS")
    print("=" * 70)

    print(f"\nSIMULATION DURATION:")
    print(f"   Trading Days: {TIMESTEPS}")
    print(f"   Monte Carlo Runs: {MONTE_CARLO_RUNS}")
    print(f"   Trades per Day: {TRADES_PER_TIMESTEP}")
    print(f"   Total Trading Opportunities: {TIMESTEPS * TRADES_PER_TIMESTEP}")

    print(f"\n MARKET PARAMETERS:")
    print(f"   Base Volatility: {BASE_VOLATILITY:.1%}")
    print(f"   Price Impact Factor: {PRICE_IMPACT_FACTOR}")
    print(f"   Mean Reversion: {MEAN_REVERSION}")
    print(f"   Initial Spread: {INITIAL_SPREAD_PCT:.2%}")

    print(f"\n RANDOMNESS:")
    print(f"   Random Seed: {RANDOM_SEED}")
    print(f"   Trade Probabilities:")
    for trader, prob in TRADE_PROBABILITY.items():
        print(f"      {trader:15s}: {prob:.0%}")

    print("=" * 70)
