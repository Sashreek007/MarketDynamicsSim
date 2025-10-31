"""
    Initial Conditions Configuration
This file defines the starting state of our market simulation:
    - Stock prices
    - Market capitalizations
    - Trader starting capital
    - Number of intitial shares
"""


# STOCK INITIAL CONDITIONS

INITIAL_STOCK_PRICES = {
    "APPL": 270.0,
    "GOOGL": 281.0,
    "AMZN": 244.0,
    "NVDA": 202.0,
}

# Market Capitalization(in billions)
# Market cap = stock price x total shares outstanding

MARKET_CAPS = {
    "APPL": 4010.0,
    "GOOGL": 3400.0,
    "AMZN": 2600.0,
    "NVDA": 4920.0,
}


TOTAL_SHARES = {
    ticker: (market_cap / price) * 1_000_000_000
    for ticker, (market_cap, price) in zip(
        MARKET_CAPS.keys(), zip(MARKET_CAPS.values(), INITIAL_STOCK_PRICES.values())
    )
}


# TRADER INITIAL CONDITIONS

TRADER_INITIAL_CAPITAL = {
    "Aggressive": 1_000_000,
    "Conservative": 2_000_000,
    "LossMaker": 500_000,
    "LongTerm": 5_000_000,
}

# INITIAL HOLDINGS

TRADER_INITIAL_HOLDINGS = {
    "Aggressive": {"APPL": 0, "GOOGL": 0, "AMZN": 0, "NVDA": 0},
    "Conservative": {"APPL": 0, "GOOGL": 0, "AMZN": 0, "NVDA": 0},
    "LossMaker": {"APPL": 0, "GOOGL": 0, "AMZN": 0, "NVDA": 0},
    "LongTerm": {"APPL": 0, "GOOGL": 0, "AMZN": 0, "NVDA": 0},
}


TICKERS = list(INITIAL_STOCK_PRICES.keys())

TRADER_NAMES = list(TRADER_INITIAL_CAPITAL.keys())


def getInitialState():
    """
    Returns a dictionary with all initial conditions.

    This function is used by the cadCAD model to set up the starting state.
    it packages all the initial conditions into one convenient dictionary.

    Returns:
        dict: Complete initial sstate of simulation
    """
    return {
        "stock_prices": INITIAL_STOCK_PRICES.copy(),
        "market_caps": MARKET_CAPS.copy(),
        "total_shares": TOTAL_SHARES.copy(),
        "trader_capital": TRADER_INITIAL_CAPITAL.copy(),
        "trader_holdings": {
            trader: holdings.copy()
            for trader, holdings in TRADER_INITIAL_HOLDINGS.items()
        },
        "ticker": TICKERS,
        "trader_names": TRADER_NAMES,
    }


if __name__ == "__main__":
    print("=" * 70)
    print("MARKET SIMULATION - INITIAL CONDITIONS")
    print("=" * 70)

    print("\nSTOCKS:")
    print("-" * 70)
    for ticker in TICKERS:
        print(
            f"{ticker:6s} | Price: ${INITIAL_STOCK_PRICES[ticker]:8.2f} | "
            f"Market Cap: ${MARKET_CAPS[ticker]:8.1f}B | "
            f"Shares: {TOTAL_SHARES[ticker]:,.0f}"
        )

    print("\n TRADERS:")
    print("-" * 70)
    for trader in TRADER_NAMES:
        print(f"{trader:15s} | Starting Capital: ${TRADER_INITIAL_CAPITAL[trader]:,}")

    total_capital = sum(TRADER_INITIAL_CAPITAL.values())
    print(f"\n Total Capital in Market: ${total_capital:,}")
    print("=" * 70)
