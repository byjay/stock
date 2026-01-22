"""
🎯 AUTO MARKET SCANNER v2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

대규모 자동 사냥 시스템 (Auto Hunting System)

기능:
1. 2,000개 종목 자동 스캔 (data/KR/*.csv, data/US/*.csv)
2. Deep Insight Scanner v2.0 통합 (로컬 CSV 직접 분석)
3. 종합 점수 7점 이상 종목만 필터링
4. daily_target_list.csv 자동 생성
5. ISATS 메인 파이프라인 연결

작성자: ISATS Neural Swarm
버전: 2.0 (Optimized)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import pandas as pd
import numpy as np
import glob
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# Deep Insight Scanner 임포트
sys.path.append(str(Path(__file__).parent.parent.parent))
try:
    from deep_insight_v2 import DeepInsightV2
except ImportError:
    # 경로 문제시 현재 폴더에서 찾기 시도
    sys.path.append(os.path.dirname(__file__))
    from deep_insight_v2 import DeepInsightV2

class AutoScanner:
    """대규모 자동 시장 스캐너 (최적화 버전)"""
    
    def __init__(self, data_dir: str = "data", min_score: int = 8):
        """
        Args:
            data_dir: 데이터 디렉토리 경로 (기본값: "data")
            min_score: 최소 점수 (기본값: 7점)
        """
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / data_dir
        self.output_file = self.project_root / "daily_target_list.csv"
        self.min_score = min_score
        
        # Deep Insight Scanner 초기화
        self.engine = DeepInsightV2()
        
        print(f"\n{'='*80}")
        print(f"🎯 AUTO MARKET SCANNER v2.0 (Optimized)")
        print(f"{'='*80}")
        print(f"📂 데이터 디렉토리: {self.data_dir}")
        print(f"🎯 최소 점수 기준: {min_score}점 이상")
        print(f"{'='*80}\n")
    
    def load_file_list(self) -> List[str]:
        """분석할 데이터 파일 목록 로드"""
        files = []
        
        # KR 시장
        kr_files = glob.glob(str(self.data_dir / "KR" / "*.csv"))
        files.extend(kr_files)
        print(f"✅ KR 시장: {len(kr_files)}개 파일 발견")
        
        # US 시장
        us_files = glob.glob(str(self.data_dir / "US" / "*.csv"))
        files.extend(us_files)
        print(f"✅ US 시장: {len(us_files)}개 파일 발견")
        
        print(f"📂 [Scanner] 총 분석 대상: {len(files)}개 파일\n")
        return files
    
    def run_scan(self) -> List[Dict]:
        """전체 스캔 실행"""
        files = self.load_file_list()
        
        if not files:
            print("❌ 데이터 파일이 없습니다. 데이터 수집기(Miner)를 먼저 실행하십시오.")
            return []
        
        targets = []
        
        print(f"\n{'='*80}")
        print(f"🚀 [Mission Start] 전 종목 정밀 타격 스캔 시작...")
        print(f"{'='*80}")
        print(f"   기준: 종합 점수 {self.min_score}점 이상")
        print(f"   대상: {len(files)}개 종목")
        print(f"{'='*80}\n")
        
        # 진행바 표시
        for filepath in tqdm(files, desc="🔍 Scanning", unit="stock"):
            try:
                # 1. 데이터 로드 (CSV 직접 읽기 - 속도 최적화)
                df = pd.read_csv(filepath)
                
                # 데이터 부족 스킵
                if len(df) < 60:
                    continue
                
                # 날짜 인덱스 처리
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                
                # 티커명 추출 (파일명)
                ticker = os.path.basename(filepath).replace('.csv', '')
                
                # 시장 구분 (KR/US)
                if 'KR' in filepath:
                    market = 'KR'
                else:
                    market = 'US'
                
                # 2. Deep Insight 분석 수행
                # 기술적 지표 계산
                rsi = self.engine.tech_analyzer.calculate_rsi(df)
                macd, signal, hist = self.engine.tech_analyzer.calculate_macd(df)
                upper, middle, lower = self.engine.tech_analyzer.calculate_bollinger_bands(df)
                trend_info = self.engine.tech_analyzer.detect_trend(df)
                
                # 수급 분석
                vol_profile = self.engine.vol_analyzer.analyze_volume_profile(df)
                accumulation = self.engine.vol_analyzer.detect_accumulation(df)
                
                # 분석 딕셔너리 구성
                analysis = {
                    'technical': {
                        'rsi': rsi,
                        'macd': {'macd': macd, 'signal': signal, 'hist': hist},
                        'bollinger': {'upper': upper, 'middle': middle, 'lower': lower},
                        'trend': trend_info
                    },
                    'volume': {
                        'strength_ratio': vol_profile['strength_ratio'],
                        'volume_ratio': vol_profile['volume_ratio'],
                        'accumulation': accumulation
                    }
                }
                
                # 점수 계산
                score, reasons = self.engine.calculate_score(analysis)
                
                # 3. 타겟 필터링 (min_score 이상)
                if score >= self.min_score:
                    current_price = df.iloc[-1]['Close']
                    prev_close = df.iloc[-2]['Close']
                    change_pct = (current_price - prev_close) / prev_close * 100
                    
                    # 추천 등급
                    if score >= 8:
                        recommendation = "STRONG BUY"
                    elif score >= 6:
                        recommendation = "BUY"
                    else:
                        recommendation = "HOLD"
                    
                    targets.append({
                        'ticker': ticker,
                        'market': market,
                        'score': score,
                        'recommendation': recommendation,
                        'current_price': current_price,
                        'change_pct': change_pct,
                        'rsi': rsi,
                        'macd_hist': hist,
                        'trend': trend_info['trend'],
                        'strength_ratio': vol_profile['strength_ratio'],
                        'volume_ratio': vol_profile['volume_ratio'],
                        'accumulation_signal': accumulation['signal'],
                        'reasons': ' | '.join(reasons),
                        'scan_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
            except Exception as e:
                # 에러난 파일은 스킵하고 계속 진행
                continue
        
        # 결과 저장
        self.save_targets(targets)
        return targets
    
    def save_targets(self, targets: List[Dict]):
        """타겟 리스트 저장"""
        if not targets:
            print(f"\n{'='*80}")
            print("⚠️ [Result] 조건에 맞는 종목이 하나도 없습니다.")
            print(f"{'='*80}")
            print(f"   💡 TIP: 최소 점수를 낮추거나 (현재: {self.min_score}점)")
            print(f"           데이터 수집 기간을 늘려보십시오.")
            print(f"{'='*80}\n")
            return
        
        # DataFrame 생성 및 정렬
        df = pd.DataFrame(targets)
        df = df.sort_values(by='score', ascending=False)
        
        # CSV 저장
        df.to_csv(self.output_file, index=False, encoding='utf-8-sig')
        
        print(f"\n{'='*80}")
        print(f"🎉 [Scan Complete] 유망 종목 {len(targets)}개 발굴 완료!")
        print(f"{'='*80}")
        print(f"   💾 타겟 리스트 저장: {self.output_file}")
        print(f"   📊 선정 비율: {len(targets)} / {len(self.load_file_list())} "
              f"({len(targets)/len(self.load_file_list())*100:.1f}%)")
        print(f"{'='*80}\n")
        
        # Top 10 출력
        print(f"{'─'*80}")
        print("🏆 TOP 10 TARGETS")
        print(f"{'─'*80}\n")
        
        for i, row in df.head(10).iterrows():
            print(f"{i+1:2d}. [{row['market']}] {row['ticker']:12s} | "
                  f"점수: {row['score']:2.0f}/10 | "
                  f"추천: {row['recommendation']:12s} | "
                  f"현재가: {row['current_price']:,.2f} ({row['change_pct']:+.2f}%)")
        
        print(f"\n{'─'*80}\n")


def main():
    """메인 실행 함수"""
    # 스캐너 초기화 (최소 점수 8점 - 상위 2.5%)
    scanner = AutoScanner(min_score=8)
    
    # 실행
    targets = scanner.run_scan()
    
    if targets:
        print(f"\n💡 다음 단계:")
        print(f"   1. daily_target_list.csv 파일을 확인하세요.")
        print(f"   2. ISATS 메인 매매 엔진(main.py)을 실행하세요.")
        print(f"   3. 엔진이 자동으로 이 리스트를 로드하여 집중 감시합니다.\n")


if __name__ == "__main__":
    main()
