import streamlit as st
import pandas as pd
import redis
import json
import time

# ---------------------------------------------------------
# [ISATS Commander Console] 지휘 통제실
# 파일: isats/backend/dashboard_app.py
# 실행: streamlit run isats/backend/dashboard_app.py
# ---------------------------------------------------------

# 페이지 기본 설정
st.set_page_config(page_title="ISATS Commander Console", layout="wide", page_icon="🚢")
st.title("🚢 ISATS v2.2 통합 지휘 통제실")

# Redis 연결 (데이터 수신용)
@st.cache_resource
def get_redis():
    return redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

try:
    r = get_redis()
    r.ping() # 연결 확인
except Exception as e:
    st.error(f"❌ Redis 연결 실패. Docker 컨테이너(isats-redis)가 켜져 있는지 확인하십시오. ({e})")
    st.stop()

# ==========================================
# 🕹️ [사이드바] 작전 통제 패널 (Control)
# ==========================================
st.sidebar.header("🕹️ 작전 통제 (Control)")
st.sidebar.markdown("---")

# [핵심] 실전 매매 승인 토글 (Kill Switch)
# 이 버튼이 켜져야만 smart_trader.py가 실제 주문을 낼 수 있음
real_trade_on = st.sidebar.toggle("⚔️ 실전 매매 승인 (Real Trading)", value=False)

if real_trade_on:
    r.set("cmd:real_trading_approved", "TRUE")
    st.sidebar.success("✅ 실전 매매 승인됨\n\n(자금이 투입됩니다)")
else:
    r.set("cmd:real_trading_approved", "FALSE")
    st.sidebar.warning("🛑 실전 매매 차단됨\n\n(안전 모드)")

st.sidebar.markdown("---")
st.sidebar.info("Tip: '실전 매매'를 켜면 AI가 승인된 알고리즘에 따라 실제 매수/매도를 수행합니다.")


# ==========================================
# 📊 [메인 화면] 실시간 자산 현황 (MTS View)
# ==========================================
st.markdown("### 📊 자산 현황 (Live Assets)")

# 실시간 데이터 갱신을 위한 컨테이너
placeholder = st.empty()

while True:
    try:
        # 백엔드 엔진(smart_trader.py)이 보낸 데이터 수신
        data_json = r.get("dashboard:status")
        
        if not data_json:
            with placeholder.container():
                st.warning("📡 엔진 신호 대기 중... (isats/scripts/smart_trader.py를 실행하십시오)")
            time.sleep(1)
            continue
            
        data = json.loads(data_json)
        
        with placeholder.container():
            # 1. 상단 요약 지표 (Metrics)
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("🧪 가상 계좌 (Total)", f"{data['virtual']['balance']:,}원", "KR/US/ETF")
            kpi2.metric("⚔️ 실전 계좌 (Real)", f"{data['real']['balance']:,}원", "0원 (미체결)")
            kpi3.metric("엔진 상태", "🟢 가동 중", f"Update: {data['timestamp']}")
            
            status_text = "매매 진행 중" if real_trade_on else "승인 대기"
            kpi4.metric("작전 상태", "ON" if real_trade_on else "OFF", status_text, delta_color="normal" if not real_trade_on else "inverse")

            st.markdown("---")

            # 2. 보유 종목 리스트 (테이블)
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("🧪 가상 포트폴리오")
                v_holdings = data['virtual']['holdings']
                rows = []
                for market, stocks in v_holdings.items():
                    for code, info in stocks.items():
                        rows.append({
                            "시장": market,
                            "종목": info['name'],
                            "수량": f"{info['qty']:,}",
                            "평가금": f"{int(info['qty'] * info['avg']):,}원"
                        })
                if rows:
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.info("보유 종목 없음")

            with c2:
                st.subheader("⚔️ 실전 포트폴리오")
                # 실전 데이터 (현재는 비어있음)
                if data['real']['holdings']:
                    st.dataframe(pd.DataFrame(data['real']['holdings']), use_container_width=True)
                else:
                    st.info("현재 보유 중인 실전 종목이 없습니다.")

            # 3. 로그 창
            with st.expander("📝 실시간 매매 로그 확인", expanded=True):
                if real_trade_on:
                    st.write(f"[{data['timestamp']}] 📡 시장 감시 중... 타겟 포착 시 자동 매수 진행.")
                else:
                    st.write(f"[{data['timestamp']}] 🔒 안전 장치 가동 중. 모든 주문이 차단되었습니다.")

        time.sleep(1) # 1초마다 화면 리프레시

    except Exception as e:
        # 에러 발생 시 잠시 대기 후 재시도
        time.sleep(1)
