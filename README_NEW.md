# Market Dynamics Simulation

A sophisticated market simulation engine featuring autonomous traders, dynamic pricing, and comprehensive data logging.

## 🎯 Overview

This simulation models a stock market with:
- **4 autonomous trader types** with distinct strategies
- **Dynamic price discovery** based on supply/demand
- **Real-time market cap updates** (price × shares)
- **Market effects system** (news, crashes, volatility, etc.)
- **Comprehensive SQLite database** logging all trades, portfolios, and metrics
- **SimPy discrete event simulation** for realistic continuous trading

## 🏗️ Architecture

```
MarketDynamicsSim/
├── database/           # SQLite database management
│   ├── db_manager.py   # Database operations & schema
│   └── __init__.py
├── market/             # Market/exchange logic
│   ├── market.py       # Dynamic pricing & order matching
│   ├── market_effects.py  # Market events system
│   └── __init__.py
├── traders/            # Trader implementations
│   ├── base_trader.py  # Base trader class
│   ├── trader_types.py # 4 specific trader types
│   └── __init__.py
├── simulation/         # Simulation engine
│   ├── simulation_engine.py  # SimPy-based engine
│   └── __init__.py
├── config/             # Configuration
│   ├── simulation_params.py   # Simulation parameters
│   └── initial_conditions.py  # Initial market state
├── run_simulation.py   # Main runner script
└── requirements.txt
```

## 📦 Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

Required packages:
- `simpy` - Discrete event simulation
- `order-matching` - Order book matching engine
- `pandas`, `numpy` - Data processing
- `matplotlib`, `seaborn` - Visualization
- `python-dateutil` - Date/time handling

2. **Verify installation:**
```bash
python -c "import simpy; from order_matching import MatchingEngine; print('✅ All dependencies installed')"
```

## 🚀 Quick Start

### Basic Usage

Run the simulation continuously (Ctrl+C to stop):
```bash
python run_simulation.py
```

Run for a specific number of days:
```bash
python run_simulation.py --days 100
```

### Command Line Options

```bash
python run_simulation.py --help

Options:
  --days DAYS         Run for specified days (default: continuous)
  --db PATH          Database path (default: market_simulation.db)
  --verbosity LEVEL  Output level 0-2 (default: 1)
  --no-events        Disable random market events
  --clear-db         Clear database before starting
```

### Examples

```bash
# Run for 50 days with maximum verbosity
python run_simulation.py --days 50 --verbosity 2

# Run continuously with custom database
python run_simulation.py --db my_market.db

# Run without random events (manual control)
python run_simulation.py --no-events

# Fresh start (clear old data)
python run_simulation.py --clear-db --days 30
```

## 👥 Trader Types

### 1. Aggressive Trader
- **Trade Probability:** 70%
- **Strategy:** Momentum-based, chases trends
- **Order Size:** 5-10% of capital
- **Behavior:**
  - Buys on upward momentum
  - Sells on downward trends
  - Takes quick profits
  - Uses limit orders strategically

### 2. Conservative Trader
- **Trade Probability:** 30%
- **Strategy:** Value-based, patient
- **Order Size:** 2-5% of capital
- **Behavior:**
  - Buys on dips (value opportunities)
  - Sells on peaks (risk management)
  - Maintains diversified portfolio
  - Risk-averse position sizing

### 3. LossMaker Trader
- **Trade Probability:** 80%
- **Strategy:** Poor timing, emotional
- **Order Size:** 5-15% of capital
- **Behavior:**
  - Buys high (FOMO)
  - Sells low (panic)
  - Sells winners too early
  - Holds losing positions
  - Impulsive on volatility

### 4. LongTerm Trader
- **Trade Probability:** 20%
- **Strategy:** Buy and hold
- **Order Size:** 8-15% of capital
- **Behavior:**
  - Strategic accumulation
  - Holds through volatility
  - Rarely sells (only rebalances)
  - Buys major dips
  - Patient position building

## 📊 Market Dynamics

### Dynamic Pricing
Prices update based on:
- **Trade size** relative to typical volume
- **Direction** (buy pushes up, sell pushes down)
- **Current volatility** (amplifies movements)
- **Market sentiment** (overall market bias)

### Dynamic Market Cap
Market cap automatically updates as:
```
Market Cap = Current Price × Total Shares Outstanding
```

### Market Effects

Random events can occur:
- **News Events:** Stock-specific positive/negative news
- **Market Crashes/Rallies:** Market-wide movements
- **Volatility Spikes:** Sudden volatility increases
- **Sector Rotation:** Money flows between stocks
- **Sentiment Shifts:** Overall market mood changes
- **Dividend Payments:** Cash distributions

## 💾 Database Schema

### Tables

1. **trades** - Every individual trade
   - timestamp, ticker, trader_id, side, quantity, price, order_type

2. **portfolio_snapshots** - Daily portfolio states
   - timestamp, trader_id, cash, portfolio_value, holdings (JSON)

3. **stock_metrics** - Stock performance data
   - timestamp, ticker, price, market_cap, volume, volatility

4. **trader_performance** - Aggregated trader metrics
   - timestamp, trader_id, total_trades, P&L, win_rate, sharpe_ratio

5. **market_events** - All market events
   - timestamp, event_type, description, affected_tickers, impact

## 📈 Data Analysis

### Query Database

```python
from database import DatabaseManager

db = DatabaseManager("market_simulation.db")

# Get trades for a specific stock
aapl_trades = db.get_trades_by_ticker("AAPL")

# Get trades by a specific trader
aggressive_trades = db.get_trades_by_trader("Aggressive")

# Get portfolio history
portfolio_hist = db.get_portfolio_history("Conservative")

# Get stock price history
price_hist = db.get_stock_price_history("GOOGL")

# Get all market events
events = db.get_market_events()

# Get summary statistics
summary = db.get_summary_statistics()
print(summary)
# {'total_trades': 1234, 'total_volume': 5000000, ...}
```

### Analyze with Pandas

```python
import pandas as pd
from database import DatabaseManager

db = DatabaseManager("market_simulation.db")

# Load all trades into DataFrame
trades_df = db.get_trades_by_ticker("AAPL")

# Calculate metrics
avg_price = trades_df['price'].mean()
total_volume = trades_df['quantity'].sum()

# Group by trader
trader_volumes = trades_df.groupby('trader_id')['total_value'].sum()

# Plot price over time
import matplotlib.pyplot as plt
trades_df.plot(x='timestamp', y='price')
plt.show()
```

## 🎮 Manual Event Triggering

You can manually trigger market events:

```python
from simulation import MarketSimulation
from market.market_effects import EventType

# Create simulation
sim = MarketSimulation()

# Start simulation in background
import threading
thread = threading.Thread(target=sim.run)
thread.start()

# Trigger events manually
sim.trigger_event(EventType.MARKET_CRASH, {'magnitude': -0.10})
sim.trigger_event(EventType.POSITIVE_NEWS, {'ticker': 'AAPL', 'magnitude': 0.05})
sim.trigger_event(EventType.SENTIMENT_SHIFT, {'sentiment': 0.8})

# Stop simulation
# (Ctrl+C or thread management)
```

## ⚙️ Configuration

### Modify Simulation Parameters

Edit `config/simulation_params.py`:
```python
TIMESTEPS = 100              # Trading days
TRADES_PER_TIMESTEP = 4      # Trades per day
BASE_VOLATILITY = 0.02       # 2% daily volatility
PRICE_IMPACT_FACTOR = 0.1    # Trade impact on price
```

### Modify Initial Conditions

Edit `config/initial_conditions.py`:
```python
INITIAL_STOCK_PRICES = {
    "AAPL": 270.0,
    "GOOGL": 281.0,
    # Add more stocks...
}

TRADER_INITIAL_CAPITAL = {
    "Aggressive": 1_000_000,
    "Conservative": 2_000_000,
    # Modify capital...
}
```

## 🔧 Extending the System

### Add New Trader Type

```python
from traders.base_trader import BaseTrader

class MyCustomTrader(BaseTrader):
    def decide_trade(self, ticker, current_price, market_data):
        # Implement your strategy
        if some_condition:
            return (ticker, 'buy', quantity, limit_price)
        return None
```

### Add New Market Effect

```python
from market.market_effects import MarketEffect, EventType

class CustomEffect(MarketEffect):
    def __init__(self, param):
        super().__init__(EventType.CUSTOM, "Description")
        self.param = param
```

## 📝 Notes

- **Database:** SQLite (no server needed, portable)
- **Order Matching:** Uses `order-matching` library for realistic execution
- **Thread-safe:** Database uses context managers for safety
- **Real-time:** All data logged as events occur
- **Extensible:** Clean modular design for easy expansion

## 🐛 Troubleshooting

**Import errors:**
```bash
pip install -r requirements.txt --upgrade
```

**Database locked:**
- Only one simulation per database file
- Use different `--db` path for parallel runs

**Simulation too fast/slow:**
- Adjust `TRADES_PER_TIMESTEP` in config
- Change verbosity level

## 📄 License

See main project repository for license information.

## 🤝 Contributing

This is a clean, modular codebase designed for extension. Key extension points:
- New trader types in `traders/`
- New market effects in `market/market_effects.py`
- New analysis tools using the database

Enjoy the simulation! 🚀
