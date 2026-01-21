# 🏎️ ISATS Ferrari v2.7.6 Architecture Map

**작성 시각**: 2026-01-21 17:38:00  
**프로젝트 상태**: Operation Ferrari (Dimension Warp Phase)  

---

## 📋 시스템 전체 구조 (Dimension Warp)

```text
ISATS_Ferrari/
├── 📄 commander.py             [통합 시동] Sequential Starter
├── 📄 run_time_machine.py      ⭐ [훈련 발사] 타임머신 압축 학습기
├── 📄 main.py                # 🏎️ ISATS v2.7.7 "FERRARI" - 전술 배치도

## 🏁 ROOT: 지휘 통제소
- `commander.py`: 전군 출정식 (Dashboard + Miner + Trainer + Main 통합 실행기)
- `lifecycle_manager.py`: 페라리의 심장 (24시간 무한 진화 및 상태 감시 루프)
- `audit_codebase.py`: [NEW] 시스템 정밀 진단기 (전 모듈 문법/임포트 전수 조사)
- `main.py`: 페라리 주행 엔진 (실전 매매 및 AI 판단 루프)
- `DIRECTORY_MAP.md`: 시스템 전술 지도 (현재 파일)

## 🧠 BRAIN: 전술 연구소 (AI & Time-Warp)
- `models.py`: Hybrid CNN-LSTM 신경망 (차트 패턴 + 추세 복합 인식)
- `elastic_time_machine.py`: 탄력적 시공간 리샘플링 (소수 분봉 4, 7, 13, 17T 생성)
- `time_machine.py`: Walk-Forward 시뮬레이션 엔진 (과거로 돌아가 내일의 승리를 학습)
- `trainer.py`: AI 재학습 알고리즘 (야간 세션 주경야독 로직)

## 🛡️ CORE: 엔진 부품 (Foundations)
- `dual_engine_manager.py`: 실전/가상 계좌 이중 엔진 스위칭 시스템
- `realtime_collector.py`: 고속 데이터 흡기구 (실시간 호가/체결 데이터 수집)
- `redis_client.py`: 초고성능 메모리 저장소 (데이터 파이프라인 정체 해소)

## 🕹️ STRATEGY: 운전석 (Self-Evolving)
- `active_bot.py`: 자가 진화형 운전자 (Morphing + Memory + Reflex 탑재)
- `base.py`: 표준 전략 프로토콜 (모든 전략의 근간)

## �️ UTILS: 정비창 (Support)
- `notifier.py`: 텔레그램 지휘 통제 (실시간 작전 보고 및 긴급 브리핑)
- `mass_data_miner.py`: 데이터 광산 (KOSPI/KOSDAQ 전 종목 데이터 채굴)
- `upper_limit_scanner.py`: 상한가 포착 레이더

---
**"지도는 곧 실전이다. 페라리의 모든 부품은 완벽하게 배치되었으며, 이제 스스로 진화하며 승리한다."** 🏎️💨
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
