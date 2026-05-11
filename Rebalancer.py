import yfinance as yf
from typing import Dict, Tuple

# Global portfolio storage
portfolio = {}
current_prices = {}


def set_portfolio(holdings: Dict[str, Tuple[float, float]]) -> None:
    """
    Set the current portfolio with target allocations.
    
    Args:
        holdings: Dictionary with format {
            'TICKER': (quantity, target_allocation_percent)
        }
        Example: {'AAPL': (10, 0.40), 'MSFT': (5, 0.30), 'CASH': (1000, 0.30)}
    """
    global portfolio
    portfolio = holdings
    print(f"Portfolio set with {len(holdings)} assets")
    print(f"Portfolio: {holdings}")


def get_current_prices(tickers: list) -> Dict[str, float]:
    """
    Fetch current prices for given tickers using yFinance.
    
    Args:
        tickers: List of ticker symbols (e.g., ['AAPL', 'MSFT'])
    
    Returns:
        Dictionary with format {'TICKER': current_price}
    """
    global current_prices
    
    try:
        # Remove 'CASH' if present (it doesn't have a price)
        tickers_to_fetch = [t for t in tickers if t.upper() != 'CASH']
        
        if not tickers_to_fetch:
            current_prices = {}
            return {}
        
        # Fetch prices
        data = yf.download(tickers_to_fetch, period='1d', progress=False)
        
        # Helper function to extract float value
        def get_float_value(val):
            if hasattr(val, 'item'):  # numpy/pandas scalar
                return float(val.item())
            return float(val)
        
        # Handle single ticker vs multiple
        if len(tickers_to_fetch) == 1:
            price = get_float_value(data['Close'].iloc[-1])
            current_prices = {tickers_to_fetch[0]: price}
        else:
            prices_series = data['Close'].iloc[-1]
            current_prices = {k: get_float_value(v) for k, v in prices_series.items()}
        
        # Add cash with price of 1
        if 'CASH' in tickers:
            current_prices['CASH'] = 1.0
        
        print(f"Current prices fetched: {current_prices}")
        return current_prices
        
    except Exception as e:
        print(f"Error fetching prices: {e}")
        return {}


def check_rebalance(threshold: float = 5.0) -> Dict:
    """
    Check if portfolio needs rebalancing based on threshold.
    
    Args:
        threshold: Rebalancing threshold in percentage (default 5%)
    
    Returns:
        Dictionary with format {
            'needs_rebalance': bool,
            'current_allocations': {ticker: current_percent},
            'target_allocations': {ticker: target_percent},
            'differences': {ticker: difference_percent},
            'assets_to_adjust': list of tickers exceeding threshold
        }
    """
    if not portfolio or not current_prices:
        print("Error: Portfolio or prices not set")
        return {'needs_rebalance': False}
    
    # Calculate current portfolio value
    portfolio_value = 0
    holdings_value = {}
    
    for ticker, (quantity, target_alloc) in portfolio.items():
        price_val = current_prices.get(ticker, 0)
        price = float(price_val) if price_val != 0 else 0
        value = quantity * price
        holdings_value[ticker] = value
        portfolio_value += value
    
    # Calculate current vs target allocations
    current_allocations = {}
    target_allocations = {}
    differences = {}
    assets_to_adjust = []
    
    for ticker, (_, target_alloc) in portfolio.items():
        current_alloc = (holdings_value.get(ticker, 0) / portfolio_value * 100) if portfolio_value > 0 else 0
        current_allocations[ticker] = round(current_alloc, 2)
        target_allocations[ticker] = target_alloc * 100
        diff = abs(current_alloc - (target_alloc * 100))
        differences[ticker] = round(diff, 2)
        
        if diff > threshold:
            assets_to_adjust.append(ticker)
    
    needs_rebalance = len(assets_to_adjust) > 0
    
    result = {
        'needs_rebalance': needs_rebalance,
        'portfolio_value': round(portfolio_value, 2),
        'current_allocations': current_allocations,
        'target_allocations': target_allocations,
        'differences': differences,
        'assets_to_adjust': assets_to_adjust,
        'threshold': threshold
    }
    
    print(f"\n--- Rebalance Check ---")
    print(f"Portfolio Value: ${result['portfolio_value']}")
    print(f"Needs Rebalance: {needs_rebalance}")
    print(f"Current vs Target Allocations:")
    for ticker in portfolio:
        print(f"  {ticker}: {current_allocations[ticker]}% (target: {target_allocations[ticker]}%, diff: {differences[ticker]}%)")
    # Recommended trades block: compute per-ticker buy/sell recommendation to reach target
    print(f"\nRecommended Trades:")
    any_trade = False
    for ticker, (quantity, target_alloc) in portfolio.items():
        price_val = current_prices.get(ticker, 0)
        try:
            price = float(price_val) if price_val is not None else 0.0
        except Exception:
            price = 0.0

        # compute dollar and share change needed to reach target
        current_value = holdings_value.get(ticker, 0)
        target_value = (target_alloc * result['portfolio_value'])
        dollar_change = target_value - current_value
        # avoid division by zero
        shares_change = (dollar_change / price) if price else 0.0

        if abs(shares_change) < 1e-12:
            continue

        any_trade = True
        if shares_change > 0:
            sign = '+'
            action = 'BUY'
        else:
            sign = '-'
            action = 'SELL'

        # print with arrow prefix, + for buys and - for sells
        print(f"  → {ticker}: {action} {sign}${abs(dollar_change):.2f}, {sign}{abs(shares_change):.4f} shares")

    if needs_rebalance:
        print(f"Assets exceeding {threshold}% threshold: {assets_to_adjust}")
    
    return result


def main():
    """Interactive CLI for portfolio rebalancer."""
    print("=" * 50)
    print("Portfolio Rebalancer CLI")
    print("=" * 50)
    
    threshold = 5.0
    
    while True:
        print("\nOptions:")
        print("1. Set portfolio")
        print("2. Get current prices")
        print("3. Check rebalance (5% threshold)")
        print("4. Set custom threshold")
        print("5. View portfolio")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            print("\nSet portfolio holdings (format: ticker quantity target_percent)")
            print("Example: SPY 20 0.50")
            holdings = {}
            while True:
                line = input("Enter holding (or 'done'): ").strip()
                if line.lower() == 'done':
                    break
                try:
                    parts = line.split()
                    if len(parts) != 3:
                        print("Invalid format. Use: ticker quantity target_percent")
                        continue
                    ticker = parts[0].upper()
                    quantity = float(parts[1])
                    target = float(parts[2])
                    holdings[ticker] = (quantity, target)
                except ValueError:
                    print("Invalid input. Please use: ticker quantity target_percent")
            
            if holdings:
                set_portfolio(holdings)
            else:
                print("No holdings entered.")
        
        elif choice == '2':
            if not portfolio:
                print("Error: Portfolio not set. Use option 1 first.")
                continue
            tickers = list(portfolio.keys())
            get_current_prices(tickers)
        
        elif choice == '3':
            if not portfolio or not current_prices:
                print("Error: Portfolio and prices not set.")
                continue
            check_rebalance(threshold=threshold)
        
        elif choice == '4':
            try:
                new_threshold = float(input("Enter new threshold (%): "))
                threshold = new_threshold
                print(f"Threshold set to {threshold}%")
            except ValueError:
                print("Invalid input. Please enter a number.")
        
        elif choice == '5':
            if not portfolio:
                print("Portfolio not set.")
            else:
                print("\nCurrent Portfolio:")
                for ticker, (qty, target) in portfolio.items():
                    print(f"  {ticker}: {qty} shares (target: {target*100}%)")
                if current_prices:
                    print("\nCurrent Prices:")
                    for ticker, price in current_prices.items():
                        price_val = float(price)
                        print(f"  {ticker}: ${price_val:.2f}")
        
        elif choice == '6':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter 1-6.")


if __name__ == "__main__":
    main()
