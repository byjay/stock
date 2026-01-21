# 🏎️ ISATS Ferrari v2.7.6 Architecture Map

**작성 시각**: 2026-01-21 17:38:00  
**프로젝트 상태**: Operation Ferrari (Dimension Warp Phase)  

---

## 📋 시스템 전체 구조 (Dimension Warp)

```text
ISATS_Ferrari/
├── 📄 commander.py             [통합 시동] Sequential Starter
├── 📄 run_time_machine.py      ⭐ [훈련 발사] 타임머신 압축 학습기
├── 📄 main.py                  [메인 엔진] 최종 매매 실행
│
├── 📁 core/                    # [기동] 시스템 핵심 인프라
│   ├── 📄 lifecycle_manager.py  [불멸의 심장] 24H 루프 관리
│   └── ...
│
├── � brain/                   # [지능] AI 신경망 및 훈련기
│   ├── 📄 time_machine.py      ⭐ [과거 회귀] Walk-Forward 훈련 엔진
│   ├── 📄 elastic_time_machine.py ⭐ [시공간 왜곡] 소수(Prime) 기반 리샘플러
│   ├── 📄 models.py             [두뇌 설계] Hybrid CNN-LSTM
│   └── ...
│
├── 📁 config/                  # [중추] 단일 설정 점점
│   └── 📄 secrets.yaml          # KIS + Telegram + System Config
│
├── 📁 strategy/                # [전략] AI-DNA 하이브리드
│   └── 📄 active_bot.py         [실전 보드] AI 렌즈 반영 전략
│
├── 📁 utils/                   # [유틸] 알림 및 수집
│   ├── 📄 notifier.py           📡 [전술 통신] 텔레그램 알림
│   └── ...
│
├── 📁 data/                    # [연료] 시세 데이터
│   ├── 📁 KR/ (1M/1D CSV)      # 분봉/일봉 혼합 데이터셋
│   └── ...
```

---

## �️ 4차원 훈련 시스템 (Dimension Warp System)

1. **타임머신 (`time_machine.py`)**: 
   - 과거 2년 전으로 "기억 소거 후 회귀".
   - 매일 밤 어제의 차트를 보고 AI가 반성 및 미세 조정(Fine-tuning).
   - 정답(내일 가격)을 모르는 채로 730일을 살아남는 실전 압축 훈련.

2. **탄력적 리샘플러 (`elastic_time_machine.py`)**: 
   - 남들이 다 보는 5분, 15분, 60분 봉의 함정을 회피.
   - **4, 7, 13, 17분(소수)** 단위로 차트를 재조립하여 숨겨진 세력의 흔적 수색.
   - 주간 단위로 가장 잘 맞는 "시간의 렌즈"를 찾아 전략에 주입.

---

**"페라리는 이제 과거를 통해 미래를 보고, 남들이 보지 못하는 시간의 틈새에서 수익을 창출합니다."** 🏎️💨
