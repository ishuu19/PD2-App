"""Automated Scheduler Service for Daily Stock Data Refresh and Alert Checking"""
import time
import threading
from datetime import datetime
import streamlit as st
import database.models as db
import services.stock_data as stock_service
import services.alert_service as alert_service
from typing import Dict, List

# Try to import schedule, fallback to alternative if not available
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    print("WARNING: Schedule module not available. Scheduler will use alternative timing method.")

class SchedulerService:
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        
    def start_scheduler(self):
        """Start the automated scheduler"""
        if self.running:
            return
            
        self.running = True
        
        if SCHEDULE_AVAILABLE:
            # Use schedule library for precise timing
            schedule.every().day.at("00:00").do(self._daily_automated_tasks)
            self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
            self.scheduler_thread.start()
            print("Automated scheduler started - Daily tasks scheduled for 12:00 AM")
        else:
            # Use alternative timing method
            self.scheduler_thread = threading.Thread(target=self._run_scheduler_alternative, daemon=True)
            self.scheduler_thread.start()
            print("Automated scheduler started (alternative mode) - Daily tasks will run every 24 hours")
    
    def stop_scheduler(self):
        """Stop the automated scheduler"""
        self.running = False
        if SCHEDULE_AVAILABLE:
            schedule.clear()
        print("Automated scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop (with schedule library)"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _run_scheduler_alternative(self):
        """Run the scheduler loop (alternative method without schedule library)"""
        last_run = None
        while self.running:
            now = datetime.now()
            # Run daily at midnight (00:00)
            if now.hour == 0 and now.minute == 0:
                if last_run is None or (now - last_run).days >= 1:
                    self._daily_automated_tasks()
                    last_run = now
            time.sleep(60)  # Check every minute
    
    def _daily_automated_tasks(self):
        """Execute daily automated tasks"""
        print(f"Starting daily automated tasks at {datetime.now()}")
        
        try:
            # Step 1: Refresh stock data
            print("Refreshing stock data...")
            self._refresh_stock_data()
            
            # Step 2: Check all alerts and send emails
            print("Checking alerts and sending emails...")
            self._check_and_send_alerts()
            
            print("Daily automated tasks completed successfully")
            
        except Exception as e:
            print(f"Error in daily automated tasks: {str(e)}")
    
    def _refresh_stock_data(self):
        """Refresh stock data for all users"""
        try:
            # Force refresh of stock data by clearing session state
            if hasattr(st, 'session_state'):
                if 'top_stocks_data' in st.session_state:
                    del st.session_state.top_stocks_data
                if 'last_refresh_time' in st.session_state:
                    del st.session_state.last_refresh_time
            
            # Load fresh stock data
            stock_service.get_all_stocks()
            print("Stock data refreshed successfully")
            
        except Exception as e:
            print(f"Error refreshing stock data: {str(e)}")
    
    def _check_and_send_alerts(self):
        """Check all active alerts and send emails if criteria are met"""
        try:
            # Get all users with active alerts
            users_with_alerts = db.get_users_with_active_alerts()
            
            if not users_with_alerts:
                print("No users with active alerts found")
                return
            
            print(f"Found {len(users_with_alerts)} users with active alerts")
            
            # Get fresh stock data
            all_stocks_data = stock_service.get_all_stocks()
            
            emails_sent = 0
            alerts_checked = 0
            
            for user in users_with_alerts:
                user_id = user['_id']
                user_email = user.get('email')
                
                if not user_email:
                    print(f"WARNING: User {user_id} has no email address, skipping")
                    continue
                
                # Get user's active alerts
                alerts = db.get_alerts(user_id, active_only=True)
                
                for alert in alerts:
                    alerts_checked += 1
                    ticker = alert['ticker']
                    criteria = alert['criteria']
                    threshold = alert['threshold']
                    
                    # Check if we have data for this ticker
                    if ticker not in all_stocks_data:
                        print(f"WARNING: No data available for {ticker}, skipping alert")
                        continue
                    
                    stock_data = all_stocks_data[ticker]
                    
                    # Check if alert criteria is met
                    triggered = alert_service.check_alert_criteria(stock_data, criteria, threshold)
                    
                    if triggered:
                        print(f"ALERT: Alert triggered for {user_email}: {ticker} - {criteria}")
                        
                        # Send email
                        success = alert_service.send_alert_email(
                            user_email,
                            ticker,
                            criteria,
                            threshold,
                            stock_data,
                            {
                                'threshold': threshold,
                                'current_value': stock_data['current_price'],
                                'change': stock_data['change_percent']
                            }
                        )
                        
                        if success:
                            emails_sent += 1
                            print(f"Email sent successfully to {user_email}")
                            
                            # Update alert last triggered timestamp
                            db.update_alert_last_triggered(str(alert['_id']))
                        else:
                            print(f"Failed to send email to {user_email}")
                    else:
                        print(f"Alert not triggered for {ticker} - {criteria} (Current: ${stock_data['current_price']:.2f}, Threshold: ${threshold:.2f})")
            
            print(f"Alert checking completed: {alerts_checked} alerts checked, {emails_sent} emails sent")
            
        except Exception as e:
            print(f"Error checking alerts: {str(e)}")
    
    def get_scheduler_status(self) -> Dict:
        """Get current scheduler status"""
        status = {
            'running': self.running,
            'schedule_available': SCHEDULE_AVAILABLE
        }
        
        if SCHEDULE_AVAILABLE:
            status.update({
                'next_run': schedule.next_run() if schedule.jobs else None,
                'jobs_count': len(schedule.jobs)
            })
        else:
            status.update({
                'next_run': 'Alternative timing method (daily at midnight)',
                'jobs_count': 1 if self.running else 0
            })
        
        return status
    
    def run_manual_check(self):
        """Manually run the alert checking process (for testing)"""
        print("Running manual alert check...")
        self._check_and_send_alerts()

# Global scheduler instance
scheduler = SchedulerService()

def start_automated_scheduler():
    """Start the automated scheduler"""
    scheduler.start_scheduler()

def stop_automated_scheduler():
    """Stop the automated scheduler"""
    scheduler.stop_scheduler()

def get_scheduler_status():
    """Get scheduler status"""
    return scheduler.get_scheduler_status()

def run_manual_alert_check():
    """Run manual alert check for testing"""
    scheduler.run_manual_check()
