import logging

logger = logging.getLogger("Core:PortfolioManager")

class PortfolioManager:
    """
    [CRITICAL] Money Management Module
    Enforces the User's "Strategic Guide":
    - How much to buy? (Position Sizing)
    - How many stocks? (Max Slots)
    """
    def __init__(self, total_capital=100_000_000, max_slots=5, risk_per_trade=0.02):
        self.total_capital = total_capital
        self.max_slots = max_slots
        self.risk_per_trade = risk_per_trade # Risk 2% of capital per trade
        
        # Track current positions
        # { "Code": { "qty": 10, "entry_price": 50000, "current_val": 500000 } }
        self.positions = {}
        
    def can_open_new_position(self) -> bool:
        if len(self.positions) >= self.max_slots:
            logger.warning(f"🚫 Portfolio Full: {len(self.positions)}/{self.max_slots} slots used.")
            return False
        return True

    def calculate_position_size(self, entry_price: float, stop_loss_pct: float = 0.01) -> int:
        """
        Calculates quantity based on Risk.
        Rule: Loss Amount = Total Capital * Risk Per Trade
        Loss Amount = Qty * (Entry Price * Stop Loss Pct)
        => Qty = (Total Capital * Risk) / (Entry * Stop Loss Pct)
        """
        if entry_price <= 0: return 0
        
        risk_amount = self.total_capital * self.risk_per_trade
        loss_per_share = entry_price * stop_loss_pct
        
        qty = int(risk_amount / loss_per_share)
        
        # Hardware Check: Don't exceed remaining cash (Simplified)
        # In real engine, we check dynamic cash balance.
        # estimated_cost = qty * entry_price
        # if estimated_cost > self.current_cash: ...
        
        logger.info(f"💰 Position Sizing: Capital({self.total_capital}) Risk({self.risk_per_trade*100}%) -> Allocating {qty} shares @ {entry_price}")
        return qty

    def add_position(self, code, qty, price):
        self.positions[code] = {"qty": qty, "entry_price": price}
        logger.info(f"✅ Position Recorded: {code} ({qty} shares)")

    def remove_position(self, code):
        if code in self.positions:
            del self.positions[code]
            logger.info(f"👋 Position Removed: {code}")

    def get_performance_metrics(self):
        """
        [Mobile View] Returns Daily/Monthly Performance.
        """
        # Stub: In real system, this would aggregate `self.trade_log` by date.
        return {
            "daily_pnl": 150000,
            "monthly_pnl": 3200000,
            "accumulated_return": 12.5, # %
            "win_rate": 65.0, # %
            "best_trade": {"code": "005930", "profit": 500000},
            "worst_trade": {"code": "000660", "profit": -100000}
        }
