"""
🤖 ISATS v6.0 - FinRL (강화학습 앙상블 전략)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

작전명: "PPO + A2C + DDPG 앙상블 + Turbulence Index"

역할:
- PPO (추세 추종)
- A2C (안정성)
- DDPG (연속 제어)
- 금융 난기류 지수 (리스크 관리)
- 분기별 최적 모델 선택

작성자: ISATS Neural Swarm
버전: 6.0 (FinRL Ensemble)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# 프로젝트 루트
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 선택적 임포트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

try:
    import gym
    from gym import spaces
    HAS_GYM = True
except ImportError:
    HAS_GYM = False
    print("⚠️ [Warning] gym not found. Installing...")
    os.system("pip install gym --quiet")
    import gym
    from gym import spaces
    HAS_GYM = True

try:
    from stable_baselines3 import PPO, A2C, DDPG
    from stable_baselines3.common.vec_env import DummyVecEnv
    HAS_SB3 = True
except ImportError:
    HAS_SB3 = False
    print("⚠️ [Warning] stable-baselines3 not found. Installing...")
    os.system("pip install stable-baselines3 --quiet")
    from stable_baselines3 import PPO, A2C, DDPG
    from stable_baselines3.common.vec_env import DummyVecEnv
    HAS_SB3 = True


# ==========================================
# 📊 주식 거래 환경 (Gym Environment)
# ==========================================

class StockTradingEnv(gym.Env):
    """강화학습용 주식 거래 환경"""
    
    metadata = {'render.modes': ['human']}
    
    def __init__(
        self,
        df: pd.DataFrame,
        initial_balance: float = 10000.0,
        transaction_fee: float = 0.001
    ):
        """
        Args:
            df: OHLCV + 기술적 지표 데이터프레임
            initial_balance: 초기 자금
            transaction_fee: 거래 수수료 (0.1%)
        """
        super(StockTradingEnv, self).__init__()
        
        self.df = df.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.transaction_fee = transaction_fee
        
        # 상태 공간: [잔고, 보유주식수, 현재가, 기술적지표들...]
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(len(df.columns) + 2,),  # +2 for balance and holdings
            dtype=np.float32
        )
        
        # 행동 공간: [-1, 1] (매도 ~ 매수)
        # -1: 전량 매도, 0: 보유, 1: 전량 매수
        self.action_space = spaces.Box(
            low=-1,
            high=1,
            shape=(1,),
            dtype=np.float32
        )
        
        self.reset()
    
    def reset(self):
        """환경 초기화"""
        self.current_step = 0
        self.balance = self.initial_balance
        self.holdings = 0
        self.total_asset = self.initial_balance
        
        return self._get_observation()
    
    def _get_observation(self):
        """현재 상태 반환"""
        if self.current_step >= len(self.df):
            self.current_step = len(self.df) - 1
        
        row = self.df.iloc[self.current_step]
        
        # [잔고, 보유주식수, 현재가, 기술적지표들...]
        obs = np.array([
            self.balance / self.initial_balance,  # 정규화
            self.holdings,
            *row.values
        ], dtype=np.float32)
        
        return obs
    
    def step(self, action):
        """행동 실행"""
        action = action[0]  # [-1, 1]
        current_price = self.df.iloc[self.current_step]['Close']
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 행동 실행
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if action > 0.1:  # 매수
            # 사용 가능한 금액으로 최대한 매수
            max_shares = int(self.balance / (current_price * (1 + self.transaction_fee)))
            shares_to_buy = int(max_shares * action)
            
            if shares_to_buy > 0:
                cost = shares_to_buy * current_price * (1 + self.transaction_fee)
                self.balance -= cost
                self.holdings += shares_to_buy
        
        elif action < -0.1:  # 매도
            # 보유 주식 매도
            shares_to_sell = int(self.holdings * abs(action))
            
            if shares_to_sell > 0:
                revenue = shares_to_sell * current_price * (1 - self.transaction_fee)
                self.balance += revenue
                self.holdings -= shares_to_sell
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 다음 스텝
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        self.current_step += 1
        done = self.current_step >= len(self.df) - 1
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 보상 계산 (총 자산 변화율)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if not done:
            next_price = self.df.iloc[self.current_step]['Close']
        else:
            next_price = current_price
        
        new_total_asset = self.balance + self.holdings * next_price
        reward = (new_total_asset - self.total_asset) / self.total_asset
        self.total_asset = new_total_asset
        
        obs = self._get_observation()
        info = {
            'balance': self.balance,
            'holdings': self.holdings,
            'total_asset': self.total_asset
        }
        
        return obs, reward, done, info
    
    def render(self, mode='human'):
        """환경 시각화"""
        print(f"Step: {self.current_step}, Balance: ${self.balance:.2f}, "
              f"Holdings: {self.holdings}, Total: ${self.total_asset:.2f}")


# ==========================================
# 🤖 FinRL 앙상블 에이전트
# ==========================================

class FinRLEnsemble:
    """PPO + A2C + DDPG 앙상블 전략"""
    
    def __init__(
        self,
        env: StockTradingEnv,
        turbulence_threshold: float = 100.0
    ):
        """
        Args:
            env: 거래 환경
            turbulence_threshold: 난기류 지수 임계값
        """
        self.env = DummyVecEnv([lambda: env])
        self.turbulence_threshold = turbulence_threshold
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3개 에이전트 생성
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        self.agents = {
            'PPO': PPO('MlpPolicy', self.env, verbose=0),
            'A2C': A2C('MlpPolicy', self.env, verbose=0),
            'DDPG': DDPG('MlpPolicy', self.env, verbose=0)
        }
        
        self.best_agent = 'PPO'
        self.performance = {name: [] for name in self.agents.keys()}
    
    def train(self, timesteps: int = 10000):
        """
        모든 에이전트 학습
        
        Args:
            timesteps: 학습 타임스텝
        """
        print(f"\n{'='*80}")
        print(f"🎓 FinRL 앙상블 학습 시작")
        print(f"{'='*80}\n")
        
        for name, agent in self.agents.items():
            print(f"🤖 [{name}] 학습 중...")
            agent.learn(total_timesteps=timesteps)
            print(f"   ✅ [{name}] 학습 완료\n")
    
    def evaluate(self, test_env: StockTradingEnv) -> Dict[str, float]:
        """
        모든 에이전트 평가
        
        Args:
            test_env: 테스트 환경
        
        Returns:
            Dict[str, float]: 에이전트별 샤프 지수
        """
        print(f"\n{'='*80}")
        print(f"📊 FinRL 앙상블 평가")
        print(f"{'='*80}\n")
        
        sharpe_ratios = {}
        
        for name, agent in self.agents.items():
            obs = test_env.reset()
            done = False
            returns = []
            
            while not done:
                action, _ = agent.predict(obs, deterministic=True)
                obs, reward, done, info = test_env.step(action)
                returns.append(reward)
            
            # 샤프 지수 계산
            returns = np.array(returns)
            sharpe = np.mean(returns) / (np.std(returns) + 1e-9) * np.sqrt(252)
            sharpe_ratios[name] = sharpe
            
            print(f"🤖 [{name}] Sharpe Ratio: {sharpe:.4f}")
        
        # 최고 성능 에이전트 선택
        self.best_agent = max(sharpe_ratios, key=sharpe_ratios.get)
        print(f"\n🏆 최고 성능: {self.best_agent} (Sharpe: {sharpe_ratios[self.best_agent]:.4f})")
        print(f"{'='*80}\n")
        
        return sharpe_ratios
    
    def predict(self, obs: np.ndarray, turbulence: float = 0.0) -> np.ndarray:
        """
        예측 (최고 성능 에이전트 사용)
        
        Args:
            obs: 관측값
            turbulence: 난기류 지수
        
        Returns:
            행동
        """
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 난기류 지수 확인 (리스크 관리)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if turbulence > self.turbulence_threshold:
            # 시장 붕괴 감지 → 전량 매도
            return np.array([-1.0])
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 최고 성능 에이전트로 예측
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        action, _ = self.agents[self.best_agent].predict(obs, deterministic=True)
        return action
    
    def save(self, path: str):
        """모든 에이전트 저장"""
        for name, agent in self.agents.items():
            agent_path = f"{path}_{name}.zip"
            agent.save(agent_path)
            print(f"✅ [{name}] 저장: {agent_path}")
    
    def load(self, path: str):
        """모든 에이전트 로드"""
        for name in self.agents.keys():
            agent_path = f"{path}_{name}.zip"
            
            if os.path.exists(agent_path):
                if name == 'PPO':
                    self.agents[name] = PPO.load(agent_path, env=self.env)
                elif name == 'A2C':
                    self.agents[name] = A2C.load(agent_path, env=self.env)
                elif name == 'DDPG':
                    self.agents[name] = DDPG.load(agent_path, env=self.env)
                
                print(f"✅ [{name}] 로드: {agent_path}")


# ==========================================
# 📈 금융 난기류 지수 (Turbulence Index)
# ==========================================

def calculate_turbulence(df: pd.DataFrame, window: int = 252) -> pd.Series:
    """
    금융 난기류 지수 계산
    
    Args:
        df: OHLCV 데이터프레임
        window: 계산 윈도우 (252일 = 1년)
    
    Returns:
        난기류 지수 시리즈
    """
    returns = df['Close'].pct_change().dropna()
    
    turbulence = []
    
    for i in range(window, len(returns)):
        window_returns = returns.iloc[i-window:i]
        
        # 평균 및 공분산
        mean = window_returns.mean()
        cov = window_returns.var()
        
        # 마할라노비스 거리
        current_return = returns.iloc[i]
        distance = (current_return - mean) ** 2 / (cov + 1e-9)
        
        turbulence.append(distance)
    
    # 앞부분 패딩
    turbulence = [0] * window + turbulence
    
    return pd.Series(turbulence, index=df.index)


# ==========================================
# 실행
# ==========================================

if __name__ == "__main__":
    print(f"\n{'='*80}")
    print(f"🤖 FinRL 앙상블 테스트")
    print(f"{'='*80}\n")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. 데이터 로드
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    data_path = "data/KR/005930.KS.csv"
    
    if os.path.exists(data_path):
        df = pd.read_csv(data_path)
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
        
        # 기술적 지표 추가 (간단한 예시)
        df['SMA_20'] = df['Close'].rolling(20).mean()
        df['SMA_60'] = df['Close'].rolling(60).mean()
        df = df.dropna()
        
        print(f"✅ 데이터 로드: {len(df)}개 레코드")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. 학습/테스트 분할
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        train_size = int(len(df) * 0.8)
        train_df = df.iloc[:train_size]
        test_df = df.iloc[train_size:]
        
        print(f"✅ 학습 데이터: {len(train_df)}개")
        print(f"✅ 테스트 데이터: {len(test_df)}개")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. 환경 생성
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        train_env = StockTradingEnv(train_df)
        test_env = StockTradingEnv(test_df)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4. FinRL 앙상블 생성 및 학습
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        ensemble = FinRLEnsemble(train_env)
        ensemble.train(timesteps=10000)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 5. 평가
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        sharpe_ratios = ensemble.evaluate(test_env)
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 6. 모델 저장
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        ensemble.save("brain/finrl_ensemble")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 7. 난기류 지수 계산
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        turbulence = calculate_turbulence(df)
        print(f"\n✅ 난기류 지수 계산 완료")
        print(f"   평균: {turbulence.mean():.2f}")
        print(f"   최대: {turbulence.max():.2f}")
        print(f"   임계값: {ensemble.turbulence_threshold:.2f}")
    
    else:
        print(f"❌ 데이터 파일 없음: {data_path}")
