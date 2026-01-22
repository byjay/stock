import asyncio
import os
import sys
sys.path.append(os.getcwd())

from core.dual_engine_manager import DualEngineManager

async def test_tri_engine_status():
    print("🧪 [Test] Tri-Engine Status Verification Starting...")
    manager = DualEngineManager(initial_balance_usd=10000.0)
    
    # Initialize and fetch balances
    await manager.update_balances()
    
    status = manager.get_status()
    print("\n📊 [Status Report]")
    print(f"   • Mode: {status['mode']}")
    print(f"   • Real Balance: {status['balances']['real']:,.0f} KRW")
    print(f"   • Virtual Sim: ${status['balances']['virtual']:,.0f}")
    print(f"   • Mock Invest: {status['balances']['mock']:,.0f} KRW")
    
    if status['balances']['mock'] > 0:
        print("\n✅ Verification SUCCESS: Mock balance retrieved.")
    else:
        print("\n⚠️ Verification WARNING: Mock balance is 0. Check API connectivity.")

if __name__ == "__main__":
    asyncio.run(test_tri_engine_status())
