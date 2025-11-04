"""
Database Manager for Market Simulation

This module handles all database operations including:
- Creating and managing SQLite database schema
- Logging trades, portfolio snapshots, stock metrics
- Tracking trader performance and market events
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
from contextlib import contextmanager


class DatabaseManager:
    """Manages all database operations for the market simulation."""

    def __init__(self, db_path: str = "market_simulation.db"):
        """
        Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._initialize_database()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _initialize_database(self):
        """Create all necessary tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Trades table - logs every individual trade
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    simulation_time REAL NOT NULL,
                    ticker TEXT NOT NULL,
                    trader_id TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    total_value REAL NOT NULL,
                    order_type TEXT NOT NULL,
                    execution_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Portfolio snapshots - periodic snapshots of trader portfolios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    simulation_time REAL NOT NULL,
                    trader_id TEXT NOT NULL,
                    cash REAL NOT NULL,
                    portfolio_value REAL NOT NULL,
                    total_value REAL NOT NULL,
                    holdings TEXT NOT NULL,  -- JSON string of holdings
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Stock metrics - tracks stock prices and market caps
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    simulation_time REAL NOT NULL,
                    ticker TEXT NOT NULL,
                    price REAL NOT NULL,
                    market_cap REAL NOT NULL,
                    total_shares REAL NOT NULL,
                    buy_volume REAL NOT NULL,
                    sell_volume REAL NOT NULL,
                    volatility REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Trader performance - aggregated performance metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trader_performance (
                    performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    simulation_time REAL NOT NULL,
                    trader_id TEXT NOT NULL,
                    total_trades INTEGER NOT NULL,
                    total_buy_volume REAL NOT NULL,
                    total_sell_volume REAL NOT NULL,
                    realized_pnl REAL NOT NULL,
                    unrealized_pnl REAL NOT NULL,
                    total_pnl REAL NOT NULL,
                    win_rate REAL,
                    sharpe_ratio REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Market events - logs market-wide events and shocks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    simulation_time REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    affected_tickers TEXT,  -- JSON string of affected tickers
                    impact_magnitude REAL,
                    parameters TEXT,  -- JSON string of event parameters
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_ticker
                ON trades(ticker, timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trades_trader
                ON trades(trader_id, timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_portfolio_trader
                ON portfolio_snapshots(trader_id, timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_stock_ticker
                ON stock_metrics(ticker, timestamp)
            """)

            conn.commit()

    def log_trade(self, timestamp: float, sim_time: float, ticker: str,
                  trader_id: str, side: str, quantity: float, price: float,
                  order_type: str, execution_type: str = None):
        """
        Log a trade to the database.

        Args:
            timestamp: Unix timestamp
            sim_time: Simulation time in days
            ticker: Stock ticker symbol
            trader_id: ID of the trader
            side: 'buy' or 'sell'
            quantity: Number of shares
            price: Price per share
            order_type: 'market' or 'limit'
            execution_type: Type of execution (from order matching engine)
        """
        total_value = quantity * price

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trades (timestamp, simulation_time, ticker, trader_id,
                                  side, quantity, price, total_value, order_type,
                                  execution_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, sim_time, ticker, trader_id, side, quantity,
                  price, total_value, order_type, execution_type))

    def log_portfolio_snapshot(self, timestamp: float, sim_time: float,
                              trader_id: str, cash: float, portfolio_value: float,
                              holdings: Dict[str, float]):
        """
        Log a portfolio snapshot to the database.

        Args:
            timestamp: Unix timestamp
            sim_time: Simulation time in days
            trader_id: ID of the trader
            cash: Cash balance
            portfolio_value: Value of all holdings
            holdings: Dictionary of ticker -> quantity
        """
        import json
        total_value = cash + portfolio_value
        holdings_json = json.dumps(holdings)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO portfolio_snapshots (timestamp, simulation_time,
                                                trader_id, cash, portfolio_value,
                                                total_value, holdings)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, sim_time, trader_id, cash, portfolio_value,
                  total_value, holdings_json))

    def log_stock_metrics(self, timestamp: float, sim_time: float, ticker: str,
                         price: float, market_cap: float, total_shares: float,
                         buy_volume: float, sell_volume: float,
                         volatility: Optional[float] = None):
        """
        Log stock metrics to the database.

        Args:
            timestamp: Unix timestamp
            sim_time: Simulation time in days
            ticker: Stock ticker symbol
            price: Current stock price
            market_cap: Market capitalization
            total_shares: Total shares outstanding
            buy_volume: Cumulative buy volume
            sell_volume: Cumulative sell volume
            volatility: Price volatility measure
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO stock_metrics (timestamp, simulation_time, ticker,
                                         price, market_cap, total_shares,
                                         buy_volume, sell_volume, volatility)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, sim_time, ticker, price, market_cap, total_shares,
                  buy_volume, sell_volume, volatility))

    def log_trader_performance(self, timestamp: float, sim_time: float,
                             trader_id: str, total_trades: int,
                             total_buy_volume: float, total_sell_volume: float,
                             realized_pnl: float, unrealized_pnl: float,
                             win_rate: Optional[float] = None,
                             sharpe_ratio: Optional[float] = None):
        """
        Log trader performance metrics to the database.

        Args:
            timestamp: Unix timestamp
            sim_time: Simulation time in days
            trader_id: ID of the trader
            total_trades: Total number of trades
            total_buy_volume: Total buy volume
            total_sell_volume: Total sell volume
            realized_pnl: Realized profit and loss
            unrealized_pnl: Unrealized profit and loss
            win_rate: Percentage of profitable trades
            sharpe_ratio: Risk-adjusted return metric
        """
        total_pnl = realized_pnl + unrealized_pnl

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trader_performance (timestamp, simulation_time,
                                              trader_id, total_trades,
                                              total_buy_volume, total_sell_volume,
                                              realized_pnl, unrealized_pnl,
                                              total_pnl, win_rate, sharpe_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, sim_time, trader_id, total_trades, total_buy_volume,
                  total_sell_volume, realized_pnl, unrealized_pnl, total_pnl,
                  win_rate, sharpe_ratio))

    def log_market_event(self, timestamp: float, sim_time: float,
                        event_type: str, description: str,
                        affected_tickers: Optional[List[str]] = None,
                        impact_magnitude: Optional[float] = None,
                        parameters: Optional[Dict] = None):
        """
        Log a market event to the database.

        Args:
            timestamp: Unix timestamp
            sim_time: Simulation time in days
            event_type: Type of event (e.g., 'news', 'volatility_shock')
            description: Human-readable description
            affected_tickers: List of affected stock tickers
            impact_magnitude: Magnitude of impact (e.g., percentage change)
            parameters: Additional event parameters
        """
        import json
        affected_json = json.dumps(affected_tickers) if affected_tickers else None
        params_json = json.dumps(parameters) if parameters else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO market_events (timestamp, simulation_time, event_type,
                                         description, affected_tickers,
                                         impact_magnitude, parameters)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, sim_time, event_type, description, affected_json,
                  impact_magnitude, params_json))

    def get_trades_by_ticker(self, ticker: str, limit: Optional[int] = None) -> pd.DataFrame:
        """Get all trades for a specific ticker."""
        query = "SELECT * FROM trades WHERE ticker = ? ORDER BY timestamp DESC"
        if limit:
            query += f" LIMIT {limit}"

        with self._get_connection() as conn:
            return pd.read_sql_query(query, conn, params=(ticker,))

    def get_trades_by_trader(self, trader_id: str, limit: Optional[int] = None) -> pd.DataFrame:
        """Get all trades for a specific trader."""
        query = "SELECT * FROM trades WHERE trader_id = ? ORDER BY timestamp DESC"
        if limit:
            query += f" LIMIT {limit}"

        with self._get_connection() as conn:
            return pd.read_sql_query(query, conn, params=(trader_id,))

    def get_portfolio_history(self, trader_id: str) -> pd.DataFrame:
        """Get portfolio history for a specific trader."""
        query = """
            SELECT * FROM portfolio_snapshots
            WHERE trader_id = ?
            ORDER BY timestamp ASC
        """
        with self._get_connection() as conn:
            return pd.read_sql_query(query, conn, params=(trader_id,))

    def get_stock_price_history(self, ticker: str) -> pd.DataFrame:
        """Get price history for a specific stock."""
        query = """
            SELECT * FROM stock_metrics
            WHERE ticker = ?
            ORDER BY timestamp ASC
        """
        with self._get_connection() as conn:
            return pd.read_sql_query(query, conn, params=(ticker,))

    def get_trader_performance_history(self, trader_id: str) -> pd.DataFrame:
        """Get performance history for a specific trader."""
        query = """
            SELECT * FROM trader_performance
            WHERE trader_id = ?
            ORDER BY timestamp ASC
        """
        with self._get_connection() as conn:
            return pd.read_sql_query(query, conn, params=(trader_id,))

    def get_market_events(self, event_type: Optional[str] = None) -> pd.DataFrame:
        """Get market events, optionally filtered by type."""
        if event_type:
            query = """
                SELECT * FROM market_events
                WHERE event_type = ?
                ORDER BY timestamp DESC
            """
            with self._get_connection() as conn:
                return pd.read_sql_query(query, conn, params=(event_type,))
        else:
            query = "SELECT * FROM market_events ORDER BY timestamp DESC"
            with self._get_connection() as conn:
                return pd.read_sql_query(query, conn)

    def get_summary_statistics(self) -> Dict:
        """Get summary statistics for the entire simulation."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total trades
            cursor.execute("SELECT COUNT(*) FROM trades")
            total_trades = cursor.fetchone()[0]

            # Total volume
            cursor.execute("SELECT SUM(total_value) FROM trades")
            total_volume = cursor.fetchone()[0] or 0

            # Unique traders
            cursor.execute("SELECT COUNT(DISTINCT trader_id) FROM trades")
            unique_traders = cursor.fetchone()[0]

            # Unique stocks
            cursor.execute("SELECT COUNT(DISTINCT ticker) FROM trades")
            unique_stocks = cursor.fetchone()[0]

            # Market events
            cursor.execute("SELECT COUNT(*) FROM market_events")
            total_events = cursor.fetchone()[0]

            return {
                "total_trades": total_trades,
                "total_volume": total_volume,
                "unique_traders": unique_traders,
                "unique_stocks": unique_stocks,
                "total_market_events": total_events
            }

    def clear_all_data(self):
        """Clear all data from all tables (use with caution!)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM trades")
            cursor.execute("DELETE FROM portfolio_snapshots")
            cursor.execute("DELETE FROM stock_metrics")
            cursor.execute("DELETE FROM trader_performance")
            cursor.execute("DELETE FROM market_events")
            conn.commit()


if __name__ == "__main__":
    """Test the database manager."""
    print("=" * 70)
    print("DATABASE MANAGER TEST")
    print("=" * 70)

    # Create a test database
    db = DatabaseManager("test_market.db")

    print("\n✅ Database initialized successfully!")
    print("\nTables created:")
    print("  - trades")
    print("  - portfolio_snapshots")
    print("  - stock_metrics")
    print("  - trader_performance")
    print("  - market_events")

    # Test logging a trade
    print("\n📝 Testing trade logging...")
    db.log_trade(
        timestamp=1234567890.0,
        sim_time=1.0,
        ticker="AAPL",
        trader_id="Aggressive",
        side="buy",
        quantity=100,
        price=150.0,
        order_type="market"
    )
    print("✅ Trade logged successfully!")

    # Test getting trades
    print("\n📊 Retrieving trades for AAPL...")
    trades_df = db.get_trades_by_ticker("AAPL")
    print(trades_df)

    # Get summary
    print("\n📈 Summary statistics:")
    summary = db.get_summary_statistics()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 70)
    print("✅ Database test complete!")
    print("=" * 70)
