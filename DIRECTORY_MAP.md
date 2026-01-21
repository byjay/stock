# 🏎️ ISATS Ferrari v2.7.5 Architecture Map

**작성 시각**: 2026-01-21 17:30:00  
**프로젝트 상태**: Operation Ferrari (Autonomous Lifecycle Phase)  
**가훈**: "화물차의 짐을 버리고, 페라리의 엔진만을 남겼다. 15,000개의 과거는 이제 50개의 미래다."

---

## 📋 시스템 전체 구조 (Pure Core Structure)

```text
ISATS_Ferrari/
├── 📄 commander.py             [통합 시동] 채굴-학습-수집-매매 Sequential Starter
├── 📄 main.py                  [메인 엔진] 최종 매매 실행 진입점
│
├── 📁 core/                    # [기동] 시스템 핵심 인프라
│   ├── 📄 lifecycle_manager.py  ⭐ [불멸의 심장] 24H 루프 및 무한 진화 관리
│   ├── 📄 engine.py            # DNA 진화 및 메인 루프 제어
│   ├── 📄 dual_engine_manager.py # 실전/모의 동시 운영 및 자동 승격 매니저
│   ├── 📄 realtime_collector.py # 실시간 시세 수집 및 Redis 전송
│   └── 📄 redis_client.py      # 비중 중추 고속 통신 클라이언트
│
├── 📁 config/                  # [중추] 단일 진실 공급원 (Single Source of Truth)
│   ├── 📄 dna.json             # 유전자 (진화하는 매매 파라미터)
│   ├── 📄 secrets.yaml         # KIS API + 텔레그램 인증 정보
│   └── 📄 dual_engine.yaml     # 실전+모의 동시 운영 설정
│
├── 📁 brain/                   # [지능] AI 신경망 시스템
│   ├── 📄 models.py            # CNN-LSTM 하이브리드 패턴 인식 설계도
│   ├── 📄 trainer.py           # 훈련 교관 (데이터 기반 자동 학습)
│   ├── 📄 evolution.py         # DNA 변이 및 적자생존 로직
│   └── 📁 weights/             # 학습된 지능 가중치 저장소 (.pth)
│
├── 📁 strategy/                # [전략] 하이브리드 매매 로직
│   ├── 📄 base.py              # 전략 템플릿 (DNA 연동 인터페이스)
│   └── 📄 active_bot.py        # AI-DNA 하이브리드 실전 전략
│
├── 📁 dashboard/               # [시각] 지휘 통제 GUI
│   ├── 📄 server.py            # 웹 대시보드 서버 (Port 8080)
│   └── 📄 sniper_dragon_dashboard.html # Sniper Dragon 통합 차트 분석기
│
├── 📁 utils/                   # [특수] 고성능 유틸리티
│   ├── 📄 notifier.py          📡 [전술 통신] 텔레그램 알림 모듈
│   ├── 📄 mass_data_miner.py   # 대규모 데이터 채굴기 (한미 1,000종목 4년치)
│   └── 📄 upper_limit_scanner.py # 실시간 상한가/거래량 급증 종목 수색기
│
├── 📁 data/                    # [연료] 시세 데이터 저장소
│   ├── 📁 KR/                  # 한국 주식 정제 데이터 (CSV)
│   ├── 📁 US/                  # 미국 주식 정제 데이터 (CSV)
│   └── 📄 upper_limit_*.csv    # 실시간 수색된 타겟 종목 리스트
│
├── 📁 tests/                   # [검증] 통신 및 로직 테스트
│   └── 📄 test_kis_api.py      # KIS API 연결 정밀 진단기
│
├── 📁 database/                # [기록] 로컬 데이터베이스
└── 📁 logs/                    # [감사] 시스템 실행 로그
```

---

## 🏎️ 불멸의 주기 (Infinite Evolution Lifecycle)

1. **상시 기동**: `lifecycle_manager.py`가 24시간 상주하며 시스템 감시.
2. **실시간 보고**: 중요한 순간마다 `notifier.py`가 사령관님께 텔레그램 보고.
3. **새벽의 진화**: 매일 08:30, 봇이 스스로 매매를 멈추고 데이터를 채굴한 뒤, **Deep Eyes** 신경망을 재학습(Evolution)하여 더 똑똑한 버전으로 부활.
4. **자동 심폐소생**: 메인 엔진(`main.py`)이 오류로 죽으면 관리자가 즉시 감지하여 재점화.

---

**"페라리는 이제 스스로 생각하고, 스스로 진화하며, 사령관님께 보고합니다."** 🏎️💨
