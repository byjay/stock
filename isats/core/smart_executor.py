import time
import pandas as pd
import numpy as np
import logging

class SmartExecutor:
    """
    Algorithmic Order Execution Engine (Stealth Mode)
    Implements TWAP/VWAP to minimize market impact and slippage.
    """
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)

    def execute_twap(self, symbol, total_qty, duration_min, side='BUY'):
        """
        Time Weighted Average Price execution.
        Slices order into equal parts over time.
        """
        slices = max(1, duration_min)
        qty_per_slice = total_qty // slices
        remainder = total_qty % slices
        
        self.logger.info(f"[TWAP] {side} {symbol}: {total_qty} units over {duration_min} min. Slice: {qty_per_slice}")
        
        for i in range(slices):
            current_qty = qty_per_slice + (1 if i < remainder else 0)
            if current_qty > 0:
                # In real world, this would call core_trader.order()
                self.logger.debug(f"[TWAP-STEP] {i+1}/{slices}: Submitting {side} {symbol} {current_qty}")
                # Wait for next slice (simplified for simulation/structure)
                # time.sleep(60) 
        
        return True

    def execute_vwap(self, symbol, total_qty, target_vwap_df, side='BUY'):
        """
        Volume Weighted Average Price execution.
        Follows the historical or real-time volume profile.
        """
        if target_vwap_df is None or target_vwap_df.empty:
            return self.execute_twap(symbol, total_qty, 5, side)

        self.logger.info(f"[VWAP] {side} {symbol}: {total_qty} units following volume profile.")
        # Logic to slice based on 'volume' column ratios
        total_volume = target_vwap_df['volume'].sum()
        target_vwap_df['slice_ratio'] = target_vwap_df['volume'] / total_volume
        
        for idx, row in target_vwap_df.iterrows():
            slice_qty = int(total_qty * row['slice_ratio'])
            if slice_qty > 0:
                self.logger.debug(f"[VWAP-STEP] Submitting {side} {symbol} {slice_qty} at {row.name}")
        
        return True

    def calculate_slippage(self, base_price, order_qty, avg_volume, volatility, spread_pct=0.0005):
        """
        [Phase E] Execution Precision & Slippage Mastery
        Slippage = (Fixed Spread Cost) + (Market Impact Cost)
        
        - spread_pct: Default 0.05% for liquid stocks.
        - Market Impact: Square root model (simplified) or linear ratio.
        """
        if avg_volume == 0: return base_price * 1.01 # Severe penalty for zero liquidity
        
        # 1. Bid-Ask Spread Cost (Half-spread)
        spread_cost = base_price * (spread_pct / 2)
        
        # 2. Market Impact Cost (Non-linear impact based on size vs volume)
        # Impact Factor increases as order_qty/avg_volume increases
        size_ratio = order_qty / avg_volume
        impact_cost = base_price * (size_ratio * volatility * 0.5)
        
        total_drift = spread_cost + impact_cost
        real_price = base_price + total_drift if order_qty > 0 else base_price - total_drift
        
        self.logger.debug(f"[SLIPPAGE] Base: {base_price:.0f}, Impact: {impact_cost:.2f}, Real: {real_price:.2f}")
        return real_price
