import streamlit as st
import pandas as pd
import redis
import json
import time

# ---------------------------------------------------------
# [ISATS Ferrari Commander Console] 지휘 통제실
# ---------------------------------------------------------

st.set_page_config(page_title="ISATS Ferrari Console", layout="wide", page_icon="🏎️")
st.title("🏎️ ISATS v2.5 Ferrari 지휘 통제실")

@st.cache_resource
def get_redis():
    return redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

try:
    r = get_redis()
    r.ping()
except Exception as e:
    st.error(f"❌ Redis 연결 실패. Docker를 확인하십시오. ({e})")
    st.stop()

# ==========================================
# 🕹️ [사이드바] 작전 제어
# ==========================================
st.sidebar.header("🕹️ 전군 지휘 (Control)")
st.sidebar.markdown("---")

real_trade_on = st.sidebar.toggle("⚔️ 실전 매수 승인 (Real Trade)", value=False)
if real_trade_on:
    r.set("cmd:real_trading_approved", "TRUE")
    st.sidebar.success("✅ 실전 투입 승인됨")
else:
    r.set("cmd:real_trading_approved", "FALSE")
    st.sidebar.warning("🛑 안전 장치 가동 중")

st.sidebar.markdown("---")
st.sidebar.info("Tip: DNA 유전자가 시장 상황에 맞춰 매일 밤 스스로 재설계됩니다.")

# ==========================================
# 📊 [메인] 현황판
# ==========================================
placeholder = st.empty()

while True:
    try:
        data_json = r.get("dashboard:status")
        if not data_json:
            with placeholder.container():
                st.warning("📡 엔진 신호 대기 중... (isats/core/engine.py를 실행하십시오)")
            time.sleep(1)
            continue
            
        data = json.loads(data_json)
        
        with placeholder.container():
            # 1. 퀀텀 매트릭스 (KPI)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🧬 현재 세대", f"{data['generation']} Gen")
            m2.metric("💰 가상 자산", f"{data['virtual_bal']:,}원")
            m3.metric("⚔️ 실전 자산", f"{data['real_bal']:,}원")
            m4.metric("📈 아키텍처", "🏎️ Ferrari (v2.5)", "Pure Core")

            st.markdown("---")

            # 2. DNA 유전자 지도 (Genetics Map)
            st.subheader("🧬 활성화된 유전자 (Current DNA)")
            genes = data['genes']
            col1, col2, col3 = st.columns(3)
            col1.info(f"RSI Period: {genes['rsi_period']}")
            col2.warning(f"Stop Loss: {genes['stop_loss_pct']*100}%")
            col3.success(f"Take Profit: {genes['take_profit_pct']*100}%")

            # 3. 진화 로그 및 자산 데이터 (테이블 예시)
            st.markdown("---")
            st.subheader("📝 실시간 작전 보고")
            log_text = f"[{data['timestamp']}] {data['generation']}세대 인공지능이 시장의 지각변동을 감지하고 반응 지표를 조정 중입니다."
            st.code(log_text)
            
            if real_trade_on:
                st.snow() # 승인 시 축하 효과 예시

        time.sleep(1)
    except Exception as e:
        time.sleep(1)
