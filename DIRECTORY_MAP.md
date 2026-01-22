# 🦅 ISATS PHOENIX v7.0 DIRECTORY MAP (Standardized)

## 1. System Overview
**ISATS Phoenix v7.0**은 기존의 비직관적인 명칭을 배제하고, 산업 표준(Industrial Standard)에 맞춘 네이밍과 구조를 채택한 지능형 매매 시스템입니다. 모든 핵심 모듈은 S-Class 수준의 문서화와 타입 힌트를 준수하며, 환경적 리스크(API 속도 제한, 데이터 지연)에 대한 자동 방어 체계를 갖추고 있습니다.

## 2. Core Directory Structure

### 📂 Root Directory
- `main.py`: **System Command Center**. 시스템 초기화, 자원 점검, 다중 에이전트(Sniper, Scout, Patrol) 조율 및 실행.
- `api_server.py`: **Communication Hub**. FastAPI 기반 WebSocket/REST 서버. Redis 데이터를 대시보드로 중계.
- `antigravity_agent.py`: **Intelligence Orchestrator**. 종목 분석, 리포트 생성, 시스템 진단을 수행하는 AI 에이전트.
- `Dockerfile` & `docker-compose.yml`: **Virtualization**. 시스템의 컨테이너화 및 배포 정의.

### 📂 core/ (Standard Engines)
- `system_monitor.py`: **Resource Monitor**. CPU, RAM, 네트워크, **Redis Latency(50ms Warning)** 모니터링.
- `risk_manager.py`: **Market Risk Guard**. Turbulence Index를 활용해 시장 상태(Crash, Bull, Normal) 판단.
- `signal_validator.py`: **Standard Validator**. 기술적 신호의 유효성(거래량, 상위 추세, 스프레드) 최종 필터링.
- `kis_api_client.py`: **API Bridge**. 한국투자증권 API 연동. **Adaptive Backoff(429 Error)** 기능 포함.
- `redis_client.py`: **Data Backbone**. 고속 데이터 교환을 위한 Redis 인터페이스.

### � strategy/ (Tactical Pilots)
- `active_bot.py`: **Standard Trading Pilot**. DNA(Target Profit/Stop Loss/Timeframe) 연동형 실전 매매 봇.
- `strategy_factory.py`: DNA 정보를 바탕으로 실전 전략 객체 생성.

### � brain/ (Evolutionary Center)
- `genesis_evolution_v2.py`: **Strategy Breeder**. SignalValidator가 통합된 유전 알고리즘 훈련소.
- `task.md`: 현재 작업 진행률 및 로드맵 관리.

### 📂 reports/ (Audit & Results)
- `TOTAL_AUDIT_REPORT.md`: 시스템 전체 코드 퀄리티 감사 결과.
- `walkthrough.md`: 단계별 구현 및 검증 결과 기록.

## 3. Technology Stack
- **Language**: Python 3.10+ (Static Typing)
- **Framework**: FastAPI (API), PyTorch (Optional Training), Pandas/Numpy (Analysis)
- **Infrastructure**: Redis (Cache/Streaming), Docker (Deployment)
- **Principles**: MECE, Solid Pillars of Trading, High-Quality Documentation

## 4. Execution (Real-Battle Mode)
1. **Docker Build**: `docker-compose build`
2. **System Launch**: `docker-compose up -d`
3. **Internal Core**: `main.py` -> `SystemMonitor` Check -> `ActiveBot` Sortie.

---
**"Standardization is the Foundation of Excellence."**
**v7.0 Standard Edition Fully Approved.**
