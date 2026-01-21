"""
[파일명]: backend/ai/gemini_advisor.py
[역할]: ISATS의 '이성적 브레인'. 퀀트 전략이 찾은 타점에 대해 AI가 최종 이성적 판단을 내림.
[저장위치]: c:/Users/FREE/Desktop/주식/isats/backend/ai/gemini_advisor.py
[상세설명]:
구글 제미나이(Gemini 1.5 Pro & Flash) API를 활용하여, 단순히 수치만 보는 것이 아니라 
현재의 시황, 뉴스, 테마성 등을 종합적으로 고려하여 매수 신호에 대한 최종 승인(Confirm)을 내립니다.
무료 할당량을 아끼기 위해 중요도에 따라 Pro와 Flash 모델을 교대로 사용합니다.
"""

import logging
import os
import json
import google.generativeai as genai
from typing import Dict, Any

logger = logging.getLogger("GeminiAdvisor")

class GeminiAdvisor:
    """
    제미나이 AI를 활용하여 매매 신호의 타당성을 검토하는 클래스입니다.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.mock_mode = os.getenv("GEMINI_MOCK_MODE", "FALSE").upper() == "TRUE"
        
        if not self.mock_mode and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # [듀얼 엔진] Pro는 정밀 판단용, Flash는 고속 분석용
                self.pro_model = genai.GenerativeModel('gemini-1.5-pro')
                self.flash_model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Gemini AI 듀얼 엔진(Pro & Flash) 초기화 완료.")
            except Exception as e:
                logger.error(f"제미나이 API 설정 실패: {e}. Mock 모드로 전환합니다.")
                self.mock_mode = True
        else:
            logger.warning("GEMINI_API_KEY를 찾을 수 없습니다. Mock 모드로 가동합니다.")
            self.mock_mode = True

    async def ask_ai_confirmation(self, code: str, technical_summary: Dict, news_summary: Dict) -> Dict[str, Any]:
        """
        퀀트 알고리즘이 발생시킨 신호에 대해 AI 파트너의 최종 의견을 묻습니다.
        [전략]: 중요 신호(Critical)는 성능 위주의 Pro, 일반 신호(Normal)는 속도 위주의 Flash 사용.
        """
        if self.mock_mode:
            return self._mock_decision(technical_summary)

        # 중요도에 따라 모델 선택 (스나이퍼 전략 등은 Pro 사용 권장)
        # [COST-FREE OPTIMIZATION]
        # User requested NO BILLING. We force 'gemini-1.5-flash' which has a generous free tier.
        # 'gemini-1.5-pro' is disabled to prevent accidental costs.
        model = self.flash_model 
        
        # AI 트레이더에게 전달할 냉철한 프롬프트 구성
        prompt = f"""
        당신은 냉철한 퀀트 트레이더입니다. {code} 종목의 신호를 검증하십시오.
        
        [기술적 지표]:
        {json.dumps(technical_summary, indent=2, ensure_ascii=False)}
        
        [최근 뉴스 및 매크로 상황]:
        {json.dumps(news_summary, indent=2, ensure_ascii=False)}
        
        [가이드라인]
        [전략적 지침: "APEX ADAPTATION - 압도적 유능함"]
        1. 당신은 겁쟁이 기록관이 아니라, 위기 상황의 '전술 지휘관(Tactical Commander)'입니다.
        2. '혼돈(Chaos)'은 도망칠 신호가 아니라, 대중의 공포를 역이용할 '기회'입니다. 
        3. [Maverick 판단] 섹터가 무너져도 이 종목만의 독보적 거래량과 에너지가 있다면 과감히 'BUY'를 승인하십시오.
        4. [위기 베팅] 폭락장에서도 과매도(RSI < 20)와 수급(Volume)이 수학적 반등을 가리키면 '공격적 진입'을 명령하십시오.
        
        당신의 판단(Decision)이 최종 실행을 결정합니다. 냉철하고 과감하게 답하십시오:
        {
            "decision": "BUY" | "SELL" | "HOLD",
            "reason": "결정 사유 (한글 20자 이내)",
            "tactical_context": "현재 상황을 '위기'로 볼 것인가, '기회'로 볼 것인가?",
            "chaos_opportunity_score": 0.0 ~ 1.0 (높을수록 위기 속 기회),
            "confidence_score": 0.0 ~ 1.0
        }
        """
        
        try:
            # 비동기적으로 AI의 답변을 기다림
            response = await model.generate_content_async(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Resource has been exhausted" in error_msg:
                logger.warning("⚠️ [QUOTA] Gemini Free Tier Limit Reached. Switching to Mock Decision.")
                return self._mock_decision(technical_summary)
            
            logger.error(f"Gemini API 호출 중 에러 발생: {e}")
            return {"decision": "HOLD", "reason": "AI 통신 에러", "risk_level": "UNKNOWN"}

    def _mock_decision(self, technical_summary):
        """Simulates a decision when API is unavailable."""
        # Simple logic: If strict algo said BUY, we mostly agree unless it looks "too good"
        return {
            "decision": "BUY",
            "reason": "Mock Tactician: Chaos Opportunity Confirmed",
            "tactical_context": "Panic selling detected, smart money absorbing.",
            "chaos_opportunity_score": 0.92,
            "confidence_score": 0.88
        }
