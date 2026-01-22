"""
🧬 ISATS v6.0 "CONTEXT AWARE" TRAINER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

맥락 인식 훈련 시스템 (Context-Aware Training System)

기능:
1. 종목 + 섹터 + 고무줄 분봉 통합 분석
2. "섹터가 상승세일 때만 매수"의 유효성 검증
3. 1,000명의 에이전트 진화 훈련
4. 최적 전략 압축 (master_context_bot.py)

작성자: ISATS Neural Swarm
버전: 6.0 (Context Aware)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import pandas as pd
import numpy as np
import random
import os
import json
import glob
from pathlib import Path
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# 🧬 CONTEXT DNA (맥락 인식 유전자)
# ==========================================

class ContextDNA:
    """맥락 인식 전략 DNA"""
    
    def __init__(self):
        # 1. 고무줄 분봉 (Elastic Timeframe)
        self.timeframe = random.choice(['3T', '5T', '7T', '13T', '30T', '60T'])
        
        # 2. 기술적 지표
        self.ma_short = random.randint(3, 10)
        self.ma_long = random.randint(20, 60)
        
        # 3. [핵심] 섹터 동조화 계수 (Sector Synchronization)
        # True면 섹터가 상승세일 때만 매수, False면 개별 종목만 봄
        self.use_sector_filter = random.choice([True, False])
        
        # 4. 자금 관리
        self.take_profit = round(random.uniform(0.02, 0.20), 3)
        self.stop_loss = round(random.uniform(0.01, 0.10), 3)
    
    def mutate(self):
        """변이 (Mutation)"""
        if random.random() < 0.2:
            self.timeframe = random.choice(['7T', '13T', '23T'])
        if random.random() < 0.2:
            self.use_sector_filter = not self.use_sector_filter
        if random.random() < 0.1:
            self.take_profit = round(random.uniform(0.02, 0.20), 3)
        if random.random() < 0.1:
            self.stop_loss = round(random.uniform(0.01, 0.10), 3)


# ==========================================
# 📊 SECTOR MANAGER (섹터 관리자)
# ==========================================

class SectorManager:
    """가상의 섹터 지수 생성기"""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.files = list(self.data_dir.glob("*.csv"))
        print(f"📂 [SectorManager] {len(self.files)}개 파일 발견")
    
    def get_sector_index(self, target_file):
        """
        타겟 종목을 제외한 나머지 종목들의 평균 등락률을 '섹터 지수'로 정의
        
        실전에서는:
        - 반도체면 반도체 종목만 추려서 평균
        - 2차전지면 2차전지 종목만 추려서 평균
        
        여기서는 간소화를 위해 랜덤하게 5개 종목을 뽑아 섹터라고 가정
        """
        # 랜덤하게 5개 종목을 뽑아 섹터라고 가정
        peers = random.sample(self.files, min(len(self.files), 5))
        sector_df = pd.DataFrame()
        
        for p in peers:
            if p == target_file:
                continue
            
            try:
                df = pd.read_csv(p)
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                    df.set_index('Date', inplace=True)
                
                # 종가만 가져와서 병합
                if sector_df.empty:
                    sector_df = df[['Close']].rename(columns={'Close': 'Peer1'})
                else:
                    # 인덱스 기준으로 병합 (날짜 매칭)
                    temp = df[['Close']]
                    sector_df = sector_df.join(temp, rsuffix=f'_{len(sector_df.columns)}', how='inner')
            except:
                pass
        
        # 평균값 계산 (섹터 지수)
        if not sector_df.empty:
            sector_df['Sector_Index'] = sector_df.mean(axis=1)
            return sector_df['Sector_Index']
        
        return None


# ==========================================
# 🏋️ CONTEXT TRAINER (맥락 훈련기)
# ==========================================

class ContextTrainer:
    """맥락 인식 훈련 시스템"""
    
    def __init__(self, data_dir="data/KR", population=500, generations=3):
        """
        Args:
            data_dir: 데이터 디렉토리
            population: 에이전트 수
            generations: 진화 세대 수
        """
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / data_dir
        self.sector_mgr = SectorManager(self.data_dir)
        self.population = population
        self.generations = generations
        self.agents = []
        
        print(f"\n{'='*80}")
        print(f"🧬 CONTEXT AWARE TRAINER v6.0")
        print(f"{'='*80}")
        print(f"📂 데이터 디렉토리: {self.data_dir}")
        print(f"👥 에이전트 수: {population}명")
        print(f"🔄 진화 세대: {generations}세대")
        print(f"{'='*80}\n")
    
    def load_data(self, filepath):
        """데이터 로드"""
        df = pd.read_csv(filepath)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        return df
    
    def run_simulation(self):
        """전체 시뮬레이션 실행"""
        # 1. 타겟 데이터 선정
        files = list(self.data_dir.glob("*.csv"))
        if not files:
            print("❌ 데이터가 없습니다.")
            return
        
        target_file = files[0]  # 예시로 첫 번째 파일 사용
        print(f"🎯 타겟 종목: {target_file.name}")
        
        stock_df = self.load_data(target_file)
        sector_series = self.sector_mgr.get_sector_index(target_file)
        
        # 날짜 교집합 맞추기
        if sector_series is not None:
            common_idx = stock_df.index.intersection(sector_series.index)
            stock_df = stock_df.loc[common_idx]
            sector_series = sector_series.loc[common_idx]
            stock_df['Sector'] = sector_series
        else:
            stock_df['Sector'] = stock_df['Close']  # 섹터 데이터 없으면 자기 자신으로 대체
        
        print(f"📊 데이터 기간: {stock_df.index[0]} ~ {stock_df.index[-1]} ({len(stock_df)}일)")
        
        # 2. 진화 시작
        self.agents = [{'dna': ContextDNA(), 'score': 0} for _ in range(self.population)]
        
        for g in range(1, self.generations + 1):
            print(f"\n{'='*80}")
            print(f"⚔️ [Generation {g}/{self.generations}] 맥락 인식 훈련 중...")
            print(f"{'='*80}\n")
            
            # 모든 에이전트 평가
            for agent in tqdm(self.agents, desc=f"Gen {g} 평가"):
                agent['score'] = self.evaluate(agent['dna'], stock_df)
            
            # 생존자 선발 (점수 높은 순 정렬)
            self.agents.sort(key=lambda x: x['score'], reverse=True)
            best = self.agents[0]
            
            print(f"\n🏆 Best Agent:")
            print(f"   점수: {best['score']:+.2f}%")
            print(f"   분봉: {best['dna'].timeframe}")
            print(f"   섹터 필터: {'ON' if best['dna'].use_sector_filter else 'OFF'}")
            print(f"   익절: {best['dna'].take_profit*100:.1f}% / 손절: {best['dna'].stop_loss*100:.1f}%")
            
            # 다음 세대 생성
            if g < self.generations:
                # 상위 20%만 남기고 나머지 리셋
                survivors = self.agents[:int(self.population * 0.2)]
                self.agents = survivors.copy()
                
                while len(self.agents) < self.population:
                    parent = random.choice(survivors)
                    # 복제 및 변이
                    new_dna = ContextDNA()
                    new_dna.timeframe = parent['dna'].timeframe
                    new_dna.use_sector_filter = parent['dna'].use_sector_filter
                    new_dna.take_profit = parent['dna'].take_profit
                    new_dna.stop_loss = parent['dna'].stop_loss
                    new_dna.ma_short = parent['dna'].ma_short
                    new_dna.ma_long = parent['dna'].ma_long
                    new_dna.mutate()
                    self.agents.append({'dna': new_dna, 'score': 0})
        
        # 3. 최적 DNA 압축 저장
        self.save_essence(self.agents[0]['dna'])
    
    def evaluate(self, dna, df_origin):
        """에이전트 평가 (백테스팅)"""
        try:
            # 리샘플링
            df = df_origin.resample(dna.timeframe).agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum',
                'Sector': 'last'
            }).dropna()
            
            if len(df) < 60:
                return -100
            
            # 지표 계산
            df['MA_S'] = df['Close'].rolling(dna.ma_short).mean()
            df['MA_L'] = df['Close'].rolling(dna.ma_long).mean()
            
            # 섹터 추세 (20일선 기준)
            df['Sector_MA'] = df['Sector'].rolling(20).mean()
            
            # 백테스팅
            balance = 100.0
            position = False
            entry_price = 0
            
            closes = df['Close'].values
            ma_s = df['MA_S'].values
            ma_l = df['MA_L'].values
            sectors = df['Sector'].values
            sec_mas = df['Sector_MA'].values
            
            for i in range(dna.ma_long, len(df)):
                if not position:
                    # 기본 조건: 골든크로스
                    signal = ma_s[i] > ma_l[i]
                    
                    # [맥락 필터] 섹터가 상승세인가?
                    if dna.use_sector_filter:
                        sector_bullish = sectors[i] > sec_mas[i]
                        if not sector_bullish:
                            signal = False
                    
                    if signal:
                        position = True
                        entry_price = closes[i]
                
                elif position:
                    pnl = (closes[i] - entry_price) / entry_price
                    if pnl >= dna.take_profit or pnl <= -dna.stop_loss:
                        balance *= (1 + pnl)
                        position = False
            
            return balance - 100.0
            
        except Exception as e:
            return -100
    
    def save_essence(self, dna):
        """최적 DNA를 압축하여 저장"""
        code = f'''"""
👑 ISATS CONTEXT MASTER (Compressed Essence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

맥락 인식 마스터 전략 (Context-Aware Master Strategy)

훈련 결과:
- 섹터 필터: {"ON (섹터 상승세일 때만 매수)" if dna.use_sector_filter else "OFF (개별 종목만 봄)"}
- 분봉: {dna.timeframe}
- 이평선: MA{dna.ma_short} / MA{dna.ma_long}
- 익절: {dna.take_profit*100:.1f}% / 손절: {dna.stop_loss*100:.1f}%

작성자: ISATS Neural Swarm (Auto-Generated)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

class ContextMaster:
    """맥락 인식 마스터 전략"""
    
    def __init__(self):
        self.timeframe = "{dna.timeframe}"
        self.use_sector = {dna.use_sector_filter}
        self.tp = {dna.take_profit}
        self.sl = {dna.stop_loss}
        self.ma_s = {dna.ma_short}
        self.ma_l = {dna.ma_long}
    
    def analyze(self, df, sector_trend_bullish):
        """
        맥락 분석
        
        Args:
            df: 종목 데이터 (DataFrame)
            sector_trend_bullish: 섹터가 상승세인지 (bool)
        
        Returns:
            (action, take_profit, stop_loss)
        """
        # 1. 섹터 필터 확인
        if self.use_sector and not sector_trend_bullish:
            return "HOLD (Sector Weak)", 0, 0
        
        # 2. 차트 분석
        # 리샘플링
        df_resampled = df.resample(self.timeframe).agg({{
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }}).dropna()
        
        if len(df_resampled) < self.ma_l:
            return "HOLD (Insufficient Data)", 0, 0
        
        # 이평선 계산
        ma_s = df_resampled['Close'].rolling(self.ma_s).mean().iloc[-1]
        ma_l = df_resampled['Close'].rolling(self.ma_l).mean().iloc[-1]
        
        # 골든크로스 확인
        if ma_s > ma_l:
            return "BUY", self.tp, self.sl
        else:
            return "HOLD (No Signal)", 0, 0
'''
        
        output_path = self.project_root / "strategy" / "master_context_bot.py"
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, "w", encoding='utf-8') as f:
            f.write(code)
        
        print(f"\n{'='*80}")
        print(f"💾 [Essence] 알짜배기 전략 압축 완료")
        print(f"{'='*80}")
        print(f"   파일: {output_path}")
        print(f"   섹터 필터: {'ON' if dna.use_sector_filter else 'OFF'}")
        print(f"   분봉: {dna.timeframe}")
        print(f"{'='*80}\n")


def main():
    """메인 실행 함수"""
    trainer = ContextTrainer(
        data_dir="data/KR",
        population=500,
        generations=3
    )
    trainer.run_simulation()


if __name__ == "__main__":
    main()
