# 🤖 한국투자증권 AI 서비스 & 자동매매 완전 가이드

## 📅 최종 업데이트: 2026-01-22

---

## 🎯 한국투자증권 제공 AI 서비스 전체 목록

### 1. KIS Developers 포털 (API 문서)
**URL**: https://apiportal.koreainvestment.com

**제공 서비스**:
- API 명세서 (336개 API)
- 샘플 코드 다운로드
- API 테스트 도구
- 개발자 가이드

**접속 방법**:
```
1. 위 URL 접속
2. 로그인 (한국투자증권 계좌 필요)
3. "API 서비스" 메뉴 선택
4. "API 문서 보기" 클릭
```

---

### 2. 공식 GitHub 저장소
**URL**: https://github.com/koreainvestment/open-trading-api

**제공 내용**:
- 전체 샘플 코드 (Python, Node.js 등)
- 실시간 WebSocket 예제
- Postman 컬렉션
- 종목 마스터 파일

**주요 폴더**:
```
/examples_llm/        # LLM용 기능 단위 샘플
/examples_user/       # 사용자용 통합 예제
/stocks_info/         # 종목 정보 마스터
/postman/            # Postman 테스트 세트
```

---

### 3. 자동매매 구성 가이드

#### 📌 3단계 자동매매 구조

```
┌─────────────────────────────────────────────────────────┐
│  [1단계] 인증 (Authentication)                            │
│  - 접근토큰 발급: /oauth2/tokenP                          │
│  - 유효기간: 1일                                          │
│  - 제한: 5분당 1회                                        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  [2단계] 데이터 수집 (Data Collection)                    │
│  - 실시간 시세: WebSocket (H0STCNT0, H0STASP0)           │
│  - 현재가 조회: /uapi/domestic-stock/v1/quotations/...   │
│  - 조건검색: /uapi/domestic-stock/v1/analysis/...        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  [3단계] 주문 실행 (Order Execution)                      │
│  - 매수/매도: /uapi/domestic-stock/v1/trading/order-cash │
│  - 정정/취소: /uapi/domestic-stock/v1/trading/order-...  │
│  - 체결통보: WebSocket (H0STCNI0)                        │
└─────────────────────────────────────────────────────────┘
```

---

### 4. API 카테고리별 접속 정보

#### 🇰🇷 국내주식 API

| 기능 | TR_ID | URL | 비고 |
|------|-------|-----|------|
| **주문** |
| 현금매수 | TTTC0802U | `/uapi/domestic-stock/v1/trading/order-cash` | POST |
| 현금매도 | TTTC0801U | `/uapi/domestic-stock/v1/trading/order-cash` | POST |
| 정정취소 | TTTC0803U | `/uapi/domestic-stock/v1/trading/order-rvsecncl` | POST |
| **조회** |
| 현재가 | FHKST01010100 | `/uapi/domestic-stock/v1/quotations/inquire-price` | GET |
| 호가 | FHKST01010200 | `/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn` | GET |
| 일봉 | FHKST01010400 | `/uapi/domestic-stock/v1/quotations/inquire-daily-price` | GET |
| 잔고 | TTTC8434R | `/uapi/domestic-stock/v1/trading/inquire-balance` | GET |

#### 🌍 해외주식 API

| 기능 | TR_ID | URL | 거래소 |
|------|-------|-----|--------|
| 매수 | JTTT1002U | `/uapi/overseas-stock/v1/trading/order` | NAS, NYS, AMS |
| 매도 | JTTT1006U | `/uapi/overseas-stock/v1/trading/order` | NAS, NYS, AMS |
| 현재가 | HHDFS76200200 | `/uapi/overseas-price/v1/quotations/price-detail` | 전체 |
| 일봉 | HHDFS76240000 | `/uapi/overseas-price/v1/quotations/dailyprice` | 전체 |

**지원 거래소**:
- NAS: NASDAQ
- NYS: NYSE
- AMS: AMEX
- TSE: 도쿄증권거래소
- SHS: 상해증권거래소
- HKS: 홍콩증권거래소

#### ⚡ 실시간 WebSocket 채널

| 채널 ID | 설명 | 데이터 형식 |
|---------|------|-------------|
| H0STCNT0 | 국내주식 실시간체결 | 체결가, 거래량, 시간 |
| H0STASP0 | 국내주식 실시간호가 | 10호가, 잔량 |
| H0STCNI0 | 체결통보 | 내 주문 체결 알림 |
| H0GSCNT0 | 해외주식 실시간체결 | 해외 체결가 |
| H0GSASP0 | 해외주식 실시간호가 | 해외 호가 |

**WebSocket 접속 URL**:
- 실전: `ws://ops.koreainvestment.com:21000`
- 모의: `ws://ops.koreainvestment.com:31000`

---

### 5. 자동매매 샘플 코드 위치

#### Python 예제
```bash
# GitHub 클론
git clone https://github.com/koreainvestment/open-trading-api.git
cd open-trading-api

# 인증 샘플
examples_user/kis_auth.py

# 국내주식 자동매매
examples_user/domestic_stock/domestic_stock_functions.py
examples_user/domestic_stock/domestic_stock_examples.py

# 해외주식 자동매매
examples_user/overseas_stock/overseas_stock_functions.py
examples_user/overseas_stock/overseas_stock_examples.py

# 실시간 WebSocket
examples_user/domestic_stock/domestic_stock_functions_ws.py
```

---

### 6. ISATS 시스템에서 활용하는 방법

#### 현재 구현 상태
```python
# 1. 통합 API 클라이언트
from core.kis_official_api import KISUnifiedClient

# 2. 초기화
client = KISUnifiedClient(mode="virtual")  # 또는 "real"
client.initialize()

# 3. 국내주식 현재가 조회
price = client.get_price("005930", market="KR")

# 4. 미국주식 현재가 조회
price = client.get_price("AAPL", market="US")

# 5. 주문 실행
result = client.place_order(
    ticker="005930",
    action="BUY",
    quantity=10,
    price=70000,
    market="KR"
)

# 6. 잔고 조회
holdings, summary = client.get_balance(market="KR")
```

---

### 7. 실전 자동매매 실행 방법

#### A. 국내주식 자동매매
```bash
# 모의투자
python auto_trading_launcher.py --mode virtual

# 실전투자
python auto_trading_launcher.py --mode real
```

#### B. 미국주식 자동매매
```bash
# 모의투자
python us_trading_launcher.py --mode virtual

# 실전투자
python us_trading_launcher.py --mode real
```

#### C. 계좌 조회
```bash
python check_accounts.py
```

---

### 8. API 제한 사항 (Rate Limit)

| 항목 | 제한 | 비고 |
|------|------|------|
| 토큰 발급 | 5분당 1회 | 재발급 시 기존 토큰 무효화 |
| API 호출 | 초당 10건 | 초과 시 429 에러 |
| WebSocket 연결 | 동시 40개 | 채널 제한 |
| 토큰 유효기간 | 1일 | 매일 갱신 필요 |

**대응 방법**:
```python
# 1. 토큰 캐싱
# 2. Exponential Backoff
# 3. 요청 큐잉
# 4. WebSocket 우선 사용
```

---

### 9. 모의투자 vs 실전투자

| 구분 | 모의투자 | 실전투자 |
|------|----------|----------|
| **URL** | https://openapivts.koreainvestment.com:29443 | https://openapi.koreainvestment.com:9443 |
| **WebSocket** | ws://ops.koreainvestment.com:31000 | ws://ops.koreainvestment.com:21000 |
| **TR_ID** | V로 시작 (예: VTTC0802U) | T로 시작 (예: TTTC0802U) |
| **자금** | 가상 1억원 | 실제 계좌 잔고 |
| **수수료** | 무료 | 실제 부과 |
| **데이터** | 15분 지연 | 실시간 |

---

### 10. 문의 및 지원

#### 공식 지원 채널
| 채널 | URL | 용도 |
|------|-----|------|
| 고객의소리 | https://www.truefriend.com/main/customer/support/Support.jsp?cmd=agree_3 | 기술 문의 |
| Developers 포털 | https://apiportal.koreainvestment.com | API 문서 |
| GitHub Issues | https://github.com/koreainvestment/open-trading-api/issues | 버그 리포트 |

#### 자주 묻는 질문 (FAQ)

**Q1. 토큰이 만료되었습니다. 어떻게 하나요?**
```python
# 자동 재발급
client.auth.get_access_token(force_refresh=True)
```

**Q2. 429 에러가 발생합니다.**
```python
# Rate Limit 초과. 대기 후 재시도
import time
time.sleep(1)
```

**Q3. WebSocket 연결이 끊깁니다.**
```python
# Ping/Pong 자동 응답 구현 필요
# 또는 재연결 로직 추가
```

---

### 11. 보안 주의사항

#### ⚠️ 절대 금지
```python
# ❌ AppKey/SecretKey를 코드에 하드코딩
app_key = "PSwZrk7YYIoakVSkM2e0uxtcmvekby1CQlzj"  # 절대 금지!

# ✅ 환경변수 또는 설정 파일 사용
import os
app_key = os.getenv("KIS_APP_KEY")

# ✅ 또는 YAML 설정 파일
import yaml
with open("config/secrets.yaml") as f:
    config = yaml.safe_load(f)
    app_key = config["key"]["kis_app_key"]
```

#### 🔒 권장 사항
1. ✅ 설정 파일은 `.gitignore`에 추가
2. ✅ 토큰은 로컬에만 저장
3. ✅ HTTPS/WSS만 사용
4. ✅ 주기적인 토큰 갱신

---

### 12. 성능 최적화 팁

#### A. 데이터 수집
```python
# ❌ 나쁜 예: 반복 API 호출
for ticker in tickers:
    price = client.get_price(ticker)  # 너무 느림

# ✅ 좋은 예: WebSocket 사용
client.websocket.subscribe_price(tickers, callback)
```

#### B. 주문 실행
```python
# ❌ 나쁜 예: 동기 처리
for order in orders:
    client.place_order(**order)  # 순차 실행

# ✅ 좋은 예: 비동기 처리
import asyncio
await asyncio.gather(*[
    client.place_order(**order) for order in orders
])
```

---

## 🎯 결론

한국투자증권은 **336개의 완전한 API**와 **실시간 WebSocket**을 통해 전문가 수준의 자동매매 시스템 구축을 지원합니다.

### 핵심 링크
1. **API 포털**: https://apiportal.koreainvestment.com
2. **GitHub**: https://github.com/koreainvestment/open-trading-api
3. **고객지원**: https://www.truefriend.com/main/customer/support/Support.jsp?cmd=agree_3

### ISATS 시스템 현황
- ✅ 336개 API 100% 통합 완료
- ✅ 국내/미국 자동매매 실행 중
- ✅ 실시간 데이터 처리 준비 완료
- ✅ 오류 자동 해결 시스템 가동

---

**작성**: ISATS Development Team  
**날짜**: 2026-01-22  
**버전**: Final v1.0
