import sys
import os
import asyncio
import requests
import json
import yaml

# Path setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

def main():
    print("🐞 [DEBUG] Starting KIS API Diagnosis...")
    
    # 1. Load Config Directly to verify parsing
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend/core")) # Secrets in backend/core? No, root/isats?
    # Wrapper looks in backend/core/secrets.yaml but step 4 showed secrets.yaml in C:\Users\FREE\Desktop\주식\isats
    # Let's try the path the wrapper uses.
    
    # The wrapper says:
    # base_dir = os.path.dirname(os.path.abspath(__file__)) (which is backend/core)
    # secret_path = os.path.join(base_dir, "secrets.yaml")
    
    # But files in step 4 showed secrets.yaml in `isats` (root), NOT in `backend/core`.
    # `backend/core` listing in step 41 did NOT show secrets.yaml.
    # WAIT!
    # If `korea_inv_wrapper.py` is looking for `backend/core/secrets.yaml` and it DOES NOT EXIST, it might fail?
    # But the wrapper logic says:
    # try: ... with open(secret_path, "r") ...
    
    # If the file didn't exist, it would hit `except Exception` and default to Mock.
    # But the Verification Script said "System is in REAL MODE".
    # This implies `korea_inv_wrapper.py` SUCCESSFULLY loaded a secrets file.
    # Did I miss `secrets.yaml` in `backend/core` in step 41?
    # Step 41 output:
    # {"name":"secrets.yaml","sizeBytes":"344"}  <-- YES, IT IS THERE!
    # I missed it in my thought process.
    
    # Okay, so there is a `secrets.yaml` in `backend/core`.
    # Let's read THAT file to see if it's correct.
    # The user might have edited the ROOT `secrets.yaml` but not the one in `backend/core`!
    
    # I'll check both paths.
    
    wrapper_secret_path = os.path.join(os.path.dirname(__file__), "../backend/core/secrets.yaml")
    root_secret_path = os.path.join(os.path.dirname(__file__), "../secrets.yaml")
    
    print(f"Checking Wrapper Config: {wrapper_secret_path}")
    if os.path.exists(wrapper_secret_path):
        with open(wrapper_secret_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            app_key = config['key'].get('kis_app_key', '')
            print(f"   [Wrapper] AppKey matches 'PASTE_YOUR'? {'Yes' if 'PASTE_YOUR' in app_key else 'No'}")
            print(f"   [Wrapper] AccountNum: {config['account'].get('kis_account_num')}")
    else:
        print("   [Wrapper] File NOT FOUND.")

    # 2. Re-run manual request
    # If wrapper loaded real keys, let's try to replicate the fail.
    
    # ... (Actual debug logic)
    
    # Wait, if `verify_real_api` said REAL MODE, then `backend/core/secrets.yaml` MUST have valid keys (no 'PASTE_YOUR').
    # So the file check passes.
    
    # Let's inspect the `response.text` from the API.
    
    from backend.core.korea_inv_wrapper import KoreaInvWrapper
    broker = KoreaInvWrapper(allow_mock_fallback=False)
    
    print(f"\n🔑 Token Status: {'Available' if broker.access_token else 'None'}")
    if not broker.access_token:
        broker.get_token()
    
    if not broker.access_token:
        print("❌ Failed to get token.")
        return

    print("\nREQUEST: Fetch Balance (Raw Debug)")
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {broker.access_token}",
        "appkey": broker.app_key,
        "appsecret": broker.secret_key,
        "tr_id": "TTTC8434R"
    }
    params = {
        "CANO": broker.account_num,
        "ACNT_PRDT_CD": "01",
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "N",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "00",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    
    print(f"   Endpoint: {broker.base_url}/u2/u0112/v1/inquire-balance")
    print(f"   Account: {broker.account_num}")
    
    try:
        res = requests.get(f"{broker.base_url}/u2/u0112/v1/inquire-balance", headers=headers, params=params)
        print(f"   Status Code: {res.status_code}")
        print(f"   Response Text: {res.text[:500]}") # Print first 500 chars
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    main()
