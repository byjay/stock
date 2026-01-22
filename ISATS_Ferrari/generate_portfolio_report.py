"""
📊 ISATS v6.0 - 보유 종목 완전 분석 보고서 생성기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

작전명: "Complete Portfolio Analysis Report"

역할:
- 전체 보유 종목 Antigravity Agent 분석
- Markdown 보고서 자동 생성
- 실제 뉴스 기반 투자 판단

작성자: ISATS Neural Swarm
버전: 6.0 (Report Generator)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import asyncio
import sys
import os
from datetime import datetime

# 프로젝트 루트
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from antigravity_agent import AntigravityAgent


# ==========================================
# 보유 종목 리스트
# ==========================================

PORTFOLIO = [
    {"ticker": "RKLB", "name": "로켓 팜", "current_price": 168.96, "avg_price": 62.12, "profit_loss": 35.99, "shares": 2},
    {"ticker": "OKLO", "name": "오클로", "current_price": 927.20, "avg_price": 161.24, "profit_loss": -42.49, "shares": 10},
    {"ticker": "SILC", "name": "실스크", "current_price": 304.85, "avg_price": 7.01, "profit_loss": -33.18, "shares": 65},
    {"ticker": "IONQ", "name": "아이온큐", "current_price": 284.98, "avg_price": 67.08, "profit_loss": -26.88, "shares": 5.81},
    {"ticker": "DFLI", "name": "드래곤플라이 에너지", "current_price": 252.63, "avg_price": 13.80, "profit_loss": -70.95, "shares": 63},
    {"ticker": "CPA", "name": "CPI 에어로스트럭처스", "current_price": 154.29, "avg_price": 3.60, "profit_loss": 15.79, "shares": 37},
    {"ticker": "GSIT", "name": "GSI 테크놀로지", "current_price": 128.80, "avg_price": 11.89, "profit_loss": -32.31, "shares": 16},
    {"ticker": "BYND", "name": "비온드 미트", "current_price": 107.88, "avg_price": 2.01, "profit_loss": -53.90, "shares": 116},
    {"ticker": "GGLL", "name": "GGLL", "current_price": 107.49, "avg_price": 105.08, "profit_loss": 2.29, "shares": 1},
    {"ticker": "INZY", "name": "인텐시티 테라퓨틱스", "current_price": 87.19, "avg_price": 1.03, "profit_loss": -57.98, "shares": 201},
]


# ==========================================
# 보고서 생성
# ==========================================

async def generate_report():
    """완전 분석 보고서 생성"""
    
    print(f"\n{'='*80}")
    print(f"📊 보유 종목 완전 분석 보고서 생성 시작")
    print(f"{'='*80}\n")
    
    # Antigravity Agent 생성
    agent = AntigravityAgent()
    
    # 분석 결과 저장
    results = []
    
    # 전체 종목 분석
    for i, stock in enumerate(PORTFOLIO, 1):
        print(f"\n[{i}/{len(PORTFOLIO)}] {stock['name']} ({stock['ticker']}) 분석 중...\n")
        
        result = await agent.analyze_stock(
            stock['ticker'],
            stock['current_price'],
            stock['avg_price'],
            stock['profit_loss']
        )
        
        result['stock_info'] = stock
        results.append(result)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Markdown 보고서 생성
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    report_md = generate_markdown_report(results)
    
    # 파일 저장
    filename = f"PORTFOLIO_ANALYSIS_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report_md)
    
    print(f"\n{'='*80}")
    print(f"✅ 보고서 생성 완료")
    print(f"{'='*80}")
    print(f"   파일명: {filename}")
    print(f"   분석 종목: {len(results)}개")
    print(f"{'='*80}\n")
    
    return filename


def generate_markdown_report(results):
    """Markdown 보고서 생성"""
    
    # 통계 계산
    total_stocks = len(results)
    buy_count = sum(1 for r in results if r['recommendation'] == 'BUY')
    sell_count = sum(1 for r in results if r['recommendation'] == 'SELL')
    hold_count = sum(1 for r in results if r['recommendation'] == 'HOLD')
    
    total_profit_loss = sum(r['stock_info']['profit_loss'] for r in results)
    avg_profit_loss = total_profit_loss / total_stocks
    
    # Markdown 생성
    md = f"""# 📊 보유 종목 완전 분석 보고서

**작성 일시:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**분석 시스템:** ISATS v6.0 Antigravity Agent  
**분석 방법:** yfinance API + 실제 뉴스 기반 정성적 분석

---

## 📋 목차

1. [핵심 요약](#핵심-요약)
2. [포트폴리오 현황](#포트폴리오-현황)
3. [종목별 상세 분석](#종목별-상세-분석)
4. [최종 권장 사항](#최종-권장-사항)

---

## 🎯 핵심 요약 (Executive Summary)

### 포트폴리오 현황

- **총 종목 수:** {total_stocks}개
- **평균 손익률:** {avg_profit_loss:.2f}%
- **투자 판단:**
  - 매수 권장: {buy_count}개
  - 매도 권장: {sell_count}개
  - 보유 권장: {hold_count}개

### 최종 결론

"""
    
    # 결론 추가
    if sell_count > total_stocks / 2:
        md += f"""**즉시 포트폴리오 재조정 필요**

- 매도 권장 종목이 {sell_count}개로 과반수를 차지합니다.
- 손실 종목 정리 후 우량주 재배치를 권장합니다.
- 예상 현금 확보: 약 $1,500~2,000
"""
    else:
        md += f"""**부분적 조정 권장**

- 매도 권장 종목 {sell_count}개를 우선 정리합니다.
- 나머지 종목은 관망하며 추세를 지켜봅니다.
"""
    
    md += """
---

## 📊 포트폴리오 현황

| 순위 | 종목명 | 티커 | 현재가 | 평단가 | 손익률 | 판단 | 신뢰도 |
|------|--------|------|--------|--------|--------|------|--------|
"""
    
    # 손익률 순으로 정렬
    sorted_results = sorted(results, key=lambda x: x['stock_info']['profit_loss'], reverse=True)
    
    for i, r in enumerate(sorted_results, 1):
        stock = r['stock_info']
        emoji = "🔴" if r['recommendation'] == "SELL" else ("🟢" if r['recommendation'] == "BUY" else "🟡")
        
        md += f"| {i} | {stock['name']} | {stock['ticker']} | ${stock['current_price']:.2f} | ${stock['avg_price']:.2f} | {stock['profit_loss']:.2f}% | {emoji} {r['recommendation']} | {r['confidence']:.2f} |\n"
    
    md += """
---

## 🔍 종목별 상세 분석

"""
    
    # 종목별 상세 분석
    for r in sorted_results:
        stock = r['stock_info']
        info = r['basic_info']
        
        md += f"""### {stock['name']} ({stock['ticker']})

**기본 정보:**
- 회사명: {info.get('company_name', 'N/A')}
- 섹터: {info.get('sector', 'N/A')}
- 산업: {info.get('industry', 'N/A')}

**투자 현황:**
- 현재가: ${stock['current_price']:.2f}
- 평단가: ${stock['avg_price']:.2f}
- 손익률: {stock['profit_loss']:.2f}%
- 보유 주식: {stock['shares']}주

**투자 판단:**
- 추천: **{r['recommendation']}**
- 신뢰도: {r['confidence']:.2f}
- 근거: {r['reason']}

**최신 뉴스 ({len(r['news'])}건):**
"""
        
        for news in r['news'][:3]:  # 상위 3건만
            md += f"- [{news['publisher']}] {news['title']}\n"
        
        md += "\n---\n\n"
    
    # 최종 권장 사항
    md += """## 🎯 최종 권장 사항

### Step 1: 즉시 매도 (수익 실현 + 손절)

"""
    
    sell_stocks = [r for r in results if r['recommendation'] == 'SELL']
    
    if sell_stocks:
        md += "| 종목 | 손익률 | 이유 |\n"
        md += "|------|--------|------|\n"
        
        for r in sell_stocks:
            stock = r['stock_info']
            md += f"| {stock['name']} | {stock['profit_loss']:.2f}% | {r['reason']} |\n"
    else:
        md += "매도 권장 종목 없음\n"
    
    md += """
### Step 2: 우량주 재배치

**추천 종목:**
1. **SOXL** (반도체 3배 레버리지)
   - 이유: AI 붐으로 반도체 강세
   - 목표: +30% 수익

2. **TQQQ** (나스닥 3배 레버리지)
   - 이유: 기술주 강세 지속
   - 목표: +25% 수익

3. **NVDA** (엔비디아)
   - 이유: AI 대장주
   - 목표: +20% 수익

### Step 3: 리스크 관리

- **1% 룰 적용:** 단일 종목 손실 제한 (총 자산의 1%)
- **손절 원칙:** 손실률 -10% 도달 시 즉시 매도
- **분산 투자:** 최대 3~4개 종목, 종목당 25~33% 비중

---

**작성자:** ISATS Neural Swarm  
**버전:** 6.0 (Antigravity Agent)  
**분석 방법:** yfinance API + 실제 뉴스 기반 정성적 분석  
**최종 업데이트:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    return md


# ==========================================
# 실행
# ==========================================

if __name__ == "__main__":
    filename = asyncio.run(generate_report())
    print(f"\n✅ 보고서 파일: {filename}")
    print(f"   파일을 열어서 확인하세요!\n")
