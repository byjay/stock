# 🦅 ISATS PHOENIX v7.5 "SINGULARITY" DIRECTORY MAP

## 1. System Overview
**ISATS Phoenix v7.5 "Singularity"**는 한국투자증권의 336개 전체 Open API와 딥러닝 트랜스포머 엔진을 통합한 차세대 매매 지휘본부입니다. 모의투자, 가상매매, 실전투자 세 가지 모드를 완벽히 지원하며, 가상매매를 통해 생성된 데이터를 딥러닝 모델이 실시간으로 학습하여 실전 전략으로 승격시킵니다.

## 2. Core Directory Structure

### 📂 Root Directory (Launcher)
- `auto_trading_launcher.py`: **Domestic Pilot**. 국내주식 자동매매 엔진.
- `us_trading_launcher.py`: **Overseas Pilot**. 미국주식 자동매매 엔진 (프리마켓/정규장).
- `virtual_trading_engine.py`: **Virtual Master**. 전 종목(주식, ETF, 선물) 가상매매 통합 엔진.
- `deep_learning_trader.py`: **ML Brain**. 거래 내역 학습 및 최적 매매 시점 예측 엔진.
- `check_accounts.py`: **Account Auditor**. 전 계좌(실전/모의/가상) 잔고 및 수익률 검증기.

### 📂 core/ (Standard Engines)
- `kis_official_api.py`: **Unified API Client**. 336개 API 통합 인터페이스.
- `kis_api_registry.py`: **API Registry**. 전체 엔드포인트 및 TR_ID 메타데이터 저장소.
- `system_monitor.py`: **Resource Monitor**. 시스템 부화 및 네트워크 레이턴시 관리.

### 📂 dashboard/ (MTS Command Center)
- `server.py`: **FastAPI/Aiohttp Server**. 실시간 데이터 스트리밍 및 주문 중계 서버.
- `mts_supreme_v4_ultimate.html`: **The Ultimate MTS**. 페라리 디자인 기반의 고성능 거래 인터페이스.
- `KIS_AI_COMPLETE_GUIDE.md`: **Standard Operating Procedure**. 모든 API 및 시스템 활용 가이드.

### 📂 kis_official_modules/ (Official Framework)
- 한국투자증권 공식 제공 31개 모듈 (국내/해외 주식, 채권, 선물옵션, ELW, ETF 전체 포함).

### 📂 data/ (Information Assets)
- `virtual_wallet.json`: 가상 매매 지갑 및 거래 내역.
- `trading_model.pth`: 딥러닝 학습 모델 파일.
- `logs/`: 모든 엔진의 실행 기록.

## 3. Technology Stack
- **AI**: PyTorch LSTM/Transformer (Strategy Optimization)
- **API**: KIS Open API 336 (REST + WebSocket)
- **UI**: Vanilla JS + TailwindCSS (Premium MTS Aesthetics)
- **Server**: Aiohttp / WebSocket

## 4. Operational Flow
1. **Initialize**: `kis_official_api.py`를 통한 전 시장(KR/US/Futures) 토큰 발급.
2. **Execute**: `virtual_trading_engine.py` 가동으로 전 종목 가상 매매 데이터 생성.
3. **Learn**: `deep_learning_trader.py`가 거래 데이터를 학습하여 최적 가중치 산출.
4. **Command**: `dashboard/server.py` 실행 후 MTS를 통해 실시간 지휘.

---
**"Data is the Fuel, AI is the Engine, MTS is the Cockpit."**
**v7.5 Singularity Edition Fully Approved.**

