"""Portfolio Service - Calculate portfolio metrics and P&L"""
from typing import Dict, List, Optional
import pandas as pd
import database.models as db
from config import constants

def calculate_portfolio_value(user_id: str, all_stock_data: Dict) -> Dict:
    """Calculate total portfolio value and metrics with P&L tracking"""
    portfolio = db.get_portfolio(user_id)
    if not portfolio:
        return {}
    
    cash = portfolio.get('cash_balance', constants.INITIAL_CASH)
    holdings = portfolio.get('holdings', {})
    holdings_details = portfolio.get('holdings_details', {})
    
    total_stock_value = 0
    total_cost_basis = 0
    total_unrealized_pnl = 0
    holdings_list = []
    
    for ticker, quantity in holdings.items():
        if quantity > 0 and ticker in all_stock_data and all_stock_data[ticker]:
            stock_data = all_stock_data[ticker]
            current_price = stock_data.get('current_price', 0)
            current_value = quantity * current_price
            total_stock_value += current_value
            
            # Get purchase details
            holding_detail = holdings_details.get(ticker, {})
            purchase_price = holding_detail.get('purchase_price', current_price)
            purchase_date = holding_detail.get('purchase_date', 'Unknown')
            
            # Calculate P&L
            cost_basis = quantity * purchase_price
            total_cost_basis += cost_basis
            
            unrealized_pnl = current_value - cost_basis
            total_unrealized_pnl += unrealized_pnl
            
            pnl_percent = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            holdings_list.append({
                'ticker': ticker,
                'name': stock_data.get('name', ticker),
                'quantity': quantity,
                'current_price': current_price,
                'purchase_price': purchase_price,
                'purchase_date': purchase_date,
                'current_value': current_value,
                'cost_basis': cost_basis,
                'unrealized_pnl': unrealized_pnl,
                'pnl_percent': pnl_percent,
                'daily_change_percent': stock_data.get('change_percent', 0)
            })
    
    total_value = cash + total_stock_value
    total_return_percent = (total_unrealized_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0
    
    return {
        'cash': cash,
        'total_stock_value': total_stock_value,
        'total_cost_basis': total_cost_basis,
        'total_unrealized_pnl': total_unrealized_pnl,
        'total_return_percent': total_return_percent,
        'total_value': total_value,
        'holdings': holdings_list
    }

def calculate_portfolio_return(user_id: str) -> float:
    """Calculate total return percentage"""
    portfolio = db.get_portfolio(user_id)
    if not portfolio:
        return 0.0
    
    initial_cash = constants.INITIAL_CASH
    current_value = portfolio.get('total_value', initial_cash)
    
    return_percent = ((current_value - initial_cash) / initial_cash) * 100
    return round(return_percent, 2)

def can_buy_stock(user_id: str, price: float, quantity: float) -> tuple[bool, str]:
    """Check if user can afford to buy stock"""
    portfolio = db.get_portfolio(user_id)
    if not portfolio:
        return False, "Portfolio not found"
    
    cash = portfolio.get('cash_balance', 0)
    total_cost = price * quantity
    
    if total_cost > cash:
        return False, f"Insufficient cash. Need {total_cost:,.0f} HKD, have {cash:,.0f} HKD"
    
    return True, "OK"

def can_sell_stock(user_id: str, ticker: str, quantity: float) -> tuple[bool, str]:
    """Check if user has enough shares to sell"""
    portfolio = db.get_portfolio(user_id)
    if not portfolio:
        return False, "Portfolio not found"
    
    holdings = portfolio.get('holdings', {})
    current_quantity = holdings.get(ticker, 0)
    
    if quantity > current_quantity:
        return False, f"Insufficient shares. Own {current_quantity} shares, trying to sell {quantity}"
    
    return True, "OK"

def execute_buy(user_id: str, ticker: str, price: float, quantity: float) -> bool:
    """Execute buy transaction with purchase price tracking"""
    # Check cash
    can_buy, msg = can_buy_stock(user_id, price, quantity)
    if not can_buy:
        return False
    
    portfolio = db.get_portfolio(user_id)
    if not portfolio:
        return False
    
    # Update cash
    new_cash = portfolio['cash_balance'] - (price * quantity)
    
    # Update holdings
    holdings = portfolio.get('holdings', {})
    current_quantity = holdings.get(ticker, 0)
    holdings[ticker] = current_quantity + quantity
    
    # Update holdings details with purchase price
    from datetime import datetime
    db.update_holdings_details(user_id, ticker, price, datetime.utcnow(), quantity)
    
    # Save to database
    db.update_portfolio(user_id, {'cash_balance': new_cash, 'holdings': holdings})
    
    # Create transaction record
    db.create_transaction(user_id, ticker, 'buy', quantity, price)
    
    return True

def execute_sell(user_id: str, ticker: str, price: float, quantity: float) -> bool:
    """Execute sell transaction"""
    # Check holdings
    can_sell, msg = can_sell_stock(user_id, ticker, quantity)
    if not can_sell:
        return False
    
    portfolio = db.get_portfolio(user_id)
    if not portfolio:
        return False
    
    # Update cash
    proceeds = price * quantity
    new_cash = portfolio['cash_balance'] + proceeds
    
    # Update holdings
    holdings = portfolio.get('holdings', {})
    current_quantity = holdings.get(ticker, 0)
    new_quantity = current_quantity - quantity
    
    if new_quantity <= 0:
        holdings.pop(ticker, None)
    else:
        holdings[ticker] = new_quantity
    
    # Save to database
    db.update_portfolio(user_id, {'cash_balance': new_cash, 'holdings': holdings})
    
    # Create transaction record
    db.create_transaction(user_id, ticker, 'sell', quantity, price)
    
    return True

def refresh_portfolio_data(user_id: str) -> Dict:
    """Refresh all stock data for portfolio and update last refresh time"""
    import services.stock_data as stock_service
    from datetime import datetime, timedelta
    
    portfolio = db.get_portfolio(user_id)
    if not portfolio:
        return {}
    
    holdings = portfolio.get('holdings', {})
    if not holdings:
        return {}
    
    # Get fresh data for all holdings
    tickers = list(holdings.keys())
    all_stock_data = stock_service.get_multiple_stocks(tickers, use_cache=False)
    
    # Update last refresh time
    db.update_portfolio_refresh_time(user_id)
    
    # Calculate updated portfolio value
    portfolio_value = calculate_portfolio_value(user_id, all_stock_data)
    
    return {
        'portfolio_value': portfolio_value,
        'last_refresh': datetime.utcnow(),
        'stocks_refreshed': len([t for t in tickers if t in all_stock_data and all_stock_data[t]])
    }
