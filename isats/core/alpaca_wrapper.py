import logging
import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from backend.core.broker_interface import BrokerInterface

logger = logging.getLogger("AlpacaWrapper")

class AlpacaWrapper(BrokerInterface):
    """
    [ISATS Core] Alpaca Markets API Wrapper (US Stocks)
    Implements BrokerInterface for reliable US equity trading.
    """
    def __init__(self, api_key=None, secret_key=None, paper_mode=True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper_mode = paper_mode
        self.base_url = "https://paper-api.alpaca.markets" if paper_mode else "https://api.alpaca.markets"
        
        # Load from secrets if not provided
        if not api_key:
            self._load_config()

    def _load_config(self):
        try:
            import yaml
            base_dir = os.path.dirname(os.path.abspath(__file__))
            secret_path = os.path.join(base_dir, "secrets.yaml")
            
            if os.path.exists(secret_path):
                with open(secret_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    alpaca_cfg = config.get('alpaca', {})
                    self.api_key = alpaca_cfg.get('api_key')
                    self.secret_key = alpaca_cfg.get('secret_key')
                    self.paper_mode = alpaca_cfg.get('paper_mode', True)
                    
                    if self.paper_mode:
                        self.base_url = "https://paper-api.alpaca.markets"
                    else:
                        self.base_url = "https://api.alpaca.markets"
                        
                    if self.api_key and "PASTE_YOUR" not in self.api_key:
                        logger.info(f"🦙 [Alpaca] Credentials Loaded ({'PAPER' if self.paper_mode else 'LIVE'})")
                    else:
                        logger.warning("⚠️ [Alpaca] No valid keys found. Mock Mode effective.")
            else:
                logger.warning("⚠️ [Alpaca] secrets.yaml not found.")
        except Exception as e:
            logger.error(f"❌ [Alpaca] Config Load Error: {e}")

    def get_token(self):
        # Alpaca uses API Key headers, no OAuth token exchange needed usually.
        # But we can check connectivity here.
        try:
            self.get_account()
            return True
        except:
            return False

    def get_account(self):
        """Internal helper to get account info"""
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key
        }
        res = requests.get(f"{self.base_url}/v2/account", headers=headers)
        if res.status_code == 200:
            return res.json()
        raise Exception(f"Alpaca Error: {res.text}")

    async def fetch_price(self, code: str) -> Dict[str, Any]:
        """
        Fetch Snapshot (Latest Trade)
        Alpaca Data API (v2)
        """
        # Data API URL is different
        data_url = "https://data.sandbox.alpaca.markets" if self.paper_mode else "https://data.alpaca.markets"
        
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key
        }
        
        try:
            # Get latest trade
            url = f"{data_url}/v2/stocks/{code}/trades/latest"
            res = requests.get(url, headers=headers)
            
            if res.status_code == 200:
                data = res.json()
                trade = data.get('trade', {})
                price = trade.get('p', 0.0)
                return {
                    "code": code,
                    "price": price,
                    "time": trade.get('t'),
                    "source": "Alpaca"
                }
            else:
                # Fallback MOCK if keys invalid or sandbox empty
                if "forbidden" in res.text.lower() or "unauthorized" in res.text.lower():
                     import random
                     return {"code": code, "price": random.uniform(100, 200), "source": "Alpaca-MOCK"}
                     
                logger.warning(f"Alpaca Price Fetch Failed: {res.text}")
                return None
        except Exception as e:
            logger.error(f"Alpaca Connection Error: {e}")
            return None

    def create_order(self, side: str, code: str, qty: int, price: float = 0) -> Dict[str, Any]:
        """
        Submit Order
        side: 'buy' or 'sell' (BrokerInterface standard is uppercase, convert here)
        """
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key
        }
        
        side_lower = side.lower()
        order_type = "limit" if price > 0 else "market"
        
        body = {
            "symbol": code,
            "qty": qty,
            "side": side_lower,
            "type": order_type,
            "time_in_force": "day"
        }
        if price > 0:
            body["limit_price"] = price
            
        try:
            res = requests.post(f"{self.base_url}/v2/orders", json=body, headers=headers)
            if res.status_code == 200:
                data = res.json()
                logger.info(f"🚀 [Alpaca] Order Sent: {data['id']}")
                return {"id": data['id'], "status": "submitted", "msg": "Success"}
            else:
                logger.error(f"❌ [Alpaca] Order Failed: {res.text}")
                return {"id": None, "status": "failed", "msg": res.text}
        except Exception as e:
             logger.error(f"❌ [Alpaca] Order Exception: {e}")
             return {"id": None, "status": "error", "msg": str(e)}

    async def fetch_balance(self) -> Dict[str, float]:
        try:
            acct = self.get_account()
            return {
                "total_cash": float(acct.get('cash', 0.0)),
                "total_asset": float(acct.get('portfolio_value', 0.0)),
                "buying_power": float(acct.get('buying_power', 0.0))
            }
        except Exception:
            return {"total_cash": 100000.0, "total_asset": 100000.0} # Mock

    async def fetch_history(self, code: str, days: int) -> List[Dict[str, Any]]:
        # Implement Bar fetch if needed
        return []
