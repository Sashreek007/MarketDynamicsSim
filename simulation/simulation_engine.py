"""
SimPy-based Simulation Engine

This module implements the main simulation engine using SimPy for
discrete event simulation. Traders trade autonomously, market effects
occur randomly or can be triggered manually, and all data is logged to database.
"""

import simpy
import random
from typing import Dict, List, Optional
from datetime import datetime

from config.simulation_params import get_simulation_params
from config.initial_conditions import getInitialState
from database.db_manager import DatabaseManager
from market.market import Market
from market.market_effects import (
    MarketEffectsEngine,
    EventType,
    apply_effect_to_market
)
from traders import (
    AggressiveTrader,
    ConservativeTrader,
    LossMakerTrader,
    LongTermTrader
)


class MarketSimulation:
    """
    Main simulation engine using SimPy.

    Coordinates traders, market, and events in a discrete event simulation.
    """

    def __init__(self, config: Optional[Dict] = None,
                 initial_state: Optional[Dict] = None,
                 db_path: str = "market_simulation.db"):
        """
        Initialize the simulation.

        Args:
            config: Simulation configuration (uses defaults if None)
            initial_state: Initial market state (uses defaults if None)
            db_path: Path to SQLite database
        """
        # Load configuration
        self.config = config or get_simulation_params()
        self.initial_state = initial_state or getInitialState()

        # Initialize database
        self.db_manager = DatabaseManager(db_path)

        # Initialize SimPy environment
        self.env = simpy.Environment()

        # Simulation state
        self.sim_time = 0.0  # In days
        self.running = False
        self.paused = False

        # Initialize market
        self._initialize_market()

        # Initialize traders
        self._initialize_traders()

        # Initialize market effects engine
        self.effects_engine = MarketEffectsEngine(
            tickers=list(self.market.stocks.keys()),
            random_event_probability=0.01  # 1% chance per trading session (reduced)
        )

        # Statistics
        self.total_trades = 0
        self.total_events = 0

        # Seed initial liquidity in order books
        self._seed_initial_liquidity()

        print("=" * 70)
        print("SIMULATION INITIALIZED")
        print("=" * 70)
        print(f"Traders: {len(self.traders)}")
        print(f"Stocks: {len(self.market.stocks)}")
        print(f"Database: {db_path}")
        print("=" * 70)

    def _initialize_market(self):
        """Initialize the market with stocks."""
        stocks_config = {}

        for ticker in self.initial_state['ticker']:
            stocks_config[ticker] = {
                'price': self.initial_state['stock_prices'][ticker],
                'total_shares': self.initial_state['total_shares'][ticker],
                'market_cap': self.initial_state['market_caps'][ticker] * 1e9  # Convert to dollars
            }

        self.market = Market(
            stocks_config=stocks_config,
            db_manager=self.db_manager,
            price_impact_factor=self.config['price_impact_factor'],
            base_volatility=self.config['base_volatility']
        )

    def _initialize_traders(self):
        """Initialize traders based on configuration."""
        self.traders = {}

        trader_types = {
            'Aggressive': AggressiveTrader,
            'Conservative': ConservativeTrader,
            'LossMaker': LossMakerTrader,
            'LongTerm': LongTermTrader
        }

        for trader_name in self.initial_state['trader_names']:
            trader_class = trader_types[trader_name]
            initial_capital = self.initial_state['trader_capital'][trader_name]
            trade_probability = self.config['trade_probability'][trader_name]

            self.traders[trader_name] = trader_class(
                trader_id=trader_name,
                initial_capital=initial_capital,
                trade_probability=trade_probability
            )

    def _seed_initial_liquidity(self):
        """
        Seed the order books with initial liquidity.

        Creates buy and sell limit orders around current price so that
        traders have liquidity to trade against.
        """
        from order_matching.order import LimitOrder
        from order_matching.orders import Orders
        from order_matching.side import Side

        for ticker, stock in self.market.stocks.items():
            current_price = stock.current_price

            # Create buy orders (bids) below current price
            buy_orders = []
            for i in range(5):
                price = current_price * (0.99 - i * 0.001)  # 1%, 1.1%, 1.2% below
                quantity = random.uniform(50, 200)
                order = LimitOrder(
                    side=Side.BUY,
                    price=price,
                    size=quantity,
                    timestamp=self.market.timestamp,
                    order_id=f"seed_buy_{ticker}_{i}",
                    trader_id="MarketMaker"
                )
                buy_orders.append(order)

            # Create sell orders (asks) above current price
            sell_orders = []
            for i in range(5):
                price = current_price * (1.01 + i * 0.001)  # 1%, 1.1%, 1.2% above
                quantity = random.uniform(50, 200)
                order = LimitOrder(
                    side=Side.SELL,
                    price=price,
                    size=quantity,
                    timestamp=self.market.timestamp,
                    order_id=f"seed_sell_{ticker}_{i}",
                    trader_id="MarketMaker"
                )
                sell_orders.append(order)

            # Place all orders in the book
            all_orders = buy_orders + sell_orders
            if all_orders:
                orders_wrapper = Orders(all_orders)
                self.market.matching_engines[ticker].match(
                    timestamp=self.market.timestamp,
                    orders=orders_wrapper
                )

    def trader_process(self, trader_id: str):
        """
        SimPy process for a trader.

        Trader continuously looks for trading opportunities.
        """
        trader = self.traders[trader_id]
        tickers = list(self.market.stocks.keys())

        while True:
            # Wait for next trading opportunity
            # Trading happens multiple times per day
            wait_time = 1.0 / self.config['trades_per_timestep']  # Fraction of a day
            yield self.env.timeout(wait_time)

            # Update simulation time
            self.sim_time = self.env.now

            # Trader considers each stock
            for ticker in tickers:
                current_price = self.market.get_current_price(ticker)
                market_data = self.market.get_market_data(ticker)
                market_data['sim_time'] = self.sim_time

                # Trader decides whether to trade
                trade_decision = trader.decide_trade(ticker, current_price, market_data)

                if trade_decision:
                    ticker, side, quantity, limit_price = trade_decision

                    # Determine order type
                    order_type = 'limit' if limit_price > 0 else 'market'

                    # Check if trader can execute (has funds or shares)
                    can_execute = False
                    if side == 'buy':
                        can_execute = trader.can_afford(ticker, quantity, current_price)
                    else:
                        can_execute = trader.has_shares(ticker, quantity)

                    if can_execute:
                        # Place order on market
                        result = self.market.place_order(
                            ticker=ticker,
                            trader_id=trader_id,
                            side=side,
                            quantity=quantity,
                            order_type=order_type,
                            price=limit_price,
                            sim_time=self.sim_time
                        )

                        # Update trader portfolio if trade executed
                        if result.get('success') and result.get('executed'):
                            avg_price = result['average_price']

                            if side == 'buy':
                                trader.execute_buy(ticker, quantity, avg_price)
                            else:
                                trader.execute_sell(ticker, quantity, avg_price)

                            self.total_trades += 1

                            if self.config['verbosity'] >= 2:
                                print(f"[{self.sim_time:.2f}] {trader_id} {side} "
                                      f"{quantity:.0f} {ticker} @ ${avg_price:.2f}")

    def market_effects_process(self):
        """
        SimPy process for random market effects.

        Generates random market events periodically.
        """
        while True:
            # Check for random events every trading session (quarter day)
            yield self.env.timeout(0.25)

            self.sim_time = self.env.now

            # Generate random event
            effect = self.effects_engine.generate_random_event()

            if effect:
                apply_effect_to_market(effect, self.market, self.sim_time)
                self.total_events += 1

    def market_maker_process(self):
        """
        SimPy process for continuous market making.

        Provides ongoing liquidity by placing limit orders around current price.
        """
        from order_matching.order import LimitOrder
        from order_matching.orders import Orders
        from order_matching.side import Side

        while True:
            # Add liquidity every half day
            yield self.env.timeout(0.5)

            self.sim_time = self.env.now

            # For each stock, add fresh liquidity
            for ticker, stock in self.market.stocks.items():
                current_price = stock.current_price

                # Add a few buy and sell orders around current price
                orders = []

                # 2 buy orders below price
                for i in range(2):
                    price = current_price * (0.995 - i * 0.002)
                    quantity = random.uniform(30, 100)
                    order = LimitOrder(
                        side=Side.BUY,
                        price=price,
                        size=quantity,
                        timestamp=self.market.timestamp,
                        order_id=f"mm_buy_{ticker}_{self.sim_time}_{i}",
                        trader_id="MarketMaker"
                    )
                    orders.append(order)

                # 2 sell orders above price
                for i in range(2):
                    price = current_price * (1.005 + i * 0.002)
                    quantity = random.uniform(30, 100)
                    order = LimitOrder(
                        side=Side.SELL,
                        price=price,
                        size=quantity,
                        timestamp=self.market.timestamp,
                        order_id=f"mm_sell_{ticker}_{self.sim_time}_{i}",
                        trader_id="MarketMaker"
                    )
                    orders.append(order)

                # Place orders in the book
                if orders:
                    orders_wrapper = Orders(orders)
                    try:
                        self.market.matching_engines[ticker].match(
                            timestamp=self.market.timestamp,
                            orders=orders_wrapper
                        )
                    except:
                        pass  # Ignore market maker errors

    def logging_process(self):
        """
        SimPy process for periodic logging.

        Logs snapshots of portfolio and market metrics.
        """
        while True:
            # Log every day
            yield self.env.timeout(1.0)

            self.sim_time = self.env.now

            # Log market metrics
            self.market.log_market_metrics(self.sim_time)

            # Log portfolio snapshots
            current_prices = self.market.get_current_prices()

            for trader_id, trader in self.traders.items():
                holdings_value = trader.get_holdings_value(current_prices)

                self.db_manager.log_portfolio_snapshot(
                    timestamp=datetime.now().timestamp(),
                    sim_time=self.sim_time,
                    trader_id=trader_id,
                    cash=trader.cash,
                    portfolio_value=holdings_value,
                    holdings=trader.holdings
                )

                # Log trader performance
                unrealized_pnl = trader.get_unrealized_pnl(current_prices)

                self.db_manager.log_trader_performance(
                    timestamp=datetime.now().timestamp(),
                    sim_time=self.sim_time,
                    trader_id=trader_id,
                    total_trades=trader.trades_executed,
                    total_buy_volume=trader.total_buy_volume,
                    total_sell_volume=trader.total_sell_volume,
                    realized_pnl=trader.realized_pnl,
                    unrealized_pnl=unrealized_pnl
                )

            if self.config['verbosity'] >= 1:
                print(f"\n[Day {self.sim_time:.1f}] Market Update:")
                print(self.market.get_market_summary())
                print(f"Total trades: {self.total_trades} | Events: {self.total_events}")

    def run(self, until: Optional[float] = None):
        """
        Run the simulation.

        Args:
            until: Run until this simulation time (in days). If None, runs indefinitely.
        """
        print(f"\n{'=' * 70}")
        print("STARTING SIMULATION")
        print(f"{'=' * 70}\n")

        self.running = True

        # Start trader processes
        for trader_id in self.traders.keys():
            self.env.process(self.trader_process(trader_id))

        # Start market effects process
        self.env.process(self.market_effects_process())

        # Start market maker process (provides continuous liquidity)
        self.env.process(self.market_maker_process())

        # Start logging process
        self.env.process(self.logging_process())

        # Run simulation
        try:
            if until:
                self.env.run(until=until)
                print(f"\n{'=' * 70}")
                print(f"SIMULATION COMPLETE (ran for {until} days)")
                print(f"{'=' * 70}")
            else:
                # Run indefinitely (user can stop with Ctrl+C)
                print("Running simulation (press Ctrl+C to stop)...")
                self.env.run()

        except KeyboardInterrupt:
            print(f"\n{'=' * 70}")
            print("SIMULATION STOPPED BY USER")
            print(f"{'=' * 70}")

        finally:
            self.running = False
            self._print_final_summary()

    def trigger_event(self, event_type: EventType, params: Optional[Dict] = None):
        """
        Manually trigger a market event.

        Args:
            event_type: Type of event to trigger
            params: Event parameters

        Example:
            sim.trigger_event(EventType.MARKET_CRASH, {'magnitude': -0.10})
        """
        effect = self.effects_engine.create_event(event_type, params)
        apply_effect_to_market(effect, self.market, self.sim_time)
        self.total_events += 1

        print(f"\n[MANUAL EVENT] {effect.description}")

    def _print_final_summary(self):
        """Print final simulation summary."""
        print("\nFINAL SUMMARY")
        print("=" * 70)

        # Market summary
        print("\nMarket Performance:")
        for ticker, stock in self.market.stocks.items():
            price_change = ((stock.current_price - stock.initial_price) /
                          stock.initial_price * 100)
            print(f"  {ticker}: ${stock.current_price:.2f} ({price_change:+.2f}%) "
                  f"| MCap: ${stock.market_cap/1e9:.2f}B")

        # Trader summary
        print("\nTrader Performance:")
        current_prices = self.market.get_current_prices()

        for trader_id, trader in self.traders.items():
            portfolio_value = trader.get_portfolio_value(current_prices)
            total_return = trader.get_return(current_prices)
            total_pnl = trader.get_total_pnl(current_prices)

            print(f"  {trader_id:15s}: ${portfolio_value:,.2f} "
                  f"({total_return:+.1%}) | P&L: ${total_pnl:+,.2f} | "
                  f"Trades: {trader.trades_executed}")

        print(f"\nTotal Simulation Time: {self.sim_time:.1f} days")
        print(f"Total Trades Executed: {self.total_trades}")
        print(f"Total Market Events: {self.total_events}")

        # Database summary
        print("\nDatabase Summary:")
        db_stats = self.db_manager.get_summary_statistics()
        for key, value in db_stats.items():
            print(f"  {key}: {value}")

        print("=" * 70)

    def get_trader_portfolio(self, trader_id: str) -> Dict:
        """Get current portfolio for a trader."""
        if trader_id not in self.traders:
            return {}

        trader = self.traders[trader_id]
        current_prices = self.market.get_current_prices()

        return {
            'trader_id': trader_id,
            'cash': trader.cash,
            'holdings': trader.holdings,
            'portfolio_value': trader.get_portfolio_value(current_prices),
            'total_pnl': trader.get_total_pnl(current_prices),
            'return': trader.get_return(current_prices),
            'trades_executed': trader.trades_executed
        }

    def get_market_state(self) -> Dict:
        """Get current market state."""
        return {
            'sim_time': self.sim_time,
            'stocks': {
                ticker: stock.get_market_data()
                for ticker, stock in self.market.stocks.items()
            },
            'total_trades': self.total_trades,
            'total_events': self.total_events
        }


if __name__ == "__main__":
    """Test the simulation engine."""
    print("=" * 70)
    print("SIMULATION ENGINE TEST")
    print("=" * 70)

    # Create simulation
    sim = MarketSimulation(db_path="test_simulation.db")

    # Run for 10 days
    sim.run(until=10.0)

    # Test manual event trigger
    print("\n🎯 Triggering manual market crash...")
    sim.trigger_event(EventType.MARKET_CRASH, {'magnitude': -0.05})

    # Run for 5 more days
    print("\nContinuing simulation for 5 more days...")
    sim.run(until=sim.env.now + 5.0)

    print("\n" + "=" * 70)
    print("✅ Simulation test complete!")
    print("=" * 70)
