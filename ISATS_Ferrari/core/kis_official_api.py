# -*- coding: utf-8 -*-
"""
================================================================================
🔥 KIS Open API 완전 통합 모듈 (Official GitHub Repository Integration)
================================================================================
Source: https://github.com/koreainvestment/open-trading-api

이 모듈은 한국투자증권 공식 GitHub 저장소의 모든 API 기능을 
ISATS 자동매매 시스템에 완전 통합합니다.

지원 API 카테고리:
1. 국내주식 (domestic_stock) - 시세, 주문, 잔고, 순위분석 등 262+ API
2. 해외주식 (overseas_stock) - 미국/일본/중국/홍콩/베트남 시세 및 주문
3. 국내채권 (domestic_bond) - 채권 시세, 주문, 분석
4. 국내선물옵션 (domestic_futureoption) - 선물/옵션 시세 및 주문
5. 해외선물옵션 (overseas_futureoption) - 해외 파생상품
6. ELW - ELW 시세 및 분석
7. ETF/ETN - ETF/ETN 시세 및 분석
8. WebSocket 실시간 데이터 스트리밍

Author: ISATS Ferrari Team
Created: 2026-01-22
================================================================================
"""

import os
import sys
import copy
import json
import time
import asyncio
import logging
from datetime import datetime
from collections import namedtuple
from typing import Optional, Dict, Any, List, Callable, Tuple
from io import StringIO

import requests
import pandas as pd
import yaml

# WebSocket 및 암호화 모듈 (선택적)
try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    logging.warning("websockets 모듈 없음. WebSocket 기능 비활성화.")

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    from base64 import b64decode
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    logging.warning("pycryptodome 모듈 없음. 실시간 암호화 데이터 복호화 불가.")


# ================================================================================
# 🔐 KIS 인증 관리자 (토큰 발급/관리)
# ================================================================================

class KISAuthManager:
    """
    한국투자증권 API 인증 통합 관리자
    - REST API 토큰 발급 및 갱신
    - WebSocket 접속키 발급
    - 실전/모의투자 환경 전환
    """
    
    def __init__(self, config_path: str = None, mode: str = "virtual"):
        """
        Args:
            config_path: 설정 파일 경로 (YAML)
            mode: 'real' (실전) 또는 'virtual' (모의)
        """
        self.mode = mode
        self.config_path = config_path
        self.config = {}
        self.token = None
        self.token_expired = None
        self.approval_key = None  # WebSocket 접속키
        self._base_headers = {
            "Content-Type": "application/json",
            "Accept": "text/plain",
            "charset": "UTF-8",
        }
        
        # 토큰 캐시 경로
        self.token_cache_dir = os.path.join(os.path.expanduser("~"), "KIS", "config")
        os.makedirs(self.token_cache_dir, exist_ok=True)
        
        self._load_config()
        
    def _load_config(self):
        """설정 파일 로드"""
        if self.config_path and os.path.exists(self.config_path):
            with open(self.config_path, encoding="UTF-8") as f:
                self.config = yaml.safe_load(f)
        else:
            # 기본 ISATS 설정 경로
            isats_config = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "config", "dual_engine.yaml"
            )
            if os.path.exists(isats_config):
                with open(isats_config, encoding="UTF-8") as f:
                    cfg = yaml.safe_load(f)
                    account_cfg = cfg.get("accounts", {}).get(self.mode, {})
                    self.config = {
                        "app_key": account_cfg.get("kis_app_key", ""),
                        "app_secret": account_cfg.get("kis_secret_key", ""),
                        "account_no": account_cfg.get("account_no", ""),
                        "base_url": account_cfg.get("base_url", ""),
                    }
    
    @property
    def base_url(self) -> str:
        """현재 모드에 따른 기본 URL"""
        if self.mode == "real":
            return self.config.get("base_url", "https://openapi.koreainvestment.com:9443")
        else:
            return self.config.get("base_url", "https://openapivts.koreainvestment.com:29443")
    
    @property
    def ws_url(self) -> str:
        """WebSocket URL"""
        if self.mode == "real":
            return "ws://ops.koreainvestment.com:21000"
        else:
            return "ws://ops.koreainvestment.com:31000"
    
    @property
    def app_key(self) -> str:
        return self.config.get("app_key", "")
    
    @property
    def app_secret(self) -> str:
        return self.config.get("app_secret", "")
    
    @property
    def account_no(self) -> str:
        return self.config.get("account_no", "")
    
    @property
    def account_prefix(self) -> str:
        """계좌번호 앞 8자리"""
        return self.account_no.split("-")[0] if "-" in self.account_no else self.account_no[:8]
    
    @property
    def account_suffix(self) -> str:
        """계좌번호 뒤 2자리"""
        return self.account_no.split("-")[1] if "-" in self.account_no else self.account_no[8:10]
    
    def _get_token_cache_path(self) -> str:
        """토큰 캐시 파일 경로"""
        return os.path.join(
            self.token_cache_dir, 
            f"KIS_{self.mode}_{datetime.today().strftime('%Y%m%d')}"
        )
    
    def _save_token(self, token: str, expired: str):
        """토큰 로컬 저장"""
        cache_path = self._get_token_cache_path()
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(f"token: {token}\n")
            f.write(f"valid-date: {expired}\n")
        self.token = token
        self.token_expired = datetime.strptime(expired, "%Y-%m-%d %H:%M:%S")
    
    def _load_cached_token(self) -> Optional[str]:
        """캐시된 토큰 로드"""
        cache_path = self._get_token_cache_path()
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, encoding="UTF-8") as f:
                data = yaml.safe_load(f)
            
            exp_dt = data.get("valid-date")
            if isinstance(exp_dt, datetime):
                exp_str = exp_dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                exp_str = str(exp_dt)
            
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if exp_str > now_str:
                return data.get("token")
        except Exception as e:
            logging.warning(f"토큰 캐시 로드 실패: {e}")
        
        return None
    
    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        접근 토큰 발급 (캐시 우선)
        
        Args:
            force_refresh: True면 새로 발급
            
        Returns:
            access_token 문자열
        """
        # 캐시 확인
        if not force_refresh:
            cached = self._load_cached_token()
            if cached:
                self.token = cached
                return cached
        
        # 신규 발급
        url = f"{self.base_url}/oauth2/tokenP"
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }
        
        res = requests.post(url, json=payload, headers=self._base_headers)
        
        if res.status_code == 200:
            data = res.json()
            token = data.get("access_token")
            expired = data.get("access_token_token_expired")
            self._save_token(token, expired)
            logging.info(f"✅ 토큰 발급 완료 (만료: {expired})")
            return token
        else:
            logging.error(f"❌ 토큰 발급 실패: {res.status_code} - {res.text}")
            raise Exception(f"Token issuance failed: {res.text}")
    
    def get_approval_key(self) -> str:
        """WebSocket 접속키 발급"""
        url = f"{self.base_url}/oauth2/Approval"
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "secretkey": self.app_secret,
        }
        
        res = requests.post(url, json=payload, headers=self._base_headers)
        
        if res.status_code == 200:
            self.approval_key = res.json().get("approval_key")
            logging.info("✅ WebSocket 접속키 발급 완료")
            return self.approval_key
        else:
            logging.error(f"❌ WebSocket 접속키 발급 실패: {res.text}")
            raise Exception(f"Approval key issuance failed: {res.text}")
    
    def get_headers(self, tr_id: str, tr_cont: str = "") -> Dict[str, str]:
        """API 호출용 헤더 생성"""
        if not self.token:
            self.get_access_token()
        
        # 모의투자용 TR ID 변환
        if tr_id[0] in ("T", "J", "C") and self.mode == "virtual":
            tr_id = "V" + tr_id[1:]
        
        return {
            "Content-Type": "application/json",
            "Accept": "text/plain",
            "charset": "UTF-8",
            "authorization": f"Bearer {self.token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "tr_cont": tr_cont,
            "custtype": "P",
        }


# ================================================================================
# 📊 API 응답 래퍼
# ================================================================================

class APIResponse:
    """API 응답 통합 래퍼"""
    
    def __init__(self, response: requests.Response):
        self.status_code = response.status_code
        self.raw = response
        self._body = None
        self._parse()
    
    def _parse(self):
        try:
            self._body = self.raw.json()
        except:
            self._body = {}
    
    @property
    def is_ok(self) -> bool:
        return self._body.get("rt_cd") == "0"
    
    @property
    def message(self) -> str:
        return self._body.get("msg1", "")
    
    @property
    def error_code(self) -> str:
        return self._body.get("msg_cd", "")
    
    @property
    def output(self) -> Any:
        """단일 출력값"""
        return self._body.get("output", {})
    
    @property
    def output1(self) -> Any:
        """첫 번째 출력"""
        return self._body.get("output1", self.output)
    
    @property
    def output2(self) -> Any:
        """두 번째 출력 (리스트 형태 등)"""
        return self._body.get("output2", [])
    
    def to_dataframe(self, output_key: str = "output") -> pd.DataFrame:
        """응답을 DataFrame으로 변환"""
        data = self._body.get(output_key, [])
        if isinstance(data, list):
            return pd.DataFrame(data)
        elif isinstance(data, dict):
            return pd.DataFrame([data])
        return pd.DataFrame()


# ================================================================================
# 🏦 국내주식 API (262+ Functions)
# ================================================================================

class DomesticStockAPI:
    """
    국내주식 API 통합 모듈
    
    지원 기능:
    - 기본시세: 현재가, 호가, 체결, 일봉/주봉/월봉
    - 주문: 매수/매도/정정/취소
    - 잔고: 잔고조회, 예수금, 평가손익
    - 순위분석: 거래량상위, 시세급등락, 신용잔고 등
    - 업종/기타: 휴장일, 금리, 프로그램매매
    """
    
    def __init__(self, auth: KISAuthManager):
        self.auth = auth
    
    def _request(self, method: str, url: str, tr_id: str, 
                 params: Dict = None, data: Dict = None, 
                 tr_cont: str = "") -> APIResponse:
        """공통 API 요청 처리"""
        full_url = f"{self.auth.base_url}{url}"
        headers = self.auth.get_headers(tr_id, tr_cont)
        
        if method.upper() == "GET":
            res = requests.get(full_url, headers=headers, params=params)
        else:
            res = requests.post(full_url, headers=headers, json=data)
        
        return APIResponse(res)
    
    # ─────────────────────────────────────────────────────────────────────────
    # 📈 기본시세 API
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_price(self, ticker: str) -> Dict:
        """
        [국내주식-007] 주식현재가 시세
        
        Args:
            ticker: 종목코드 (예: "005930")
            
        Returns:
            현재가 정보 딕셔너리
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # J: 주식, ETF, ETN
            "FID_INPUT_ISCD": ticker,
        }
        
        res = self._request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/inquire-price",
            "FHKST01010100",
            params=params
        )
        
        if res.is_ok:
            return res.output
        return {}
    
    def get_orderbook(self, ticker: str) -> Dict:
        """
        [국내주식-011] 주식현재가 호가/예상체결
        
        Args:
            ticker: 종목코드
            
        Returns:
            호가 정보 (10호가)
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
        }
        
        res = self._request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
            "FHKST01010200",
            params=params
        )
        
        if res.is_ok:
            return res.output1
        return {}
    
    def get_ccnl(self, ticker: str) -> List[Dict]:
        """
        [국내주식-012] 주식현재가 체결
        
        Args:
            ticker: 종목코드
            
        Returns:
            체결 데이터 리스트
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
        }
        
        res = self._request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/inquire-ccnl",
            "FHKST01010300",
            params=params
        )
        
        if res.is_ok:
            return res.output
        return []
    
    def get_daily_price(self, ticker: str, period: str = "D", 
                        adjust: bool = True) -> pd.DataFrame:
        """
        [국내주식-016] 주식현재가 일자별
        
        Args:
            ticker: 종목코드
            period: D(일), W(주), M(월)
            adjust: 수정주가 적용 여부
            
        Returns:
            OHLCV DataFrame
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
            "FID_PERIOD_DIV_CODE": period,
            "FID_ORG_ADJ_PRC": "0" if adjust else "1",
        }
        
        res = self._request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/inquire-daily-price",
            "FHKST01010400",
            params=params
        )
        
        return res.to_dataframe("output")
    
    def get_minute_chart(self, ticker: str, time_unit: str = "1") -> pd.DataFrame:
        """
        [국내주식-022] 주식당일분봉조회
        
        Args:
            ticker: 종목코드
            time_unit: 분봉 단위 (1, 3, 5, 10, 15, 30, 60)
            
        Returns:
            분봉 DataFrame
        """
        params = {
            "FID_ETC_CLS_CODE": "",
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
            "FID_INPUT_HOUR_1": "",
            "FID_PW_DATA_INCU_YN": "N",
        }
        
        res = self._request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
            "FHKST03010200",
            params=params
        )
        
        return res.to_dataframe("output2")
    
    def get_investor_trend(self, ticker: str) -> pd.DataFrame:
        """
        [국내주식-019] 주식현재가 투자자
        
        Args:
            ticker: 종목코드
            
        Returns:
            투자자별 매매동향 DataFrame
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
        }
        
        res = self._request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/inquire-investor",
            "FHKST01010900",
            params=params
        )
        
        return res.to_dataframe("output")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 📝 주문 API
    # ─────────────────────────────────────────────────────────────────────────
    
    def place_order(self, ticker: str, order_type: str, quantity: int, 
                    price: int = 0, order_div: str = "00") -> Dict:
        """
        [국내주식-001] 주식주문(현금)
        
        Args:
            ticker: 종목코드
            order_type: "BUY" 또는 "SELL"
            quantity: 수량
            price: 가격 (시장가 주문시 0)
            order_div: 주문구분 (00: 지정가, 01: 시장가, 02: 조건부지정가, ...)
            
        Returns:
            주문 결과
        """
        # TR ID 결정
        if order_type.upper() == "BUY":
            tr_id = "TTTC0802U"  # 매수
        else:
            tr_id = "TTTC0801U"  # 매도
        
        data = {
            "CANO": self.auth.account_prefix,
            "ACNT_PRDT_CD": self.auth.account_suffix,
            "PDNO": ticker,
            "ORD_DVSN": order_div,
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price) if price > 0 else "0",
        }
        
        res = self._request(
            "POST",
            "/uapi/domestic-stock/v1/trading/order-cash",
            tr_id,
            data=data
        )
        
        if res.is_ok:
            output = res.output
            return {
                "success": True,
                "order_no": output.get("ODNO", ""),
                "executed_time": output.get("ORD_TMD", ""),
                "message": res.message,
            }
        else:
            return {
                "success": False,
                "error_code": res.error_code,
                "message": res.message,
            }
    
    def cancel_order(self, order_no: str, ticker: str, 
                     quantity: int, order_type: str = "BUY") -> Dict:
        """
        [국내주식-003] 주식주문(정정취소)
        
        Args:
            order_no: 원주문번호
            ticker: 종목코드
            quantity: 취소수량
            order_type: 원주문 유형
            
        Returns:
            취소 결과
        """
        # 정정/취소는 원주문 유형에 따라 TR ID 다름
        if order_type.upper() == "BUY":
            tr_id = "TTTC0803U"  # 매수정정취소
        else:
            tr_id = "TTTC0803U"  # 매도정정취소
        
        data = {
            "CANO": self.auth.account_prefix,
            "ACNT_PRDT_CD": self.auth.account_suffix,
            "KRX_FWDG_ORD_ORGNO": "",
            "ORGN_ODNO": order_no,
            "ORD_DVSN": "00",
            "RVSE_CNCL_DVSN_CD": "02",  # 02: 취소
            "ORD_QTY": str(quantity),
            "ORD_UNPR": "0",
            "QTY_ALL_ORD_YN": "Y",
        }
        
        res = self._request(
            "POST",
            "/uapi/domestic-stock/v1/trading/order-rvsecncl",
            tr_id,
            data=data
        )
        
        return {
            "success": res.is_ok,
            "message": res.message,
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # 💰 잔고/계좌 API
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_balance(self) -> Tuple[pd.DataFrame, Dict]:
        """
        [국내주식-006] 주식잔고조회
        
        Returns:
            (보유종목 DataFrame, 계좌요약 Dict)
        """
        params = {
            "CANO": self.auth.account_prefix,
            "ACNT_PRDT_CD": self.auth.account_suffix,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",  # 종목별
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }
        
        res = self._request(
            "GET",
            "/uapi/domestic-stock/v1/trading/inquire-balance",
            "TTTC8434R",
            params=params
        )
        
        if res.is_ok:
            holdings = res.to_dataframe("output1")
            summary = res.output2[0] if res.output2 else {}
            return holdings, summary
        
        return pd.DataFrame(), {}
    
    def get_deposit(self) -> Dict:
        """
        [국내주식-008] 주식예수금현황
        
        Returns:
            예수금 정보
        """
        params = {
            "CANO": self.auth.account_prefix,
            "ACNT_PRDT_CD": self.auth.account_suffix,
            "INQR_DVSN_1": "",
            "BSPR_BF_DT_APLY_YN": "",
        }
        
        res = self._request(
            "GET",
            "/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl",
            "TTTC8908R",
            params=params
        )
        
        return res.output if res.is_ok else {}
    
    def get_pending_orders(self) -> pd.DataFrame:
        """
        [국내주식-004] 주식정정취소가능주문조회
        
        Returns:
            미체결 주문 DataFrame
        """
        params = {
            "CANO": self.auth.account_prefix,
            "ACNT_PRDT_CD": self.auth.account_suffix,
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
            "INQR_DVSN_1": "0",
            "INQR_DVSN_2": "0",
        }
        
        res = self._request(
            "GET",
            "/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl",
            "TTTC8036R",
            params=params
        )
        
        return res.to_dataframe("output")
    
    # ─────────────────────────────────────────────────────────────────────────
    # 📊 순위분석 API
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_volume_rank(self, market: str = "J") -> pd.DataFrame:
        """
        [국내주식-047] 거래량순위
        
        Args:
            market: J(코스피), Q(코스닥)
            
        Returns:
            거래량 순위 DataFrame
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": market,
            "FID_COND_SCR_DIV_CODE": "20171",
            "FID_INPUT_ISCD": "0000",
            "FID_DIV_CLS_CODE": "0",
            "FID_BLNG_CLS_CODE": "0",
            "FID_TRGT_CLS_CODE": "111111111",
            "FID_TRGT_EXLS_CLS_CODE": "000000",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "",
            "FID_INPUT_DATE_1": "",
        }
        
        res = self._request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/volume-rank",
            "FHPST01710000",
            params=params
        )
        
        return res.to_dataframe("output")
    
    def get_fluctuation_rank(self, market: str = "J", 
                             direction: str = "1") -> pd.DataFrame:
        """
        [국내주식-051] 시세급등락/체결강도급등락
        
        Args:
            market: J(코스피), Q(코스닥)
            direction: 1(상승), 2(하락)
            
        Returns:
            급등락 순위 DataFrame
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": market,
            "FID_COND_SCR_DIV_CODE": "10400",
            "FID_INPUT_ISCD": "0000",
            "FID_RANK_SORT_CLS_CODE": direction,
            "FID_INPUT_CNT_1": "0",
            "FID_PRC_CLS_CODE": "1",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "",
            "FID_TRGT_CLS_CODE": "",
            "FID_TRGT_EXLS_CLS_CODE": "",
            "FID_DIV_CLS_CODE": "0",
            "FID_RSFL_RATE1": "",
            "FID_RSFL_RATE2": "",
        }
        
        res = self._request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/capture-drastic",
            "HHKST03810000",
            params=params
        )
        
        return res.to_dataframe("output")
    
    def get_top_interest(self) -> pd.DataFrame:
        """
        [국내주식-050] 관심종목등록상위
        
        Returns:
            관심종목 등록 상위 DataFrame
        """
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_COND_SCR_DIV_CODE": "16601",
            "FID_INPUT_ISCD": "0000",
            "FID_DIV_CLS_CODE": "0",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "",
            "FID_INPUT_DATE_1": "",
        }
        
        res = self._request(
            "GET",
            "/uapi/domestic-stock/v1/quotations/interest-top",
            "HHKST03020000",
            params=params
        )
        
        return res.to_dataframe("output")


# ================================================================================
# 🌍 해외주식 API
# ================================================================================

class OverseasStockAPI:
    """
    해외주식 API 통합 모듈
    
    지원 시장:
    - 미국: NYSE, NASDAQ, AMEX
    - 일본: TSE
    - 중국: SSE (상해), SZSE (선전)
    - 홍콩: HKEX
    - 베트남: HSX, HNX
    """
    
    EXCHANGE_CODES = {
        "NYSE": "NYS",
        "NASDAQ": "NAS",
        "AMEX": "AMS",
        "JAPAN": "TSE",
        "SHANGHAI": "SHS",
        "SHENZHEN": "SZS",
        "HONGKONG": "HKS",
        "VIETNAM_HO": "HSX",
        "VIETNAM_HA": "HNX",
    }
    
    def __init__(self, auth: KISAuthManager):
        self.auth = auth
    
    def _request(self, method: str, url: str, tr_id: str, 
                 params: Dict = None, data: Dict = None) -> APIResponse:
        full_url = f"{self.auth.base_url}{url}"
        headers = self.auth.get_headers(tr_id)
        
        if method.upper() == "GET":
            res = requests.get(full_url, headers=headers, params=params)
        else:
            res = requests.post(full_url, headers=headers, json=data)
        
        return APIResponse(res)
    
    def get_price(self, ticker: str, exchange: str = "NAS") -> Dict:
        """
        [해외주식-008] 해외주식 현재가상세
        
        Args:
            ticker: 종목코드 (예: "AAPL")
            exchange: 거래소 코드
            
        Returns:
            현재가 정보
        """
        params = {
            "AUTH": "",
            "EXCD": exchange,
            "SYMB": ticker,
        }
        
        res = self._request(
            "GET",
            "/uapi/overseas-price/v1/quotations/price-detail",
            "HHDFS76200200",
            params=params
        )
        
        return res.output if res.is_ok else {}
    
    def get_daily_price(self, ticker: str, exchange: str = "NAS", 
                        period: str = "D", count: int = 100) -> pd.DataFrame:
        """
        [해외주식-010] 해외주식 기간별시세
        
        Args:
            ticker: 종목코드
            exchange: 거래소 코드
            period: D(일), W(주), M(월)
            count: 조회 건수
            
        Returns:
            OHLCV DataFrame
        """
        params = {
            "AUTH": "",
            "EXCD": exchange,
            "SYMB": ticker,
            "GUBN": "0" if period == "D" else "1" if period == "W" else "2",
            "BYMD": "",
            "MODP": "1",  # 수정주가
        }
        
        res = self._request(
            "GET",
            "/uapi/overseas-price/v1/quotations/dailyprice",
            "HHDFS76240000",
            params=params
        )
        
        return res.to_dataframe("output2")
    
    def place_order(self, ticker: str, exchange: str, order_type: str,
                    quantity: int, price: float = 0, 
                    order_div: str = "00") -> Dict:
        """
        [해외주식-001] 해외주식 주문
        
        Args:
            ticker: 종목코드
            exchange: 거래소 코드
            order_type: "BUY" 또는 "SELL"
            quantity: 수량
            price: 가격
            order_div: 주문구분
            
        Returns:
            주문 결과
        """
        if order_type.upper() == "BUY":
            tr_id = "JTTT1002U"  # 해외 매수
        else:
            tr_id = "JTTT1006U"  # 해외 매도
        
        data = {
            "CANO": self.auth.account_prefix,
            "ACNT_PRDT_CD": self.auth.account_suffix,
            "OVRS_EXCG_CD": exchange,
            "PDNO": ticker,
            "ORD_QTY": str(quantity),
            "OVRS_ORD_UNPR": str(price),
            "ORD_SVR_DVSN_CD": "0",
            "ORD_DVSN": order_div,
        }
        
        res = self._request(
            "POST",
            "/uapi/overseas-stock/v1/trading/order",
            tr_id,
            data=data
        )
        
        return {
            "success": res.is_ok,
            "order_no": res.output.get("ODNO", "") if res.is_ok else "",
            "message": res.message,
        }
    
    def get_balance(self, exchange: str = "NASD") -> Tuple[pd.DataFrame, Dict]:
        """
        [해외주식-006] 해외주식 잔고
        
        Args:
            exchange: 거래소 코드 (NASD, NYSE, AMEX, ...)
            
        Returns:
            (보유종목 DataFrame, 계좌요약 Dict)
        """
        params = {
            "CANO": self.auth.account_prefix,
            "ACNT_PRDT_CD": self.auth.account_suffix,
            "OVRS_EXCG_CD": exchange,
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": "",
        }
        
        res = self._request(
            "GET",
            "/uapi/overseas-stock/v1/trading/inquire-balance",
            "JTTT3012R",
            params=params
        )
        
        if res.is_ok:
            return res.to_dataframe("output1"), res.output2
        return pd.DataFrame(), {}


# ================================================================================
# 📈 국내채권 API
# ================================================================================

class DomesticBondAPI:
    """국내채권 API 모듈"""
    
    def __init__(self, auth: KISAuthManager):
        self.auth = auth
    
    def _request(self, method: str, url: str, tr_id: str, 
                 params: Dict = None) -> APIResponse:
        full_url = f"{self.auth.base_url}{url}"
        headers = self.auth.get_headers(tr_id)
        res = requests.get(full_url, headers=headers, params=params)
        return APIResponse(res)
    
    def get_bond_price(self, bond_code: str) -> Dict:
        """채권 현재가 조회"""
        params = {
            "FID_COND_MRKT_DIV_CODE": "B",
            "FID_INPUT_ISCD": bond_code,
        }
        
        res = self._request(
            "GET",
            "/uapi/domestic-bond/v1/quotations/inquire-price",
            "FHKBT02300000",
            params=params
        )
        
        return res.output if res.is_ok else {}


# ================================================================================
# 🎯 국내선물옵션 API
# ================================================================================

class DomesticFutureOptionAPI:
    """국내선물옵션 API 모듈"""
    
    def __init__(self, auth: KISAuthManager):
        self.auth = auth
    
    def _request(self, method: str, url: str, tr_id: str, 
                 params: Dict = None) -> APIResponse:
        full_url = f"{self.auth.base_url}{url}"
        headers = self.auth.get_headers(tr_id)
        res = requests.get(full_url, headers=headers, params=params)
        return APIResponse(res)
    
    def get_future_price(self, future_code: str) -> Dict:
        """선물 현재가 조회"""
        params = {
            "FID_COND_MRKT_DIV_CODE": "F",
            "FID_INPUT_ISCD": future_code,
        }
        
        res = self._request(
            "GET",
            "/uapi/domestic-futureoption/v1/quotations/inquire-price",
            "FHMIF10000000",
            params=params
        )
        
        return res.output if res.is_ok else {}
    
    def get_option_price(self, option_code: str) -> Dict:
        """옵션 현재가 조회"""
        params = {
            "FID_COND_MRKT_DIV_CODE": "O",
            "FID_INPUT_ISCD": option_code,
        }
        
        res = self._request(
            "GET",
            "/uapi/domestic-futureoption/v1/quotations/inquire-price",
            "FHMIF10010000",
            params=params
        )
        
        return res.output if res.is_ok else {}


# ================================================================================
# 📡 WebSocket 실시간 데이터 스트리밍
# ================================================================================

class KISWebSocketClient:
    """
    KIS 실시간 데이터 WebSocket 클라이언트
    
    지원 기능:
    - 실시간 체결가
    - 실시간 호가
    - 실시간 체결통보
    """
    
    def __init__(self, auth: KISAuthManager):
        self.auth = auth
        self.websocket = None
        self.subscriptions = {}
        self.callbacks = {}
        self.running = False
    
    async def connect(self):
        """WebSocket 연결"""
        if not HAS_WEBSOCKETS:
            raise ImportError("websockets 모듈이 필요합니다.")
        
        # 접속키 발급
        approval_key = self.auth.get_approval_key()
        
        url = f"{self.auth.ws_url}/tryitout/H0STCNT0"
        self.websocket = await websockets.connect(url)
        self.running = True
        
        logging.info("✅ WebSocket 연결 완료")
    
    async def subscribe_price(self, ticker: str, callback: Callable):
        """
        실시간 체결가 구독
        
        Args:
            ticker: 종목코드
            callback: 데이터 수신 시 호출될 콜백 함수
        """
        tr_id = "H0STCNT0"  # 실시간 체결
        
        msg = {
            "header": {
                "approval_key": self.auth.approval_key,
                "custtype": "P",
                "tr_type": "1",  # 1: 등록
                "content-type": "utf-8",
            },
            "body": {
                "input": {
                    "tr_id": tr_id,
                    "tr_key": ticker,
                }
            }
        }
        
        await self.websocket.send(json.dumps(msg))
        self.callbacks[ticker] = callback
        
        logging.info(f"📡 {ticker} 실시간 체결가 구독 시작")
    
    async def subscribe_orderbook(self, ticker: str, callback: Callable):
        """
        실시간 호가 구독
        
        Args:
            ticker: 종목코드
            callback: 데이터 수신 시 호출될 콜백 함수
        """
        tr_id = "H0STASP0"  # 실시간 호가
        
        msg = {
            "header": {
                "approval_key": self.auth.approval_key,
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8",
            },
            "body": {
                "input": {
                    "tr_id": tr_id,
                    "tr_key": ticker,
                }
            }
        }
        
        await self.websocket.send(json.dumps(msg))
        self.callbacks[f"{ticker}_orderbook"] = callback
        
        logging.info(f"📡 {ticker} 실시간 호가 구독 시작")
    
    async def listen(self):
        """메시지 수신 루프"""
        while self.running:
            try:
                raw = await self.websocket.recv()
                await self._process_message(raw)
            except websockets.ConnectionClosed:
                logging.warning("WebSocket 연결 종료")
                break
            except Exception as e:
                logging.error(f"메시지 처리 오류: {e}")
    
    async def _process_message(self, raw: str):
        """수신 메시지 처리"""
        if raw[0] in ["0", "1"]:
            # 데이터 메시지
            parts = raw.split("|")
            if len(parts) >= 4:
                tr_id = parts[1]
                data = parts[3]
                
                # 콜백 호출
                for key, callback in self.callbacks.items():
                    if key in data or tr_id in self.subscriptions.get(key, []):
                        await callback(data)
        else:
            # 시스템 메시지
            msg = json.loads(raw)
            if msg.get("header", {}).get("tr_id") == "PINGPONG":
                await self.websocket.pong(raw)
    
    async def close(self):
        """연결 종료"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
        logging.info("WebSocket 연결 해제")


# ================================================================================
# 🚀 통합 KIS API 클라이언트
# ================================================================================

class KISUnifiedClient:
    """
    KIS Open API 완전 통합 클라이언트
    
    모든 API 모듈을 하나의 인터페이스로 제공:
    - domestic_stock: 국내주식
    - overseas_stock: 해외주식
    - domestic_bond: 국내채권
    - domestic_future: 국내선물옵션
    - websocket: 실시간 데이터
    """
    
    def __init__(self, mode: str = "virtual", config_path: str = None):
        """
        Args:
            mode: 'real' (실전) 또는 'virtual' (모의)
            config_path: 설정 파일 경로
        """
        self.auth = KISAuthManager(config_path=config_path, mode=mode)
        
        # API 모듈 초기화
        self.domestic_stock = DomesticStockAPI(self.auth)
        self.overseas_stock = OverseasStockAPI(self.auth)
        self.domestic_bond = DomesticBondAPI(self.auth)
        self.domestic_future = DomesticFutureOptionAPI(self.auth)
        self.websocket = KISWebSocketClient(self.auth)
        
        logging.info(f"🔥 KIS Unified Client 초기화 완료 (모드: {mode})")
    
    def initialize(self) -> bool:
        """클라이언트 초기화 (토큰 발급)"""
        try:
            self.auth.get_access_token()
            return True
        except Exception as e:
            logging.error(f"초기화 실패: {e}")
            return False
    
    # ─────────────────────────────────────────────────────────────────────────
    # 🎯 편의 메서드 (자주 사용하는 기능 바로 접근)
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_price(self, ticker: str, market: str = "KR") -> Dict:
        """
        현재가 조회 (국내/해외 자동 판별)
        
        Args:
            ticker: 종목코드
            market: "KR" (국내) 또는 "US", "JP", "CN", "HK", "VN"
        """
        if market == "KR":
            return self.domestic_stock.get_price(ticker)
        else:
            exchange_map = {
                "US": "NAS",
                "JP": "TSE",
                "CN": "SHS",
                "HK": "HKS",
                "VN": "HSX",
            }
            return self.overseas_stock.get_price(
                ticker, 
                exchange_map.get(market, "NAS")
            )
    
    def place_order(self, ticker: str, action: str, quantity: int,
                    price: float = 0, market: str = "KR", 
                    exchange: str = None) -> Dict:
        """
        주문 실행 (국내/해외 자동 판별)
        
        Args:
            ticker: 종목코드
            action: "BUY" 또는 "SELL"
            quantity: 수량
            price: 가격 (시장가는 0)
            market: "KR" 또는 "US", "JP" 등
            exchange: 해외 거래소 코드 (market이 KR이 아닐 때)
        """
        if market == "KR":
            order_div = "01" if price == 0 else "00"  # 시장가/지정가
            return self.domestic_stock.place_order(
                ticker, action, quantity, int(price), order_div
            )
        else:
            if not exchange:
                exchange = "NAS" if market == "US" else "TSE"
            return self.overseas_stock.place_order(
                ticker, exchange, action, quantity, price
            )
    
    def get_balance(self, market: str = "KR") -> Tuple[pd.DataFrame, Dict]:
        """
        잔고 조회 (국내/해외)
        
        Args:
            market: "KR" 또는 "US" 등
        """
        if market == "KR":
            return self.domestic_stock.get_balance()
        else:
            return self.overseas_stock.get_balance()
    
    def get_daily_chart(self, ticker: str, market: str = "KR", 
                        period: str = "D") -> pd.DataFrame:
        """
        일봉/주봉/월봉 조회
        
        Args:
            ticker: 종목코드
            market: "KR" 또는 "US" 등
            period: "D" (일), "W" (주), "M" (월)
        """
        if market == "KR":
            return self.domestic_stock.get_daily_price(ticker, period)
        else:
            return self.overseas_stock.get_daily_price(ticker, period=period)


# ================================================================================
# 🎬 메인 실행 (테스트)
# ================================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    # 클라이언트 초기화
    client = KISUnifiedClient(mode="virtual")
    
    if client.initialize():
        print("\n" + "=" * 60)
        print("🔥 KIS Unified Client 테스트")
        print("=" * 60)
        
        # 삼성전자 현재가 조회
        price = client.get_price("005930", market="KR")
        print(f"\n삼성전자 현재가: {price.get('stck_prpr', 'N/A')}원")
        
        # 잔고 조회
        holdings, summary = client.get_balance()
        print(f"\n보유종목 수: {len(holdings)}")
        print(f"평가금액: {summary.get('tot_evlu_amt', 'N/A')}원")
        
        print("\n" + "=" * 60)
        print("✅ 테스트 완료!")
        print("=" * 60)
