"""
🔍 ISATS v6.0 - Qualitative Intelligence Team
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

작전명: "정성적 분석 전담팀 (Qualitative Intelligence Team)"

역할:
- 공시 분석 (DART API)
- 뉴스 분석 (네이버 뉴스 크롤링)
- 증권사 리포트 분석 (PDF 파싱)
- 구글 딥리서치 (Google Gemini)
- 최종 신뢰도 점수 산출 (0~1)

작성자: ISATS Neural Swarm
버전: 6.0 (Qualitative Intelligence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 프로젝트 루트 경로
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 선택적 임포트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    print("⚠️ [Warning] BeautifulSoup4 not found. Installing...")
    os.system("pip install beautifulsoup4 --quiet")
    from bs4 import BeautifulSoup
    HAS_BS4 = True

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    print("⚠️ [Warning] Google Generative AI not found. Installing...")
    os.system("pip install google-generativeai --quiet")
    import google.generativeai as genai
    HAS_GEMINI = True


# ==========================================
# 🔍 1. 공시 분석 에이전트 (DART API)
# ==========================================

class DARTAnalyzer:
    """전자공시 분석 에이전트"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DART_API_KEY", "YOUR_DART_API_KEY")
        self.base_url = "https://opendart.fss.or.kr/api"
    
    async def get_recent_disclosures(self, corp_code: str, days: int = 7) -> List[Dict]:
        """
        최근 공시 조회
        
        Args:
            corp_code: 기업 고유번호
            days: 조회 기간 (일)
        
        Returns:
            List[Dict]: 공시 리스트
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f"{self.base_url}/list.json"
        params = {
            "crtfc_key": self.api_key,
            "corp_code": corp_code,
            "bgn_de": start_date.strftime("%Y%m%d"),
            "end_de": end_date.strftime("%Y%m%d"),
            "page_count": 100
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get("status") == "000":
                return data.get("list", [])
            else:
                return []
        
        except Exception as e:
            print(f"❌ DART API 오류: {e}")
            return []
    
    def analyze_disclosure_sentiment(self, disclosures: List[Dict]) -> float:
        """
        공시 감성 분석
        
        Args:
            disclosures: 공시 리스트
        
        Returns:
            float: 감성 점수 (-1 ~ 1)
        """
        if not disclosures:
            return 0.0
        
        # 긍정 키워드
        positive_keywords = [
            "증자", "배당", "실적개선", "흑자전환", "수주", "계약체결",
            "신제품", "특허", "인증", "수출", "투자유치"
        ]
        
        # 부정 키워드
        negative_keywords = [
            "감자", "적자", "횡령", "배임", "소송", "과징금",
            "영업정지", "파산", "회생", "구조조정", "감사의견"
        ]
        
        score = 0
        
        for disclosure in disclosures:
            title = disclosure.get("report_nm", "")
            
            # 긍정 키워드 체크
            for keyword in positive_keywords:
                if keyword in title:
                    score += 1
            
            # 부정 키워드 체크
            for keyword in negative_keywords:
                if keyword in title:
                    score -= 1
        
        # 정규화 (-1 ~ 1)
        max_score = len(disclosures) * 2
        normalized_score = max(-1, min(1, score / max(1, max_score)))
        
        return normalized_score


# ==========================================
# 📰 2. 뉴스 분석 에이전트
# ==========================================

class NewsAnalyzer:
    """뉴스 분석 에이전트"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    async def get_naver_news(self, keyword: str, count: int = 10) -> List[Dict]:
        """
        네이버 뉴스 검색
        
        Args:
            keyword: 검색 키워드 (종목명)
            count: 뉴스 개수
        
        Returns:
            List[Dict]: 뉴스 리스트
        """
        url = "https://search.naver.com/search.naver"
        params = {
            "where": "news",
            "query": keyword,
            "sort": 0,  # 최신순
            "start": 1
        }
        
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            news_list = []
            news_items = soup.select(".news_area")[:count]
            
            for item in news_items:
                title_elem = item.select_one(".news_tit")
                desc_elem = item.select_one(".news_dsc")
                
                if title_elem:
                    news_list.append({
                        "title": title_elem.get_text(strip=True),
                        "description": desc_elem.get_text(strip=True) if desc_elem else "",
                        "link": title_elem.get("href", "")
                    })
            
            return news_list
        
        except Exception as e:
            print(f"❌ 뉴스 크롤링 오류: {e}")
            return []
    
    def analyze_news_sentiment(self, news_list: List[Dict]) -> float:
        """
        뉴스 감성 분석
        
        Args:
            news_list: 뉴스 리스트
        
        Returns:
            float: 감성 점수 (-1 ~ 1)
        """
        if not news_list:
            return 0.0
        
        # 긍정 키워드
        positive_keywords = [
            "상승", "급등", "호재", "성장", "실적개선", "흑자",
            "신고가", "돌파", "강세", "매수", "투자", "확대"
        ]
        
        # 부정 키워드
        negative_keywords = [
            "하락", "급락", "악재", "감소", "적자", "부진",
            "신저가", "약세", "매도", "축소", "위험", "우려"
        ]
        
        score = 0
        
        for news in news_list:
            text = news.get("title", "") + " " + news.get("description", "")
            
            # 긍정 키워드 체크
            for keyword in positive_keywords:
                if keyword in text:
                    score += 1
            
            # 부정 키워드 체크
            for keyword in negative_keywords:
                if keyword in text:
                    score -= 1
        
        # 정규화 (-1 ~ 1)
        max_score = len(news_list) * 2
        normalized_score = max(-1, min(1, score / max(1, max_score)))
        
        return normalized_score


# ==========================================
# 📊 3. 증권사 리포트 분석 에이전트
# ==========================================

class BrokerageReportAnalyzer:
    """증권사 리포트 분석 에이전트"""
    
    def __init__(self):
        pass
    
    async def get_reports(self, ticker: str) -> List[Dict]:
        """
        증권사 리포트 조회 (Mock)
        
        Args:
            ticker: 종목 코드
        
        Returns:
            List[Dict]: 리포트 리스트
        """
        # 실제 구현 시 증권사 API 또는 크롤링 필요
        # 현재는 Mock 데이터 반환
        
        return [
            {
                "brokerage": "삼성증권",
                "analyst": "김철수",
                "target_price": 85000,
                "opinion": "BUY",
                "date": "2026-01-20"
            },
            {
                "brokerage": "NH투자증권",
                "analyst": "이영희",
                "target_price": 80000,
                "opinion": "HOLD",
                "date": "2026-01-18"
            }
        ]
    
    def analyze_reports(self, reports: List[Dict], current_price: float) -> float:
        """
        리포트 분석
        
        Args:
            reports: 리포트 리스트
            current_price: 현재가
        
        Returns:
            float: 신뢰도 점수 (0 ~ 1)
        """
        if not reports:
            return 0.5  # 중립
        
        buy_count = 0
        hold_count = 0
        sell_count = 0
        avg_target_price = 0
        
        for report in reports:
            opinion = report.get("opinion", "").upper()
            target_price = report.get("target_price", 0)
            
            if opinion == "BUY" or opinion == "매수":
                buy_count += 1
            elif opinion == "HOLD" or opinion == "보유":
                hold_count += 1
            elif opinion == "SELL" or opinion == "매도":
                sell_count += 1
            
            avg_target_price += target_price
        
        # 평균 목표가
        avg_target_price /= len(reports)
        
        # 상승 여력
        upside = (avg_target_price - current_price) / current_price
        
        # 의견 점수
        opinion_score = (buy_count - sell_count) / len(reports)
        
        # 최종 점수 (0 ~ 1)
        final_score = (opinion_score + 1) / 2 * 0.6 + min(1, max(0, upside)) * 0.4
        
        return max(0, min(1, final_score))


# ==========================================
# 🧠 4. 구글 딥리서치 에이전트 (Gemini)
# ==========================================

class DeepResearchAgent:
    """구글 Gemini 기반 딥리서치 에이전트"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
        
        if HAS_GEMINI and self.api_key != "YOUR_GEMINI_API_KEY":
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
    
    async def analyze_comprehensive(
        self,
        ticker: str,
        disclosures: List[Dict],
        news: List[Dict],
        reports: List[Dict],
        technical_signal: str
    ) -> Dict:
        """
        종합 분석
        
        Args:
            ticker: 종목 코드
            disclosures: 공시 리스트
            news: 뉴스 리스트
            reports: 리포트 리스트
            technical_signal: 기술적 신호 (BUY/SELL/HOLD)
        
        Returns:
            Dict: 분석 결과
        """
        if not self.model:
            return {
                "recommendation": technical_signal,
                "confidence": 0.5,
                "reason": "Gemini API 미설정"
            }
        
        # 프롬프트 생성
        prompt = self._create_prompt(ticker, disclosures, news, reports, technical_signal)
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)
            return result
        
        except Exception as e:
            print(f"❌ Gemini API 오류: {e}")
            return {
                "recommendation": technical_signal,
                "confidence": 0.5,
                "reason": f"API 오류: {e}"
            }
    
    def _create_prompt(
        self,
        ticker: str,
        disclosures: List[Dict],
        news: List[Dict],
        reports: List[Dict],
        technical_signal: str
    ) -> str:
        """프롬프트 생성"""
        
        prompt = f"""
당신은 전문 주식 애널리스트입니다. 다음 정보를 종합적으로 분석하여 투자 의견을 제시하세요.

**종목:** {ticker}
**기술적 신호:** {technical_signal}

**최근 공시 ({len(disclosures)}건):**
{self._format_disclosures(disclosures)}

**최근 뉴스 ({len(news)}건):**
{self._format_news(news)}

**증권사 리포트 ({len(reports)}건):**
{self._format_reports(reports)}

**분석 요청:**
1. 위 정보를 종합하여 투자 의견(BUY/SELL/HOLD)을 제시하세요.
2. 신뢰도(0~1)를 숫자로 제시하세요.
3. 핵심 근거를 3줄 이내로 요약하세요.

**응답 형식 (JSON):**
{{
  "recommendation": "BUY/SELL/HOLD",
  "confidence": 0.0~1.0,
  "reason": "핵심 근거"
}}
"""
        return prompt
    
    def _format_disclosures(self, disclosures: List[Dict]) -> str:
        """공시 포맷팅"""
        if not disclosures:
            return "없음"
        
        lines = []
        for d in disclosures[:5]:  # 최근 5건만
            lines.append(f"- {d.get('report_nm', 'N/A')}")
        
        return "\n".join(lines)
    
    def _format_news(self, news: List[Dict]) -> str:
        """뉴스 포맷팅"""
        if not news:
            return "없음"
        
        lines = []
        for n in news[:5]:  # 최근 5건만
            lines.append(f"- {n.get('title', 'N/A')}")
        
        return "\n".join(lines)
    
    def _format_reports(self, reports: List[Dict]) -> str:
        """리포트 포맷팅"""
        if not reports:
            return "없음"
        
        lines = []
        for r in reports:
            lines.append(f"- {r.get('brokerage', 'N/A')}: {r.get('opinion', 'N/A')} (목표가: {r.get('target_price', 0):,}원)")
        
        return "\n".join(lines)
    
    def _parse_response(self, response_text: str) -> Dict:
        """응답 파싱"""
        try:
            # JSON 추출 시도
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            
            if start != -1 and end > start:
                json_str = response_text[start:end]
                result = json.loads(json_str)
                return result
            else:
                # JSON 형식이 아닌 경우
                return {
                    "recommendation": "HOLD",
                    "confidence": 0.5,
                    "reason": response_text[:200]
                }
        
        except Exception as e:
            return {
                "recommendation": "HOLD",
                "confidence": 0.5,
                "reason": f"파싱 오류: {e}"
            }


# ==========================================
# 🎯 5. 통합 분석 매니저
# ==========================================

class QualitativeIntelligenceTeam:
    """정성적 분석 전담팀"""
    
    def __init__(
        self,
        dart_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None
    ):
        self.dart_analyzer = DARTAnalyzer(dart_api_key)
        self.news_analyzer = NewsAnalyzer()
        self.report_analyzer = BrokerageReportAnalyzer()
        self.deep_research = DeepResearchAgent(gemini_api_key)
    
    async def analyze(
        self,
        ticker: str,
        corp_code: str,
        current_price: float,
        technical_signal: str
    ) -> Dict:
        """
        종합 정성적 분석
        
        Args:
            ticker: 종목 코드
            corp_code: 기업 고유번호 (DART)
            current_price: 현재가
            technical_signal: 기술적 신호 (BUY/SELL/HOLD)
        
        Returns:
            Dict: 분석 결과
        """
        print(f"\n{'='*80}")
        print(f"🔍 정성적 분석 시작: {ticker}")
        print(f"{'='*80}\n")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. 공시 분석
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print("📋 [1/4] 공시 분석 중...")
        disclosures = await self.dart_analyzer.get_recent_disclosures(corp_code)
        disclosure_sentiment = self.dart_analyzer.analyze_disclosure_sentiment(disclosures)
        print(f"   ✅ 공시 {len(disclosures)}건 분석 완료 (감성: {disclosure_sentiment:.2f})")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. 뉴스 분석
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print("📰 [2/4] 뉴스 분석 중...")
        news = await self.news_analyzer.get_naver_news(ticker)
        news_sentiment = self.news_analyzer.analyze_news_sentiment(news)
        print(f"   ✅ 뉴스 {len(news)}건 분석 완료 (감성: {news_sentiment:.2f})")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. 증권사 리포트 분석
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print("📊 [3/4] 증권사 리포트 분석 중...")
        reports = await self.report_analyzer.get_reports(ticker)
        report_score = self.report_analyzer.analyze_reports(reports, current_price)
        print(f"   ✅ 리포트 {len(reports)}건 분석 완료 (점수: {report_score:.2f})")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4. 구글 딥리서치 (종합 분석)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print("🧠 [4/4] 구글 딥리서치 중...")
        deep_analysis = await self.deep_research.analyze_comprehensive(
            ticker, disclosures, news, reports, technical_signal
        )
        print(f"   ✅ 딥리서치 완료 (신뢰도: {deep_analysis.get('confidence', 0):.2f})")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 최종 결과
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        result = {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "technical_signal": technical_signal,
            "qualitative_analysis": {
                "disclosure_sentiment": disclosure_sentiment,
                "news_sentiment": news_sentiment,
                "report_score": report_score,
                "deep_research": deep_analysis
            },
            "final_recommendation": deep_analysis.get("recommendation", technical_signal),
            "final_confidence": deep_analysis.get("confidence", 0.5),
            "reason": deep_analysis.get("reason", "분석 완료")
        }
        
        print(f"\n{'='*80}")
        print(f"🎯 최종 결과")
        print(f"{'='*80}")
        print(f"   추천: {result['final_recommendation']}")
        print(f"   신뢰도: {result['final_confidence']:.2f}")
        print(f"   근거: {result['reason']}")
        print(f"{'='*80}\n")
        
        return result


# ==========================================
# 실행
# ==========================================

if __name__ == "__main__":
    async def main():
        # 정성적 분석 전담팀 생성
        team = QualitativeIntelligenceTeam()
        
        # 테스트: 삼성전자 분석
        result = await team.analyze(
            ticker="005930",
            corp_code="00126380",  # 삼성전자 고유번호
            current_price=72000,
            technical_signal="BUY"
        )
        
        # 결과 저장
        output_path = "qualitative_analysis_result.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        
        print(f"✅ 결과 저장: {output_path}")
    
    asyncio.run(main())
