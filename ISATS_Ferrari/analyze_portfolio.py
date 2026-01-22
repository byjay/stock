"""
📊 보유 종목 정성적 분석 실행 스크립트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

작전명: "Portfolio Deep Analysis"

역할:
- 보유 종목 15개 정성적 분석
- 공시/뉴스/리포트/딥리서치 통합
- 매수/매도/보유 판단

작성자: ISATS Neural Swarm
버전: 6.0 (Portfolio Analysis)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
import json
from datetime import datetime
import sys
import os

# 프로젝트 루트
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.qualitative_intelligence_team import QualitativeIntelligenceTeam


# ==========================================
# 보유 종목 리스트
# ==========================================

PORTFOLIO = [
    {
        "ticker": "RKLB",  # 로켓 팜
        "name": "로켓 팜",
        "current_price": 168.96,
        "avg_price": 62.12,
        "profit_loss": 35.99,
        "shares": 2,
        "technical_signal": "SELL"  # 수익 실현
    },
    {
        "ticker": "OKLO",  # 오클로
        "name": "오클로",
        "current_price": 927.20,
        "avg_price": 161.24,
        "profit_loss": -42.49,
        "shares": 10,
        "technical_signal": "SELL"  # 손절
    },
    {
        "ticker": "SILC",  # 실스크
        "name": "실스크",
        "current_price": 304.85,
        "avg_price": 7.01,
        "profit_loss": -33.18,
        "shares": 65,
        "technical_signal": "HOLD"  # 관망
    },
    {
        "ticker": "IONQ",  # 아이온큐
        "name": "아이온큐",
        "current_price": 284.98,
        "avg_price": 67.08,
        "profit_loss": -26.88,
        "shares": 5.81,
        "technical_signal": "HOLD"  # 관망
    },
    {
        "ticker": "DFLI",  # 드래곤플라이 에너지 홀딩스
        "name": "드래곤플라이 에너지 홀딩스",
        "current_price": 252.63,
        "avg_price": 13.80,
        "profit_loss": -70.95,
        "shares": 63,
        "technical_signal": "SELL"  # 손절
    },
    {
        "ticker": "CPA",  # CPI 에어로스트럭처스
        "name": "CPI 에어로스트럭처스",
        "current_price": 154.29,
        "avg_price": 3.60,
        "profit_loss": 15.79,
        "shares": 37,
        "technical_signal": "HOLD"  # 보유
    },
    {
        "ticker": "GSIT",  # GSI 테크놀로지
        "name": "GSI 테크놀로지",
        "current_price": 128.80,
        "avg_price": 11.89,
        "profit_loss": -32.31,
        "shares": 16,
        "technical_signal": "HOLD"  # 관망
    },
    {
        "ticker": "BYND",  # 비온드 미트
        "name": "비온드 미트",
        "current_price": 107.88,
        "avg_price": 2.01,
        "profit_loss": -53.90,
        "shares": 116,
        "technical_signal": "SELL"  # 손절
    },
    {
        "ticker": "GGLL",  # GGLL
        "name": "GGLL",
        "current_price": 107.49,
        "avg_price": 105.08,
        "profit_loss": 2.29,
        "shares": 1,
        "technical_signal": "HOLD"  # 보유
    },
    {
        "ticker": "INZY",  # 인텐시티 테라퓨틱스
        "name": "인텐시티 테라퓨틱스",
        "current_price": 87.19,
        "avg_price": 1.03,
        "profit_loss": -57.98,
        "shares": 201,
        "technical_signal": "SELL"  # 손절
    }
]


# ==========================================
# 분석 실행
# ==========================================

async def analyze_portfolio():
    """보유 종목 정성적 분석"""
    
    print(f"\n{'='*80}")
    print(f"📊 보유 종목 정성적 분석 시작")
    print(f"{'='*80}\n")
    
    # 정성적 분석 전담팀 생성
    qi_team = QualitativeIntelligenceTeam()
    
    results = []
    
    for i, stock in enumerate(PORTFOLIO, 1):
        print(f"\n{'='*80}")
        print(f"[{i}/{len(PORTFOLIO)}] {stock['name']} ({stock['ticker']}) 분석 중...")
        print(f"{'='*80}\n")
        
        try:
            # 정성적 분석 실행
            result = await qi_team.analyze(
                ticker=stock['ticker'],
                corp_code="00000000",  # Mock
                current_price=stock['current_price'],
                technical_signal=stock['technical_signal']
            )
            
            # 결과 저장
            result['stock_info'] = stock
            results.append(result)
            
            # 결과 출력
            print(f"\n{'='*80}")
            print(f"✅ {stock['name']} 분석 완료")
            print(f"{'='*80}")
            print(f"   추천: {result['final_recommendation']}")
            print(f"   신뢰도: {result['final_confidence']:.2f}")
            print(f"   근거: {result['reason']}")
            print(f"{'='*80}\n")
        
        except Exception as e:
            print(f"\n❌ {stock['name']} 분석 실패: {e}\n")
            results.append({
                'ticker': stock['ticker'],
                'error': str(e),
                'stock_info': stock
            })
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 최종 결과 저장
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    output_file = f"portfolio_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"📊 전체 분석 완료")
    print(f"{'='*80}")
    print(f"   분석 종목 수: {len(PORTFOLIO)}개")
    print(f"   결과 파일: {output_file}")
    print(f"{'='*80}\n")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 요약 리포트
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    buy_count = sum(1 for r in results if r.get('final_recommendation') == 'BUY')
    sell_count = sum(1 for r in results if r.get('final_recommendation') == 'SELL')
    hold_count = sum(1 for r in results if r.get('final_recommendation') == 'HOLD')
    
    print(f"\n{'='*80}")
    print(f"📈 요약 리포트")
    print(f"{'='*80}")
    print(f"   매수 권장: {buy_count}개")
    print(f"   매도 권장: {sell_count}개")
    print(f"   보유 권장: {hold_count}개")
    print(f"{'='*80}\n")
    
    # 매도 권장 종목 리스트
    if sell_count > 0:
        print(f"\n{'='*80}")
        print(f"🔴 매도 권장 종목")
        print(f"{'='*80}")
        
        for r in results:
            if r.get('final_recommendation') == 'SELL':
                stock = r['stock_info']
                print(f"   - {stock['name']} ({stock['ticker']})")
                print(f"     손익: {stock['profit_loss']:.2f}%")
                print(f"     신뢰도: {r.get('final_confidence', 0):.2f}")
                print(f"     근거: {r.get('reason', 'N/A')[:100]}...")
                print()
        
        print(f"{'='*80}\n")
    
    return results


# ==========================================
# 실행
# ==========================================

if __name__ == "__main__":
    asyncio.run(analyze_portfolio())
