"""
🛡️ ISATS PHOENIX S-CLASS: SAVAGE VALIDATOR API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
역할:
- 외부 데이터 소스(Mock Safari API)를 통한 실시간 시장 데이터 통합 검증
- 사용자 신호에 대한 냉소적 비평 및 신뢰도 산출
- 계좌 상태 기반의 현실 체크(Reality Check) 수행

원칙:
- 모든 데이터 호출은 예외 처리를 동반한다.
- 비평은 날카롭고 구체적이어야 한다 (Savage Logic).
- 실제 자산 보호를 위해 가혹한 기준을 적용한다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Optional, Any, List

class SavageValidatorAPI:
    """
    S-Class 냉소적 검증 API.
    시장의 장밋빛 전망을 파괴하고 객관적인 지표로 진실을 드러냅니다.
    """
    
    # 설정 상수 (S-Class Standard)
    SAFARI_URL: str = "https://api.safari.com/v1"

    def __init__(self, api_key: str = "S-CLASS-PHOENIX-KEY") -> None:
        """
        검증 엔진 초기화.
        
        Args:
            api_key (str): 사파리 API 접근 키.
        """
        self.api_key: str = api_key
        self.headers: Dict[str, str] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 가혹한 검증 임계값
        self.min_vol_ratio: float = 2.0
        self.min_strength: float = 120.0
        self.spread_limit: float = 0.002
        
    def fetch_market_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        외부 API를 통해 실시간 시장 데이터를 조회합니다. (Mock 연동)
        
        Args:
            ticker (str): 종목 코드.
            
        Returns:
            Optional[Dict]: 수집된 데이터 세트.
        """
        try:
            # [MOCK] 실제 연동 시 requests 사용
            return {
                "ticker": ticker,
                "price": 100000.0,
                "volume": 50000,
                "volume_avg_20": 20000,
                "order_strength": 135.0,
                "rsi": 45.0,
                "ma20": 98000.0,
                "ma60": 95000.0,
                "bid": 99900.0,
                "ask": 100100.0
            }
        except Exception as e:
            print(f"🚨 API Fetch Error: {e}")
            return None
    
    def validate_signal(self, ticker: str, signal_type: str = "BUY") -> Dict[str, Any]:
        """
        매매 신호의 정밀 검증을 수행하고 냉소적 리포트를 생성합니다.
        
        Args:
            ticker (str): 종목 코드.
            signal_type (str): "BUY" 또는 "SELL".
            
        Returns:
            Dict: 검증 결과 및 비평.
        """
        data: Optional[Dict[str, Any]] = self.fetch_market_data(ticker)
        if not data:
            return self._build_error_response("데이터 동기화 실패")

        checks: List[str] = []
        comments: List[str] = []
        confidence: float = 100.0
        
        # 1. 수급 분석
        vol_ratio: float = data["volume"] / data["volume_avg_20"]
        if vol_ratio < self.min_vol_ratio:
            confidence -= 40
            comments.append(f"💀 거래량이 {vol_ratio:.1f}배? 당신 혼자 파티 중이군요.")
            checks.append("❌ 거래량 부족")
        else:
            checks.append("✅ 거래량 합격")

        # 2. 체결강도 분석
        strength: float = data["order_strength"]
        if strength < self.min_strength:
            confidence -= 30
            comments.append(f"⚠️ 체결강도 {strength}%... 곧 물릴 관상입니다.")
            checks.append("❌ 수급 강도 약세")
        else:
            checks.append("✅ 체결강도 우수")

        # 3. 추세 및 모멘텀 (RSI)
        if data["rsi"] > 80:
            confidence -= 20
            comments.append("🔥 RSI 과열! 고점 판독기 가동 중.")
            checks.append("❌ 과매수 상태")
        
        # 최종 판정
        confidence = max(0.0, min(100.0, confidence))
        is_valid: bool = confidence >= 85 # S-Class는 기준이 높음

        return {
            "is_valid": is_valid,
            "confidence": round(confidence, 1),
            "reason": "S-CLASS PHOENIX APPROVED" if is_valid else "SYSTEM REJECTED",
            "savage_comment": "\n".join(comments) if comments else "✅ 완벽하군요. (방심은 금물입니다)",
            "checks": checks,
            "details": data
        }

    def _build_error_response(self, message: str) -> Dict[str, Any]:
        """에러 응답 생성 유틸리티."""
        return {
            "is_valid": False,
            "confidence": 0,
            "reason": message,
            "savage_comment": "🤡 현실 부정 중이신가요? 시스템이 응답하지 않습니다.",
            "checks": ["❌ SYSTEM FAILURE"],
            "details": {}
        }
    
    def get_reality_check(self, balance: float, bet_amount: float, recent_trades: list) -> Dict:
        """
        현실 체크 (계좌 잔고, 승률, 복수 매매)
        
        Args:
            balance: 계좌 잔고
            bet_amount: 베팅 금액
            recent_trades: 최근 거래 결과 [True, False, ...]
            
        Returns:
            현실 체크 결과
        """
        warnings = []
        
        # 1. 계좌 잔고 체크
        if bet_amount > balance:
            warnings.append({
                "type": "CRITICAL",
                "message": "🤡 돈도 없으면서 무슨 매매를 하시려고? 현실을 직시하세요."
            })
        elif bet_amount > balance * 0.1:
            warnings.append({
                "type": "DANGER",
                "message": f"⚠️ 계좌의 {bet_amount/balance*100:.0f}%를 한 번에? 미쳤습니까? 분산투자 들어보셨나요?"
            })
        elif bet_amount > balance * 0.05:
            warnings.append({
                "type": "WARNING",
                "message": "⚠️ 계좌의 5% 이상 투자... 용감하시네요. (무모하다는 뜻)"
            })
        
        # 2. 승률 체크
        if len(recent_trades) >= 10:
            win_rate = sum(recent_trades) / len(recent_trades) * 100
            
            if win_rate > 70:
                warnings.append({
                    "type": "INFO",
                    "message": f"🎰 승률 {win_rate:.1f}%? 당신은 워렌 버핏을 뛰어넘었습니다! (거짓말입니다. 샘플이 적거나 운이 좋았을 뿐)"
                })
            elif win_rate < 30:
                warnings.append({
                    "type": "DANGER",
                    "message": f"💀 승률 {win_rate:.1f}% - 이 정도면 그냥 반대로 매매하는 게 나을 듯? 진지하게."
                })
        
        # 3. 복수 매매 체크
        if len(recent_trades) > 0 and not recent_trades[-1]:
            warnings.append({
                "type": "WARNING",
                "message": "🎲 방금 손실 났죠? 복수 매매하려고요? 파산 지름길입니다. 멈추세요."
            })
        
        return {
            "is_safe": len([w for w in warnings if w["type"] in ["CRITICAL", "DANGER"]]) == 0,
            "warnings": warnings,
            "savage_summary": (
                "💊 현실 체크 완료. 당신의 월급을 지키는 것이 우리의 임무입니다."
                if warnings else
                "✅ 현실 체크 통과. 그래도 이성적으로 판단하세요."
            )
        }


# ==========================================
# FastAPI 엔드포인트 (Flask/FastAPI에 통합)
# ==========================================

def create_validator_endpoints(app):
    """
    Flask/FastAPI 앱에 검증 엔드포인트 추가
    
    사용법:
        from flask import Flask
        app = Flask(__name__)
        create_validator_endpoints(app)
    """
    validator = SavageValidatorAPI()
    
    @app.route('/api/validate/signal', methods=['POST'])
    def validate_signal():
        """
        POST /api/validate/signal
        Body: {"ticker": "NVDA", "signal_type": "BUY"}
        """
        from flask import request, jsonify
        
        data = request.get_json()
        ticker = data.get('ticker')
        signal_type = data.get('signal_type', 'BUY')
        
        if not ticker:
            return jsonify({"error": "ticker is required"}), 400
        
        result = validator.validate_signal(ticker, signal_type)
        return jsonify(result)
    
    @app.route('/api/validate/reality', methods=['POST'])
    def validate_reality():
        """
        POST /api/validate/reality
        Body: {
            "balance": 1000000,
            "bet_amount": 100000,
            "recent_trades": [true, false, true, ...]
        }
        """
        from flask import request, jsonify
        
        data = request.get_json()
        balance = data.get('balance', 0)
        bet_amount = data.get('bet_amount', 0)
        recent_trades = data.get('recent_trades', [])
        
        result = validator.get_reality_check(balance, bet_amount, recent_trades)
        return jsonify(result)
    
    print("✅ Savage Validator API endpoints registered:")
    print("   - POST /api/validate/signal")
    print("   - POST /api/validate/reality")


# ==========================================
# 테스트
# ==========================================

if __name__ == "__main__":
    print("=" * 60)
    print("🛡️  SAVAGE VALIDATOR API - TEST MODE")
    print("=" * 60)
    print()
    
    validator = SavageValidatorAPI()
    
    # 더미 데이터로 테스트
    print("📊 테스트 1: 신호 검증 (더미 데이터)")
    print("-" * 60)
    
    # 실제로는 사파리 API에서 받아올 데이터
    # 여기서는 테스트용 더미 데이터 사용
    test_result = validator.validate_signal("NVDA", "BUY")
    
    print(f"검증 결과: {'✅ 통과' if test_result['is_valid'] else '❌ 실패'}")
    print(f"신뢰도: {test_result['confidence']}%")
    print(f"사유: {test_result['reason']}")
    print()
    print("냉소적 코멘트:")
    print(test_result['savage_comment'])
    print()
    print("상세 체크:")
    for check in test_result['checks']:
        print(f"  {check}")
    print()
    
    # 현실 체크 테스트
    print("=" * 60)
    print("💊 테스트 2: 현실 체크")
    print("-" * 60)
    
    reality = validator.get_reality_check(
        balance=1000000,
        bet_amount=200000,
        recent_trades=[True, False, True, False, False]
    )
    
    print(f"안전 여부: {'✅ 안전' if reality['is_safe'] else '❌ 위험'}")
    print()
    print("경고 사항:")
    for warning in reality['warnings']:
        print(f"  [{warning['type']}] {warning['message']}")
    print()
    print(reality['savage_summary'])
    print()
    print("=" * 60)
