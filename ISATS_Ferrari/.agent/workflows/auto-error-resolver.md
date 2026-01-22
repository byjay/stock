---
name: Auto Error Resolver
description: 오류 발생 시 자동으로 감지하고 해결하는 AI 스킬
---

# 🔧 Auto Error Resolver Skill

## 목적
시스템 실행 중 발생하는 모든 오류를 자동으로 감지하고, 즉시 해결책을 제시하거나 자동 수정합니다.

## 작동 방식

### 1. 오류 감지 (Error Detection)
```python
# 로그 파일 실시간 모니터링
# 오류 패턴 자동 인식:
# - Python Exception
# - API Error (403, 404, 500 등)
# - Connection Timeout
# - Data Format Error
```

### 2. 오류 분류 (Error Classification)
| 오류 유형 | 자동 해결 가능 여부 | 조치 |
|-----------|---------------------|------|
| **API 인증 오류** | ✅ 자동 해결 | 토큰 재발급 |
| **Rate Limit** | ✅ 자동 해결 | 대기 후 재시도 |
| **네트워크 오류** | ✅ 자동 해결 | 재연결 시도 |
| **데이터 파싱 오류** | ✅ 자동 해결 | 예외 처리 추가 |
| **설정 오류** | ⚠️ 수동 필요 | 사용자 알림 |
| **코드 로직 오류** | ⚠️ 수동 필요 | 디버그 정보 제공 |

### 3. 자동 해결 프로세스

#### A. API 인증 오류 (403, 401)
```python
def auto_fix_auth_error():
    """
    1. 토큰 만료 확인
    2. 새 토큰 자동 발급
    3. 설정 파일 업데이트
    4. 시스템 재시작 없이 적용
    """
    pass
```

#### B. Rate Limit 오류 (429)
```python
def auto_fix_rate_limit():
    """
    1. 현재 요청 일시 중단
    2. Exponential Backoff 적용
    3. 재시도 간격 자동 조정
    4. 정상화 후 재개
    """
    pass
```

#### C. 데이터 오류
```python
def auto_fix_data_error(error_msg):
    """
    1. 오류 발생 지점 파악
    2. 데이터 타입 자동 변환
    3. 예외 처리 코드 삽입
    4. 로그 기록
    """
    pass
```

### 4. 실시간 모니터링

```bash
# 로그 파일 감시
tail -f logs/*.log | grep -E "ERROR|CRITICAL|Exception"

# 오류 발생 시 즉시 알림
```

### 5. 해결 불가능한 오류 처리

```python
def escalate_to_user(error_info):
    """
    1. 오류 상세 정보 수집
    2. 스택 트레이스 저장
    3. 사용자에게 알림 (콘솔 + 파일)
    4. 임시 우회 방법 제시
    """
    pass
```

## 사용 예시

### 자동 실행
```bash
# 백그라운드에서 오류 모니터링 시작
python skills/auto_error_resolver.py &

# 메인 프로그램 실행
python auto_trading_launcher.py --mode virtual
```

### 수동 실행
```bash
# 특정 오류 해결
python skills/auto_error_resolver.py --fix "API 403 Error"
```

## 해결 사례

### Case 1: 토큰 만료
```
[오류] 403 - 유효하지 않은 AppKey
[조치] 토큰 자동 재발급 완료
[결과] ✅ 시스템 정상 작동
```

### Case 2: 데이터 파싱 오류
```
[오류] could not convert string to float: ''
[조치] 빈 문자열 처리 로직 추가
[결과] ✅ 예외 처리 완료
```

### Case 3: 네트워크 타임아웃
```
[오류] Connection timeout
[조치] 재연결 시도 (3회)
[결과] ✅ 연결 복구
```

## 설정

```yaml
# config/error_resolver.yaml
auto_resolve:
  enabled: true
  retry_count: 3
  retry_interval: 5  # seconds
  
notifications:
  console: true
  file: true
  email: false  # 추후 구현
  
escalation:
  critical_errors:
    - "Database connection failed"
    - "Critical system error"
  notify_user: true
```

## 로그 형식

```
2026-01-22 22:06:31 [ERROR] API 403 Error detected
2026-01-22 22:06:32 [RESOLVER] Attempting auto-fix: Token refresh
2026-01-22 22:06:33 [SUCCESS] ✅ Error resolved automatically
2026-01-22 22:06:33 [INFO] System resumed normal operation
```

## 향후 개선 사항

1. **AI 기반 오류 예측**: 오류 발생 전 사전 감지
2. **자동 코드 패치**: 간단한 버그 자동 수정
3. **학습 기능**: 반복 오류 패턴 학습 및 최적화
4. **알림 통합**: Slack, Email, SMS 알림 지원

---

**작성일**: 2026-01-22  
**버전**: 1.0  
**상태**: 활성화
