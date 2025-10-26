"""Portfolio Service - Calculate portfolio metrics and P&L"""
from typing import Dict, List, Optional
import pandas as pd
import database.models as db
from config import constants

def calculate_portfolio_value(user_id: str, all_stock_data: Dict) -> Dict:
    """Calculate total portfolio value and metrics"""
    portfolio = db.get_portfolio(user_id)
    if not portfolio:
        return {}
    
    cash = portfolio.get('cash_balance', constants.INITIAL_CASH)
    holdings = portfolio.get('holdings', {})
    
    total_stock_value = 0
    holdings_details = []
    
    for ticker, quantity in holdings.items():
        if quantity > 0 and ticker in all_stock_data and all_stock_data[ticker]:
            stock_data = all_stock_data[ticker]
            current_price = stock_data.get('current_price', 0)
            value = quantity * current_price
            total_stock_value += value
            
            holdings_details.append({
                'ticker': ticker,
                'name': stock_data.get('name', ticker),
                'quantity': quantity,
                'current_price': current_price,
                'value': value,
                'change_percent': stock_data.get('change_percent', 0)
            })
    
    total_value = cash + total_stock_value
    
    return {
        'cash': cash,
        'total_stock_value': total_stock_value,
        'total_value': total_value,
        'holdings': holdings_details
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
    """Execute buy transaction"""
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
