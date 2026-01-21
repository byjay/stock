import pandas as pd
import pandas_ta as ta
import logging

logger = logging.getLogger("AdvancedIndicators")

def add_advanced_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    고급 기술 지표 추가
    
    Indicators:
    - MACD (Moving Average Convergence Divergence)
    - Bollinger Bands
    - Stochastic Oscillator
    - ATR (Average True Range)
    - Volume Analysis
    
    Args:
        df: OHLCV DataFrame
    
    Returns:
        DataFrame with additional indicator columns
    """
    if df.empty or len(df) < 30:
        logger.warning("DataFrame too small for indicators")
        return df
    
    df = df.copy()
    
    try:
        # 1. MACD (12, 26, 9)
        macd = ta.macd(df['Close'], fast=12, slow=26, signal=9)
        if macd is not None:
            df['MACD'] = macd['MACD_12_26_9']
            df['MACD_signal'] = macd['MACDs_12_26_9']
            df['MACD_hist'] = macd['MACDh_12_26_9']
        
        # 2. Bollinger Bands (20, 2)
        bbands = ta.bbands(df['Close'], length=20, std=2)
        if bbands is not None:
            df['BB_upper'] = bbands['BBU_20_2.0']
            df['BB_middle'] = bbands['BBM_20_2.0']
            df['BB_lower'] = bbands['BBL_20_2.0']
            df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / df['BB_middle']
            df['BB_pct'] = (df['Close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])
        
        # 3. Stochastic Oscillator (14, 3, 3)
        stoch = ta.stoch(df['High'], df['Low'], df['Close'], k=14, d=3, smooth_k=3)
        if stoch is not None:
            df['STOCH_k'] = stoch['STOCHk_14_3_3']
            df['STOCH_d'] = stoch['STOCHd_14_3_3']
        
        # 4. ATR (Average True Range) - 14
        atr = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        if atr is not None:
            df['ATR'] = atr
            df['ATR_pct'] = (df['ATR'] / df['Close']) * 100
        
        # 5. RSI (14) - if not already present
        if 'RSI' not in df.columns:
            rsi = ta.rsi(df['Close'], length=14)
            if rsi is not None:
                df['RSI'] = rsi
        
        # 6. Moving Averages
        df['MA5'] = ta.sma(df['Close'], length=5)
        df['MA10'] = ta.sma(df['Close'], length=10)
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['MA50'] = ta.sma(df['Close'], length=50)
        df['MA200'] = ta.sma(df['Close'], length=200)
        
        # 7. EMA
        df['EMA12'] = ta.ema(df['Close'], length=12)
        df['EMA26'] = ta.ema(df['Close'], length=26)
        
        # 8. Volume Analysis
        df['Volume_MA20'] = ta.sma(df['Volume'], length=20)
        df['Volume_ratio'] = df['Volume'] / df['Volume_MA20']
        
        # 9. OBV (On-Balance Volume)
        obv = ta.obv(df['Close'], df['Volume'])
        if obv is not None:
            df['OBV'] = obv
        
        logger.info(f"✅ Added {len([c for c in df.columns if c not in ['Open', 'High', 'Low', 'Close', 'Volume']])} indicators")
        
    except Exception as e:
        logger.error(f"Error adding indicators: {e}")
    
    return df


def check_macd_cross(df: pd.DataFrame) -> dict:
    """MACD 골든크로스/데드크로스 체크"""
    if 'MACD' not in df.columns or len(df) < 2:
        return {'signal': False, 'score': 0, 'reason': 'No MACD data'}
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 골든크로스: MACD가 Signal을 상향 돌파
    golden_cross = (latest['MACD'] > latest['MACD_signal'] and 
                    prev['MACD'] <= prev['MACD_signal'])
    
    # 히스토그램 증가
    hist_increasing = latest['MACD_hist'] > prev['MACD_hist']
    
    if golden_cross and hist_increasing:
        return {'signal': True, 'score': 15, 'reason': 'MACD Golden Cross + Hist↑'}
    elif golden_cross:
        return {'signal': True, 'score': 10, 'reason': 'MACD Golden Cross'}
    elif hist_increasing and latest['MACD_hist'] > 0:
        return {'signal': True, 'score': 5, 'reason': 'MACD Hist Increasing'}
    
    return {'signal': False, 'score': 0, 'reason': 'No MACD signal'}


def check_bb_squeeze(df: pd.DataFrame) -> dict:
    """볼린저 밴드 스퀴즈 및 돌파 체크"""
    if 'BB_width' not in df.columns or len(df) < 20:
        return {'signal': False, 'score': 0, 'reason': 'No BB data'}
    
    latest = df.iloc[-1]
    
    # BB Width가 최근 20일 중 하위 20%면 스퀴즈
    recent_widths = df['BB_width'].tail(20)
    is_squeeze = latest['BB_width'] < recent_widths.quantile(0.2)
    
    # 상단 돌파
    upper_breakout = latest['Close'] > latest['BB_upper']
    
    # BB %B (0~1 사이, 0.5가 중간)
    bb_pct = latest.get('BB_pct', 0.5)
    
    if upper_breakout:
        return {'signal': True, 'score': 12, 'reason': 'BB Upper Breakout'}
    elif is_squeeze and bb_pct > 0.7:
        return {'signal': True, 'score': 8, 'reason': 'BB Squeeze + High %B'}
    elif bb_pct > 0.8:
        return {'signal': True, 'score': 5, 'reason': 'BB %B > 0.8'}
    
    return {'signal': False, 'score': 0, 'reason': 'No BB signal'}


def check_stochastic(df: pd.DataFrame) -> dict:
    """스토캐스틱 과매수/과매도 체크"""
    if 'STOCH_k' not in df.columns or len(df) < 2:
        return {'signal': False, 'score': 0, 'reason': 'No Stoch data'}
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    stoch_k = latest['STOCH_k']
    stoch_d = latest['STOCH_d']
    
    # 과매도 구간에서 상승 반전
    if stoch_k < 20 and stoch_k > stoch_d and prev['STOCH_k'] <= prev['STOCH_d']:
        return {'signal': True, 'score': 10, 'reason': 'Stoch Oversold Reversal'}
    
    # 과매수 구간 진입
    elif stoch_k > 80:
        return {'signal': False, 'score': -5, 'reason': 'Stoch Overbought'}
    
    return {'signal': False, 'score': 0, 'reason': 'No Stoch signal'}
