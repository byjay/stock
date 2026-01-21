import logging
import requests
import json
from datetime import datetime
from .broker_interface import BrokerInterface

logger = logging.getLogger("KoreaInvWrapper")

class KoreaInvWrapper(BrokerInterface):
    """
    [NEW] Korea Investment & Securities (KIS) API Wrapper.
    Provides redundancy to Kiwoom and enables web-based trading.
    """
    def __init__(self, app_key=None, secret_key=None, mock_mode=True, allow_mock_fallback=True):
        self.app_key = app_key
        self.secret_key = secret_key
        self.mock_mode = mock_mode
        self.allow_mock_fallback = allow_mock_fallback
        self.access_token = None
        self.base_url = "https://openapi.koreainvestment.com:9443"
        self._load_config() # Auto-load on init

    def _load_config(self):
        """secrets.yaml 동기 로드"""
        try:
            import yaml
            import os
            # [FIX] Use absolute path relative to this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            secret_path = os.path.join(base_dir, "secrets.yaml")
            
            with open(secret_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                self.app_key = config['key']['kis_app_key']
                self.secret_key = config['key']['kis_secret_key']
                # [FIX] Ensure Account Num is 8 digits (remove hyphen if exists)
                raw_acc = str(config['account']['kis_account_num'])
                self.account_num = raw_acc.split('-')[0].strip()
                
                if "PASTE_YOUR" in self.app_key:
                    logger.warning("[KIS] secrets.yaml default values detected. MOCK MODE.")
                    self.mock_mode = True
                else:
                    self.mock_mode = False
                    self.base_url = "https://openapi.koreainvestment.com:9443"
                    logger.info("[KIS] Real Credentials Loaded.")
        except Exception as e:
            logger.warning(f"[KIS] Config Load Failed ({e}). Defaulting to MOCK.")
            self.mock_mode = True
            self.base_url = "https://openapivts.koreainvestment.com:9443"

    def get_token(self):
        """
        [Refactored] 실전 매매를 위한 OAuth2 토큰 발급.
        Follows official sample logic (kis_auth.py) strictly.
        """
        if self.mock_mode:
            self.access_token = "MOCK_TOKEN"
            logger.info("✅ [KIS-MOCK] System Ready (Simulation Mode)")
            return

        # 1. Try to Load Cached Token (File-based, like official sample)
        cached_token = self._read_token_official()
        if cached_token:
            self.access_token = cached_token
            logger.info("✅ [KIS-REAL] Using Cached Token.")
            return

        # 2. Request New Token
        try:
            logger.info("🔑 Requesting New KIS Token...")
            headers = {
                "content-type": "application/json",
            }
            body = {
                "grant_type": "client_credentials",
                "appkey": self.app_key,
                "appsecret": self.secret_key
            }
            
            # Use tokenP endpoint for Real Trading (Official Sample uses this)
            url = f"{self.base_url}/oauth2/tokenP"
            
            res = requests.post(url, headers=headers, data=json.dumps(body))
            
            if res.status_code == 200:
                data = res.json()
                self.access_token = data.get('access_token')
                expired = data.get('access_token_token_expired') # YYYY-MM-DD HH:MM:SS
                
                self._save_token_to_cache_official(self.access_token, expired)
                logger.info(f"✅ [KIS-REAL] New Access Token Issued. (Expires: {expired})")
            else:
                logger.error(f"❌ [KIS] Token Failed: {res.text}")
                
        except Exception as e:
            logger.error(f"❌ [KIS] Connection Error: {e}")

    def _read_token_official(self):
        """Official Sample-style token reading"""
        try:
            import os
            import yaml
            # Use the same path/format as official sample or our own standardized path
            base_dir = os.path.dirname(os.path.abspath(__file__))
            token_path = os.path.join(base_dir, "token.yaml") # Changed to yaml to match structure logic
            
            if not os.path.exists(token_path):
                return None
                
            with open(token_path, encoding='utf-8') as f:
                tkg_tmp = yaml.safe_load(f)
            
            exp_dt = tkg_tmp.get("valid-date")
            now_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if exp_dt > now_dt:
                return tkg_tmp.get("token")
            else:
                return None
        except Exception:
            return None

    def _save_token_to_cache_official(self, token, expired):
        """Official Sample-style token saving"""
        try:
            import os
            base_dir = os.path.dirname(os.path.abspath(__file__))
            token_path = os.path.join(base_dir, "token.yaml")
            
            with open(token_path, "w", encoding="utf-8") as f:
                f.write(f"token: {token}\n")
                f.write(f"valid-date: {expired}\n")
        except Exception as e:
            logger.error(f"Token Cache Save Failed: {e}")

    def _save_token_to_cache(self, token, expired):
        try:
            import os
            base_dir = os.path.dirname(os.path.abspath(__file__))
            token_path = os.path.join(base_dir, "token.json")
            
            with open(token_path, "w") as f:
                json.dump({"access_token": token, "expired": expired}, f)
        except Exception:
            pass

    async def fetch_price(self, code):
        """실시간 현재가 수집 (REST API) - Official Endpoint"""
        if self.mock_mode:
            import random
            return {"code": code, "price": random.randint(50000, 50500), "source": "KIS-MOCK"}
        
        try:
            # [Real API Call] Official Endpoint
            # /uapi/domestic-stock/v1/quotations/inquire-price
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            
            headers = {
                "content-type": "application/json; charset=utf-8",
                 # authorization, appkey, appsecret handled here or in caller?
                 # Wrapper usually handles auth header construction manually or via helper.
                 # Need to include all headers manually as we differ from kis_auth structure.
                "authorization": f"Bearer {self.access_token}",
                "appkey": self.app_key,
                "appsecret": self.secret_key,
                "tr_id": "FHKST01010100",
                "custtype": "P"
            }
            
            # Official sample uses uppercase params keys for some reason in _url_fetch context?
            # domestic_stock_functions.py passes "FID_COND_MRKT_DIV_CODE".
            # Let's match it to be safe.
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": code
            }
            
            res = requests.get(url, headers=headers, params=params)
            
            if res.status_code == 200:
                data = res.json()
                # check if output exists
                if data.get('output'):
                    current_price = int(data['output']['stck_prpr'])
                    return {"code": code, "price": current_price, "source": "KIS-REAL"}
                else:
                    logger.error(f"❌ [PRICE-FAIL] No Output: {data.get('msg1')}")
                    return None
            else:
                logger.error(f"❌ [PRICE-FAIL] Status {res.status_code}: {res.text[:100]}")
                return None
        except Exception as e:
            logger.error(f"Connection Failed: {e}")
            return None

    async def fetch_index(self, index_code="0001"):
        """
        [NEW] Fetch Domestic Index (KOSPI/KOSDAQ).
        index_code: '0001' (KOSPI), '1001' (KOSDAQ)
        Endpoint: /uapi/domestic-stock/v1/quotations/inquire-index-price
        TR_ID: FHPST01010000
        """
        if self.mock_mode:
            import random
            return {"code": index_code, "price": 2500 + random.randint(-10, 10), "change_p": "+0.5%", "source": "KIS-MOCK"}

        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-index-price"
            headers = {
                "content-type": "application/json; charset=utf-8",
                 "authorization": f"Bearer {self.access_token}",
                 "appkey": self.app_key,
                 "appsecret": self.secret_key,
                 "tr_id": "FHPST01010000",
                 "custtype": "P"
            }
            params = {
                "FID_COND_MRKT_DIV_CODE": "U", # U: Index
                "FID_INPUT_ISCD": index_code
            }
            res = requests.get(url, headers=headers, params=params)
            if res.status_code == 200:
                data = res.json()
                if data.get('output'):
                    out = data['output']
                    return {
                        "code": index_code,
                        "price": float(out['bstp_nmix_prpr']),
                        "change_p": f"{float(out['bstp_nmix_prdy_ctrt']):+}%",
                        "source": "KIS-REAL"
                    }
            return None
        except Exception as e:
            logger.error(f"Index Fetch Failed: {e}")
            return None


    def _get_hash_key(self, body):
        """
        [Security] Generate HashKey for POST requests (Orders).
        Uses /uapi/hashkey endpoint.
        """
        try:
            url = f"{self.base_url}/uapi/hashkey"
            headers = {
                "content-type": "application/json; charset=utf-8",
                 "appkey": self.app_key,
                 "appsecret": self.secret_key
            }
            res = requests.post(url, headers=headers, data=json.dumps(body))
            if res.status_code == 200:
                data = res.json()
                return data.get("HASH")
            else:
                logger.warning(f"⚠️ [HASH] Failed: {res.text}")
                return None
        except Exception as e:
            logger.error(f"⚠️ [HASH] Error: {e}")
            return None

    def create_order(self, side: str, code: str, qty: int, price: int):
        """실전 주식 주문 (매수/매도) - Official Endpoint & HashKey"""
        if self.mock_mode:
            logger.info(f"🧪 [MOCK-ORDER] {side} {code} {qty}주 @ {price}원")
            return {"rt_cd": "0", "msg1": "모의주문 완료"}

        try:
            # 1. 결정: 매수(TTTC0802U) vs 매도(TTTC0801U)
            tr_id = "TTTC0802U" if side == "BUY" else "TTTC0801U"
            
            # Official Body Params
            body = {
                "CANO": self.account_num,        # 계좌번호 전반부
                "ACNT_PRDT_CD": "01",            # 상품코드
                "PDNO": code,                    # 종목코드
                "ORD_DVSN": "00",                # 주문구분 (00: 지정가)
                "ORD_QTY": str(qty),             # 주문수량
                "ORD_UNPR": str(price),          # 주문단가
            }

            # 2. Generate HashKey (Security)
            hash_key = self._get_hash_key(body)
            
            headers = {
                "content-type": "application/json; charset=utf-8",
                "authorization": f"Bearer {self.access_token}",
                "appkey": self.app_key,
                "appsecret": self.secret_key,
                "tr_id": tr_id,
                "custtype": "P"
            }
            
            if hash_key:
                headers["hashkey"] = hash_key
            
            # Official Endpoint for Order: /uapi/domestic-stock/v1/trading/order-cash
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
            
            res = requests.post(url, headers=headers, data=json.dumps(body))
            data = res.json()
            
            if res.status_code == 200:
                 if data['rt_cd'] == '0':
                    logger.info(f"🚀 [REAL-ORDER] {side} {code} Success: {data['msg1']} (OrdNo: {data['output']['ODNO']})")
                    return data
                 else:
                    logger.error(f"❌ [ORDER-FAIL] {data['msg1']}")
                    return None
            else:
                logger.error(f"❌ [ORDER-FAIL] Status {res.status_code}: {res.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ [ORDER-ERROR] {e}")
            return None

    async def fetch_balance(self) -> dict:
        """
        Fetch Account Balance (Interface Implementation)
        Uses KIS /uapi/domestic-stock/v1/trading/inquire-balance (TTTC8434R)
        Wrapper for official inquire_balance logic.
        """
        if self.mock_mode:
             return {"total_cash": 10_000_000, "total_asset": 10_000_000}

        try:
            # [Real API Call] Official Endpoint
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
            
            headers = {
                "content-type": "application/json; charset=utf-8",
                "authorization": f"Bearer {self.access_token}",
                "appkey": self.app_key,
                "appsecret": self.secret_key,
                "tr_id": "TTTC8434R",
                "custtype": "P"
            }
            
            # Official Sample Params (Uppercased)
            params = {
                "CANO": self.account_num,
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
            
            res = requests.get(url, headers=headers, params=params)
            
            if res.status_code == 200:
                data = res.json()
                if data.get('output2'):
                    summary = data['output2'][0]
                    total_asset = float(summary.get('tot_evlu_amt', 0))
                    total_cash = float(summary.get('prvs_rcdl_excc_amt', 0)) # Dn+2 예수금
                    return {"total_cash": total_cash, "total_asset": total_asset}
                else:
                    logger.error(f"❌ [BALANCE-FAIL] No Output2: {data.get('msg1')}")
                    return {"total_cash": 0, "total_asset": 0}
            else:
                 logger.error(f"❌ [BALANCE-FAIL] Status {res.status_code}: {res.text[:100]}")
                 return {"total_cash": 0, "total_asset": 0}
                 
        except Exception as e:
            logger.error(f"❌ [BALANCE-ERROR] {e}")
            return {"total_cash": 0, "total_asset": 0}

    async def fetch_history(self, code: str, days: int = 100) -> list:
        """
        Fetch Historical Candles (Interface Implementation)
        Delegates to the existing logic but adapts parameters.
        """
        # Calculate years roughly from days for legacy function
        years = max(1, days // 250)
        return await self._fetch_missing_history_logic(code, years)

    async def _fetch_missing_history_logic(self, code: str, years: int = 5):
        """
        [Time Machine] Fetch up to 5 years of daily candles for Backtesting.
        Uses KIS 'inquire-daily-itemchartprice' endpoint.
        """
        try:
            import pandas as pd
            import random
        except:
            pass

        if self.mock_mode:
            # Mock 5 years of data
            dates = pd.date_range(end=datetime.now(), periods=years*250, freq='B')
            data = []
            price = 50000
            for d in dates:
                change = random.randint(-1000, 1050)
                price += change
                data.append({
                    "stck_bsop_date": d.strftime("%Y%m%d"),
                    "stck_clpr": str(price),
                    "stck_oprc": str(price - change + random.randint(-100, 100)),
                    "stck_hgpr": str(price + 500),
                    "stck_lwpr": str(price - 500),
                    "acml_vol": str(random.randint(10000, 100000))
                })
            return data

        try:
            # [Real API Call] /u2/u0110/v1/inquire-daily-itemchartprice
            headers = {
                "content-type": "application/json",
                "authorization": f"Bearer {self.access_token}",
                "appkey": self.app_key,
                "appsecret": self.secret_key,
                "tr_id": "FHKST03010100"
            }
            
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now().replace(year=datetime.now().year - years)).strftime("%Y%m%d")
            
            params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": code,
                "fid_input_date_1": start_date,
                "fid_input_date_2": end_date,
                "fid_period_div_code": "D", # Daily
                "fid_org_adj_prc": "1"      # Adjusted Price
            }
            
            res = requests.get(f"{self.base_url}/u2/u0110/v1/inquire-daily-itemchartprice", headers=headers, params=params)
            try:
                data = res.json()
            except json.JSONDecodeError:
                logger.error(f"[API-JSON-FAIL] Status: {res.status_code} | Raw: {res.text[:100]}")
                # [FAIL-SAFE] If we get HTML (Error Page), switch to Mock Mode only if allowed
                if "<html" in res.text.lower():
                    if self.allow_mock_fallback:
                        logger.warning("[SYSTEM] KIS API returned HTML Error. Switching to MOCK MODE for resilience.")
                        self.mock_mode = True
                        return await self._fetch_missing_history_logic(code, years) # Retry with Mock
                    else:
                        logger.error("[SYSTEM] KIS API returned HTML Error. Mock fallback is DISABLED.")
                        return []
                return []
            
            if res.status_code == 200 and data.get('output2'):
                logger.info(f"[HISTORY] Fetched {len(data['output2'])} days for {code}")
                return data['output2']
            else:
                msg = data.get('msg1', 'Unknown Error') if isinstance(data, dict) else res.text[:50]
                logger.error(f"[HISTORY-FAIL] {code}: {msg}")
        except Exception as e:
            logger.error(f"[HISTORY-ERROR] {e}")
            return []

    async def fetch_upper_limit_ranking(self):
        """
        [Real API] Returns list of stocks with highest increase rate (>29%).
        Uses KIS Ranking API (FHPST01700000).
        """
        if self.mock_mode:
            logger.info("🧪 [MOCK] Returning Simulated Upper Limit Stocks")
            return [
                {"mksc_shrn_iscd": "005930", "hts_kor_isnm": "삼성전자(Mock)", "prdy_ctrt": "29.8"},
                {"mksc_shrn_iscd": "000660", "hts_kor_isnm": "SK하이닉스(Mock)", "prdy_ctrt": "29.9"}
            ]

        try:
            # 1. Ensure Token
            if not self.access_token:
                self.get_token()

            headers = {
                "content-type": "application/json; charset=utf-8",
                "authorization": f"Bearer {self.access_token}",
                "appkey": self.app_key,
                "appsecret": self.secret_key,
                "tr_id": "FHPST01700000",
                "custtype": "P"
            }
            
            # Param for "Top Increase Rate"
            # Official endpoint likely uses uppercase params too, trying safe match
            # But let's check basic structure first.
            params = {
                "fid_cond_mrkt_div_code": "J", # J: Total, 1: Kospi, 2: Kosdaq
                "fid_cond_scr_div_code": "20170",
                "fid_input_iscd": "0000",
                "fid_rank_sort_cls_code": "0", # 0: Descending (High->Low)
                "fid_org_adj_prc": "1", # 1: Adjusted Price
                "fid_period_div_code": "D", # D: Daily
                "fid_trgt_cls_code": "0", # 0: All
                "fid_trgt_exls_cls_code": "0", # 0: All
                "fid_vol_cnt": "", 
                "fid_input_price_1": "", 
                "fid_input_price_2": "", 
                "fid_prc_cls_code": "0",
                "fid_fidus_prc_cls_code": "0",
                "fid_item_name": ""
            }
            
            # Update to /uapi endpoint
            url = f"{self.base_url}/uapi/domestic-stock/v1/ranking/fluctuation"
            res = requests.get(url, headers=headers, params=params)
            
            # [DEBUG] Log Raw Response for Diagnosis
            if res.status_code != 200:
                 logger.error(f"❌ [API-FAIL] Status: {res.status_code} | Body: {res.text[:200]}")
            
            data = res.json()
            
            if res.status_code == 200 and data.get('output'):
                results = []
                for item in data['output']:
                    # KIS API returns strings, check fluctuation rate
                    rate = float(item['prdy_ctrt'])
                    if rate >= 29.0: # Filter mainly upper limit candidates
                         results.append(item)
                logger.info(f"🚀 [RANKING] Found {len(results)} Upper Limit Stocks")
                return results
            else:
                logger.error(f"❌ [RANKING-FAIL] {data.get('msg1')}")
                return []
                
        except Exception as e:
            logger.error(f"❌ [RANKING-ERROR] {e}")
            return []

    async def fetch_us_eminent_gainers(self):
        """
        [Global Expansion] Fetch Top 10 US Gainers.
        Currently returns Mock Data as KIS Overseas API is not fully integrated yet.
        """
        logger.info("🇺🇸 [US-MOCK] Fetching Top 10 US Gainers...")
        import random
        
        # Mock Data based on real market trends
        us_stocks = [
            {"symbol": "NVDA", "name": "NVIDIA Corp", "price": 540.0, "change": 4.5},
            {"symbol": "AMD", "name": "Advanced Micro Devices", "price": 145.2, "change": 3.2},
            {"symbol": "TSLA", "name": "Tesla Inc", "price": 240.5, "change": 2.8},
            {"symbol": "MSFT", "name": "Microsoft Corp", "price": 390.1, "change": 1.5},
            {"symbol": "PLTR", "name": "Palantir Tech", "price": 18.5, "change": 5.2},
            {"symbol": "COIN", "name": "Coinbase Global", "price": 150.3, "change": 6.8},
            {"symbol": "AAPL", "name": "Apple Inc", "price": 195.4, "change": 0.8},
            {"symbol": "GOOGL", "name": "Alphabet Inc", "price": 140.2, "change": 1.2},
            {"symbol": "AMZN", "name": "Amazon.com", "price": 155.6, "change": 1.8},
            {"symbol": "META", "name": "Meta Platforms", "price": 360.8, "change": 2.1}
        ]
        
        # Add random volatility for liveness
        results = []
        for s in us_stocks:
            volatility = random.uniform(-0.5, 1.0) # Slight drift
            new_change = round(s['change'] + volatility, 2)
            new_price = round(s['price'] * (1 + new_change/100), 2)
            results.append({
                "rank": 0, # Will be set by index
                "code": s['symbol'],
                "name": s['name'],
                "price": new_price,
                "change_p": f"{new_change:+}%"
            })
            
        # Sort by change %
        results.sort(key=lambda x: float(x['change_p'].strip('%+')), reverse=True)
        
        # Add Rank
        for i, item in enumerate(results):
            item['rank'] = i + 1
            
        return results
