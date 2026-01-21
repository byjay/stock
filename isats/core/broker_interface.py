from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BrokerInterface(ABC):
    """
    [ISATS Core] Abstract Broker Interface
    Standardizes methods for all connected brokers (KIS, Alpaca, etc.)
    """

    @abstractmethod
    def get_token(self):
        """Authentication / Token Refresh"""
        pass

    @abstractmethod
    async def fetch_price(self, code: str) -> Dict[str, Any]:
        """
        Fetch Real-Time Price
        Returns: {"code": str, "price": float, "time": str, ...}
        """
        pass

    @abstractmethod
    def create_order(self, side: str, code: str, qty: int, price: float) -> Dict[str, Any]:
        """
        Execute Order
        Returns: {"id": str, "status": str, "msg": str}
        """
        pass

    @abstractmethod
    async def fetch_balance(self) -> Dict[str, float]:
        """
        Fetch Account Balance
        Returns: {"total_cash": float, "total_asset": float}
        """
        pass
    
    @abstractmethod
    async def fetch_history(self, code: str, days: int) -> List[Dict[str, Any]]:
        """
        Fetch Historical Candles
        """
        pass
