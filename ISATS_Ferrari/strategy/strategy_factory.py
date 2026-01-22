"""
🏭 ISATS v4.0 "STRATEGY FACTORY" - Champion DNA to Code
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

역할:
- 챔피언 DNA 로드 (genesis_champion.json)
- 즉시 사용 가능한 파이썬 코드로 변환
- master_bot_v4.py 자동 생성

작성자: ISATS Neural Swarm
버전: 4.0 (Strategy Factory)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
from datetime import datetime


def load_champion_dna():
    """챔피언 DNA 로드"""
    dna_path = os.path.join(os.path.dirname(__file__), "..", "brain", "genesis_champion.json")
    
    if not os.path.exists(dna_path):
        print(f"❌ 챔피언 DNA를 찾을 수 없습니다: {dna_path}")
        print("   먼저 genesis_evolution.py를 실행하세요.")
        return None
    
    with open(dna_path, "r") as f:
        dna = json.load(f)
    
    return dna


def generate_strategy_code(dna):
    """DNA를 파이썬 코드로 변환"""
    
    code = f'''"""
🏆 ISATS v4.0 Master Bot (Genesis Champion)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

이 코드는 AI가 1,000명의 봇을 100개의 역사적 난제에서 5세대 동안 진화시켜
최종적으로 살아남은 챔피언의 DNA를 코드로 압축한 것입니다.

생성 시각: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

챔피언 DNA:
- 분봉: {dna['timeframe']}
- 단기 이평선: {dna['ma_short']}
- 장기 이평선: {dna['ma_long']}
- 익절: {dna['take_profit'] * 100:.1f}%
- 손절: {dna['stop_loss'] * 100:.1f}%
- 거래량 배수: {dna['vol_factor']}배

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import pandas as pd
import numpy as np
from datetime import datetime


class MasterBotV4:
    """Genesis Champion Strategy"""
    
    def __init__(self):
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 챔피언 DNA (자동 생성)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        self.timeframe = '{dna['timeframe']}'
        self.ma_short = {dna['ma_short']}
        self.ma_long = {dna['ma_long']}
        self.take_profit = {dna['take_profit']}
        self.stop_loss = {dna['stop_loss']}
        self.vol_factor = {dna['vol_factor']}
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 상태 변수
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        self.position = False
        self.entry_price = 0
        self.entry_time = None
        self.balance = 10000.0
        self.ticker = None
        
        print(f"✅ [MasterBotV4] 챔피언 전략 로드 완료")
        print(f"   분봉: {{self.timeframe}}")
        print(f"   이평선: {{self.ma_short}}/{{self.ma_long}}")
        print(f"   익절/손절: {{self.take_profit*100:.1f}}% / {{self.stop_loss*100:.1f}}%")
    
    def on_tick(self, market_data):
        """
        실시간 틱 데이터 수신
        
        Args:
            market_data: Dict with keys: Date, Open, High, Low, Close, Volume
        """
        # 실시간 데이터는 별도 처리 필요
        # 여기서는 백테스팅용 인터페이스만 제공
        pass
    
    def analyze(self, df):
        """
        차트 분석 및 매매 신호 생성
        
        Args:
            df: DataFrame with columns: Date, Open, High, Low, Close, Volume
        
        Returns:
            str: 'BUY', 'SELL', 'HOLD'
        """
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. 분봉 변환
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if 'Date' in df.columns:
            df = df.set_index('Date')
        
        df_resampled = df.resample(self.timeframe).agg({{
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }}).dropna()
        
        if len(df_resampled) < self.ma_long:
            return 'HOLD'
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. 지표 계산
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        df_resampled['MA_S'] = df_resampled['Close'].rolling(self.ma_short).mean()
        df_resampled['MA_L'] = df_resampled['Close'].rolling(self.ma_long).mean()
        df_resampled['Vol_MA'] = df_resampled['Volume'].rolling(20).mean()
        
        # 최근 데이터
        current = df_resampled.iloc[-1]
        prev = df_resampled.iloc[-2]
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. 매매 신호
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if not self.position:
            # [매수] 골든크로스 + 수급 폭발
            golden_cross = (current['MA_S'] > current['MA_L']) and (prev['MA_S'] <= prev['MA_L'])
            volume_spike = current['Volume'] > current['Vol_MA'] * self.vol_factor
            
            if golden_cross and volume_spike:
                self.position = True
                self.entry_price = current['Close']
                self.entry_time = current.name
                return 'BUY'
        
        else:
            # [청산] 익절/손절/추세 종료
            pct_change = (current['Close'] - self.entry_price) / self.entry_price
            
            # 손절
            if pct_change <= -self.stop_loss:
                self.position = False
                return 'SELL'
            
            # 익절
            if pct_change >= self.take_profit:
                self.position = False
                return 'SELL'
            
            # 데드크로스
            if current['MA_S'] < current['MA_L']:
                self.position = False
                return 'SELL'
        
        return 'HOLD'
    
    def backtest(self, df):
        """
        백테스팅
        
        Args:
            df: DataFrame with columns: Date, Open, High, Low, Close, Volume
        
        Returns:
            Dict: 백테스팅 결과
        """
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. 분봉 변환
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if 'Date' in df.columns:
            df = df.set_index('Date')
        
        df_resampled = df.resample(self.timeframe).agg({{
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }}).dropna()
        
        if len(df_resampled) < self.ma_long:
            return {{'error': 'Not enough data'}}
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. 지표 계산
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        df_resampled['MA_S'] = df_resampled['Close'].rolling(self.ma_short).mean()
        df_resampled['MA_L'] = df_resampled['Close'].rolling(self.ma_long).mean()
        df_resampled['Vol_MA'] = df_resampled['Volume'].rolling(20).mean()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. 백테스팅 루프
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        balance = 10000.0
        position = False
        entry_price = 0
        trades = []
        
        for i in range(self.ma_long, len(df_resampled)):
            current = df_resampled.iloc[i]
            prev = df_resampled.iloc[i-1]
            
            if not position:
                # 매수
                golden_cross = (current['MA_S'] > current['MA_L']) and (prev['MA_S'] <= prev['MA_L'])
                volume_spike = current['Volume'] > current['Vol_MA'] * self.vol_factor
                
                if golden_cross and volume_spike:
                    position = True
                    entry_price = current['Close']
            
            else:
                # 청산
                pct_change = (current['Close'] - entry_price) / entry_price
                
                action = None
                
                if pct_change <= -self.stop_loss:
                    action = 'STOP_LOSS'
                elif pct_change >= self.take_profit:
                    action = 'TAKE_PROFIT'
                elif current['MA_S'] < current['MA_L']:
                    action = 'TREND_END'
                
                if action:
                    balance *= (1 + pct_change)
                    position = False
                    
                    trades.append({{
                        'entry': entry_price,
                        'exit': current['Close'],
                        'pnl': pct_change * 100,
                        'action': action
                    }})
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4. 결과 집계
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        total_return = (balance - 10000.0) / 10000.0 * 100
        win_trades = [t for t in trades if t['pnl'] > 0]
        lose_trades = [t for t in trades if t['pnl'] <= 0]
        
        return {{
            'total_return': round(total_return, 2),
            'final_balance': round(balance, 2),
            'total_trades': len(trades),
            'win_trades': len(win_trades),
            'lose_trades': len(lose_trades),
            'win_rate': round(len(win_trades) / max(1, len(trades)) * 100, 2),
            'trades': trades
        }}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 테스트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    import os
    
    bot = MasterBotV4()
    
    # 테스트 데이터 로드
    test_files = [
        "data/KR/005930.KS.csv",
        "data/US/AAPL.csv",
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\\n📊 백테스팅: {{test_file}}")
            
            df = pd.read_csv(test_file)
            df['Date'] = pd.to_datetime(df['Date'])
            
            result = bot.backtest(df)
            
            print(f"   총 수익률: {{result['total_return']}}%")
            print(f"   최종 잔고: ${{result['final_balance']:,.2f}}")
            print(f"   총 거래: {{result['total_trades']}}회")
            print(f"   승률: {{result['win_rate']}}%")
            
            break
'''
    
    return code


def save_strategy_code(code):
    """전략 코드 저장"""
    strategy_dir = os.path.join(os.path.dirname(__file__))
    os.makedirs(strategy_dir, exist_ok=True)
    
    output_path = os.path.join(strategy_dir, "master_bot_v4.py")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    
    return output_path


def main():
    """메인 실행"""
    print(f"\n{'='*80}")
    print(f"🏭 ISATS v4.0 Strategy Factory")
    print(f"{'='*80}\n")
    
    # 1. DNA 로드
    print("📂 챔피언 DNA 로드 중...")
    dna = load_champion_dna()
    
    if not dna:
        return
    
    print(f"✅ DNA 로드 완료")
    print(f"   분봉: {dna['timeframe']}")
    print(f"   이평선: {dna['ma_short']}/{dna['ma_long']}")
    print(f"   익절/손절: {dna['take_profit']*100:.1f}% / {dna['stop_loss']*100:.1f}%")
    print(f"   거래량: {dna['vol_factor']}배")
    
    # 2. 코드 생성
    print(f"\n🏭 전략 코드 생성 중...")
    code = generate_strategy_code(dna)
    
    # 3. 저장
    output_path = save_strategy_code(code)
    
    print(f"✅ 전략 코드 생성 완료: {output_path}")
    print(f"\n{'='*80}")
    print(f"🚀 사용 방법")
    print(f"{'='*80}")
    print(f"from strategy.master_bot_v4 import MasterBotV4")
    print(f"")
    print(f"bot = MasterBotV4()")
    print(f"result = bot.backtest(df)")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
