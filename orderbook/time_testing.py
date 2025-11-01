import time
import csv
from datetime import datetime
from order_matching.matching_engine import MatchingEngine
from order_matching.order import LimitOrder, MarketOrder
from order_matching.orders import Orders
from order_matching.side import Side
import random


# --------------------------
# CSV LOGGING BUFFER
# --------------------------
LOG_BUFFER = []
LOG_FILE = "trades_benchmark.csv"
FLUSH_INTERVAL = 1000  # write every 1000 trades


def flush_csv(buffer, filename=LOG_FILE):
    """Flush buffered trades to CSV (fast batch I/O)."""
    if not buffer:
        return
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=buffer[0].keys())
        if f.tell() == 0:
            writer.writeheader()
        writer.writerows(buffer)
    buffer.clear()


def log_trade(trade):
    """Add a trade to memory buffer and flush periodically."""
    LOG_BUFFER.append(
        {
            "timestamp": trade.timestamp,
            "side": trade.side.name,
            "price": trade.price,
            "size": trade.size,
            "incoming_order_id": trade.incoming_order_id,
            "book_order_id": trade.book_order_id,
        }
    )
    if len(LOG_BUFFER) >= FLUSH_INTERVAL:
        flush_csv(LOG_BUFFER)


# --------------------------
# EXCHANGE SIMULATION CORE
# --------------------------
def simulate_matching(num_orders=10000):
    """Match every single order and log every resulting trade."""
    engine = MatchingEngine(seed=42)
    total_trades = 0

    start_time = time.time()
    for i in range(num_orders):
        # Randomize order properties
        side = random.choice([Side.BUY, Side.SELL])
        price = round(random.uniform(90, 110), 2)
        size = random.randint(1, 100)

        # Alternate limit/market orders
        if random.random() < 0.8:
            order = LimitOrder(
                side=side,
                price=price,
                size=size,
                timestamp=datetime.now(),
                order_id=f"Order_{i}",
                trader_id=f"T{i % 4}",  # simulate 4 traders
            )
        else:
            order = MarketOrder(
                side=side,
                size=size,
                timestamp=datetime.now(),
                order_id=f"Order_{i}",
                trader_id=f"T{i % 4}",
            )

        # Match immediately after placing the order
        executed_trades = engine.match(datetime.now(), orders=Orders([order]))
        if executed_trades.trades:
            total_trades += len(executed_trades.trades)
            for t in executed_trades.trades:
                log_trade(t)

    # Final flush
    flush_csv(LOG_BUFFER)
    end_time = time.time()

    elapsed = end_time - start_time
    print(f"\n Simulation finished in {elapsed:.2f} s for {num_orders} orders.")
    print(f"   Trades executed: {total_trades}")
    print(f"   Avg time per order: {(elapsed / num_orders) * 1000:.3f} ms")
    print(f"   Logged to: {LOG_FILE}")


if __name__ == "__main__":
    print("🚀 Starting full per-order matching + CSV logging benchmark...")
    simulate_matching(num_orders=10000)
