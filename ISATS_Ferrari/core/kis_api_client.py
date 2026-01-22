import aiohttp
import asyncio
import yaml
import json
import os
from datetime import datetime
import hashlib
import hmac
import base64
from typing import Dict, Any, List, Optional

class KISAPIClient:
    """
    한국투자증권 API 완전 통합 클라이언트
    - 실시간 호가/체결
    - 실시간 잔고/평가손익
    - 실시간 거래내역/미체결
    - 실시간 주문 상태
    - 실시간 차트
    - 실시간 뉴스
    - 실시간 투자자별 매매동향
    - 실시간 프로그램 매매
    """
    
    def __init__(self, config_path="config/secrets.yaml", engine_config_path="config/dual_engine.yaml", account_type=None):
        # 1. 시크릿 로드
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            config = {}
        
        # 2. 엔진 설정 로드 (계좌 정보용)
        if not os.path.exists(engine_config_path):
            # Try absolute path based on project root if relative fails
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            engine_config_path = os.path.join(base_dir, "config", "dual_engine.yaml")

        if os.path.exists(engine_config_path):
            with open(engine_config_path, 'r', encoding='utf-8') as f:
                engine_config = yaml.safe_load(f)
        else:
            engine_config = {'accounts': {}}
        
        # 모드 결정 (VIRTUAL/REAL)
        self.mode = config.get('system', {}).get('mode', 'REAL')
        
        # 특정 계좌 타입이 지정된 경우 (Tri-Engine 지원용)
        if account_type:
            target_type = account_type
        else:
            target_type = 'virtual' if self.mode == "VIRTUAL" else 'real'
            
        target_account = engine_config.get('accounts', {}).get(target_type, {})
        
        # API 키 결정: secrets.yaml 우선, 없으면 dual_engine.yaml
        self.app_key = config.get('key', {}).get('kis_app_key') or target_account.get('kis_app_key')
        self.app_secret = config.get('key', {}).get('kis_secret_key') or target_account.get('kis_secret_key')
        
        # 계좌 번호 파싱
        acc_no = target_account.get('account_no', "00000000-01")
        self.account_no = acc_no.split('-')[0]
        self.prdt_cd = acc_no.split('-')[1] if '-' in acc_no else "01"
        self.base_url = target_account.get('base_url', "https://openapi.koreainvestment.com:9443")

        # 모드에 따른 출력 (시각적 구분)
        if target_type == "virtual":
            print(f"🌐 [ISATS] KIS 모의투자 연결 ({self.account_no}-{self.prdt_cd})")
        else:
            print(f"🌐 [ISATS] KIS 실전투자 연결 ({self.account_no}-{self.prdt_cd})")
        
        self.access_token = None
        self.session = None
        self.token_cache_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", f"token_{target_type}.json")
    
    async def initialize(self):
        """API 초기화 및 토큰 발급"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        await self.get_access_token()

    async def _close(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_access_token(self):
        """OAuth 토큰 발급 (캐시 지원)"""
        # 1. 캐시 확인
        if os.path.exists(self.token_cache_path):
            try:
                with open(self.token_cache_path, 'r') as f:
                    cache = json.load(f)
                    # 만료 시간 확인 (보통 24시간이나, 안전하게 23시간으로 체크)
                    cached_time = datetime.fromisoformat(cache['timestamp'])
                    if (datetime.now() - cached_time).total_seconds() < 3600 * 23:
                        self.access_token = cache['access_token']
                        print(f"✅ KIS API 토큰 캐시 사용 중 ({cache['timestamp']})")
                        return True
            except:
                pass

        # 2. 신규 발급
        url = f"{self.base_url}/oauth2/tokenP"
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            async with self.session.post(url, json=payload) as resp:
                data = await resp.json()
                if resp.status == 200:
                    self.access_token = data['access_token']
                    # 캐시 저장
                    with open(self.token_cache_path, 'w') as f:
                        json.dump({
                            'access_token': self.access_token,
                            'timestamp': datetime.now().isoformat()
                        }, f)
                    print(f"✅ KIS API 토큰 신규 발급 완료 및 캐시 저장")
                    return True
                else:
                    print(f"❌ 토큰 발급 실패: {resp.status}")
                    print(f"   메시지: {data}")
                    return False
        except Exception as e:
            print(f"❌ 토큰 발급 서버 통신 오류: {e}")
            return False
    
    def _get_headers(self, tr_id):
        """API 요청 헤더 생성"""
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P" # 개인 고객 기본값
        }
    
    async def get_realtime_price(self, ticker):
        """실시간 현재가 조회"""
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = self._get_headers("FHKST01010100")
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker
        }
        
        async with self.session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                output = data.get('output', {})
                return {
                    'ticker': ticker,
                    'price': float(output.get('stck_prpr', 0)),
                    'change': float(output.get('prdy_ctrt', 0)),
                    'volume': int(output.get('acml_vol', 0)),
                    'high': float(output.get('stck_hgpr', 0)),
                    'low': float(output.get('stck_lwpr', 0))
                }
            return None
    
    async def get_realtime_orderbook(self, ticker):
        """실시간 호가 조회 (10호가)"""
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn"
        headers = self._get_headers("FHKST01010200")
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker
        }
        
        async with self.session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                output = data.get('output1', {})
                
                # 매도호가 (Ask)
                asks = []
                for i in range(1, 11):
                    price = float(output.get(f'askp{i}', 0))
                    qty = int(output.get(f'askp_rsqn{i}', 0))
                    if price > 0:
                        asks.append({'price': price, 'qty': qty})
                
                # 매수호가 (Bid)
                bids = []
                for i in range(1, 11):
                    price = float(output.get(f'bidp{i}', 0))
                    qty = int(output.get(f'bidp_rsqn{i}', 0))
                    if price > 0:
                        bids.append({'price': price, 'qty': qty})
                
                return {
                    'ticker': ticker,
                    'asks': asks,
                    'bids': bids,
                    'timestamp': datetime.now().isoformat()
                }
            return None
    
    async def place_order(self, ticker: str, action: str, price: int, quantity: int, order_type: str = "00"):
        """
        국내주식 주문 집행
        action: 'BUY' or 'SELL'
        order_type: '00' (지정가), '01' (시장가)
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
        
        # 모드에 따른 TR_ID 선택 (신규 TR ID 적용)
        if action == 'BUY':
            tr_id = "VTTC0012U" if self.mode == "VIRTUAL" else "TTTC0012U"
        else:
            tr_id = "VTTC0011U" if self.mode == "VIRTUAL" else "TTTC0011U"
            
        headers = self._get_headers(tr_id)
        
        payload = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.prdt_cd,
            "PDNO": ticker,
            "ORD_DVSN": order_type,
            "ORD_QTY": str(int(quantity)),
            "ORD_UNPR": str(int(price)) if order_type == "00" else "0"
        }
        
        async with self.session.post(url, headers=headers, json=payload) as resp:
            data = await resp.json()
            if resp.status == 200 and data.get('rt_cd') == '0':
                return {
                    "success": True,
                    "order_no": data.get('output', {}).get('ODNO'),
                    "message": "Order Placed Successfully"
                }
            else:
                return {
                    "success": False,
                    "error": data.get('msg1', "Unknown error"),
                    "code": data.get('rt_cd')
                }

    async def place_overseas_order(self, ticker: str, exch_code: str, action: str, price: float, quantity: int, order_type: str = "00"):
        """
        해외주식 주문 집행
        exch_code: 'NAS', 'NYS', 'AMS', 'HKS', 'SHS', 'SZS', 'TSE', 'HSX', 'HNX'
        action: 'BUY' or 'SELL'
        """
        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/order"
        
        # 모드에 따른 TR_ID (해외주식)
        tr_id = "VTTT1002U" if self.mode == "VIRTUAL" else "TTTT1002U"
            
        headers = self._get_headers(tr_id)
        
        payload = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.prdt_cd,
            "OVRS_EXCG_CD": exch_code,
            "PDNO": ticker,
            "ORD_DVSN": order_type,
            "ORD_QTY": str(int(quantity)),
            "ORD_UNPR": f"{price:.2f}",
            "SLL_TYPE": "00" if action == "SELL" else "00" # 기본값
        }
        
        async with self.session.post(url, headers=headers, json=payload) as resp:
            data = await resp.json()
            if resp.status == 200 and data.get('rt_cd') == '0':
                return {
                    "success": True,
                    "order_no": data.get('output', {}).get('ODNO'),
                    "message": "Overseas Order Placed Successfully"
                }
            else:
                return {
                    "success": False,
                    "error": data.get('msg1', "Unknown error"),
                    "code": data.get('rt_cd')
                }

    async def get_balance(self):
        """실시간 국내주식 잔고 조회"""
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        
        # 모드에 따른 TR_ID 선택
        tr_id = "VTTC8434R" if self.mode == "VIRTUAL" else "TTTC8434R"
        headers = self._get_headers(tr_id)
        
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.prdt_cd,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        async with self.session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                output1 = data.get('output1', [])
                output2_raw = data.get('output2', [])
                
                # output2가 리스트로 올 경우 첫 번째 객체 사용
                if isinstance(output2_raw, list) and len(output2_raw) > 0:
                    output2 = output2_raw[0]
                elif isinstance(output2_raw, dict):
                    output2 = output2_raw
                else:
                    output2 = {}
                
                positions = []
                for item in output1:
                    positions.append({
                        'ticker': item.get('pdno'),
                        'name': item.get('prdt_name'),
                        'qty': int(item.get('hldg_qty', 0)),
                        'avg_price': float(item.get('pchs_avg_pric', 0)),
                        'current_price': float(item.get('prpr', 0)),
                        'profit': float(item.get('evlu_pfls_amt', 0)),
                        'profit_pct': float(item.get('evlu_pfls_rt', 0))
                    })
                
                return {
                    'positions': positions,
                    'total_value': float(output2.get('tot_evlu_amt', 0)),
                    'cash': float(output2.get('dnca_tot_amt', 0)),
                    'profit': float(output2.get('evlu_pfls_smtl_amt', 0)),
                    'profit_pct': float(output2.get('tot_evlu_pfls_amt', 0))
                }
            return None

    async def get_overseas_balance(self):
        """실시간 해외주식 잔고 조회"""
        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/inquire-balance"
        
        # 모드에 따른 TR_ID 선택 (해외주식 체결기준잔고)
        tr_id = "VTTS3012R" if self.mode == "VIRTUAL" else "TTTS3012R"
        headers = self._get_headers(tr_id)
        
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.prdt_cd,
            "OVRS_EXCG_CD": "NAS", # 기본값
            "TR_P_CRCY_CD": "USD", # 기본값
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        
        async with self.session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                output1 = data.get('output1', [])
                output2 = data.get('output2', {})
                
                positions = []
                for item in output1:
                    positions.append({
                        'ticker': item.get('pdno'),
                        'name': item.get('prdt_name'),
                        'qty': int(item.get('hldg_qty', 0)),
                        'avg_price': float(item.get('pchs_avg_pric', 0)),
                        'current_price': float(item.get('last_prc', 0)),
                        'profit': float(item.get('evlu_pfls_amt', 0)),
                        'profit_pct': float(item.get('evlu_pfls_rt', 0))
                    })
                
                return {
                    'positions': positions,
                    'total_value': float(output2.get('tot_evlu_pamt', 0)),
                    'cash': float(output2.get('ovrs_dnca_amt', 0)),
                    'profit': float(output2.get('evlu_pfls_smtl_amt', 0)),
                    'profit_pct': float(output2.get('evlu_pfls_rt', 0))
                }
            return None

    async def get_overseas_trade_history(self):
        """실시간 해외주식 거래내역 조회"""
        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/inquire-ccnl"
        
        # 모드에 따른 TR_ID 선택 (해외주식 체결기준내역)
        tr_id = "VTTS3035R" if self.mode == "VIRTUAL" else "TTTS3035R"
        headers = self._get_headers(tr_id)
        
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.prdt_cd,
            "PDNO": "", # 전체
            "ORD_STRT_DT": datetime.now().strftime("%Y%m%d"),
            "ORD_END_DT": datetime.now().strftime("%Y%m%d"),
            "SLL_BUY_DVSN_CD": "00", # 전체
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        
        async with self.session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                output = data.get('output', [])
                trades = []
                for item in output:
                    trades.append({
                        'timestamp': item.get('ord_tmd'),
                        'ticker': item.get('pdno'),
                        'name': item.get('prdt_name'),
                        'action': "매수" if item.get('sll_buy_dvsn_cd') == "02" else "매도",
                        'qty': int(item.get('ft_ord_qty', 0)),
                        'price': float(item.get('ft_ord_unpr', 0)),
                        'engine': 'mock' if self.mode == "VIRTUAL" else 'real'
                    })
                return trades
            return []

    async def get_elw_sensitivity(self, market_div="W", asset_code="000000"):
        """ELW 민감도 순위 조회 (FHPEW02850000)"""
        url = f"{self.base_url}/uapi/elw/v1/ranking/sensitivity"
        headers = self._get_headers("FHPEW02850000")
        params = {
            "FID_COND_MRKT_DIV_CODE": market_div,
            "FID_COND_SCR_DIV_CODE": "20285",
            "FID_UNAS_INPUT_ISCD": asset_code,
            "FID_INPUT_ISCD": "00000",
            "FID_DIV_CLS_CODE": "0",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_INPUT_VOL_1": "",
            "FID_INPUT_VOL_2": "",
            "FID_RANK_SORT_CLS_CODE": "0",
            "FID_INPUT_RMNN_DYNU_1": "",
            "FID_INPUT_DATE_1": datetime.now().strftime("%Y%m%d"),
            "FID_BLNG_CLS_CODE": "0"
        }
        async with self.session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get('output', [])
            return []

    async def get_overseas_industry_prices(self, exch_code="NAS", industry_code="1"):
        """해외주식 업종별 시세 조회 (HHDFS76370000)"""
        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/industry-theme"
        headers = self._get_headers("HHDFS76370000")
        params = {
            "KEYB": "",
            "AUTH": "",
            "EXCD": exch_code,
            "ICOD": industry_code,
            "VOL_RANG": "0"
        }
        async with self.session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get('output2', [])
            return []

    async def get_minute_chart(self, ticker, hour=""):
        """주식 일별 분봉 조회 (FHKST03010230)"""
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice"
        headers = self._get_headers("FHKST03010230")
        if not hour:
            hour = datetime.now().strftime("%H%M%S")
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
            "FID_INPUT_HOUR_1": hour,
            "FID_INPUT_DATE_1": datetime.now().strftime("%Y%m%d"),
            "FID_PW_DATA_INCU_YN": "N",
            "FID_FAKE_TICK_INCU_YN": " "
        }
        async with self.session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    "summary": data.get('output1', {}),
                    "chart": data.get('output2', [])
                }
            return None
    
    async def get_trade_history(self):
        """실시간 거래내역 조회"""
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
        
        # 모드에 따른 TR_ID 선택
        tr_id = "VTTC8001R" if self.mode == "VIRTUAL" else "TTTC8001R"
        headers = self._get_headers(tr_id)
        
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.prdt_cd,
            "INQR_STRT_DT": datetime.now().strftime("%Y%m%d"),
            "INQR_END_DT": datetime.now().strftime("%Y%m%d"),
            "SLL_BUY_DVSN_CD": "00",
            "INQR_DVSN": "00",
            "PDNO": "",
            "CCLD_DVSN": "00",
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "INQR_DVSN_3": "00",
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        async with self.session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                output1 = data.get('output1', [])
                
                trades = []
                for item in output1:
                    trades.append({
                        'ticker': item.get('pdno'),
                        'name': item.get('prdt_name'),
                        'action': '매수' if item.get('sll_buy_dvsn_cd') == '02' else '매도',
                        'qty': int(item.get('cncl_cfrm_qty', 0)),
                        'price': float(item.get('avg_prvs', 0)),
                        'time': item.get('ord_tmd'),
                        'status': item.get('ord_dvsn_name')
                    })
                
                return trades
            return []
    
    async def get_pending_orders(self):
        """실시간 미체결 조회"""
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl"
        
        # 모드에 따른 TR_ID 선택
        tr_id = "VTTC8036R" if self.mode == "VIRTUAL" else "TTTC8036R"
        headers = self._get_headers(tr_id)
        
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.prdt_cd,
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
            "INQR_DVSN_1": "0",
            "INQR_DVSN_2": "0"
        }
        
        async with self.session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                output = data.get('output', [])
                
                pending = []
                for item in output:
                    pending.append({
                        'order_no': item.get('odno'),
                        'ticker': item.get('pdno'),
                        'name': item.get('prdt_name'),
                        'action': '매수' if item.get('sll_buy_dvsn_cd') == '02' else '매도',
                        'qty': int(item.get('ord_qty', 0)),
                        'filled_qty': int(item.get('tot_ccld_qty', 0)),
                        'price': float(item.get('ord_unpr', 0)),
                        'time': item.get('ord_tmd')
                    })
                
                return pending
            return []
    
    async def get_investor_trends(self, ticker):
        """실시간 투자자별 매매동향"""
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-investor"
        headers = self._get_headers("FHKST01010900")
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker
        }
        
        async with self.session.get(url, headers=headers, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                output = data.get('output', {})
                
                return {
                    'ticker': ticker,
                    'foreign': {
                        'buy': int(output.get('frgn_ntby_qty', 0)),
                        'ratio': float(output.get('frgn_ntby_tr_pbmn', 0))
                    },
                    'institution': {
                        'buy': int(output.get('orgn_ntby_qty', 0)),
                        'ratio': float(output.get('orgn_ntby_tr_pbmn', 0))
                    },
                    'individual': {
                        'buy': int(output.get('prsn_ntby_qty', 0)),
                        'ratio': float(output.get('prsn_ntby_tr_pbmn', 0))
                    }
                }
            return None
    
    async def close(self):
        """세션 종료"""
        if self.session:
            await self.session.close()


# 실시간 데이터 스트리밍 매니저
class RealtimeDataManager:
    """
    모든 KIS API 데이터를 실시간으로 수집하고 대시보드에 제공.
    S-Class 특화 기능: Adaptive Polling Interval (Rate Limit Backoff)
    """
    
    def __init__(self) -> None:
        self.client: Optional[KISAPIClient] = None
        self.running: bool = False
        self.intervals: Dict[str, float] = {
            'prices': 1.0,
            'orderbooks': 0.5,
            'balance': 2.0,
            'trades': 3.0,
            'pending': 2.0
        }
        self.data_cache: Dict[str, Any] = {
            'prices': {},
            'orderbooks': {},
            'balance': {},
            'trades': [],
            'pending': [],
            'investor_trends': {},
            'environmental_flags': {"rate_limit_active": False}
        }
    
    async def start(self) -> None:
        """실시간 데이터 수집 시작"""
        self.client = KISAPIClient()
        await self.client.initialize()
        self.running = True
        
        # 병렬 데이터 수집
        await asyncio.gather(
            self.update_prices(),
            self.update_orderbooks(),
            self.update_balance(),
            self.update_trades(),
            self.update_pending_orders()
        )
    
    async def _adaptive_sleep(self, category: str, error_occurred: bool = False) -> None:
        """Rate Limit 감지 시 대기 시간을 동적으로 조절합니다."""
        base_interval = self.intervals.get(category, 1.0)
        
        if error_occurred:
            # 429 발생 시 즉시 interval 2배 증가 (Max 5.0s)
            self.data_cache['environmental_flags']['rate_limit_active'] = True
            sleep_time = min(base_interval * 2, 5.0)
            print(f"⚠️ [RATE LIMIT] {category} backoff: {base_interval}s -> {sleep_time}s")
        else:
            # 정상 작동 시 점진적으로 원래 interval 복구
            self.data_cache['environmental_flags']['rate_limit_active'] = False
            sleep_time = base_interval
            
        await asyncio.sleep(sleep_time)

    async def update_prices(self) -> None:
        """실시간 가격 업데이트"""
        tickers = ['005930', '000660', '035720']
        while self.running:
            error = False
            try:
                for ticker in tickers:
                    price_data = await self.client.get_realtime_price(ticker)
                    if price_data:
                        self.data_cache['prices'][ticker] = price_data
            except Exception as e:
                if "429" in str(e): error = True
            
            await self._adaptive_sleep('prices', error)
    
    async def update_orderbooks(self) -> None:
        """실시간 호가 업데이트"""
        tickers = ['005930']
        while self.running:
            error = False
            try:
                for ticker in tickers:
                    orderbook = await self.client.get_realtime_orderbook(ticker)
                    if orderbook:
                        self.data_cache['orderbooks'][ticker] = orderbook
            except Exception as e:
                if "429" in str(e): error = True
                
            await self._adaptive_sleep('orderbooks', error)
    
    async def update_balance(self) -> None:
        """실시간 잔고 업데이트"""
        while self.running:
            error = False
            try:
                balance = await self.client.get_balance()
                if balance:
                    self.data_cache['balance'] = balance
            except Exception as e:
                if "429" in str(e): error = True
                
            await self._adaptive_sleep('balance', error)
    
    async def update_trades(self) -> None:
        """실시간 거래내역 업데이트"""
        while self.running:
            error = False
            try:
                trades = await self.client.get_trade_history()
                if trades:
                    self.data_cache['trades'] = trades
            except Exception as e:
                if "429" in str(e): error = True
                
            await self._adaptive_sleep('trades', error)
    
    async def update_pending_orders(self) -> None:
        """실시간 미체결 업데이트"""
        while self.running:
            error = False
            try:
                pending = await self.client.get_pending_orders()
                if pending:
                    self.data_cache['pending'] = pending
            except Exception as e:
                if "429" in str(e): error = True
                
            await self._adaptive_sleep('pending', error)
    
    def get_all_data(self) -> Dict[str, Any]:
        """모든 실시간 데이터 반환"""
        return self.data_cache
    
    async def stop(self) -> None:
        """데이터 수집 중지"""
        self.running = False
        if self.client:
            await self.client.close()
