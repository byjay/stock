import sys
import os
import asyncio

# Path setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from backend.core.korea_inv_wrapper import KoreaInvWrapper

async def main():
    print("🚀 [TEST] Starting Real API Verification...")
    
    # 1. Initialize Wrapper
    # allow_mock_fallback=False to strictly test Real API if keys are present
    broker = KoreaInvWrapper(allow_mock_fallback=False)
    
    # 2. Check Mode
    if broker.mock_mode:
        print("⚠️ [WARNING] System is in MOCK MODE.")
        print("   Reason: API Keys in secrets.yaml are likely default/missing.")
        print("   Please update 'c:\\Users\\FREE\\Desktop\\주식\\isats\\secrets.yaml' with real keys.")
    else:
        print("✅ [INFO] System is in REAL MODE.")

    # 3. Get Token
    print("\n🔑 Requesting Token...")
    try:
        broker.get_token()
        if broker.access_token and broker.access_token != "MOCK_TOKEN":
            print(f"   Success! Token: {broker.access_token[:10]}...")
        elif broker.access_token == "MOCK_TOKEN":
             print("   [Mock Token] System is simulating connection.")
        else:
            print("   Failed to get token.")
    except Exception as e:
        print(f"   Token Error: {e}")

    # 4. Fetch Balance
    print("\n💰 Checking Balance...")
    balance = await broker.fetch_balance()
    print(f"   Result: {balance}")

    # 5. Fetch Price (Samsung Elec)
    print("\n📈 Checking Price (005930 - Samsung Electronics)...")
    price = await broker.fetch_price("005930")
    print(f"   Result: {price}")
    
    print("\n🏁 Verification Complete.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
