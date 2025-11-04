#!/usr/bin/env python3
"""
Market Dynamics Simulation - Main Runner

This script runs the market simulation with autonomous traders.
You can:
- Run the simulation continuously (Ctrl+C to stop)
- Trigger market events manually
- View real-time market updates
- All data is logged to SQLite database

Usage:
    python run_simulation.py [options]

Options:
    --days DAYS         Run for specified number of days (default: continuous)
    --db PATH          Database path (default: market_simulation.db)
    --verbosity LEVEL  Output verbosity 0-2 (default: 1)
    --no-events        Disable random market events
"""

import argparse
import sys
from simulation import MarketSimulation
from market.market_effects import EventType


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Run autonomous market simulation with dynamic pricing'
    )

    parser.add_argument(
        '--days',
        type=float,
        default=None,
        help='Number of days to simulate (default: run until stopped)'
    )

    parser.add_argument(
        '--db',
        type=str,
        default='market_simulation.db',
        help='Database file path (default: market_simulation.db)'
    )

    parser.add_argument(
        '--verbosity',
        type=int,
        choices=[0, 1, 2],
        default=1,
        help='Output verbosity: 0=silent, 1=daily updates, 2=all trades (default: 1)'
    )

    parser.add_argument(
        '--no-events',
        action='store_true',
        help='Disable random market events'
    )

    parser.add_argument(
        '--clear-db',
        action='store_true',
        help='Clear existing database before starting'
    )

    return parser.parse_args()


def print_welcome():
    """Print welcome message."""
    print("""
╔═══════════════════════════════════════════════════════════════════════╗
║                   MARKET DYNAMICS SIMULATION                          ║
║                                                                       ║
║  Autonomous traders compete in a dynamic market with:                ║
║  • Real-time price discovery based on supply/demand                  ║
║  • Dynamic market cap updates (price × shares)                       ║
║  • Market effects (news, crashes, volatility, sentiment)             ║
║  • 4 trader types with distinct strategies                           ║
║  • Comprehensive database logging                                    ║
╚═══════════════════════════════════════════════════════════════════════╝
    """)


def print_controls():
    """Print simulation controls."""
    print("""
CONTROLS:
---------
• Press Ctrl+C to stop the simulation gracefully
• All data is logged to the database in real-time
• You can query the database while simulation runs

TRADER TYPES:
-------------
1. Aggressive    - High frequency, momentum trading (70% trade prob)
2. Conservative  - Value-based, patient (30% trade prob)
3. LossMaker     - Poor timing, buys high/sells low (80% trade prob)
4. LongTerm      - Buy & hold strategy (20% trade prob)

MARKET EFFECTS:
---------------
Random events will occur during simulation:
• News events (positive/negative)
• Market crashes/rallies
• Volatility spikes
• Sector rotation
• Sentiment shifts
• And more...
    """)


def main():
    """Main entry point."""
    args = parse_args()

    print_welcome()
    print_controls()

    print("=" * 70)
    print("INITIALIZING SIMULATION")
    print("=" * 70)
    print(f"Database: {args.db}")
    print(f"Verbosity: {args.verbosity}")
    print(f"Random Events: {'Disabled' if args.no_events else 'Enabled'}")

    if args.days:
        print(f"Duration: {args.days} days")
    else:
        print("Duration: Continuous (run until stopped)")

    print("=" * 70)

    # Create simulation
    from config.simulation_params import get_simulation_params

    config = get_simulation_params()
    config['verbosity'] = args.verbosity

    sim = MarketSimulation(
        config=config,
        db_path=args.db
    )

    # Clear database if requested
    if args.clear_db:
        print("\n⚠️  Clearing existing database...")
        sim.db_manager.clear_all_data()
        print("✅ Database cleared\n")

    # Disable random events if requested
    if args.no_events:
        sim.effects_engine.random_event_probability = 0.0

    # Print initial market state
    print("\nINITIAL MARKET STATE:")
    print(sim.market.get_market_summary())

    print("\nINITIAL TRADER PORTFOLIOS:")
    for trader_id in sim.traders.keys():
        portfolio = sim.get_trader_portfolio(trader_id)
        print(f"  {trader_id:15s}: ${portfolio['cash']:,.2f} cash")

    # Run simulation
    try:
        print("\n" + "=" * 70)
        if args.days:
            print(f"STARTING SIMULATION (will run for {args.days} days)")
        else:
            print("STARTING SIMULATION (press Ctrl+C to stop)")
        print("=" * 70 + "\n")

        sim.run(until=args.days)

    except KeyboardInterrupt:
        print("\n\n⚠️  Stopping simulation...")

    except Exception as e:
        print(f"\n\n❌ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Print final summary
    print("\n" + "=" * 70)
    print("SIMULATION COMPLETE")
    print("=" * 70)

    print("\n📊 To analyze results, you can:")
    print(f"   1. Query the database: {args.db}")
    print(f"   2. Use Python to load data:")
    print(f"""
   from database import DatabaseManager
   db = DatabaseManager("{args.db}")

   # Get all trades for a stock
   trades = db.get_trades_by_ticker("AAPL")

   # Get portfolio history for a trader
   portfolio = db.get_portfolio_history("Aggressive")

   # Get stock price history
   prices = db.get_stock_price_history("AAPL")

   # Get summary statistics
   summary = db.get_summary_statistics()
   """)

    print("\n✅ Simulation ended successfully!")


if __name__ == "__main__":
    main()
