#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ISATS v2.0 "Deep Eyes" - 피처 엔지니어링 모듈
"호가창이 쎄하다"는 느낌을 수학적 지표로 변환
"""

import numpy as np
import logging

logger = logging.getLogger("FeatureFactory")

class FeatureFactory:
    """고수의 직관을 수치화하는 피처 생산 공장"""
    
    @staticmethod
    def calculate_oir(bid_vols, ask_vols):
        """
        OIR (Order Imbalance Ratio): 매수/매도 세력 균형
        -1(매도우세) ~ +1(매수우세)
        """
        bid_sum = np.sum(bid_vols)
        ask_sum = np.sum(ask_vols)
        if (bid_sum + ask_sum) == 0:
            return 0
        return (bid_sum - ask_sum) / (bid_sum + ask_sum)

    @staticmethod
    def calculate_tfi(buy_trade_vol, sell_trade_vol):
        """
        TFI (Trade Flow Imbalance): 실제 체결 강도
        체결은 진짜 돈의 흐름.
        """
        if (buy_trade_vol + sell_trade_vol) == 0:
            return 0
        return (buy_trade_vol - sell_trade_vol) / (buy_trade_vol + sell_trade_vol)

    @staticmethod
    def calculate_micro_price(bid_p1, ask_p1, bid_v1, ask_v1):
        """
        Micro-Price (가중 평균가): 미래 가격 예측 포인트
        """
        if (bid_v1 + ask_v1) == 0:
            return (bid_p1 + ask_p1) / 2
        return (bid_p1 * ask_v1 + ask_p1 * bid_v1) / (bid_v1 + ask_v1)

    @staticmethod
    def calculate_spread_dynamics(bid_p1, ask_p1):
        """
        스프레드 동학: 변동성 확대 신호
        """
        return ask_p1 - bid_p1

    def generate_intuition_vector(self, data):
        """
        실시간 데이터를 받아 intuition vector 생성
        data에는 bid_vols, ask_vols, trade_vols 등이 포함되어야 함
        """
        try:
            # 호가 잔량 (리스트 형태 가정)
            bid_vols = data.get('bid_vols', [0]*10)
            ask_vols = data.get('ask_vols', [0]*10)
            
            # 1호가 정보
            bid_p1 = data.get('bid_p1', 0)
            ask_p1 = data.get('ask_p1', 0)
            bid_v1 = bid_vols[0] if bid_vols else 0
            ask_v1 = ask_vols[0] if ask_vols else 0
            
            # 체결 강도
            buy_vol = data.get('buy_vol', 0)
            sell_vol = data.get('sell_vol', 0)
            
            oir = self.calculate_oir(bid_vols, ask_vols)
            tfi = self.calculate_tfi(buy_vol, sell_vol)
            m_price = self.calculate_micro_price(bid_p1, ask_p1, bid_v1, ask_v1)
            spread = self.calculate_spread_dynamics(bid_p1, ask_p1)
            
            return np.array([oir, tfi, m_price, spread])
        except Exception as e:
            logger.error(f"피처 생성 오류: {e}")
            return None
