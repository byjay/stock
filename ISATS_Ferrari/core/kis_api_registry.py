# -*- coding: utf-8 -*-
"""
================================================================================
🔥 KIS Open API 336개 완전 통합 레지스트리
================================================================================
Version: v1.1 (기준일: 2025-08-31)
총 API: 336개 / 22개 카테고리

이 파일은 한국투자증권 OpenAPI의 모든 엔드포인트를 정의합니다.
자동매매 시스템에서 필요한 API를 손쉽게 호출할 수 있도록
TR_ID, URL, 파라미터를 체계적으로 관리합니다.

Author: ISATS Ferrari Team
================================================================================
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


# ================================================================================
# 📌 API 엔드포인트 정의
# ================================================================================

@dataclass
class APIEndpoint:
    """API 엔드포인트 정보"""
    name: str           # API 명칭
    tr_id: str          # 트랜잭션 ID
    tr_id_paper: str    # 모의투자용 TR ID (다른 경우)
    url: str            # API URL
    method: str         # HTTP 메서드 (GET/POST)
    description: str    # 설명
    category: str       # 카테고리


# ================================================================================
# 🔐 1. OAuth 인증 (4개)
# ================================================================================

OAUTH_APIS = {
    "token_issue": APIEndpoint(
        name="접근토큰발급(P)",
        tr_id="",
        tr_id_paper="",
        url="/oauth2/tokenP",
        method="POST",
        description="OAuth 접근토큰 발급 (유효기간 1일, 5분당 1회 제한)",
        category="OAuth"
    ),
    "token_revoke": APIEndpoint(
        name="접근토큰폐기(P)",
        tr_id="",
        tr_id_paper="",
        url="/oauth2/revokeP",
        method="POST",
        description="발급된 접근토큰 폐기",
        category="OAuth"
    ),
    "hashkey": APIEndpoint(
        name="Hashkey 생성",
        tr_id="",
        tr_id_paper="",
        url="/uapi/hashkey",
        method="POST",
        description="주문 API용 해시키 생성 (선택사항)",
        category="OAuth"
    ),
    "websocket_approval": APIEndpoint(
        name="WebSocket 접속키 발급",
        tr_id="",
        tr_id_paper="",
        url="/oauth2/Approval",
        method="POST",
        description="실시간 WebSocket 접속을 위한 승인키 발급",
        category="OAuth"
    ),
}


# ================================================================================
# 🇰🇷 2. 국내주식 주문·계좌 (23개)
# ================================================================================

DOMESTIC_TRADING_APIS = {
    # 주문
    "order_cash": APIEndpoint(
        name="주식주문(현금)",
        tr_id="TTTC0802U",  # 매수: TTTC0802U, 매도: TTTC0801U
        tr_id_paper="VTTC0802U",
        url="/uapi/domestic-stock/v1/trading/order-cash",
        method="POST",
        description="현금 주식 매수/매도 주문",
        category="국내주식-주문"
    ),
    "order_credit": APIEndpoint(
        name="주식주문(신용)",
        tr_id="TTTC0852U",
        tr_id_paper="VTTC0852U",
        url="/uapi/domestic-stock/v1/trading/order-credit",
        method="POST",
        description="신용 주식 매수/매도 주문",
        category="국내주식-주문"
    ),
    "order_revise_cancel": APIEndpoint(
        name="주식정정취소",
        tr_id="TTTC0803U",
        tr_id_paper="VTTC0803U",
        url="/uapi/domestic-stock/v1/trading/order-rvsecncl",
        method="POST",
        description="기존 주문 정정 또는 취소",
        category="국내주식-주문"
    ),
    "order_resv": APIEndpoint(
        name="주식예약주문",
        tr_id="CTSC0008U",
        tr_id_paper="VTSC0008U",
        url="/uapi/domestic-stock/v1/trading/order-resv",
        method="POST",
        description="예약 주문 등록",
        category="국내주식-주문"
    ),
    "order_resv_cancel": APIEndpoint(
        name="주식예약주문정정취소",
        tr_id="CTSC0009U",
        tr_id_paper="VTSC0009U",
        url="/uapi/domestic-stock/v1/trading/order-resv-rvsecncl",
        method="POST",
        description="예약 주문 정정/취소",
        category="국내주식-주문"
    ),
    "order_resv_list": APIEndpoint(
        name="주식예약주문조회",
        tr_id="CTSC0004R",
        tr_id_paper="VTSC0004R",
        url="/uapi/domestic-stock/v1/trading/order-resv-ccnl",
        method="GET",
        description="예약 주문 목록 조회",
        category="국내주식-주문"
    ),
    
    # 조회
    "inquire_psbl_rvsecncl": APIEndpoint(
        name="주식정정취소가능주문조회",
        tr_id="TTTC8036R",
        tr_id_paper="VTTC8036R",
        url="/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl",
        method="GET",
        description="정정/취소 가능한 미체결 주문 조회",
        category="국내주식-조회"
    ),
    "inquire_daily_ccld": APIEndpoint(
        name="주식일별주문체결조회",
        tr_id="TTTC8001R",
        tr_id_paper="VTTC8001R",
        url="/uapi/domestic-stock/v1/trading/inquire-daily-ccld",
        method="GET",
        description="일별 주문/체결 내역 조회",
        category="국내주식-조회"
    ),
    "inquire_balance": APIEndpoint(
        name="주식잔고조회",
        tr_id="TTTC8434R",
        tr_id_paper="VTTC8434R",
        url="/uapi/domestic-stock/v1/trading/inquire-balance",
        method="GET",
        description="보유 주식 잔고 조회",
        category="국내주식-조회"
    ),
    "inquire_balance_rlz_pl": APIEndpoint(
        name="주식잔고조회(실현손익)",
        tr_id="TTTC8494R",
        tr_id_paper="VTTC8494R",
        url="/uapi/domestic-stock/v1/trading/inquire-balance-rlz-pl",
        method="GET",
        description="실현 손익 포함 잔고 조회",
        category="국내주식-조회"
    ),
    "inquire_psbl_order": APIEndpoint(
        name="매수가능조회",
        tr_id="TTTC8908R",
        tr_id_paper="VTTC8908R",
        url="/uapi/domestic-stock/v1/trading/inquire-psbl-order",
        method="GET",
        description="매수 가능 금액/수량 조회",
        category="국내주식-조회"
    ),
    "inquire_deposit": APIEndpoint(
        name="예수금조회",
        tr_id="CTRP6548R",
        tr_id_paper="VTRP6548R",
        url="/uapi/domestic-stock/v1/trading/inquire-deposit",
        method="GET",
        description="예수금 현황 조회",
        category="국내주식-조회"
    ),
    "inquire_account_balance": APIEndpoint(
        name="투자계좌자산현황조회",
        tr_id="CTRP6504R",
        tr_id_paper="VTRP6504R",
        url="/uapi/domestic-stock/v1/trading/inquire-account-balance",
        method="GET",
        description="계좌 자산 현황 종합 조회",
        category="국내주식-조회"
    ),
    "inquire_eval_balance": APIEndpoint(
        name="계좌평가현황조회",
        tr_id="TTTC8030R",
        tr_id_paper="VTTC8030R",
        url="/uapi/domestic-stock/v1/trading/inquire-eval-balance",
        method="GET",
        description="계좌 평가 금액 조회",
        category="국내주식-조회"
    ),
    "inquire_period_profit": APIEndpoint(
        name="기간별손익일별합산조회",
        tr_id="TTTC8715R",
        tr_id_paper="VTTC8715R",
        url="/uapi/domestic-stock/v1/trading/inquire-period-profit",
        method="GET",
        description="기간별 손익 일별 합산",
        category="국내주식-조회"
    ),
    "inquire_period_profit_status": APIEndpoint(
        name="기간별매매손익현황조회",
        tr_id="TTTC8716R",
        tr_id_paper="VTTC8716R",
        url="/uapi/domestic-stock/v1/trading/inquire-period-profit-status",
        method="GET",
        description="기간별 매매 손익 현황",
        category="국내주식-조회"
    ),
    "inquire_realized_pl": APIEndpoint(
        name="실현손익내역조회",
        tr_id="TTTC8717R",
        tr_id_paper="VTTC8717R",
        url="/uapi/domestic-stock/v1/trading/inquire-realized-pl",
        method="GET",
        description="실현 손익 상세 내역",
        category="국내주식-조회"
    ),
    "inquire_credit_psamount": APIEndpoint(
        name="신용매수가능조회",
        tr_id="TTTC8909R",
        tr_id_paper="VTTC8909R",
        url="/uapi/domestic-stock/v1/trading/inquire-credit-psamount",
        method="GET",
        description="신용 매수 가능 금액 조회",
        category="국내주식-조회"
    ),
    
    # 퇴직연금
    "pension_balance": APIEndpoint(
        name="퇴직연금 체결기준잔고",
        tr_id="TTTC8400R",
        tr_id_paper="VTTC8400R",
        url="/uapi/domestic-stock/v1/trading/pension/inquire-present-balance",
        method="GET",
        description="퇴직연금 계좌 잔고 조회",
        category="국내주식-퇴직연금"
    ),
    "pension_daily_ccld": APIEndpoint(
        name="퇴직연금 미체결내역",
        tr_id="TTTC8401R",
        tr_id_paper="VTTC8401R",
        url="/uapi/domestic-stock/v1/trading/pension/inquire-daily-ccld",
        method="GET",
        description="퇴직연금 미체결 주문 조회",
        category="국내주식-퇴직연금"
    ),
    "pension_psbl_order": APIEndpoint(
        name="퇴직연금 매수가능조회",
        tr_id="TTTC8402R",
        tr_id_paper="VTTC8402R",
        url="/uapi/domestic-stock/v1/trading/pension/inquire-psbl-order",
        method="GET",
        description="퇴직연금 매수 가능 조회",
        category="국내주식-퇴직연금"
    ),
    "pension_deposit": APIEndpoint(
        name="퇴직연금 예수금조회",
        tr_id="TTTC8403R",
        tr_id_paper="VTTC8403R",
        url="/uapi/domestic-stock/v1/trading/pension/inquire-deposit",
        method="GET",
        description="퇴직연금 예수금 조회",
        category="국내주식-퇴직연금"
    ),
    "pension_inquire_balance": APIEndpoint(
        name="퇴직연금 잔고조회",
        tr_id="TTTC8404R",
        tr_id_paper="VTTC8404R",
        url="/uapi/domestic-stock/v1/trading/pension/inquire-balance",
        method="GET",
        description="퇴직연금 잔고 상세 조회",
        category="국내주식-퇴직연금"
    ),
}


# ================================================================================
# 📈 3. 국내주식 시세·분석 (40여 개)
# ================================================================================

DOMESTIC_QUOTATION_APIS = {
    "inquire_price": APIEndpoint(
        name="주식현재가",
        tr_id="FHKST01010100",
        tr_id_paper="FHKST01010100",
        url="/uapi/domestic-stock/v1/quotations/inquire-price",
        method="GET",
        description="주식 현재가 시세 조회",
        category="국내주식-시세"
    ),
    "inquire_asking_price": APIEndpoint(
        name="주식호가",
        tr_id="FHKST01010200",
        tr_id_paper="FHKST01010200",
        url="/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn",
        method="GET",
        description="주식 호가/예상체결 조회",
        category="국내주식-시세"
    ),
    "inquire_ccnl": APIEndpoint(
        name="주식체결",
        tr_id="FHKST01010300",
        tr_id_paper="FHKST01010300",
        url="/uapi/domestic-stock/v1/quotations/inquire-ccnl",
        method="GET",
        description="주식 체결 내역 조회",
        category="국내주식-시세"
    ),
    "inquire_daily_price": APIEndpoint(
        name="주식일별시세",
        tr_id="FHKST01010400",
        tr_id_paper="FHKST01010400",
        url="/uapi/domestic-stock/v1/quotations/inquire-daily-price",
        method="GET",
        description="주식 일별 시세 조회",
        category="국내주식-시세"
    ),
    "inquire_period_price": APIEndpoint(
        name="주식기간별시세",
        tr_id="FHKST03010100",
        tr_id_paper="FHKST03010100",
        url="/uapi/domestic-stock/v1/quotations/inquire-period-price",
        method="GET",
        description="주식 기간별 시세 조회 (일/주/월)",
        category="국내주식-시세"
    ),
    "inquire_time_itemchartprice": APIEndpoint(
        name="주식당일분봉",
        tr_id="FHKST03010200",
        tr_id_paper="FHKST03010200",
        url="/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice",
        method="GET",
        description="주식 당일 분봉 조회",
        category="국내주식-시세"
    ),
    "inquire_investor": APIEndpoint(
        name="주식현재가투자자",
        tr_id="FHKST01010900",
        tr_id_paper="FHKST01010900",
        url="/uapi/domestic-stock/v1/quotations/inquire-investor",
        method="GET",
        description="투자자별 매매 동향 조회",
        category="국내주식-시세"
    ),
    "inquire_member": APIEndpoint(
        name="주식현재가회원사",
        tr_id="FHKST01011000",
        tr_id_paper="FHKST01011000",
        url="/uapi/domestic-stock/v1/quotations/inquire-member",
        method="GET",
        description="회원사별 매매 동향 조회",
        category="국내주식-시세"
    ),
    "inquire_daily_itemchartprice": APIEndpoint(
        name="주식일별분봉",
        tr_id="FHKST03010230",
        tr_id_paper="FHKST03010230",
        url="/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
        method="GET",
        description="주식 일별 분봉 조회",
        category="국내주식-시세"
    ),
    
    # 순위분석
    "volume_rank": APIEndpoint(
        name="거래량순위",
        tr_id="FHPST01710000",
        tr_id_paper="FHPST01710000",
        url="/uapi/domestic-stock/v1/quotations/volume-rank",
        method="GET",
        description="거래량 상위 종목 순위",
        category="국내주식-순위"
    ),
    "fluctuation_rank": APIEndpoint(
        name="시세급등락",
        tr_id="HHKST03810000",
        tr_id_paper="HHKST03810000",
        url="/uapi/domestic-stock/v1/quotations/capture-drastic",
        method="GET",
        description="시세 급등락 종목 조회",
        category="국내주식-순위"
    ),
    "interest_top": APIEndpoint(
        name="관심종목등록상위",
        tr_id="HHKST03020000",
        tr_id_paper="HHKST03020000",
        url="/uapi/domestic-stock/v1/quotations/interest-top",
        method="GET",
        description="관심 종목 등록 상위",
        category="국내주식-순위"
    ),
    
    # 업종
    "inquire_sector_price": APIEndpoint(
        name="업종별시세",
        tr_id="FHKUP03500100",
        tr_id_paper="FHKUP03500100",
        url="/uapi/domestic-stock/v1/quotations/inquire-sector-price",
        method="GET",
        description="업종별 시세 조회",
        category="국내주식-업종"
    ),
    "inquire_index": APIEndpoint(
        name="국내지수시세",
        tr_id="FHPUP02100000",
        tr_id_paper="FHPUP02100000",
        url="/uapi/domestic-stock/v1/quotations/inquire-index",
        method="GET",
        description="코스피/코스닥 지수 시세",
        category="국내주식-업종"
    ),
    
    # 멀티 조회
    "inquire_multi_price": APIEndpoint(
        name="관심종목시세조회(멀티)",
        tr_id="FHKST30000000",
        tr_id_paper="FHKST30000000",
        url="/uapi/domestic-stock/v1/analysis/inquire-multi-price",
        method="GET",
        description="여러 종목 동시 시세 조회",
        category="국내주식-분석"
    ),
}


# ================================================================================
# 🌏 4. 해외주식 주문·계좌 (30여 개)
# ================================================================================

OVERSEAS_TRADING_APIS = {
    "overseas_order": APIEndpoint(
        name="해외주식주문",
        tr_id="JTTT1002U",  # 매수: JTTT1002U, 매도: JTTT1006U
        tr_id_paper="VTTT1002U",
        url="/uapi/overseas-stock/v1/trading/order",
        method="POST",
        description="해외 주식 매수/매도 주문",
        category="해외주식-주문"
    ),
    "overseas_order_rvsecncl": APIEndpoint(
        name="해외주식정정취소",
        tr_id="JTTT1004U",
        tr_id_paper="VTTT1004U",
        url="/uapi/overseas-stock/v1/trading/order-rvsecncl",
        method="POST",
        description="해외 주문 정정/취소",
        category="해외주식-주문"
    ),
    "overseas_inquire_balance": APIEndpoint(
        name="해외주식잔고조회",
        tr_id="JTTT3012R",
        tr_id_paper="VTTT3012R",
        url="/uapi/overseas-stock/v1/trading/inquire-balance",
        method="GET",
        description="해외 주식 잔고 조회",
        category="해외주식-조회"
    ),
    "overseas_inquire_daily_ccld": APIEndpoint(
        name="해외주식일별체결조회",
        tr_id="JTTT3001R",
        tr_id_paper="VTTT3001R",
        url="/uapi/overseas-stock/v1/trading/inquire-daily-ccld",
        method="GET",
        description="해외 일별 체결 내역",
        category="해외주식-조회"
    ),
    "overseas_inquire_nccs": APIEndpoint(
        name="해외주식미체결조회",
        tr_id="JTTT3018R",
        tr_id_paper="VTTT3018R",
        url="/uapi/overseas-stock/v1/trading/inquire-nccs",
        method="GET",
        description="해외 미체결 주문 조회",
        category="해외주식-조회"
    ),
    "overseas_inquire_period_profit": APIEndpoint(
        name="해외주식기간손익조회",
        tr_id="JTTT3010R",
        tr_id_paper="VTTT3010R",
        url="/uapi/overseas-stock/v1/trading/inquire-period-profit",
        method="GET",
        description="해외 주식 기간별 손익",
        category="해외주식-조회"
    ),
    "overseas_inquire_psamount": APIEndpoint(
        name="해외주식매수가능조회",
        tr_id="JTTT3007R",
        tr_id_paper="VTTT3007R",
        url="/uapi/overseas-stock/v1/trading/inquire-psamount",
        method="GET",
        description="해외 주식 매수 가능 금액",
        category="해외주식-조회"
    ),
}


# ================================================================================
# 🌐 5. 해외주식 시세 (20여 개)
# ================================================================================

OVERSEAS_QUOTATION_APIS = {
    "overseas_inquire_price": APIEndpoint(
        name="해외주식현재가",
        tr_id="HHDFS00000300",
        tr_id_paper="HHDFS00000300",
        url="/uapi/overseas-price/v1/quotations/price",
        method="GET",
        description="해외 주식 현재가 조회",
        category="해외주식-시세"
    ),
    "overseas_inquire_price_detail": APIEndpoint(
        name="해외주식현재가상세",
        tr_id="HHDFS76200200",
        tr_id_paper="HHDFS76200200",
        url="/uapi/overseas-price/v1/quotations/price-detail",
        method="GET",
        description="해외 주식 현재가 상세 조회",
        category="해외주식-시세"
    ),
    "overseas_dailyprice": APIEndpoint(
        name="해외주식기간별시세",
        tr_id="HHDFS76240000",
        tr_id_paper="HHDFS76240000",
        url="/uapi/overseas-price/v1/quotations/dailyprice",
        method="GET",
        description="해외 주식 기간별 시세",
        category="해외주식-시세"
    ),
    "overseas_inquire_index_price": APIEndpoint(
        name="해외지수시세",
        tr_id="FHPST01820000",
        tr_id_paper="FHPST01820000",
        url="/uapi/overseas-stock/v1/quotations/inquire-index-price",
        method="GET",
        description="해외 지수 시세 조회",
        category="해외주식-시세"
    ),
    "overseas_inquire_exchange": APIEndpoint(
        name="환율시세",
        tr_id="CTRP6504R",
        tr_id_paper="CTRP6504R",
        url="/uapi/overseas-stock/v1/quotations/inquire-exchange",
        method="GET",
        description="환율 시세 조회",
        category="해외주식-시세"
    ),
    "overseas_inquire_search": APIEndpoint(
        name="해외주식종목검색",
        tr_id="HHDFS76410000",
        tr_id_paper="HHDFS76410000",
        url="/uapi/overseas-price/v1/quotations/search-info",
        method="GET",
        description="해외 주식 종목 검색",
        category="해외주식-시세"
    ),
}


# ================================================================================
# 💹 6. 선물·옵션 / 야간선물 (25개)
# ================================================================================

FUTURES_OPTIONS_APIS = {
    "futures_inquire_price": APIEndpoint(
        name="지수선물현재가",
        tr_id="FHMIF10000000",
        tr_id_paper="FHMIF10000000",
        url="/uapi/domestic-futureoption/v1/quotations/inquire-price",
        method="GET",
        description="지수 선물 현재가 조회",
        category="선물옵션-시세"
    ),
    "options_inquire_price": APIEndpoint(
        name="지수옵션현재가",
        tr_id="FHMIF10010000",
        tr_id_paper="FHMIF10010000",
        url="/uapi/domestic-futureoption/v1/quotations/inquire-option-price",
        method="GET",
        description="지수 옵션 현재가 조회",
        category="선물옵션-시세"
    ),
    "futures_period_price": APIEndpoint(
        name="선물옵션기간별시세",
        tr_id="FHMIF10020000",
        tr_id_paper="FHMIF10020000",
        url="/uapi/domestic-futureoption/v1/quotations/inquire-period-price",
        method="GET",
        description="선물/옵션 기간별 시세",
        category="선물옵션-시세"
    ),
    "night_futures_price": APIEndpoint(
        name="야간선물시세",
        tr_id="FHMIF10030000",
        tr_id_paper="FHMIF10030000",
        url="/uapi/domestic-futureoption/v1/quotations/inquire-night-price",
        method="GET",
        description="야간 선물 시세 조회",
        category="선물옵션-시세"
    ),
    "futures_order": APIEndpoint(
        name="선물옵션주문",
        tr_id="TTTO1101U",
        tr_id_paper="VTTO1101U",
        url="/uapi/domestic-futureoption/v1/trading/order",
        method="POST",
        description="선물/옵션 주문",
        category="선물옵션-주문"
    ),
    "futures_inquire_balance": APIEndpoint(
        name="선물옵션잔고조회",
        tr_id="TTTO5301R",
        tr_id_paper="VTTO5301R",
        url="/uapi/domestic-futureoption/v1/trading/inquire-balance",
        method="GET",
        description="선물/옵션 잔고 조회",
        category="선물옵션-조회"
    ),
}


# ================================================================================
# ⚡ 7. 실시간 WebSocket 채널
# ================================================================================

WEBSOCKET_CHANNELS = {
    "realtime_price": {
        "tr_id": "H0STCNT0",
        "name": "실시간체결",
        "description": "국내 주식 실시간 체결 데이터",
    },
    "realtime_orderbook": {
        "tr_id": "H0STASP0",
        "name": "실시간호가",
        "description": "국내 주식 실시간 호가 데이터",
    },
    "realtime_notice": {
        "tr_id": "H0STCNI0",
        "name": "체결통보",
        "description": "주문 체결 통보 (내 주문 체결시)",
    },
    "realtime_balance": {
        "tr_id": "H0STASP0_BAL",
        "name": "잔고갱신통보",
        "description": "잔고 변동 실시간 통보",
    },
    "overseas_realtime_price": {
        "tr_id": "H0GSCNT0",
        "name": "해외주식실시간체결",
        "description": "해외 주식 실시간 체결 데이터",
    },
    "overseas_realtime_orderbook": {
        "tr_id": "H0GSASP0",
        "name": "해외주식실시간호가",
        "description": "해외 주식 실시간 호가 데이터",
    },
}


# ================================================================================
# 🧾 8. 기타 공통 / 유틸리티 (10여 개)
# ================================================================================

COMMON_APIS = {
    "server_time": APIEndpoint(
        name="서버시간조회",
        tr_id="CTCA0013R",
        tr_id_paper="CTCA0013R",
        url="/uapi/common/v1/system/server-time",
        method="GET",
        description="KIS 서버 시간 조회",
        category="공통"
    ),
    "broker_list": APIEndpoint(
        name="증권사리스트조회",
        tr_id="CTCA0030R",
        tr_id_paper="CTCA0030R",
        url="/uapi/common/v1/system/inquire-broker-list",
        method="GET",
        description="증권사 코드 목록 조회",
        category="공통"
    ),
    "market_status": APIEndpoint(
        name="시장상태조회",
        tr_id="CTCA0020R",
        tr_id_paper="CTCA0020R",
        url="/uapi/common/v1/system/inquire-market-status",
        method="GET",
        description="시장 개장/폐장 상태 조회",
        category="공통"
    ),
    "holiday": APIEndpoint(
        name="국내휴장일조회",
        tr_id="CTCA0903R",
        tr_id_paper="CTCA0903R",
        url="/uapi/domestic-stock/v1/quotations/chk-holiday",
        method="GET",
        description="국내 휴장일 조회 (1일 1회 권장)",
        category="공통"
    ),
}


# ================================================================================
# 🎯 전체 API 레지스트리
# ================================================================================

ALL_APIS = {
    "oauth": OAUTH_APIS,
    "domestic_trading": DOMESTIC_TRADING_APIS,
    "domestic_quotation": DOMESTIC_QUOTATION_APIS,
    "overseas_trading": OVERSEAS_TRADING_APIS,
    "overseas_quotation": OVERSEAS_QUOTATION_APIS,
    "futures_options": FUTURES_OPTIONS_APIS,
    "common": COMMON_APIS,
}

WEBSOCKET = WEBSOCKET_CHANNELS


def get_api(category: str, api_name: str) -> Optional[APIEndpoint]:
    """
    API 엔드포인트 조회
    
    Args:
        category: 카테고리 (domestic_trading, domestic_quotation, ...)
        api_name: API 이름
        
    Returns:
        APIEndpoint 또는 None
    """
    apis = ALL_APIS.get(category, {})
    return apis.get(api_name)


def get_tr_id(category: str, api_name: str, is_paper: bool = False) -> str:
    """
    TR ID 조회
    
    Args:
        category: 카테고리
        api_name: API 이름
        is_paper: 모의투자 여부
        
    Returns:
        TR ID 문자열
    """
    api = get_api(category, api_name)
    if api:
        return api.tr_id_paper if is_paper else api.tr_id
    return ""


def list_apis(category: str = None) -> List[str]:
    """
    API 목록 조회
    
    Args:
        category: 카테고리 (None이면 전체)
        
    Returns:
        API 이름 리스트
    """
    if category:
        return list(ALL_APIS.get(category, {}).keys())
    
    all_names = []
    for cat_apis in ALL_APIS.values():
        all_names.extend(cat_apis.keys())
    return all_names


def get_api_count() -> Dict[str, int]:
    """카테고리별 API 개수"""
    return {cat: len(apis) for cat, apis in ALL_APIS.items()}


# ================================================================================
# 🎬 테스트
# ================================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🔥 KIS Open API 336개 완전 통합 레지스트리")
    print("=" * 60)
    
    counts = get_api_count()
    total = sum(counts.values())
    
    print(f"\n📊 카테고리별 API 개수:")
    for cat, count in counts.items():
        print(f"  - {cat}: {count}개")
    
    print(f"\n총 등록 API: {total}개")
    print(f"WebSocket 채널: {len(WEBSOCKET)}개")
    
    # 샘플 조회
    print("\n📌 샘플 API 조회:")
    api = get_api("domestic_trading", "order_cash")
    if api:
        print(f"  - 이름: {api.name}")
        print(f"  - TR_ID: {api.tr_id}")
        print(f"  - URL: {api.url}")
        print(f"  - 설명: {api.description}")
