# Quick Start Guide

## 🚀 Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## ▶️ Running the Simulation

### Basic Usage
```bash
# Run continuously (press Ctrl+C to stop)
python run_simulation.py

# Run for 50 days
python run_simulation.py --days 50

# Run with full verbosity (see all trades)
python run_simulation.py --days 20 --verbosity 2

# Start fresh (clear old data)
python run_simulation.py --clear-db --days 30
```

## 🎮 Manual Event Triggering

While simulation is running, you can trigger events in a Python shell:

```python
from simulation import MarketSimulation
from market.market_effects import EventType

# Create and run simulation
sim = MarketSimulation()

# In a separate thread or process, run:
# sim.run()

# Trigger events manually:
sim.trigger_event(EventType.MARKET_CRASH, {'magnitude': -0.10})
sim.trigger_event(EventType.POSITIVE_NEWS, {'ticker': 'AAPL', 'magnitude': 0.05})
sim.trigger_event(EventType.SENTIMENT_SHIFT, {'sentiment': 0.8})
```

## 📊 Analyzing Results

```python
from database import DatabaseManager
import pandas as pd

# Connect to database
db = DatabaseManager("market_simulation.db")

# Get all trades for AAPL
aapl_trades = db.get_trades_by_ticker("AAPL")
print(aapl_trades.head())

# Get Aggressive trader's trades
aggressive_trades = db.get_trades_by_trader("Aggressive")

# Get portfolio history
portfolio = db.get_portfolio_history("Aggressive")

# Plot stock price over time
price_history = db.get_stock_price_history("AAPL")
price_history.plot(x='simulation_time', y='price', title='AAPL Price History')

# Get summary statistics
summary = db.get_summary_statistics()
print(summary)
```

## 🏛️ Architecture Summary

```
4 Trader Types:
├── Aggressive (70% trade prob) - Momentum, large orders
├── Conservative (30% trade prob) - Value-based, small orders
├── LossMaker (80% trade prob) - Poor timing, buys high/sells low
└── LongTerm (20% trade prob) - Buy & hold strategy

Market Dynamics:
├── Dynamic Pricing - Supply/demand based
├── Dynamic Market Cap - Auto-updates (price × shares)
├── Order Matching - Uses order-matching library
└── Market Effects - News, crashes, volatility, etc.

Database Tracking:
├── Individual trades (per stock & trader)
├── Portfolio snapshots (daily)
├── Stock metrics (price, market cap, volume)
├── Trader performance (P&L, win rate, etc.)
└── Market events log
```

## 🎯 What Happens During Simulation

1. **Traders evaluate** each stock every trading opportunity (4 per day)
2. **Decisions are made** based on their strategy and market conditions
3. **Orders are placed** in the market (limit or market orders)
4. **Matching engine** executes trades when buyers/sellers match
5. **Prices update** dynamically based on trade flow
6. **Market cap recalculates** automatically (price × total shares)
7. **Everything is logged** to SQLite database in real-time
8. **Market events** occur randomly (or triggered manually)

## 📈 Example Output

```
[Day 1.0] Market Update:
======================================================================
APPL: $293.43 (+8.68%) | MCap: $4358.05B | Vol: 1.43%
GOOGL: $298.79 (+6.33%) | MCap: $3615.29B | Vol: 0.30%
AMZN: $269.53 (+10.46%) | MCap: $2872.07B | Vol: 1.00%
NVDA: $218.92 (+8.38%) | MCap: $5332.08B | Vol: 0.74%
======================================================================

Trader Performance:
  Aggressive     : $1,028,855.49 (+2.9%) | P&L: $+28,855.49 | Trades: 8
  Conservative   : $2,000,000.00 (+0.0%) | P&L: $+0.00 | Trades: 0
  LossMaker      : $521,210.13 (+4.2%) | P&L: $+21,210.13 | Trades: 8
  LongTerm       : $5,000,000.00 (+0.0%) | P&L: $+0.00 | Trades: 0
```

## ⚙️ Configuration

Edit `config/simulation_params.py` to change:
- Trading frequency
- Volatility levels
- Price impact factors
- Trader behavior probabilities

Edit `config/initial_conditions.py` to change:
- Stock starting prices
- Trader starting capital
- Market capitalizations

## 🔧 Extending

### Add New Trader Type
```python
# In traders/trader_types.py
from traders.base_trader import BaseTrader

class MyTrader(BaseTrader):
    def decide_trade(self, ticker, current_price, market_data):
        # Your strategy here
        if some_condition:
            return (ticker, 'buy', quantity, limit_price)
        return None
```

### Add New Market Effect
```python
# In market/market_effects.py
class CustomEffect(MarketEffect):
    def __init__(self, param):
        super().__init__(EventType.CUSTOM, "Description")
        self.param = param
```

## 🐛 Troubleshooting

**No trades executing?**
- Increase verbosity to see what's happening: `--verbosity 2`
- Check trader trade probabilities in config
- Run for more days to see activity

**Database locked?**
- Only run one simulation per database file
- Use different `--db path.db` for parallel runs

**Want faster/slower simulation?**
- Adjust `TRADES_PER_TIMESTEP` in `config/simulation_params.py`

## 📚 Learn More

See `README_NEW.md` for comprehensive documentation.

Enjoy! 🚀
